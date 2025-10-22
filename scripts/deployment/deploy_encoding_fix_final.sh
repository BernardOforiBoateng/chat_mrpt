#!/bin/bash

echo "🚀 Deploying Final Encoding Fix to Staging"
echo "========================================="

# Files to deploy
FILES="app/data_analysis_v3/core/encoding_handler.py app/data_analysis_v3/core/tpr_workflow_handler.py"

# Staging IPs
STAGING_IPS="3.21.167.170 18.220.103.20"

for ip in $STAGING_IPS; do
    echo ""
    echo "📦 Deploying to $ip..."
    
    # Copy files
    for file in $FILES; do
        echo "  - Copying $file"
        scp -i /tmp/chatmrpt-key2.pem "$file" "ec2-user@$ip:~/ChatMRPT/$file"
    done
    
    # Restart service
    echo "  - Restarting service..."
    ssh -i /tmp/chatmrpt-key2.pem "ec2-user@$ip" 'sudo systemctl restart chatmrpt'
    
    echo "  ✅ Deployed to $ip"
done

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🧪 Testing deployment..."
sleep 5

# Test health
curl -s "http://3.21.167.170:8080/ping" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Instance 1 is healthy"
else
    echo "❌ Instance 1 health check failed"
fi

curl -s "http://18.220.103.20:8080/ping" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Instance 2 is healthy"
else
    echo "❌ Instance 2 health check failed"
fi

echo ""
echo "🎉 Encoding fix deployed successfully!"
echo "Test at: http://3.21.167.170:8080"