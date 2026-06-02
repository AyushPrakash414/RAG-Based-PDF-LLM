"""
Abstract interface for vector store backends.

All retrieval logic depends on this abstraction,
enabling future swaps to Pinecone, Weaviate, or ChromaDB
without modifying service code.
"""

from abc import ABC, abstractmethod
from typing import Any


class VectorStore(ABC):
    """Abstract base class for vector store implementations."""

    @abstractmethod
    async def add_documents(
        self,
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
        ids: list[str],
    ) -> None:
        """
        Add documents with their embeddings and metadata to the store.

        Args:
            documents: List of raw text chunks.
            embeddings: Corresponding embedding vectors.
            metadatas: Metadata dicts for each document.
            ids: Unique identifiers for each document.
        """
        ...

    @abstractmethod
    async def search(
        self,
        query_embedding: list[float],
        k: int = 4,
        score_threshold: float = 0.0,
        allowed_document_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search for the most similar documents.

        Args:
            query_embedding: The embedding vector of the query.
            k: Number of results to return.
            score_threshold: Minimum similarity score to include.
            allowed_document_ids: List of document IDs the user is allowed to search.

        Returns:
            A list of dicts, each containing:
                - "content": str
                - "score": float
                - "metadata": dict
        """
        ...

    @abstractmethod
    async def delete_documents(self, ids: list[str]) -> None:
        """
        Delete documents by their IDs.

        Args:
            ids: List of document IDs to remove.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Verify the vector store connection is healthy.

        Returns:
            True if the store is reachable, False otherwise.
        """
        ...
