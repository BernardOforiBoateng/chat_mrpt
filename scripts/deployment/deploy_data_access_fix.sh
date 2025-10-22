#!/bin/bash

echo "🚀 Deploying Data Access fixes to staging..."
echo "This fixes the fundamental issue where tools don't receive actual data"

# Copy SSH key
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

# Files to deploy
FILES="app/data_analysis_v3/core/agent.py \
       app/data_analysis_v3/tools/python_tool.py"

# Deploy to both staging instances
for ip in 3.21.167.170 18.220.103.20; do
    echo ""
    echo "📦 Deploying to staging instance: $ip"
    
    # Copy files
    for file in $FILES; do
        echo "  Copying $file..."
        scp -i /tmp/chatmrpt-key2.pem "$file" "ec2-user@$ip:/home/ec2-user/ChatMRPT/$file"
    done
    
    # Restart service
    echo "  Restarting service..."
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$ip "sudo systemctl restart chatmrpt"
    
    # Wait for service to start
    sleep 5
    
    # Check status
    echo "  Checking service status..."
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$ip "sudo systemctl status chatmrpt | grep 'Active:' | head -1"
    
    echo "✅ Deployed to $ip"
done

echo ""
echo "✅ Data Access fixes deployed to staging!"
echo ""
echo "📝 Test with:"
echo "1. Upload adamawa_tpr_cleaned.csv"
echo "2. Try queries like:"
echo "   - 'Show me the top 10 facilities by total testing volume'"
echo "   - 'Which LGA has the highest number of tests performed?'"
echo "   - 'Calculate positivity rate for adults ≥5 years'"
echo ""
echo "The agent should now return REAL facility names and data, not 'Facility A, B, C'!"
echo ""
echo "URL: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo "Direct: http://3.21.167.170:8080"