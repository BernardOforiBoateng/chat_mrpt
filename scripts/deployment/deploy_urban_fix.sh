#!/bin/bash

# Deploy urban percentage fix to both production instances

echo "==========================================="
echo "Deploying Urban Percentage Fix"
echo "==========================================="

# Copy SSH key
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

# Production instances (formerly staging)
INSTANCES=("3.21.167.170" "18.220.103.20")

for IP in "${INSTANCES[@]}"; do
    echo ""
    echo "📍 Deploying to Instance: $IP"
    echo "-----------------------------------"
    
    # 1. Copy the fixed TPR analysis tool
    echo "1. Copying fixed TPR analysis tool..."
    scp -i /tmp/chatmrpt-key2.pem \
        app/data_analysis_v3/tools/tpr_analysis_tool.py \
        ec2-user@$IP:/home/ec2-user/ChatMRPT/app/data_analysis_v3/tools/
    
    # 2. Install libpysal for spatial imputation
    echo "2. Installing libpysal module..."
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$IP << 'EOF'
        cd /home/ec2-user/ChatMRPT
        source chatmrpt_venv/bin/activate
        pip install libpysal
        echo "libpysal installed successfully"
EOF
    
    # 3. Verify the fix was applied
    echo "3. Verifying urban_extent in zone variables..."
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$IP << 'EOF'
        grep -A 1 "North-East.*urban_extent" /home/ec2-user/ChatMRPT/app/data_analysis_v3/tools/tpr_analysis_tool.py
        if [ $? -eq 0 ]; then
            echo "✅ Urban extent fix verified"
        else
            echo "❌ Urban extent fix NOT found"
        fi
EOF
    
    # 4. Restart the service
    echo "4. Restarting ChatMRPT service..."
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$IP "sudo systemctl restart chatmrpt"
    
    # 5. Check service status
    echo "5. Checking service status..."
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$IP "sudo systemctl status chatmrpt | grep Active"
    
    echo "✅ Deployment complete for $IP"
done

echo ""
echo "==========================================="
echo "Urban Percentage Fix Deployment Complete"
echo "==========================================="
echo ""
echo "Summary of changes:"
echo "1. Added 'urban_extent' to all geopolitical zones"
echo "2. Fixed urban percentage extraction and column naming"
echo "3. Installed libpysal for spatial imputation"
echo "4. Ensured urban_percentage column is always available"
echo ""
echo "Test the fix by:"
echo "1. Running TPR analysis for any state"
echo "2. Proceeding to risk analysis"
echo "3. Testing ITN distribution with urban threshold"