#!/usr/bin/env python3
"""
Coordinator script to download water level images for each year and process them using existing scripts.
- Downloads images for each year (1914-2024)
- Calls crop_water_level_image.py to crop the graph area
- Calls extract_water_level_line.py to extract water level data
"""

import os
import sys
import requests
import subprocess
from tqdm import tqdm
import argparse

# Import functions from other scripts
import crop_water_level_image
import extract_water_level_line

def get_image_url(year):
    """
    Get the URL for the water level image for a specific year.
    
    Args:
        year: The year to get the image for
        
    Returns:
        The URL for the image
    """
    # Use the correct URL based on year
    if year >= 2021:
        return f"https://wasserstand.edersee.me/images_jahr/pegel_bild_{year}.png"
    elif 2001 <= year < 2020:
        return f"https://wasserstand.edersee.me/images_jahr/archiv/pegel_bild_{year}.png"
    else:
        return f"https://wasserstand.edersee.me/images_jahr/archiv_1914/pegel_bild_{year}.png"


def download_image(url, output_path):
    """
    Download an image from a URL and save it to a file.
    
    Args:
        url: The URL to download from
        output_path: The path to save the image to
        
    Returns:
        True if successful, False otherwise
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return True
    except Exception as e:
        print(f"Error downloading image: {e}")
        return False

def process_year(year):
    """
    Process a single year: download image and call existing scripts.
    
    Args:
        year: Year to process
    
    Returns:
        True if successful, False otherwise
    """
    print("="*80)
    print(f"Processing year {year}")
    print("="*80)
    
    # Define file paths
    image_path = f"pegel_bild_{year}.png"
    cropped_path = f"cropped_pegel_bild_{year}.png"
    extracted_csv = f"extracted_water_level_{year}.csv"
    
    # Step 1: Crop the image
    print(f"Cropping image for {year}")
    try:
        crop_water_level_image.crop_image(image_path, cropped_path)
    except Exception as e:
        print(f"Error cropping image: {e}")
        return False
    
    # Step 2: Extract water level data
    print(f"Extracting water level data for {year}")
    try:
        # Extract water level data from the image
        extracted_df, water_levels_px = extract_water_level_line.extract_water_level_line(cropped_path, year)
        
        # Save extracted data to CSV
        extracted_df.to_csv(extracted_csv)
        print(f"Extracted data saved to {extracted_csv}")
        
        # Compare with actual data (the function will check if the file exists)
        extract_water_level_line.compare_with_actual_data(extracted_df, year)
        
        # Visualize the extraction process
        extract_water_level_line.visualize_extraction(cropped_path, water_levels_px, extracted_df, year)
        
    except Exception as e:
        print(f"Error extracting water level data: {e}")
        return False
    
    print(f"Successfully processed year {year}")
    return True

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Download and process historical water level data')
    parser.add_argument('start_year', type=int, nargs='?', default=2024,
                        help='Start year (default: 2024)')
    parser.add_argument('end_year', type=int, nargs='?', default=None,
                        help='End year (default: same as start_year)')
    
    args = parser.parse_args()
    
    # Set end_year to start_year if not provided
    if args.end_year is None:
        args.end_year = args.start_year
    
    # Validate year range
    if args.start_year < 1914 or args.end_year > 2024:
        print("Error: Years must be between 1914 and 2024")
        return 1
    
    if args.start_year > args.end_year:
        print("Error: Start year must be less than or equal to end year")
        return 1
    
    print(f"Processing years {args.start_year} to {args.end_year}")
    
    # Process each year in the range
    years = list(range(args.start_year, args.end_year + 1))
    success_count = 0
    failed_years = []
    
    for year in tqdm(years):
        # Step 1: Always download the image
        image_path = f"pegel_bild_{year}.png"
        
        # Remove existing image if it exists
        if os.path.exists(image_path):
            os.remove(image_path)
            
        print(f"Downloading image for {year}")
        url = get_image_url(year)
        if not download_image(url, image_path):
            print(f"Failed to download image for {year}, skipping")
            failed_years.append(year)
            continue
        
        # Step 2: Process the year
        if process_year(year):
            success_count += 1
        else:
            failed_years.append(year)
    
    # Print summary
    print("\nProcessing complete!")
    print(f"Successfully processed {success_count} years")
    print(f"Failed to process {len(failed_years)} years")
    
    if failed_years:
        print(f"Failed years: {failed_years}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
