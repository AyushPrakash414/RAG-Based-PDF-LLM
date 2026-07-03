"""
Ingestion service for document processing.

Handles extracting text from uploaded files, chunking it,
embedding it, and storing it in the vector database.

Supports:
  - Streaming page-by-page PDF processing (low memory)
  - Background async processing with progress tracking
  - Batch embedding with configurable batch sizes
  - Retry support for failed chunks
"""

import asyncio
import io
import logging
import uuid
import os
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from fastapi import UploadFile
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.interfaces.vector_store import VectorStore

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Task tracking
# ---------------------------------------------------------------------------

class IngestionStatus(str, Enum):
    """Status of an ingestion task."""
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class IngestionTask:
    """Tracks the state of an async ingestion task."""
    task_id: str
    document_id: str
    filename: str
    status: IngestionStatus = IngestionStatus.QUEUED
    progress_pct: float = 0.0
    chunks_processed: int = 0
    total_chunks: int = 0
    error: str | None = None
    result: dict[str, Any] | None = None


# Global task store (in-memory; for production use Redis or DB)
_task_store: dict[str, IngestionTask] = {}


def get_task(task_id: str) -> IngestionTask | None:
    """Retrieve an ingestion task by ID."""
    return _task_store.get(task_id)


# ---------------------------------------------------------------------------
# File validation
# ---------------------------------------------------------------------------

# Magic bytes for supported file types
_MAGIC_BYTES = {
    "pdf": [b"%PDF"],
    "docx": [b"PK\x03\x04"],  # ZIP archive (DOCX is a ZIP)
    "txt": [],  # No magic bytes for plain text
}

_ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".csv"}
_MAX_FILENAME_LENGTH = 255


