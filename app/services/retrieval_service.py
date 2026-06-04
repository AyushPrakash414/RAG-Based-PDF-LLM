"""
Retrieval service for fetching relevant document chunks.

Single responsibility: query the vector store and return
structured retrieval results with confidence scoring.
Includes typo-tolerant retrieval via spell correction.
"""

import logging
from typing import Any

from app.interfaces.vector_store import VectorStore
from app.models.response_models import RetrievalResult
from app.providers.qdrant_vector_store import QdrantVectorStore
from app.services.spell_corrector import SpellCorrector

logger = logging.getLogger(__name__)


class RetrievalService:
    """
    Service responsible for retrieving relevant document chunks
    from the vector store with typo-tolerant query support.
    """

    def __init__(
        self,
        vector_store: QdrantVectorStore,
        spell_corrector: SpellCorrector | None = None,
    ) -> None:
        """
        Initialise the retrieval service.

        Args:
            vector_store: A concrete QdrantVectorStore instance
                          (uses embed_query for query embedding).
            spell_corrector: Optional spell corrector for typo tolerance.
        """
        self._vector_store = vector_store
        self._spell_corrector = spell_corrector

    async def retrieve(
        self,
        question: str,
        k: int = 4,
        score_threshold: float = 0.0,
        allowed_document_ids: list[str] | None = None,
    ) -> RetrievalResult:
        """
        Retrieve the top-k most relevant chunks for a question.

        Performs dual-query retrieval when spell correction produces
        a different query, merging results by best score.

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

        # Determine if we should also search with corrected query
        corrected_query = None
        if self._spell_corrector:
            corrected = self._spell_corrector.correct_query(question)
            if corrected.lower().strip() != question.lower().strip():
                corrected_query = corrected
                logger.info(
                    "Spell correction activated: '%s' → '%s'",
                    question[:60],
                    corrected[:60],
                )

        # Generate query embedding(s)
        query_embedding = self._vector_store.embed_query(question)

        # Search with original query
        results: list[dict[str, Any]] = await self._vector_store.search(
            query_embedding=query_embedding,
            k=k,
            score_threshold=score_threshold,
            allowed_document_ids=allowed_document_ids,
        )

        # If spell correction produced a different query, search with that too
        if corrected_query:
            corrected_embedding = self._vector_store.embed_query(corrected_query)
            corrected_results = await self._vector_store.search(
                query_embedding=corrected_embedding,
                k=k,
                score_threshold=score_threshold,
                allowed_document_ids=allowed_document_ids,
            )

            # Merge results: keep best score per unique content
            results = self._merge_results(results, corrected_results)

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
            r.get("metadata", {}).get("source",
                r.get("metadata", {}).get("filename", "unknown"))
            for r in results
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

    @staticmethod
    def _merge_results(
        original: list[dict[str, Any]],
        corrected: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Merge results from original and corrected queries.

        Deduplicates by content, keeping the higher score.
        Returns results sorted by score descending.
        """
        seen: dict[str, dict[str, Any]] = {}

        for r in original + corrected:
            content = r["content"]
            if content not in seen or r["score"] > seen[content]["score"]:
                seen[content] = r

        merged = sorted(seen.values(), key=lambda x: x["score"], reverse=True)
        return merged
