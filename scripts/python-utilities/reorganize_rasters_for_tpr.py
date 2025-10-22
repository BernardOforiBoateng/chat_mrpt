#!/usr/bin/env python3
"""
Reorganize raster files for TPR module with focus on most recent 3 years.
Aligns with the TPR module structure and variable requirements.
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime
import re

# Configuration
SOURCE_DIR = "/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/rasters"
TARGET_DIR = "/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/app/tpr_module/raster_database"

# Variable mapping to TPR module structure
VARIABLE_MAPPING = {
    # Environmental variables
    'evi': 'vegetation',
    'ndmi': 'vegetation', 
    'ndwi': 'vegetation',
    'rainfall': 'rainfall',
    'temperature': 'temperature',
    'soil_wetness': 'soil',
    
    # Static variables
    'elevation': 'elevation',
    'distance_to_water': 'water_bodies',
    
    # Socioeconomic
    'nighttime_lights': 'urban',
    'housing': 'housing',
    
    # Health (not in original plan but available)
    'pfpr': 'health',
    'flood': 'flood'
}

class RasterReorganizer:
    def __init__(self, source_dir, target_dir):
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir)
        self.operations = []
        self.metadata = {}
        
    def analyze_and_reorganize(self, dry_run=True):
        """Main method to analyze and reorganize rasters."""
        print(f"{'DRY RUN' if dry_run else 'EXECUTING'} - Reorganizing rasters for TPR module")
        print(f"Source: {self.source_dir}")
        print(f"Target: {self.target_dir}\n")
        
        # Process each variable type
        self.process_evi()
        self.process_ndmi_ndwi()
        self.process_elevation()
        self.process_distance_to_water()
        self.process_flood()
        self.process_housing()
        self.process_nighttime_lights()
        self.process_pfpr()
        self.process_rainfall()
        self.process_temperature()
        self.process_soil_wetness()
        
        # Execute operations
        if not dry_run:
            self.execute_operations()
            self.create_metadata_files()
        else:
            self.print_operations()
            
        # Create summary
        self.create_summary_report()
    
    def process_evi(self):
        """Process EVI files - keep most recent 3 years."""
        evi_dir = self.source_dir / "EVI"
        target_dir = self.target_dir / "vegetation"
        
        # Find EVI files (2018, 2015, 2013, 2010 available)
        # We'll use 2018 as most recent, then calculate annual averages
        evi_2018_files = [
            "EVI_v6.2018.08.mean.1km.tif",
            "EVI_v6.2018.09.mean.1km.tif", 
            "EVI_v6.2018.10.mean.1km.tif",
            "EVI_v6.2018.11.mean.1km.tif",
            "EVI_v6.2018.12.mean.1km.tif"
        ]
        
        # For now, copy most recent monthly data
        for file in evi_2018_files:
            if (evi_dir / file).exists():
                self.add_operation(
                    evi_dir / file,
                    target_dir / f"evi_2018_{file.split('.')[2]}.tif",
                    "EVI 2018 monthly data"
                )
        
        # Also include 2015 and 2013 as our "3 most recent years"
        self.add_operation(
            evi_dir / "EVI_v6.2015.12.mean.1km.tif",
            target_dir / "evi_2015_12.tif",
            "EVI 2015 December"
        )
        
        # Note: We need annual averages, which should be computed later
        self.metadata['evi'] = {
            'years_available': [2018, 2015, 2013, 2010],
            'selected_years': [2018, 2015, 2013],
            'note': 'Monthly data available, annual averages need to be computed'
        }
    
    def process_ndmi_ndwi(self):
        """Process NDMI and NDWI files - already have 2023."""
        # NDMI
        self.add_operation(
            self.source_dir / "NDMI" / "NDMI_Nigeria_2023.tif",
            self.target_dir / "vegetation" / "ndmi_2023_annual.tif",
            "NDMI 2023 annual"
        )
        
        # NDWI
        self.add_operation(
            self.source_dir / "NDWI" / "Nigeria_NDWI_2023.tif",
            self.target_dir / "vegetation" / "ndwi_2023_annual.tif",
            "NDWI 2023 annual"
        )
        
        self.metadata['ndmi'] = {'years_available': [2023], 'selected_years': [2023]}
        self.metadata['ndwi'] = {'years_available': [2023], 'selected_years': [2023]}
    
    def process_elevation(self):
        """Process elevation - static variable."""
        self.add_operation(
            self.source_dir / "Elevation" / "MERIT_Elevation.max.1km.tif",
            self.target_dir / "elevation" / "elevation_static.tif",
            "Elevation (static)"
        )
        
        self.metadata['elevation'] = {'type': 'static', 'source': 'MERIT DEM'}
    
    def process_distance_to_water(self):
        """Process distance to water - static variable."""
        self.add_operation(
            self.source_dir / "distance_to_water_bodies" / "distance_to_water.tif",
            self.target_dir / "water_bodies" / "distance_to_water_static.tif",
            "Distance to water bodies (static)"
        )
        
        self.metadata['distance_to_water'] = {'type': 'static'}
    
    def process_flood(self):
        """Process flood extent - keep 2021 and 2018."""
        # Annual flood extent
        self.add_operation(
            self.source_dir / "flood_extent" / "Year" / "flooded_2021_1Y.tif",
            self.target_dir / "flood" / "flood_extent_2021_annual.tif",
            "Flood extent 2021 annual"
        )
        
        self.add_operation(
            self.source_dir / "flood_extent" / "Year" / "flooded_2018_1Y.tif",
            self.target_dir / "flood" / "flood_extent_2018_annual.tif",
            "Flood extent 2018 annual"
        )
        
        self.metadata['flood'] = {
            'years_available': [2021, 2018],
            'selected_years': [2021, 2018]
        }
    
    def process_housing(self):
        """Process housing quality."""
        self.add_operation(
            self.source_dir / "housing" / "2019_Nature_Africa_Housing_2015_NGA.tiff",
            self.target_dir / "housing" / "housing_quality_2015.tif",
            "Housing quality 2015"
        )
        
        self.metadata['housing'] = {
            'years_available': [2015, 2000],
            'selected_years': [2015],
            'note': 'Most recent available'
        }
    
    def process_nighttime_lights(self):
        """Process nighttime lights - we have 2024!"""
        # 2024 (most recent)
        self.add_operation(
            self.source_dir / "night_timel_lights" / "2024" / "VIIRS_NTL_2024_Nigeria.tif",
            self.target_dir / "urban" / "nighttime_lights_2024.tif",
            "Nighttime lights 2024"
        )
        
        # 2021
        self.add_operation(
            self.source_dir / "night_timel_lights" / "VIIRS_NTL_Nigeria_2021.tif",
            self.target_dir / "urban" / "nighttime_lights_2021.tif",
            "Nighttime lights 2021"
        )
        
        # 2018
        self.add_operation(
            self.source_dir / "night_timel_lights" / "VIIRS_NTL_Nigeria_2018.tif",
            self.target_dir / "urban" / "nighttime_lights_2018.tif",
            "Nighttime lights 2018"
        )
        
        self.metadata['nighttime_lights'] = {
            'years_available': [2024, 2021, 2018, 2015, 2010],
            'selected_years': [2024, 2021, 2018]
        }
    
    def process_pfpr(self):
        """Process Pf parasite rate - get 2022, 2021, 2020."""
        years = [2022, 2021, 2020]
        
        for year in years:
            source_file = self.source_dir / "pf_parasite_rate" / f"202406_Global_Pf_Parasite_Rate_NGA_{year}.tiff"
            if source_file.exists():
                self.add_operation(
                    source_file,
                    self.target_dir / "health" / f"pfpr_{year}.tif",
                    f"Pf parasite rate {year}"
                )
        
        self.metadata['pfpr'] = {
            'years_available': list(range(2000, 2023)),
            'selected_years': years
        }
    
    def process_rainfall(self):
        """Process rainfall - get most recent available."""
        # 2021 (most recent with multiple months)
        rainfall_2021 = [
            ("X2021_rainfall_year_2021_month_10.tif", "rainfall_2021_10.tif"),
            ("X2021_rainfall_year_2021_month_11.tif", "rainfall_2021_11.tif"),
            ("X2021_rainfall_year_2021_month_12.tif", "rainfall_2021_12.tif")
        ]
        
        for source, target in rainfall_2021:
            self.add_operation(
                self.source_dir / "rainfall_monthly" / "2021" / source,
                self.target_dir / "rainfall" / target,
                f"Rainfall {target}"
            )
        
        # 2018 (complete late year data)
        rainfall_2018 = [
            ("rainfall_year_2018_month_08.tif", "rainfall_2018_08.tif"),
            ("rainfall_year_2018_month_09.tif", "rainfall_2018_09.tif"),
            ("rainfall_year_2018_month_10.tif", "rainfall_2018_10.tif"),
            ("rainfall_year_2018_month_11.tif", "rainfall_2018_11.tif"),
            ("rainfall_year_2018_month_12.tif", "rainfall_2018_12.tif")
        ]
        
        for source, target in rainfall_2018:
            self.add_operation(
                self.source_dir / "rainfall_monthly" / "2018" / source,
                self.target_dir / "rainfall" / target,
                f"Rainfall {target}"
            )
        
        self.metadata['rainfall'] = {
            'years_available': [2021, 2018, 2015, 2013, 2010],
            'selected_years': [2021, 2018],
            'note': 'Monthly data, annual totals need to be computed'
        }
    
    def process_temperature(self):
        """Process temperature - similar to rainfall."""
        # 2021 (most recent)
        temp_2021 = [
            ("X2021_temperature_year_2021_month_10.tif", "temperature_2021_10.tif"),
            ("X2021_temperature_year_2021_month_11.tif", "temperature_2021_11.tif"),
            ("X2021_temperature_year_2021_month_12.tif", "temperature_2021_12.tif")
        ]
        
        for source, target in temp_2021:
            self.add_operation(
                self.source_dir / "temperature_monthly" / "2021" / source,
                self.target_dir / "temperature" / target,
                f"Temperature {target}"
            )
        
        # 2018
        temp_2018 = [
            ("temperature_year_2018_month_08.tif", "temperature_2018_08.tif"),
            ("temperature_year_2018_month_09.tif", "temperature_2018_09.tif"),
            ("temperature_year_2018_month_10.tif", "temperature_2018_10.tif"),
            ("temperature_year_2018_month_11.tif", "temperature_2018_11.tif"),
            ("temperature_year_2018_month_12.tif", "temperature_2018_12.tif")
        ]
        
        for source, target in temp_2018:
            self.add_operation(
                self.source_dir / "temperature_monthly" / "2018" / source,
                self.target_dir / "temperature" / target,
                f"Temperature {target}"
            )
        
        self.metadata['temperature'] = {
            'years_available': [2021, 2018, 2015, 2013, 2010],
            'selected_years': [2021, 2018],
            'note': 'Monthly data, annual means need to be computed'
        }
    
    def process_soil_wetness(self):
        """Process soil wetness - GIOVANNI data."""
        # 2018 (most recent complete)
        soil_2018_files = [
            ("GIOVANNI-g4.timeAvgMap.M2TMNXLND_5_12_4_GWETTOP.20180801-20180831.180W_90S_180E_90N.tif", "soil_wetness_2018_08.tif"),
            ("GIOVANNI-g4.timeAvgMap.M2TMNXLND_5_12_4_GWETTOP.20180901-20180930.180W_90S_180E_90N.tif", "soil_wetness_2018_09.tif"),
            ("GIOVANNI-g4.timeAvgMap.M2TMNXLND_5_12_4_GWETTOP.20181001-20181031.180W_90S_180E_90N.tif", "soil_wetness_2018_10.tif"),
            ("GIOVANNI-g4.timeAvgMap.M2TMNXLND_5_12_4_GWETTOP.20181101-20181130.180W_90S_180E_90N.tif", "soil_wetness_2018_11.tif"),
            ("GIOVANNI-g4.timeAvgMap.M2TMNXLND_5_12_4_GWETTOP.20181201-20181231.180W_90S_180E_90N.tif", "soil_wetness_2018_12.tif")
        ]
        
        for source, target in soil_2018_files:
            self.add_operation(
                self.source_dir / "surface_soil_wetness" / source,
                self.target_dir / "soil" / target,
                f"Soil wetness {target}"
            )
        
        self.metadata['soil_wetness'] = {
            'years_available': [2018, 2015, 2010],
            'selected_years': [2018],
            'source': 'NASA GIOVANNI'
        }
    
    def add_operation(self, source, target, description):
        """Add a file operation to the queue."""
        self.operations.append({
            'source': source,
            'target': target,
            'description': description
        })
    
    def execute_operations(self):
        """Execute all queued file operations."""
        print(f"\nExecuting {len(self.operations)} file operations...\n")
        
        for op in self.operations:
            source = Path(op['source'])
            target = Path(op['target'])
            
            if not source.exists():
                print(f"⚠️  Source not found: {source}")
                continue
            
            # Create target directory
            target.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            try:
                shutil.copy2(source, target)
                print(f"✅ {op['description']}")
                print(f"   {source.name} → {target.name}")
            except Exception as e:
                print(f"❌ Failed: {op['description']}")
                print(f"   Error: {e}")
    
    def print_operations(self):
        """Print planned operations without executing."""
        print(f"\nPlanned operations ({len(self.operations)} files):\n")
        
        for op in self.operations:
            source = Path(op['source'])
            target = Path(op['target'])
            exists = "✓" if source.exists() else "✗"
            
            print(f"{exists} {op['description']}")
            print(f"   {source.name} → {target}")
            print()
    
    def create_metadata_files(self):
        """Create metadata.json files for each variable directory."""
        for var_type, var_info in self.metadata.items():
            # Determine target directory
            if var_type in ['evi', 'ndmi', 'ndwi']:
                target_dir = self.target_dir / 'vegetation'
            elif var_type in VARIABLE_MAPPING:
                target_dir = self.target_dir / VARIABLE_MAPPING[var_type]
            else:
                continue
            
            metadata_file = target_dir / 'metadata.json'
            
            # Create metadata
            metadata = {
                'variable': var_type,
                'last_updated': datetime.now().isoformat(),
                'info': var_info
            }
            
            # Write metadata
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
    
    def create_summary_report(self):
        """Create a summary report of the reorganization."""
        report = f"""
