# Berufeanalyzer mit ESCO Support

Eine intelligente Streamlit-Anwendung zur automatisierten Analyse von Ausbildungsberufen und deren Mapping mit ESCO-Kompetenzen. Die Anwendung verarbeitet Rahmenlehrpläne und Ausbildungsrahmenpläne und ordnet die enthaltenen Lernziele den entsprechenden ESCO-Kompetenzen zu.

## 🚀 Features

- **📄 Dokumentenverarbeitung**
  - Unterstützung für Rahmenlehrpläne und Ausbildungsrahmenpläne im PDF-Format
  - Automatische Dokumenttyp-Erkennung
  - Intelligente Extraktion von Lernzielen und Zeiträumen
  - Unterstützung für Markdown-Dateien (.md)

- **🔄 Flexible Konvertierung**
  - Drei spezialisierte PDF-Konverter für optimale Ergebnisse:
    - **IBMDocling**: Höchste Genauigkeit, unterstützt viele Formate und OCR
    - **PyMuPDF4LLM**: Schnelle Verarbeitung von PDF
    - **PDFPlumber**: Robuste Extraktion von PDF

- **🧠 KI-gestützte Analyse**
  - Automatische ESCO-Kompetenz-Zuordnung
  - Intelligente Dokumenttyp-Erkennung
  - Kontextsensitive Analyse von Lernzielen

- **💾 Dateimanagement**
  - Upload mehrerer Dateien gleichzeitig
  - Bulk-Download als ZIP
  - Einfache Dateiverwaltung im Browser

- **📊 Strukturierte Ausgabe**
  - JSON-Export für detaillierte Analysen
  - CSV-Export für einfache Tabellenverarbeitung
  - Direkter Download der Ergebnisse

## 🛠 Installation

1. **Repository klonen**
   ```bash
   git clone [repository-url]
   cd BerufeanalyzerESCO
   ```

2. **Python-Umgebung einrichten** (Python 3.8 oder höher empfohlen)
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. **Abhängigkeiten installieren**
   ```bash
   pip install -r requirements.txt
   ```

## 🎯 Verwendung

1. **Anwendung starten**
   ```bash
   streamlit run app.py
   ```

2. **Konfiguration einrichten**
   - OpenAI API-Key eingeben (erforderlich)
   - LLM-Modell wählen:
     - `gpt-4o-mini`: Schneller, kostengünstiger
     - `gpt-4o`: Präziser, besser bei komplexen Analysen
   - PDF-Konverter entsprechend Ihren Bedürfnissen auswählen

3. **Dateien verarbeiten**
   - PDFs in den Datenordner hochladen
   - Verarbeitung starten
   - Ergebnisse im gewünschten Format herunterladen

## 📋 Ausgabeformate

### JSON-Format
Detaillierte, hierarchische Struktur mit allen Analyseergebnissen:
```json
{
    "dokumententyp": "Rahmenlehrplan/Ausbildungsrahmenplan",
    "beruf": {
        "dokumente_daten": {
            "berufsbezeichnung": "",
            "berufsbeschreibung": "",
            "lernfelder_ausbildungsteile": {
                "id": "",
                "titel": "",
                "beschreibung": "",
                "lernziele": [
                    {
                        "text": "",
                        "esco_kompetenzen": []
                    }
                ]
            }
        },
        "esco_daten": {
            "kompetenzen": [],
            "beschreibungen": {}
        }
    }
}
```

### CSV-Format
Flache Struktur für einfache Weiterverarbeitung:
- Dokumenttyp
- Berufsbezeichnung
- Lernfeld/Ausbildungsteil
- Lernziel
- Zugeordnete ESCO-Kompetenzen
- Konfidenz der Zuordnung

## 💡 Best Practices

1. **PDF-Konverter-Auswahl**
   - **IBMDocling**: Für komplexe Dokumente mit verschiedenen Formaten
   - **PyMuPDF4LLM**: Für standard PDF-Dokumente und schnelle Verarbeitung
   - **PDFPlumber**: Für problematische PDFs mit schwieriger Formatierung

2. **Optimale Ergebnisse**
   - Verwenden Sie qualitativ hochwertige PDF-Dokumente
   - Stellen Sie sicher, dass die PDFs textbasiert und nicht gescannt sind
   - Testen Sie verschiedene Konverter für optimale Ergebnisse

3. **Ressourcenmanagement**
   - Verarbeiten Sie große Dateien einzeln
   - Nutzen Sie den ZIP-Download für mehrere Ergebnisdateien
   - Löschen Sie nicht mehr benötigte Dateien über die Benutzeroberfläche

## ⚠️ Fehlerbehebung

- **PDF wird nicht erkannt**
  - Überprüfen Sie das Dateiformat
  - Versuchen Sie einen anderen PDF-Konverter
  - Stellen Sie sicher, dass die Datei nicht beschädigt ist

- **ESCO-Zuordnung ungenau**
  - Prüfen Sie die Textqualität der PDF-Extraktion
  - Verwenden Sie einen genaueren PDF-Konverter
  - Überprüfen Sie die Lernziel-Formulierungen

- **Verarbeitung schlägt fehl**
  - Überprüfen Sie den API-Key
  - Stellen Sie sicher, dass alle Ordner existieren
  - Prüfen Sie die Internetverbindung für ESCO-API-Zugriff

## 📝 Lizenz

[Ihre Lizenz hier]

## 🤝 Mitwirken

Beiträge sind willkommen! Bitte beachten Sie:
1. Fork des Repositories
2. Feature-Branch erstellen
3. Änderungen committen
4. Pull Request erstellen
