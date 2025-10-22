#!/usr/bin/env python3
"""
Download NDMI and NDWI raster files for Nigeria from Sentinel-2 using Google Earth Engine
NDMI: Normalized Difference Moisture Index = (NIR - SWIR1) / (NIR + SWIR1)
NDWI: Normalized Difference Water Index = (Green - NIR) / (Green + NIR)
"""

import ee
import os
import datetime
import time

# Initialize Earth Engine
ee.Initialize()

# Define Nigeria boundary
nigeria = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017').filter(ee.Filter.eq('country_na', 'Nigeria'))

# Define date range
start_date = '2023-01-01'
end_date = '2023-12-31'

def maskS2clouds(image):
    """
    Function to mask clouds from Sentinel-2 images using the QA60 band
    """
    qa = image.select('QA60')
    
    # Bits 10 and 11 are clouds and cirrus, respectively
    cloudBitMask = 1 << 10
    cirrusBitMask = 1 << 11
    
    # Both flags should be set to zero, indicating clear conditions
    mask = qa.bitwiseAnd(cloudBitMask).eq(0).And(qa.bitwiseAnd(cirrusBitMask).eq(0))
    
    return image.updateMask(mask).divide(10000).copyProperties(image, ["system:time_start"])

def addIndices(image):
    """
    Calculate NDMI and NDWI indices
    NDMI = (B8 - B11) / (B8 + B11)  # NIR - SWIR1
    NDWI = (B3 - B8) / (B3 + B8)    # Green - NIR
    """
    ndmi = image.normalizedDifference(['B8', 'B11']).rename('NDMI')
    ndwi = image.normalizedDifference(['B3', 'B8']).rename('NDWI')
    
    return image.addBands([ndmi, ndwi])

# Load Sentinel-2 Surface Reflectance collection
s2_collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                 .filterBounds(nigeria)
                 .filterDate(start_date, end_date)
                 .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                 .map(maskS2clouds)
                 .map(addIndices))

# Calculate median composites
median_composite = s2_collection.select(['NDMI', 'NDWI']).median()

# Clip to Nigeria boundary
ndmi_image = median_composite.select('NDMI').clip(nigeria)
ndwi_image = median_composite.select('NDWI').clip(nigeria)

# Define export parameters
export_params = {
    'scale': 10,  # Sentinel-2 native resolution
    'crs': 'EPSG:4326',
    'region': nigeria.geometry(),
    'maxPixels': 1e13,
    'fileFormat': 'GeoTIFF'
}

# Export NDMI
ndmi_task = ee.batch.Export.image.toDrive(
    image=ndmi_image,
    description='Nigeria_NDMI_Sentinel2_2023',
    folder='GEE_Nigeria_Indices',
    fileNamePrefix='Nigeria_NDMI_S2_2023_median',
    **export_params
)

# Export NDWI
ndwi_task = ee.batch.Export.image.toDrive(
    image=ndwi_image,
    description='Nigeria_NDWI_Sentinel2_2023',
    folder='GEE_Nigeria_Indices',
    fileNamePrefix='Nigeria_NDWI_S2_2023_median',
    **export_params
)

# Start the export tasks
ndmi_task.start()
ndwi_task.start()

print(f"Export tasks started at {datetime.datetime.now()}")
print(f"NDMI Task ID: {ndmi_task.id}")
print(f"NDWI Task ID: {ndwi_task.id}")

# Optional: Monitor task progress
def check_task_status(task):
    """Check the status of an export task"""
    status = task.status()
    return status['state']

# Wait and check status
print("\nMonitoring export progress...")
while True:
    ndmi_status = check_task_status(ndmi_task)
    ndwi_status = check_task_status(ndwi_task)
    
    print(f"\rNDMI: {ndmi_status} | NDWI: {ndwi_status}", end='')
    
    if ndmi_status == 'COMPLETED' and ndwi_status == 'COMPLETED':
        print("\n\nBoth exports completed successfully!")
        print("Check your Google Drive folder 'GEE_Nigeria_Indices' for the output files.")
        break
    elif ndmi_status == 'FAILED' or ndwi_status == 'FAILED':
        print("\n\nOne or more exports failed!")
        break
    
    time.sleep(30)  # Check every 30 seconds

