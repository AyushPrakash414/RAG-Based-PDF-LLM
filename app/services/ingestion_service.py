import logging
import io
import uuid
from fastapi import UploadFile
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.interfaces.vector_store import VectorStore
import fitz  # PyMuPDF
import docx

logger = logging.getLogger(__name__)

class IngestionService:
    """
    Handles extracting text from uploaded files, chunking it,
    embedding it, and storing it in the vector database.
    """
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )

    async def ingest_file(self, file: UploadFile, document_id: str) -> dict:
        content = await file.read()
        filename = file.filename or "unknown.txt"
        text = ""

        try:
            if filename.lower().endswith(".pdf"):
                doc = fitz.open(stream=content, filetype="pdf")
                for page in doc:
                    text += page.get_text()
                doc.close()
            elif filename.lower().endswith(".docx"):
                doc = docx.Document(io.BytesIO(content))
                text = "\n".join([para.text for para in doc.paragraphs])
            else:
                # Assume TXT or other raw format
                text = content.decode("utf-8", errors="replace")
        except Exception as e:
            logger.error("Failed to parse document %s: %s", filename, e)
            raise ValueError(f"Failed to parse document: {str(e)}")

        if not text.strip():
            raise ValueError("No text could be extracted from the document")

        # Split text into manageable chunks
        chunks = self.text_splitter.split_text(text)
        
        # Vectorize
        embeddings = self.vector_store.embed_texts(chunks)
        
        # Prepare metadata for each chunk
        metadatas = [
            {"document_id": document_id, "filename": filename, "chunk_index": i}
            for i in range(len(chunks))
        ]
        
        ids = [str(uuid.uuid4()) for _ in chunks]
        
        # Save to Qdrant
        await self.vector_store.add_documents(
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info("Ingested %s into %d chunks with document_id=%s", filename, len(chunks), document_id)
        
        return {
            "document_id": document_id, 
            "filename": filename,
            "chunks_processed": len(chunks)
        }

    async def delete_document(self, document_id: str) -> None:
        """Deletes all vector chunks associated with the document_id."""
        if hasattr(self.vector_store, "delete_by_document_id"):
            await self.vector_store.delete_by_document_id(document_id)
        else:
            logger.warning("Configured VectorStore does not support delete_by_document_id")
