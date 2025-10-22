#!/usr/bin/env python3
"""
Explore ECOSTRESS LST folder structure and catalog raster files
Prepares inventory for upload to Cloud Storage bucket and DHS/field study extraction
"""

import os
import glob
from pathlib import Path
import pandas as pd
from datetime import datetime
import rasterio
import json

def get_file_info(filepath):
    """Get detailed information about a raster file"""
    info = {
        'filename': os.path.basename(filepath),
        'folder': os.path.basename(os.path.dirname(filepath)),
        'full_path': filepath,
        'size_mb': round(os.path.getsize(filepath) / (1024*1024), 2),
        'modified_date': datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Try to read raster metadata
    try:
        with rasterio.open(filepath) as src:
            info['crs'] = str(src.crs)
            info['width'] = src.width
            info['height'] = src.height
            info['bands'] = src.count
            info['dtype'] = str(src.dtypes[0])
            info['bounds'] = {
                'left': src.bounds.left,
                'bottom': src.bounds.bottom,
                'right': src.bounds.right,
                'top': src.bounds.top
            }
            info['transform'] = str(src.transform)
            info['nodata'] = src.nodata
    except Exception as e:
        info['error'] = str(e)
    
    return info

def analyze_folder_structure(base_path):
    """Analyze the folder structure and file naming patterns"""
    
    # Dictionary to store results
    results = {
        'summary': {},
        'folders': {},
        'all_files': []
    }
    
    # Get all subdirectories
    subdirs = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
    subdirs.sort()
    
    print("=" * 80)
    print("ECOSTRESS LST FOLDER STRUCTURE ANALYSIS")
    print("=" * 80)
    print(f"\nBase path: {base_path}")
    print(f"Found {len(subdirs)} subdirectories:")
    
    total_files = 0
    total_size_gb = 0
    
    # Analyze each subdirectory
    for subdir in subdirs:
        subdir_path = os.path.join(base_path, subdir)
        print(f"\n{'='*60}")
        print(f"Analyzing: {subdir}")
        print(f"{'='*60}")
        
        # Find all raster files (common extensions)
        raster_patterns = ['*.tif', '*.tiff', '*.TIF', '*.TIFF', '*.hdf', '*.HDF', '*.nc', '*.grd']
        raster_files = []
        
        for pattern in raster_patterns:
            files = glob.glob(os.path.join(subdir_path, '**', pattern), recursive=True)
            raster_files.extend(files)
        
        # Remove duplicates and sort
        raster_files = sorted(list(set(raster_files)))
        
        if not raster_files:
            print(f"  ⚠ No raster files found")
            results['folders'][subdir] = {
                'file_count': 0,
                'files': []
            }
            continue
        
        print(f"  ✓ Found {len(raster_files)} raster file(s)")
        
        # Analyze file naming patterns
        filenames = [os.path.basename(f) for f in raster_files]
        
        # Try to identify patterns
        print("\n  File naming patterns:")
        
        # Check for year patterns
        years = set()
        months = set()
        for fname in filenames:
            # Look for 4-digit years
            import re
            year_matches = re.findall(r'20[0-2][0-9]', fname)
            years.update(year_matches)
            
            # Look for month patterns (01-12)
            month_matches = re.findall(r'_([01][0-9])_', fname)
            months.update(month_matches)
        
        if years:
            print(f"    Years found: {sorted(years)}")
        if months:
            print(f"    Months found: {sorted(months)}")
        
        # Sample first few files for details
        print(f"\n  First {min(5, len(raster_files))} files:")
        folder_info = {
            'file_count': len(raster_files),
            'files': [],
            'total_size_mb': 0
        }
        
        for i, filepath in enumerate(raster_files):
            file_info = get_file_info(filepath)
            folder_info['files'].append(file_info)
            folder_info['total_size_mb'] += file_info['size_mb']
            results['all_files'].append(file_info)
            
            if i < 5:  # Show first 5 files
                print(f"    {i+1}. {file_info['filename']}")
                print(f"       Size: {file_info['size_mb']} MB")
                if 'width' in file_info:
                    print(f"       Dimensions: {file_info['width']} x {file_info['height']}")
                    print(f"       Bands: {file_info['bands']}")
                if 'error' in file_info:
                    print(f"       ⚠ Error reading file: {file_info['error']}")
        
        results['folders'][subdir] = folder_info
        total_files += len(raster_files)
        total_size_gb += folder_info.get('total_size_mb', 0) / 1024
        
        print(f"\n  Total size in {subdir}: {folder_info['total_size_mb']/1024:.2f} GB")
    
    # Overall summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total folders: {len(subdirs)}")
    print(f"Total raster files: {total_files}")
    print(f"Total size: {total_size_gb:.2f} GB")
    
    results['summary'] = {
        'total_folders': len(subdirs),
        'total_files': total_files,
        'total_size_gb': round(total_size_gb, 2),
        'folders': subdirs
    }
    
    return results

def save_inventory(results, output_dir="/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT"):
    """Save the inventory to CSV and JSON files"""
    
    # Create DataFrame from all files
    if results['all_files']:
        df = pd.DataFrame(results['all_files'])
        
        # Save detailed inventory
        csv_path = os.path.join(output_dir, 'ecostress_lst_inventory.csv')
        df.to_csv(csv_path, index=False)
        print(f"\n✓ Detailed inventory saved to: {csv_path}")
        
        # Save summary JSON
        json_path = os.path.join(output_dir, 'ecostress_lst_summary.json')
        with open(json_path, 'w') as f:
            # Convert for JSON serialization
            summary_data = {
                'summary': results['summary'],
                'folders': {k: {
                    'file_count': v['file_count'],
                    'total_size_mb': v['total_size_mb']
                } for k, v in results['folders'].items()}
            }
            json.dump(summary_data, f, indent=2)
        print(f"✓ Summary saved to: {json_path}")
        
        # Group by folder for analysis
        print(f"\n{'='*80}")
        print("FILES BY FOLDER (for planning uploads)")
        print(f"{'='*80}")
        folder_summary = df.groupby('folder').agg({
            'filename': 'count',
            'size_mb': 'sum'
        }).round(2)
        folder_summary.columns = ['file_count', 'total_size_mb']
        folder_summary['total_size_gb'] = (folder_summary['total_size_mb'] / 1024).round(2)
        print(folder_summary)
        
        # Identify patterns for extraction planning
        print(f"\n{'='*80}")
        print("EXTRACTION PLANNING")
        print(f"{'='*80}")
        print("\nRecommendations:")
        print("1. Upload folders to Cloud Storage bucket in batches")
        print("2. Organize by year/half-year pattern (H1/H2)")
        print("3. Create GEE scripts for:")
        print("   - DHS extraction (2018, 2021, 2022, 2023, 2024)")
        print("   - Field study extraction (Kano & Ibadan)")
        
        # Check for specific patterns
        h1_folders = [f for f in results['folders'].keys() if 'H1' in f]
        h2_folders = [f for f in results['folders'].keys() if 'H2' in f]
        
        if h1_folders:
            print(f"\n✓ H1 (First half year) folders: {sorted(h1_folders)}")
        if h2_folders:
            print(f"✓ H2 (Second half year) folders: {sorted(h2_folders)}")
        
        eco_lst_folders = [f for f in results['folders'].keys() if 'ECO_LST' in f]
        if eco_lst_folders:
            print(f"✓ ECO_LST folders: {sorted(eco_lst_folders)}")

def main():
    # Base path to ECOSTRESS LST folder
    base_path = "/mnt/c/Users/bbofo/Urban Malaria Proj Dropbox/urban_malaria/data/nigeria/Raster_files/ECOSTRESS_LST"
    
    # Check if path exists
    if not os.path.exists(base_path):
        print(f"Error: Path does not exist: {base_path}")
        return
    
    # Analyze folder structure
    results = analyze_folder_structure(base_path)
    
    # Save inventory
    save_inventory(results)
    
    print("\n✅ Analysis complete!")
    print("\nNext steps:")
    print("1. Review ecostress_lst_inventory.csv for detailed file list")
    print("2. Review ecostress_lst_summary.json for folder structure")
    print("3. Plan upload strategy to Cloud Storage bucket")
    print("4. Create GEE extraction scripts for DHS and field study points")

if __name__ == "__main__":
    main()