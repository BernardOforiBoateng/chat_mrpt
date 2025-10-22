#!/bin/bash
echo "🚀 Deploying CRITICAL workflow transition fix"
echo "This fix is ALREADY in your local code - just needs deployment!"
echo ""

STAGING_IPS=("3.21.167.170" "18.220.103.20")
KEY_PATH="/tmp/chatmrpt-key.pem"

for ip in "${STAGING_IPS[@]}"; do
    echo "📦 Deploying to $ip..."
    scp -i $KEY_PATH app/core/request_interpreter.py ec2-user@$ip:/home/ec2-user/ChatMRPT/app/core/request_interpreter.py
    ssh -i $KEY_PATH ec2-user@$ip "sudo systemctl restart chatmrpt"
    echo "✅ Done with $ip"
done

echo ""
echo "🎉 Critical fix deployed! The workflow transition check now runs for ALL sessions."
