from typing import Optional
import logging
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from tools.converters.base_converter import BaseConverter

_log = logging.getLogger(__name__)

class IBMDoclingConverter(BaseConverter):
    """IBM Docling Implementierung des Dokumentenkonverters für PDF Dateien"""
    
    def convert_to_markdown(self, file_path: str) -> Optional[str]:
        """
        Konvertiert eine PDF-Datei zu Markdown.
        """
        try:
            # PDF-Pipeline-Optionen konfigurieren
            pipeline_options = PdfPipelineOptions(do_table_structure=True)  # Tabellenextraktion aktivieren
            pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE  # Präzise Tabellenerkennung
            pipeline_options.table_structure_options.do_cell_matching = True  # Bessere Spaltenzuordnung
            pipeline_options.do_ocr = True  # OCR aktivieren

            # DocumentConverter initialisieren
            doc_converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                }
            )

            # Dokument konvertieren
            result = doc_converter.convert(file_path)

            # Markdown-Export erzeugen
            if result and result.document:
                return result.document.export_to_markdown()
            return None
            
        except Exception as e:
            _log.error(f"Fehler bei der Konvertierung mit IBM Docling: {str(e)}")
            return None
