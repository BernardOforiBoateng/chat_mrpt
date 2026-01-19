#!/usr/bin/env python3
"""Test map generation to diagnose visualization issues"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_visualization_imports():
    """Test if visualization libraries are available"""
    print("\n=== Testing Visualization Libraries ===")
    
    libraries = {
        'folium': False,
        'plotly': False,
        'matplotlib': False,
        'geopandas': False,
        'json': False
    }
    
    for lib in libraries:
        try:
            __import__(lib)
            libraries[lib] = True
            print(f"✓ {lib} - available")
        except ImportError as e:
            print(f"✗ {lib} - MISSING: {e}")
    
    return all(libraries.values())

def check_map_file_structure():
    """Check the structure of generated map files"""
    print("\n=== Checking Map File Structure ===")
    
    import glob
    map_files = glob.glob("instance/uploads/*/*.html")
    
    if not map_files:
        print("No map files found!")
        return
    
    # Check latest map file
    latest_map = max(map_files, key=os.path.getmtime)
    print(f"Latest map: {latest_map}")
    print(f"Size: {os.path.getsize(latest_map) / 1024:.1f} KB")
    
    with open(latest_map, 'r') as f:
        content = f.read()
    
    # Check for key components
    checks = {
        'HTML structure': '<html' in content and '</html>' in content,
        'Folium/Leaflet': 'leaflet' in content.lower() or 'folium' in content.lower(),
        'Map div': 'id="map"' in content or 'class="folium-map"' in content,
        'JavaScript': '<script' in content,
        'Tile layer': 'tile' in content.lower() or 'openstreetmap' in content.lower()
    }
    
    print("\nMap components:")
    for check, present in checks.items():
        print(f"  {check}: {'✓' if present else '✗'}")
    
    # Check for potential issues
    if content.strip() == '' or len(content) < 100:
        print("\n⚠️  WARNING: Map file is empty or too small!")
    
    if 'error' in content.lower() or 'exception' in content.lower():
        print("\n⚠️  WARNING: Map file contains error messages!")

def test_simple_map_creation():
    """Try to create a simple map to test the environment"""
    print("\n=== Testing Simple Map Creation ===")
    
    try:
        import folium
        import os
        
        # Create a simple map
        m = folium.Map(location=[0, 0], zoom_start=2)
        
        # Save it
        test_path = "instance/uploads/test_map.html"
        os.makedirs(os.path.dirname(test_path), exist_ok=True)
        m.save(test_path)
        
        print(f"✓ Test map created: {test_path}")
        print(f"  Size: {os.path.getsize(test_path) / 1024:.1f} KB")
        
        # Check if it's valid
        with open(test_path, 'r') as f:
            content = f.read()
        
        if 'leaflet' in content and len(content) > 1000:
            print("✓ Map appears valid")
        else:
            print("✗ Map may be invalid")
            
    except Exception as e:
        print(f"✗ Failed to create test map: {e}")
        import traceback
        traceback.print_exc()

def check_visualization_service():
    """Check if visualization service is properly initialized"""
    print("\n=== Checking Visualization Service ===")
    
    try:
        from app.services.visualization_service import VisualizationService
        print("✓ VisualizationService can be imported")
        
        # Check methods
        methods = ['create_choropleth_map', 'create_distribution_map', 'create_bar_chart']
        for method in methods:
            if hasattr(VisualizationService, method):
                print(f"  ✓ {method} exists")
            else:
                print(f"  ✗ {method} missing")
                
    except Exception as e:
        print(f"✗ Failed to import VisualizationService: {e}")

def check_serve_route():
    """Check the file serving configuration"""
    print("\n=== Checking File Serving Route ===")
    
    # Check if route exists
    route_files = [
        "app/web/routes/viz.py",
        "app/web/routes/core.py",
        "app/__init__.py"
    ]
    
    for file in route_files:
        if os.path.exists(file):
            with open(file, 'r') as f:
                content = f.read()
                if 'serve_viz_file' in content:
                    print(f"✓ serve_viz_file route found in {file}")
                    # Look for the route pattern
                    if '/serve_viz_file/' in content:
                        print("  Route pattern: /serve_viz_file/<filename>")

if __name__ == "__main__":
    print("Map Visualization Diagnostic Tool")
    print("=" * 40)
    
    test_visualization_imports()
    check_map_file_structure()
    test_simple_map_creation()
    check_visualization_service()
    check_serve_route()