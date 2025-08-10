#!/usr/bin/env python3
"""
Script to extract the water level line from a cropped water level graph image.
"""

import os
import sys
import argparse
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import pandas as pd
from datetime import datetime, timedelta
from scipy.signal import savgol_filter

# Constants for image processing
WATER_LEVEL_MIN_M = 205.0  # Minimum water level in meters (at bottom of image)
PIXELS_PER_METER = 15.0  # Each 15 pixels upward equals 1 meter increase in water level

def extract_water_level_line(image_path, year):
    """
    Extract the water level line from a cropped water level graph image.
    
    Args:
        image_path: Path to the cropped image file
        year: Year of the water level data (for the Wasserwirtschaftsjahr)
    
    Returns:
        DataFrame with timestamps and water level values
    """
    print(f"Extracting water level line from: {image_path}")
    
    # Load the image
    img = Image.open(image_path)
    img_array = np.array(img)
    
    # Get image dimensions
    height, width = img_array.shape[:2]
    print(f"Image dimensions: {width}x{height}")
    
    # Create arrays to store the detected water level at each x position
    water_levels_px = []
    
    # Process each column (x position) in the graph
    for x in range(width):
        column = img_array[:, x]
        
        # For RGB images
        if len(img_array.shape) == 3:
            if img_array.shape[2] >= 3:  # RGB or RGBA
                # Create a mask for blue pixels
                # The water level line is blue, so we look for pixels where blue > red and blue > green
                r, g, b = column[:, 0], column[:, 1], column[:, 2]
                
                # More precise blue detection
                blue_mask = (b > 120) & (b > r * 1.5) & (b > g * 1.5)
                blue_pixels = np.where(blue_mask)[0]
                
                if len(blue_pixels) > 0:
                    # Get the topmost blue pixel (lowest y-value)
                    water_levels_px.append(np.min(blue_pixels))
                else:
                    # If no blue pixel found, use the previous value or a default
                    water_levels_px.append(water_levels_px[-1] if water_levels_px else height // 2)
        else:
            # For grayscale images
            # Find the darkest pixel in this column (assuming the line is dark)
            dark_pixels = np.where(column < 100)[0]
            if len(dark_pixels) > 0:
                water_levels_px.append(np.min(dark_pixels))
            else:
                # If no dark pixel found, use the previous value or a default
                water_levels_px.append(water_levels_px[-1] if water_levels_px else height // 2)
    
    # Convert pixel heights to water levels in meters
    water_levels_m = []
    for px in water_levels_px:
        # Calculate water level based on pixel position
        # The y-axis in the image is inverted (0 at top, max at bottom)
        # Each 15 pixels up from the bottom = 1 meter increase from 205m
        water_level = WATER_LEVEL_MIN_M + ((height - px) / PIXELS_PER_METER)
        # Round to two decimal places
        water_level = round(water_level, 2)
        water_levels_m.append(water_level)
    
    # Generate timestamps for the Wasserwirtschaftsjahr (Nov 1 of previous year to Oct 31 of the year)
    start_date = datetime(year-1, 11, 1)
    end_date = datetime(year, 10, 31)
    total_days = (end_date - start_date).days + 1
    
    # Map x positions to dates
    timestamps = []
    for x in range(width):
        # Calculate the day offset based on the x position
        day_offset = int(x / width * total_days)
        date = start_date + timedelta(days=day_offset)
        timestamps.append(date)
    
    # Create DataFrame
    data = {
        'timestamp': timestamps,
        'value': water_levels_m
    }
    df = pd.DataFrame(data)
    
    return df, water_levels_px

def compare_with_actual_data(extracted_df, year):
    """
    Compare extracted water level data with actual data for validation.
    
    Args:
        extracted_df: DataFrame with extracted water level data
        year: Year to compare (for the Wasserwirtschaftsjahr)
    """
    print(f"\nComparing extracted data with actual data for {year-1}-{year} Wasserwirtschaftsjahr...")
    
    # Hardcoded actual data file
    actual_data_file = "pegelonline-edertalsperre.json"
    
    # Check if actual data file exists
    if not os.path.exists(actual_data_file):
        print(f"Actual data file {actual_data_file} not found, skipping comparison")
        return
    
    # Load actual data
    with open(actual_data_file, 'r') as f:
        import json
        actual_data = json.load(f)
    
    # Convert to DataFrame
    actual_df = pd.DataFrame(actual_data)
    actual_df['timestamp'] = pd.to_datetime(actual_df['timestamp'], utc=True)
    
    # Filter actual data for the Wasserwirtschaftsjahr
    start_date = pd.Timestamp(f"{year-1}-11-01", tz='UTC')
    end_date = pd.Timestamp(f"{year}-10-31", tz='UTC')
    actual_df = actual_df[(actual_df['timestamp'] >= start_date) & (actual_df['timestamp'] <= end_date)]
    
    # Resample actual data to daily values for easier comparison
    actual_df.set_index('timestamp', inplace=True)
    actual_daily = actual_df.resample('D').mean().reset_index()
    
    # Resample extracted data to daily values
    extracted_df['timestamp'] = pd.to_datetime(extracted_df['timestamp'])
    extracted_df.set_index('timestamp', inplace=True)
    extracted_daily = extracted_df.resample('D').mean().reset_index()
    
    # Calculate statistics
    actual_mean = actual_daily['value'].mean()
    extracted_mean = extracted_daily['value'].mean()
    mean_diff = abs(actual_mean - extracted_mean)
    
    actual_min = actual_daily['value'].min()
    extracted_min = extracted_daily['value'].min()
    min_diff = abs(actual_min - extracted_min)
    
    actual_max = actual_daily['value'].max()
    extracted_max = extracted_daily['value'].max()
    max_diff = abs(actual_max - extracted_max)
    
    print(f"Actual data: {len(actual_daily)} days, Mean: {actual_mean:.2f}m, Min: {actual_min:.2f}m, Max: {actual_max:.2f}m")
    print(f"Extracted data: {len(extracted_daily)} days, Mean: {extracted_mean:.2f}m, Min: {extracted_min:.2f}m, Max: {extracted_max:.2f}m")
    print(f"Differences - Mean: {mean_diff:.2f}m, Min: {min_diff:.2f}m, Max: {max_diff:.2f}m")
    
    # Plot comparison
    plt.figure(figsize=(15, 8))
    plt.plot(actual_daily['timestamp'], actual_daily['value'], 'b-', label='Actual Data')
    plt.plot(extracted_daily['timestamp'], extracted_daily['value'], 'r--', label='Extracted Data')
    plt.xlabel('Date')
    plt.ylabel('Water Level (m)')
    plt.title(f'Comparison of Actual vs. Extracted Water Level Data ({year-1}-{year})')
    plt.legend()
    plt.grid(False)
    plt.savefig(f'water_level_comparison_{year}.png')
    print(f"Comparison plot saved to water_level_comparison_{year}.png")
    
    # Visualize the difference
    plt.figure(figsize=(15, 8))
    
    # Convert timestamps to string format for comparison
    actual_daily_copy = actual_daily.copy()
    extracted_daily_copy = extracted_daily.copy()
    
    actual_daily_copy['date_str'] = actual_daily_copy['timestamp'].dt.strftime('%Y-%m-%d')
    extracted_daily_copy['date_str'] = extracted_daily_copy['timestamp'].dt.strftime('%Y-%m-%d')
    
    # Merge the dataframes on date string
    merged_df = pd.merge(actual_daily_copy, extracted_daily_copy, on='date_str', suffixes=('_actual', '_extracted'))
    
    # Calculate the difference
    merged_df['difference'] = merged_df['value_actual'] - merged_df['value_extracted']
    
    # Plot the difference
    plt.plot(merged_df['timestamp_actual'], merged_df['difference'], 'g-')
    plt.axhline(y=0, color='r', linestyle='-')
    plt.xlabel('Date')
    plt.ylabel('Difference (m)')
    plt.title(f'Difference between Actual and Extracted Water Level Data ({year-1}-{year})')
    plt.grid(False)
    plt.savefig(f'water_level_difference_{year}.png')
    print(f"Difference plot saved to water_level_difference_{year}.png")

def visualize_extraction(image_path, water_levels_px, extracted_df, year):
    """
    Visualize the extraction process by overlaying the detected line on the original image.
    
    Args:
        image_path: Path to the cropped image
        water_levels_px: Array of pixel positions of the detected water level line
        extracted_df: DataFrame with extracted water level data
        year: Year of the water level data
    """
    # Load the image
    img = Image.open(image_path)
    img_array = np.array(img)
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))
    
    # Plot the image with the detected line overlaid
    ax1.imshow(img_array)
    ax1.plot(range(len(water_levels_px)), water_levels_px, 'r-', linewidth=2)
    ax1.set_title(f'Detected Water Level Line ({year-1}-{year})')
    ax1.set_xlabel('X Position (pixels)')
    ax1.set_ylabel('Y Position (pixels)')
    
    # Plot the extracted water level data
    plot_df = extracted_df.reset_index()
    ax2.plot(plot_df['timestamp'], plot_df['value'], 'b-')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Water Level (m)')
    ax2.set_title(f'Extracted Water Level Data ({year-1}-{year})')
    ax2.grid(False)
    
    plt.tight_layout()
    plt.savefig(f'extraction_visualization_{year}.png')
    print(f"Extraction visualization saved to extraction_visualization_{year}.png")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Extract water level data from a cropped graph image')
    parser.add_argument('--input', '-i', type=str, help='Input cropped image path', default='cropped_pegel_bild_2024.png')
    parser.add_argument('--year', '-y', type=int, help='Year of the water level data (Wasserwirtschaftsjahr)', default=2024)
    parser.add_argument('--output', '-o', type=str, help='Output CSV file path', default=None)
    parser.add_argument('--actual-data', '-a', type=str, help='Path to actual water level data JSON file', 
                        default='pegelonline-edertalsperre.json')
    
    args = parser.parse_args()
    
    # Set output path if not provided
    if args.output is None:
        args.output = f'extracted_water_level_{args.year}.csv'
    
    # Extract water level data from the image
    extracted_df, water_levels_px = extract_water_level_line(args.input, args.year)
    
    # Save extracted data to CSV
    extracted_df.to_csv(args.output)
    print(f"Extracted data saved to {args.output}")
    
    # Compare with actual data if file exists
    if os.path.exists(args.actual_data):
        compare_with_actual_data(extracted_df, args.actual_data, args.year)
    else:
        print(f"Actual data file {args.actual_data} not found, skipping comparison")
    
    # Visualize the extraction process
    visualize_extraction(args.input, water_levels_px, extracted_df, args.year)

if __name__ == "__main__":
    main()
