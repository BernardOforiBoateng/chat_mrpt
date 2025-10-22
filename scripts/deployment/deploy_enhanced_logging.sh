#!/bin/bash
echo "🔍 DEPLOYING ENHANCED DEBUG LOGGING"
echo "===================================="
echo ""

STAGING_IPS=("3.21.167.170" "18.220.103.20")
KEY_PATH="/tmp/chatmrpt-key.pem"

for ip in "${STAGING_IPS[@]}"; do
    echo "📍 Deploying to $ip..."
    
    # Deploy updated request_interpreter
    scp -i $KEY_PATH -o StrictHostKeyChecking=no \
        app/core/request_interpreter.py \
        ec2-user@$ip:/home/ec2-user/ChatMRPT/app/core/
    
    # Clear Python cache and restart
    ssh -i $KEY_PATH -o StrictHostKeyChecking=no ec2-user@$ip \
        "cd /home/ec2-user/ChatMRPT && find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true && sudo systemctl restart chatmrpt"
    
    echo "  ✅ Done"
done

echo ""
echo "🎉 DEPLOYED! Now test and check logs with:"
echo "ssh -i $KEY_PATH ec2-user@3.21.167.170 'sudo journalctl -u chatmrpt -f | grep -E \"🔍|✅|❌|🔧|📊|📦|🛠️|📝|🎯|📋\"'"
