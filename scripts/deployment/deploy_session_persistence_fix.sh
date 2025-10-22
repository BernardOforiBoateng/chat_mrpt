#!/bin/bash
# Deploy session persistence fix for TPR workflow
# This fixes: session persistence, geometry preservation, and download links

echo "===== Deploying Session Persistence Fix ====="
echo "This deployment fixes:"
echo "1. Session persistence across TPR workflow"
echo "2. Geometry preservation in output files"
echo "3. Download links availability"
echo "4. Risk analysis transition after TPR"

# Configuration
SERVER="ubuntu@3.137.158.17"
KEY_PATH="aws_files/chatmrpt_kp.pem"
REMOTE_DIR="/home/ubuntu/ChatMRPT"

echo -e "\n=== Creating deployment package ==="

# Create temporary directory for deployment
TEMP_DIR=$(mktemp -d)
echo "Using temp directory: $TEMP_DIR"

# Copy the new and updated files
echo "Copying updated files..."
mkdir -p $TEMP_DIR/app/core
mkdir -p $TEMP_DIR/app/tpr_module/integration
mkdir -p $TEMP_DIR/app/tpr_module/output
mkdir -p $TEMP_DIR/app/web/routes

# Core files
cp app/core/file_session_store.py $TEMP_DIR/app/core/
cp app/core/request_interpreter.py $TEMP_DIR/app/core/

# TPR module files
cp app/tpr_module/integration/tpr_handler.py $TEMP_DIR/app/tpr_module/integration/
cp app/tpr_module/output/output_generator.py $TEMP_DIR/app/tpr_module/output/

# Routes
cp app/web/routes/tpr_routes.py $TEMP_DIR/app/web/routes/

# Create deployment info
cat > $TEMP_DIR/deployment_info.txt << EOF
Session Persistence Fix Deployment
Date: $(date)
Files updated:
- app/core/file_session_store.py (NEW)
- app/core/request_interpreter.py
- app/tpr_module/integration/tpr_handler.py
- app/tpr_module/output/output_generator.py
- app/web/routes/tpr_routes.py
EOF

echo -e "\n=== Deploying to AWS ==="
echo "Server: $SERVER"

# Deploy files
echo "Uploading files..."
scp -i "$KEY_PATH" -r $TEMP_DIR/* "$SERVER:$REMOTE_DIR/"

# Create session directory and restart application
echo -e "\n=== Setting up on server ==="
ssh -i "$KEY_PATH" "$SERVER" << 'ENDSSH'
cd /home/ubuntu/ChatMRPT

# Create session directory for file-based sessions
echo "Creating session directory..."
sudo mkdir -p /tmp/chatmrpt_sessions
sudo chmod 777 /tmp/chatmrpt_sessions

# Also create in instance folder as backup
mkdir -p instance/sessions
chmod 755 instance/sessions

# Verify files were copied
echo -e "\nVerifying deployment..."
if [ -f "app/core/file_session_store.py" ]; then
    echo "✓ file_session_store.py deployed"
else
    echo "✗ file_session_store.py missing!"
fi

# Check Python syntax
echo -e "\nChecking Python syntax..."
python3 -m py_compile app/core/file_session_store.py
python3 -m py_compile app/core/request_interpreter.py
python3 -m py_compile app/tpr_module/integration/tpr_handler.py
python3 -m py_compile app/tpr_module/output/output_generator.py
python3 -m py_compile app/web/routes/tpr_routes.py

# Restart the application
echo -e "\nRestarting application..."
sudo systemctl restart chatmrpt

# Wait for restart
sleep 5

# Check status
echo -e "\nChecking application status..."
sudo systemctl status chatmrpt | head -20

# Check for errors in logs
echo -e "\nRecent log entries:"
sudo journalctl -u chatmrpt -n 50 --no-pager | grep -E "(ERROR|CRITICAL|Started)" | tail -20

echo -e "\n=== Deployment complete ==="
echo "Test the following:"
echo "1. Upload TPR file and complete analysis"
echo "2. Verify all wards show on map (no green areas)"
echo "3. Say 'yes' to proceed to risk analysis"
echo "4. Check download tab has files available"
ENDSSH

# Cleanup
rm -rf $TEMP_DIR

echo -e "\n===== Session Persistence Fix Deployed Successfully ====="
echo "Please test at: http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com"
echo ""
echo "Testing checklist:"
echo "□ Upload NMEP TPR Excel file"
echo "□ Complete TPR analysis for a state"
echo "□ Verify map shows all wards (no green areas)"
echo "□ Respond 'yes' when asked about risk analysis"
echo "□ Confirm transition to risk analysis"
echo "□ Check download tab for generated files"
echo "□ Test page refresh maintains session state"