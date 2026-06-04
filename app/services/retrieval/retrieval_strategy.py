from abc import ABC, abstractmethod
from typing import Any

class RetrievalStrategy(ABC):
    """Abstract base class for retrieval strategies."""
    
    @abstractmethod
    async def retrieve(
        self,
        question: str,
        k: int = 4,
        score_threshold: float = 0.0,
        allowed_document_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Retrieves relevant documents.
        
        Args:
            question: The query string.
            k: Number of results to return.
            score_threshold: Minimum score threshold.
            allowed_document_ids: Filter by document IDs.
            
        Returns:
            A list of dictionary results with 'content', 'score', and 'metadata'.
        """
        pass
