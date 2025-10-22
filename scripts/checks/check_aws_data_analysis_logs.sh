#\!/bin/bash

echo "=========================================="
echo "CHECKING AWS LOGS FOR DATA ANALYSIS ERRORS"
echo "=========================================="

KEY_PATH="/tmp/chatmrpt-key2.pem"
cp aws_files/chatmrpt-key.pem $KEY_PATH
chmod 600 $KEY_PATH

# Check both staging instances
STAGING_IPS=("3.21.167.170" "18.220.103.20")

for i in "${\!STAGING_IPS[@]}"; do
    IP="${STAGING_IPS[$i]}"
    echo ""
    echo "📋 Instance $((i+1)) ($IP) - Recent logs:"
    echo "----------------------------------------"
    
    ssh -o StrictHostKeyChecking=no -i $KEY_PATH ec2-user@$IP << 'ENDSSH'
echo "=== Recent errors in system logs ==="
sudo journalctl -u chatmrpt --since "30 minutes ago" | grep -E "(ERROR|error|Exception|Failed|failed)" | tail -20

echo ""
echo "=== Data Analysis Module errors ==="
cd /home/ec2-user/ChatMRPT
if [ -f instance/app.log ]; then
    grep -E "(data.analysis|data-analysis|preliminary-eda)" instance/app.log | grep -E "(ERROR|error)" | tail -10
fi

echo ""
echo "=== Recent 500 errors ==="
sudo journalctl -u chatmrpt --since "30 minutes ago" | grep "500 Internal" | tail -5
ENDSSH
done

rm -f $KEY_PATH
echo ""
echo "=========================================="
echo "✅ LOG CHECK COMPLETE"
echo "=========================================="
