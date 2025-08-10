#!/usr/bin/env python3
"""
Interaktive HTML-Visualisierung für Edertalsperre Wasserstandsdaten.
Erstellt eine eigenständige HTML-Seite zur Erkundung der Daten mit Datumsbereichsauswahl
und Anmerkungen zu historischen Ereignissen.
"""
import json
import pandas as pd
import os
import glob
from datetime import datetime

# Constants
NORMALIZATION_OFFSET = 205  # Offset to subtract from all water level values
BUILDING_THRESHOLD = 224.70  # Water level threshold where buildings are revealed

# File paths
ACTUAL_DATA_FILE = 'pegelonline-edertalsperre.json'
TEMPLATE_FILE = 'templates/water_level_explorer.html'
OUTPUT_FILE = 'index.html'

# Historical events to mark on the timeline
HISTORICAL_EVENTS = [
    {"period": [1910, 1914], "name": "Bauzeit", "type": "range"},
    {"date": "1914-08-01", "end_date": "1918-11-11", "name": "Erster Weltkrieg", "type": "range"},
    {"date": "1914-08-15", "name": "Inbetriebnahme", "type": "point"},
    {"date": "1915-01-01", "name": "Inbetriebnahme eines Wasserkraftwerks", "type": "point"},
    {"date": "1939-09-01", "end_date": "1945-09-02", "name": "Zweiter Weltkrieg", "type": "range"},
    {"date": "1943-05-17", "name": "Beschädigung durch Bombenangriff", "type": "point"},
    {"date": "1946-01-01", "end_date": "1947-12-31", "name": "Sanierung", "type": "range"},
    {"date": "1947-01-01", "end_date": "1948-12-31", "name": "Sanierung", "type": "range"},
    {"date": "1961-01-01", "end_date": "1962-12-31", "name": "Sanierung", "type": "range"},
    {"date": "1988-01-01", "name": "Absenkung des zulässigen Aufstaus um 1,5m auf 243,5m ü. NHN", "type": "point"},
    {"date": "1991-01-01", "end_date": "1994-12-31", "name": "Sanierung - Wieder voller Aufstau möglich", "type": "range"}
]

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
    """Load extracted water level data from combined CSV file."""
    print("Lade extrahierte Daten aus combined_historic_data.csv...")
    
    combined_file = "combined_historic_data.csv"
    
    if not os.path.exists(combined_file):
        print(f"Datei {combined_file} nicht gefunden. Bitte zuerst combine_historic_data.py ausführen.")
        return None
    
    try:
        # Load the combined CSV file
        df = pd.read_csv(combined_file)
        
        # Make timestamps timezone-aware to match actual data
        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize('UTC')
        df.set_index('timestamp', inplace=True)
        
        # Sort by timestamp
        df.sort_index(inplace=True)
        
        print(f"Es wurden {len(df)} extrahierte Datenpunkte aus {combined_file} geladen.")
        return df
    except Exception as e:
        print(f"Fehler beim Laden von {combined_file}: {e}")
        return None

def combine_data(actual_df, extracted_df):
    """Combine actual and extracted data.
    
    For years 2000 and later, use only actual data from Pegelonline JSON.
    For years before 2000, use extracted data.
    """
    if extracted_df is None:
        print("Keine extrahierten Daten zum Kombinieren. Nur tatsächliche Daten werden verwendet.")
        return actual_df
    
    # Ensure column names match
    if 'value' not in extracted_df.columns:
        print("Fehler: Spalte 'value' nicht in extrahierten Daten gefunden.")
        return actual_df
    
    # Filter extracted data to only include years before 2000
    # Handle timezone-aware timestamps by converting cutoff date to UTC
    cutoff_date = pd.Timestamp('2000-01-01', tz='UTC')
    
    # Check if extracted_df index is timezone-aware
    if extracted_df.index.tz is None:
        # Convert extracted_df index to timezone-aware
        extracted_df.index = extracted_df.index.tz_localize('UTC')
    
    # Check if actual_df index is timezone-aware
    if actual_df.index.tz is None:
        # Convert actual_df index to timezone-aware
        actual_df.index = actual_df.index.tz_localize('UTC')
        
    # Now filter with timezone-aware timestamps
    extracted_df_filtered = extracted_df[extracted_df.index < cutoff_date]
    actual_df_filtered = actual_df[actual_df.index >= cutoff_date]
    
    # Combine the filtered dataframes
    combined_df = pd.concat([extracted_df_filtered, actual_df_filtered])
    
    # Sort by timestamp
    combined_df.sort_index(inplace=True)
    
    print(f"Kombinierte Daten haben {len(combined_df)} Datenpunkte.")
    print(f"  - Extrahierte Daten (vor 2000): {len(extracted_df_filtered)} Datenpunkte")
    print(f"  - Tatsächliche Daten (ab 2000): {len(actual_df_filtered)} Datenpunkte")
    
    return combined_df

