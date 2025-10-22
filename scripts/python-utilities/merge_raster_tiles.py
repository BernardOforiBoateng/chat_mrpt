#!/usr/bin/env python3
"""
Universal Raster Tile Merger
Merges multiple GeoTIFF tiles exported from Google Earth Engine into single files.
Works on Windows, Linux, and macOS.
"""

import os
import sys
import glob
from pathlib import Path
import rasterio
from rasterio.merge import merge
import numpy as np
from collections import defaultdict
import argparse

def find_tile_groups(input_dir):
    """
    Find and group tiles that belong together.
    Tiles from GEE typically have pattern: basename-0000000000-0000000000.tif
    
    Args:
        input_dir: Directory containing the tiles
        
    Returns:
        Dictionary mapping base names to list of tile files
    """
    tile_groups = defaultdict(list)
    
    # Common patterns for GEE exports
    patterns = [
        '*.tif',
        '*.tiff',
        '*.TIF',
        '*.TIFF'
    ]
    
    for pattern in patterns:
        files = glob.glob(os.path.join(input_dir, pattern))
        
        for file in files:
            filename = os.path.basename(file)
            
            # Try to identify the base name (before the tile numbers)
            # GEE pattern: name-0000000000-0000000000.tif
            if '-0000' in filename:
                # Find the position of the first -0000
                idx = filename.find('-0000')
                if idx > 0:
                    base_name = filename[:idx]
                    tile_groups[base_name].append(file)
            # Alternative pattern: name_1.tif, name_2.tif, etc.
            elif '_' in filename and filename.split('_')[-1].split('.')[0].isdigit():
                base_name = '_'.join(filename.split('_')[:-1])
                tile_groups[base_name].append(file)
            # Another pattern: name-00000000.tif
            elif '-' in filename and filename.split('-')[-1].split('.')[0].isdigit():
                base_name = '-'.join(filename.split('-')[:-1])
                tile_groups[base_name].append(file)
            else:
                # Single file, not a tile
                base_name = os.path.splitext(filename)[0]
                if not base_name.endswith('_merged'):
                    tile_groups[base_name].append(file)
    
    # Filter out groups with only one file (not tiles)
    tile_groups = {k: v for k, v in tile_groups.items() if len(v) > 1}
    
    return tile_groups

def merge_tiles(tile_files, output_file, method='first'):
    """
    Merge multiple raster tiles into a single file.
    
    Args:
        tile_files: List of tile file paths
        output_file: Output merged file path
        method: Merge method ('first', 'last', 'min', 'max', 'mean')
    """
    print(f"Merging {len(tile_files)} tiles into {output_file}")
    
    # Open all tile files
    src_files_to_mosaic = []
    for tile in sorted(tile_files):
        src = rasterio.open(tile)
        src_files_to_mosaic.append(src)
        print(f"  - Adding tile: {os.path.basename(tile)}")
    
    # Merge tiles
    mosaic, out_trans = merge(
        src_files_to_mosaic,
        method=method,
        resampling=rasterio.enums.Resampling.bilinear
    )
    
    # Copy metadata from first file and update
    out_meta = src_files_to_mosaic[0].meta.copy()
    out_meta.update({
        "driver": "GTiff",
        "height": mosaic.shape[1],
        "width": mosaic.shape[2],
        "transform": out_trans,
        "compress": "lzw"  # Add compression to reduce file size
    })
    
    # Write merged file
    with rasterio.open(output_file, "w", **out_meta) as dest:
        dest.write(mosaic)
    
    # Close all source files
    for src in src_files_to_mosaic:
        src.close()
    
    # Calculate file sizes
    input_size = sum(os.path.getsize(f) for f in tile_files) / (1024 * 1024)  # MB
    output_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
    
    print(f"✓ Merged successfully!")
    print(f"  Input: {input_size:.2f} MB ({len(tile_files)} files)")
    print(f"  Output: {output_size:.2f} MB")
    print()

def process_directory(input_dir, output_dir=None, cleanup=False):
    """
    Process all tile groups in a directory.
    
    Args:
        input_dir: Directory containing tiles
        output_dir: Output directory (defaults to input_dir/merged)
        cleanup: Whether to delete original tiles after merging
    """
    input_path = Path(input_dir)
    
    if not input_path.exists():
        print(f"Error: Input directory '{input_dir}' does not exist")
        return False
    
    # Set output directory
    if output_dir is None:
        output_path = input_path / 'merged'
    else:
        output_path = Path(output_dir)
    
    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find tile groups
    print(f"Scanning directory: {input_dir}")
    tile_groups = find_tile_groups(input_dir)
    
    if not tile_groups:
        print("No tile groups found. Make sure your tiles follow the pattern:")
        print("  - name-0000000000-0000000000.tif (GEE export pattern)")
        print("  - name_1.tif, name_2.tif, etc.")
        return False
    
    print(f"Found {len(tile_groups)} tile groups to merge:\n")
    
    # Process each tile group
    success_count = 0
    for base_name, tiles in tile_groups.items():
        print(f"Processing: {base_name} ({len(tiles)} tiles)")
        
        # Create output filename
        output_file = output_path / f"{base_name}_merged.tif"
        
        try:
            merge_tiles(tiles, str(output_file))
            success_count += 1
            
            # Clean up original tiles if requested
            if cleanup:
                for tile in tiles:
                    os.remove(tile)
                    print(f"  - Deleted tile: {os.path.basename(tile)}")
        except Exception as e:
            print(f"  ✗ Error merging {base_name}: {str(e)}\n")
            continue
    
    print("=" * 50)
    print(f"Merge complete! Successfully merged {success_count}/{len(tile_groups)} tile groups")
    print(f"Output directory: {output_path}")
    
    return True

def main():
    """Main function with command-line interface."""
    parser = argparse.ArgumentParser(
        description='Merge raster tiles from Google Earth Engine exports',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Merge all tiles in current directory
  python merge_raster_tiles.py .
  
  # Merge tiles from specific folder to custom output
  python merge_raster_tiles.py /path/to/tiles -o /path/to/output
  
  # Merge and delete original tiles
  python merge_raster_tiles.py /path/to/tiles --cleanup
  
  # Merge specific pattern only
  python merge_raster_tiles.py /path/to/tiles --pattern "NDMI*.tif"
        """
    )
    
    parser.add_argument('input_dir', 
                       help='Directory containing the raster tiles')
    parser.add_argument('-o', '--output', 
                       help='Output directory (default: input_dir/merged)')
    parser.add_argument('--cleanup', action='store_true',
                       help='Delete original tiles after merging')
    parser.add_argument('--pattern', 
                       help='File pattern to match (e.g., "NDMI*.tif")')
    
    args = parser.parse_args()
    
    # Check if rasterio is installed
    try:
        import rasterio
    except ImportError:
        print("Error: rasterio is not installed!")
        print("Install it using one of these commands:")
        print("  pip install rasterio")
        print("  conda install -c conda-forge rasterio")
        sys.exit(1)
    
    # Process the directory
    success = process_directory(args.input_dir, args.output, args.cleanup)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    # If no arguments provided, show help
    if len(sys.argv) == 1:
        print("Universal Raster Tile Merger")
        print("=" * 30)
        print("\nUsage: python merge_raster_tiles.py <directory_with_tiles>\n")
        print("For more options: python merge_raster_tiles.py --help")
        sys.exit(0)
    
    main()