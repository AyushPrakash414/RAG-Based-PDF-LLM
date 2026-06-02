"""
Retrieval service for fetching relevant document chunks.

Single responsibility: query the vector store and return
structured retrieval results with confidence scoring.
"""

import logging
from typing import Any

from app.interfaces.vector_store import VectorStore
from app.models.response_models import RetrievalResult
from app.providers.qdrant_vector_store import QdrantVectorStore

logger = logging.getLogger(__name__)


class RetrievalService:
    """
    Service responsible for retrieving relevant document chunks
    from the vector store.
    """

    def __init__(self, vector_store: QdrantVectorStore) -> None:
        """
        Initialise the retrieval service.

        Args:
            vector_store: A concrete QdrantVectorStore instance
                          (uses embed_query for query embedding).
        """
        self._vector_store = vector_store

    async def retrieve(
        self,
        question: str,
        k: int = 4,
        score_threshold: float = 0.0,
        allowed_document_ids: list[str] | None = None,
    ) -> RetrievalResult:
        """
        Retrieve the top-k most relevant chunks for a question.

        Args:
            question: The user's question (or rewritten query).
            k: Number of chunks to retrieve.
            score_threshold: Minimum similarity score to include.
            allowed_document_ids: List of document IDs the user is allowed to search.

        Returns:
            A RetrievalResult with chunks, scores, sources,
            and an overall retrieval_confidence.
        """
        logger.info(
            "Retrieving chunks: question='%s', k=%d, threshold=%.2f",
            question[:80],
            k,
            score_threshold,
        )

        # Generate query embedding
        query_embedding = self._vector_store.embed_query(question)

        # Search the vector store
        print(f"DEBUG: Executing Qdrant search with k={k}, allowed_document_ids={allowed_document_ids}")
        results: list[dict[str, Any]] = await self._vector_store.search(
            query_embedding=query_embedding,
            k=k,
            score_threshold=score_threshold,
            allowed_document_ids=allowed_document_ids,
        )
        print(f"DEBUG: Qdrant returned {len(results)} chunks")

        if not results:
            logger.warning("No chunks retrieved for question: '%s'", question[:80])
            return RetrievalResult(
                chunks=[],
                scores=[],
                sources=[],
                retrieval_confidence=0.0,
            )

        chunks = [r["content"] for r in results]
        scores = [r["score"] for r in results]
        sources = [
            r.get("metadata", {}).get("source", "unknown") for r in results
        ]

        # Calculate retrieval confidence as the mean of top scores
        retrieval_confidence = sum(scores) / len(scores) if scores else 0.0
        # Clamp to [0, 1]
        retrieval_confidence = max(0.0, min(1.0, retrieval_confidence))

        logger.info(
            "Retrieved %d chunks, retrieval_confidence=%.3f, sources=%s",
            len(chunks),
            retrieval_confidence,
            list(set(sources)),
        )

        return RetrievalResult(
            chunks=chunks,
            scores=scores,
            sources=sources,
            retrieval_confidence=retrieval_confidence,
        )
