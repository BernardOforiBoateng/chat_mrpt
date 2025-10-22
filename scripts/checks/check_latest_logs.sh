#\!/bin/bash

echo "=========================================="
echo "CHECKING LATEST LOGS WITH FILE PATHS"
echo "=========================================="

KEY_PATH="/tmp/chatmrpt-key2.pem"
cp aws_files/chatmrpt-key.pem $KEY_PATH
chmod 600 $KEY_PATH

# Check instance 1
echo "📋 Instance 1 (3.21.167.170) - Last 30 analysis logs:"
ssh -o StrictHostKeyChecking=no -i $KEY_PATH ec2-user@3.21.167.170 \
    "sudo journalctl -u chatmrpt --since '5 minutes ago' | grep -E 'Preliminary EDA|Starting analysis|File not found|data_analysis' | tail -30"

echo ""
echo "📋 Instance 2 (18.220.103.20) - Last 30 analysis logs:"
ssh -o StrictHostKeyChecking=no -i $KEY_PATH ec2-user@18.220.103.20 \
    "sudo journalctl -u chatmrpt --since '5 minutes ago' | grep -E 'Preliminary EDA|Starting analysis|File not found|data_analysis' | tail -30"

rm -f $KEY_PATH
