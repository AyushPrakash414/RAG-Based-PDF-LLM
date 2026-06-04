from typing import Any
from app.providers.qdrant_vector_store import QdrantVectorStore
from .retrieval_strategy import RetrievalStrategy

class BM25SearchStrategy(RetrievalStrategy):
    """Retrieves documents using sparse vectors for keyword matching."""
    
    def __init__(self, vector_store: QdrantVectorStore):
        self._vector_store = vector_store
        
    async def retrieve(
        self,
        question: str,
        k: int = 4,
        score_threshold: float = 0.0,
        allowed_document_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        # TODO: Implement sparse embedding and search via Qdrant's Sparse Vectors API
        raise NotImplementedError("BM25 sparse search is not yet implemented.")
