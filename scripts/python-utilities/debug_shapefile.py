#!/usr/bin/env python3
import os
import sys

print(f"Current working directory: {os.getcwd()}")
print(f"Python executable: {sys.executable}")

# Check all paths
paths = [
    'www/complete_names_wards/wards.shp',
    os.path.join(os.getcwd(), 'www/complete_names_wards/wards.shp'),
    'app/data/shapefiles/nigeria_wards.shp'
]

for path in paths:
    exists = os.path.exists(path)
    print(f"Path: {path}")
    print(f"  Exists: {exists}")
    if exists:
        print(f"  Size: {os.path.getsize(path)} bytes")
    print()

# Now test the actual function
sys.path.insert(0, '.')
print("Testing load_nigeria_shapefile function...")
try:
    from app.data_analysis_v3.tools.tpr_analysis_tool import load_nigeria_shapefile
    result = load_nigeria_shapefile()
    if result is not None:
        print(f"✅ SUCCESS: Loaded {len(result)} shapes")
    else:
        print("❌ FAILED: Function returned None")
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()