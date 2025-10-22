#!/usr/bin/env python3
"""
Exact Python version of your working Earth Engine code
Uses NASA HLS data for NDWI/NDMI monthly exports
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

# Define parameters (same as your code)
years = [2021, 2023, 2024]
start_month = 7
end_month = 12

# Your folder
FOLDER = 'Nigeria_Raster_Indices'  # Back to the original working folder

# Calculate NDWI for HLS
# NDWI = (Green - NIR) / (Green + NIR)
# HLS bands: B3 = Green, B5 = NIR
def compute_ndwi(img):
    return img.normalizedDifference(['B3', 'B5']).rename('NDWI') \
              .copyProperties(img, ["system:time_start"])

# Calculate NDMI for HLS
# NDMI = (NIR - SWIR1) / (NIR + SWIR1)
# HLS bands: B5 = NIR, B6 = SWIR1
def compute_ndmi(img):
    return img.normalizedDifference(['B5', 'B6']).rename('NDMI') \
              .copyProperties(img, ["system:time_start"])

# Track all exports
export_count = 0
all_exports = []

print(f"\nStarting exports to folder: {FOLDER}")
print("="*50)

# Process and export (exact translation of your JS code)
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
        
        # Format month
        month_str = f"{month:02d}"
        
        # Process NDWI
        ndwi_monthly = merged.map(compute_ndwi).median().clip(nigeria_geometry)
        
        # Reproject to ensure single file output
        ndwi_monthly = ndwi_monthly.reproject(
            crs='EPSG:4326',
            scale=30
        ).toFloat()
        
        ndwi_task = ee.batch.Export.image.toDrive(
            image=ndwi_monthly,
            description=f'NDWI_{year}_{month_str}',
            folder=FOLDER,
            fileNamePrefix=f'NDWI_{year}_{month_str}',
            region=nigeria_geometry,
            scale=30,
            crs='EPSG:4326',
            maxPixels=1e13,
            fileFormat='GeoTIFF',
            formatOptions={
                'cloudOptimized': True
            }
        )
        ndwi_task.start()
        all_exports.append((ndwi_task, f'NDWI_{year}_{month_str}'))
        
        # Process NDMI
        ndmi_monthly = merged.map(compute_ndmi).median().clip(nigeria_geometry)
        
        # Reproject to ensure single file output
        ndmi_monthly = ndmi_monthly.reproject(
            crs='EPSG:4326',
            scale=30
        ).toFloat()
        
        ndmi_task = ee.batch.Export.image.toDrive(
            image=ndmi_monthly,
            description=f'NDMI_{year}_{month_str}',
            folder=FOLDER,
            fileNamePrefix=f'NDMI_{year}_{month_str}',
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
        
        export_count += 2
        print(f"  ✓ Started exports for {year}-{month_str} (NDWI & NDMI)")

print(f"\n{'='*50}")
print(f"Total exports: {export_count}")
print("HLS Band mapping: B3=Green, B5=NIR, B6=SWIR1")
print(f"Files will appear in: {FOLDER}")
print("\nCheck progress at: https://code.earthengine.google.com/tasks")

# Optional: Monitor progress
monitor = input("\nMonitor progress? (y/n): ")
if monitor.lower() == 'y':
    print("\nMonitoring tasks...")
    while all_exports:
        remaining = []
        for task, name in all_exports:
            status = task.status()
            state = status.get('state', 'UNKNOWN')
            
            if state == 'COMPLETED':
                print(f"✓ Completed: {name}")
            elif state == 'FAILED':
                print(f"✗ Failed: {name}")
            elif state in ['READY', 'RUNNING']:
                remaining.append((task, name))
        
        all_exports = remaining
        if all_exports:
            print(f"\r{len(all_exports)} tasks remaining...", end='', flush=True)
            time.sleep(30)
    
    print("\n✓ All exports completed!")
else:
    print("\nExports running in background. Check Earth Engine Tasks tab.")