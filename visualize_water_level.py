#!/usr/bin/env python3
"""Visualisierungsskript für Edertalsperre Wasserstandsdaten.
Beinhaltet Visualisierung von Landmarken-Schwellenwerten und Bericht darüber, wann Landmarken sichtbar wurden.
"""
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import os

# Set a nicer font for plots
plt.rcParams['font.family'] = 'Helvetica'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12

# Constants
NORMALIZATION_OFFSET = 205  # Offset to subtract from all water level values

# File path
DATA_FILE = 'pegelonline-edertalsperre.json'

# Landmark thresholds - name, volume (Mio m³), water level (m)
LANDMARKS = [
    ("Brücke Alt-Bringhausen, Widerlager höchster Punkt", 46.40, 224.70),
    ("Stukenkante/Durchfahrt Schleppbahn/Krananlage Rehbach (6000 kg)", 43.18, 224.00),
    ("Ende Stützbetrieb für die Oberweser", 40.00, 223.28),
    ("Brücke von Alt-Bringhausen nach Scheid, Mittelpfeiler", 39.40, 223.15),
    ("Krananlage Rehbach (4000 kg)", 34.70, 222.00),
    ("Schutthalde am Weissen Stein", 33.50, 221.70),
    ("Sperrmauermodell an der Bericher Hütte", 31.00, 221.05)
]

def load_data(file_path):
    """Lädt Wasserstandsdaten aus JSON-Datei."""
    print(f"Lade Daten aus {file_path}...")
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    print(f"Es wurden {len(data)} Datenpunkte geladen.")
    return data

def process_data(data):
    """Konvertiert JSON-Daten in pandas DataFrame und verarbeitet Zeitstempel."""
    # Convert data to DataFrame
    df = pd.DataFrame(data)
    
    # Convert timestamps to datetime objects
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    
    # Normalize water levels by subtracting the offset
    df['original_value'] = df['value'].copy()  # Keep original values
    df['value'] = df['value'] - NORMALIZATION_OFFSET
    
    # Set timestamp as index
    df.set_index('timestamp', inplace=True)
    
    # Sort by timestamp
    df.sort_index(inplace=True)
    
    return df