# Additional export options - Monthly composites
def export_monthly_composites():
    """Export monthly NDMI and NDWI composites for time series analysis"""
    months = ee.List.sequence(1, 12)
    
    def create_monthly_composite(month):
        """Create monthly composite for a given month"""
        # Filter by month across all years
        monthly_collection = s2_collection.filter(
            ee.Filter.calendarRange(month, month, 'month')
        )
        
        # Calculate median
        monthly_median = monthly_collection.select(['NDMI', 'NDWI']).median()
        
        return monthly_median.set({
            'month': month,
            'system:time_start': ee.Date.fromYMD(2023, month, 1).millis()
        })
    
    # Map over months
    monthly_composites = ee.ImageCollection(months.map(create_monthly_composite))
    
    # Export each month
    for i in range(1, 13):
        month_image = monthly_composites.filter(ee.Filter.eq('month', i)).first()
        
        # NDMI monthly export
        ndmi_monthly = month_image.select('NDMI').clip(nigeria)
        ndmi_monthly_task = ee.batch.Export.image.toDrive(
            image=ndmi_monthly,
            description=f'Nigeria_NDMI_S2_2023_month{i:02d}',
            folder='GEE_Nigeria_Indices',
            fileNamePrefix=f'Nigeria_NDMI_S2_2023_month{i:02d}',
            **export_params
        )
        ndmi_monthly_task.start()
        
        # NDWI monthly export
        ndwi_monthly = month_image.select('NDWI').clip(nigeria)
        ndwi_monthly_task = ee.batch.Export.image.toDrive(
            image=ndwi_monthly,
            description=f'Nigeria_NDWI_S2_2023_month{i:02d}',
            folder='GEE_Nigeria_Indices',
            fileNamePrefix=f'Nigeria_NDWI_S2_2023_month{i:02d}',
            **export_params
        )
        ndwi_monthly_task.start()
        
        print(f"Started export for month {i}")

# Uncomment to export monthly composites
# export_monthly_composites()

# Statistics calculation
def calculate_statistics():
    """Calculate and print statistics for the indices"""
    # Define reducer
    reducer = ee.Reducer.mean().combine(
        reducer2=ee.Reducer.stdDev(),
        sharedInputs=True
    ).combine(
        reducer2=ee.Reducer.minMax(),
        sharedInputs=True
    )
    
    # Calculate statistics
    ndmi_stats = ndmi_image.reduceRegion(
        reducer=reducer,
        geometry=nigeria.geometry(),
        scale=1000,  # Use coarser scale for statistics
        maxPixels=1e10
    )
    
    ndwi_stats = ndwi_image.reduceRegion(
        reducer=reducer,
        geometry=nigeria.geometry(),
        scale=1000,
        maxPixels=1e10
    )
    
    print("\n\nNDMI Statistics for Nigeria:")
    print(f"Mean: {ndmi_stats.getInfo()['NDMI_mean']:.4f}")
    print(f"Std Dev: {ndmi_stats.getInfo()['NDMI_stdDev']:.4f}")
    print(f"Min: {ndmi_stats.getInfo()['NDMI_min']:.4f}")
    print(f"Max: {ndmi_stats.getInfo()['NDMI_max']:.4f}")
    
    print("\nNDWI Statistics for Nigeria:")
    print(f"Mean: {ndwi_stats.getInfo()['NDWI_mean']:.4f}")
    print(f"Std Dev: {ndwi_stats.getInfo()['NDWI_stdDev']:.4f}")
    print(f"Min: {ndwi_stats.getInfo()['NDWI_min']:.4f}")
    print(f"Max: {ndwi_stats.getInfo()['NDWI_max']:.4f}")

# Uncomment to calculate statistics
# calculate_statistics()