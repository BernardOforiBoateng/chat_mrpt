#!/usr/bin/env python3
"""
Nigeria HLS NDWI/NDMI Export - SINGLE FILES (No Tiles)
Forces mosaicking to create one file per month
"""

import ee
import time

# Initialize Earth Engine
print("Initializing Earth Engine...")
ee.Initialize(project='epidemiological-intelligence')

# Define Nigeria boundary
nigeria = ee.FeatureCollection("FAO/GAUL_SIMPLIFIED_500m/2015/level0") \
            .filter(ee.Filter.eq("ADM0_NAME", "Nigeria"))
nigeria_geometry = nigeria.geometry()

# Define parameters
years = [2015, 2018, 2021, 2023, 2024]
start_month = 7
end_month = 12

# Your folder
FOLDER = 'Rasters'

# Calculate indices
def compute_ndwi(img):
    return img.normalizedDifference(['B3', 'B5']).rename('NDWI')

def compute_ndmi(img):
    return img.normalizedDifference(['B5', 'B6']).rename('NDMI')

# Track exports
all_exports = []

print(f"\nStarting SINGLE FILE exports to folder: {FOLDER}")
print("="*50)

for year in years:
    print(f"\nProcessing year {year}...")
    
    for month in range(start_month, end_month + 1):
        start = ee.Date.fromYMD(year, month, 1)
        end = start.advance(1, 'month')
        
        # Get HLS collections
        s2 = ee.ImageCollection('NASA/HLS/HLSS30/v002') \
            .filterDate(start, end) \
            .filterBounds(nigeria_geometry)
        
        l8 = ee.ImageCollection('NASA/HLS/HLSL30/v002') \
            .filterDate(start, end) \
            .filterBounds(nigeria_geometry)
        
        # Merge collections
        merged = s2.merge(l8)
        
        month_str = f"{month:02d}"
        
        # CRITICAL: Create mosaics to ensure single files
        # Process NDWI - mosaic() ensures single output
        ndwi_collection = merged.map(compute_ndwi)
        ndwi_monthly = ndwi_collection.median().clip(nigeria_geometry)
        
        # Reproject to ensure single file output
        ndwi_monthly = ndwi_monthly.reproject(
            crs='EPSG:4326',
            scale=30
        ).toFloat()  # Ensure consistent data type
        
        # Export NDWI as single file
        ndwi_task = ee.batch.Export.image.toDrive(
            image=ndwi_monthly,
            description=f'NDWI_{year}_{month_str}_Nigeria',
            folder=FOLDER,
            fileNamePrefix=f'NDWI_{year}_{month_str}_Nigeria',
            region=nigeria_geometry,
            scale=30,
            crs='EPSG:4326',
            maxPixels=1e13,
            fileFormat='GeoTIFF',
            formatOptions={
                'cloudOptimized': True  # Creates single cloud-optimized GeoTIFF
            }
        )
        ndwi_task.start()
        all_exports.append((ndwi_task, f'NDWI_{year}_{month_str}'))
        
        # Process NDMI - same approach
        ndmi_collection = merged.map(compute_ndmi)
        ndmi_monthly = ndmi_collection.median().clip(nigeria_geometry)
        
        # Reproject to ensure single file output
        ndmi_monthly = ndmi_monthly.reproject(
            crs='EPSG:4326',
            scale=30
        ).toFloat()
        
        # Export NDMI as single file
        ndmi_task = ee.batch.Export.image.toDrive(
            image=ndmi_monthly,
            description=f'NDMI_{year}_{month_str}_Nigeria',
            folder=FOLDER,
            fileNamePrefix=f'NDMI_{year}_{month_str}_Nigeria',
            region=nigeria_geometry,
            scale=30,
            crs='EPSG:4326',
            maxPixels=1e13,
            fileFormat='GeoTIFF',
            formatOptions={
                'cloudOptimized': True
            }
        )
        ndmi_task.start()
        all_exports.append((ndmi_task, f'NDMI_{year}_{month_str}'))
        
        print(f"  ✓ Started SINGLE FILE exports for {year}-{month_str}")

print(f"\n{'='*50}")
print(f"Total exports: {len(all_exports)} SINGLE FILES")
print("Each export will create ONE GeoTIFF file (no tiles)")
print(f"Files will appear in: {FOLDER}")
print("\nCheck progress at: https://code.earthengine.google.com/tasks")

# Optional: Monitor progress
monitor = input("\nMonitor progress? (y/n): ")
if monitor.lower() == 'y':
    print("\nMonitoring tasks...")
    completed = 0
    failed = 0
    
    while all_exports:
        remaining = []
        for task, name in all_exports:
            status = task.status()
            state = status.get('state', 'UNKNOWN')
            
            if state == 'COMPLETED':
                print(f"✓ Completed: {name}.tif (SINGLE FILE)")
                completed += 1
            elif state == 'FAILED':
                print(f"✗ Failed: {name}")
                failed += 1
                error = status.get('error_message', 'Unknown error')
                print(f"  Error: {error}")
            elif state in ['READY', 'RUNNING']:
                remaining.append((task, name))
        
        all_exports = remaining
        if all_exports:
            print(f"\r{len(all_exports)} tasks remaining... ({completed} completed, {failed} failed)", end='', flush=True)
            time.sleep(30)
    
    print(f"\n\n✓ Export complete! {completed} single files created.")
else:
    print("\nExports running in background.")