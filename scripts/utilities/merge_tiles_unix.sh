#!/bin/bash

echo "========================================"
echo "Universal Raster Tile Merger for Linux/Mac"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3"
    exit 1
fi

# Check if rasterio is installed
if ! python3 -c "import rasterio" &> /dev/null; then
    echo "rasterio is not installed. Installing now..."
    pip3 install rasterio
    if [ $? -ne 0 ]; then
        echo ""
        echo "Failed to install rasterio. Try running:"
        echo "  pip3 install rasterio"
        echo "or"
        echo "  conda install -c conda-forge rasterio"
        exit 1
    fi
fi

# Get the directory path
read -p "Enter the path to folder containing tiles: " input_dir

# Check if directory exists
if [ ! -d "$input_dir" ]; then
    echo "ERROR: Directory does not exist: $input_dir"
    exit 1
fi

echo ""
echo "Processing tiles in: $input_dir"
echo ""

# Run the merge script
python3 merge_raster_tiles.py "$input_dir"

echo ""
echo "========================================"
echo "Process complete! Check the 'merged' folder"
echo "========================================"