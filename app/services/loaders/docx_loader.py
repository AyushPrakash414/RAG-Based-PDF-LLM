import asyncio
from typing import AsyncGenerator
from .document_loader import DocumentLoader

class DOCXLoader(DocumentLoader):
    """Loader for DOCX documents using python-docx."""
    
    def __init__(self, batch_size: int = 50):
        self._batch_size = batch_size

    async def load(self, file_content: bytes) -> AsyncGenerator[tuple[str, float], None]:
        import docx
        import io
        
        doc = docx.Document(io.BytesIO(file_content))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        
        if not paragraphs:
            raise ValueError("No text could be extracted from the DOCX")
            
        total_batches = (len(paragraphs) + self._batch_size - 1) // self._batch_size
        
        for batch_idx in range(0, len(paragraphs), self._batch_size):
            batch_paras = paragraphs[batch_idx:batch_idx + self._batch_size]
            batch_text = "\n".join(batch_paras)
            
            current_batch = batch_idx // self._batch_size + 1
            progress_pct = (current_batch / total_batches) * 100
            
            yield batch_text, progress_pct
            
            await asyncio.sleep(0)
