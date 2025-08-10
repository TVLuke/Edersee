# Edertalsperre Water Level Visualization

This project provides tools for visualizing and analyzing historical water level data of the Edertalsperre (Eder Dam) in Germany. It includes scripts for data extraction, processing, and interactive visualization.

## Overview

The Edertalsperre is one of Germany's largest dams, built between 1908 and 1914. This project aims to visualize and analyze water level data from 1914 to the present day, showing historical trends and notable events that affected the water level.

This project is a little one day open data exploration. More on that at http://tvluke.de/edertalsperre.html (in German)

## Features

- **Data Extraction**: Extract water level data from historical images
- **Data Processing**: Process and normalize water level measurements
- **Interactive Visualization**: Create interactive HTML visualizations of water level data
- **Historical Analysis**: Identify periods when buildings became visible due to low water levels
- **Automated Updates**: Fetch the latest data from the Pegelonline API

## Key Components

### Data Sources

- **Historical Data (1914-1999)**: Extracted from yearly water level images
- **Recent Data (2000-present)**: Fetched from the Pegelonline API

### Main Scripts

- `main.py`: The primary script that orchestrates the entire data processing and visualization pipeline
- `download_and_process_historical_data.py`: Downloads and processes historical water level images
- `crop_water_level_image.py`: Crops the water level images to extract the relevant graph area
- `extract_water_level_line.py`: Extracts water level data from the cropped images
- `combine_historic_data.py`: Combines all historical CSV files into one dataset
- `update_pegelonline_data.py`: Updates the water level data from the Pegelonline API
- `update_and_generate.py`: Combines the update and visualization steps
- `interactive_water_level_explorer.py`: Creates an interactive HTML visualization

### Visualization Scripts

- `visualize_all_years.py`: Creates a complete water level history visualization from 1914 to present
- `visualize_1943_bombing.py`: Focused visualization of the period around the RAF bombing (May 17, 1943)
- `visualize_building_revealed_history.py`: Analysis of when low water levels revealed submerged buildings
- `visualize_days_below_threshold.py`: Analysis of days when water level dropped below critical thresholds
- `visualize_days_below_threshold_filtered.py`: Similar to above but excludes years with intentional drawdowns
- `visualize_weekly_probability.py`: Calculates and visualizes the probability of water levels below threshold by week
- `visualize_water_level.py`: Creates the basic water level visualization

## Setup and Usage

### Requirements

Install the required dependencies:

```bash
pip install -r requirements.txt
```

### Basic Usage

1. **Update water level data**:
   ```bash
   python update_pegelonline_data.py
   ```

2. **Generate interactive visualization**:
   ```bash
   python interactive_water_level_explorer.py
   ```

3. **Do both in one step**:
   ```bash
   python update_and_generate.py
   ```

## Automated Updates

This project includes a GitHub Action workflow that automatically:
1. Updates the water level data from the Pegelonline API
2. Generates the interactive visualization
3. Deploys the visualization to a web server

The workflow runs weekly and can also be triggered manually.

## Note on Use of LLMs

This code was created using, among other tools, LLM tools like ChatGPT.