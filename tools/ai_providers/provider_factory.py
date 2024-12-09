from typing import Dict, Type
from .base_provider import BaseAIProvider
from .openai_provider import OpenAIProvider

class AIProviderFactory:
    """Factory-Klasse für die Erstellung von KI-Providern"""
    
    _providers: Dict[str, Type[BaseAIProvider]] = {
        'OpenAI': OpenAIProvider
    }
    
    @classmethod
    def get_provider(cls, provider_name: str) -> BaseAIProvider:
        """
        Erstellt eine Instanz des gewählten KI-Providers
        
        Args:
            provider_name: Name des gewünschten Providers
            
        Returns:
            BaseAIProvider: Instanz des gewählten Providers
            
        Raises:
            ValueError: Wenn der Provider nicht gefunden wurde
        """
        provider_class = cls._providers.get(provider_name)
        if not provider_class:
            raise ValueError(f"Unbekannter KI-Provider: {provider_name}")
        return provider_class()
    
    @classmethod
    def register_provider(cls, name: str, provider_class: Type[BaseAIProvider]):
        """
        Registriert einen neuen KI-Provider
        
        Args:
            name: Name des Providers
            provider_class: Provider-Klasse die BaseAIProvider implementiert
        """
        cls._providers[name] = provider_class
