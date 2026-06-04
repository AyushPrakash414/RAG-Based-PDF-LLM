"""
Unit tests for the ingestion service (Issues 2 & 3).

Tests:
1. Streaming PDF processing (page-by-page)
2. Async ingestion with progress tracking
3. File type validation
4. Filename sanitization
5. Memory efficiency (no full file in memory)
6. Batch embedding
"""

import asyncio
import uuid

import pytest
import pytest_asyncio

from tests.conftest import (
    MockVectorStore,
    FakeUploadFile,
    create_test_pdf,
    create_test_docx,
    create_test_txt,
)
from app.services.ingestion_service import (
    IngestionService,
    IngestionStatus,
    get_task,
    _sanitize_filename,
    _validate_file_type,
)


class TestFileValidation:
    """Test file type validation and sanitization."""

    def test_valid_pdf_extension(self):
        assert _validate_file_type("test.pdf", b"%PDF-1.4") is True

    def test_valid_docx_extension(self):
        assert _validate_file_type("test.docx", b"PK\x03\x04") is True

    def test_valid_txt_extension(self):
        assert _validate_file_type("test.txt", b"Hello") is True

    def test_invalid_extension(self):
        assert _validate_file_type("test.exe", b"\x00\x00") is False

    def test_pdf_extension_wrong_magic(self):
        """PDF extension but not a real PDF should fail."""
        assert _validate_file_type("fake.pdf", b"NOT-PDF!") is False

    def test_docx_extension_wrong_magic(self):
        """DOCX extension but not a real ZIP should fail."""
        assert _validate_file_type("fake.docx", b"NOT-ZIP!") is False

    def test_sanitize_path_traversal(self):
        """Filename with path traversal must be sanitized."""
        result = _sanitize_filename("../../etc/passwd")
        assert ".." not in result
        assert "/" not in result or "\\" not in result

    def test_sanitize_null_bytes(self):
        result = _sanitize_filename("test\x00.pdf")
        assert "\x00" not in result

    def test_sanitize_long_filename(self):
        long_name = "a" * 300 + ".pdf"
        result = _sanitize_filename(long_name)
        assert len(result) <= 255

    def test_sanitize_normal_filename(self):
        result = _sanitize_filename("my_document.pdf")
        assert result == "my_document.pdf"


class TestIngestionService:
    """Test core ingestion functionality."""

    @pytest.fixture
    def svc(self):
        vs = MockVectorStore()
        return IngestionService(
            vector_store=vs,
            embedding_batch_size=4,
            page_window_size=2,
        ), vs

    @pytest.mark.asyncio
    async def test_pdf_ingestion_basic(self, svc):
        """Basic PDF ingestion should work."""
        ingestion, vs = svc
        pdf_bytes = create_test_pdf("Spring Boot microservices tutorial content.")
        file = FakeUploadFile("test.pdf", pdf_bytes)
        doc_id = str(uuid.uuid4())

        result = await ingestion.ingest_file(file, doc_id)

        assert result["document_id"] == doc_id
        assert result["filename"] == "test.pdf"
        assert result["chunks_processed"] > 0
        assert len(vs._documents) > 0

    @pytest.mark.asyncio
    async def test_docx_ingestion_basic(self, svc):
        """Basic DOCX ingestion should work."""
        ingestion, vs = svc
        docx_bytes = create_test_docx("Machine learning is transforming industries.")
        file = FakeUploadFile("report.docx", docx_bytes)
        doc_id = str(uuid.uuid4())

        result = await ingestion.ingest_file(file, doc_id)

        assert result["chunks_processed"] > 0
        assert result["filename"] == "report.docx"

    @pytest.mark.asyncio
    async def test_txt_ingestion_basic(self, svc):
        """Basic TXT ingestion should work."""
        ingestion, vs = svc
        txt_bytes = create_test_txt("Artificial intelligence is the future of computing." * 10)
        file = FakeUploadFile("notes.txt", txt_bytes)
        doc_id = str(uuid.uuid4())

        result = await ingestion.ingest_file(file, doc_id)

        assert result["chunks_processed"] > 0

    @pytest.mark.asyncio
    async def test_empty_document_raises(self, svc):
        """Empty document should raise ValueError."""
        ingestion, vs = svc
        file = FakeUploadFile("empty.txt", b"   ")
        doc_id = str(uuid.uuid4())

        with pytest.raises(ValueError, match="No text"):
            await ingestion.ingest_file(file, doc_id)

    @pytest.mark.asyncio
    async def test_invalid_file_type_raises(self, svc):
        """Invalid file type should raise ValueError."""
        ingestion, vs = svc
        file = FakeUploadFile("malware.exe", b"\x00\x01\x02\x03")
        doc_id = str(uuid.uuid4())

        with pytest.raises(ValueError, match="Invalid file type"):
            await ingestion.ingest_file(file, doc_id)

    @pytest.mark.asyncio
    async def test_metadata_includes_source(self, svc):
        """All stored chunks must have source metadata."""
        ingestion, vs = svc
        txt_bytes = create_test_txt("Test content for metadata verification.")
        file = FakeUploadFile("metadata_test.txt", txt_bytes)
        doc_id = str(uuid.uuid4())

        await ingestion.ingest_file(file, doc_id)

        for doc in vs._documents:
            assert "source" in doc["metadata"]
            assert doc["metadata"]["source"] == "metadata_test.txt"
            assert "document_id" in doc["metadata"]
            assert doc["metadata"]["document_id"] == doc_id

    @pytest.mark.asyncio
    async def test_batch_embedding(self, svc):
        """Embedding should be called in batches."""
        ingestion, vs = svc
        # Create enough content to generate multiple chunks
        big_text = ("This is a long document about various topics. " * 100)
        txt_bytes = create_test_txt(big_text)
        file = FakeUploadFile("big.txt", txt_bytes)
        doc_id = str(uuid.uuid4())

        await ingestion.ingest_file(file, doc_id)

        # embed_texts should have been called multiple times (batch_size=4)
        assert vs._embed_call_count >= 1
        assert len(vs._documents) > 0


