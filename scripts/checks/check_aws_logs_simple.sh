#\!/bin/bash

echo "=========================================="
echo "CHECKING AWS LOGS"
echo "=========================================="

KEY_PATH="/tmp/chatmrpt-key2.pem"
cp aws_files/chatmrpt-key.pem $KEY_PATH
chmod 600 $KEY_PATH

# Check instance 1
echo "📋 Instance 1 (3.21.167.170):"
ssh -o StrictHostKeyChecking=no -i $KEY_PATH ec2-user@3.21.167.170 \
    "sudo journalctl -u chatmrpt --since '30 minutes ago' | grep -E 'data.analysis|ERROR' | tail -20"

echo ""
echo "📋 Instance 2 (18.220.103.20):"
ssh -o StrictHostKeyChecking=no -i $KEY_PATH ec2-user@18.220.103.20 \
    "sudo journalctl -u chatmrpt --since '30 minutes ago' | grep -E 'data.analysis|ERROR' | tail -20"

rm -f $KEY_PATH
