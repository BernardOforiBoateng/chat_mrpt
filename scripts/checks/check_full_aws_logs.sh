#\!/bin/bash

echo "=========================================="
echo "CHECKING FULL AWS LOGS FOR DATA ANALYSIS"
echo "=========================================="

KEY_PATH="/tmp/chatmrpt-key2.pem"
cp aws_files/chatmrpt-key.pem $KEY_PATH
chmod 600 $KEY_PATH

# Check instance 1 for ALL recent logs
echo "📋 Instance 1 (3.21.167.170) - ALL recent logs:"
echo "----------------------------------------"
ssh -o StrictHostKeyChecking=no -i $KEY_PATH ec2-user@3.21.167.170 \
    "sudo journalctl -u chatmrpt --since '5 minutes ago' | grep -v 'INFO in app' | grep -E 'data_analysis|preliminary|executor|ERROR|Starting analysis|File' | tail -50"

echo ""
echo "📋 Instance 2 (18.220.103.20) - ALL recent logs:"
echo "----------------------------------------"
ssh -o StrictHostKeyChecking=no -i $KEY_PATH ec2-user@18.220.103.20 \
    "sudo journalctl -u chatmrpt --since '5 minutes ago' | grep -v 'INFO in app' | grep -E 'data_analysis|preliminary|executor|ERROR|Starting analysis|File' | tail -50"

echo ""
echo "📋 Checking if LLM is configured on Instance 1:"
ssh -o StrictHostKeyChecking=no -i $KEY_PATH ec2-user@3.21.167.170 \
    "grep -i 'llm_manager' /home/ec2-user/ChatMRPT/app/services/container.py | head -5"

rm -f $KEY_PATH
