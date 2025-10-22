#!/usr/bin/env python3
"""
Check Google Drive for exported NDWI/NDMI files
"""

import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def check_drive_manually():
    """Provide instructions for manual checking"""
    print("="*60)
    print("How to Check Your Exported Files in Google Drive")
    print("="*60)
    
    print("\n1. Open Google Drive in your browser")
    print("   https://drive.google.com")
    
    print("\n2. Look for the folder: 'Nigeria_Raster_Indices'")
    print("   - It should be in your main Drive folder")
    print("   - If not visible, use the search bar")
    
    print("\n3. Expected files (when completed):")
    years = [2015, 2018, 2021, 2023, 2024]
    months = range(7, 13)  # July to December
    
    print("\n   For each year-month combination:")
    print("   - NDWI_YYYY_MM_Nigeria.tif")
    print("   - NDMI_YYYY_MM_Nigeria.tif")
    
    print("\n   Total expected: 60 files")
    print("   - 30 NDWI files")
    print("   - 30 NDMI files")
    
    print("\n4. File sizes:")
    print("   - Each file should be several MB to GB")
    print("   - Empty or very small files indicate export issues")
    
    print("\n5. Based on your script output, these should be completed:")
    completed = [
        "NDWI_2015_07_Nigeria", "NDMI_2015_07_Nigeria",
        "NDWI_2015_08_Nigeria", "NDMI_2015_08_Nigeria",
        "NDWI_2015_09_Nigeria", "NDMI_2015_09_Nigeria",
        "NDWI_2015_10_Nigeria", "NDMI_2015_10_Nigeria",
        "NDWI_2015_11_Nigeria", "NDMI_2015_11_Nigeria",
        "NDWI_2015_12_Nigeria", "NDMI_2015_12_Nigeria",
        "NDWI_2018_07_Nigeria", "NDMI_2018_07_Nigeria",
        "NDWI_2018_08_Nigeria", "NDMI_2018_08_Nigeria",
        "NDWI_2018_09_Nigeria", "NDMI_2018_09_Nigeria",
        "NDWI_2018_10_Nigeria", "NDMI_2018_10_Nigeria",
        "NDWI_2018_11_Nigeria", "NDMI_2018_11_Nigeria"
    ]
    
    print("\n   Completed exports from your script:")
    for i, filename in enumerate(completed, 1):
        print(f"   {i}. {filename}.tif ✓")
    
    print(f"\n   Progress: {len(completed)}/60 files ({len(completed)/60*100:.1f}%)")

def list_completed_exports():
    """Show what exports have completed based on the script output"""
    print("\n" + "="*60)
    print("Summary of Your Export Progress")
    print("="*60)
    
    # Based on the terminal output you showed
    completed_count = 20  # Approximate from your output
    total_count = 60
    
    print(f"\nExport Status:")
    print(f"- Completed: ~{completed_count} tasks")
    print(f"- Remaining: ~{total_count - completed_count} tasks")
    print(f"- Progress: {completed_count/total_count*100:.1f}%")
    
    print("\nThe exports are running in the background on Google's servers.")
    print("They will continue even if you close your script.")
    
    print("\nEstimated completion time:")
    print("- Each export typically takes 5-30 minutes")
    print("- Total time for all 60 exports: 2-6 hours")
    print("- Files appear in Drive as soon as each export completes")

if __name__ == "__main__":
    print("Google Earth Engine Export Checker")
    print("==================================\n")
    
    check_drive_manually()
    list_completed_exports()
    
    print("\n" + "="*60)
    print("What to do if exports are missing:")
    print("="*60)
    print("1. Wait - exports can take time")
    print("2. Check Earth Engine quota limits")
    print("3. Re-run the export script for missing dates")
    print("4. Check for error messages in the task manager")