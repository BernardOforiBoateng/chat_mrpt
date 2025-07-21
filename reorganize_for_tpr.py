#!/usr/bin/env python3
"""
TPR Module Raster Reorganization Script
Aligns raster files with existing TPR module structure
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime

# Define paths
SOURCE_DIR = Path("/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/rasters")
TARGET_DIR = Path("/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/app/tpr_module/raster_database")

# Mapping to existing TPR structure
TPR_STRUCTURE_MAPPING = {
    "elevation": {
        "source_files": ["MERIT_Elevation.max.1km.tif"],
        "target_dir": "elevation"
    },
    "housing": {
        "source_files": ["2019_Nature_Africa_Housing_2015_NGA.tiff"],
        "target_dir": "housing"
    },
    "rainfall": {
        "source_pattern": r"rainfall_year_(\d{4})_month_(\d{2})",
        "years": [2021, 2018],
        "target_dir": "rainfall"
    },
    "temperature": {
        "source_pattern": r"temperature_year_(\d{4})_month_(\d{2})",
        "years": [2021, 2018],
        "target_dir": "temperature"
    },
    "soil": {
        "source_pattern": r"GIOVANNI.*GWETTOP\.(\d{4})(\d{2})",
        "years": [2018],
        "target_dir": "soil"
    },
    "vegetation": {
        "source_pattern": r"(?:EVI_v6\.|evi_nigeria_)(\d{4})\.?(\d{2})",
        "years": [2018],
        "target_dir": "vegetation"
    },
    "water_bodies": {
        "source_files": [
            "distance_to_water.tif",
            "NDMI_Nigeria_2023.tif",
            "Nigeria_NDWI_2023.tif"
        ],
        "flood_pattern": r"flooded_(\d{4})_(\w+)",
        "years": [2021],
        "target_dir": "water_bodies"
    },
    "urban": {
        "source_pattern": r"(?:DMSP|VIIRS)_NTL_(?:Nigeria_)?(\d{4})",
        "years": [2024, 2021],
        "target_dir": "urban"
    },
    "health": {
        "source_pattern": r"Global_Pf_Parasite_Rate_NGA_(\d{4})",
        "years": [2022, 2021, 2020],
        "target_dir": "health"
    }
}

def organize_for_tpr(dry_run=True):
    """Organize rasters according to TPR module structure"""
    results = {
        "copied": [],
        "errors": [],
        "summary": {}
    }
    
    # Process each category
    for category, config in TPR_STRUCTURE_MAPPING.items():
        print(f"\nProcessing {category}...")
        results["summary"][category] = []
        
        target_category_dir = TARGET_DIR / config["target_dir"]
        
        # Handle static files
        if "source_files" in config:
            for filename in config["source_files"]:
                # Search for the file
                for root, dirs, files in os.walk(SOURCE_DIR):
                    if filename in files:
                        source_path = Path(root) / filename
                        
                        # Determine target name
                        if category == "elevation":
                            target_name = "elevation_merit.tif"
                        elif category == "housing":
                            target_name = "housing_2015.tif"
                        elif "NDMI" in filename:
                            target_name = "ndmi_2023.tif"
                        elif "NDWI" in filename:
                            target_name = "ndwi_2023.tif"
                        else:
                            target_name = filename
                        
                        target_path = target_category_dir / target_name
                        
                        if dry_run:
                            print(f"  Would copy: {filename} -> {config['target_dir']}/{target_name}")
                        else:
                            target_category_dir.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(source_path, target_path)
                            print(f"  Copied: {filename} -> {config['target_dir']}/{target_name}")
                        
                        results["copied"].append(str(target_path))
                        results["summary"][category].append(target_name)
                        break
        
        # Handle pattern-based files
        if "source_pattern" in config:
            import re
            pattern = re.compile(config["source_pattern"])
            years = config.get("years", [])
            
            for root, dirs, files in os.walk(SOURCE_DIR):
                for file in files:
                    if file.endswith('.tif') and not file.endswith('.aux.xml'):
                        match = pattern.search(file)
                        if match:
                            # Extract year
                            year = int(match.group(1))
                            
                            if year in years:
                                source_path = Path(root) / file
                                
                                # Create appropriate filename
                                if category == "vegetation":
                                    month = match.group(2)
                                    target_name = f"evi_{year}_{month}.tif"
                                elif category in ["rainfall", "temperature"]:
                                    month = match.group(2)
                                    target_name = f"{category}_{year}_{month}.tif"
                                elif category == "soil":
                                    month = match.group(2)
                                    target_name = f"soil_wetness_{year}_{month}.tif"
                                elif category == "urban":
                                    sensor = "viirs" if "VIIRS" in file else "dmsp"
                                    target_name = f"night_lights_{sensor}_{year}.tif"
                                elif category == "health":
                                    target_name = f"pf_parasite_rate_{year}.tif"
                                else:
                                    target_name = file
                                
                                # Create year subdirectory
                                target_year_dir = target_category_dir / str(year)
                                target_path = target_year_dir / target_name
                                
                                if dry_run:
                                    print(f"  Would copy: {file} -> {config['target_dir']}/{year}/{target_name}")
                                else:
                                    target_year_dir.mkdir(parents=True, exist_ok=True)
                                    shutil.copy2(source_path, target_path)
                                    print(f"  Copied: {file} -> {config['target_dir']}/{year}/{target_name}")
                                
                                results["copied"].append(str(target_path))
                                results["summary"][category].append(f"{year}/{target_name}")
        
        # Handle flood data separately
        if "flood_pattern" in config:
            pattern = re.compile(config["flood_pattern"])
            for root, dirs, files in os.walk(SOURCE_DIR / "flood_extent"):
                for file in files:
                    if file.endswith('.tif'):
                        match = pattern.search(file)
                        if match:
                            year = int(match.group(1))
                            if year in config.get("years", []):
                                source_path = Path(root) / file
                                target_name = f"flood_extent_{year}_{match.group(2)}.tif"
                                target_path = target_category_dir / "flood" / str(year) / target_name
                                
                                if dry_run:
                                    print(f"  Would copy: {file} -> water_bodies/flood/{year}/{target_name}")
                                else:
                                    target_path.parent.mkdir(parents=True, exist_ok=True)
                                    shutil.copy2(source_path, target_path)
                                    print(f"  Copied: {file} -> water_bodies/flood/{year}/{target_name}")
                                
                                results["copied"].append(str(target_path))
                                results["summary"][category].append(f"flood/{year}/{target_name}")
    
    return results

def create_tpr_metadata(results):
    """Create metadata for TPR module"""
    metadata = {
        "generated_at": datetime.now().isoformat(),
        "tpr_raster_inventory": {},
        "data_coverage": {
            "temporal_range": {
                "environmental": "2018-2021 (partial 2021)",
                "water": "2021-2023",
                "urban": "2021-2024",
                "health": "2020-2022"
            },
            "spatial_coverage": "Nigeria (national coverage)",
            "resolution": "1km for most datasets"
        },
        "processing_notes": {
            "elevation": "MERIT DEM, static dataset",
            "housing": "2015 Nature Africa dataset (most recent)",
            "rainfall": "CHIRPS or similar, monthly",
            "temperature": "ERA5 or similar, monthly",
            "soil": "GIOVANNI GWETTOP, monthly",
            "vegetation": "MODIS EVI, monthly",
            "water_bodies": "NDMI/NDWI (2023), flood extent (2021)",
            "urban": "VIIRS night lights",
            "health": "MAP Pf parasite rate, annual"
        }
    }
    
    # Organize inventory by category
    for category, files in results["summary"].items():
        if files:
            metadata["tpr_raster_inventory"][category] = {
                "file_count": len(files),
                "files": sorted(files)
            }
    
    return metadata

def main(dry_run=True):
    """Main execution for TPR module organization"""
    print("TPR Module Raster Organization")
    print("=" * 50)
    print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
    print(f"Source: {SOURCE_DIR}")
    print(f"Target: {TARGET_DIR}")
    print("-" * 50)
    
    # Organize files
    results = organize_for_tpr(dry_run)
    
    # Create metadata
    metadata = create_tpr_metadata(results)
    
    # Save metadata
    if not dry_run:
        metadata_path = TARGET_DIR / "raster_inventory.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"\nMetadata saved to: {metadata_path}")
    
    # Print summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Total files to be copied: {len(results['copied'])}")
    print(f"Errors: {len(results['errors'])}")
    
    print("\nFiles by category:")
    for category, files in results["summary"].items():
        if files:
            print(f"  {category}: {len(files)} files")
    
    print("\nData gaps identified:")
    print("  - Environmental data (EVI, rainfall, temperature) missing 2022-2024")
    print("  - Consider acquiring recent environmental data for complete analysis")
    print("  - Current data suitable for 2021 baseline analysis")
    
    if dry_run:
        print("\nTo execute the reorganization, run:")
        print("  python reorganize_for_tpr.py --execute")

if __name__ == "__main__":
    import sys
    dry_run = "--execute" not in sys.argv
    main(dry_run=dry_run)