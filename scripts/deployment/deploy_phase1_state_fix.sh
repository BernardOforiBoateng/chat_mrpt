#!/bin/bash

# Phase 1 State Management Fix Deployment
# Deploys immediate stabilization fixes for workflow state management

echo "🚀 Deploying Phase 1 State Management Fixes..."
echo "========================================"
echo "Changes:"
echo "1. Fix request_interpreter.py to check workflow context before trusting markers"
echo "2. Add workflow_source and workflow_stage to session state"
echo "3. Clear stale .analysis_complete markers on workflow transitions"
echo "4. Update complete_analysis_tools.py to set workflow_stage"
echo ""

# Files to deploy
FILES=(
    "app/core/request_interpreter.py"
    "app/web/routes/data_analysis_v3_routes.py"
    "app/data_analysis_v3/core/tpr_workflow_handler.py"
    "app/tools/complete_analysis_tools.py"
)

# Check if deploying to staging or production
if [[ "$1" == "production" ]]; then
    echo "📦 Deploying to PRODUCTION (2 instances)..."
    INSTANCES=("172.31.44.52" "172.31.43.200")
    ENVIRONMENT="production"
elif [[ "$1" == "staging" ]]; then
    echo "📦 Deploying to STAGING (2 instances)..."
    # Updated staging IPs as of Jan 7, 2025
    INSTANCES=("3.21.167.170" "18.220.103.20")
    ENVIRONMENT="staging"
else
    echo "❌ Usage: $0 [staging|production]"
    exit 1
fi

# SSH key location
SSH_KEY="/tmp/chatmrpt-key2.pem"
if [ ! -f "$SSH_KEY" ]; then
    # Try to copy from standard location
    if [ -f "aws_files/chatmrpt-key.pem" ]; then
        cp aws_files/chatmrpt-key.pem "$SSH_KEY"
        chmod 600 "$SSH_KEY"
        echo "✅ SSH key prepared"
    else
        echo "❌ SSH key not found at aws_files/chatmrpt-key.pem"
        exit 1
    fi
fi

# Deploy to each instance
for INSTANCE in "${INSTANCES[@]}"; do
    echo ""
    echo "🔄 Deploying to instance: $INSTANCE"
    echo "-----------------------------------"
    
    # Copy files
    for FILE in "${FILES[@]}"; do
        echo "  📄 Copying $FILE..."
        scp -i "$SSH_KEY" -o StrictHostKeyChecking=no \
            "$FILE" "ec2-user@$INSTANCE:/home/ec2-user/ChatMRPT/$FILE"
        
        if [ $? -ne 0 ]; then
            echo "  ❌ Failed to copy $FILE to $INSTANCE"
            exit 1
        fi
    done
    
    echo "  ✅ Files copied successfully"
    
    # Restart the service
    echo "  🔄 Restarting ChatMRPT service..."
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "ec2-user@$INSTANCE" \
        "sudo systemctl restart chatmrpt && echo '  ✅ Service restarted'"
    
    # Check service status
    echo "  📊 Checking service status..."
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "ec2-user@$INSTANCE" \
        "sudo systemctl is-active chatmrpt" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo "  ✅ Service is running on $INSTANCE"
    else
        echo "  ⚠️  Service may not be running properly on $INSTANCE"
    fi
done

echo ""
echo "✅ Phase 1 deployment complete to $ENVIRONMENT!"
echo ""
echo "📋 Testing recommendations:"
echo "1. Upload a file via Data Analysis tab"
echo "2. Complete TPR analysis"
echo "3. Transition to main workflow"
echo "4. Request risk analysis - should NOT say 'already completed'"
echo "5. Complete the risk analysis"
echo "6. Upload new data - should start fresh without stale markers"
echo ""

if [[ "$ENVIRONMENT" == "staging" ]]; then
    echo "🌐 Test at: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
elif [[ "$ENVIRONMENT" == "production" ]]; then
    echo "🌐 Test at: https://d225ar6c86586s.cloudfront.net"
fi