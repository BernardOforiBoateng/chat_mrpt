#!/bin/bash

echo "=== AWS Upload Issue Diagnostic ==="
echo "=================================="
echo ""

# 1. Check session directories
echo "1. Session directories in instance/uploads:"
echo "-------------------------------------------"
ls -la instance/uploads/ | tail -10
echo ""

# 2. Check recent file uploads
echo "2. Recently modified files (last 30 min):"
echo "-----------------------------------------"
find instance/uploads -type f -mmin -30 -ls 2>/dev/null | tail -10
echo ""

# 3. Check for CSV files
echo "3. CSV files in uploads:"
echo "------------------------"
find instance/uploads -name "*.csv" -ls 2>/dev/null | tail -10
echo ""

# 4. Check session handling in logs
echo "4. Session-related log entries:"
echo "-------------------------------"
tail -100 gunicorn.log | grep -i "session\|upload\|file.*saved\|raw_data" | tail -20
echo ""

# 5. Check file permissions
echo "5. Upload directory permissions:"
echo "--------------------------------"
ls -ld instance/uploads
ls -la instance/uploads/*/ 2>/dev/null | head -10
echo ""

# 6. Check disk space
echo "6. Disk space:"
echo "--------------"
df -h | grep -E "Filesystem|/$"
echo ""

# 7. Check data processing logs
echo "7. Data processing logs:"
echo "------------------------"
tail -100 gunicorn.log | grep -i "datahandler\|loaded.*data\|rows.*columns" | tail -20
echo ""

# 8. Check for errors during upload
echo "8. Upload errors:"
echo "-----------------"
tail -200 gunicorn.log | grep -i "error.*upload\|failed.*save\|exception.*file" | tail -20
echo ""

# 9. Check worker processes
echo "9. Gunicorn workers:"
echo "--------------------"
ps aux | grep gunicorn | grep -v grep
echo ""

# 10. Check environment variables
echo "10. Key environment variables:"
echo "------------------------------"
grep -E "UPLOAD_FOLDER|SESSION_TYPE|PERMANENT_SESSION" .env 2>/dev/null || echo "No relevant env vars found"
echo ""

# 11. Check latest session data
echo "11. Latest session directory contents:"
echo "--------------------------------------"
latest_session=$(ls -t instance/uploads/ | head -1)
if [ ! -z "$latest_session" ]; then
    echo "Latest session: $latest_session"
    ls -la "instance/uploads/$latest_session/" 2>/dev/null
else
    echo "No sessions found"
fi
echo ""

# 12. Check Flask session configuration
echo "12. Session configuration in production.py:"
echo "-------------------------------------------"
grep -A5 -B5 "SESSION\|session" app/config/production.py | grep -v "^--$"