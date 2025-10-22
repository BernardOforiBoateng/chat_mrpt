#!/bin/bash
# Deploy Data Analysis V3 fixes to staging
# Updated: Aug 12, 2025

set -e

echo "========================================="
echo "   Deploying Data Analysis V3 Fixes     "
echo "========================================="
echo ""

# Staging instances (using public IPs as per CLAUDE.md)
STAGING_IPS=(
    "3.21.167.170"    # Instance 1 (updated Jan 7, 2025)
    "18.220.103.20"   # Instance 2
)

KEY_PATH="/tmp/chatmrpt-key.pem"
APP_DIR="/home/ec2-user/ChatMRPT"

# Copy key to /tmp for proper permissions
echo "Setting up SSH key..."
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key.pem
chmod 600 /tmp/chatmrpt-key.pem

# Files to deploy (Data Analysis V3 fixes)
echo "Preparing files to deploy..."
FILES=(
    "app/data_analysis_v3/core/agent.py"
    "app/data_analysis_v3/core/column_validator.py"
    "app/data_analysis_v3/core/executor.py"
    "app/data_analysis_v3/prompts/system_prompt.py"
)

# Deploy to each staging instance
for ip in "${STAGING_IPS[@]}"; do
    echo ""
    echo "Deploying to $ip..."
    echo "----------------------------------------"
    
    # Test connection
    echo "Testing connection..."
    if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -i $KEY_PATH ec2-user@$ip "echo 'Connected to $ip'" 2>/dev/null; then
        echo "✓ Connected successfully"
    else
        echo "✗ Cannot connect to $ip - skipping"
        continue
    fi
    
    # Create directories if needed
    echo "Ensuring directory structure..."
    ssh -i $KEY_PATH ec2-user@$ip "mkdir -p $APP_DIR/app/data_analysis_v3/core $APP_DIR/app/data_analysis_v3/prompts"
    
    # Copy files
    echo "Copying files..."
    for file in "${FILES[@]}"; do
        echo "  - Copying $file"
        scp -i $KEY_PATH "$file" ec2-user@$ip:$APP_DIR/$file
    done
    
    # Restart service
    echo "Restarting service..."
    ssh -i $KEY_PATH ec2-user@$ip "sudo systemctl restart chatmrpt"
    
    # Wait for service to start
    sleep 5
    
    # Check service status
    echo "Checking service status..."
    if ssh -i $KEY_PATH ec2-user@$ip "sudo systemctl is-active chatmrpt" 2>/dev/null; then
        echo "✓ Service is running on $ip"
        
        # Check application health
        if ssh -i $KEY_PATH ec2-user@$ip "curl -s http://localhost:8080/ping | grep -q pong" 2>/dev/null; then
            echo "✓ Application is responding on $ip"
        else
            echo "⚠ Application may not be fully started on $ip"
        fi
    else
        echo "✗ Service failed to start on $ip"
        echo "Checking logs..."
        ssh -i $KEY_PATH ec2-user@$ip "sudo journalctl -u chatmrpt -n 20"
    fi
    
    echo "✓ Deployment to $ip completed"
done

echo ""
echo "========================================="
echo "         Deployment Complete             "
echo "========================================="
echo ""
echo "Testing staging ALB endpoint..."
if curl -s -m 5 http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com/ping | grep -q pong 2>/dev/null; then
    echo "✓ Staging ALB is responding"
    echo ""
    echo "Staging URL: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
    echo ""
    echo "You can now test the Data Analysis V3 fixes:"
    echo "1. Upload TPR data (Excel/CSV)"
    echo "2. Choose 'Calculate TPR' option"
    echo "3. Verify column names are handled correctly"
    echo "4. Check that map visualization works"
else
    echo "⚠ ALB may need time to detect healthy targets"
    echo "Wait a minute and try accessing:"
    echo "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
fi

echo ""
echo "Deployment script completed!"