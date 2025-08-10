#!/usr/bin/env python3
"""
Update pegelonline-edertalsperre.json with new data from the Pegelonline API.

This script fetches the latest water level data from the Pegelonline API,
merges it with the existing data in pegelonline-edertalsperre.json,
and saves the updated data back to the file.
"""

import json
import requests
import pandas as pd
from datetime import datetime, timedelta
import pytz
import os

# Constants
API_URL = "https://www.pegelonline.wsv.de/webservices/rest-api/v2/stations/c6e9f744-4dbf-4e8e-a219-cab051ec610c/W/measurements.json"
DATA_FILE = "pegelonline-edertalsperre.json"
BACKUP_FILE = "pegelonline-edertalsperre.json.bak"

def fetch_latest_data(days=15):
    """
    Fetch the latest water level data from the Pegelonline API.
    
    Args:
        days (int): Number of days of data to fetch
        
    Returns:
        list: List of data points with timestamp and value
    """
    print(f"Fetching latest data from Pegelonline API (last {days} days)...")
    
    params = {
        "start": f"P{days}D"  # Last X days of data
    }
    
    try:
        response = requests.get(API_URL, params=params)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        data = response.json()
        print(f"Successfully fetched {len(data)} data points from API")
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from API: {e}")
        return []

def load_existing_data():
    """
    Load existing water level data from the JSON file.
    
    Returns:
        list: List of data points with timestamp and value
    """
    if not os.path.exists(DATA_FILE):
        print(f"Data file {DATA_FILE} not found. Creating new file.")
        return []
    
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
        print(f"Loaded {len(data)} existing data points from {DATA_FILE}")
        return data
    except Exception as e:
        print(f"Error loading data from {DATA_FILE}: {e}")
        # Create a backup of the corrupted file if it exists
        if os.path.exists(DATA_FILE):
            backup_name = f"{DATA_FILE}.corrupted.{datetime.now().strftime('%Y%m%d%H%M%S')}"
            os.rename(DATA_FILE, backup_name)
            print(f"Renamed corrupted file to {backup_name}")
        return []

def merge_data(existing_data, new_data):
    """
    Merge existing data with new data, avoiding duplicates.
    
    Args:
        existing_data (list): Existing data points
        new_data (list): New data points from API
        
    Returns:
        list: Merged data points
    """
    print("Merging existing data with new data...")
    
    # Convert to pandas DataFrames for easier manipulation
    if existing_data:
        df_existing = pd.DataFrame(existing_data)
        df_existing['timestamp'] = pd.to_datetime(df_existing['timestamp'])
    else:
        df_existing = pd.DataFrame(columns=['timestamp', 'value'])
    
    df_new = pd.DataFrame(new_data)
    df_new['timestamp'] = pd.to_datetime(df_new['timestamp'])
    
    # Combine and remove duplicates
    df_combined = pd.concat([df_existing, df_new]).drop_duplicates(subset=['timestamp'])
    
    # Sort by timestamp
    df_combined = df_combined.sort_values('timestamp')
    
    # Convert timestamps back to ISO format strings
    result = []
    for _, row in df_combined.iterrows():
        result.append({
            "timestamp": row['timestamp'].isoformat(),
            "value": row['value']
        })
    
    print(f"Merged data has {len(result)} data points")
    
    # Calculate how many new points were added
    new_points = len(result) - len(existing_data)
    print(f"Added {new_points} new data points")
    
    return result

def save_data(data):
    """
    Save data to the JSON file.
    
    Args:
        data (list): Data points to save
    """
    # Create a backup of the existing file
    if os.path.exists(DATA_FILE):
        print(f"Creating backup of {DATA_FILE} as {BACKUP_FILE}")
        try:
            with open(DATA_FILE, 'r') as src, open(BACKUP_FILE, 'w') as dst:
                dst.write(src.read())
        except Exception as e:
            print(f"Error creating backup: {e}")
    
    # Save the updated data
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Saved {len(data)} data points to {DATA_FILE}")
    except Exception as e:
        print(f"Error saving data to {DATA_FILE}: {e}")

def main():
    """Main function to update the water level data."""
    print(f"Starting update at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load existing data
    existing_data = load_existing_data()
    
    # Fetch latest data
    new_data = fetch_latest_data()
    
    if not new_data:
        print("No new data fetched. Exiting.")
        return
    
    # Merge data
    merged_data = merge_data(existing_data, new_data)
    
    # Save merged data
    save_data(merged_data)
    
    print(f"Update completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Print data range
    if merged_data:
        first_date = pd.to_datetime(merged_data[0]['timestamp']).strftime('%Y-%m-%d')
        last_date = pd.to_datetime(merged_data[-1]['timestamp']).strftime('%Y-%m-%d')
        print(f"Data now covers from {first_date} to {last_date}")

if __name__ == "__main__":
    main()
