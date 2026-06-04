"""
Unit tests for the source citation fix (Issue 1).

Verifies that:
1. Ingestion stores both "filename" and "source" in metadata
2. Retrieval correctly extracts source from metadata
3. Backward compatibility: old data with only "filename" still works
4. Edge cases: missing metadata, empty filename
"""

import pytest
import pytest_asyncio
import asyncio
import uuid

from tests.conftest import (
    MockVectorStore,
    FakeUploadFile,
    create_test_pdf,
    create_test_docx,
    create_test_txt,
)
from app.services.ingestion_service import IngestionService
from app.services.retrieval_service import RetrievalService


class TestCitationIngestion:
    """Test that ingestion correctly stores source metadata."""

    @pytest.fixture
    def svc(self):
        vs = MockVectorStore()
        return IngestionService(vector_store=vs), vs

    @pytest.mark.asyncio
    async def test_pdf_ingestion_stores_source(self, svc):
        """PDF ingestion must store 'source' key in metadata."""
        ingestion, vs = svc
        pdf_bytes = create_test_pdf("Spring Boot is a Java framework.")
        file = FakeUploadFile("myreport.pdf", pdf_bytes)
        doc_id = str(uuid.uuid4())

        await ingestion.ingest_file(file, doc_id)

        assert len(vs._documents) > 0
        for doc in vs._documents:
            assert "source" in doc["metadata"], "Metadata must contain 'source'"
            assert doc["metadata"]["source"] == "myreport.pdf"
            assert doc["metadata"]["filename"] == "myreport.pdf"

    @pytest.mark.asyncio
    async def test_docx_ingestion_stores_source(self, svc):
        """DOCX ingestion must store 'source' key in metadata."""
        ingestion, vs = svc
        docx_bytes = create_test_docx("Machine learning is a subset of AI.")
        file = FakeUploadFile("thesis.docx", docx_bytes)
        doc_id = str(uuid.uuid4())

        await ingestion.ingest_file(file, doc_id)

        assert len(vs._documents) > 0
        for doc in vs._documents:
            assert doc["metadata"]["source"] == "thesis.docx"
            assert doc["metadata"]["filename"] == "thesis.docx"

    @pytest.mark.asyncio
    async def test_txt_ingestion_stores_source(self, svc):
        """TXT ingestion must store 'source' key in metadata."""
        ingestion, vs = svc
        txt_bytes = create_test_txt("Artificial intelligence and neural networks.")
        file = FakeUploadFile("notes.txt", txt_bytes)
        doc_id = str(uuid.uuid4())

        await ingestion.ingest_file(file, doc_id)

        assert len(vs._documents) > 0
        for doc in vs._documents:
            assert doc["metadata"]["source"] == "notes.txt"

    @pytest.mark.asyncio
    async def test_source_equals_filename(self, svc):
        """Source and filename must always be the same value."""
        ingestion, vs = svc
        pdf_bytes = create_test_pdf("Test content for verification.")
        file = FakeUploadFile("report_2024.pdf", pdf_bytes)
        doc_id = str(uuid.uuid4())

        await ingestion.ingest_file(file, doc_id)

        for doc in vs._documents:
            assert doc["metadata"]["source"] == doc["metadata"]["filename"]

    @pytest.mark.asyncio
    async def test_document_id_stored(self, svc):
        """Document ID must be stored in metadata."""
        ingestion, vs = svc
        txt_bytes = create_test_txt("Some test content here.")
        file = FakeUploadFile("doc.txt", txt_bytes)
        doc_id = "test-doc-id-123"

        await ingestion.ingest_file(file, doc_id)

        for doc in vs._documents:
            assert doc["metadata"]["document_id"] == doc_id


class TestCitationRetrieval:
    """Test that retrieval correctly extracts source from metadata."""

    @pytest.mark.asyncio
    async def test_retrieval_reads_source_key(self):
        """Retrieval must read 'source' from metadata when present."""
        vs = MockVectorStore()
        # Manually add a document with source metadata
        await vs.add_documents(
            documents=["Spring Boot tutorial content"],
            embeddings=[[0.1] * 384],
            metadatas=[{"document_id": "doc1", "source": "tutorial.pdf", "filename": "tutorial.pdf"}],
            ids=["id1"],
        )

        svc = RetrievalService(vector_store=vs)
        result = await svc.retrieve("What is Spring Boot?", k=4, allowed_document_ids=["doc1"])

        assert len(result.sources) > 0
        assert result.sources[0] == "tutorial.pdf"
        assert "unknown" not in result.sources

    @pytest.mark.asyncio
    async def test_retrieval_fallback_to_filename(self):
        """Retrieval must fall back to 'filename' when 'source' is missing (legacy data)."""
        vs = MockVectorStore()
        # Simulate old data that only has "filename" (no "source")
        await vs.add_documents(
            documents=["Legacy document about MongoDB"],
            embeddings=[[0.1] * 384],
            metadatas=[{"document_id": "doc2", "filename": "old_data.pdf"}],
            ids=["id2"],
        )

        svc = RetrievalService(vector_store=vs)
        result = await svc.retrieve("MongoDB query", k=4, allowed_document_ids=["doc2"])

        assert len(result.sources) > 0
        assert result.sources[0] == "old_data.pdf"
        assert "unknown" not in result.sources

    @pytest.mark.asyncio
    async def test_retrieval_unknown_only_when_genuinely_missing(self):
        """'unknown' should only appear when neither source nor filename exists."""
        vs = MockVectorStore()
        # Document with no source metadata at all
        await vs.add_documents(
            documents=["Orphan content with no source info"],
            embeddings=[[0.1] * 384],
            metadatas=[{"document_id": "doc3"}],
            ids=["id3"],
        )

        svc = RetrievalService(vector_store=vs)
        result = await svc.retrieve("orphan", k=4, allowed_document_ids=["doc3"])

        assert len(result.sources) > 0
        assert result.sources[0] == "unknown"

    @pytest.mark.asyncio
    async def test_retrieval_no_results(self):
        """Empty retrieval should return empty sources list."""
        vs = MockVectorStore()
        svc = RetrievalService(vector_store=vs)
        result = await svc.retrieve("nonexistent", k=4)

        assert result.sources == []
        assert result.chunks == []
        assert result.retrieval_confidence == 0.0

    @pytest.mark.asyncio
    async def test_end_to_end_ingest_then_retrieve(self):
        """Full pipeline: ingest a file, then retrieve — source must not be 'unknown'."""
        vs = MockVectorStore()
        ingestion = IngestionService(vector_store=vs)
        retrieval = RetrievalService(vector_store=vs)

        # Ingest
        pdf_bytes = create_test_pdf("Spring Boot microservices architecture patterns.")
        file = FakeUploadFile("architecture.pdf", pdf_bytes)
        doc_id = "e2e-doc-id"
        await ingestion.ingest_file(file, doc_id)

        # Retrieve
        result = await retrieval.retrieve(
            "microservices", k=4, allowed_document_ids=[doc_id]
        )

        assert len(result.chunks) > 0
        assert all(s != "unknown" for s in result.sources), \
            f"All sources must be non-unknown, got: {result.sources}"
        assert all(s == "architecture.pdf" for s in result.sources)