def normalize_data(df):
    """Normalize water level values by subtracting the offset."""
    df['value'] = df['value'] - NORMALIZATION_OFFSET
    return df

def identify_revealed_years(df):
    """Identify years when water level dropped below the building threshold."""
    # Normalize the threshold
    normalized_threshold = BUILDING_THRESHOLD - NORMALIZATION_OFFSET
    
    # Group by year and check if any value is below threshold
    yearly_min = df.groupby(df.index.year)['value'].min()
    revealed_years = yearly_min[yearly_min < normalized_threshold].index.tolist()
    
    print("Jahre, in denen Gebäude sichtbar wurden (Wasserstand unter 224.7m):")
    for year in sorted(revealed_years):
        print(f"- {year}")
    
    return revealed_years

def create_interactive_html(df, revealed_years, output_file=OUTPUT_FILE):
    """Create an interactive HTML visualization."""
    print(f"\nErstelle interaktive HTML-Visualisierung in {output_file}...")
    
    # Debug output to check data range
    print(f"Data range in input DataFrame: {df.index.min()} to {df.index.max()}")
    print(f"Total data points in input DataFrame: {len(df)}")
    
    # Check for any data after 2000 before resampling
    post_2000_data = df[df.index >= pd.Timestamp('2000-01-01', tz='UTC')]
    print(f"Data points after 2000 before resampling: {len(post_2000_data)}")
    print(f"Post-2000 data range: {post_2000_data.index.min()} to {post_2000_data.index.max()}")
    
    # Debug the post-2000 data before resampling
    print(f"Post-2000 data index type: {type(post_2000_data.index)}")
    print(f"Post-2000 data index dtype: {post_2000_data.index.dtype}")
    print(f"Post-2000 data timezone: {post_2000_data.index.tz}")
    
    # Try a completely different approach: manually create daily data
    # Create a date range from min to max date
    start_date = df.index.min().floor('D')
    end_date = df.index.max().floor('D')
    print(f"Creating date range from {start_date} to {end_date}")
    
    # Create a new DataFrame with daily dates
    date_range = pd.date_range(start=start_date, end=end_date, freq='D', tz='UTC')
    daily_df = pd.DataFrame(index=date_range, columns=['value'])
    
    # Group by day and calculate mean
    for day, group in df.groupby(df.index.floor('D')):
        daily_df.loc[day, 'value'] = group['value'].mean()
    
    # Drop any NaN values
    daily_df.dropna(inplace=True)
    
    # Reset index to convert timestamp to a column
    daily_df = daily_df.reset_index()
    daily_df.rename(columns={'index': 'timestamp'}, inplace=True)
    
    # Debug the manually created daily data
    print(f"Daily data index type: {type(daily_df.index)}")
    print(f"Daily data index dtype: {daily_df.index.dtype}")
    print(f"Daily data timestamp column type: {type(daily_df['timestamp'])}")
    print(f"Daily data timestamp dtype: {daily_df['timestamp'].dtype}")
    
    print(f"Data range after daily resampling: {daily_df['timestamp'].min()} to {daily_df['timestamp'].max()}")
    print(f"Total data points after daily resampling: {len(daily_df)}")
    
    # Check if post-2000 data is included
    post_2000_daily_check = daily_df[daily_df['timestamp'] >= pd.Timestamp('2000-01-01', tz='UTC')]
    print(f"Data points after 2000 after resampling: {len(post_2000_daily_check)}")
    if len(post_2000_daily_check) > 0:
        print(f"Post-2000 daily data range: {post_2000_daily_check['timestamp'].min()} to {post_2000_daily_check['timestamp'].max()}")
    else:
        print("No post-2000 data after resampling!")
    
    # Calculate yearly average for second line using the same approach as daily data
    # Create a date range from min to max date by year
    start_year = df.index.min().year
    end_year = df.index.max().year
    print(f"Creating yearly averages from {start_year} to {end_year}")
    
    # Create a new DataFrame for yearly averages
    yearly_dates = [pd.Timestamp(f"{year}-12-31", tz='UTC') for year in range(start_year, end_year + 1)]
    yearly_avg = pd.DataFrame(index=yearly_dates, columns=['value'])
    
    # Group by year and calculate mean
    for year, group in df.groupby(df.index.year):
        yearly_avg.loc[pd.Timestamp(f"{year}-12-31", tz='UTC'), 'value'] = group['value'].mean()
    
    # Drop any NaN values
    yearly_avg.dropna(inplace=True)
    
    # Reset index to get timestamp as column
    yearly_avg = yearly_avg.reset_index()
    yearly_avg.rename(columns={'index': 'timestamp'}, inplace=True)
    
    print(f"Yearly average data range: {yearly_avg['timestamp'].min()} to {yearly_avg['timestamp'].max()}")
    print(f"Total yearly average data points: {len(yearly_avg)}")
    
    # Format timestamp for JavaScript
    daily_df['timestamp'] = daily_df['timestamp'].dt.strftime('%Y-%m-%d')
    yearly_avg['timestamp'] = yearly_avg['timestamp'].dt.strftime('%Y-%m-%d')
    
    # Debug output for yearly average data
    print("\nYearly average data sample:")
    print(yearly_avg.head())
    
    # Convert to list of dictionaries for JSON
    data_json = daily_df.to_dict(orient='records')
    yearly_avg_json = yearly_avg.to_dict(orient='records')
    
    # Format historical events for JavaScript
    events_json = []
    for event in HISTORICAL_EVENTS:
        if event['type'] == 'range':
            if 'period' in event:
                # Convert year range to dates
                start_date = f"{event['period'][0]}-01-01"
                end_date = f"{event['period'][1]}-12-31"
                events_json.append({
                    'start': start_date,
                    'end': end_date,
                    'name': event['name'],
                    'type': 'range'
                })
            else:
                events_json.append({
                    'start': event['date'],
                    'end': event['end_date'],
                    'name': event['name'],
                    'type': 'range'
                })
        else:  # point event
            events_json.append({
                'date': event['date'],
                'name': event['name'],
                'type': 'point'
            })
    
    # Format revealed years for JavaScript
    revealed_years_json = []
    for year in revealed_years:
        revealed_years_json.append({
            'start': f"{year}-01-01",
            'end': f"{year}-12-31",
            'year': year
        })
    
    # Convert data to JSON strings
    data_json_str = json.dumps(data_json)
    yearly_avg_json_str = json.dumps(yearly_avg_json)
    events_json_str = json.dumps(events_json)
    revealed_years_json_str = json.dumps(revealed_years_json)
    building_threshold_normalized = BUILDING_THRESHOLD - NORMALIZATION_OFFSET
    
    # Read the template file
    with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Replace placeholders in the template using simple string replacement
    html_content = html_content.replace('WATER_LEVEL_DATA_PLACEHOLDER', data_json_str)
    html_content = html_content.replace('YEARLY_AVG_DATA_PLACEHOLDER', yearly_avg_json_str)
    html_content = html_content.replace('HISTORICAL_EVENTS_PLACEHOLDER', events_json_str)
    html_content = html_content.replace('REVEALED_YEARS_PLACEHOLDER', revealed_years_json_str)
    html_content = html_content.replace('BUILDING_THRESHOLD_NORMALIZED_PLACEHOLDER', str(building_threshold_normalized))
    html_content = html_content.replace('BUILDING_THRESHOLD_PLACEHOLDER', str(BUILDING_THRESHOLD))
    html_content = html_content.replace('NORMALIZATION_OFFSET_PLACEHOLDER', str(NORMALIZATION_OFFSET))
    
    # Write the HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Interaktive HTML-Visualisierung wurde in {output_file} gespeichert.")

def main():
    """Main function to create the interactive HTML visualization."""
    # Load actual data
    actual_df = load_actual_data(ACTUAL_DATA_FILE)
    
    # Load extracted data
    extracted_df = load_extracted_data()
    
    # Combine data
    combined_df = combine_data(actual_df, extracted_df)
    
    # Normalize data
    normalized_df = normalize_data(combined_df.copy())
    
    # Identify years when buildings were revealed
    revealed_years = identify_revealed_years(combined_df)
    
    # Create interactive HTML visualization
    create_interactive_html(normalized_df, revealed_years)
    
    print("\nFertig!")

if __name__ == "__main__":
    main()
