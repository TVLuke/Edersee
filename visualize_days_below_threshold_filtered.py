#!/usr/bin/env python3
"""
Visualization script for Edertalsperre water level data.
For each year starting 1924, shows the number of days in the last 10 years
where the water level dropped below 223.28m (Ende Stützbetrieb für die Oberweser).
Excludes years where the water level was intentionally reduced for inspection or renovation.
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
OBERWESER_THRESHOLD = 223.28  # Water level threshold for "Ende Stützbetrieb für die Oberweser"
START_YEAR = 1924  # First year to analyze
WINDOW_SIZE = 10  # Number of years to look back

# Years to exclude (intentional drawdowns for inspection/renovation)
EXCLUDED_YEARS = [1943, 1946, 1947, 1948, 1961, 1962, 1991, 1992, 1993, 1994]

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

def filter_excluded_years(df):
    """Filter out data from excluded years."""
    # Create a copy of the dataframe
    filtered_df = df.copy()
    
    # Filter out excluded years
    for year in EXCLUDED_YEARS:
        start_date = pd.Timestamp(f"{year}-01-01", tz='UTC')
        end_date = pd.Timestamp(f"{year}-12-31", tz='UTC')
        
        # Replace values in excluded years with NaN
        mask = (filtered_df.index >= start_date) & (filtered_df.index <= end_date)
        filtered_df.loc[mask, 'value'] = np.nan
    
    print(f"Daten aus {len(EXCLUDED_YEARS)} ausgeschlossenen Jahren herausgefiltert: {', '.join(map(str, sorted(EXCLUDED_YEARS)))}")
    return filtered_df

def calculate_days_below_threshold(df):
    """
    Calculate for each year starting from START_YEAR, how many days in the 
    previous WINDOW_SIZE years had water levels below the threshold.
    """
    # Resample to daily frequency and take the minimum value for each day
    daily_min = df.resample('D')['value'].min()
    
    # Find days where water level was below the threshold
    below_threshold = daily_min < OBERWESER_THRESHOLD
    
    # Create a dictionary to store the results
    days_history = {}
    
    # Get the full range of years from the data
    min_year = daily_min.index.min().year
    max_year = daily_min.index.max().year
    all_years = range(min_year, max_year + 1)
    
    # For each year starting from START_YEAR
    for year in [y for y in all_years if y >= START_YEAR]:
        # Define the 10-year window
        start_date = pd.Timestamp(f"{year-WINDOW_SIZE+1}-01-01", tz='UTC')
        end_date = pd.Timestamp(f"{year}-12-31", tz='UTC')
        
        # Count days below threshold in this window
        window_data = below_threshold[start_date:end_date]
        days_count = window_data.sum()  # Sum of True values
        
        days_history[year] = days_count
    
    return days_history

def create_days_below_threshold_visualization(days_history, output_file=None):
    print("\nErstelle Visualisierung...")
    # Convert the history dictionary to lists for plotting
    years = list(days_history.keys())
    days_counts = list(days_history.values())
    
    # Calculate the maximum possible days (10 years * 365.25 days)
    max_possible_days = WINDOW_SIZE * 365.25
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(15, 8))
    
    # Plot the data as a bar chart
    bars = ax.bar(years, days_counts, width=0.8, color='#0066cc', alpha=0.7)
     
    # Add data labels above bars that are significant
    for bar, count in zip(bars, days_counts):
        if count > max_possible_days * 0.1:  # Only label bars that are >10% of max
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 5,
                    f'{int(count)}', ha='center', va='bottom', fontsize=8)
    
    # Set labels and title
    ax.set_xlabel('Jahr')
    ax.set_ylabel(f'Anzahl der Tage unter {OBERWESER_THRESHOLD}m in den vorherigen {WINDOW_SIZE} Jahren')
    ax.set_title(f'Edertalsperre: Tage unter "Ende Stützbetrieb für die Oberweser" Schwellenwert ({START_YEAR}-{max(years)})\nOhne absichtliche Absenkungen')
    
    # Set y-axis limits
    ax.set_ylim(bottom=0, top=max(days_counts) * 1.1)  # 10% above the maximum count
    
    # Set x-axis ticks to show every 5 years
    ax.set_xticks([y for y in years if y % 5 == 0])
    ax.set_xticklabels([str(y) for y in years if y % 5 == 0], rotation=45)
    
    # Add minor ticks for all years
    ax.set_xticks(years, minor=True)
    
    # Add grid for y-axis only
    ax.grid(axis='y', alpha=0.3)
    
    # Add a text box listing the excluded years
    excluded_years_text = "Ausgeschlossene Jahre (absichtliche Absenkungen):\n" + ", ".join(map(str, sorted(EXCLUDED_YEARS)))
    ax.text(0.98, 0.02, excluded_years_text, transform=ax.transAxes, fontsize=9,
            verticalalignment='bottom', horizontalalignment='right',
            bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.5'))
    
    # Tight layout
    plt.tight_layout()
    
    # Save figure if output file is provided
    if output_file:
        plt.savefig(output_file, dpi=300)
        print(f"Visualisierung der Tage unter Schwellenwert gespeichert unter {output_file}")
    
    # Show plot
    plt.show()

def main():
    """Main function to load data and create visualizations."""
    # Load actual data
    if os.path.exists(ACTUAL_DATA_FILE):
        actual_df = load_actual_data(ACTUAL_DATA_FILE)
    else:
        print(f"Warning: Actual data file {ACTUAL_DATA_FILE} not found.")
        actual_df = None
    
    # Load extracted data
    extracted_df = load_extracted_data()
    
    # Combine data
    df = combine_data(actual_df, extracted_df)
    
    if df is None or df.empty:
        print("Error: No data available for analysis.")
        return
    
    # Filter out excluded years
    df = filter_excluded_years(df)
    
    # Calculate days below threshold history
    days_history = calculate_days_below_threshold(df)
    
    # Create visualization
    output_file = f"tage_unter_{OBERWESER_THRESHOLD}_filtered.png"
    # HTML export removed
    create_days_below_threshold_visualization(
        days_history, 
        output_file=output_file
    )
    
    print("\nVisualisierung abgeschlossen!")
    print(f"PNG-Visualisierung gespeichert unter {output_file}")
    # HTML export message removed

if __name__ == "__main__":
    main()
