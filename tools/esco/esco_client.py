import requests
from typing import Dict, List, Optional, Tuple, Any
import json

class ESCOClient:
    """Client für die ESCO API Integration"""
    
    def __init__(self):
        self.base_url = "https://ec.europa.eu/esco/api"
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    def get_occupation(self, berufsbild_name: str) -> Optional[Dict[str, Any]]:
        """
        Sucht nach einem Beruf in ESCO basierend auf dem Berufsbildnamen
        
        Args:
            berufsbild_name: Name des Berufsbildes
            
        Returns:
            Optional[Dict[str, Any]]: Gefundener Beruf oder None
        """
        try:
            # Suche nach dem Beruf
            search_url = f"{self.base_url}/search"
            params = {
                'text': berufsbild_name,
                'type': 'occupation',
                'language': 'de',
                'full': 'true',
                'limit': 3  # Hole die Top 3 Treffer
            }
            
            response = requests.get(search_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if not data.get('_embedded', {}).get('results', []):
                print(f"Kein passender Beruf gefunden für: {berufsbild_name}")
                return None
            
            # Nimm den ersten Treffer
            occupation = data['_embedded']['results'][0]
            return {
                "uri": occupation['uri'],
                "title": occupation['preferredLabel'].get('de', occupation['preferredLabel'].get('en', '')),
                "description": occupation.get('description', {}).get('de', occupation.get('description', {}).get('en', ''))
            }
            
        except Exception as e:
            print(f"Fehler bei der ESCO-Berufssuche: {e}")
            return None
    
    def get_skills(self, occupation_uri: str) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
        """
        Holt die wesentlichen und optionalen Kompetenzen für einen Beruf
        
        Args:
            occupation_uri: URI des Berufs
            
        Returns:
            Tuple[List[Dict[str, str]], List[Dict[str, str]]]: (Wesentliche Kompetenzen, Optionale Kompetenzen)
        """
        try:
            essential_skills = []
            optional_skills = []
            
            # Hole die Kompetenzen für beide Typen
            for skill_type in ['hasEssentialSkill', 'hasOptionalSkill']:
                skills_url = f"{self.base_url}/resource/related"
                params = {
                    'uri': occupation_uri,
                    'relation': skill_type,
                    'language': 'de',
                    'full': 'true',
                    'limit': 100  # Maximale Anzahl von Kompetenzen
                }
                
                response = requests.get(skills_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                skills = data.get('_embedded', {}).get(skill_type, [])
                
                for skill in skills:
                    skill_info = {
                        "name": skill['preferredLabel'].get('de', skill['preferredLabel'].get('en', '')),
                        "description": skill.get('description', {}).get('de', skill.get('description', {}).get('en', '')),
                        "uri": skill['uri']
                    }
                    
                    if skill_type == 'hasEssentialSkill':
                        essential_skills.append(skill_info)
                    else:
                        optional_skills.append(skill_info)
            
            return essential_skills, optional_skills
            
        except Exception as e:
            print(f"Fehler beim Abrufen der ESCO-Kompetenzen: {e}")
            return [], []
