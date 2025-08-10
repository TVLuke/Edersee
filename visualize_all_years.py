#!/usr/bin/env python3
"""
Visualisierungsskript für Edertalsperre Wasserstandsdaten über alle Jahre.
Kombiniert JSON-Daten für 2000-2025 mit extrahierten Daten für frühere Jahre.
Markiert Jahre, in denen der Wasserstand Gebäude freilegte (unter 224,70m).
"""
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import os
import glob

# Set a nicer font for plots
plt.rcParams['font.family'] = 'Helvetica'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12

# Constants
NORMALIZATION_OFFSET = 205  # Offset to subtract from all water level values
BUILDING_THRESHOLD = 224.70  # Water level threshold where buildings are revealed

# File paths
ACTUAL_DATA_FILE = 'pegelonline-edertalsperre.json'

def load_actual_data(file_path):
    """Load water level data from JSON file."""
    print(f"Lade tatsächliche Daten aus {file_path}...")
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    print(f"Es wurden {len(data)} tatsächliche Datenpunkte geladen.")
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Convert timestamps to datetime objects
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    
    # Set timestamp as index
    df.set_index('timestamp', inplace=True)
    
    # Sort by timestamp
    df.sort_index(inplace=True)
    
    return df

def load_extracted_data():
    """Load extracted water level data from CSV files."""
    print("Lade extrahierte Daten aus CSV-Dateien...")
    
    # Find all extracted data files
    csv_files = glob.glob("extracted_water_level_*.csv")
    
    # Filter to only include years before 2000
    pre_2000_files = [f for f in csv_files if int(f.split('_')[-1].split('.')[0]) < 2000]
    
    if not pre_2000_files:
        print("Keine extrahierten Datendateien für Jahre vor 2000 gefunden.")
        return None
    
    # Load each CSV file and combine
    dfs = []
    for file in sorted(pre_2000_files):
        year = int(file.split('_')[-1].split('.')[0])
        print(f"Lade Daten für Jahr {year}...")
        try:
            df = pd.read_csv(file)
            # Make timestamps timezone-aware to match actual data
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize('UTC')
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

def combine_data(actual_df, extracted_df):
    """Combine actual and extracted data."""
    if extracted_df is None:
        print("Keine extrahierten Daten zum Kombinieren. Nur tatsächliche Daten werden verwendet.")
        return actual_df
    
    # Ensure column names match
    if 'value' not in extracted_df.columns:
        print("Fehler: Spalte 'value' nicht in extrahierten Daten gefunden.")
        return actual_df
    
    # Combine the dataframes
    combined_df = pd.concat([extracted_df, actual_df])
    
    # Sort by timestamp
    combined_df.sort_index(inplace=True)
    
    # Remove duplicates if any
    combined_df = combined_df[~combined_df.index.duplicated(keep='first')]
    
    print(f"Kombinierte Daten haben {len(combined_df)} Datenpunkte.")
    return combined_df

def normalize_data(df):
    """Normalisiert Wasserstandswerte durch Subtrahieren des Offsets."""
    df['original_value'] = df['value'].copy()  # Keep original values
    df['value'] = df['value'] - NORMALIZATION_OFFSET
    return df

def identify_revealed_years(df):
    """Identify years when water level dropped below the building threshold."""
    # Group by year and find minimum water level
    yearly_min = df.resample('Y')['original_value'].min()
    
    # Find years where minimum water level was below threshold
    revealed_years = yearly_min[yearly_min < BUILDING_THRESHOLD].index.year.tolist()
    
    print(f"Jahre, in denen Gebäude sichtbar wurden (Wasserstand unter {BUILDING_THRESHOLD}m):")
    for year in sorted(revealed_years):
        print(f"- {year}")
    
    return revealed_years

