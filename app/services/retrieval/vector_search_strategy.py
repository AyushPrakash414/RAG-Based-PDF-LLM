from typing import Any
from app.providers.qdrant_vector_store import QdrantVectorStore
from .retrieval_strategy import RetrievalStrategy

class VectorSearchStrategy(RetrievalStrategy):
    """Retrieves documents using dense vector semantic search."""
    
    def __init__(self, vector_store: QdrantVectorStore):
        self._vector_store = vector_store
        
    async def retrieve(
        self,
        question: str,
        k: int = 4,
        score_threshold: float = 0.0,
        allowed_document_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        
        query_embedding = self._vector_store.embed_query(question)
        
        return await self._vector_store.search(
            query_embedding=query_embedding,
            k=k,
            score_threshold=score_threshold,
            allowed_document_ids=allowed_document_ids,
        )
