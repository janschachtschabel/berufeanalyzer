from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseAIProvider(ABC):
    """Basisklasse für alle KI-Provider"""
    
    @abstractmethod
    def initialize(self, api_key: str) -> None:
        """
        Initialisiert den KI-Provider mit dem API-Key
        
        Args:
            api_key: Der API-Schlüssel für den Service
        """
        pass
    
    @abstractmethod
    def analyze_text(self, 
                    text: str, 
                    prompt_template: str,
                    model: str,
                    max_retries: int = 3,
                    **kwargs) -> Optional[str]:
        """
        Analysiert Text mit dem KI-Modell
        
        Args:
            text: Zu analysierender Text
            prompt_template: Template für den Prompt
            model: Name des zu verwendenden Modells
            max_retries: Maximale Anzahl von Wiederholungsversuchen
            **kwargs: Zusätzliche Parameter für den Provider
            
        Returns:
            Optional[str]: Analyseergebnis oder None bei Fehler
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        Gibt die Liste der verfügbaren Modelle zurück
        
        Returns:
            List[str]: Liste der Modellnamen
        """
        pass
