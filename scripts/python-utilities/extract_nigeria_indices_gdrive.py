"""
Nigeria NDWI and NDMI Extraction Script - Google Drive Export
Exports monthly NDWI and NDMI from NASA HLS data for Nigeria
Exports complete files to Google Drive at 30m resolution
"""

import ee
import os
import sys
from datetime import datetime
import time

# Initialize Earth Engine
try:
    ee.Initialize(project='epidemiological-intelligence')
    print("✓ Earth Engine initialized successfully")
except Exception as e:
    print(f"Error initializing Earth Engine: {e}")
    sys.exit(1)

# Configuration
YEARS = [2015, 2018, 2021, 2023, 2024]
MONTHS = range(7, 13)  # July to December
GOOGLE_DRIVE_FOLDER = 'Rasters'  # Updated to use your existing folder

# Load Nigeria boundary
print("Loading Nigeria boundary...")
nigeria = ee.FeatureCollection("FAO/GAUL_SIMPLIFIED_500m/2015/level0") \
            .filter(ee.Filter.eq("ADM0_NAME", "Nigeria"))
nigeria_geometry = nigeria.geometry()

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
    
    # Compute NDWI: (Green - NIR) / (Green + NIR)
    # HLS bands: B3 = Green, B5 = NIR
    ndwi = merged_collection.map(
        lambda img: img.normalizedDifference(['B3', 'B5']).rename('NDWI')
    ).median().clip(nigeria_geometry)
    
    # Compute NDMI: (NIR - SWIR1) / (NIR + SWIR1)
    # HLS bands: B5 = NIR, B6 = SWIR1
    ndmi = merged_collection.map(
        lambda img: img.normalizedDifference(['B5', 'B6']).rename('NDMI')
    ).median().clip(nigeria_geometry)
    
    return ndwi, ndmi, collection_size

def export_to_drive(image, description, filename, folder):
    """Create export task to Google Drive"""
    task = ee.batch.Export.image.toDrive(
        image=image,
        description=description,
        folder=folder,
        fileNamePrefix=filename,
        region=nigeria_geometry,
        scale=30,
        crs='EPSG:4326',
        maxPixels=1e13,
        fileFormat='GeoTIFF'
    )
    
    task.start()
    return task

def wait_for_tasks(tasks, check_interval=30):
    """Wait for export tasks to complete"""
    print("\nMonitoring export tasks...")
    print("You can also check progress at: https://code.earthengine.google.com/tasks")
    
    while tasks:
        remaining_tasks = []
        for task, name in tasks:
            status = task.status()
            state = status.get('state', 'UNKNOWN')
            
            if state == 'COMPLETED':
                print(f"✓ Completed: {name}")
            elif state == 'FAILED':
                print(f"✗ Failed: {name}")
                error = status.get('error_message', 'Unknown error')
                print(f"  Error: {error}")
            else:
                remaining_tasks.append((task, name))
        
        tasks = remaining_tasks
        
        if tasks:
            print(f"\r{len(tasks)} tasks remaining...", end='')
            time.sleep(check_interval)
    
    print("\nAll tasks processed!")

def main():
    """Main processing function"""
    
    print("\n" + "="*60)
    print("Starting Nigeria NDWI/NDMI Export to Google Drive")
    print(f"Google Drive folder: {GOOGLE_DRIVE_FOLDER}")
    print(f"Years: {YEARS}")
    print(f"Months: July-December")
    print(f"Resolution: 30m")
    print("="*60 + "\n")
    
    # Track all tasks
    all_tasks = []
    
    # Process each year and month
    for year in YEARS:
        print(f"\n--- Processing Year {year} ---")
        
        for month in MONTHS:
            month_str = f"{month:02d}"
            print(f"Setting up exports for {year}-{month_str}...")
            
            try:
                # Compute indices
                ndwi, ndmi, img_count = compute_indices_for_month(year, month)
                print(f"  Found {img_count.getInfo()} images for this month")
                
                # Export NDWI
                ndwi_filename = f"NDWI_{year}_{month_str}_Nigeria"
                ndwi_task = export_to_drive(
                    ndwi,
                    f"NDWI_{year}_{month_str}",
                    ndwi_filename,
                    GOOGLE_DRIVE_FOLDER
                )
                all_tasks.append((ndwi_task, ndwi_filename))
                print(f"  ✓ Started NDWI export: {ndwi_filename}")
                
                # Export NDMI
                ndmi_filename = f"NDMI_{year}_{month_str}_Nigeria"
                ndmi_task = export_to_drive(
                    ndmi,
                    f"NDMI_{year}_{month_str}",
                    ndmi_filename,
                    GOOGLE_DRIVE_FOLDER
                )
                all_tasks.append((ndmi_task, ndmi_filename))
                print(f"  ✓ Started NDMI export: {ndmi_filename}")
                
            except Exception as e:
                print(f"  ✗ Error processing {year}-{month_str}: {str(e)}")
    
    # Summary
    print("\n" + "="*60)
    print(f"Started {len(all_tasks)} export tasks")
    print(f"Files will be saved to Google Drive folder: {GOOGLE_DRIVE_FOLDER}")
    print("="*60)
    
    # Option to monitor tasks
    monitor = input("\nMonitor task progress? (y/n): ")
    if monitor.lower() == 'y':
        wait_for_tasks(all_tasks)
    else:
        print("\nTasks are running in the background.")
        print("Check progress at: https://code.earthengine.google.com/tasks")
        print(f"Files will appear in Google Drive: {GOOGLE_DRIVE_FOLDER}")

if __name__ == "__main__":
    main()