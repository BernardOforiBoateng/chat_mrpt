#!/bin/bash

echo "======================================================"
echo "   STAGING VS PRODUCTION COMPARISON"
echo "======================================================"
echo "Date: $(date)"
echo ""

KEY_PATH="/tmp/chatmrpt-key2.pem"
STAGING_IP="3.21.167.170"
PROD_IP1="172.31.44.52"
PROD_IP2="172.31.43.200"

# Copy key if needed
if [ ! -f "$KEY_PATH" ]; then
    cp aws_files/chatmrpt-key.pem "$KEY_PATH"
    chmod 600 "$KEY_PATH"
fi

echo "📋 SECTION 1: PYTHON PACKAGES"
echo "=============================="
echo ""

echo "🔍 Checking Staging packages..."
ssh -i "$KEY_PATH" ec2-user@$STAGING_IP 'cd ChatMRPT && source chatmrpt_venv/bin/activate && pip list | grep -E "ftfy|chardet|langchain|openai|pandas|flask|gunicorn" | sort' > /tmp/staging_packages.txt

echo "🔍 Checking Production Instance 1 packages..."
ssh -i "$KEY_PATH" ec2-user@$STAGING_IP "ssh -o StrictHostKeyChecking=no -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP1 'cd ChatMRPT && source chatmrpt_venv/bin/activate && pip list | grep -E \"ftfy|chardet|langchain|openai|pandas|flask|gunicorn\" | sort'" > /tmp/prod1_packages.txt

echo "📊 Package Comparison:"
echo "----------------------"
echo "Staging Only:"
comm -23 /tmp/staging_packages.txt /tmp/prod1_packages.txt | sed 's/^/  ⚠️  /'
echo ""
echo "Production Only:"
comm -13 /tmp/staging_packages.txt /tmp/prod1_packages.txt | sed 's/^/  ⚠️  /'
echo ""
echo "Common Packages (showing version differences):"
diff -y --suppress-common-lines /tmp/staging_packages.txt /tmp/prod1_packages.txt | head -10

echo ""
echo "📋 SECTION 2: DATA_ANALYSIS_V3 DIRECTORY"
echo "========================================"
echo ""

echo "🔍 Checking Staging data_analysis_v3 files..."
ssh -i "$KEY_PATH" ec2-user@$STAGING_IP 'cd ChatMRPT && find app/data_analysis_v3 -type f -name "*.py" | sort' > /tmp/staging_v3_files.txt

echo "🔍 Checking Production data_analysis_v3 files..."
ssh -i "$KEY_PATH" ec2-user@$STAGING_IP "ssh -o StrictHostKeyChecking=no -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP1 'cd ChatMRPT && find app/data_analysis_v3 -type f -name \"*.py\" | sort'" > /tmp/prod_v3_files.txt

echo "Files in Staging but NOT in Production:"
comm -23 /tmp/staging_v3_files.txt /tmp/prod_v3_files.txt | sed 's/^/  ❌ /'
echo ""
echo "Files in Production but NOT in Staging:"
comm -13 /tmp/staging_v3_files.txt /tmp/prod_v3_files.txt | sed 's/^/  ➕ /'

echo ""
echo "📋 SECTION 3: KEY FILE CHECKSUMS"
echo "================================"
echo ""

# Check critical files
FILES_TO_CHECK=(
    "app/data_analysis_v3/core/agent.py"
    "app/data_analysis_v3/core/encoding_handler.py"
    "app/static/js/modules/chat/core/message-handler.js"
    "app/web/routes/data_analysis_v3_routes.py"
    "app/templates/index.html"
    "requirements.txt"
)

for file in "${FILES_TO_CHECK[@]}"; do
    echo "Checking: $file"
    
    staging_hash=$(ssh -i "$KEY_PATH" ec2-user@$STAGING_IP "cd ChatMRPT && md5sum $file 2>/dev/null | cut -d' ' -f1")
    prod_hash=$(ssh -i "$KEY_PATH" ec2-user@$STAGING_IP "ssh -o StrictHostKeyChecking=no -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP1 'cd ChatMRPT && md5sum $file 2>/dev/null | cut -d\" \" -f1'")
    
    if [ "$staging_hash" = "$prod_hash" ]; then
        echo "  ✅ Match"
    else
        echo "  ❌ DIFFERENT - Staging: ${staging_hash:0:8}... Prod: ${prod_hash:0:8}..."
    fi
done

echo ""
echo "📋 SECTION 4: SERVICE CONFIGURATION"
echo "===================================="
echo ""

echo "🔍 Checking Gunicorn workers..."
echo "Staging:"
ssh -i "$KEY_PATH" ec2-user@$STAGING_IP 'ps aux | grep gunicorn | grep -v grep | wc -l' | sed 's/^/  Workers: /'
echo "Production Instance 1:"
ssh -i "$KEY_PATH" ec2-user@$STAGING_IP "ssh -o StrictHostKeyChecking=no -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP1 'ps aux | grep gunicorn | grep -v grep | wc -l'" | sed 's/^/  Workers: /'

echo ""
echo "📋 SECTION 5: RECENT CHANGES"
echo "============================="
echo ""

echo "🔍 Last 5 modified files on Staging:"
ssh -i "$KEY_PATH" ec2-user@$STAGING_IP 'cd ChatMRPT && find app -type f -name "*.py" -o -name "*.js" | xargs ls -lt 2>/dev/null | head -5 | cut -d" " -f9-'

echo ""
echo "🔍 Last 5 modified files on Production:"
ssh -i "$KEY_PATH" ec2-user@$STAGING_IP "ssh -o StrictHostKeyChecking=no -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP1 'cd ChatMRPT && find app -type f -name \"*.py\" -o -name \"*.js\" | xargs ls -lt 2>/dev/null | head -5 | cut -d\" \" -f9-'"

echo ""
echo "======================================================"
echo "   SUMMARY"
echo "======================================================"
echo ""
echo "Key differences will be listed above."
echo "Files marked with ❌ need to be synced from staging to production."
echo ""