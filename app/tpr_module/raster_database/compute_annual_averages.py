#!/usr/bin/env python3
"""
Compute annual averages/totals from monthly raster data.
This script processes monthly rasters to create annual summaries.
"""

import os
import numpy as np
import rasterio
from rasterio.enums import Resampling
from pathlib import Path
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AnnualRasterProcessor:
    """Process monthly rasters to create annual summaries."""
    
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        
    def compute_annual_average(self, variable, year, months, output_name=None):
        """
        Compute annual average from monthly rasters.
        
        Args:
            variable: Variable name (e.g., 'evi', 'temperature', 'soil_wetness')
            year: Year to process
            months: List of month numbers to include
            output_name: Custom output filename (optional)
        """
        # Determine input directory
        if variable in ['evi', 'ndvi', 'ndmi', 'ndwi']:
            input_dir = self.base_dir / 'vegetation'
        elif variable == 'soil_wetness':
            input_dir = self.base_dir / 'soil'
        else:
            input_dir = self.base_dir / variable
            
        # Find monthly files
        monthly_files = []
        for month in months:
            pattern = f"{variable}_{year}_{month:02d}.tif"
            file_path = input_dir / pattern
            if file_path.exists():
                monthly_files.append(file_path)
            else:
                logger.warning(f"Missing file: {pattern}")
        
        if not monthly_files:
            logger.error(f"No monthly files found for {variable} {year}")
            return None
            
        logger.info(f"Processing {len(monthly_files)} files for {variable} {year}")
        
        # Read first file to get metadata
        with rasterio.open(monthly_files[0]) as src:
            meta = src.meta.copy()
            height = src.height
            width = src.width
            
        # Initialize array for accumulation
        sum_array = np.zeros((height, width), dtype=np.float32)
        count_array = np.zeros((height, width), dtype=np.int16)
        
        # Process each monthly file
        for file_path in monthly_files:
            logger.info(f"Reading {file_path.name}")
            with rasterio.open(file_path) as src:
                data = src.read(1)
                # Handle nodata values
                if 'nodata' in meta:
                    valid_mask = data != meta['nodata']
                else:
                    valid_mask = ~np.isnan(data)
                
                sum_array[valid_mask] += data[valid_mask]
                count_array[valid_mask] += 1
        
        # Compute average
        avg_array = np.divide(sum_array, count_array, 
                             out=np.zeros_like(sum_array), 
                             where=count_array > 0)
        
        # Set nodata values
        if 'nodata' in meta:
            avg_array[count_array == 0] = meta['nodata']
        else:
            avg_array[count_array == 0] = -9999
            meta['nodata'] = -9999
        
        # Update metadata
        meta.update({
            'dtype': 'float32',
            'compress': 'lzw'
        })
        
        # Write output
        if output_name is None:
            output_name = f"{variable}_{year}_annual.tif"
        output_path = input_dir / output_name
        
        with rasterio.open(output_path, 'w', **meta) as dst:
            dst.write(avg_array, 1)
            
        logger.info(f"Created annual average: {output_path}")
        return output_path
    
    def compute_annual_total(self, variable, year, months, output_name=None):
        """
        Compute annual total from monthly rasters (e.g., for rainfall).
        
        Args:
            variable: Variable name (e.g., 'rainfall')
            year: Year to process
            months: List of month numbers to include
            output_name: Custom output filename (optional)
        """
        input_dir = self.base_dir / variable
        
        # Find monthly files
        monthly_files = []
        for month in months:
            pattern = f"{variable}_{year}_{month:02d}.tif"
            file_path = input_dir / pattern
            if file_path.exists():
                monthly_files.append(file_path)
        
        if not monthly_files:
            logger.error(f"No monthly files found for {variable} {year}")
            return None
            
        logger.info(f"Summing {len(monthly_files)} files for {variable} {year}")
        
        # Read first file to get metadata
        with rasterio.open(monthly_files[0]) as src:
            meta = src.meta.copy()
            height = src.height
            width = src.width
            
        # Initialize array for accumulation
        sum_array = np.zeros((height, width), dtype=np.float32)
        valid_count = np.zeros((height, width), dtype=np.int16)
        
        # Process each monthly file
        for file_path in monthly_files:
            logger.info(f"Reading {file_path.name}")
            with rasterio.open(file_path) as src:
                data = src.read(1)
                # Handle nodata values
                if 'nodata' in meta:
                    valid_mask = data != meta['nodata']
                else:
                    valid_mask = ~np.isnan(data)
                
                sum_array[valid_mask] += data[valid_mask]
                valid_count[valid_mask] += 1
        
        # Extrapolate to full year if needed (assuming we have partial year data)
        if len(monthly_files) < 12:
            logger.warning(f"Only {len(monthly_files)} months available, extrapolating to annual")
            # Simple scaling - multiply by 12/n_months
            scale_factor = 12.0 / len(monthly_files)
            sum_array = sum_array * scale_factor
        
        # Set nodata values
        if 'nodata' in meta:
            sum_array[valid_count == 0] = meta['nodata']
        else:
            sum_array[valid_count == 0] = -9999
            meta['nodata'] = -9999
        
        # Update metadata
        meta.update({
            'dtype': 'float32',
            'compress': 'lzw'
        })
        
        # Write output
        if output_name is None:
            output_name = f"{variable}_{year}_annual.tif"
        output_path = input_dir / output_name
        
        with rasterio.open(output_path, 'w', **meta) as dst:
            dst.write(sum_array, 1)
            
        logger.info(f"Created annual total: {output_path}")
        return output_path
    
    def process_all_annual_summaries(self):
        """Process all available monthly data to create annual summaries."""
        
        # Temperature - compute annual means
        self.compute_annual_average('temperature', 2021, [10, 11, 12])
        self.compute_annual_average('temperature', 2018, [8, 9, 10, 11, 12])
        
        # Rainfall - compute annual totals
        self.compute_annual_total('rainfall', 2021, [10, 11, 12])
        self.compute_annual_total('rainfall', 2018, [8, 9, 10, 11, 12])
        
        # EVI - compute annual means
        self.compute_annual_average('evi', 2018, [8, 9, 10, 11, 12])
        
        # Soil wetness - compute annual means
        self.compute_annual_average('soil_wetness', 2018, [8, 9, 10, 11, 12])
        
        logger.info("Completed all annual summary computations")
        
    def create_summary_report(self):
        """Create a report of all available rasters."""
        report = f"""# Raster Database Summary
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Available Annual Rasters

"""
        # Check each directory
        for dir_path in self.base_dir.iterdir():
            if dir_path.is_dir() and not dir_path.name.startswith('.'):
                annual_files = list(dir_path.glob("*annual*.tif"))
                if annual_files:
                    report += f"### {dir_path.name}\n"
                    for file in sorted(annual_files):
                        report += f"- {file.name}\n"
                    report += "\n"
        
        # Write report
        report_path = self.base_dir / "ANNUAL_RASTERS_SUMMARY.md"
        with open(report_path, 'w') as f:
            f.write(report)
            
        logger.info(f"Summary report created: {report_path}")


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Compute annual raster summaries')
    parser.add_argument('--base-dir', default='app/tpr_module/raster_database',
                       help='Base directory containing raster subdirectories')
    parser.add_argument('--process-all', action='store_true',
                       help='Process all available monthly data')
    
    args = parser.parse_args()
    
    processor = AnnualRasterProcessor(args.base_dir)
    
    if args.process_all:
        processor.process_all_annual_summaries()
        processor.create_summary_report()
    else:
        # Example: process specific variable
        logger.info("Use --process-all to compute all annual summaries")
        logger.info("Example: python compute_annual_averages.py --process-all")


if __name__ == "__main__":
    main()