"""
Qdrant vector store implementation.

Implements the VectorStore interface using the qdrant-client
SDK for document storage and similarity search.
"""

import asyncio
import logging
import uuid
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    PointStruct,
    VectorParams,
    Filter,
)
from fastembed import TextEmbedding

from app.interfaces.vector_store import VectorStore
from app.config.settings import Settings

logger = logging.getLogger(__name__)


class QdrantVectorStore(VectorStore):
    """
    Concrete vector store backed by Qdrant.

    Manages collection creation, document upsert,
    similarity search, and deletion.
    """

    def __init__(self, settings: Settings) -> None:
        """
        Initialise the Qdrant vector store.

        Args:
            settings: Application settings with Qdrant connection info.
        """
        self._settings = settings
        self._collection_name = settings.qdrant_collection_name

        # Initialise Qdrant client
        if settings.qdrant_api_key:
            self._client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key,
            )
        else:
            self._client = QdrantClient(url=settings.qdrant_url)

        # Initialise embedding model using fastembed for lower memory usage
        self._embedding_model = TextEmbedding(model_name=settings.embedding_model)
        self._embedding_dimension = settings.embedding_dimension

        # Ensure collection exists
        self._ensure_collection()

        logger.info(
            "QdrantVectorStore initialised: url=%s, collection=%s",
            settings.qdrant_url,
            self._collection_name,
        )

    def _ensure_collection(self) -> None:
        """Create the Qdrant collection if it does not already exist."""
        collections = self._client.get_collections().collections
        existing_names = [c.name for c in collections]

        if self._collection_name not in existing_names:
            self._client.create_collection(
                collection_name=self._collection_name,
                vectors_config=VectorParams(
                    size=self._embedding_dimension,
                    distance=Distance.COSINE,
                ),
            )
            logger.info("Created Qdrant collection: %s", self._collection_name)
        else:
            logger.info("Qdrant collection already exists: %s", self._collection_name)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a list of text strings.

        Args:
            texts: Text strings to embed.

        Returns:
            List of embedding vectors.
        """
        embeddings = list(self._embedding_model.embed(texts))
        return [emb.tolist() for emb in embeddings]

    def embed_query(self, query: str) -> list[float]:
        """
        Generate an embedding for a single query string.

        Args:
            query: The query text.

        Returns:
            The embedding vector.
        """
        # fastembed expects a list of strings and returns a generator of embeddings
        embeddings = list(self._embedding_model.embed([query]))
        return embeddings[0].tolist()

    async def add_documents(
        self,
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
        ids: list[str],
    ) -> None:
        """
        Upsert documents with embeddings and metadata into Qdrant.

        Args:
            documents: Raw text chunks.
            embeddings: Pre-computed embedding vectors.
            metadatas: Metadata for each chunk.
            ids: Unique string identifiers for each point.
        """
        points = []
        for doc, emb, meta, point_id in zip(
            documents, embeddings, metadatas, ids, strict=True
        ):
            # Store the text content in the payload alongside metadata
            payload = {**meta, "content": doc}
            points.append(
                PointStruct(
                    id=point_id,
                    vector=emb,
                    payload=payload,
                )
            )

        # Upsert in batches of 100
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            await asyncio.to_thread(
                self._client.upsert,
                collection_name=self._collection_name,
                points=batch,
            )

        logger.info(
            "Upserted %d documents into Qdrant collection '%s'",
            len(points),
            self._collection_name,
        )

    async def search(
        self,
        query_embedding: list[float],
        k: int = 4,
        score_threshold: float = 0.0,
    ) -> list[dict[str, Any]]:
        """
        Perform a similarity search in Qdrant.

        Args:
            query_embedding: The query embedding vector.
            k: Number of top results to return.
            score_threshold: Minimum similarity score to include.

        Returns:
            List of dicts with 'content', 'score', and 'metadata' keys.
        """
        results = await asyncio.to_thread(
            self._client.query_points,
            collection_name=self._collection_name,
            query=query_embedding,
            limit=k,
            score_threshold=score_threshold,
        )

        search_results: list[dict[str, Any]] = []
        for hit in results.points:
            payload = hit.payload or {}
            content = payload.pop("content", "")
            search_results.append(
                {
                    "content": content,
                    "score": hit.score,
                    "metadata": payload,
                }
            )

        logger.debug(
            "Qdrant search returned %d results (k=%d, threshold=%.2f)",
            len(search_results),
            k,
            score_threshold,
        )
        return search_results

    async def delete_documents(self, ids: list[str]) -> None:
        """
        Delete documents from Qdrant by their point IDs.

        Args:
            ids: List of point IDs to delete.
        """
        from qdrant_client.http.models import PointIdsList

        await asyncio.to_thread(
            self._client.delete,
            collection_name=self._collection_name,
            points_selector=PointIdsList(points=ids),
        )
        logger.info("Deleted %d points from Qdrant", len(ids))

    async def delete_by_document_id(self, document_id: str) -> None:
        """
        Delete all points belonging to a specific document ID.
        """
        from qdrant_client.http.models import Filter, FieldCondition, MatchValue

        await asyncio.to_thread(
            self._client.delete,
            collection_name=self._collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            ),
        )
        logger.info("Deleted all points for document %s from Qdrant", document_id)

    async def health_check(self) -> bool:
        """
        Check if Qdrant is reachable.

        Returns:
            True if the collection info can be retrieved.
        """
        try:
            info = await asyncio.to_thread(
                self._client.get_collection,
                collection_name=self._collection_name,
            )
            return info is not None
        except Exception as exc:
            logger.warning("Qdrant health check failed: %s", exc)
            return False
