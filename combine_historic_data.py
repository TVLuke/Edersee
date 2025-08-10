#!/usr/bin/env python3
"""
Combine all historic extracted water level CSV files into a single CSV file.
This script finds all extracted_water_level_*.csv files and combines them into
a single CSV file for easier loading in the interactive explorer.
"""

import os
import glob
import pandas as pd

# Output file name
OUTPUT_FILE = "combined_historic_data.csv"

def combine_csv_files():
    """Combine all extracted water level CSV files into a single CSV file."""
    print(f"Combining historic water level data into {OUTPUT_FILE}...")
    
    # Find all extracted water level CSV files
    csv_files = glob.glob("extracted_water_level_*.csv")
    
    if not csv_files:
        print("No extracted water level CSV files found.")
        return
    
    print(f"Found {len(csv_files)} CSV files to combine.")
    
    # Initialize an empty list to store DataFrames
    dfs = []
    
    # Read each CSV file and append to the list
    for csv_file in sorted(csv_files):
        try:
            year = csv_file.replace("extracted_water_level_", "").replace(".csv", "")
            print(f"Processing data for year {year}...")
            df = pd.read_csv(csv_file)
            
            # Ensure timestamp column exists
            if "timestamp" not in df.columns:
                # Some files might have different column names
                if "date" in df.columns:
                    df.rename(columns={"date": "timestamp"}, inplace=True)
            
            # Add to the list
            dfs.append(df)
        except Exception as e:
            print(f"Error processing {csv_file}: {e}")
    
    if not dfs:
        print("No valid data found in CSV files.")
        return
    
    # Combine all DataFrames
    combined_df = pd.concat(dfs, ignore_index=True)
    
    # Sort by timestamp
    if "timestamp" in combined_df.columns:
        combined_df.sort_values("timestamp", inplace=True)
    
    # Save to CSV
    combined_df.to_csv(OUTPUT_FILE, index=False)
    print(f"Combined data saved to {OUTPUT_FILE}")
    print(f"Total data points: {len(combined_df)}")

if __name__ == "__main__":
    combine_csv_files()
