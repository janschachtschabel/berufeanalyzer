import os
import time
import pandas as pd
import streamlit as st
import csv
from datetime import datetime
from typing import List, Any, Dict, Optional, Tuple
import warnings
import json
import pathlib
import requests
import shutil
from tools.converters.converter_factory import ConverterFactory
from tools.ai_providers.provider_factory import AIProviderFactory
from tools.esco.esco_client import ESCOClient

warnings.filterwarnings("ignore", message="`resume_download` is deprecated")
warnings.filterwarnings("ignore", message="`huggingface_hub` cache-system uses symlinks")

def print_status(message: str, color: str = 'green'):
    """Zeigt eine Statusmeldung an."""
    if not hasattr(st.session_state, 'status_container'):
        st.session_state.status_container = st.empty()
    
    with st.session_state.status_container:
        if color == 'red':
            st.error(message, icon="🚫")
        elif color == 'blue':
            st.info(message, icon="ℹ️")
        else:
            st.success(message, icon="✅")

def print_result(message: str):
    with st.container():
        st.markdown(f"<p>{message}</p>", unsafe_allow_html=True)

def save_csv(data: List[List[str]], output_path: str):
    try:
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=';')
            writer.writerow(["Dokumententyp", "Beruf", "Lernfelder/Ausbildungsteile", "Zeitraum", "Benötigte Zeit", "Lernziel"])
            for row in data:
                if len(row) >= 6:  # Ensure we have all required columns
                    writer.writerow([row[0], row[1], row[2], row[3], row[4], row[5]])
        print_status(f"CSV-Datei erfolgreich gespeichert: {output_path}", color='green')
    except Exception as e:
        print_status(f"Fehler beim Speichern der CSV-Datei {output_path}: {e}", 'red')

def call_openai(client: Any, messages: List[dict], model: str = 'gpt-3.5-turbo') -> Optional[str]:
    """Wrapper für OpenAI API Calls mit Retry-Logik"""
    try:
        response = client.analyze_text(
            text=messages[-1]["content"],
            prompt_template=messages[0]["content"],
            model=model
        )
        return response
    except Exception as e:
        print_status(f"Fehler beim OpenAI API Call: {e}", color='red')
        return None

