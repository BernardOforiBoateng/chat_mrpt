#!/bin/bash

echo "🚀 Deploying Flask session synchronization fix to staging servers..."

# Copy key to temp location
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

# Staging servers (NEW IPs as of Jan 7, 2025)
STAGING_SERVERS=("3.21.167.170" "18.220.103.20")

for SERVER in "${STAGING_SERVERS[@]}"; do
    echo ""
    echo "📦 Deploying to staging server: $SERVER"
    
    # Copy the fixed request_interpreter.py
    echo "   📄 Copying fixed request_interpreter.py..."
    scp -i /tmp/chatmrpt-key2.pem app/core/request_interpreter.py ec2-user@$SERVER:/home/ec2-user/ChatMRPT/app/core/
    
    # Restart the service
    echo "   🔄 Restarting ChatMRPT service..."
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$SERVER 'sudo systemctl restart chatmrpt'
    
    # Check service status
    echo "   ✅ Checking service status..."
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$SERVER 'sudo systemctl status chatmrpt | grep "Active:"'
    
    echo "   ✅ Deployment to $SERVER complete!"
done

echo ""
echo "🎉 Session synchronization fix deployed to all staging servers!"
echo ""
echo "The fix addresses:"
echo "1. ✅ Missing os import in workflow transition check"
echo "2. ✅ Flask session flags (csv_loaded, shapefile_loaded) now sync after V3 transition"
echo "3. ✅ Immediate session flag update when agent state is trusted"
echo ""
echo "Expected behavior after fix:"
echo "- Tools will execute properly after TPR workflow completion"
echo "- No more Python code descriptions instead of actual tool execution"
echo "- Session state will be consistent across all workers"
echo ""
echo "Test the fix at: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"