#!/bin/bash

echo "=== TPR Output Files Check on AWS ==="
echo "====================================="
echo ""

# 1. Check TPR-specific files across all sessions
echo "1. TPR Analysis files across all sessions:"
echo "------------------------------------------"
find instance/uploads -name "*TPR*.csv" -o -name "*tpr*.csv" -o -name "*TPR*.zip" -o -name "*tpr*.html" -ls 2>/dev/null | head -20
echo ""

# 2. Check ITN distribution files
echo "2. ITN Distribution files:"
echo "--------------------------"
find instance/uploads -name "itn_distribution_results.json" -o -name "*itn*.csv" -o -name "*ITN*.csv" -ls 2>/dev/null | head -20
echo ""

# 3. Check _plus.csv files (TPR + environmental variables)
echo "3. State_plus.csv files (main analysis):"
echo "----------------------------------------"
find instance/uploads -name "*_plus.csv" -ls 2>/dev/null | head -20
echo ""

# 4. Check shapefiles
echo "4. Shapefiles generated:"
echo "------------------------"
find instance/uploads -name "*.shp" -o -name "*.shx" -o -name "*.dbf" -o -name "*.prj" | head -20
echo ""

# 5. Check HTML reports
echo "5. HTML reports:"
echo "----------------"
find instance/uploads -name "*report*.html" -o -name "*Report*.html" -ls 2>/dev/null | head -10
echo ""

# 6. Check specific session structure (last 3 sessions)
echo "6. Session directory structures (last 3):"
echo "-----------------------------------------"
for session in $(ls -t instance/uploads/ | head -3); do
    echo "Session: $session"
    echo "Contents:"
    ls -la "instance/uploads/$session/" 2>/dev/null | grep -E "\.csv|\.json|\.html|\.zip|\.shp"
    echo "---"
done
echo ""

# 7. Check TPR pipeline logs
echo "7. TPR/ITN Pipeline execution logs:"
echo "-----------------------------------"
tail -200 gunicorn.log | grep -i "tpr\|itn.*distribution\|output.*generator" | tail -30
echo ""

# 8. Check file permissions on TPR outputs
echo "8. File permissions on recent TPR outputs:"
echo "------------------------------------------"
find instance/uploads -name "*TPR*.csv" -o -name "itn_distribution_results.json" -mtime -1 -ls 2>/dev/null | head -10
echo ""

# 9. Check for zip files
echo "9. Export packages (zip files):"
echo "-------------------------------"
find instance/uploads -name "*.zip" -ls 2>/dev/null | tail -10
echo ""

# 10. Check export directory
echo "10. Export directory contents:"
echo "------------------------------"
if [ -d "instance/exports" ]; then
    ls -la instance/exports/
    # Check subdirectories
    for dir in $(find instance/exports -type d -maxdepth 2 | tail -5); do
        echo "Dir: $dir"
        ls -la "$dir" 2>/dev/null | head -5
    done
else
    echo "No exports directory found"
fi
echo ""

# 11. Check for TPR module errors
echo "11. TPR module errors in logs:"
echo "------------------------------"
tail -500 gunicorn.log | grep -i "error.*tpr\|tpr.*error\|output.*generator.*error" | tail -20
echo ""

# 12. Disk usage by session
echo "12. Disk usage by session (top 10):"
echo "-----------------------------------"
du -sh instance/uploads/* 2>/dev/null | sort -rh | head -10
echo ""

# 13. Check for incomplete file operations
echo "13. Recent file write operations:"
echo "---------------------------------"
tail -100 gunicorn.log | grep -i "saved.*to\|writing.*file\|generated.*output" | tail -15
echo ""

# 14. Check specific TPR output patterns
echo "14. TPR Output Generator activity:"
echo "----------------------------------"
tail -200 gunicorn.log | grep -i "OutputGenerator\|generate_outputs\|TPR Analysis\|Summary Report" | tail -20