def process_pdf_texts(pdf_file: str, converter: str) -> str:
    """Konvertiert PDF zu Markdown."""
    filename = os.path.basename(pdf_file)
    
    try:
        print_status(f"Konvertiere {filename} mit {converter}...", color='blue')
        # Hole den passenden Konverter über die Factory
        # Konvertiere alte Namen in neue Namen
        name_mapping = {
            "IBMDocling": "IBMDocling (genau)",
            "PyMuPDF4LLM": "PyMuPDF4LLM (schnell)",
            "PDFPlumber": "PDFPlumber (robust)"
        }
        converter = name_mapping.get(converter, converter)
        converter_instance = ConverterFactory.get_converter(converter)
        # Konvertiere die Datei
        md_text = converter_instance.convert_to_markdown(pdf_file)
        
        if md_text:
            # Speichere die Markdown-Datei im output Ordner
            output_path = os.path.join('output', os.path.splitext(filename)[0] + '.md')
            os.makedirs('output', exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(md_text)
            print_status(f"PDF-Konvertierung von {filename} erfolgreich abgeschlossen", color='green')
            return md_text
        else:
            print_status(f"Fehler bei der Konvertierung von {filename}: Keine Ausgabe erhalten", 'red')
            return ""
    except Exception as e:
        print_status(f"Fehler bei der Konvertierung von {filename}: {e}", 'red')
        return ""

def process_all_files(data_folder: str, api_key: str, selected_model: str, prompts: Dict[str, Any], output_folder: str, converter: str) -> (List[List[str]], List[str], List[str]):
    results = []
    json_paths = []
    csv_paths = []
    berufsbeschreibungen = {}  # Initialize berufsbeschreibungen dictionary
    
    # Initialisiere KI-Provider und ESCO Client
    ai_provider = AIProviderFactory.get_provider('OpenAI')
    ai_provider.initialize(api_key)
    esco_client = ESCOClient()
    
    # Konverter-Name bereinigen
    converter = converter.split()[0] if " " in converter else converter
    
    for root, dirs, files in os.walk(data_folder):
        for file in files:
            if file.endswith('.pdf') or file.endswith('.md'):
                source_path = os.path.join(root, file)
                filename = os.path.basename(source_path)
                
                # Verarbeitung der Datei
                if not hasattr(st.session_state, 'progress_container'):
                    st.session_state.progress_container = st.container()

                with st.session_state.progress_container:
                    # Progress header
                    st.subheader(f"Verarbeite: {filename}")
                    progress_text = st.empty()
                    
                    # Update progress
                    def update_progress(step: str):
                        progress_text.text(f"Schritt: {step}")
                    
                    update_progress("Konvertiere Datei")
                    
                    # Bestimme den Pfad für die Markdown-Datei
                    md_filename = os.path.splitext(filename)[0] + '.md'
                    md_output_path = os.path.join(output_folder, md_filename)
                    
                    # Prüfe ob bereits eine konvertierte Markdown-Datei existiert
                    if os.path.exists(md_output_path):
                        print_status(f"Verwende existierende Markdown-Datei: {md_output_path}", color='green')
                        with open(md_output_path, 'r', encoding='utf-8') as f:
                            md_text = f.read()
                    else:
                        # PDF zu Markdown konvertieren wenn nötig
                        if file.endswith('.pdf'):
                            md_text = process_pdf_texts(source_path, converter)
                            if not md_text:
                                continue
                            # Speichere die konvertierte Datei
                            with open(md_output_path, 'w', encoding='utf-8') as f:
                                f.write(md_text)
                            print_status(f"Neue Markdown-Datei erstellt: {md_output_path}", color='green')
                        else:  # .md Datei
                            try:
                                with open(source_path, 'r', encoding='utf-8') as f:
                                    md_text = f.read()
                            except Exception as e:
                                print_status(f"Fehler beim Lesen der Markdown-Datei {file}: {e}", 'red')
                                continue
                    
                    # 1. Dokumententyp bestimmen
                    update_progress("Bestimme Dokumententyp")
                    doc_type_messages = [
                        {"role": "system", "content": "Du bist ein hilfreicher Assistent."},
                        {"role": "user", "content": prompts["document_type_prompt"] + "\n\n" + md_text}
                    ]
                    document_type = call_openai(ai_provider, doc_type_messages, selected_model).strip()
                    if not document_type:
                        continue
                    
                    with st.expander("Erkannter Dokumententyp", expanded=False):
                        st.dataframe(pd.DataFrame([[document_type]], columns=["Dokumententyp"]))
                    
                    # 2. Name des Berufsbildes
                    update_progress("Analysiere Berufsbild")
                    prompts_set = "rahmenlehrplan_prompts" if document_type == "Rahmenlehrplan" else "ausbildungsrahmenplan_prompts"
                    berufsbild_messages = [
                        {"role": "system", "content": "Du bist ein hilfreicher Assistent."},
                        {"role": "user", "content": prompts[prompts_set]["berufsbild_query"] + "\n\n" + md_text}
                    ]
                    berufsbild_name = call_openai(ai_provider, berufsbild_messages, selected_model).strip()
                    if not berufsbild_name:
                        continue
                    
                    with st.expander("Erkanntes Berufsbild", expanded=False):
                        berufsbild_df = pd.DataFrame([[document_type, berufsbild_name]], 
                                                   columns=["Dokumententyp", "Berufsbild"])
                        st.dataframe(berufsbild_df, use_container_width=True)
                    
                    # 3. Berufsbeschreibung generieren
                    update_progress("Generiere Berufsbeschreibung")
                    berufsbeschreibung_messages = [
                        {"role": "system", "content": "Du bist ein hilfreicher Assistent."},
                        {"role": "user", "content": prompts[prompts_set]["berufsbeschreibung_query"] + "\n\n" + md_text}
                    ]
                    berufsbeschreibung = call_openai(ai_provider, berufsbeschreibung_messages, selected_model).strip()
                    if not berufsbeschreibung:
                        print_status("Keine Berufsbeschreibung generiert", color='red')
                        continue
                    
                    with st.expander("Generierte Berufsbeschreibung", expanded=False):
                        berufsbeschreibung_df = pd.DataFrame(
                            [[document_type, berufsbild_name, berufsbeschreibung]], 
                            columns=["Dokumententyp", "Berufsbild", "Beschreibung"]
                        )
                        st.dataframe(berufsbeschreibung_df, use_container_width=True)

                    # Speichere Ergebnisse für später
                    results.append([document_type, berufsbild_name])
                    berufsbeschreibungen[berufsbild_name] = berufsbeschreibung
                    
                    # 4. ESCO-Beruf suchen
                    esco_data = None
                    if berufsbild_name:
                        update_progress("Suche ESCO-Beruf")
                        occupation = esco_client.get_occupation(berufsbild_name)
                        if occupation:
                            print_status(f"ESCO-Beruf gefunden: {occupation['title']}", color='green')
                            
                            update_progress("Lade ESCO-Kompetenzen")
                            essential_skills, optional_skills = esco_client.get_skills(occupation['uri'])
                            
                            if essential_skills or optional_skills:
                                esco_data = {
                                    'occupation': occupation,
                                    'essential_skills': essential_skills,
                                    'optional_skills': optional_skills,
                                    'skill_mappings': []
                                }
                                
                                with st.expander("ESCO-Daten", expanded=False):
                                    # Beruf
                                    st.subheader("Gefundener Beruf")
                                    st.dataframe(pd.DataFrame(
                                        [[occupation['title'], occupation['description']]], 
                                        columns=['Beruf', 'Beschreibung']
                                    ))
                                    
                                    # Kompetenz-Statistiken
                                    st.subheader("Kompetenzen")
                                    st.dataframe(pd.DataFrame([
                                        ['Wesentliche Kompetenzen', len(essential_skills)],
                                        ['Optionale Kompetenzen', len(optional_skills)]
                                    ], columns=['Typ', 'Anzahl']))
                                    
                                    # Detaillierte Kompetenztabellen
                                    if essential_skills:
                                        st.subheader("Wesentliche Kompetenzen")
                                        st.dataframe(pd.DataFrame(
                                            [[skill['name'], skill['description']] for skill in essential_skills],
                                            columns=['Kompetenz', 'Beschreibung']
                                        ))
                                    
                                    if optional_skills:
                                        st.subheader("Optionale Kompetenzen")
                                        st.dataframe(pd.DataFrame(
                                            [[skill['name'], skill['description']] for skill in optional_skills],
                                            columns=['Kompetenz', 'Beschreibung']
                                        ))
                            else:
                                print_status("Keine ESCO-Kompetenzen gefunden", color='yellow')
                        else:
                            print_status("Kein passender ESCO-Beruf gefunden", color='yellow')
                    
                    # 5. Lernfelder/Ausbildungsteile und ihre Zeiträume
                    update_progress("Analysiere Lernfelder und Zeiträume")
                    lernfeld_messages = [
                        {"role": "system", "content": "Du bist ein hilfreicher Assistent."},
                        {"role": "user", "content": prompts[prompts_set]["lernfeld_query"] + "\n\n" + md_text}
                    ]
                    lernfeld_response = call_openai(ai_provider, lernfeld_messages, selected_model)
                    
                    # Parse die Antwort in Lernfeld-Zeitraum-Kombinationen
                    lernfeld_zeitraum_kombinationen = []
                    for line in lernfeld_response.strip().split('\n'):
                        if line.strip():
                            parts = line.strip().split(';')
                            lernfeld = parts[0].strip()
                            zeitraeume = [z.strip() for z in parts[1:]]
                            for zeitraum in zeitraeume:
                                lernfeld_zeitraum_kombinationen.append([document_type, berufsbild_name, lernfeld, zeitraum])

                    with st.expander("Lernfelder und Zeiträume", expanded=False):
                        st.subheader("Gefundene Lernfelder/Ausbildungsteile")
                        st.dataframe(pd.DataFrame(lernfeld_zeitraum_kombinationen,
                                   columns=["Dokumententyp", "Berufsbild", "Lernfeld/Ausbildungsteil", "Zeitraum"]))
                    
                    # Verarbeite Zeitwerte und Lernziele
                    final_entries = []
                    for entry in lernfeld_zeitraum_kombinationen:
                        lernfeld = entry[2]
                        zeitraeume = [entry[3]]  # Liste für mögliche mehrere Zeiträume
                        
                        update_progress(f"Verarbeite Lernfeld: {lernfeld}")
                        
                        # Zeitwerte abfragen
                        zeitwert_messages = [
                            {"role": "system", "content": "Du bist ein hilfreicher Assistent."},
                            {"role": "user", "content": prompts[prompts_set]["zeitwerte_query"].format(
                                lernfeld_name=lernfeld
                            ) + "\n\n" + md_text}
                        ]
                        zeitwert_response = call_openai(ai_provider, zeitwert_messages, selected_model)
                        zeitwerte = zeitwert_response.strip().split(';')
                        
                        # Lernziele abfragen
                        lernziel_messages = [
                            {"role": "system", "content": "Du bist ein hilfreicher Assistent."},
                            {"role": "user", "content": prompts[prompts_set]["lernziel_query"].format(
                                lernfeld_name=lernfeld
                            ) + "\n\n" + md_text}
                        ]
                        lernziel_response = call_openai(ai_provider, lernziel_messages, selected_model)
                        
                        # Verarbeite Lernziele nach Zeiträumen
                        with st.expander(f"Lernziele - {lernfeld}", expanded=False):
                            for line in lernziel_response.strip().split('\n'):
                                if line.strip():
                                    zeitraum, lernziel = line.strip().split(';', 1)
                                    zeitraum = zeitraum.strip()
                                    lernziel = lernziel.strip()
                                    
                                    # Finde den passenden Zeitwert
                                    zeitwert_index = zeitraeume.index(zeitraum) if zeitraum in zeitraeume else 0
                                    zeitwert = zeitwerte[zeitwert_index] if zeitwert_index < len(zeitwerte) else "unspezifisch"
                                    
                                    final_entry = [
                                        document_type,
                                        berufsbild_name,
                                        lernfeld,
                                        zeitraum,
                                        zeitwert.strip(),
                                        lernziel
                                    ]
                                    final_entries.append(final_entry)
                            
                            # Zeige Zwischenergebnis
                            st.dataframe(pd.DataFrame([[z[3], z[4], z[5]] for z in final_entries if z[2] == lernfeld],
                                                   columns=["Zeitraum", "Zeit", "Lernziel"]))
                    
                    # Gesamtergebnis
                    with st.expander("Gesamtergebnis", expanded=True):
                        st.subheader("Alle Lernziele")
                        df = pd.DataFrame(final_entries,
                                       columns=["Dokumententyp", "Berufsbild", "Lernfeld/Ausbildungsteil", 
                                              "Zeitraum", "Zeit", "Lernziel"])
                        st.dataframe(df)
                    
                    # Verarbeite und speichere die Daten
                    if final_entries:
                        # Erstelle Basis-Dateinamen
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        base_name = os.path.splitext(file)[0]
                        
                        # Verarbeite und speichere die Daten
                        json_filename = f"{base_name}_{timestamp}.json"
                        csv_filename = f"{base_name}_{timestamp}.csv"
                        json_path = os.path.join(output_folder, json_filename)
                        csv_path = os.path.join(output_folder, csv_filename)
                        
                        # Erstelle und speichere JSON mit ESCO-Daten
                        json_data = save_json(final_entries, esco_data, json_path, ai_provider, selected_model, berufsbeschreibungen)
                        
                        if json_data:
                            # Speichere CSV mit den vollständigen Daten
                            save_csv(json_data, csv_path)
                            
                            json_paths.append(json_path)
                            csv_paths.append(csv_path)
                            
                            # Zeige ESCO-Mappings in der UI an
                            if esco_data:
                                st.write("### ESCO-Kompetenz-Zuordnungen")
                                for lernfeld, mappings in json_data["beruf"]["matching"].items():
                                    st.write(f"\n**{lernfeld}**")
                                    for zeitraum, zeitraum_data in mappings.items():
                                        st.write(f"*{zeitraum}*")
                                        for lz_id, lz_data in zeitraum_data["lernziele"].items():
                                            if lz_data["mappings"]:
                                                st.write(f"- {lz_data['text']}")
                                                for mapping in lz_data["mappings"]:
                                                    st.write(f"  * {mapping['typ'].upper()}: {', '.join(mapping['kompetenzen'])}")
                        
                        results.extend(final_entries)
                    else:
                        print_status("Keine Daten zum Speichern gefunden.", 'red')
    
    return results, json_paths, csv_paths

def get_esco_occupation(berufsbild_name: str) -> Optional[Dict[str, Any]]:
    """Sucht nach einem Beruf in ESCO basierend auf dem Berufsbildnamen."""
    esco_client = ESCOClient()
    occupation = esco_client.get_occupation(berufsbild_name)
    return occupation

def get_esco_skills(occupation_uri: str) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """Holt die wesentlichen und optionalen Kompetenzen für einen Beruf."""
    esco_client = ESCOClient()
    essential_skills, optional_skills = esco_client.get_skills(occupation_uri)
    return essential_skills, optional_skills

def match_learning_objectives_with_esco(learning_objectives: List[str], esco_skills: List[Dict[str, str]], 
                                      ai_provider: Any, model: str) -> Dict[str, List[Dict[str, str]]]:
    """Ordnet Lernziele den ESCO-Kompetenzen zu."""
    if not learning_objectives or not esco_skills:
        return {}

    # Erstelle nummerierte Listen
    numbered_objectives = [f"{i+1}. {obj}" for i, obj in enumerate(learning_objectives)]
    numbered_skills = [f"{i+1}. {skill['label']}" for i, skill in enumerate(esco_skills)]
    
    # Erstelle den Prompt für die Zuordnung
    prompt = f"""Ordne die folgenden Lernziele den ESCO-Kompetenzen zu.
    
Lernziele:
{chr(10).join(numbered_objectives)}

ESCO-Kompetenzen:
{chr(10).join(numbered_skills)}

Gib die Zuordnungen im Format "Lernziel-Nr -> ESCO-Kompetenz-Nr" an.
Ein Lernziel kann mehreren Kompetenzen zugeordnet werden und umgekehrt.
Beispiel: 1 -> 2,3 bedeutet, dass Lernziel 1 den ESCO-Kompetenzen 2 und 3 zugeordnet ist.

Bitte gib nur die Zuordnungen zurück, keine weiteren Erklärungen.
"""

    messages = [
        {"role": "system", "content": "Du bist ein hilfreicher Assistent."},
        {"role": "user", "content": prompt}
    ]
    
    try:
        response = call_openai(ai_provider, messages, model)
        mappings = {}
        
        for line in response.strip().split('\n'):
            if '->' in line:
                try:
                    src, targets = line.split('->')
                    src_num = int(src.strip()) - 1
                    target_nums = [int(t.strip()) - 1 for t in targets.strip().split(',')]
                    
                    if 0 <= src_num < len(learning_objectives) and all(0 <= t < len(esco_skills) for t in target_nums):
                        lernziel = learning_objectives[src_num]
                        matched_skills = []
                        for t in target_nums:
                            matched_skills.append({
                                'label': esco_skills[t]['label'],
                                'uri': esco_skills[t]['uri']
                            })
                        mappings[lernziel] = matched_skills
                except (ValueError, IndexError) as e:
                    print_status(f"Fehler beim Parsen der Zuordnung '{line}': {e}", color='yellow')
                    continue
                
        return mappings
    except Exception as e:
        print_status(f"Fehler bei der Zuordnung von Lernzielen zu ESCO-Kompetenzen: {e}", color='red')
        return {}

def process_document_data(data: List[List[str]], berufsbezeichnung: str, berufsbeschreibung: str) -> Dict[str, Any]:
    """Konvertiert die Rohdaten in eine hierarchische Struktur."""
    doc_data = {
        "berufsbezeichnung": berufsbezeichnung,
        "berufsbeschreibung": berufsbeschreibung,
        "lernfelder_ausbildungsteile": {}
    }
    
    for row in data:
        if len(row) >= 6:
            lernfeld = row[2]
            zeitraum = row[3]
            zeit_raw = row[4]
            lernziele = [lz.strip() for lz in row[5].split(";") if lz.strip()]
            
            if lernfeld not in doc_data["lernfelder_ausbildungsteile"]:
                doc_data["lernfelder_ausbildungsteile"][lernfeld] = {
                    "beschreibung": lernfeld,
                    "zeitraeume": {}
                }
            
            if zeitraum not in doc_data["lernfelder_ausbildungsteile"][lernfeld]["zeitraeume"]:
                zeit_wert, zeit_einheit = zeit_raw.split(" ") if " " in zeit_raw else (zeit_raw, "unspezifisch")
                doc_data["lernfelder_ausbildungsteile"][lernfeld]["zeitraeume"][zeitraum] = {
                    "zeit": {
                        "wert": zeit_wert,
                        "einheit": zeit_einheit
                    },
                    "lernziele": {}
                }
            
            zeitraum_data = doc_data["lernfelder_ausbildungsteile"][lernfeld]["zeitraeume"][zeitraum]
            for lernziel in lernziele:
                if lernziel.strip():
                    lz_id = f"dok_lz_{len(zeitraum_data['lernziele']) + 1}"
                    zeitraum_data["lernziele"][lz_id] = {
                        "text": lernziel.strip(),
                        "esco_mappings": []
                    }
    
    return doc_data

def process_esco_data(esco_raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Verarbeitet die ESCO-Rohdaten in ein strukturiertes Format."""
    if not esco_raw_data:
        return {}
        
    esco_data = {
        "beruf": {
            "uri": esco_raw_data["occupation"]["uri"],
            "titel": esco_raw_data["occupation"]["title"],
            "beschreibung": esco_raw_data["occupation"]["description"]
        },
        "kompetenzen": {
            "essentiell": {},
            "optional": {}
        }
    }
    
    # Verarbeite essentielle Kompetenzen
    for i, skill in enumerate(esco_raw_data["essential_skills"]):
        skill_id = f"esco_ess_{i + 1}"
        esco_data["kompetenzen"]["essentiell"][skill_id] = {
            "titel": skill["name"],
            "beschreibung": skill["description"],
            "uri": skill["uri"]
        }
    
    # Verarbeite optionale Kompetenzen
    for i, skill in enumerate(esco_raw_data["optional_skills"]):
        skill_id = f"esco_opt_{i + 1}"
        esco_data["kompetenzen"]["optional"][skill_id] = {
            "titel": skill["name"],
            "beschreibung": skill["description"],
            "uri": skill["uri"]
        }
    
    return esco_data

def create_matching_structure(doc_data: Dict[str, Any], esco_data: Dict[str, Any]) -> Dict[str, Any]:
    """Erstellt die Matching-Struktur basierend auf Lernfeldern und Zeiträumen."""
    matching = {}
    
    for lernfeld, lernfeld_data in doc_data["lernfelder_ausbildungsteile"].items():
        matching[lernfeld] = {}
        for zeitraum, zeitraum_data in lernfeld_data["zeitraeume"].items():
            matching[lernfeld][zeitraum] = {
                "lernziele": {}
            }
            for lz_id, lz_data in zeitraum_data["lernziele"].items():
                matching[lernfeld][zeitraum]["lernziele"][lz_id] = {
                    "text": lz_data["text"],
                    "mappings": lz_data["esco_mappings"]
                }
    
    return matching

def save_json(data: List[List[str]], esco_data: Optional[Dict[str, Any]], output_path: str, 
             ai_provider: Any, model: str, berufsbeschreibungen: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """Speichert die Daten im JSON-Format mit hierarchischer Struktur."""
    try:
        # Erstelle die Basis-Struktur
        berufsbezeichnung = data[0][1]
        dokument_typ = data[0][0]
        json_data = {
            "dokumententyp": dokument_typ,
            "beruf": {
                "dokumente_daten": process_document_data(data, berufsbezeichnung, berufsbeschreibungen.get(berufsbezeichnung, "")),
                "esco_daten": {},
                "matching": {}
            }
        }
        
        # Bestimme das richtige Promptset basierend auf dem Dokumenttyp
        prompts_set = "rahmenlehrplan_prompts" if dokument_typ == "Rahmenlehrplan" else "ausbildungsrahmenplan_prompts"
        
        # Verarbeite ESCO-Daten wenn vorhanden
        if esco_data:
            json_data["beruf"]["esco_daten"] = process_esco_data(esco_data)
            
            # Erstelle und integriere die Mappings
            lernfelder = json_data["beruf"]["dokumente_daten"]["lernfelder_ausbildungsteile"]
            for lernfeld, lernfeld_data in lernfelder.items():
                # Sammle alle Lernziele des Lernfelds
                all_lernziele_im_lernfeld = []
                lz_mapping = {}  # Mapping zwischen Text und {zeitraum, lz_id}
                
                for zeitraum, zeitraum_data in lernfeld_data["zeitraeume"].items():
                    for lz_id, lz_data in zeitraum_data["lernziele"].items():
                        all_lernziele_im_lernfeld.append(lz_data["text"])
                        lz_mapping[lz_data["text"]] = {"zeitraum": zeitraum, "lz_id": lz_id}
                
                # Führe Mapping für alle Lernziele des Lernfelds durch
                all_skills = []
                for skill_type in ["essentiell", "optional"]:
                    skills_data = json_data["beruf"]["esco_daten"]["kompetenzen"][skill_type]
                    for skill_id, data in skills_data.items():
                        all_skills.append({
                            "label": data["titel"],
                            "uri": data["uri"],
                            "type": skill_type
                        })
                
                if all_lernziele_im_lernfeld and all_skills:
                    # Führe das Matching durch
                    mappings = match_learning_objectives_with_esco(
                        all_lernziele_im_lernfeld,
                        all_skills,
                        ai_provider,
                        model
                    )
                    
                    # Integriere die Mappings in die JSON-Struktur
                    for lernziel_text, matched_skills in mappings.items():
                        lz_info = lz_mapping[lernziel_text]
                        zeitraum = lz_info["zeitraum"]
                        lz_id = lz_info["lz_id"]
                        
                        if matched_skills:
                            for skill in matched_skills:
                                mapping = {
                                    "kompetenz": skill["label"],
                                    "uri": skill["uri"]
                                }
                                lernfelder[lernfeld]["zeitraeume"][zeitraum]["lernziele"][lz_id]["esco_mappings"].append(mapping)
        
        # Speichere die JSON-Datei
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
            
        print_status(f"JSON-Datei erfolgreich gespeichert: {output_path}", color='green')
        return json_data
        
    except Exception as e:
        print_status(f"Fehler beim Speichern der JSON-Datei {output_path}: {e}", color='red')
        return None

def save_csv(json_data: Dict[str, Any], output_path: str):
    """Speichert die Daten im CSV-Format als flache Struktur."""
    try:
        headers = [
            "Dokumententyp",
            "Berufsbezeichnung Dokument",
            "Berufsbezeichnung ESCO",
            "Beruf URI ESCO",
            "Lernfelder/Ausbildungsteile",
            "Zeiträume",
            "Zeit",
            "Zeiteinheiten",
            "Lernziel Dokument",
            "Lernziel ESCO Entsprechung",
            "Lernziel ESCO URI"
        ]
        
        rows = []
        esco_uri = json_data["beruf"].get("esco_daten", {}).get("beruf", {}).get("uri", "")
        esco_berufstitel = json_data["beruf"].get("esco_daten", {}).get("beruf", {}).get("titel", "")
        lernfelder = json_data["beruf"]["dokumente_daten"]["lernfelder_ausbildungsteile"]
        
        # Erstelle flache Struktur
        for lernfeld, lernfeld_data in lernfelder.items():
            for zeitraum, zeitraum_data in lernfeld_data["zeitraeume"].items():
                for lz_id, lz_data in zeitraum_data["lernziele"].items():
                    # Basis-Informationen
                    base_row = [
                        json_data["dokumententyp"],
                        json_data["beruf"]["dokumente_daten"]["berufsbezeichnung"],
                        esco_berufstitel,
                        esco_uri,
                        lernfeld,
                        zeitraum,
                        zeitraum_data["zeit"]["wert"],
                        zeitraum_data["zeit"]["einheit"],
                        lz_data["text"]
                    ]
                    
                    # Wenn keine ESCO-Mappings vorhanden sind
                    if not lz_data["esco_mappings"]:
                        rows.append(base_row + ["-", "-"])
                    else:
                        # Für jedes Mapping eine neue Zeile
                        for mapping in lz_data["esco_mappings"]:
                            row = base_row + [mapping["kompetenz"], mapping["uri"]]
                            rows.append(row)
        
        # Speichere CSV
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(headers)
            writer.writerows(rows)
        
        print_status(f"CSV-Datei erfolgreich gespeichert: {output_path}", color='green')
        
    except Exception as e:
        print_status(f"Fehler beim Speichern der CSV-Datei {output_path}: {e}", color='red')

# Streamlit UI
st.set_page_config(layout="wide")

st.title("Berufeanalyzer mit ESCO Support")

# Erstelle die benötigten Ordner beim Start
data_folder = "./data"
output_folder = "./output"
temp_folder = "./temp"

# Stelle sicher, dass alle Ordner existieren
os.makedirs(data_folder, exist_ok=True)
os.makedirs(output_folder, exist_ok=True)
os.makedirs(temp_folder, exist_ok=True)

# Prompt Konfiguration
with st.expander("Dokumententyp-Bestimmung", expanded=False):
    document_type_prompt = st.text_area(
        "Dokumententyp-Bestimmung",
        """Ist dieses Dokument ein Ausbildungsrahmenplan (Gesetz) oder ein Rahmenlehrplan mit Lernfeldern? Bitte antworte nur mit 'Ausbildungsrahmenplan' oder 'Rahmenlehrplan'.""",
        height=150,
        key="document_type_prompt"
    )

col1, col2 = st.columns(2)

with col1:
    with st.expander("Rahmenlehrplan Prompts", expanded=False):
        rahmenlehrplan_prompts = {
            "berufsbild_query": st.text_area(
                "Berufsbild-Abfrage (Rahmenlehrplan)",
                """Gib den Beruf in der Form 'männliche Form/weibliche Form' an.

Beispiel:
Maurer/Maurerin""",
                height=150,
                key="berufsbild_query_rlp"
            ),
            "berufsbeschreibung_query": st.text_area(
                "Berufsbeschreibung-Abfrage (Rahmenlehrplan)",
                """Erstelle eine prägnante Beschreibung des Berufs basierend auf dem Dokument.
Die Beschreibung soll maximal 700 Zeichen lang sein und in drei Absätzen strukturiert sein:

Absatz 1: Die offizielle Berufsbezeichnung
Absatz 2: Die typischen Tätigkeiten und Aufgaben in fließendem Text
Absatz 3: Die charakteristischen Merkmale des Berufs in fließendem Text

Antworte nur mit der Beschreibung, ohne Überschriften oder Aufzählungszeichen. Jeder Absatz soll ein eigenständiger Fließtext sein.""",
                height=200,
                key="berufsbeschreibung_query_rlp"
            ),
            "lernfeld_query": st.text_area(
                "Lernfeld-Abfrage (Rahmenlehrplan)",
                """Liste die Lernfelder und ihre zugehörigen Zeiträume auf. 
Entferne dabei Nummerierungen und Aufzählungszeichen vor den Lernfeldern.
Verwende folgendes Format:
Lernfeldname;Zeitraum

Beispiele:
Geschäftsprozesse und Märkte erkunden;1. Ausbildungsjahr
Waren annehmen und kontrollieren;1. Ausbildungsjahr;2. Ausbildungsjahr
Kunden beraten;2. Ausbildungsjahr""",
                height=300,
                key="lernfeld_query_rlp"
            ),
            "zeitwerte_query": st.text_area(
                "Zeitwerte-Abfrage (Rahmenlehrplan)",
                """Gib die Zeit mit Einheit für '{lernfeld_name}' in den Zeiträumen an.
Antworte nur mit Zahlen und Einheiten, keine weiteren Erklärungen.
Bei mehreren Zeiträumen trenne die Zeiten mit Semikolon.

Beispiele für einen Zeitraum:
40 Stunden
4 Wochen
3 Monate

Beispiele für zwei Zeiträume:
40 Stunden;60 Stunden
4 Wochen;8 Wochen
2 Monate;4 Monate

Bei fehlender Zeitangabe:
unspezifisch""",
                height=200,
                key="zeitwerte_query_rlp"
            ),
            "lernziel_query": st.text_area(
                "Lernziel-Abfrage (Rahmenlehrplan)",
                """Liste die Lernziele für '{lernfeld_name}' sortiert nach Zeiträumen auf.
Verwende folgendes Format:
Zeitraum;Lernziel

Ein Lernziel pro Zeile, keine Aufzählungszeichen.

Beispiel für einen Zeitraum:
1. Ausbildungsjahr;Kundenberatungsgespräche führen
1. Ausbildungsjahr;Verkaufsgespräche durchführen

Beispiel für zwei Zeiträume:
1. - 15. Monat;Grundlagen der Kundenberatung anwenden
1. - 15. Monat;Verkaufstechniken einüben
16. - 36. Monat;Komplexe Beratungsgespräche führen
16. - 36. Monat;Verkaufsstrategien entwickeln""",
                height=300,
                key="lernziel_query_rlp"
            )
        }

with col2:
    with st.expander("Ausbildungsrahmenplan Prompts", expanded=False):
        ausbildungsrahmenplan_prompts = {
            "berufsbild_query": st.text_area(
                "Berufsbild-Abfrage (Ausbildungsrahmenplan)",
                """Gib den Beruf in der Form 'männliche Form/weibliche Form' an.

Beispiel:
Maurer/Maurerin""",
                height=150,
                key="berufsbild_query_arp"
            ),
            "berufsbeschreibung_query": st.text_area(
                "Berufsbeschreibung-Abfrage (Ausbildungsrahmenplan)",
                """Erstelle eine prägnante Beschreibung des Berufs basierend auf dem Dokument.
Die Beschreibung soll maximal 700 Zeichen lang sein und in drei Absätzen strukturiert sein:

Absatz 1: Die offizielle Berufsbezeichnung
Absatz 2: Die typischen Tätigkeiten und Aufgaben in fließendem Text
Absatz 3: Die charakteristischen Merkmale des Berufs in fließendem Text

Antworte nur mit der Beschreibung, ohne Überschriften oder Aufzählungszeichen. Jeder Absatz soll ein eigenständiger Fließtext sein.""",
                height=200,
                key="berufsbeschreibung_query_arp"
            ),
            "lernfeld_query": st.text_area(
                "Ausbildungsteil-Abfrage (Ausbildungsrahmenplan)",
                """Liste die Ausbildungsteile und ihre zugehörigen Zeiträume auf.
Entferne dabei Nummerierungen und Aufzählungszeichen vor den Ausbildungsteilen.
Verwende folgendes Format:
Ausbildungsteilname;Zeitraum

Beispiele:
Berufsbildung sowie Arbeits- und Tarifrecht;1. bis 18. Ausbildungsmonat
Aufbau und Organisation des Ausbildungsbetriebes;1. - 15. Monat;16. - 36. Monat
Sicherheit und Gesundheitsschutz bei der Arbeit;1. bis 18. Ausbildungsmonat""",
                height=300,
                key="lernfeld_query_arp"
            ),
            "zeitwerte_query": st.text_area(
                "Zeitwerte-Abfrage (Ausbildungsrahmenplan)",
                """Gib die Zeit mit Einheit für '{lernfeld_name}' in den Zeiträumen an.
Antworte nur mit Zahlen und Einheiten, keine weiteren Erklärungen.
Bei mehreren Zeiträumen trenne die Zeiten mit Semikolon.

Beispiele für einen Zeitraum:
40 Stunden
4 Wochen
3 Monate

Beispiele für zwei Zeiträume:
40 Stunden;60 Stunden
4 Wochen;8 Wochen
2 Monate;4 Monate

Bei fehlender Zeitangabe:
unspezifisch""",
                height=200,
                key="zeitwerte_query_arp"
            ),
            "lernziel_query": st.text_area(
                "Lernziel-Abfrage (Ausbildungsrahmenplan)",
                """Liste die Lernziele für '{lernfeld_name}' sortiert nach Zeiträumen auf.
Verwende folgendes Format:
Zeitraum;Lernziel

Ein Lernziel pro Zeile, keine Aufzählungszeichen.

Beispiel für einen Zeitraum:
1. Ausbildungsjahr;Kundenberatungsgespräche führen
1. Ausbildungsjahr;Verkaufsgespräche durchführen

Beispiel für zwei Zeiträume:
1. - 15. Monat;Grundlagen der Kundenberatung anwenden
1. - 15. Monat;Verkaufstechniken einüben
16. - 36. Monat;Komplexe Beratungsgespräche führen
16. - 36. Monat;Verkaufsstrategien entwickeln""",
                height=300,
                key="lernziel_query_arp"
            )
        }
        
prompts = {
    "document_type_prompt": document_type_prompt,
    "rahmenlehrplan_prompts": rahmenlehrplan_prompts,
    "ausbildungsrahmenplan_prompts": ausbildungsrahmenplan_prompts
}

# Sidebar Konfiguration
st.sidebar.title("Konfiguration")

with st.sidebar:
    # LLM Konfiguration
    with st.expander("LLM Konfiguration", expanded=False):
        api_key_input = st.text_input(
            "OpenAI API Key",
            value=os.environ.get('OPENAI_API_KEY', ''),
            type="password",
            key='openai_api_key'
        )
        model_options = ["gpt-4o-mini", "gpt-4o"]
        selected_model = st.selectbox("Wähle das LLM-Modell", model_options, index=0)

    # Dokumentenkonvertierung
    with st.expander("Konverter Konfiguration", expanded=False):
        # Aktualisierte Konverter-Optionen
        converter_options = ["IBMDocling (genau)", "PyMuPDF4LLM (schnell)", "PDFPlumber (robust)"]
        selected_converter = st.selectbox(
            "PDF Konverter",
            converter_options,
            index=1,  # Set PyMuPDF4LLM as default (index 1 in the list)
            help="Wählen Sie den PDF Konverter aus"
        )

        # Definiere erlaubte Dateiformate basierend auf Konvertierungstool
        allowed_extensions = []
        if "IBMDocling" in selected_converter:
            allowed_extensions = ['.pdf', '.docx', '.pptx', '.xlsx', '.jpg', '.jpeg', '.png', '.gif', '.html', '.adoc', '.md']
        elif "PyMuPDF4LLM" in selected_converter:
            allowed_extensions = ['.pdf', '.md']
        else:  # PDFPlumber
            allowed_extensions = ['.pdf', '.md']

    # Ordner Konfiguration
    with st.expander("Ordner Konfiguration", expanded=False):
        # Ordner Einstellungen
        data_folder = st.text_input("Datenordner", value="./data", key='data_folder')
        output_folder = st.text_input("Output-Ordner", value="./output", key='output_folder')
        temp_folder = st.text_input("Temporärer Ordner", value="./temp", key='temp_folder')

    # Dateimanagement
    with st.expander("Dateimanagement", expanded=False):
        # Verwende eindeutige Keys für alle UI-Elemente
        tab1, tab2 = st.tabs(["Upload", "Download/Löschen"])
        
        with tab1:
            uploaded_files = st.file_uploader("Dateien hochladen", 
                                           accept_multiple_files=True,
                                           key="file_uploader")
            if uploaded_files:
                for uploaded_file in uploaded_files:
                    if not os.path.exists(data_folder):
                        os.makedirs(data_folder)
                    
                    file_path = os.path.join(data_folder, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    st.success(f"Datei hochgeladen: {uploaded_file.name}")
        
        with tab2:
            folder = st.radio("Ordner auswählen", 
                            ["Datenordner", "Ausgabeordner"],
                            key="folder_selection")
            operation = st.radio("Operation", 
                               ["Download", "Löschen"],
                               key="operation_selection")
            
            target_folder = data_folder if folder == "Datenordner" else output_folder
            
            if os.path.exists(target_folder) and os.listdir(target_folder):
                files = os.listdir(target_folder)
                if operation == "Download":
                    download_type = st.radio("Download Typ", 
                                          ["Einzelne Datei", "Alle als ZIP"],
                                          key="download_type")
                    
                    if download_type == "Alle als ZIP":
                        if st.button("Als ZIP herunterladen", key="zip_download"):
                            zip_path = os.path.join(temp_folder, f"{folder.lower()}_files.zip")
                            if not os.path.exists(temp_folder):
                                os.makedirs(temp_folder)
                            shutil.make_archive(zip_path[:-4], 'zip', target_folder)
                            with open(zip_path, "rb") as f:
                                st.download_button(
                                    label="ZIP-Datei herunterladen",
                                    data=f,
                                    file_name=f"{folder.lower()}_files.zip",
                                    mime="application/zip",
                                    key="zip_download_button"
                                )
                    else:
                        selected_file = st.selectbox("Datei auswählen", 
                                                   files,
                                                   key="file_selection")
                        if selected_file:
                            file_path = os.path.join(target_folder, selected_file)
                            with open(file_path, "rb") as f:
                                st.download_button(
                                    label=f"Datei herunterladen",
                                    data=f,
                                    file_name=selected_file,
                                    mime="application/octet-stream",
                                    key="single_file_download"
                                )
                else:  # Löschen
                    files_to_delete = st.multiselect("Dateien zum Löschen auswählen",
                                                   files,
                                                   key="files_to_delete")
                    if st.button("Ausgewählte Dateien löschen", key="delete_button"):
                        for file_name in files_to_delete:
                            try:
                                os.remove(os.path.join(target_folder, file_name))
                                st.success(f"Datei gelöscht: {file_name}")
                            except Exception as e:
                                st.error(f"Fehler beim Löschen von {file_name}: {e}")
            else:
                st.info(f"Keine Dateien im {folder} vorhanden")

if st.button("Start Verarbeitung"):
    if api_key_input:
        with st.spinner('Verarbeitung läuft...'):
            try:
                # Erstelle Ordner wenn sie nicht existieren
                os.makedirs(data_folder, exist_ok=True)
                os.makedirs(output_folder, exist_ok=True)
                os.makedirs(temp_folder, exist_ok=True)

                # Prüfe Dateien im data_folder
                input_files = []
                for file in os.listdir(data_folder):
                    file_extension = os.path.splitext(file)[1].lower()
                    if file_extension not in allowed_extensions:
                        print_status(f"Überspringe nicht unterstützte Datei: {file}", 'warning')
                        continue
                    
                    # Wenn es eine Markdown-Datei ist, kopiere sie direkt in den Output-Ordner
                    if file_extension == '.md':
                        src_path = os.path.join(data_folder, file)
                        dst_path = os.path.join(output_folder, file)
                        shutil.copy2(src_path, dst_path)
                        print_status(f"Markdown-Datei kopiert: {file}", 'info')
                        continue
                        
                    input_files.append(os.path.join(data_folder, file))

                # Verarbeite die Dateien
                results, json_paths, csv_paths = process_all_files(
                    data_folder=data_folder,
                    api_key=api_key_input,
                    selected_model=selected_model,
                    prompts=prompts,
                    output_folder=output_folder,
                    converter=selected_converter
                )
                
                if json_paths and csv_paths:
                    st.success("Verarbeitung abgeschlossen.")
                    for json_path in json_paths:
                        if os.path.exists(json_path):
                            with open(json_path, "rb") as file:
                                st.download_button(
                                    label=f"Download JSON - {os.path.basename(json_path)}",
                                    data=file,
                                    file_name=os.path.basename(json_path),
                                    mime="application/json",
                                    key=f"json_download_{os.path.basename(json_path)}"
                                )
                        else:
                            print_status(f"JSON-Datei nicht gefunden: {json_path}", 'red')
                    for csv_path in csv_paths:
                        if os.path.exists(csv_path):
                            with open(csv_path, "rb") as file:
                                st.download_button(
                                    label=f"Download CSV - {os.path.basename(csv_path)}",
                                    data=file,
                                    file_name=os.path.basename(csv_path),
                                    mime="text/csv",
                                    key=f"csv_download_{os.path.basename(csv_path)}"
                                )
                        else:
                            print_status(f"CSV-Datei nicht gefunden: {csv_path}", 'red')
                else:
                    print_status("Keine JSON- oder CSV-Dateien erstellt.", 'warning')
            except Exception as e:
                st.error(f"Ein Fehler ist aufgetreten: {e}")
    else:
        st.error("Bitte gib Deinen OpenAI API Key ein.")
