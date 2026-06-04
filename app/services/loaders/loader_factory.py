from .document_loader import DocumentLoader
from .pdf_loader import PDFLoader
from .docx_loader import DOCXLoader
from .txt_loader import TXTLoader

class LoaderFactory:
    """Factory for creating document loaders based on file extensions."""
    
    @staticmethod
    def get_loader(filename: str) -> DocumentLoader:
        """
        Returns the appropriate DocumentLoader for the given filename.
        
        Args:
            filename: The name of the file to load.
            
        Returns:
            An instance of a DocumentLoader subclass.
            
        Raises:
            ValueError: If the file extension is not supported.
        """
        filename_lower = filename.lower()
        if filename_lower.endswith(".pdf"):
            return PDFLoader()
        elif filename_lower.endswith(".docx"):
            return DOCXLoader()
        elif filename_lower.endswith(".txt") or filename_lower.endswith(".md"):
            return TXTLoader()
        else:
            raise ValueError(f"Unsupported file type: {filename}")
