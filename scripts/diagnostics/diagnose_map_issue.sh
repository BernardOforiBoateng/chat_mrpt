#!/bin/bash

echo "=== Map Visualization Diagnostic ==="
echo "===================================="
echo ""

# 1. Check for recently created map files
echo "1. Recent map files (last 30 minutes):"
echo "--------------------------------------"
find instance/uploads -name "*map*.html" -mmin -30 -ls 2>/dev/null | tail -10
echo ""

# 2. Check file sizes
echo "2. Map file sizes:"
echo "------------------"
find instance/uploads -name "*map*.html" -exec ls -lh {} \; 2>/dev/null | tail -10
echo ""

# 3. Check map generation logs
echo "3. Map/visualization logs:"
echo "--------------------------"
tail -200 gunicorn.log | grep -i "map\|visualization\|folium\|plotly" | tail -20
echo ""

# 4. Check for errors during visualization
echo "4. Visualization errors:"
echo "------------------------"
tail -200 gunicorn.log | grep -i "error.*viz\|failed.*map\|exception.*visualization" | tail -20
echo ""

# 5. Check a sample map file content
echo "5. Sample map file content (first 50 lines):"
echo "--------------------------------------------"
latest_map=$(find instance/uploads -name "*map*.html" -mmin -30 | head -1)
if [ ! -z "$latest_map" ]; then
    echo "File: $latest_map"
    head -50 "$latest_map"
else
    echo "No recent map files found"
fi
echo ""

# 6. Check visualization service status
echo "6. Visualization-related imports:"
echo "---------------------------------"
grep -l "folium\|plotly" app/services/*.py app/tools/*.py 2>/dev/null | head -10
echo ""

# 7. Check file serving route
echo "7. File serving logs:"
echo "---------------------"
tail -100 gunicorn.log | grep -i "serve_viz_file\|GET.*map.*html" | tail -10
echo ""

# 8. Check for JavaScript/resource errors
echo "8. Resource loading issues:"
echo "---------------------------"
if [ ! -z "$latest_map" ]; then
    echo "Checking for CDN/resource URLs in map:"
    grep -o "https://[^\"']*" "$latest_map" | sort | uniq | head -10
fi
echo ""

# 9. Check shapefile status
echo "9. Shapefile availability:"
echo "--------------------------"
find instance/uploads -name "*.shp" -o -name "*.geojson" | tail -5
echo ""

# 10. Check memory/resource usage
echo "10. System resources:"
echo "--------------------"
free -h
echo ""
df -h | grep -E "Filesystem|/$"