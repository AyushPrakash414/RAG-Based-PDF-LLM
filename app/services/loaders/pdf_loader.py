import asyncio
from typing import AsyncGenerator
from .document_loader import DocumentLoader

class PDFLoader(DocumentLoader):
    """Loader for PDF documents using PyMuPDF."""
    
    def __init__(self, page_window_size: int = 5):
        self._page_window_size = page_window_size

    async def load(self, file_content: bytes) -> AsyncGenerator[tuple[str, float], None]:
        import fitz  # PyMuPDF
        
        doc = fitz.open(stream=file_content, filetype="pdf")
        total_pages = doc.page_count

        if total_pages == 0:
            doc.close()
            raise ValueError("PDF contains no pages")

        try:
            for window_start in range(0, total_pages, self._page_window_size):
                window_end = min(window_start + self._page_window_size, total_pages)
                
                window_text = ""
                for page_num in range(window_start, window_end):
                    page = doc[page_num]
                    window_text += page.get_text() + "\n"
                    
                progress_pct = (window_end / total_pages) * 100
                
                if window_text.strip():
                    yield window_text, progress_pct
                else:
                    # Still yield empty text so progress updates
                    yield "", progress_pct
                    
                await asyncio.sleep(0)
        finally:
            doc.close()
