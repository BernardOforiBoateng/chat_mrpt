#!/usr/bin/env python3
"""Test export download functionality"""

import requests
import os

# Test data
session_id = "59b18890-638c-4c1e-862b-82a900cea3e9"
base_url = "http://127.0.0.1:5000"

# Check what files exist in export directory
export_dir = f"instance/exports/{session_id}"
print(f"Checking export directory: {export_dir}")

if os.path.exists(export_dir):
    print("Export files found:")
    for root, dirs, files in os.walk(export_dir):
        for file in files:
            file_path = os.path.join(root, file)
            print(f"  - {file_path}")
            
            # Try to access via URL
            relative_path = os.path.relpath(file_path, export_dir)
            download_url = f"{base_url}/export/download/{session_id}/{file}"
            print(f"    URL: {download_url}")
            
            # Test the download URL
            try:
                response = requests.get(download_url, timeout=5)
                print(f"    Response: {response.status_code}")
                if response.status_code != 200:
                    print(f"    Error: {response.text[:200]}")
            except Exception as e:
                print(f"    Error: {e}")
else:
    print("Export directory not found!")

# Also check for any zip files
print("\nLooking for ZIP files:")
for root, dirs, files in os.walk("instance/exports"):
    for file in files:
        if file.endswith('.zip'):
            print(f"  Found: {os.path.join(root, file)}")