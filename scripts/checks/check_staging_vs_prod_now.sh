#!/bin/bash

echo "======================================================"
echo "   STAGING VS PRODUCTION - CURRENT STATE CHECK"
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

echo "📋 1. CHECKING KEY FILES"
echo "========================"
echo ""

# Critical files to check
FILES=(
    "app/data_analysis_v3/core/agent.py"
    "app/data_analysis_v3/core/data_profiler.py"
    "app/data_analysis_v3/prompts/system_prompt.py"
    "app/web/routes/data_analysis_v3_routes.py"
    "app/templates/index.html"
)

for file in "${FILES[@]}"; do
    echo "Checking: $file"
    
    # Get checksums from staging
    staging_hash=$(ssh -i "$KEY_PATH" ec2-user@$STAGING_IP "cd ChatMRPT && md5sum $file 2>/dev/null | cut -d' ' -f1")
    
    # Get checksums from production instance 1
    prod1_hash=$(ssh -i "$KEY_PATH" ec2-user@$STAGING_IP "ssh -o StrictHostKeyChecking=no -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP1 'cd ChatMRPT && md5sum $file 2>/dev/null | cut -d\" \" -f1'")
    
    # Get checksums from production instance 2
    prod2_hash=$(ssh -i "$KEY_PATH" ec2-user@$STAGING_IP "ssh -o StrictHostKeyChecking=no -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP2 'cd ChatMRPT && md5sum $file 2>/dev/null | cut -d\" \" -f1'")
    
    if [ "$staging_hash" = "$prod1_hash" ] && [ "$prod1_hash" = "$prod2_hash" ]; then
        echo "  ✅ All match"
    else
        echo "  ❌ DIFFERENT!"
        echo "     Staging:  ${staging_hash:0:8}..."
        echo "     Prod-1:   ${prod1_hash:0:8}..."
        echo "     Prod-2:   ${prod2_hash:0:8}..."
    fi
done

echo ""
echo "📋 2. DATA_ANALYSIS_V3 DIRECTORY"
echo "================================="
echo ""

echo "File count in app/data_analysis_v3:"
staging_count=$(ssh -i "$KEY_PATH" ec2-user@$STAGING_IP "cd ChatMRPT && find app/data_analysis_v3 -type f -name '*.py' | wc -l")
prod1_count=$(ssh -i "$KEY_PATH" ec2-user@$STAGING_IP "ssh -o StrictHostKeyChecking=no -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP1 'cd ChatMRPT && find app/data_analysis_v3 -type f -name \"*.py\" | wc -l'")
prod2_count=$(ssh -i "$KEY_PATH" ec2-user@$STAGING_IP "ssh -o StrictHostKeyChecking=no -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP2 'cd ChatMRPT && find app/data_analysis_v3 -type f -name \"*.py\" | wc -l'")

echo "Staging:     $staging_count files"
echo "Production1: $prod1_count files"
echo "Production2: $prod2_count files"

if [ "$staging_count" != "$prod1_count" ] || [ "$prod1_count" != "$prod2_count" ]; then
    echo "❌ File count mismatch!"
else
    echo "✅ File counts match"
fi

echo ""
echo "📋 3. ENVIRONMENT/CONFIG"
echo "========================"
echo ""

echo "Checking for environment differences..."

# Check if Redis is enabled
echo ""
echo "Redis configuration:"
echo "Staging:"
ssh -i "$KEY_PATH" ec2-user@$STAGING_IP "cd ChatMRPT && grep -E 'REDIS|SESSION_TYPE' .env 2>/dev/null | head -3" | sed 's/^/  /'

echo "Production 1:"
ssh -i "$KEY_PATH" ec2-user@$STAGING_IP "ssh -o StrictHostKeyChecking=no -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP1 'cd ChatMRPT && grep -E \"REDIS|SESSION_TYPE\" .env 2>/dev/null | head -3'" | sed 's/^/  /'

echo ""
echo "📋 4. RECENT MODIFICATIONS"
echo "=========================="
echo ""

echo "Last modified files on Staging:"
ssh -i "$KEY_PATH" ec2-user@$STAGING_IP 'cd ChatMRPT && find app -type f -name "*.py" -mtime -1 2>/dev/null | head -5' | sed 's/^/  /'

echo ""
echo "Last modified files on Production 1:"
ssh -i "$KEY_PATH" ec2-user@$STAGING_IP "ssh -o StrictHostKeyChecking=no -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP1 'cd ChatMRPT && find app -type f -name \"*.py\" -mtime -1 2>/dev/null | head -5'" | sed 's/^/  /'

echo ""
echo "📋 5. SERVICE STATUS"
echo "===================="
echo ""

echo "Staging service:"
ssh -i "$KEY_PATH" ec2-user@$STAGING_IP 'sudo systemctl status chatmrpt | grep "Active:" | head -1' | sed 's/^/  /'

echo "Production 1 service:"
ssh -i "$KEY_PATH" ec2-user@$STAGING_IP "ssh -o StrictHostKeyChecking=no -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP1 'sudo systemctl status chatmrpt | grep \"Active:\" | head -1'" | sed 's/^/  /'

echo "Production 2 service:"
ssh -i "$KEY_PATH" ec2-user@$STAGING_IP "ssh -o StrictHostKeyChecking=no -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP2 'sudo systemctl status chatmrpt | grep \"Active:\" | head -1'" | sed 's/^/  /'

echo ""
echo "======================================================"
echo "   SUMMARY"
echo "======================================================"
echo ""
echo "Check the differences above to identify what's different"
echo "between staging (working) and production (not working)."
echo ""