def create_visualization(df, output_file=None):
    """Erstellt eine Visualisierung der Wasserstandsdaten."""
    # Calculate figure width based on 25px per month
    # Get number of months in the data
    start_date = df.index.min()
    end_date = df.index.max()
    num_months = (end_date.year - start_date.year) * 12 + end_date.month - start_date.month + 1
    
    # Width: 25px per month (converted to inches for matplotlib, assuming 100 DPI)
    width_inches = num_months * 25 / 100
    
    # Define min_level for fill_between
    min_level = 0
    
    # Calculate max_level for y-axis (30 above the maximum water level)
    max_level = max(df['value']) + 10
    
    # Create figure and axis with calculated width and increased height
    fig, ax = plt.subplots(figsize=(width_inches, 15))
    
    # Plot water level with light blue fill below
    ax.plot(df.index, df['value'], color='#0066cc', linewidth=1.5, label='Wasserstand')
    ax.fill_between(df.index, df['value'], min_level, color='#a8d1ff', alpha=0.6)
    
    # Add landmark threshold lines
    for name, _, original_level in LANDMARKS:
        normalized_level = original_level - NORMALIZATION_OFFSET
        ax.axhline(y=normalized_level, color='#cc0000', linestyle='--', alpha=0.8, linewidth=1)
        # Add text label for each landmark
        ax.text(df.index[0], normalized_level, f"{name} ({original_level}m)", fontsize=10, 
                verticalalignment='bottom', horizontalalignment='left',
                bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.5', edgecolor='#cc0000'))
    
    # Set labels and title
    ax.set_xlabel('Datum')
    ax.set_ylabel('Wasserstand über NN - 205m')
    ax.set_title('Edertalsperre Wasserstand (2000-2025) mit Landmarken-Schwellenwerten')
    
    # Format x-axis to show every month clearly
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    
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
        plt.savefig(output_file)
        print(f"Visualisierung gespeichert unter {output_file}")
    
    # Show plot
    plt.show()

def create_yearly_average_visualization(df, output_file=None):
    """Erstellt eine Visualisierung der jährlichen durchschnittlichen Wasserstände."""
    # Resample data to get yearly averages
    yearly_avg = df.resample('YE').mean()
    
    # Create figure and axis
    plt.figure(figsize=(12, 6))
    
    # Plot yearly average water level
    plt.plot(yearly_avg.index, yearly_avg['value'], 'r-o', linewidth=2)
    
    # Set labels and title
    plt.xlabel('Jahr')
    plt.ylabel('Durchschnittlicher Wasserstand (m)')
    plt.title('Edertalsperre Jährlicher Durchschnittlicher Wasserstand (2000-2025)')
    
    # Format x-axis to show years
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    plt.gca().xaxis.set_major_locator(mdates.YearLocator())
    
    # Set y-axis to start at 0
    plt.ylim(bottom=0)
    
    # Add grid
    plt.grid(True, alpha=0.3)
    
    # Tight layout
    plt.tight_layout()
    
    # Save figure if output file is provided
    if output_file:
        plt.savefig(output_file)
        print(f"Visualisierung der jährlichen Durchschnittswerte gespeichert unter {output_file}")
    
    # Show plot
    plt.show()

def create_monthly_pattern_visualization(df, output_file=None):
    """Erstellt eine Visualisierung, die monatliche Muster im Wasserstand zeigt."""
    # Make sure we're working with a DatetimeIndex
    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError("Index muss ein DatetimeIndex sein")
        
    # Extract month from timestamp
    df_with_month = df.copy()
    df_with_month['month'] = df_with_month.index.month
    
    # Group by month and calculate average
    monthly_avg = df_with_month.groupby('month')['value'].mean()
    
    # Create figure and axis
    plt.figure(figsize=(10, 6))
    
    # Plot monthly average water level
    months = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']
    plt.bar(months, monthly_avg.values)
    
    # Set labels and title
    plt.xlabel('Monat')
    plt.ylabel('Durchschnittlicher Wasserstand (m)')
    plt.title('Edertalsperre Monatliches Wasserstandsmuster (2000-2025)')
    
    # Set y-axis to start at 0
    plt.ylim(bottom=0)
    
    # Add grid
    plt.grid(True, axis='y', alpha=0.3)
    
    # Tight layout
    plt.tight_layout()
    
    # Save figure if output file is provided
    if output_file:
        plt.savefig(output_file)
        print(f"Visualisierung des monatlichen Musters gespeichert unter {output_file}")
    
    # Show plot
    plt.show()

def generate_landmark_report(df):
    """Generiert einen Bericht darüber, wann Landmarken sichtbar wurden (Wasserstand sank unter Schwellenwert)."""
    print("\nLandmarken-Sichtbarkeitsbericht:")
    print("-" * 100)
    print(f"{'Landmarke':<50} {'Wasserstand':<15} {'Erste Sichtbarkeit':<20} {'Tage sichtbar gesamt':<20}")
    print("-" * 100)
    
    for name, _, level in LANDMARKS:
        # Find first date when water level dropped below the landmark threshold
        below_threshold = df[df['original_value'] < level]  # Use original values for comparison
        if not below_threshold.empty:
            first_visible = below_threshold.index[0].strftime('%Y-%m-%d')
            days_visible = (below_threshold.index[-1] - below_threshold.index[0]).days
            print(f"{name:<50} {level:<15.2f} {first_visible:<20} {days_visible:<20}")
        else:
            print(f"{name:<50} {level:<15.2f} {'Nie sichtbar':<20} {'0':<20}")
    
    print("-" * 100)

def create_focused_visualization(df, output_file=None):
    """Erstellt eine fokussierte Visualisierung mit aktuellen Wasserständen und Landmarken."""
    # Get data for the last 5 years
    recent_df = df[df.index >= (df.index.max() - pd.Timedelta(days=365*5))]
    
    # Calculate figure width based on 25px per month for 5 years (60 months)
    width_inches = 60 * 25 / 100  # 60 months * 25px per month / 100 DPI
    
    # Set y-axis limits to focus on the relevant range
    min_level = 0  # Start at 0
    max_level = max(recent_df['value']) + 10  # 10 above the maximum water level
    
    # Create figure and axis with increased height
    fig, ax = plt.subplots(figsize=(width_inches, 15))
    
    # Plot water level with light blue fill below
    ax.plot(recent_df.index, recent_df['value'], color='#0066cc', linewidth=1.5, label='Wasserstand')
    ax.fill_between(recent_df.index, recent_df['value'], min_level, color='#a8d1ff', alpha=0.6)
    
    # Add landmark threshold lines
    for name, _, original_level in LANDMARKS:
        normalized_level = original_level - NORMALIZATION_OFFSET
        ax.axhline(y=normalized_level, color='#cc0000', linestyle='--', alpha=0.8, linewidth=1)
        # Add text label for each landmark
        ax.text(recent_df.index[-1], normalized_level, f"{name} ({original_level}m)", fontsize=10, 
                verticalalignment='bottom', horizontalalignment='right',
                bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.5', edgecolor='#cc0000'))
    
    # Set labels and title
    ax.set_xlabel('Datum')
    ax.set_ylabel('Wasserstand über NN - 205m')
    ax.set_title('Edertalsperre Wasserstand (Letzte 5 Jahre) mit Landmarken-Schwellenwerten')
    
    # Format x-axis to show every month clearly
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    
    # Apply the y-axis limits
    ax.set_ylim(bottom=min_level, top=max_level)
    
    # Remove grid
    ax.grid(False)
    
    # Rotate date labels
    plt.xticks(rotation=90)
    
    # Add legend
    ax.legend()
    
    # Tight layout
    plt.tight_layout()
    
    # Save figure if output file is provided
    if output_file:
        plt.savefig(output_file)
        print(f"Fokussierte Visualisierung gespeichert unter {output_file}")
    
    # Show plot
    plt.show()

def main():
    """Hauptfunktion zum Laden von Daten und Erstellen von Visualisierungen."""
    # Check if data file exists
    if not os.path.exists(DATA_FILE):
        print(f"Fehler: Datendatei '{DATA_FILE}' nicht gefunden.")
        return
    
    # Load data
    data = load_data(DATA_FILE)
    
    # Process data
    df = process_data(data)
    
    # Print some statistics
    print("\nDatenstatistik:")
    print(f"Datumsbereich: {df.index.min()} bis {df.index.max()}")
    print(f"Durchschnittlicher Wasserstand: {df['value'].mean():.2f} m")
    print(f"Minimaler Wasserstand: {df['value'].min():.2f} m")
    print(f"Maximaler Wasserstand: {df['value'].max():.2f} m")
    
    # Generate landmark visibility report
    generate_landmark_report(df)
    
    # Create visualizations
    print("\nErstelle Visualisierungen...")
    
    # Full time series visualization with landmarks
    create_visualization(df, 'edertalsperre_wasserstand.png')
    
    # Focused visualization of recent years with landmarks
    create_focused_visualization(df, 'edertalsperre_fokussierte_ansicht.png')

if __name__ == "__main__":
    main()
