#!/bin/bash

# Deploy risk analysis workflow fix to staging and production
# Fixes ITN planning tool not recognizing completed analysis

echo "=========================================="
echo "DEPLOYING RISK ANALYSIS WORKFLOW FIX"
echo "=========================================="
echo ""

# Files to deploy
FILES_TO_DEPLOY=(
    "app/tools/itn_planning_tools.py"
    "app/core/unified_data_state.py"
    "app/tools/complete_analysis_tools.py"
    "app/core/request_interpreter.py"
)

# Staging instances
STAGING_IPS=("3.21.167.170" "18.220.103.20")

# Production instances (private IPs, accessed via staging)
PROD_IPS=("172.31.44.52" "172.31.43.200")

KEY_PATH="/tmp/chatmrpt-key2.pem"

# Ensure key is available
if [ ! -f "$KEY_PATH" ]; then
    cp aws_files/chatmrpt-key.pem $KEY_PATH
    chmod 600 $KEY_PATH
    echo "✅ SSH key prepared"
fi

# Function to deploy to an instance
deploy_to_instance() {
    local ip=$1
    local instance_name=$2
    
    echo "📦 Deploying to $instance_name ($ip)..."
    
    # Copy files
    for file in "${FILES_TO_DEPLOY[@]}"; do
        echo "   Copying $file..."
        scp -i $KEY_PATH "$file" ec2-user@$ip:/home/ec2-user/ChatMRPT/$file
    done
    
    # Restart service
    ssh -i $KEY_PATH ec2-user@$ip 'sudo systemctl restart chatmrpt'
    echo "   ✅ Service restarted"
}

# Deploy to staging
echo "🚀 STEP 1: Deploying to Staging Environment"
echo "============================================"

for i in "${!STAGING_IPS[@]}"; do
    ip="${STAGING_IPS[$i]}"
    instance_num=$((i + 1))
    deploy_to_instance "$ip" "Staging Instance $instance_num"
done

echo ""
echo "✅ Staging deployment complete!"
echo ""

# Test on staging
echo "🧪 STEP 2: Testing on Staging"
echo "=============================="

# Quick health check
echo "Testing staging ALB health..."
STAGING_ALB="http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
if curl -s -o /dev/null -w "%{http_code}" "$STAGING_ALB/ping" | grep -q "200"; then
    echo "✅ Staging ALB responding normally"
else
    echo "⚠️ Staging ALB health check failed"
fi

echo ""
read -p "Deploy to production? (y/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Production deployment cancelled"
    exit 0
fi

# Deploy to production through staging
echo ""
echo "🚀 STEP 3: Deploying to Production Environment"
echo "=============================================="

# First, copy files to staging instance for relay
echo "Preparing files on staging for production relay..."
STAGING_RELAY="${STAGING_IPS[0]}"

# Copy key to staging for production access
scp -i $KEY_PATH aws_files/chatmrpt-key.pem ec2-user@$STAGING_RELAY:~/.ssh/
ssh -i $KEY_PATH ec2-user@$STAGING_RELAY 'chmod 600 ~/.ssh/chatmrpt-key.pem'

# Deploy to each production instance via staging
for i in "${!PROD_IPS[@]}"; do
    prod_ip="${PROD_IPS[$i]}"
    instance_num=$((i + 1))
    echo "📦 Deploying to Production Instance $instance_num ($prod_ip)..."
    
    # Copy files from staging to production
    for file in "${FILES_TO_DEPLOY[@]}"; do
        echo "   Copying $file..."
        ssh -i $KEY_PATH ec2-user@$STAGING_RELAY \
            "scp -i ~/.ssh/chatmrpt-key.pem /home/ec2-user/ChatMRPT/$file ec2-user@$prod_ip:/home/ec2-user/ChatMRPT/$file"
    done
    
    # Restart production service
    ssh -i $KEY_PATH ec2-user@$STAGING_RELAY \
        "ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$prod_ip 'sudo systemctl restart chatmrpt'"
    echo "   ✅ Production Instance $instance_num restarted"
done

echo ""
echo "✅ Production deployment complete!"
echo ""

# Test production
echo "🧪 STEP 4: Testing Production"
echo "============================="

# Check CloudFront
echo "Testing CloudFront CDN..."
if curl -s -o /dev/null -w "%{http_code}" "https://d225ar6c86586s.cloudfront.net/ping" | grep -q "200"; then
    echo "✅ CloudFront CDN responding normally"
else
    echo "⚠️ CloudFront health check failed"
fi

# Check ALB
echo "Testing Production ALB..."
if curl -s -o /dev/null -w "%{http_code}" "http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com/ping" | grep -q "200"; then
    echo "✅ Production ALB responding normally"
else
    echo "⚠️ Production ALB health check failed"
fi

echo ""
echo "=========================================="
echo "DEPLOYMENT COMPLETE"
echo "=========================================="
echo ""
echo "📊 Summary:"
echo "✅ Deployed to ${#STAGING_IPS[@]} staging instances"
echo "✅ Deployed to ${#PROD_IPS[@]} production instances"
echo ""
echo "🔧 Fixed Issues:"
echo "1. ITN tool now checks for .analysis_complete marker first"
echo "2. Direct file checks prioritized over session state"
echo "3. UnifiedDataState enhanced with better detection"
echo "4. Session state recovery for cross-worker reliability"
echo "5. Analysis completion marker file created automatically"
echo ""
echo "📝 Next Steps:"
echo "1. Run ./fix_redis_connectivity.sh to fix Redis issues"
echo "2. Test ITN planning after risk analysis"
echo "3. Monitor logs for any errors"