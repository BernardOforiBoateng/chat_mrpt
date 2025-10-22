#!/bin/bash

echo "======================================================"
echo "   SYNCING STAGING TO PRODUCTION - FINAL CHECK"
echo "======================================================"
echo ""

KEY_PATH="/tmp/chatmrpt-key2.pem"
STAGING_IP="3.21.167.170"
PROD_IPS=("172.31.44.52" "172.31.43.200")

# Copy key if needed
if [ ! -f "$KEY_PATH" ]; then
    cp aws_files/chatmrpt-key.pem "$KEY_PATH"
    chmod 600 "$KEY_PATH"
fi

echo "📋 IDENTIFYING FILES TO SYNC"
echo "============================="
echo ""

# Files that might need syncing from staging to production
FILES_TO_CHECK=(
    "requirements.txt"
    "app/data_analysis_v3/core/agent.py"
    "app/data_analysis_v3/core/encoding_handler.py"
    "app/data_analysis_v3/core/tpr_workflow_handler.py"
    "app/data_analysis_v3/core/metadata_cache.py"
    "app/data_analysis_v3/tools/tpr_analysis_tool.py"
    "app/static/js/modules/upload/data-analysis-upload.js"
    "app/web/routes/__init__.py"
    "gunicorn_config.py"
)

echo "Checking which files are different..."
echo ""

DIFFERENT_FILES=()

for file in "${FILES_TO_CHECK[@]}"; do
    staging_hash=$(ssh -i "$KEY_PATH" ec2-user@$STAGING_IP "cd ChatMRPT && md5sum $file 2>/dev/null | cut -d' ' -f1")
    prod_hash=$(ssh -i "$KEY_PATH" ec2-user@$STAGING_IP "ssh -o StrictHostKeyChecking=no -i ~/.ssh/chatmrpt-key.pem ec2-user@${PROD_IPS[0]} 'cd ChatMRPT && md5sum $file 2>/dev/null | cut -d\" \" -f1'")
    
    if [ -z "$staging_hash" ]; then
        echo "  ⚠️  $file - Not found on staging"
    elif [ -z "$prod_hash" ]; then
        echo "  ❌ $file - Missing on production (needs to be copied)"
        DIFFERENT_FILES+=("$file")
    elif [ "$staging_hash" != "$prod_hash" ]; then
        echo "  ❌ $file - Different (needs update)"
        DIFFERENT_FILES+=("$file")
    else
        echo "  ✅ $file - Already synced"
    fi
done

echo ""
echo "📋 FILES THAT NEED SYNCING"
echo "=========================="
echo ""

if [ ${#DIFFERENT_FILES[@]} -eq 0 ]; then
    echo "✅ All checked files are already synced!"
else
    echo "The following files need to be synced from staging to production:"
    for file in "${DIFFERENT_FILES[@]}"; do
        echo "  • $file"
    done
fi

echo ""
echo "======================================================"
echo ""
