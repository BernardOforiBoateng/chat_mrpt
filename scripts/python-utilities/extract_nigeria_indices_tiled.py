"""
Nigeria NDWI and NDMI Extraction Script - Tiled Version
Extracts monthly NDWI and NDMI from NASA HLS data for Nigeria
Downloads in tiles and merges to maintain 30m resolution
"""

import ee
import os
import sys
from datetime import datetime
import rasterio
from rasterio.merge import merge
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Initialize Earth Engine
try:
    ee.Initialize(project='epidemiological-intelligence')
    print("✓ Earth Engine initialized successfully")
except Exception as e:
    print(f"Error initializing Earth Engine: {e}")
    sys.exit(1)

# Configuration
DROPBOX_PATH = r"C:\Users\bbofo\Urban Malaria Proj Dropbox\urban_malaria\data\nigeria\Raster_files"
YEARS = [2015, 2018, 2021, 2023, 2024]
MONTHS = range(7, 13)  # July to December

# Create subdirectories
ndwi_dir = os.path.join(DROPBOX_PATH, "NDWI")
ndmi_dir = os.path.join(DROPBOX_PATH, "NDMI")
temp_dir = os.path.join(DROPBOX_PATH, "temp_tiles")

for dir_path in [ndwi_dir, ndmi_dir, temp_dir]:
    os.makedirs(dir_path, exist_ok=True)

# Load Nigeria boundary
print("Loading Nigeria boundary...")
nigeria = ee.FeatureCollection("FAO/GAUL_SIMPLIFIED_500m/2015/level0") \
            .filter(ee.Filter.eq("ADM0_NAME", "Nigeria"))
nigeria_geometry = nigeria.geometry()

# Define tiles for Nigeria (split into 4 regions)
def create_tiles():
    """Create 4 tiles covering Nigeria to stay under pixel limits"""
    # Get bounds
    bounds = nigeria_geometry.bounds().getInfo()['coordinates'][0]
    min_lon = min(coord[0] for coord in bounds)
    max_lon = max(coord[0] for coord in bounds)
    min_lat = min(coord[1] for coord in bounds)
    max_lat = max(coord[1] for coord in bounds)
    
    # Split longitude at middle
    mid_lon = (min_lon + max_lon) / 2
    mid_lat = (min_lat + max_lat) / 2
    
    tiles = {
        'NW': ee.Geometry.Rectangle([min_lon, mid_lat, mid_lon, max_lat]),
        'NE': ee.Geometry.Rectangle([mid_lon, mid_lat, max_lon, max_lat]),
        'SW': ee.Geometry.Rectangle([min_lon, min_lat, mid_lon, mid_lat]),
        'SE': ee.Geometry.Rectangle([mid_lon, min_lat, max_lon, mid_lat])
    }
    
    # Clip tiles to Nigeria boundary
    for name, tile in tiles.items():
        tiles[name] = tile.intersection(nigeria_geometry)
    
    return tiles

def download_tile(image, tile_name, tile_geometry, folder, base_filename, scale=30):
    """Download a single tile"""
    try:
        import geemap
        
        tile_filename = f"{base_filename}_{tile_name}.tif"
        tile_path = os.path.join(folder, tile_filename)
        
        # Clip image to tile
        clipped_image = image.clip(tile_geometry)
        
        # Download
        geemap.ee_export_image(
            clipped_image,
            filename=tile_path,
            scale=scale,
            region=tile_geometry,
            file_per_band=False,
            crs='EPSG:4326'
        )
        
        print(f"    ✓ Downloaded tile {tile_name}")
        return tile_path
        
    except Exception as e:
        print(f"    ✗ Error downloading tile {tile_name}: {e}")
        return None

def merge_tiles(tile_paths, output_path):
    """Merge multiple raster tiles into one"""
    try:
        # Open all tiles
        src_files = []
        for path in tile_paths:
            if path and os.path.exists(path):
                src = rasterio.open(path)
                src_files.append(src)
        
        if not src_files:
            print("    ✗ No valid tiles to merge")
            return False
        
        # Merge tiles
        mosaic, out_trans = merge(src_files)
        
        # Copy metadata from first file
        out_meta = src_files[0].meta.copy()
        out_meta.update({
            "driver": "GTiff",
            "height": mosaic.shape[1],
            "width": mosaic.shape[2],
            "transform": out_trans,
            "compress": "lzw"
        })
        
        # Write merged file
        with rasterio.open(output_path, "w", **out_meta) as dest:
            dest.write(mosaic)
        
        # Close source files
        for src in src_files:
            src.close()
        
        # Clean up tile files
        for path in tile_paths:
            if path and os.path.exists(path):
                os.remove(path)
        
        print(f"    ✓ Merged to: {output_path}")
        return True
        
    except Exception as e:
        print(f"    ✗ Error merging tiles: {e}")
        return False

