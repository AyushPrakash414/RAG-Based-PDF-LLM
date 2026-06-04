import asyncio
from typing import AsyncGenerator
from .document_loader import DocumentLoader

class TXTLoader(DocumentLoader):
    """Loader for plain text files."""
    
    def __init__(self, window_size: int = 50_000):
        self._window_size = window_size

    async def load(self, file_content: bytes) -> AsyncGenerator[tuple[str, float], None]:
        text = file_content.decode("utf-8", errors="replace")
        
        if not text.strip():
            raise ValueError("No text could be extracted from the document")
            
        total_len = len(text)
        
        for start_idx in range(0, total_len, self._window_size):
            end_idx = min(start_idx + self._window_size, total_len)
            window_text = text[start_idx:end_idx]
            
            progress_pct = (end_idx / total_len) * 100
            
            yield window_text, progress_pct
            
            await asyncio.sleep(0)