def create_all_years_visualization(df, revealed_years, output_file=None):
    """Create a visualization of water level data for all years."""
    # Calculate figure width based on 25px per month
    start_date = df.index.min()
    end_date = df.index.max()
    num_months = (end_date.year - start_date.year) * 12 + end_date.month - start_date.month + 1
    
    # Width: 25px per month (converted to inches for matplotlib, assuming 100 DPI)
    width_inches = num_months * 25 / 100
    
    # Define min_level for fill_between
    min_level = 0
    
    # Calculate max_level for y-axis (10 above the maximum water level)
    max_level = max(df['value']) + 10
    
    # Create figure and axis with calculated width and increased height
    fig, ax = plt.subplots(figsize=(width_inches, 15))
    
    # Plot water level with light blue fill below
    ax.plot(df.index, df['value'], color='#0066cc', linewidth=1.5, label='Wasserstand')
    ax.fill_between(df.index, df['value'], min_level, color='#a8d1ff', alpha=0.6)
    
    # Add building threshold line
    building_threshold_normalized = BUILDING_THRESHOLD - NORMALIZATION_OFFSET
    ax.axhline(y=building_threshold_normalized, color='#cc0000', linestyle='-', alpha=0.8, linewidth=2)
    ax.text(df.index[0], building_threshold_normalized, 
            f"Gebäude-Schwellenwert ({BUILDING_THRESHOLD}m)", fontsize=12, 
            verticalalignment='bottom', horizontalalignment='left',
            bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.5', edgecolor='#cc0000'))
    
    # Mark years when buildings were revealed
    for year in revealed_years:
        # Find the date range for this year
        year_data = df[df.index.year == year]
        if not year_data.empty:
            # Mark the year with a vertical span
            year_start = year_data.index.min()
            year_end = year_data.index.max()
            ax.axvspan(year_start, year_end, color='#ffcccc', alpha=0.3)
            
            # Add a text label at the top of the plot
            mid_point = year_start + (year_end - year_start) / 2
            ax.text(mid_point, max_level * 0.95, str(year), 
                    fontsize=10, color='#cc0000', weight='bold',
                    ha='center', va='top',
                    bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.3'))
    
    # Set labels and title
    ax.set_xlabel('Datum')
    ax.set_ylabel('Wasserstand über NN - 205m')
    ax.set_title('Edertalsperre Wasserstand (Alle Jahre)')
    
    # Format x-axis to show years clearly
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    
    # Add minor ticks for months
    ax.xaxis.set_minor_locator(mdates.MonthLocator())
    
    # Set y-axis limits
    ax.set_ylim(bottom=0, top=max_level)
    
    # Remove grid
    ax.grid(False)
    
    # Rotate date labels for better readability
    plt.xticks(rotation=90)
    
    # Add legend
    ax.legend()
    
    # Tight layout
    plt.tight_layout()
    
    # Save figure if output file is provided
    if output_file:
        plt.savefig(output_file, dpi=300)
        print(f"Visualisierung aller Jahre gespeichert unter {output_file}")
    
    # Show plot
    plt.show()

def main():
    """Hauptfunktion zum Laden von Daten und Erstellen von Visualisierungen."""
    # Check if actual data file exists
    if not os.path.exists(ACTUAL_DATA_FILE):
        print(f"Fehler: Tatsächliche Datendatei '{ACTUAL_DATA_FILE}' nicht gefunden.")
        return
    
    # Load actual data (2000-2025)
    actual_df = load_actual_data(ACTUAL_DATA_FILE)
    
    # Load extracted data (pre-2000)
    extracted_df = load_extracted_data()
    
    # Combine data
    combined_df = combine_data(actual_df, extracted_df)
    
    # Normalize data
    normalized_df = normalize_data(combined_df)
    
    # Identify years when buildings were revealed
    revealed_years = identify_revealed_years(normalized_df)
    
    # Create visualization
    print("\nErstelle Visualisierung...")
    create_all_years_visualization(normalized_df, revealed_years, 'edertalsperre_alle_jahre.png')
    
    print("\nVisualisierung abgeschlossen!")

if __name__ == "__main__":
    main()
