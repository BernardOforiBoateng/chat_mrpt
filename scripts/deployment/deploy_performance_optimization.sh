#!/bin/bash

echo "======================================"
echo "Deploying Performance Optimizations to AWS Staging"
echo "======================================"

# AWS staging IPs (updated)
STAGING_IPS="3.21.167.170 18.220.103.20"

# Files to deploy
FILES_TO_DEPLOY="
app/data_analysis_v3/core/metadata_cache.py
app/data_analysis_v3/core/lazy_loader.py
app/data_analysis_v3/tools/python_tool.py
app/web/routes/data_analysis_v3_routes.py
test_metadata_cache.py
"

echo "Files to deploy:"
echo "$FILES_TO_DEPLOY"
echo ""

# Copy key to temp location with proper permissions
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key.pem
chmod 600 /tmp/chatmrpt-key.pem

# Deploy to each staging instance
for IP in $STAGING_IPS; do
    echo "======================================"
    echo "Deploying to staging instance: $IP"
    echo "======================================"
    
    # Copy files
    for FILE in $FILES_TO_DEPLOY; do
        echo "Copying $FILE..."
        scp -i /tmp/chatmrpt-key.pem -o StrictHostKeyChecking=no \
            "$FILE" "ec2-user@$IP:/home/ec2-user/ChatMRPT/$FILE"
    done
    
    # Install openpyxl if needed (for Excel row counting)
    echo "Installing openpyxl dependency..."
    ssh -i /tmp/chatmrpt-key.pem -o StrictHostKeyChecking=no "ec2-user@$IP" \
        "cd /home/ec2-user/ChatMRPT && source /home/ec2-user/chatmrpt_env/bin/activate && pip install openpyxl"
    
    # Restart the service
    echo "Restarting ChatMRPT service..."
    ssh -i /tmp/chatmrpt-key.pem -o StrictHostKeyChecking=no "ec2-user@$IP" \
        "sudo systemctl restart chatmrpt"
    
    echo "Deployment to $IP complete!"
    echo ""
done

echo "======================================"
echo "Performance optimizations deployed to all staging instances!"
echo "======================================"
echo ""
echo "Test the improvements at:"
echo "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo ""
echo "To test metadata caching on staging:"
echo "ssh -i /tmp/chatmrpt-key.pem ec2-user@3.21.167.170"
echo "cd ChatMRPT && source /home/ec2-user/chatmrpt_env/bin/activate"
echo "python test_metadata_cache.py"