#!/usr/bin/env python3
"""
Visualization script for Edertalsperre water level data.
For each year starting 1924, shows the number of years in the last 10 years
where the water level dropped below 224.70m at all.
"""
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import os
import glob
import numpy as np

# Set a nicer font for plots
plt.rcParams['font.family'] = 'Helvetica'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12

# Constants
BUILDING_THRESHOLD = 224.70  # Water level threshold where buildings are revealed
START_YEAR = 1924  # First year to analyze
WINDOW_SIZE = 10  # Number of years to look back

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
    
    if not csv_files:
        print("Keine extrahierten Datendateien gefunden.")
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

def identify_revealed_years(df):
    """Identify years when water level dropped below the building threshold."""
    # Group by year and find minimum water level
    yearly_min = df.resample('YE')['value'].min()
    
    # Find years where minimum water level was below threshold
    revealed_years = yearly_min[yearly_min < BUILDING_THRESHOLD].index.year.tolist()
    
    print(f"Jahre, in denen Gebäude sichtbar wurden (Wasserstand unter {BUILDING_THRESHOLD}m):")
    for year in sorted(revealed_years):
        print(f"- {year}")
    
    return revealed_years

def calculate_revealed_history(revealed_years):
    """
    Calculate for each year starting from START_YEAR, how many years in the 
    previous WINDOW_SIZE years had water levels below the threshold.
    """
    # Get the full range of years from the data
    all_years = range(min(revealed_years), max(revealed_years) + 1)
    
    # Create a dictionary to store the results
    history = {}
    
    # For each year starting from START_YEAR
    for year in [y for y in all_years if y >= START_YEAR]:
        # Count how many years in the previous WINDOW_SIZE years were revealed
        count = sum(1 for y in range(year - WINDOW_SIZE + 1, year + 1) if y in revealed_years)
        history[year] = count
    
    return history

def create_revealed_history_visualization(history, output_file=None):
    """Create a visualization of the revealed years history."""
    # Convert the history dictionary to lists for plotting
    years = list(history.keys())
    counts = list(history.values())
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(15, 8))
    
    # Plot the data as a bar chart
    bars = ax.bar(years, counts, width=0.8, color='#0066cc', alpha=0.7)
    
    # Add a horizontal line at the maximum possible value (WINDOW_SIZE)
    ax.axhline(y=WINDOW_SIZE, color='#cc0000', linestyle='--', alpha=0.8, linewidth=1)
    ax.text(years[0], WINDOW_SIZE, f"Maximum ({WINDOW_SIZE} Jahre)", fontsize=10, 
            verticalalignment='bottom', horizontalalignment='left',
            bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.5', edgecolor='#cc0000'))
    
    # Add data labels above each bar
    for bar, count in zip(bars, counts):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{count}', ha='center', va='bottom', fontsize=8)
    
    # Set labels and title
    ax.set_xlabel('Jahr')
    ax.set_ylabel(f'Anzahl der Jahre (aus den vorherigen {WINDOW_SIZE}) unter {BUILDING_THRESHOLD}m')
    ax.set_title(f'Edertalsperre: Jahre mit sichtbaren Gebäuden ({START_YEAR}-{max(years)})')
    
    # Set y-axis limits
    ax.set_ylim(bottom=0, top=WINDOW_SIZE + 1)
    
    # Set x-axis ticks to show every 5 years
    ax.set_xticks([y for y in years if y % 5 == 0])
    ax.set_xticklabels([str(y) for y in years if y % 5 == 0], rotation=45)
    
    # Add minor ticks for all years
    ax.set_xticks(years, minor=True)
    
    # Add grid for y-axis only
    ax.grid(axis='y', alpha=0.3)
    
    # Tight layout
    plt.tight_layout()
    
    # Save figure if output file is provided
    if output_file:
        plt.savefig(output_file, dpi=300)
        print(f"Visualisierung der sichtbaren Gebäude-Historie gespeichert unter {output_file}")
    
    # Show plot
    plt.show()

def main():
    """Main function to load data and create visualizations."""
    # Check if actual data file exists
    if not os.path.exists(ACTUAL_DATA_FILE):
        print(f"Error: Actual data file '{ACTUAL_DATA_FILE}' not found.")
        return
    
    # Load actual data (2000-2025)
    actual_df = load_actual_data(ACTUAL_DATA_FILE)
    
    # Load extracted data (pre-2000)
    extracted_df = load_extracted_data()
    
    # Combine data
    combined_df = combine_data(actual_df, extracted_df)
    
    # Identify years when buildings were revealed
    revealed_years = identify_revealed_years(combined_df)
    
    # Calculate revealed history
    history = calculate_revealed_history(revealed_years)
    
    # Create visualization
    print("\nErstelle Visualisierung...")
    create_revealed_history_visualization(history, 'edertalsperre_revealed_history.png')
    
    print("\nVisualisierung abgeschlossen!")

if __name__ == "__main__":
    main()
