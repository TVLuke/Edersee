#!/usr/bin/env python3
"""
Update Pegelonline data and generate interactive visualization.

This script executes the following steps in sequence:
1. Update the pegelonline-edertalsperre.json file with new data from the API
2. Generate the interactive HTML visualization page

Usage:
    python update_and_generate.py
"""

import os
import sys
import subprocess
from datetime import datetime

def run_script(script_name):
    """
    Run a Python script and print its output.
    
    Args:
        script_name (str): Name of the script to run
    
    Returns:
        bool: True if script executed successfully, False otherwise
    """
    print(f"\n{'='*80}")
    print(f"Running {script_name} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    try:
        # Run the script and capture output
        result = subprocess.run(
            [sys.executable, script_name],
            check=True,
            text=True,
            capture_output=True
        )
        
        # Print the output
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        print(f"\n{'-'*80}")
        print(f"{script_name} completed successfully")
        print(f"{'-'*80}\n")
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_name}:")
        print(f"Exit code: {e.returncode}")
        print("STDOUT:")
        print(e.stdout)
        print("STDERR:")
        print(e.stderr)
        return False

def main():
    """Main function to update data and generate visualization."""
    print(f"Starting update and generate process at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Update Pegelonline data
    update_script = "update_pegelonline_data.py"
    if not os.path.exists(update_script):
        print(f"Error: {update_script} not found")
        return
    
    update_success = run_script(update_script)
    if not update_success:
        print("Warning: Update script failed or had errors")
        # Continue anyway, as we might still want to generate the visualization
    
    # Step 2: Generate interactive visualization
    generate_script = "interactive_water_level_explorer.py"
    if not os.path.exists(generate_script):
        print(f"Error: {generate_script} not found")
        return
    
    generate_success = run_script(generate_script)
    if not generate_success:
        print("Error: Generate script failed")
        return
    
    print(f"\nUpdate and generate process completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("The interactive visualization has been updated with the latest data")
    
    # Check if the output file exists
    output_file = "index.html"
    if os.path.exists(output_file):
        print(f"Output file created: {output_file}")
        file_size = os.path.getsize(output_file) / 1024  # Size in KB
        print(f"File size: {file_size:.2f} KB")
    else:
        print(f"Warning: Output file {output_file} not found")

if __name__ == "__main__":
    main()
