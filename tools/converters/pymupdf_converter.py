from typing import Optional
import pymupdf4llm
from .base_converter import BaseConverter

class PyMuPDFConverter(BaseConverter):
    """PyMuPDF4LLM Implementierung des Dokumentenkonverters"""
    
    def convert_to_markdown(self, file_path: str) -> Optional[str]:
        try:
            return pymupdf4llm.to_markdown(file_path)
        except Exception as e:
            print(f"Fehler bei der Konvertierung mit PyMuPDF4LLM: {e}")
            return None