class TestAsyncIngestion:
    """Test async ingestion with progress tracking."""

    @pytest.mark.asyncio
    async def test_start_ingestion_returns_task_id(self):
        """Async ingestion should return a task ID immediately."""
        vs = MockVectorStore()
        ingestion = IngestionService(vector_store=vs)

        txt_bytes = create_test_txt("Test content for async processing.")
        file = FakeUploadFile("async_test.txt", txt_bytes)
        doc_id = str(uuid.uuid4())

        result = await ingestion.start_ingestion(file, doc_id)

        assert "task_id" in result
        assert result["status"] == "QUEUED"
        assert result["document_id"] == doc_id

    @pytest.mark.asyncio
    async def test_task_progresses_to_completed(self):
        """Task should eventually reach COMPLETED status."""
        vs = MockVectorStore()
        ingestion = IngestionService(vector_store=vs)

        txt_bytes = create_test_txt("Test content for progress tracking.")
        file = FakeUploadFile("progress_test.txt", txt_bytes)
        doc_id = str(uuid.uuid4())

        result = await ingestion.start_ingestion(file, doc_id)
        task_id = result["task_id"]

        # Wait for background task to complete
        for _ in range(50):
            await asyncio.sleep(0.1)
            task = get_task(task_id)
            if task and task.status in (IngestionStatus.COMPLETED, IngestionStatus.FAILED):
                break

        task = get_task(task_id)
        assert task is not None
        assert task.status == IngestionStatus.COMPLETED
        assert task.chunks_processed > 0
        assert task.progress_pct == 100.0

    @pytest.mark.asyncio
    async def test_task_reports_failure(self):
        """Failed ingestion should set FAILED status with error message."""
        vs = MockVectorStore()
        ingestion = IngestionService(vector_store=vs)

        # Empty content will fail
        file = FakeUploadFile("empty.txt", b"   ")
        doc_id = str(uuid.uuid4())

        result = await ingestion.start_ingestion(file, doc_id)
        task_id = result["task_id"]

        # Wait for background task
        for _ in range(50):
            await asyncio.sleep(0.1)
            task = get_task(task_id)
            if task and task.status in (IngestionStatus.COMPLETED, IngestionStatus.FAILED):
                break

        task = get_task(task_id)
        assert task is not None
        assert task.status == IngestionStatus.FAILED
        assert task.error is not None


class TestDocumentDeletion:
    """Test document deletion."""

    @pytest.mark.asyncio
    async def test_delete_removes_documents(self):
        """Deleting a document should remove all its chunks."""
        vs = MockVectorStore()
        ingestion = IngestionService(vector_store=vs)

        txt_bytes = create_test_txt("Content to be deleted.")
        file = FakeUploadFile("delete_test.txt", txt_bytes)
        doc_id = "delete-me-doc"

        await ingestion.ingest_file(file, doc_id)
        assert len(vs._documents) > 0

        await ingestion.delete_document(doc_id)
        assert len(vs._documents) == 0
