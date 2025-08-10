#!/usr/bin/env python3
"""
Visualisierungsskript für Edertalsperre Wasserstandsdaten.
Für jede Woche des Jahres wird die Wahrscheinlichkeit berechnet und visualisiert,
dass der Wasserstand unter 223m liegt, basierend auf den Daten der letzten 10 Jahre.
"""
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import os
import numpy as np

# Set a nicer font for plots
plt.rcParams['font.family'] = 'Helvetica'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12

# Constants
THRESHOLD = 223.0  # Water level threshold in meters
YEARS_TO_ANALYZE = 10  # Number of years to look back
CURRENT_DATE = pd.Timestamp('2025-08-10')  # Current date for reference

# File path
DATA_FILE = 'pegelonline-edertalsperre.json'

def load_data(file_path):
    """Load water level data from JSON file."""
    print(f"Lade Daten aus {file_path}...")
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    print(f"Es wurden {len(data)} Datenpunkte geladen.")
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Convert timestamps to datetime objects
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    
    # Set timestamp as index
    df.set_index('timestamp', inplace=True)
    
    # Sort by timestamp
    df.sort_index(inplace=True)
    
    return df

def filter_last_n_years(df, years=10, reference_date=None):
    """Filter data to the last N years from the reference date."""
    if reference_date is None:
        reference_date = pd.Timestamp.now(tz='UTC')
    else:
        # Make sure reference_date is timezone-aware
        if reference_date.tzinfo is None:
            reference_date = reference_date.tz_localize('UTC')
    
    # Calculate start date (N years before reference date)
    start_date = reference_date - pd.DateOffset(years=years)
    
    # Filter data
    filtered_df = df[df.index >= start_date]
    
    print(f"Gefiltert auf {len(filtered_df)} Datenpunkte aus den letzten {years} Jahren ({start_date.date()} bis {reference_date.date()}).")
    return filtered_df

def calculate_weekly_probabilities(df, threshold):
    """
    Calculate the probability of water level being below the threshold
    for each week of the year.
    """
    # Create a new column for week number (1-53)
    df['week'] = df.index.isocalendar().week
    
    # Create a new column for whether water level is below threshold
    df['below_threshold'] = df['value'] < threshold
    
    # Group by week and calculate probability
    weekly_stats = df.groupby('week')['below_threshold'].agg(['mean', 'count']).reset_index()
    
    # Rename columns for clarity
    weekly_stats.columns = ['week', 'probability', 'count']
    
    # Convert probability to percentage
    weekly_stats['probability'] = weekly_stats['probability'] * 100
    
    return weekly_stats

def create_weekly_probability_visualization(weekly_stats, threshold, output_file=None):
    """Create a visualization of weekly probabilities."""
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(15, 8))
    
    # Plot probability as a line
    ax.plot(weekly_stats['week'], weekly_stats['probability'], 
            color='#0066cc', linewidth=2, marker='o', markersize=6)
    
    # Fill area below the line
    ax.fill_between(weekly_stats['week'], weekly_stats['probability'], 0, 
                   color='#a8d1ff', alpha=0.6)
    
    # Add horizontal lines for reference
    ax.axhline(y=25, color='#cc0000', linestyle='--', alpha=0.7, linewidth=1)
    ax.text(1, 26, '25%', fontsize=10, color='#cc0000')
    
    ax.axhline(y=50, color='#cc0000', linestyle='--', alpha=0.7, linewidth=1)
    ax.text(1, 51, '50%', fontsize=10, color='#cc0000')
    
    ax.axhline(y=75, color='#cc0000', linestyle='--', alpha=0.7, linewidth=1)
    ax.text(1, 76, '75%', fontsize=10, color='#cc0000')
    
    # Set labels and title
    ax.set_xlabel('Kalenderwoche')
    ax.set_ylabel(f'Wahrscheinlichkeit für Wasserstand unter {threshold}m (%)')
    ax.set_title(f'Edertalsperre: Wöchentliche Wahrscheinlichkeit für Wasserstand unter {threshold}m\n(Basierend auf den letzten {YEARS_TO_ANALYZE} Jahren: {CURRENT_DATE.year-YEARS_TO_ANALYZE}-{CURRENT_DATE.year})')
    
    # Set x-axis ticks to show every 4 weeks
    ax.set_xticks([w for w in weekly_stats['week'] if w % 4 == 0])
    
    # Add minor ticks for all weeks
    ax.set_xticks(weekly_stats['week'], minor=True)
    
    # Set y-axis limits
    ax.set_ylim(bottom=0, top=100)
    
    # Add grid for better readability
    ax.grid(True, alpha=0.3)
    
    # Add month labels
    month_weeks = {
        'Jan': 1, 'Feb': 5, 'Mär': 9, 'Apr': 14, 
        'Mai': 18, 'Jun': 22, 'Jul': 27, 
        'Aug': 31, 'Sep': 36, 'Okt': 40, 
        'Nov': 44, 'Dez': 49
    }
    
    for month, week in month_weeks.items():
        if week in weekly_stats['week'].values:
            ax.annotate(month, xy=(week, -5), xycoords=('data', 'axes fraction'),
                        ha='center', va='top', fontsize=10)
    
    # Add annotations for high probability weeks
    high_prob_weeks = weekly_stats[weekly_stats['probability'] > 75]
    if not high_prob_weeks.empty:
        max_prob_week = high_prob_weeks.loc[high_prob_weeks['probability'].idxmax()]
        ax.annotate(f"Höchste: {max_prob_week['probability']:.1f}%",
                   xy=(max_prob_week['week'], max_prob_week['probability']),
                   xytext=(max_prob_week['week'], max_prob_week['probability'] + 5),
                   arrowprops=dict(facecolor='black', shrink=0.05, width=1.5),
                   ha='center')
    
    # Add text box with explanation
    explanation_text = (
        f"Diese Grafik zeigt die Wahrscheinlichkeit, dass der Wasserstand\n"
        f"der Edertalsperre für jede Woche des Jahres unter {threshold}m liegt,\n"
        f"basierend auf Daten von {CURRENT_DATE.year-YEARS_TO_ANALYZE} bis {CURRENT_DATE.year}."
    )
    ax.text(0.02, 0.02, explanation_text, transform=ax.transAxes, fontsize=10,
            verticalalignment='bottom', horizontalalignment='left',
            bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=0.5'))
    
    # Tight layout
    plt.tight_layout()
    
    # Save figure if output file is provided
    if output_file:
        plt.savefig(output_file, dpi=300)
        print(f"Wöchentliche Wahrscheinlichkeitsvisualisierung gespeichert unter {output_file}")
    
    # Show plot
    plt.show()

def main():
    """Hauptfunktion zum Laden von Daten und Erstellen von Visualisierungen."""
    # Check if data file exists
    if not os.path.exists(DATA_FILE):
        print(f"Fehler: Datendatei '{DATA_FILE}' nicht gefunden.")
        return
    
    # Load data
    df = load_data(DATA_FILE)
    
    # Filter to the last N years
    filtered_df = filter_last_n_years(df, years=YEARS_TO_ANALYZE, reference_date=CURRENT_DATE)
    
    # Calculate weekly probabilities
    weekly_stats = calculate_weekly_probabilities(filtered_df, THRESHOLD)
    
    # Create visualization
    print("\nErstelle Visualisierung...")
    create_weekly_probability_visualization(weekly_stats, THRESHOLD, 'edertalsperre_woechentliche_wahrscheinlichkeit.png')
    
    print("\nVisualisierung abgeschlossen!")

if __name__ == "__main__":
    main()
