import time
from typing import List, Dict, Any, Optional
from openai import OpenAI
from .base_provider import BaseAIProvider

class OpenAIProvider(BaseAIProvider):
    """OpenAI API Implementierung"""
    
    def __init__(self):
        self.client = None
        self.available_models = [
            'gpt-4',
            'gpt-4-turbo-preview',
            'gpt-3.5-turbo',
            'gpt-3.5-turbo-16k'
        ]
    
    def initialize(self, api_key: str) -> None:
        """Initialisiert den OpenAI Client"""
        self.client = OpenAI(api_key=api_key)
    
    def analyze_text(self,
                    text: str,
                    prompt_template: str,
                    model: str,
                    max_retries: int = 3,
                    temperature: float = 0.7,
                    **kwargs) -> Optional[str]:
        """
        Analysiert Text mit OpenAI API
        
        Args:
            text: Zu analysierender Text
            prompt_template: Template für den Prompt
            model: OpenAI Modell
            max_retries: Maximale Anzahl von Wiederholungsversuchen
            temperature: Kreativität der Antworten (0.0 - 1.0)
            **kwargs: Weitere Parameter für die OpenAI API
        """
        if not self.client:
            raise ValueError("OpenAI Client nicht initialisiert. Bitte initialize() aufrufen.")
            
        retry_count = 0
        while retry_count < max_retries:
            try:
                messages = [
                    {"role": "system", "content": prompt_template},
                    {"role": "user", "content": text}
                ]
                
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    **kwargs
                )
                
                return response.choices[0].message.content
                
            except Exception as e:
                retry_count += 1
                if retry_count == max_retries:
                    print(f"Fehler bei OpenAI Anfrage nach {max_retries} Versuchen: {e}")
                    return None
                print(f"Fehler bei OpenAI Anfrage (Versuch {retry_count}): {e}")
                time.sleep(1)  # Kurze Pause vor erneutem Versuch
    
    def get_available_models(self) -> List[str]:
        """Gibt die Liste der verfügbaren OpenAI Modelle zurück"""
        return self.available_models.copy()
