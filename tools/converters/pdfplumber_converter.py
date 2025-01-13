from typing import Optional
import logging
import pdfplumber
import pandas as pd
from pdfplumber.utils import extract_text, get_bbox_overlap, obj_to_bbox
from tools.converters.base_converter import BaseConverter

_log = logging.getLogger(__name__)

class PDFPlumberConverter(BaseConverter):
    """PDFPlumber Implementierung des Dokumentenkonverters für PDF Dateien"""
    
    def convert_to_markdown(self, file_path: str) -> Optional[str]:
        """
        Konvertiert eine PDF-Datei zu Markdown mit festen Einstellungen.
        """
        try:
            # Feste Einstellungen für die Tabellenerkennung
            table_settings = {
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
                "snap_tolerance": 3,
                "join_tolerance": 3,
                "min_words_vertical": 1,
                "min_words_horizontal": 1
            }
            
            all_text = []
            
            with pdfplumber.open(file_path) as pdf:
                # Verarbeite alle Seiten
                for page in pdf.pages:
                    filtered_page = page
                    chars = filtered_page.chars

                    # Tabellen auf der Seite finden und extrahieren
                    for table in page.find_tables(table_settings):
                        # Erster Charakter in der Tabelle
                        first_table_char = page.crop(table.bbox).chars[0]
                        
                        # Tabelle aus der Seite filtern, um Text zu erhalten
                        filtered_page = filtered_page.filter(lambda obj: 
                            get_bbox_overlap(obj_to_bbox(obj), table.bbox) is None
                        )
                        chars = filtered_page.chars

                        # Tabelle in Markdown konvertieren
                        df = pd.DataFrame(table.extract())
                        if not df.empty:
                            df.columns = df.iloc[0]
                            markdown = df.drop(0).to_markdown(index=False)
                            # Tabelle dem Text hinzufügen
                            chars.append(first_table_char | {"text": markdown})

                    # Text extrahieren und Layout erhalten
                    page_text = extract_text(chars, layout=True)
                    all_text.append(page_text)

            return "\n".join(all_text)
            
        except Exception as e:
            _log.error(f"Fehler bei der Konvertierung mit PDFPlumber: {str(e)}")
            return None
