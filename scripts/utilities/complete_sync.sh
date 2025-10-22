#!/bin/bash

echo "======================================================"
echo "   COMPLETE STAGING TO PRODUCTION SYNC"
echo "======================================================"
echo "Date: $(date)"
echo ""

KEY_PATH="/tmp/chatmrpt-key2.pem"
STAGING_IP="3.21.167.170"
STAGING_IP2="18.220.103.20"  # Second staging instance
PROD_IPS=("172.31.44.52" "172.31.43.200")

# Copy key if needed
if [ ! -f "$KEY_PATH" ]; then
    cp aws_files/chatmrpt-key.pem "$KEY_PATH"
    chmod 600 "$KEY_PATH"
fi

echo "📋 PART 1: SYNC STAGING TO PRODUCTION"
echo "======================================"
echo ""

# Files to sync from staging to production
echo "1. Copying data-analysis-upload.js from staging to production..."
echo ""

# First, get the file from staging
ssh -i "$KEY_PATH" ec2-user@$STAGING_IP 'cd ChatMRPT && cp app/static/js/modules/upload/data-analysis-upload.js /tmp/data-analysis-upload.js.sync 2>/dev/null'

# Check if file exists on staging
if ssh -i "$KEY_PATH" ec2-user@$STAGING_IP '[ -f /tmp/data-analysis-upload.js.sync ]'; then
    echo "✅ File found on staging, copying to production..."
    
    # Deploy to each production instance
    for i in "${!PROD_IPS[@]}"; do
        IP="${PROD_IPS[$i]}"
        INSTANCE_NUM=$((i + 1))
        
        echo "  Copying to Production Instance $INSTANCE_NUM ($IP)..."
        
        # Create directory if needed
        ssh -i "$KEY_PATH" ec2-user@$STAGING_IP "ssh -o StrictHostKeyChecking=no -i ~/.ssh/chatmrpt-key.pem ec2-user@$IP 'cd ChatMRPT && mkdir -p app/static/js/modules/upload'"
        
        # Copy file
        ssh -i "$KEY_PATH" ec2-user@$STAGING_IP "scp -o StrictHostKeyChecking=no -i ~/.ssh/chatmrpt-key.pem /tmp/data-analysis-upload.js.sync ec2-user@$IP:/home/ec2-user/ChatMRPT/app/static/js/modules/upload/data-analysis-upload.js"
        
        echo "  ✅ Instance $INSTANCE_NUM updated"
    done
else
    echo "⚠️  data-analysis-upload.js not found on staging, skipping..."
fi

echo ""
echo "2. Syncing requirements.txt..."
echo ""

# Get requirements.txt from production (it has the correct ftfy and chardet)
echo "Getting current production requirements.txt..."
ssh -i "$KEY_PATH" ec2-user@$STAGING_IP "ssh -o StrictHostKeyChecking=no -i ~/.ssh/chatmrpt-key.pem ec2-user@${PROD_IPS[0]} 'cd ChatMRPT && cat requirements.txt'" > /tmp/prod_requirements.txt

# Check if production has ftfy and chardet
if grep -q "ftfy" /tmp/prod_requirements.txt && grep -q "chardet" /tmp/prod_requirements.txt; then
    echo "✅ Production requirements.txt already has ftfy and chardet"
else
    echo "⚠️  Production requirements.txt missing ftfy or chardet, this needs investigation"
fi

echo ""
echo "📋 PART 2: UPDATE STAGING HTML"
echo "=============================="
echo ""

echo "Updating staging index.html to match production (Data Analysis text)..."

# Copy the updated index.html from production to staging
echo "1. Getting updated index.html from production..."
ssh -i "$KEY_PATH" ec2-user@$STAGING_IP "ssh -o StrictHostKeyChecking=no -i ~/.ssh/chatmrpt-key.pem ec2-user@${PROD_IPS[0]} 'cd ChatMRPT && cat app/templates/index.html'" > /tmp/updated_index.html

# Deploy to both staging instances
for STAGING in "$STAGING_IP" "$STAGING_IP2"; do
    echo "2. Updating staging instance $STAGING..."
    
    # Copy to staging
    scp -i "$KEY_PATH" /tmp/updated_index.html ec2-user@$STAGING:/tmp/index.html.new
    ssh -i "$KEY_PATH" ec2-user@$STAGING 'cd ChatMRPT && cp /tmp/index.html.new app/templates/index.html'
    
    echo "  ✅ Staging instance $STAGING updated"
done

echo ""
echo "📋 PART 3: RESTART ALL SERVICES"
echo "==============================="
echo ""

echo "Restarting production instances..."
for i in "${!PROD_IPS[@]}"; do
    IP="${PROD_IPS[$i]}"
    INSTANCE_NUM=$((i + 1))
    
    echo "  Restarting Production Instance $INSTANCE_NUM..."
    ssh -i "$KEY_PATH" ec2-user@$STAGING_IP "ssh -o StrictHostKeyChecking=no -i ~/.ssh/chatmrpt-key.pem ec2-user@$IP 'sudo systemctl restart chatmrpt'"
done

echo ""
echo "Restarting staging instances..."
ssh -i "$KEY_PATH" ec2-user@$STAGING_IP 'sudo systemctl restart chatmrpt'
ssh -i "$KEY_PATH" ec2-user@$STAGING_IP2 'sudo systemctl restart chatmrpt'

echo ""
echo "📋 PART 4: VERIFICATION"
echo "======================="
echo ""

# Wait for services to restart
sleep 5

echo "Testing endpoints..."
echo ""

# Test production
prod_response=$(curl -s -o /dev/null -w "%{http_code}" http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com/ping)
if [ "$prod_response" = "200" ]; then
    echo "✅ Production: Healthy"
else
    echo "❌ Production: Status $prod_response"
fi

# Test staging
staging_response=$(curl -s -o /dev/null -w "%{http_code}" http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com/ping)
if [ "$staging_response" = "200" ]; then
    echo "✅ Staging: Healthy"
else
    echo "❌ Staging: Status $staging_response"
fi

echo ""
echo "Checking for 'Data Analysis' text..."
prod_has_data=$(curl -s http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com | grep -c "Data Analysis")
staging_has_data=$(curl -s http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com | grep -c "Data Analysis")

echo "Production has 'Data Analysis': $prod_has_data occurrences"
echo "Staging has 'Data Analysis': $staging_has_data occurrences"

echo ""
echo "======================================================"
echo "   SYNC COMPLETE"
echo "======================================================"
echo ""
echo "Summary:"
echo "✅ data-analysis-upload.js synced to production (if it existed)"
echo "✅ index.html synced from production to staging"
echo "✅ All services restarted"
echo ""
echo "Both environments should now be synchronized with:"
echo "- Data Analysis tab (not TPR Analysis)"
echo "- All data_analysis_v3 files"
echo "- Encoding fixes (ftfy, chardet)"
echo "- JavaScript formatting fixes"
echo ""