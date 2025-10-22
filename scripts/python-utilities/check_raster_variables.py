#!/usr/bin/env python3
"""Check raster database for all variables from the CSV"""

import os
import glob

def check_raster_database():
    """Check if all required variables have corresponding raster files"""

    print("=" * 70)
    print("RASTER DATABASE VARIABLE CHECK")
    print("=" * 70)

    # Define variable mappings to raster directories
    variable_mappings = {
        'Test positivity rate (u5_tpr_rdt)': {
            'directories': ['rasters/pf_parasite_rate/', 'rasters/tpr/', 'rasters/test_positivity/'],
            'patterns': ['*tpr*', '*TPR*', '*positivity*', '*parasite*'],
            'notes': 'May be represented by PfPR (Plasmodium falciparum Parasite Rate)'
        },
        'Nighttime lights': {
            'directories': ['rasters/night_timel_lights/', 'rasters/nighttime_lights/', 'rasters/ntl/'],
            'patterns': ['*night*', '*light*', '*ntl*', '*NTL*'],
            'notes': 'Night time lights data'
        },
        'Housing quality': {
            'directories': ['rasters/housing/', 'rasters/housing_quality/', 'rasters/hq/'],
            'patterns': ['*housing*', '*quality*', '*hq*', '*HQ*'],
            'notes': 'Housing quality indicators'
        },
        'Soil wetness': {
            'directories': ['rasters/surface_soil_wetness/', 'rasters/soil_wetness/', 'rasters/soil/'],
            'patterns': ['*soil*', '*wetness*', '*moisture*'],
            'notes': 'Surface soil wetness/moisture'
        },
        'Distance to waterbodies': {
            'directories': ['rasters/distance_to_water_bodies/', 'rasters/water_distance/', 'rasters/water/'],
            'patterns': ['*water*', '*distance*', '*waterbod*'],
            'notes': 'Distance to water bodies'
        },
        'NDMI': {
            'directories': ['rasters/NDMI/', 'rasters/ndmi/', 'rasters/moisture_index/'],
            'patterns': ['*ndmi*', '*NDMI*', '*moisture_index*'],
            'notes': 'Normalized Difference Moisture Index'
        },
        'NDWI': {
            'directories': ['rasters/NDWI/', 'rasters/ndwi/', 'rasters/water_index/'],
            'patterns': ['*ndwi*', '*NDWI*', '*water_index*'],
            'notes': 'Normalized Difference Water Index'
        },
        'Rainfall': {
            'directories': ['rasters/rainfall_monthly/', 'rasters/rainfall/', 'rasters/precipitation/'],
            'patterns': ['*rain*', '*precip*', '*chirps*', '*CHIRPS*'],
            'notes': 'Monthly rainfall data'
        },
        'Elevation': {
            'directories': ['rasters/Elevation/', 'rasters/elevation/', 'rasters/dem/'],
            'patterns': ['*elev*', '*ELEV*', '*dem*', '*DEM*', '*altitude*'],
            'notes': 'Elevation/Digital Elevation Model'
        },
        'EVI': {
            'directories': ['rasters/EVI/', 'rasters/evi/', 'rasters/vegetation/'],
            'patterns': ['*evi*', '*EVI*', '*vegetation_index*'],
            'notes': 'Enhanced Vegetation Index'
        }
    }

    # Check each variable
    results = {}
    for var_name, config in variable_mappings.items():
        print(f"\n📊 {var_name}")
        print(f"   Notes: {config['notes']}")

        found_files = []
        checked_dirs = []

        # Check each potential directory
        for directory in config['directories']:
            if os.path.exists(directory):
                checked_dirs.append(directory)
                # Look for files matching patterns
                for pattern in config['patterns']:
                    matches = glob.glob(os.path.join(directory, pattern + '*.tif*'))
                    found_files.extend(matches)

        # Report results
        if found_files:
            print(f"   ✅ FOUND: {len(found_files)} raster files")
            # Show first 3 files as examples
            for f in found_files[:3]:
                print(f"      • {os.path.basename(f)}")
            if len(found_files) > 3:
                print(f"      ... and {len(found_files) - 3} more files")
            results[var_name] = 'FOUND'
        elif checked_dirs:
            print(f"   ⚠️  Directory exists but no matching files found")
            print(f"      Checked: {', '.join(checked_dirs)}")
            # List actual files in directory
            for d in checked_dirs:
                files = os.listdir(d)
                if files:
                    print(f"      Files in {d}: {files[:3]}")
            results[var_name] = 'DIRECTORY_EXISTS_NO_FILES'
        else:
            print(f"   ❌ NOT FOUND: No matching directories exist")
            results[var_name] = 'NOT_FOUND'

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    found = [k for k, v in results.items() if v == 'FOUND']
    partial = [k for k, v in results.items() if v == 'DIRECTORY_EXISTS_NO_FILES']
    missing = [k for k, v in results.items() if v == 'NOT_FOUND']

    print(f"\n✅ Variables with raster data: {len(found)}/{len(results)}")
    for var in found:
        print(f"   • {var}")

    if partial:
        print(f"\n⚠️  Variables with directories but no files: {len(partial)}")
        for var in partial:
            print(f"   • {var}")

    if missing:
        print(f"\n❌ Missing variables: {len(missing)}")
        for var in missing:
            print(f"   • {var}")

    # Check for test positivity rate specifically
    print("\n" + "=" * 70)
    print("SPECIAL CHECK: Test Positivity Rate (TPR)")
    print("=" * 70)
    print("\nNote: TPR data might not be in raster format.")
    print("It's often derived from health facility data and stored as CSV/tabular data.")
    print("\nChecking for alternative TPR data sources...")

    # Check for CSV data
    csv_patterns = ['*tpr*', '*positivity*', '*test*', '*rdt*']
    csv_dirs = ['data/', 'app/data/', 'instance/', 'www/']

    for directory in csv_dirs:
        if os.path.exists(directory):
            for pattern in csv_patterns:
                csv_matches = glob.glob(os.path.join(directory, pattern + '*.csv'))
                if csv_matches:
                    print(f"\n📄 Found CSV data in {directory}:")
                    for f in csv_matches[:3]:
                        print(f"   • {os.path.basename(f)}")

    print("\n" + "=" * 70)
    print("RECOMMENDATION")
    print("=" * 70)
    print("\n💡 For variables not found in raster format:")
    print("1. Test Positivity Rate (TPR) - Usually computed from health facility data")
    print("2. Housing Quality - May need to be derived from DHS or census data")
    print("3. Check if these are computed dynamically during analysis")
    print("4. Some variables might be stored as vector/shapefile data instead of rasters")

if __name__ == "__main__":
    check_raster_database()