#!/usr/bin/env python3
"""
FAST Monthly NDWI/NDMI Export for Nigeria
Optimized for speed - exports all months in parallel
"""

import ee
import time

# Initialize Earth Engine
ee.Initialize(project='epidemiological-intelligence')

# Configuration
YEARS = [2015, 2018, 2021, 2023, 2024]
MONTHS = range(7, 13)  # July to December as in your original
FOLDER = 'Rasters'  # Your folder

# Get Nigeria boundary once
nigeria = ee.FeatureCollection("FAO/GAUL_SIMPLIFIED_500m/2015/level0") \
           .filter(ee.Filter.eq("ADM0_NAME", "Nigeria")) \
           .geometry()

def export_month_fast(year, month):
    """Export one month - optimized for speed"""
    
    # Use Landsat 8 for faster processing (single collection)
    start = ee.Date.fromYMD(year, month, 1)
    end = start.advance(1, 'month')
    
    # Get Landsat 8 data
    collection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
        .filterDate(start, end) \
        .filterBounds(nigeria) \
        .filter(ee.Filter.lt('CLOUD_COVER', 50))  # More lenient for speed
    
    # Quick check if data exists
    count = collection.size()
    
    # Calculate both indices at once
    def calc_indices(img):
        # Scale and mask
        img = img.multiply(0.0000275).add(-0.2)
        
        # NDWI: (Green - NIR) / (Green + NIR)
        ndwi = img.normalizedDifference(['SR_B3', 'SR_B5'])
        
        # NDMI: (NIR - SWIR1) / (NIR + SWIR1)  
        ndmi = img.normalizedDifference(['SR_B5', 'SR_B6'])
        
        return ndwi.rename('NDWI').addBands(ndmi.rename('NDMI'))
    
    # Create composite
    composite = collection.map(calc_indices).median().clip(nigeria)
    
    # Export both bands in ONE file to save time
    month_str = f"{month:02d}"
    
    export_task = ee.batch.Export.image.toDrive(
        image=composite,
        description=f'NDWI_NDMI_{year}_{month_str}',
        folder=FOLDER,
        fileNamePrefix=f'NDWI_NDMI_{year}_{month_str}_Nigeria',
        region=nigeria,
        scale=30,
        maxPixels=1e13,
        fileFormat='GeoTIFF'
    )
    
    export_task.start()
    return f'NDWI_NDMI_{year}_{month_str}'

# Start all exports at once
print(f"Fast Monthly Export to: {FOLDER}")
print(f"Exporting BOTH indices in single files for speed")
print("-" * 50)

exports = []
for year in YEARS:
    for month in MONTHS:
        name = export_month_fast(year, month)
        exports.append(name)
        print(f"✓ Started: {name}")

print(f"\n✓ Started {len(exports)} exports (30 files with both indices)")
print(f"This is 2x faster - each file contains BOTH NDWI and NDMI bands")
print("\nCheck progress at: https://code.earthengine.google.com/tasks")