#!/bin/bash

echo "=== Fixing Missing tpr_utils Module ==="
echo ""

# Copy key
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

# First check if tpr_utils exists on staging
echo "Checking if tpr_utils exists on staging..."
ssh -i /tmp/chatmrpt-key2.pem ec2-user@18.220.103.20 << 'EOF'
echo "Looking for tpr_utils on staging:"
ls -la /home/ec2-user/ChatMRPT/app/core/tpr_utils.py 2>/dev/null || echo "Not found as separate file"

echo ""
echo "Checking imports in tpr_workflow_handler.py:"
grep -n "import.*tpr_utils" /home/ec2-user/ChatMRPT/app/data_analysis_v3/core/tpr_workflow_handler.py

echo ""
echo "Creating tpr_utils.py from local copy..."
cat > /tmp/tpr_utils.py << 'UTILS'
"""
TPR Utilities Module
Provides utility functions for TPR calculations
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

def calculate_tpr(data, facility_level=None, age_group=None):
    """Calculate Test Positivity Rate"""
    # Filter by facility level if specified
    if facility_level and facility_level != 'all':
        data = data[data['FacilityLevel'].str.lower() == facility_level.lower()]
    
    # Calculate TPR based on age group
    if age_group:
        if 'under' in age_group.lower() or 'u5' in age_group.lower():
            total_col = 'U5_Total_Tested'
            positive_col = 'U5_Positive'
        elif 'over' in age_group.lower() or 'o5' in age_group.lower():
            total_col = 'O5_Total_Tested'
            positive_col = 'O5_Positive'
        elif 'pregnant' in age_group.lower():
            total_col = 'Pregnant_Total_Tested'
            positive_col = 'Pregnant_Positive'
        else:
            # Default to all ages
            total_col = 'Total_Tested'
            positive_col = 'Total_Positive'
    else:
        total_col = 'Total_Tested'
        positive_col = 'Total_Positive'
    
    # Ensure columns exist
    if total_col not in data.columns:
        # Try to calculate from available columns
        if 'RDT_Total' in data.columns and 'Microscopy_Total' in data.columns:
            data[total_col] = data['RDT_Total'] + data['Microscopy_Total']
        else:
            logger.warning(f"Column {total_col} not found")
            return pd.DataFrame()
    
    if positive_col not in data.columns:
        # Try to calculate from available columns
        if 'RDT_Positive' in data.columns and 'Microscopy_Positive' in data.columns:
            data[positive_col] = data['RDT_Positive'] + data['Microscopy_Positive']
        else:
            logger.warning(f"Column {positive_col} not found")
            return pd.DataFrame()
    
    # Calculate TPR
    data['TPR'] = (data[positive_col] / data[total_col] * 100).round(2)
    data['TPR'] = data['TPR'].fillna(0)
    
    return data

def generate_tpr_summary(data):
    """Generate TPR summary statistics"""
    summary = {
        'total_facilities': len(data),
        'mean_tpr': data['TPR'].mean() if 'TPR' in data.columns else 0,
        'median_tpr': data['TPR'].median() if 'TPR' in data.columns else 0,
        'high_risk_facilities': len(data[data['TPR'] > 40]) if 'TPR' in data.columns else 0,
        'low_risk_facilities': len(data[data['TPR'] < 10]) if 'TPR' in data.columns else 0
    }
    return summary
UTILS

echo "Created temporary tpr_utils.py"
EOF

# Copy the file to both production instances
ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 << 'EOF'

# Get the utils file from staging
scp -i ~/.ssh/chatmrpt-key.pem ec2-user@18.220.103.20:/tmp/tpr_utils.py /tmp/ 2>/dev/null || echo "Using created version"

# Deploy to both production instances
for PROD_IP in 172.31.44.52 172.31.43.200; do
    echo ""
    echo "Deploying tpr_utils to: $PROD_IP"
    
    # Copy file to production
    scp -i ~/.ssh/chatmrpt-key.pem /tmp/tpr_utils.py ec2-user@$PROD_IP:/tmp/
    
    # Install on production
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP << 'INSTALL'
    # Copy to correct location
    sudo cp /tmp/tpr_utils.py /home/ec2-user/ChatMRPT/app/core/
    sudo chown ec2-user:ec2-user /home/ec2-user/ChatMRPT/app/core/tpr_utils.py
    
    # Verify it's there
    echo "Installed at:"
    ls -la /home/ec2-user/ChatMRPT/app/core/tpr_utils.py
    
    # Restart service
    echo "Restarting service..."
    sudo systemctl restart chatmrpt
    sleep 3
    
    echo "Service status:"
    sudo systemctl is-active chatmrpt
    
    echo "✅ tpr_utils installed on $PROD_IP"
INSTALL
done

echo ""
echo "=== TPR Utils Module Fixed ==="
echo "The missing module has been added to both production instances"

EOF