def compute_indices_for_month(year, month):
    """Compute NDWI and NDMI for a specific year and month"""
    start_date = ee.Date.fromYMD(year, month, 1)
    end_date = start_date.advance(1, 'month')
    
    # Get HLS collections
    hls_s2 = ee.ImageCollection('NASA/HLS/HLSS30/v002') \
        .filterDate(start_date, end_date) \
        .filterBounds(nigeria_geometry)
    
    hls_l8 = ee.ImageCollection('NASA/HLS/HLSL30/v002') \
        .filterDate(start_date, end_date) \
        .filterBounds(nigeria_geometry)
    
    # Merge collections
    merged_collection = hls_s2.merge(hls_l8)
    
    # Check if we have data
    collection_size = merged_collection.size()
    
    # Compute indices
    ndwi = merged_collection.map(
        lambda img: img.normalizedDifference(['B3', 'B5']).rename('NDWI')
    ).median()
    
    ndmi = merged_collection.map(
        lambda img: img.normalizedDifference(['B5', 'B6']).rename('NDMI')
    ).median()
    
    return ndwi, ndmi, collection_size

def main():
    """Main processing function with tiling"""
    print("\n" + "="*60)
    print("Starting Nigeria NDWI/NDMI Extraction (Tiled at 30m)")
    print(f"Output directory: {DROPBOX_PATH}")
    print("="*60 + "\n")
    
    # Create tiles
    tiles = create_tiles()
    print(f"Created {len(tiles)} tiles for processing\n")
    
    # Track progress
    total_files = len(YEARS) * len(list(MONTHS)) * 2
    completed = 0
    failed = []
    
    for year in YEARS:
        print(f"\n--- Processing Year {year} ---")
        
        for month in MONTHS:
            month_str = f"{month:02d}"
            print(f"\nProcessing {year}-{month_str}...")
            
            try:
                # Compute indices
                ndwi, ndmi, img_count = compute_indices_for_month(year, month)
                print(f"  Found {img_count.getInfo()} images for this month")
                
                # Process NDWI
                print("  Downloading NDWI tiles...")
                ndwi_tiles = []
                for tile_name, tile_geom in tiles.items():
                    tile_path = download_tile(
                        ndwi, tile_name, tile_geom, temp_dir,
                        f"NDWI_{year}_{month_str}_Nigeria"
                    )
                    if tile_path:
                        ndwi_tiles.append(tile_path)
                
                # Merge NDWI tiles
                ndwi_final = os.path.join(ndwi_dir, f"NDWI_{year}_{month_str}_Nigeria.tif")
                if merge_tiles(ndwi_tiles, ndwi_final):
                    completed += 1
                else:
                    failed.append(f"NDWI_{year}_{month_str}")
                
                # Process NDMI
                print("  Downloading NDMI tiles...")
                ndmi_tiles = []
                for tile_name, tile_geom in tiles.items():
                    tile_path = download_tile(
                        ndmi, tile_name, tile_geom, temp_dir,
                        f"NDMI_{year}_{month_str}_Nigeria"
                    )
                    if tile_path:
                        ndmi_tiles.append(tile_path)
                
                # Merge NDMI tiles
                ndmi_final = os.path.join(ndmi_dir, f"NDMI_{year}_{month_str}_Nigeria.tif")
                if merge_tiles(ndmi_tiles, ndmi_final):
                    completed += 1
                else:
                    failed.append(f"NDMI_{year}_{month_str}")
                
                print(f"Progress: {completed}/{total_files} files completed")
                
            except Exception as e:
                print(f"  ✗ Error processing {year}-{month_str}: {e}")
                failed.extend([f"NDWI_{year}_{month_str}", f"NDMI_{year}_{month_str}"])
    
    # Clean up temp directory
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    
    # Final summary
    print("\n" + "="*60)
    print("EXTRACTION COMPLETE!")
    print(f"Successfully downloaded: {completed}/{total_files} files")
    if failed:
        print(f"Failed downloads: {len(failed)}")
        for f in failed:
            print(f"  - {f}")
    print("="*60)

if __name__ == "__main__":
    main()