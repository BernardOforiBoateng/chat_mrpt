#\!/bin/bash

echo "=========================================="
echo "CHECKING DATA ANALYSIS RESPONSE IN AWS"
echo "=========================================="

KEY_PATH="/tmp/chatmrpt-key2.pem"
cp aws_files/chatmrpt-key.pem $KEY_PATH
chmod 600 $KEY_PATH

# Check both instances for recent data analysis activity
echo "📋 Instance 1 (3.21.167.170) - Last 50 lines with 'preliminary-eda':"
ssh -o StrictHostKeyChecking=no -i $KEY_PATH ec2-user@3.21.167.170 \
    "sudo journalctl -u chatmrpt --since '1 hour ago' | grep -A 5 -B 5 'preliminary-eda' | tail -50"

echo ""
echo "📋 Instance 2 (18.220.103.20) - Last 50 lines with 'preliminary-eda':"
ssh -o StrictHostKeyChecking=no -i $KEY_PATH ec2-user@18.220.103.20 \
    "sudo journalctl -u chatmrpt --since '1 hour ago' | grep -A 5 -B 5 'preliminary-eda' | tail -50"

rm -f $KEY_PATH
