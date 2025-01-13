from abc import ABC, abstractmethod
from typing import Optional

class BaseConverter(ABC):
    """Basisklasse für alle Dokumentenkonverter"""
    
    @abstractmethod
    def convert_to_markdown(self, file_path: str) -> Optional[str]:
        """
        Konvertiert eine Datei in Markdown-Format
        
        Args:
            file_path: Pfad zur Eingabedatei
            
        Returns:
            Optional[str]: Markdown-Text oder None bei Fehler
        """
        pass
