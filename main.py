#!/usr/bin/env python3
"""
Hauptskript für die Edertalsperre Wasserstandsvisualisierung.
Führt den gesamten Prozess aus:
1. Lädt historische Daten herunter und verarbeitet sie
2. Erstellt alle Visualisierungen
"""

import os
import sys
import time
from datetime import datetime

# Importiere Funktionen aus anderen Skripten
import download_and_process_historical_data

# Importiere Visualisierungsskripte
import visualize_water_level
import visualize_all_years
import visualize_days_below_threshold
import visualize_days_below_threshold_filtered
import visualize_weekly_probability
import visualize_building_revealed_history
import visualize_1943_bombing

def download_and_process_data(start_year=1914, end_year=2024):
    """
    Lädt historische Daten herunter und verarbeitet sie.
    
    Args:
        start_year: Startjahr für die Verarbeitung
        end_year: Endjahr für die Verarbeitung
    
    Returns:
        True bei Erfolg, False bei Fehler
    """
    print("="*80)
    print(f"SCHRITT 1: HERUNTERLADEN UND VERARBEITEN VON DATEN ({start_year}-{end_year})")
    print("="*80)
    
    # Verarbeite jedes Jahr im Bereich
    years = list(range(start_year, end_year + 1))
    success_count = 0
    failed_years = []
    
    for year in years:
        # Schritt 1: Immer das Bild herunterladen
        image_path = f"pegel_bild_{year}.png"
        
        # Entferne vorhandenes Bild, falls es existiert
        if os.path.exists(image_path):
            os.remove(image_path)
            
        print(f"Lade Bild für {year} herunter")
        url = download_and_process_historical_data.get_image_url(year)
        if not download_and_process_historical_data.download_image(url, image_path):
            print(f"Fehler beim Herunterladen des Bildes für {year}, überspringe")
            failed_years.append(year)
            continue
        
        # Schritt 2: Verarbeite das Jahr
        if download_and_process_historical_data.process_year(year):
            success_count += 1
        else:
            failed_years.append(year)
    
    # Drucke Zusammenfassung
    print("\nDatenverarbeitung abgeschlossen!")
    print(f"Erfolgreich verarbeitet: {success_count} Jahre")
    print(f"Fehler bei {len(failed_years)} Jahren")
    
    if failed_years:
        print(f"Jahre mit Fehlern: {failed_years}")
    
    return success_count > 0

def create_visualizations():
    """
    Erstellt alle Visualisierungen.
    """
    print("\n" + "="*80)
    print("SCHRITT 2: ERSTELLEN ALLER VISUALISIERUNGEN")
    print("="*80)
    
    # Liste der Visualisierungsfunktionen
    visualizations = [
        ("Wasserstandsvisualisierung", visualize_water_level.main),
        ("Alle Jahre Visualisierung", visualize_all_years.main),
        ("Tage unter Schwellenwert", visualize_days_below_threshold.main),
        ("Tage unter Schwellenwert (gefiltert)", visualize_days_below_threshold_filtered.main),
        ("Wöchentliche Wahrscheinlichkeit", visualize_weekly_probability.main),
        ("Gebäude sichtbar Historie", visualize_building_revealed_history.main),
        ("1943 Bombardierung", visualize_1943_bombing.main)
    ]
    
    # Führe jede Visualisierung aus
    for name, vis_func in visualizations:
        try:
            print(f"\nErstelle {name}...")
            vis_func()
            print(f"{name} erfolgreich erstellt.")
        except Exception as e:
            print(f"Fehler beim Erstellen von {name}: {e}")
    
    print("\nAlle Visualisierungen abgeschlossen!")

def main():
    """
    Hauptfunktion, die den gesamten Prozess koordiniert.
    """
    start_time = time.time()
    print(f"Starte Edertalsperre Wasserstandsvisualisierung um {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Schritt 1: Daten herunterladen und verarbeiten
    if not download_and_process_data():
        print("Fehler beim Herunterladen und Verarbeiten der Daten. Breche ab.")
        return 1
    
    # Schritt 2: Visualisierungen erstellen
    create_visualizations()
    
    # Zusammenfassung
    elapsed_time = time.time() - start_time
    print("\n" + "="*80)
    print(f"PROZESS ABGESCHLOSSEN in {elapsed_time:.1f} Sekunden")
    print("="*80)
    
    # Liste alle erzeugten Dateien auf
    print("\nErzeugte Visualisierungsdateien:")
    visualization_files = [f for f in os.listdir('.') if f.endswith('.png') and not f.startswith('pegel_bild_') and not f.startswith('cropped_')]
    for file in sorted(visualization_files):
        print(f"- {file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
