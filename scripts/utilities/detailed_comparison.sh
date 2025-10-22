#!/bin/bash

echo "======================================================"
echo "   DETAILED STAGING VS PRODUCTION COMPARISON"
echo "======================================================"
echo ""

KEY_PATH="/tmp/chatmrpt-key2.pem"
STAGING_IP="3.21.167.170"
PROD_IP1="172.31.44.52"

# Copy key if needed
if [ ! -f "$KEY_PATH" ]; then
    cp aws_files/chatmrpt-key.pem "$KEY_PATH"
    chmod 600 "$KEY_PATH"
fi

echo "📋 1. REQUIREMENTS.TXT DIFFERENCES"
echo "==================================="
echo ""

echo "Getting requirements from Staging..."
ssh -i "$KEY_PATH" ec2-user@$STAGING_IP 'cd ChatMRPT && cat requirements.txt | grep -E "ftfy|chardet|langchain|openai" | sort' > /tmp/staging_req.txt

echo "Getting requirements from Production..."
ssh -i "$KEY_PATH" ec2-user@$STAGING_IP "ssh -o StrictHostKeyChecking=no -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP1 'cd ChatMRPT && cat requirements.txt | grep -E \"ftfy|chardet|langchain|openai\" | sort'" > /tmp/prod_req.txt

echo "Staging requirements:"
cat /tmp/staging_req.txt | sed 's/^/  /'
echo ""
echo "Production requirements:"
cat /tmp/prod_req.txt | sed 's/^/  /'
echo ""

echo "📋 2. ACTUALLY INSTALLED PACKAGES"
echo "=================================="
echo ""

echo "Staging installed (using correct venv path)..."
ssh -i "$KEY_PATH" ec2-user@$STAGING_IP 'cd ChatMRPT && if [ -d "chatmrpt_venv" ]; then source chatmrpt_venv/bin/activate; elif [ -d "venv" ]; then source venv/bin/activate; fi && pip list | grep -E "ftfy|chardet|langchain|openai" | sort' > /tmp/staging_installed.txt

echo "Production installed..."
ssh -i "$KEY_PATH" ec2-user@$STAGING_IP "ssh -o StrictHostKeyChecking=no -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP1 'cd ChatMRPT && if [ -d \"chatmrpt_venv\" ]; then source chatmrpt_venv/bin/activate; elif [ -d \"venv\" ]; then source venv/bin/activate; fi && pip list | grep -E \"ftfy|chardet|langchain|openai\" | sort'" > /tmp/prod_installed.txt

echo "Staging installed packages:"
cat /tmp/staging_installed.txt | sed 's/^/  /'
echo ""
echo "Production installed packages:"
cat /tmp/prod_installed.txt | sed 's/^/  /'
echo ""

echo "📋 3. HTML TEMPLATE DIFFERENCES"
echo "================================"
echo ""

echo "Checking for 'Data Analysis' vs 'TPR Analysis' text..."
echo ""
echo "Staging index.html:"
ssh -i "$KEY_PATH" ec2-user@$STAGING_IP 'cd ChatMRPT && grep -E "Data Analysis|TPR Analysis" app/templates/index.html | head -3' | sed 's/^/  /'
echo ""
echo "Production index.html:"
ssh -i "$KEY_PATH" ec2-user@$STAGING_IP "ssh -o StrictHostKeyChecking=no -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP1 'cd ChatMRPT && grep -E \"Data Analysis|TPR Analysis\" app/templates/index.html | head -3'" | sed 's/^/  /'

echo ""
echo "📋 4. JAVASCRIPT FILES"
echo "======================"
echo ""

echo "Checking message-handler.js modification times..."
echo "Staging:"
ssh -i "$KEY_PATH" ec2-user@$STAGING_IP 'cd ChatMRPT && ls -la app/static/js/modules/chat/core/message-handler.js' | awk '{print "  "$6" "$7" "$8}'
echo "Production:"
ssh -i "$KEY_PATH" ec2-user@$STAGING_IP "ssh -o StrictHostKeyChecking=no -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP1 'cd ChatMRPT && ls -la app/static/js/modules/chat/core/message-handler.js'" | awk '{print "  "$6" "$7" "$8}'

echo ""
echo "📋 5. DATA_ANALYSIS_V3 COMPLETE CHECK"
echo "======================================"
echo ""

echo "Total files in data_analysis_v3:"
echo "Staging:"
ssh -i "$KEY_PATH" ec2-user@$STAGING_IP 'cd ChatMRPT && find app/data_analysis_v3 -type f -name "*.py" | wc -l' | sed 's/^/  Files: /'
echo "Production:"
ssh -i "$KEY_PATH" ec2-user@$STAGING_IP "ssh -o StrictHostKeyChecking=no -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP1 'cd ChatMRPT && find app/data_analysis_v3 -type f -name \"*.py\" | wc -l'" | sed 's/^/  Files: /'

echo ""
echo "📋 6. WEB ROUTES"
echo "================"
echo ""

echo "Checking for data_analysis_v3_routes.py..."
echo "Staging:"
ssh -i "$KEY_PATH" ec2-user@$STAGING_IP 'cd ChatMRPT && ls -la app/web/routes/data_analysis_v3_routes.py 2>/dev/null || echo "  NOT FOUND"' | awk '{print "  "$9}'
echo "Production:"
ssh -i "$KEY_PATH" ec2-user@$STAGING_IP "ssh -o StrictHostKeyChecking=no -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP1 'cd ChatMRPT && ls -la app/web/routes/data_analysis_v3_routes.py 2>/dev/null || echo \"  NOT FOUND\"'" | awk '{print "  "$9}'

echo ""
echo "======================================================"
echo "   SUMMARY OF DIFFERENCES"
echo "======================================================"
echo ""

# Quick check for critical differences
if diff -q /tmp/staging_installed.txt /tmp/prod_installed.txt > /dev/null; then
    echo "✅ Installed packages: MATCH"
else
    echo "❌ Installed packages: DIFFERENT"
fi

staging_v3_count=$(ssh -i "$KEY_PATH" ec2-user@$STAGING_IP 'cd ChatMRPT && find app/data_analysis_v3 -type f -name "*.py" | wc -l')
prod_v3_count=$(ssh -i "$KEY_PATH" ec2-user@$STAGING_IP "ssh -o StrictHostKeyChecking=no -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP1 'cd ChatMRPT && find app/data_analysis_v3 -type f -name \"*.py\" | wc -l'")

if [ "$staging_v3_count" = "$prod_v3_count" ]; then
    echo "✅ Data Analysis V3 files: MATCH ($staging_v3_count files)"
else
    echo "❌ Data Analysis V3 files: DIFFERENT (Staging: $staging_v3_count, Prod: $prod_v3_count)"
fi

echo ""
echo "Note: The index.html difference is expected (Production was just updated to 'Data Analysis')"
echo ""