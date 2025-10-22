#!/bin/bash

echo "=== ChatMRPT Analysis Diagnostic Check ==="
echo "========================================="
echo ""

# Check for errors in the last 200 lines
echo "1. Recent errors in logs:"
echo "------------------------"
tail -200 gunicorn.log | grep -i "error\|exception\|failed\|traceback" | grep -v HealthChecker | tail -20

echo ""
echo "2. Analysis-related log entries (last 100 lines):"
echo "-------------------------------------------------"
tail -100 gunicorn.log | grep -i "analysis\|composite\|pca\|vulnerability" | tail -20

echo ""
echo "3. Session state after analysis:"
echo "--------------------------------"
tail -50 gunicorn.log | grep -i "session\|state" | grep -v HealthChecker | tail -10

echo ""
echo "4. Tool execution logs:"
echo "----------------------"
tail -100 gunicorn.log | grep -i "tool\|execute\|running" | tail -15

echo ""
echo "5. Response/LLM-related logs:"
echo "-----------------------------"
tail -100 gunicorn.log | grep -i "response\|llm\|openai\|completion" | tail -15

echo ""
echo "6. File creation timestamps:"
echo "----------------------------"
ls -la instance/uploads/*/analysis_*.csv 2>/dev/null | tail -5

echo ""
echo "7. Check for incomplete analysis:"
echo "---------------------------------"
for dir in instance/uploads/*/; do
    if [ -d "$dir" ]; then
        session_id=$(basename "$dir")
        echo "Session: $session_id"
        csv_count=$(ls "$dir"analysis_*.csv 2>/dev/null | wc -l)
        html_count=$(ls "$dir"*_map_*.html 2>/dev/null | wc -l)
        echo "  Analysis CSVs: $csv_count"
        echo "  Map HTMLs: $html_count"
        if [ $csv_count -gt 0 ] && [ $html_count -eq 0 ]; then
            echo "  WARNING: Analysis files exist but no maps generated!"
        fi
    fi
done

echo ""
echo "8. Memory/Resource issues:"
echo "--------------------------"
tail -50 gunicorn.log | grep -i "memory\|timeout\|resource" | tail -10

echo ""
echo "9. Analysis pipeline stages:"
echo "---------------------------"
tail -100 gunicorn.log | grep -i "stage\|pipeline\|step" | tail -15

echo ""
echo "10. Critical errors in last 5 minutes:"
echo "--------------------------------------"
find . -name "*.log" -mmin -5 -exec grep -l "ERROR\|CRITICAL" {} \; 2>/dev/null