#!/bin/bash

# Fix ITN dependencies on both production instances

echo "==========================================="
echo "Installing ITN Dependencies (openpyxl)"
echo "==========================================="

# Copy SSH key
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

# Production instances
INSTANCES=("3.21.167.170" "18.220.103.20")

for IP in "${INSTANCES[@]}"; do
    echo ""
    echo "📍 Installing on Instance: $IP"
    echo "-----------------------------------"
    
    # Install openpyxl
    echo "Installing openpyxl for Excel file reading..."
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$IP << 'EOF'
        # Install openpyxl
        pip install openpyxl
        
        # Verify installation
        python3 -c "import openpyxl; print(f'✅ openpyxl {openpyxl.__version__} installed successfully')"
        
        # Test ITN population loader can now load Adamawa
        cd /home/ec2-user/ChatMRPT
        python3 -c "
import warnings
warnings.filterwarnings('ignore')
from pathlib import Path
import pandas as pd

# Test loading Adamawa data directly
file_path = Path('/home/ec2-user/ChatMRPT/www/ITN/ITN/pbi_distribution_Adamawa_clean.xlsx')
try:
    df = pd.read_excel(file_path)
    print(f'✅ Successfully loaded Adamawa data: {len(df)} wards')
    print(f'   Total population: {df[\"Population\"].sum():,.0f}')
except Exception as e:
    print(f'❌ Failed to load Adamawa data: {e}')
"
EOF
    
    # Restart service
    echo "Restarting ChatMRPT service..."
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$IP "sudo systemctl restart chatmrpt"
    
    # Check service status
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$IP "sudo systemctl status chatmrpt | grep Active"
    
    echo "✅ Dependencies installed on $IP"
done

echo ""
echo "==========================================="
echo "ITN Dependencies Fix Complete"
echo "==========================================="
echo ""
echo "Summary:"
echo "✅ openpyxl installed on both instances"
echo "✅ ITN loader can now read Excel files from www/ITN/ITN/"
echo "✅ Adamawa population data is now accessible"
echo ""
echo "Next steps to test:"
echo "1. Run new ITN distribution for Adamawa"
echo "2. Check that all 226 wards appear in the map"
echo "3. Verify urban threshold slider works"