#!/bin/bash

# Deploy TPR Dynamic Environmental Extraction and Report Generation fixes to AWS

echo "=== Deploying TPR Dynamic Environmental Extraction and Report Generation to AWS ==="

# Server details
SERVER="ec2-user@3.137.158.17"
KEY="/tmp/chatmrpt-key2.pem"
REMOTE_APP_DIR="/home/ec2-user/ChatMRPT"

# Files to copy
echo "1. Copying updated TPR files to AWS..."

# Copy the updated files
scp -i $KEY app/tpr_module/services/raster_extractor.py $SERVER:$REMOTE_APP_DIR/app/tpr_module/services/
scp -i $KEY app/tpr_module/output/output_generator.py $SERVER:$REMOTE_APP_DIR/app/tpr_module/output/
scp -i $KEY app/tpr_module/output/tpr_report_generator.py $SERVER:$REMOTE_APP_DIR/app/tpr_module/output/

echo "2. Restarting Gunicorn to apply changes..."
ssh -i $KEY $SERVER "sudo systemctl restart gunicorn"

echo "3. Checking service status..."
ssh -i $KEY $SERVER "sudo systemctl status gunicorn | head -n 10"

echo ""
echo "Deployment complete! TPR improvements deployed:"
echo "- Dynamic environmental data extraction (averages all available data)"
echo "- Comprehensive HTML analysis reports with embedded maps"
echo "- Fixed set.append() bug"
echo ""
echo "Test the TPR workflow at: http://3.137.158.17"