#\!/bin/bash

echo "=========================================="
echo "CHECKING FILE PATH LOGS"
echo "=========================================="

KEY_PATH="/tmp/chatmrpt-key2.pem"
cp aws_files/chatmrpt-key.pem $KEY_PATH
chmod 600 $KEY_PATH

# Check both instances
echo "📋 Instance 1 (3.21.167.170) - File path logs:"
ssh -o StrictHostKeyChecking=no -i $KEY_PATH ec2-user@3.21.167.170 \
    "sudo journalctl -u chatmrpt --since '2 minutes ago' | grep -E 'Preliminary EDA|Starting analysis|_load_all_data|Resolved absolute|File extension' | tail -30"

echo ""
echo "📋 Instance 2 (18.220.103.20) - File path logs:"
ssh -o StrictHostKeyChecking=no -i $KEY_PATH ec2-user@18.220.103.20 \
    "sudo journalctl -u chatmrpt --since '2 minutes ago' | grep -E 'Preliminary EDA|Starting analysis|_load_all_data|Resolved absolute|File extension' | tail -30"

rm -f $KEY_PATH
