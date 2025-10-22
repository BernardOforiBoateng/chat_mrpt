#!/usr/bin/env python3
"""
Fix the export folder in your Earth Engine script
"""

import os

def update_export_folder():
    script_name = "extract_nigeria_indices_gdrive.py"
    
    print("Current folder configuration:")
    print("-" * 50)
    
    # Read current configuration
    with open(script_name, 'r') as f:
        content = f.read()
    
    # Find current folder name
    import re
    current_folder = re.search(r"GOOGLE_DRIVE_FOLDER\s*=\s*['\"]([^'\"]+)['\"]", content)
    
    if current_folder:
        print(f"Current folder: {current_folder.group(1)}")
    
    print("\nTo update the folder name:")
    print("1. Check the exact name of your folder in Google Drive")
    print("2. Edit the script and change this line:")
    print("   GOOGLE_DRIVE_FOLDER = 'Nigeria_Raster_Indices'")
    print("   to:")
    print("   GOOGLE_DRIVE_FOLDER = 'YOUR_ACTUAL_FOLDER_NAME'")
    
    print("\nIMPORTANT:")
    print("- Use the folder NAME, not the URL or ID")
    print("- The folder name is case-sensitive")
    print("- If the folder has spaces, include them exactly")
    
    # Create a backup
    backup_name = script_name + ".backup"
    with open(backup_name, 'w') as f:
        f.write(content)
    print(f"\nBackup created: {backup_name}")

if __name__ == "__main__":
    update_export_folder()
    
    print("\n" + "="*60)
    print("Your exports are probably in 'Nigeria_Raster_Indices' folder")
    print("="*60)
    print("\nSince the script already ran with this folder name,")
    print("your exports are likely going there.")
    print("\nTo find them:")
    print("1. In Google Drive, search for: Nigeria_Raster_Indices")
    print("2. Or search for: NDWI_2015")
    print("3. Or search for: *.tif")
    print("\nThe folder might be:")
    print("- In your 'My Drive'")
    print("- In 'Shared with me' if using a shared account")
    print("- Created by Earth Engine automatically")