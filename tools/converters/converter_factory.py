from typing import Dict, Type
from .base_converter import BaseConverter
from .ibm_docling_converter import IBMDoclingConverter
from .pymupdf_converter import PyMuPDFConverter
from .pdfplumber_converter import PDFPlumberConverter

class ConverterFactory:
    """Factory-Klasse für die Erstellung von Dokumentenkonvertern"""
    
    _converters: Dict[str, Type[BaseConverter]] = {
        "IBMDocling (genau)": IBMDoclingConverter,
        "PyMuPDF4LLM (schnell)": PyMuPDFConverter,
        "PDFPlumber (robust)": PDFPlumberConverter
    }
    
    @classmethod
    def get_converter(cls, converter_name: str) -> BaseConverter:
        """
        Erstellt eine Instanz des gewählten Konverters
        
        Args:
            converter_name: Name des gewünschten Konverters
            
        Returns:
            BaseConverter: Instanz des gewählten Konverters
            
        Raises:
            ValueError: Wenn der Konverter nicht gefunden wurde
        """
        # Konvertiere alte Namen in neue Namen
        name_mapping = {
            "IBMDocling": "IBMDocling (genau)",
            "PyMuPDF4LLM": "PyMuPDF4LLM (schnell)",
            "IBMDocling Enhanced": "IBMDocling (genau)",
            "PDFPlumber": "PDFPlumber (robust)"
        }
        
        # Versuche den Namen zu mappen, falls es ein alter Name ist
        converter_name = name_mapping.get(converter_name, converter_name)
        
        converter_class = cls._converters.get(converter_name)
        if not converter_class:
            raise ValueError(f"Unbekannter Konverter: {converter_name}")
        return converter_class()
    
    @classmethod
    def register_converter(cls, name: str, converter_class: Type[BaseConverter]) -> None:
        """
        Registriert einen neuen Konverter
        
        Args:
            name: Name des Konverters
            converter_class: Konverter-Klasse die BaseConverter implementiert
        """
        cls._converters[name] = converter_class
