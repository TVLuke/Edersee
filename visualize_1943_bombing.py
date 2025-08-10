#!/usr/bin/env python3
"""
Visualisierungsskript für Edertalsperre Wasserstandsdaten während 1943-1944.
Konzentriert sich auf den Zeitraum von April 1943 bis Mai 1944, mit besonderem Fokus auf
den 17. Mai 1943, als die RAF den Damm während der Operation Chastise bombardierte.
"""
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import os
import glob
import numpy as np
from matplotlib.patches import Rectangle

# Set a nicer font for plots
plt.rcParams['font.family'] = 'Helvetica'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12

# Constants
NORMALIZATION_OFFSET = 205  # Offset to subtract from all water level values
RAF_BOMBING_DATE = pd.Timestamp('1943-05-17', tz='UTC')  # Date of the RAF bombing
START_DATE = pd.Timestamp('1943-04-01', tz='UTC')  # Start of the focus period
END_DATE = pd.Timestamp('1944-05-31', tz='UTC')  # End of the focus period

# File paths
ACTUAL_DATA_FILE = 'pegelonline-edertalsperre.json'

def load_extracted_data():
    """Load extracted water level data from CSV files."""
    print("Lade extrahierte Daten aus CSV-Dateien...")
    
    # Find the specific CSV files for 1943 and 1944
    csv_files = [f for f in glob.glob("extracted_water_level_*.csv") 
                if f.endswith("1943.csv") or f.endswith("1944.csv")]
    
    if not csv_files:
        print("Keine extrahierten Datendateien für 1943-1944 gefunden.")
        return None
    
    # Load each CSV file and combine
    dfs = []
    for file in sorted(csv_files):
        year = int(file.split('_')[-1].split('.')[0])
        print(f"Lade Daten für Jahr {year}...")
        try:
            df = pd.read_csv(file)
            # Make timestamps timezone-aware to match actual data
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize('UTC')
            # Store original values before normalization
            df['original_value'] = df['value'].copy()
            # Apply normalization offset
            df['value'] = df['value'] - NORMALIZATION_OFFSET
            df.set_index('timestamp', inplace=True)
            dfs.append(df)
        except Exception as e:
            print(f"Fehler beim Laden von {file}: {e}")
    
    if not dfs:
        print("Es konnten keine gültigen extrahierten Datendateien geladen werden.")
        return None
    
    # Combine all dataframes
    combined_df = pd.concat(dfs)
    
    # Sort by timestamp
    combined_df.sort_index(inplace=True)
    
    print(f"Es wurden {len(combined_df)} extrahierte Datenpunkte aus {len(dfs)} Dateien geladen.")
    return combined_df

def filter_date_range(df):
    """Filter data to the specific date range of interest."""
    filtered_df = df[(df.index >= START_DATE) & (df.index <= END_DATE)]
    print(f"Gefiltert auf {len(filtered_df)} Datenpunkte von {START_DATE.date()} bis {END_DATE.date()}")
    return filtered_df

def create_bombing_visualization(df, output_file=None):
    """Erstellt eine Visualisierung mit Fokus auf die Bombardierung 1943."""
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(15, 8))
    
    # Define min_level for fill_between
    min_level = 0
    
    # Calculate max_level for y-axis (10 above the maximum water level)
    max_level = max(df['value']) + 10
    
    # Plot water level
    ax.plot(df.index, df['value'], color='#0066cc', linewidth=2, label='Wasserstand')
    
    # Fill area below the water level
    ax.fill_between(df.index, df['value'], min_level, color='#a8d1ff', alpha=0.6)
    
    # Mark the RAF bombing date with a vertical line
    ax.axvline(x=RAF_BOMBING_DATE, color='#cc0000', linestyle='-', linewidth=2, 
               label='RAF Bombardierung (17. Mai 1943)')
    
    # Add annotation for the bombing
    ax.annotate('RAF Operation Chastise\nDammbruch-Angriff', 
                xy=(RAF_BOMBING_DATE, df['value'].max() * 0.5),
                xytext=(RAF_BOMBING_DATE + pd.Timedelta(days=30), df['value'].max() * 0.8),
                arrowprops=dict(facecolor='#cc0000', shrink=0.05, width=2, headwidth=10),
                fontsize=12, color='#cc0000', weight='bold',
                bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="#cc0000", alpha=0.8))
    
    # Add a shaded area for the night of the bombing
    bombing_start = RAF_BOMBING_DATE.replace(hour=0)
    bombing_end = RAF_BOMBING_DATE.replace(hour=23, minute=59, second=59)
    ax.axvspan(bombing_start, bombing_end, color='#cc0000', alpha=0.2, label='Tag der Bombardierung')
    
    # Set labels and title
    ax.set_xlabel('Datum')
    ax.set_ylabel('Wasserstand über NN - 205m')
    ax.set_title('Edertalsperre Wasserstand während der RAF Bombardierung 1943')
    
    # Set y-axis limits
    ax.set_ylim(bottom=0, top=max_level)
    
    # Format x-axis to show dates clearly
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d, %Y'))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    
    # Rotate date labels for better readability
    plt.xticks(rotation=45)
    
    # Remove grid
    ax.grid(False)
    
    # Add legend
    ax.legend(loc='upper right')
    
    # Add historical context as text box
    historical_text = (
        "Operation Chastise (16.-17. Mai 1943):\n"
        "Die 617. Staffel der RAF griff die Edertalsperre\n"
        "und andere Staudämme mit Barnes Wallis' 'Rollbomben' an.\n"
        "Der Angriff verursachte erhebliche Schäden und Überschwemmungen\n"
        "im Edertal."
    )
    ax.text(0.02, 0.02, historical_text, transform=ax.transAxes, fontsize=10,
            verticalalignment='bottom', horizontalalignment='left',
            bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=0.5'))
    
    # Tight layout
    plt.tight_layout()
    
    # Save figure if output file is provided
    if output_file:
        plt.savefig(output_file, dpi=300)
        print(f"1943 Bombardierungs-Visualisierung gespeichert unter {output_file}")
    
    # Show plot
    plt.show()

def main():
    """Hauptfunktion zum Laden von Daten und Erstellen von Visualisierungen."""
    # Load extracted data for 1943-1944
    df = load_extracted_data()
    
    if df is None or df.empty:
        print("Fehler: Keine Daten für den angegebenen Zeitraum verfügbar.")
        return
    
    # Filter to the specific date range
    filtered_df = filter_date_range(df)
    
    if filtered_df.empty:
        print("Fehler: Keine Daten für den angegebenen Datumsbereich verfügbar.")
        return
    
    # Create visualization
    print("\nErstelle Visualisierung...")
    create_bombing_visualization(filtered_df, 'edertalsperre_1943_bombardierung.png')
    
    print("\nVisualisierung abgeschlossen!")

if __name__ == "__main__":
    main()
