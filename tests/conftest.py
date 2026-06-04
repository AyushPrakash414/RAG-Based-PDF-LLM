"""
Shared test fixtures for the RAG system test suite.

Provides mock implementations of LLM providers, vector stores,
and test utility functions.
"""

import asyncio
import io
import json
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from app.config.settings import Settings
from app.interfaces.llm_provider import LLMProvider
from app.interfaces.vector_store import VectorStore
from app.services.ingestion_service import IngestionService
from app.services.retrieval_service import RetrievalService
from app.services.retrieval.vector_search_strategy import VectorSearchStrategy
from app.services.spell_corrector import SpellCorrector


# ---------------------------------------------------------------------------
# Test Settings
# ---------------------------------------------------------------------------

@pytest.fixture
def test_settings() -> Settings:
    """Settings configured for testing."""
    return Settings(
        groq_api_key="test-key-not-real",
        groq_model="test-model",
        qdrant_url="http://localhost:6333",
        qdrant_collection_name="test_collection",
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        embedding_dimension=384,
        top_k=4,
        similarity_threshold=0.3,
        max_retries=3,
        critic_approval_threshold=0.6,
        retrieval_validation_threshold=0.5,
        documents_dir="test_documents",
        traces_dir="test_traces",
        prompts_dir="app/prompts",
        log_level="DEBUG",
        internal_api_secret="test-secret-for-testing-only",
    )


# ---------------------------------------------------------------------------
# Mock LLM Provider
# ---------------------------------------------------------------------------

class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""

    def __init__(self, responses: list[str] | None = None):
        self._responses = responses or ['{"grounded": true, "confidence": 0.9, "reason": "test", "verdict": "APPROVED"}']
        self._call_count = 0

    async def generate(self, prompt: str, temperature: float | None = None) -> str:
        idx = min(self._call_count, len(self._responses) - 1)
        self._call_count += 1
        return self._responses[idx]

    async def health_check(self) -> bool:
        return True


@pytest.fixture
def mock_llm():
    """Provide a mock LLM provider."""
    return MockLLMProvider()


# ---------------------------------------------------------------------------
# Mock Vector Store
# ---------------------------------------------------------------------------

class MockVectorStore(VectorStore):
    """Mock vector store for testing."""

    def __init__(self):
        self._documents: list[dict] = []
        self._embed_call_count = 0

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Return fake embeddings."""
        self._embed_call_count += 1
        return [[0.1] * 384 for _ in texts]

    def embed_query(self, query: str) -> list[float]:
        """Return fake query embedding."""
        return [0.1] * 384

    async def add_documents(
        self,
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
        ids: list[str],
    ) -> None:
        for doc, emb, meta, id_ in zip(documents, embeddings, metadatas, ids):
            self._documents.append({
                "id": id_,
                "content": doc,
                "embedding": emb,
                "metadata": meta,
            })

    async def search(
        self,
        query_embedding: list[float],
        k: int = 4,
        score_threshold: float = 0.0,
        allowed_document_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        results = []
        for doc in self._documents:
            if allowed_document_ids:
                if doc["metadata"].get("document_id") not in allowed_document_ids:
                    continue
            results.append({
                "content": doc["content"],
                "score": 0.85,
                "metadata": doc["metadata"],
            })
        return results[:k]

    async def delete_documents(self, ids: list[str]) -> None:
        self._documents = [d for d in self._documents if d["id"] not in ids]

    async def delete_by_document_id(self, document_id: str) -> None:
        self._documents = [
            d for d in self._documents
            if d["metadata"].get("document_id") != document_id
        ]

    async def health_check(self) -> bool:
        return True


@pytest.fixture
def mock_vector_store():
    """Provide a mock vector store."""
    return MockVectorStore()


# ---------------------------------------------------------------------------
# Service Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def ingestion_service(mock_vector_store):
    """Provide an ingestion service with mock vector store."""
    return IngestionService(vector_store=mock_vector_store)


@pytest.fixture
def spell_corrector():
    """Provide a spell corrector instance."""
    return SpellCorrector(max_edit_distance=2)


@pytest.fixture
def retrieval_service(mock_vector_store, spell_corrector):
    """Provide a retrieval service with mock vector store and spell corrector."""
    strategy = VectorSearchStrategy(mock_vector_store)
    return RetrievalService(
        strategy=strategy,
        spell_corrector=spell_corrector
    )


# ---------------------------------------------------------------------------
# Test File Generators
# ---------------------------------------------------------------------------

def create_test_pdf(text: str = "This is test PDF content about Spring Boot and MongoDB.") -> bytes:
    """Create a minimal valid PDF file in memory."""
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def create_test_docx(text: str = "This is test DOCX content about machine learning.") -> bytes:
    """Create a minimal valid DOCX file in memory."""
    import docx
    doc = docx.Document()
    doc.add_paragraph(text)
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def create_test_txt(text: str = "This is test TXT content about artificial intelligence.") -> bytes:
    """Create test TXT content."""
    return text.encode("utf-8")


class FakeUploadFile:
    """Fake UploadFile for testing without FastAPI."""

    def __init__(self, filename: str, content: bytes, content_type: str = "application/octet-stream"):
        self.filename = filename
        self.content_type = content_type
        self._content = content

    async def read(self) -> bytes:
        return self._content
