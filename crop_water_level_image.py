#!/usr/bin/env python3
"""
Script to crop the relevant graph area from water level images.
"""

import os
import sys
import argparse
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

# Constants for image processing
Y_TOP_CROP = 45  # Pixels to crop from the top
Y_BOTTOM_CROP = 165  # Pixels to crop from the bottom (y-coordinate for 205m water level)
X_START_PX = 121  # Pixel x-coordinate where graph starts
X_WIDTH_PX = 1096  # Width of the graph in pixels
WATER_LEVEL_MIN_M = 205.0  # Minimum water level in meters
WATER_LEVEL_MAX_M = 245.0  # Maximum water level in meters

def crop_image(image_path, output_path=None):
    """
    Crop the graph area from the water level image.
    
    Args:
        image_path: Path to the image file
        output_path: Path to save the cropped image
    
    Returns:
        Path to the cropped image
    """
    return crop_graph_area(image_path, output_path)

def crop_graph_area(image_path, output_path=None):
    """
    Crop the graph area from the water level image.
    
    Args:
        image_path: Path to the image file
        output_path: Path to save the cropped image (if None, will use 'cropped_' prefix)
    
    Returns:
        Path to the cropped image
    """
    print(f"Processing image: {image_path}")
    
    # Load the image
    img = Image.open(image_path)
    img_array = np.array(img)
    
    # Get image dimensions
    height, width = img_array.shape[:2]
    print(f"Image dimensions: {width}x{height}")
    
    # Ensure the image is large enough to crop
    if width < X_START_PX + X_WIDTH_PX or height < Y_TOP_CROP + Y_BOTTOM_CROP:
        print("Error: Image is too small to crop with the specified dimensions")
        return None
    
    # Crop to the graph area
    # Note: PIL crop is (left, upper, right, lower)
    cropped_img = img.crop((X_START_PX, Y_TOP_CROP, X_START_PX + X_WIDTH_PX, height - Y_BOTTOM_CROP))
    
    # Generate output path if not provided
    if output_path is None:
        base_name = os.path.basename(image_path)
        name, ext = os.path.splitext(base_name)
        output_path = f"cropped_{name}{ext}"
    
    # Save the cropped image
    cropped_img.save(output_path)
    print(f"Cropped image saved to: {output_path}")
    
    # Display the original and cropped images
    plt.figure(figsize=(15, 10))
    
    plt.subplot(2, 1, 1)
    plt.imshow(img_array)
    plt.title('Original Image')
    plt.axis('on')
    plt.grid(False)
    
    # Draw rectangle on original image to show crop area
    from matplotlib.patches import Rectangle
    plt.gca().add_patch(Rectangle((X_START_PX, Y_TOP_CROP), X_WIDTH_PX, height - Y_TOP_CROP - Y_BOTTOM_CROP, 
                                  linewidth=2, edgecolor='r', facecolor='none'))
    
    plt.subplot(2, 1, 2)
    plt.imshow(np.array(cropped_img))
    plt.title('Cropped Graph Area')
    plt.axis('on')
    plt.grid(False)
    
    # Add y-axis labels to show water level scale
    y_ticks = np.linspace(0, cropped_img.height, 9)  # 9 points from 0 to cropped height
    y_labels = np.linspace(WATER_LEVEL_MAX_M, WATER_LEVEL_MIN_M, 9)  # Reversed because y-axis is inverted
    plt.yticks(y_ticks, [f"{y:.1f}m" for y in y_labels])
    
    plt.tight_layout()
    plt.savefig(f"crop_visualization_{os.path.basename(image_path)}")
    print(f"Crop visualization saved to: crop_visualization_{os.path.basename(image_path)}")
    
    return output_path

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Crop the graph area from a water level image')
    parser.add_argument('--input', '-i', type=str, help='Input image path', default='pegel_bild_2024.png')
    parser.add_argument('--output', '-o', type=str, help='Output cropped image path', default=None)
    
    args = parser.parse_args()
    
    # Process the image
    cropped_path = crop_graph_area(args.input, args.output)
    
    if cropped_path:
        print(f"Successfully cropped {args.input} to {cropped_path}")
    else:
        print(f"Failed to crop {args.input}")

if __name__ == "__main__":
    main()