def _sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and injection."""
    import os
    # Strip path components
    filename = os.path.basename(filename)
    # Remove null bytes and special characters
    filename = filename.replace("\x00", "").replace("..", "")
    # Limit length
    if len(filename) > _MAX_FILENAME_LENGTH:
        ext = os.path.splitext(filename)[1]
        filename = filename[:_MAX_FILENAME_LENGTH - len(ext)] + ext
    return filename


def _validate_file_type(filename: str, content_start: bytes) -> bool:
    """
    Validate file type by both extension and magic bytes.

    Args:
        filename: The file name.
        content_start: First 8 bytes of the file for magic number check.

    Returns:
        True if the file type is valid.
    """
    import os
    ext = os.path.splitext(filename.lower())[1]

    if ext not in _ALLOWED_EXTENSIONS:
        return False

    # Check magic bytes for known binary formats
    if ext == ".pdf":
        return any(content_start.startswith(m) for m in _MAGIC_BYTES["pdf"])
    elif ext == ".docx":
        return any(content_start.startswith(m) for m in _MAGIC_BYTES["docx"])
    # Plain text formats don't have magic bytes
    return True


# ---------------------------------------------------------------------------
# Ingestion service
# ---------------------------------------------------------------------------

class IngestionService:
    """
    Handles extracting text from uploaded files, chunking it,
    embedding it, and storing it in the vector database.

    Supports streaming page-by-page processing for large PDFs
    and background async processing with progress tracking.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_batch_size: int = 32,
        page_window_size: int = 5,
    ) -> None:
        """
        Initialise the ingestion service.

        Args:
            vector_store: Vector store for document storage.
            embedding_batch_size: Number of chunks to embed per batch.
            page_window_size: Number of PDF pages to process at once.
        """
        self.vector_store = vector_store
        self._embedding_batch_size = embedding_batch_size
        self._page_window_size = page_window_size
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )

    async def start_ingestion(self, file: UploadFile, document_id: str) -> dict:
        """
        Start async ingestion and return immediately with a task ID.

        Args:
            file: The uploaded file.
            document_id: Document identifier.

        Returns:
            Dict with task_id and initial status.
        """
        filename = _sanitize_filename(file.filename or "unknown.txt")

        # Read file content (needed before we can process in background)
        content = await file.read()

        # Validate file size
        max_bytes = 100 * 1024 * 1024  # 100 MB default
        if len(content) > max_bytes:
            raise ValueError(
                f"File too large: {len(content)} bytes "
                f"(max: {max_bytes} bytes)"
            )

        # Validate file type
        if not _validate_file_type(filename, content[:8]):
            raise ValueError(
                f"Invalid file type: {filename}. "
                f"Allowed: {', '.join(_ALLOWED_EXTENSIONS)}"
            )

        # Create task
        task_id = str(uuid.uuid4())
        task = IngestionTask(
            task_id=task_id,
            document_id=document_id,
            filename=filename,
        )
        _task_store[task_id] = task

        from app.config.settings import get_settings
        settings = get_settings()

        if settings.redis_url:
            # Save to temporary file for Celery
            temp_dir = os.path.join(tempfile.gettempdir(), "rag_ingest")
            os.makedirs(temp_dir, exist_ok=True)
            temp_filepath = os.path.join(temp_dir, f"{task_id}_{filename}")
            
            with open(temp_filepath, "wb") as f:
                f.write(content)
    
            # Launch background processing via Celery
            from app.worker.tasks import process_document_ingestion
            process_document_ingestion.delay(
                task_id=task_id,
                document_id=document_id,
                filename=filename,
                temp_filepath=temp_filepath
            )
            logger.info("Enqueued ingestion task to Celery: %s", task_id)
        else:
            # Fallback for local development without Redis/Celery
            logger.info("REDIS_URL not set. Falling back to asyncio.create_task for ingestion.")
            import asyncio
            asyncio.create_task(
                self._process_ingestion(task, content)
            )

        return {
            "task_id": task_id,
            "document_id": document_id,
            "filename": filename,
            "status": IngestionStatus.QUEUED.value,
        }

    async def ingest_file(self, file: UploadFile, document_id: str) -> dict:
        """
        Synchronous ingestion for backward compatibility.

        Processes the file and waits for completion.
        """
        filename = _sanitize_filename(file.filename or "unknown.txt")
        content = await file.read()

        # Validate file type
        if not _validate_file_type(filename, content[:8] if content else b""):
            raise ValueError(
                f"Invalid file type: {filename}. "
                f"Allowed: {', '.join(_ALLOWED_EXTENSIONS)}"
            )

        task = IngestionTask(
            task_id=str(uuid.uuid4()),
            document_id=document_id,
            filename=filename,
        )

        await self._process_ingestion(task, content)

        if task.status == IngestionStatus.FAILED:
            raise ValueError(task.error or "Ingestion failed")

        return task.result or {
            "document_id": document_id,
            "filename": filename,
            "chunks_processed": task.chunks_processed,
        }

    async def _process_ingestion(
        self, task: IngestionTask, content: bytes
    ) -> None:
        """
        Process file ingestion using the Factory Method pattern.
        """
        from app.services.loaders.loader_factory import LoaderFactory

        task.status = IngestionStatus.PROCESSING
        filename = task.filename
        document_id = task.document_id

        try:
            loader = LoaderFactory.get_loader(filename)
            
            async for text_window, progress_pct in loader.load(content):
                chunks = self.text_splitter.split_text(text_window)
                
                if chunks:
                    await self._embed_and_store_batch(
                        chunks=chunks,
                        document_id=document_id,
                        filename=filename,
                        start_chunk_index=task.chunks_processed,
                    )
                    task.chunks_processed += len(chunks)
                    
                task.progress_pct = progress_pct
                await asyncio.sleep(0)

            if task.chunks_processed == 0:
                raise ValueError("No text could be extracted from the document")

            task.status = IngestionStatus.COMPLETED
            task.progress_pct = 100.0
            task.result = {
                "document_id": document_id,
                "filename": filename,
                "chunks_processed": task.chunks_processed,
            }

            logger.info(
                "Ingestion completed: task_id=%s, filename=%s, chunks=%d",
                task.task_id,
                filename,
                task.chunks_processed,
            )

        except Exception as e:
            task.status = IngestionStatus.FAILED
            task.error = str(e)
            logger.error(
                "Ingestion failed: task_id=%s, filename=%s, error=%s",
                task.task_id,
                filename,
                e,
                exc_info=True,
            )

    async def _embed_and_store_batch(
        self,
        chunks: list[str],
        document_id: str,
        filename: str,
        start_chunk_index: int,
    ) -> None:
        """
        Embed a batch of chunks and store them in the vector DB.

        Runs embedding in a thread pool to avoid blocking the event loop.
        Processes in sub-batches to limit memory usage.
        """
        for sub_start in range(0, len(chunks), self._embedding_batch_size):
            sub_chunks = chunks[sub_start:sub_start + self._embedding_batch_size]

            # Run embedding in thread pool (non-blocking)
            embeddings = await asyncio.to_thread(
                self.vector_store.embed_texts, sub_chunks
            )

            metadatas = [
                {
                    "document_id": document_id,
                    "filename": filename,
                    "source": filename,
                    "chunk_index": start_chunk_index + sub_start + i,
                }
                for i in range(len(sub_chunks))
            ]

            ids = [str(uuid.uuid4()) for _ in sub_chunks]

            await self.vector_store.add_documents(
                documents=sub_chunks,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids,
            )

    async def delete_document(self, document_id: str) -> None:
        """Deletes all vector chunks associated with the document_id."""
        if hasattr(self.vector_store, "delete_by_document_id"):
            await self.vector_store.delete_by_document_id(document_id)
        else:
            logger.warning(
                "Configured VectorStore does not support delete_by_document_id"
            )
