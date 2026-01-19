#!/usr/bin/env python3
"""
Raster Reorganization Script for TPR Module
Reorganizes raster files into a clean, standardized structure
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

# File mapping configuration
FILE_MAPPINGS = {
    "environmental": {
        "evi": {
            "pattern": r"(?:EVI_v6\.|evi_nigeria_)(\d{4})\.?(\d{2})",
            "files": [],
            "rename": lambda year, month: f"evi_{year}_{month:02d}.tif"
        },
        "rainfall": {
            "pattern": r"rainfall_year_(\d{4})_month_(\d{2})",
            "files": [],
            "rename": lambda year, month: f"rainfall_{year}_{month:02d}.tif"
        },
        "temperature": {
            "pattern": r"temperature_year_(\d{4})_month_(\d{2})",
            "files": [],
            "rename": lambda year, month: f"temperature_{year}_{month:02d}.tif"
        },
        "soil_wetness": {
            "pattern": r"GIOVANNI.*GWETTOP\.(\d{4})(\d{2})",
            "files": [],
            "rename": lambda year, month: f"soil_wetness_{year}_{month:02d}.tif"
        }
    },
    "water": {
        "ndmi": {
            "pattern": r"NDMI_Nigeria_(\d{4})",
            "files": [],
            "rename": lambda year: f"ndmi_{year}.tif"
        },
        "ndwi": {
            "pattern": r"Nigeria_NDWI_(\d{4})",
            "files": [],
            "rename": lambda year: f"ndwi_{year}.tif"
        },
        "flood_extent": {
            "pattern": r"flooded_(\d{4})_(\w+)",
            "files": [],
            "rename": lambda year, period: f"flood_extent_{year}_{period}.tif"
        },
        "static": {
            "files": ["distance_to_water.tif"]
        }
    },
    "human_activity": {
        "night_lights": {
            "pattern": r"(?:DMSP|VIIRS)_NTL_(?:Nigeria_)?(\d{4})",
            "files": [],
            "rename": lambda year, sensor: f"night_lights_{sensor.lower()}_{year}.tif"
        },
        "housing": {
            "pattern": r"Housing_(\d{4})_NGA",
            "files": [],
            "rename": lambda year: f"housing_{year}.tif"
        }
    },
    "health": {
        "pf_parasite_rate": {
            "pattern": r"Global_Pf_Parasite_Rate_NGA_(\d{4})",
            "files": [],
            "rename": lambda year: f"pf_parasite_rate_{year}.tif"
        }
    },
    "static": {
        "elevation": {
            "files": ["MERIT_Elevation.max.1km.tif"]
        }
    }
}

# Years to prioritize (most recent 3 years + 2021 for environmental data)
PRIORITY_YEARS = [2024, 2023, 2022, 2021]

def create_directory_structure():
    """Create the target directory structure"""
    directories = [
        TARGET_DIR / "environmental" / "evi",
        TARGET_DIR / "environmental" / "rainfall",
        TARGET_DIR / "environmental" / "temperature",
        TARGET_DIR / "environmental" / "soil_wetness",
        TARGET_DIR / "water" / "ndmi",
        TARGET_DIR / "water" / "ndwi",
        TARGET_DIR / "water" / "flood_extent",
        TARGET_DIR / "water" / "static",
        TARGET_DIR / "human_activity" / "night_lights",
        TARGET_DIR / "human_activity" / "housing",
        TARGET_DIR / "health" / "pf_parasite_rate",
        TARGET_DIR / "static" / "elevation",
        TARGET_DIR / "metadata"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        # Create year subdirectories for time series data
        if "static" not in str(directory) and "metadata" not in str(directory):
            for year in PRIORITY_YEARS:
                (directory / str(year)).mkdir(exist_ok=True)

def find_and_categorize_files():
    """Find all raster files and categorize them"""
    inventory = {}
    
    for root, dirs, files in os.walk(SOURCE_DIR):
        for file in files:
            if file.endswith(('.tif', '.tiff')) and not file.endswith('.aux.xml'):
                file_path = Path(root) / file
                categorized = False
                
                # Check environmental variables
                if "EVI" in root or "evi" in file.lower():
                    if "DMSP" not in file and "rainfall" not in file:  # Exclude misplaced files
                        match = re.search(r"(?:EVI_v6\.|evi_nigeria_)(\d{4})\.?(\d{1,2})", file)
                        if match:
                            year, month = int(match.group(1)), int(match.group(2))
                            if year in PRIORITY_YEARS:
                                category = f"environmental/evi/{year}"
                                new_name = f"evi_{year}_{month:02d}.tif"
                                inventory[str(file_path)] = (category, new_name)
                                categorized = True
                
                # Check rainfall
                elif "rainfall" in root or "rainfall" in file:
                    match = re.search(r"rainfall_year_(\d{4})_month_(\d{2})", file)
                    if match:
                        year, month = int(match.group(1)), int(match.group(2))
                        if year in PRIORITY_YEARS:
                            category = f"environmental/rainfall/{year}"
                            new_name = f"rainfall_{year}_{month:02d}.tif"
                            inventory[str(file_path)] = (category, new_name)
                            categorized = True
                
                # Check temperature
                elif "temperature" in root or "temperature" in file:
                    match = re.search(r"temperature_year_(\d{4})_month_(\d{2})", file)
                    if match:
                        year, month = int(match.group(1)), int(match.group(2))
                        if year in PRIORITY_YEARS:
                            category = f"environmental/temperature/{year}"
                            new_name = f"temperature_{year}_{month:02d}.tif"
                            inventory[str(file_path)] = (category, new_name)
                            categorized = True
                
                # Check soil wetness
                elif "GIOVANNI" in file and "GWETTOP" in file:
                    match = re.search(r"(\d{4})(\d{2})\d{2}-\d{8}", file)
                    if match:
                        year, month = int(match.group(1)), int(match.group(2))
                        if year in PRIORITY_YEARS:
                            category = f"environmental/soil_wetness/{year}"
                            new_name = f"soil_wetness_{year}_{month:02d}.tif"
                            inventory[str(file_path)] = (category, new_name)
                            categorized = True
                
                # Check NDMI
                elif "NDMI" in file:
                    match = re.search(r"NDMI_Nigeria_(\d{4})", file)
                    if match:
                        year = int(match.group(1))
                        if year in PRIORITY_YEARS:
                            category = f"water/ndmi/{year}"
                            new_name = f"ndmi_{year}.tif"
                            inventory[str(file_path)] = (category, new_name)
                            categorized = True
                
                # Check NDWI
                elif "NDWI" in file:
                    match = re.search(r"Nigeria_NDWI_(\d{4})", file)
                    if match:
                        year = int(match.group(1))
                        if year in PRIORITY_YEARS:
                            category = f"water/ndwi/{year}"
                            new_name = f"ndwi_{year}.tif"
                            inventory[str(file_path)] = (category, new_name)
                            categorized = True
                
                # Check flood extent
                elif "flooded" in file:
                    match = re.search(r"flooded_(\d{4})_(\w+)", file)
                    if match:
                        year = int(match.group(1))
                        period = match.group(2)
                        if year in PRIORITY_YEARS:
                            category = f"water/flood_extent/{year}"
                            new_name = f"flood_extent_{year}_{period}.tif"
                            inventory[str(file_path)] = (category, new_name)
                            categorized = True
                
                # Check night lights
                elif "NTL" in file or "night" in root:
                    match = re.search(r"(DMSP|VIIRS)_NTL_(?:Nigeria_)?(\d{4})", file)
                    if match:
                        sensor, year = match.group(1), int(match.group(2))
                        if year in PRIORITY_YEARS:
                            category = f"human_activity/night_lights/{year}"
                            new_name = f"night_lights_{sensor.lower()}_{year}.tif"
                            inventory[str(file_path)] = (category, new_name)
                            categorized = True
                
                # Check housing
                elif "Housing" in file:
                    match = re.search(r"Housing_(\d{4})_NGA", file)
                    if match:
                        year = int(match.group(1))
                        if year == 2015:  # Use most recent available
                            category = f"human_activity/housing/{year}"
                            new_name = f"housing_{year}.tif"
                            inventory[str(file_path)] = (category, new_name)
                            categorized = True
                
                # Check Pf parasite rate
                elif "Pf_Parasite_Rate" in file:
                    match = re.search(r"Global_Pf_Parasite_Rate_NGA_(\d{4})", file)
                    if match:
                        year = int(match.group(1))
                        if year in PRIORITY_YEARS:
                            category = f"health/pf_parasite_rate/{year}"
                            new_name = f"pf_parasite_rate_{year}.tif"
                            inventory[str(file_path)] = (category, new_name)
                            categorized = True
                
                # Check static files
                elif "distance_to_water" in file:
                    category = "water/static"
                    new_name = "distance_to_water.tif"
                    inventory[str(file_path)] = (category, new_name)
                    categorized = True
                
                elif "MERIT_Elevation" in file:
                    category = "static/elevation"
                    new_name = "elevation_merit.tif"
                    inventory[str(file_path)] = (category, new_name)
                    categorized = True
    
    return inventory

def copy_files(inventory, dry_run=True):
    """Copy files to new structure"""
    results = {
        "copied": [],
        "errors": [],
        "skipped": []
    }
    
    for source_path, (category, new_name) in inventory.items():
        source = Path(source_path)
        target = TARGET_DIR / category / new_name
        
        try:
            if dry_run:
                print(f"Would copy: {source.name} -> {target}")
                results["copied"].append(str(target))
            else:
                # Create parent directory if needed
                target.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                shutil.copy2(source, target)
                print(f"Copied: {source.name} -> {target}")
                results["copied"].append(str(target))
                
        except Exception as e:
            error_msg = f"Error copying {source}: {e}"
            print(error_msg)
            results["errors"].append(error_msg)
    
    return results

def generate_metadata(inventory, results):
    """Generate metadata file"""
    metadata = {
        "generated_at": datetime.now().isoformat(),
        "source_directory": str(SOURCE_DIR),
        "target_directory": str(TARGET_DIR),
        "priority_years": PRIORITY_YEARS,
        "statistics": {
            "total_files_processed": len(inventory),
            "files_copied": len(results["copied"]),
            "errors": len(results["errors"])
        },
        "file_inventory": {}
    }
    
    # Organize inventory by category
    for source_path, (category, new_name) in inventory.items():
        if category not in metadata["file_inventory"]:
            metadata["file_inventory"][category] = []
        
        metadata["file_inventory"][category].append({
            "original_path": source_path,
            "new_name": new_name,
            "file_size_mb": round(Path(source_path).stat().st_size / (1024 * 1024), 2)
        })
    
    # Save metadata
    metadata_path = TARGET_DIR / "metadata" / "reorganization_metadata.json"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\nMetadata saved to: {metadata_path}")
    return metadata

def main(dry_run=True):
    """Main execution function"""
    print("Starting raster reorganization...")
    print(f"Dry run: {dry_run}")
    print(f"Source: {SOURCE_DIR}")
    print(f"Target: {TARGET_DIR}")
    print("-" * 50)
    
    # Create directory structure
    if not dry_run:
        print("Creating directory structure...")
        create_directory_structure()
    
    # Find and categorize files
    print("Analyzing files...")
    inventory = find_and_categorize_files()
    print(f"Found {len(inventory)} files to process")
    
    # Copy files
    print("\nCopying files...")
    results = copy_files(inventory, dry_run)
    
    # Generate metadata
    if not dry_run:
        print("\nGenerating metadata...")
        metadata = generate_metadata(inventory, results)
    
    # Print summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Total files found: {len(inventory)}")
    print(f"Files to be copied: {len(results['copied'])}")
    print(f"Errors: {len(results['errors'])}")
    
    if results['errors']:
        print("\nErrors encountered:")
        for error in results['errors']:
            print(f"  - {error}")
    
    print("\nTo execute the reorganization, run:")
    print("  python reorganize_rasters.py --execute")

if __name__ == "__main__":
    import sys
    
    # Check for --execute flag
    dry_run = "--execute" not in sys.argv
    
    main(dry_run=dry_run)