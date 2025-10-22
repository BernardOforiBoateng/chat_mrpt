#!/usr/bin/env python3
"""
Debug Earth Engine exports and check where files are going
"""

import ee
import os

def check_export_destination():
    """Check where exports are configured to go"""
    
    print("="*60)
    print("Debugging Earth Engine Export Configuration")
    print("="*60)
    
    # Check the export script
    print("\n1. Checking your export script configuration...")
    
    script_name = "extract_nigeria_indices_gdrive.py"
    if os.path.exists(script_name):
        print(f"   ✓ Found {script_name}")
        
        # Read the script to find export configuration
        with open(script_name, 'r') as f:
            content = f.read()
            
        # Look for folder name
        if "Nigeria_Raster_Indices" in content:
            print("   ✓ Folder name: Nigeria_Raster_Indices")
        
        # Look for Export.image.toDrive
        if "Export.image.toDrive" in content:
            print("   ✓ Export destination: Google Drive")
            
        # Check for specific folder configuration
        if "folder" in content:
            import re
            folder_matches = re.findall(r"folder\s*[:=]\s*['\"]([^'\"]+)['\"]", content)
            if folder_matches:
                print(f"   ✓ Export folder: {folder_matches[0]}")
    else:
        print(f"   ✗ Script {script_name} not found")
    
    print("\n2. Common issues and solutions:")
    print("   a) Folder might be in 'Shared with me' if using a shared account")
    print("   b) Folder might be in a different Google account")
    print("   c) Exports might have failed silently")
    
    print("\n3. How to search for the files:")
    print("   - In Google Drive, use the search bar")
    print("   - Search for: NDWI_2015")
    print("   - Or search for: *.tif")
    print("   - Check 'Recent' section")
    print("   - Check 'Shared with me'")
    
    print("\n4. Check which Google account you're using:")
    print("   - Earth Engine uses the account you authenticated with")
    print("   - Run: earthengine authenticate --list")
    print("   - This shows which account is active")

def create_test_export():
    """Create a simple test export to verify it works"""
    
    print("\n" + "="*60)
    print("Creating a Test Export")
    print("="*60)
    
    test_code = '''
import ee
ee.Initialize()

# Create a simple test image
test_image = ee.Image(1).rename('test_band')

# Define a small region (1 degree box around Lagos, Nigeria)
test_region = ee.Geometry.Rectangle([3.0, 6.0, 4.0, 7.0])

# Export the test image
test_export = ee.batch.Export.image.toDrive(
    image=test_image,
    description='TEST_EXPORT_NIGERIA',
    folder='Nigeria_Raster_Indices_TEST',
    fileNamePrefix='test_export',
    region=test_region,
    scale=1000,  # 1km resolution for quick test
    maxPixels=1e10
)

# Start the export
test_export.start()
print("Test export started!")
print("Check for folder: Nigeria_Raster_Indices_TEST")
print("File name: test_export.tif")
'''
    
    print("Run this test export code:")
    print("-" * 40)
    print(test_code)
    print("-" * 40)

def check_authentication():
    """Check Earth Engine authentication"""
    
    print("\n" + "="*60)
    print("Checking Authentication")
    print("="*60)
    
    print("\n1. Check which Google account is authenticated:")
    print("   Run: earthengine authenticate --list")
    
    print("\n2. View current credentials:")
    print("   Run: gcloud config list")
    
    print("\n3. Check Earth Engine account:")
    print("   Visit: https://code.earthengine.google.com/")
    print("   See which account is logged in (top right)")

if __name__ == "__main__":
    check_export_destination()
    check_authentication()
    create_test_export()
    
    print("\n" + "="*60)
    print("Additional Steps to Try:")
    print("="*60)
    print("\n1. Create the folder manually:")
    print("   - Go to Google Drive")
    print("   - Create a new folder called 'Nigeria_Raster_Indices'")
    print("   - Run the export script again")
    
    print("\n2. Check export permissions:")
    print("   - Earth Engine might not have Drive access")
    print("   - Re-authenticate: earthengine authenticate --force")
    
    print("\n3. Use Earth Engine Code Editor:")
    print("   - Go to https://code.earthengine.google.com/")
    print("   - Check the Tasks tab there")
    print("   - It might show more details about failures")