# TPR Raster Reorganization Summary

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview
- Total operations: {len(self.operations)}
- Source directory: {self.source_dir}
- Target directory: {self.target_dir}

## Variables Processed

"""
        
        # Group operations by target directory
        by_directory = {}
        for op in self.operations:
            target_dir = Path(op['target']).parent
            if target_dir not in by_directory:
                by_directory[target_dir] = []
            by_directory[target_dir].append(op)
        
        # Write summary for each directory
        for directory, ops in sorted(by_directory.items()):
            report += f"### {directory.name}\n"
            report += f"Files: {len(ops)}\n\n"
            for op in ops:
                report += f"- {Path(op['target']).name}: {op['description']}\n"
            report += "\n"
        
        # Add metadata summary
        report += "## Metadata Summary\n\n"
        for var, info in self.metadata.items():
            report += f"### {var}\n"
            report += f"```json\n{json.dumps(info, indent=2)}\n```\n\n"
        
        # Write report
        report_path = self.target_dir / "REORGANIZATION_REPORT.md"
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"\n📄 Summary report created: {report_path}")


def main():
    """Main function to run the reorganization."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Reorganize rasters for TPR module')
    parser.add_argument('--execute', action='store_true', 
                       help='Execute the reorganization (default is dry run)')
    parser.add_argument('--source', default=SOURCE_DIR,
                       help='Source directory containing rasters')
    parser.add_argument('--target', default=TARGET_DIR,
                       help='Target directory for organized rasters')
    
    args = parser.parse_args()
    
    # Create reorganizer
    reorganizer = RasterReorganizer(args.source, args.target)
    
    # Run reorganization
    reorganizer.analyze_and_reorganize(dry_run=not args.execute)


if __name__ == "__main__":
    main()