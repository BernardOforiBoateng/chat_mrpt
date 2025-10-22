"""
Nigeria NDWI and NDMI Extraction Script
Extracts monthly NDWI and NDMI from NASA HLS data for Nigeria
Saves directly to Dropbox as single GeoTIFF files
"""

import ee
import os
import sys
from datetime import datetime

# Initialize Earth Engine
try:
    # Try to initialize with cloud project
    ee.Initialize(project='epidemiological-intelligence')
    print("✓ Earth Engine initialized successfully")
except Exception as e:
    try:
        # Fallback to regular initialization
        ee.Initialize()
        print("✓ Earth Engine initialized successfully")
    except Exception as e2:
        print(f"Error initializing Earth Engine: {e2}")
        print("Please run: earthengine authenticate")
        print("Or set up a Google Cloud Project for Earth Engine")
        sys.exit(1)

# Configuration
DROPBOX_PATH = r"C:\Users\bbofo\Urban Malaria Proj Dropbox\urban_malaria\data\nigeria\Raster_files"
YEARS = [2015, 2018, 2021, 2023, 2024]
MONTHS = range(7, 13)  # July to December

# Create subdirectories for organization
ndwi_dir = os.path.join(DROPBOX_PATH, "NDWI")
ndmi_dir = os.path.join(DROPBOX_PATH, "NDMI")

# Create directories if they don't exist
for dir_path in [ndwi_dir, ndmi_dir]:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"✓ Created directory: {dir_path}")

# Load Nigeria boundary
print("Loading Nigeria boundary...")
nigeria = ee.FeatureCollection("FAO/GAUL_SIMPLIFIED_500m/2015/level0") \
            .filter(ee.Filter.eq("ADM0_NAME", "Nigeria"))

# Get the geometry for exports
nigeria_geometry = nigeria.geometry()

def download_single_geotiff(image, description, folder, filename, scale=60):
    """
    Download Earth Engine image as a single GeoTIFF
    Uses getDownloadURL for direct download
    """
    try:
        # Get download URL with specific parameters to ensure single file
        url = image.getDownloadURL({
            'name': filename,
            'scale': scale,
            'crs': 'EPSG:4326',
            'region': nigeria_geometry,
            'format': 'GEO_TIFF',
            'maxPixels': 1e13
        })
        
        # Download the file
        import urllib.request
        output_path = os.path.join(folder, filename + '.tif')
        
        print(f"  Downloading {filename}...")
        urllib.request.urlretrieve(url, output_path)
        print(f"  ✓ Saved to: {output_path}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error downloading {filename}: {str(e)}")
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

def main():
    """Main processing function"""
    
    print("\n" + "="*60)
    print("Starting Nigeria NDWI/NDMI Extraction")
    print(f"Output directory: {DROPBOX_PATH}")
    print(f"Years: {YEARS}")
    print(f"Months: July-December")
    print("="*60 + "\n")
    
    # Track progress
    total_files = len(YEARS) * len(list(MONTHS)) * 2  # 2 indices
    completed = 0
    failed = []
    
    # Process each year and month
    for year in YEARS:
        print(f"\n--- Processing Year {year} ---")
        
        for month in MONTHS:
            month_str = f"{month:02d}"
            print(f"\nProcessing {year}-{month_str}...")
            
            try:
                # Compute indices
                ndwi, ndmi, img_count = compute_indices_for_month(year, month)
                print(f"  Found {img_count.getInfo()} images for this month")
                
                # Download NDWI
                ndwi_filename = f"NDWI_{year}_{month_str}_Nigeria"
                success_ndwi = download_single_geotiff(
                    ndwi, 
                    f"NDWI {year}-{month_str}",
                    ndwi_dir,
                    ndwi_filename
                )
                
                if success_ndwi:
                    completed += 1
                else:
                    failed.append(ndwi_filename)
                
                # Download NDMI
                ndmi_filename = f"NDMI_{year}_{month_str}_Nigeria"
                success_ndmi = download_single_geotiff(
                    ndmi,
                    f"NDMI {year}-{month_str}", 
                    ndmi_dir,
                    ndmi_filename
                )
                
                if success_ndmi:
                    completed += 1
                else:
                    failed.append(ndmi_filename)
                
                # Progress update
                print(f"Progress: {completed}/{total_files} files completed")
                
            except Exception as e:
                print(f"  ✗ Error processing {year}-{month_str}: {str(e)}")
                failed.extend([f"NDWI_{year}_{month_str}", f"NDMI_{year}_{month_str}"])
    
    # Final summary
    print("\n" + "="*60)
    print("EXTRACTION COMPLETE!")
    print(f"Successfully downloaded: {completed}/{total_files} files")
    if failed:
        print(f"Failed downloads: {len(failed)}")
        for f in failed:
            print(f"  - {f}")
    print("="*60)

# Alternative: Using geemap for better control
def main_with_geemap():
    """Alternative using geemap library for more robust downloads"""
    try:
        import geemap
    except ImportError:
        print("Installing geemap...")
        os.system("pip install geemap")
        import geemap
    
    print("\n" + "="*60)
    print("Starting Nigeria NDWI/NDMI Extraction (using geemap)")
    print("="*60 + "\n")
    
    for year in YEARS:
        for month in MONTHS:
            month_str = f"{month:02d}"
            print(f"\nProcessing {year}-{month_str}...")
            
            # Compute indices
            ndwi, ndmi, img_count = compute_indices_for_month(year, month)
            
            # Export NDWI
            ndwi_path = os.path.join(ndwi_dir, f"NDWI_{year}_{month_str}_Nigeria.tif")
            geemap.ee_export_image(
                ndwi,
                filename=ndwi_path,
                scale=30,
                region=nigeria_geometry,
                file_per_band=False,
                crs='EPSG:4326'
            )
            print(f"  ✓ Exported NDWI to: {ndwi_path}")
            
            # Export NDMI
            ndmi_path = os.path.join(ndmi_dir, f"NDMI_{year}_{month_str}_Nigeria.tif")
            geemap.ee_export_image(
                ndmi,
                filename=ndmi_path,
                scale=30,
                region=nigeria_geometry,
                file_per_band=False,
                crs='EPSG:4326'
            )
            print(f"  ✓ Exported NDMI to: {ndmi_path}")

if __name__ == "__main__":
    # Check if geemap is available
    try:
        import geemap
        print("Using geemap method (recommended)...")
        main_with_geemap()
    except ImportError:
        print("Using direct download method...")
        print("For better reliability, install geemap: pip install geemap")
        main()