#!/usr/bin/env python3
"""
Raster Reorganization Script - Recent Data Focus
Reorganizes raster files focusing on the most recent available data
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime
import re

# Define paths
SOURCE_DIR = Path("/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/rasters")
TARGET_DIR = Path("/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/app/tpr_module/raster_database")

# Most recent available years by variable type
RECENT_DATA_YEARS = {
    "evi": [2018],  # Most recent available
    "rainfall": [2021, 2018],  # 2021 partial, 2018 complete
    "temperature": [2021, 2018],  # 2021 partial, 2018 complete
    "soil_wetness": [2018],  # Most recent available
    "ndmi": [2023],
    "ndwi": [2023],
    "flood_extent": [2021, 2018],
    "night_lights": [2024, 2021],
    "housing": [2015],  # Most recent available
    "pf_parasite_rate": [2022, 2021, 2020]
}

def create_minimal_structure():
    """Create a minimal directory structure for recent data"""
    directories = [
        TARGET_DIR / "environmental",
        TARGET_DIR / "water",
        TARGET_DIR / "human_activity",
        TARGET_DIR / "health",
        TARGET_DIR / "static",
        TARGET_DIR / "metadata"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

def get_most_recent_files():
    """Get only the most recent files for each variable"""
    inventory = {}
    summary = {
        "variables_found": {},
        "missing_recent_data": []
    }
    
    # EVI - Get 2018 data (most recent complete year)
    evi_files = []
    for root, dirs, files in os.walk(SOURCE_DIR / "EVI"):
        for file in files:
            if file.endswith('.tif') and "2018" in file and "EVI" in file:
                evi_files.append((Path(root) / file, file))
    
    if evi_files:
        summary["variables_found"]["evi"] = "2018 (monthly)"
        for path, filename in evi_files:
            match = re.search(r"2018\.(\d{2})", filename)
            if match:
                month = match.group(1)
                new_name = f"evi_2018_{month}.tif"
                inventory[str(path)] = ("environmental", new_name)
    else:
        summary["missing_recent_data"].append("EVI - No 2018 data found")
    
    # Rainfall - Get 2021 and 2018 data
    rainfall_files = []
    for root, dirs, files in os.walk(SOURCE_DIR / "rainfall_monthly"):
        for file in files:
            if file.endswith('.tif') and not file.endswith('.aux.xml'):
                if "2021" in file or "2018" in file:
                    rainfall_files.append((Path(root) / file, file))
    
    if rainfall_files:
        summary["variables_found"]["rainfall"] = "2021 (partial), 2018 (complete)"
        for path, filename in rainfall_files:
            match = re.search(r"rainfall_year_(\d{4})_month_(\d{2})", filename)
            if match:
                year, month = match.group(1), match.group(2)
                new_name = f"rainfall_{year}_{month}.tif"
                inventory[str(path)] = ("environmental", new_name)
    
    # Temperature - Get 2021 and 2018 data
    temp_files = []
    for root, dirs, files in os.walk(SOURCE_DIR / "temperature_monthly"):
        for file in files:
            if file.endswith('.tif') and not file.endswith('.aux.xml'):
                if "2021" in file or "2018" in file:
                    temp_files.append((Path(root) / file, file))
    
    if temp_files:
        summary["variables_found"]["temperature"] = "2021 (partial), 2018 (complete)"
        for path, filename in temp_files:
            match = re.search(r"temperature_year_(\d{4})_month_(\d{2})", filename)
            if match:
                year, month = match.group(1), match.group(2)
                new_name = f"temperature_{year}_{month}.tif"
                inventory[str(path)] = ("environmental", new_name)
    
    # Soil Wetness - Get 2018 data
    wetness_files = []
    for root, dirs, files in os.walk(SOURCE_DIR / "surface_soil_wetness"):
        for file in files:
            if file.endswith('.tif') and "2018" in file:
                wetness_files.append((Path(root) / file, file))
    
    if wetness_files:
        summary["variables_found"]["soil_wetness"] = "2018 (monthly)"
        for path, filename in wetness_files:
            match = re.search(r"(\d{4})(\d{2})\d{2}-\d{8}", filename)
            if match:
                year, month = match.group(1), match.group(2)
                new_name = f"soil_wetness_{year}_{month}.tif"
                inventory[str(path)] = ("environmental", new_name)
    
    # NDMI and NDWI - 2023 data
    ndmi_path = SOURCE_DIR / "NDMI" / "NDMI_Nigeria_2023.tif"
    if ndmi_path.exists():
        inventory[str(ndmi_path)] = ("water", "ndmi_2023.tif")
        summary["variables_found"]["ndmi"] = "2023 (annual)"
    
    ndwi_path = SOURCE_DIR / "NDWI" / "Nigeria_NDWI_2023.tif"
    if ndwi_path.exists():
        inventory[str(ndwi_path)] = ("water", "ndwi_2023.tif")
        summary["variables_found"]["ndwi"] = "2023 (annual)"
    
    # Flood Extent - 2021 data
    flood_files = []
    for root, dirs, files in os.walk(SOURCE_DIR / "flood_extent"):
        for file in files:
            if file.endswith('.tif') and "2021" in file:
                flood_files.append((Path(root) / file, file))
    
    if flood_files:
        summary["variables_found"]["flood_extent"] = "2021"
        for path, filename in flood_files:
            inventory[str(path)] = ("water", filename)
    
    # Night Lights - 2024 and 2021 data
    ntl_2024 = SOURCE_DIR / "night_timel_lights" / "2024" / "VIIRS_NTL_2024_Nigeria.tif"
    if ntl_2024.exists():
        inventory[str(ntl_2024)] = ("human_activity", "night_lights_viirs_2024.tif")
        summary["variables_found"]["night_lights"] = "2024, 2021"
    
    ntl_2021 = SOURCE_DIR / "night_timel_lights" / "VIIRS_NTL_Nigeria_2021.tif"
    if ntl_2021.exists():
        inventory[str(ntl_2021)] = ("human_activity", "night_lights_viirs_2021.tif")
    
    # Housing - 2015 (most recent)
    housing_2015 = SOURCE_DIR / "housing" / "2019_Nature_Africa_Housing_2015_NGA.tiff"
    if housing_2015.exists():
        inventory[str(housing_2015)] = ("human_activity", "housing_2015.tif")
        summary["variables_found"]["housing"] = "2015"
    
    # Pf Parasite Rate - 2022, 2021, 2020
    for year in [2022, 2021, 2020]:
        pf_file = SOURCE_DIR / "pf_parasite_rate" / f"202406_Global_Pf_Parasite_Rate_NGA_{year}.tiff"
        if pf_file.exists():
            inventory[str(pf_file)] = ("health", f"pf_parasite_rate_{year}.tif")
            if "pf_parasite_rate" not in summary["variables_found"]:
                summary["variables_found"]["pf_parasite_rate"] = f"{year}, {year-1}, {year-2}"
    
    # Static files
    elevation = SOURCE_DIR / "Elevation" / "MERIT_Elevation.max.1km.tif"
    if elevation.exists():
        inventory[str(elevation)] = ("static", "elevation_merit.tif")
        summary["variables_found"]["elevation"] = "static"
    
    distance_water = SOURCE_DIR / "distance_to_water_bodies" / "distance_to_water.tif"
    if distance_water.exists():
        inventory[str(distance_water)] = ("static", "distance_to_water.tif")
        summary["variables_found"]["distance_to_water"] = "static"
    
    return inventory, summary

def copy_recent_files(inventory, dry_run=True):
    """Copy only the most recent files"""
    results = {
        "copied": [],
        "errors": []
    }
    
    for source_path, (category, new_name) in inventory.items():
        source = Path(source_path)
        target = TARGET_DIR / category / new_name
        
        try:
            if dry_run:
                print(f"Would copy: {source.name} -> {category}/{new_name}")
                results["copied"].append(f"{category}/{new_name}")
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                print(f"Copied: {source.name} -> {category}/{new_name}")
                results["copied"].append(f"{category}/{new_name}")
        except Exception as e:
            error_msg = f"Error copying {source}: {e}"
            print(error_msg)
            results["errors"].append(error_msg)
    
    return results

def create_data_availability_report(summary):
    """Create a report on data availability"""
    report = {
        "generated_at": datetime.now().isoformat(),
        "data_summary": summary,
        "recommendations": [
            "Environmental data (EVI, rainfall, temperature, soil wetness) needs updating to 2022-2024",
            "Consider using 2021 as baseline year for multi-variable analysis",
            "NDMI/NDWI (2023) and Night Lights (2024) are the most current",
            "Pf Parasite Rate data is complete through 2022"
        ]
    }
    
    report_path = TARGET_DIR / "metadata" / "data_availability_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report_path

def main(dry_run=True):
    """Main execution for recent data organization"""
    print("Raster Reorganization - Recent Data Focus")
    print("=" * 50)
    print(f"Dry run: {dry_run}")
    print(f"Source: {SOURCE_DIR}")
    print(f"Target: {TARGET_DIR}")
    print("-" * 50)
    
    # Create directory structure
    if not dry_run:
        print("Creating directory structure...")
        create_minimal_structure()
    
    # Get most recent files
    print("Finding most recent data...")
    inventory, summary = get_most_recent_files()
    
    print(f"\nFound {len(inventory)} files with recent data")
    print("\nVariables with recent data:")
    for var, years in summary["variables_found"].items():
        print(f"  - {var}: {years}")
    
    if summary["missing_recent_data"]:
        print("\nMissing recent data:")
        for missing in summary["missing_recent_data"]:
            print(f"  - {missing}")
    
    # Copy files
    print(f"\n{'Would copy' if dry_run else 'Copying'} files...")
    results = copy_recent_files(inventory, dry_run)
    
    # Create data availability report
    if not dry_run:
        print("\nCreating data availability report...")
        report_path = create_data_availability_report(summary)
        print(f"Report saved to: {report_path}")
    
    # Print summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Total recent files found: {len(inventory)}")
    print(f"Files to be copied: {len(results['copied'])}")
    print(f"Errors: {len(results['errors'])}")
    
    print("\nRecommended next steps:")
    print("1. Run with --execute to copy files")
    print("2. Consider acquiring 2022-2024 environmental data")
    print("3. Use 2021 as baseline year for comprehensive analysis")
    
    if dry_run:
        print("\nTo execute the reorganization, run:")
        print("  python reorganize_rasters_recent.py --execute")

if __name__ == "__main__":
    import sys
    dry_run = "--execute" not in sys.argv
    main(dry_run=dry_run)