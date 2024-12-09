# Berufeanalyzer mit ESCO Support

Eine Streamlit-Anwendung zur Analyse von Ausbildungsberufen und deren Mapping mit ESCO-Kompetenzen.

## Features

- **PDF-Verarbeitung**: Unterstützt die Verarbeitung von Rahmenlehrplänen und Ausbildungsrahmenplänen
- **Dokumententyp-Erkennung**: Automatische Erkennung des Dokumenttyps (Rahmenlehrplan/Ausbildungsrahmenplan)
- **ESCO-Integration**: Automatische Zuordnung von Lernzielen zu ESCO-Kompetenzen
- **Flexible Konvertierung**: Mehrere PDF-Konverter-Optionen für optimale Textextraktion
  - IBMDocling (genau)
  - PyMuPDF4LLM (schnell)
  - PDFPlumber (robust)
- **Strukturierte Ausgabe**: Export der Ergebnisse in JSON und CSV Format

## Installation

1. Klonen Sie das Repository
2. Installieren Sie die erforderlichen Pakete:
```bash
pip install -r requirements.txt
```

## Verwendung

1. Starten Sie die Anwendung:
```bash
streamlit run main.py
```

2. Konfigurieren Sie die Einstellungen:
   - OpenAI API Key
   - LLM-Modell (GPT-3.5/GPT-4)
   - PDF-Konverter
   - Prompt-Einstellungen (optional)

3. Laden Sie die zu verarbeitenden PDF-Dokumente hoch

4. Die Anwendung:
   - Extrahiert die Textinhalte
   - Erkennt den Dokumenttyp
   - Identifiziert Lernziele und Zeiträume
   - Ordnet ESCO-Kompetenzen zu
   - Speichert die Ergebnisse strukturiert

## Ausgabeformate

### JSON-Struktur
```json
{
    "dokumententyp": "Rahmenlehrplan/Ausbildungsrahmenplan",
    "beruf": {
        "dokumente_daten": {
            "berufsbezeichnung": "",
            "berufsbeschreibung": "",
            "lernfelder_ausbildungsteile": {
                // Strukturierte Lernziele mit ESCO-Mappings
            }
        },
        "esco_daten": {
            // ESCO-Kompetenzen und Beschreibungen
        }
    }
}
```

### CSV-Format
- Flache Struktur für einfache Tabellenverarbeitung
- Enthält alle Lernziele mit zugeordneten ESCO-Kompetenzen

## Technische Details

- **Frontend**: Streamlit
- **LLM-Integration**: OpenAI GPT-3.5/GPT-4
- **ESCO-API**: Direkte Integration mit der ESCO-REST-API
- **PDF-Verarbeitung**: Mehrere Konverter für optimale Ergebnisse

## Hinweise

- Stellen Sie sicher, dass ein gültiger OpenAI API-Key konfiguriert ist
- Die Qualität der ESCO-Zuordnungen hängt von der Textqualität der PDF-Extraktion ab
- Wählen Sie den PDF-Konverter entsprechend Ihrer Anforderungen an Geschwindigkeit und Genauigkeit
