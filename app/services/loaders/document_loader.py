from abc import ABC, abstractmethod
from typing import AsyncGenerator

class DocumentLoader(ABC):
    """Abstract base class for document loaders."""
    
    @abstractmethod
    async def load(self, file_content: bytes) -> AsyncGenerator[tuple[str, float], None]:
        """
        Parses the file and yields windows of text along with progress percentage.
        
        Args:
            file_content: The raw bytes of the file.
            
        Yields:
            A tuple of (extracted_text_window, progress_percentage).
        """
        pass
