#!/bin/bash
echo "🚨 DEPLOYING CRITICAL SESSION FIX"
echo "================================="
echo ""
echo "This fixes: After V3 transition, tools not executing due to session flags"
echo ""

STAGING_IPS=("3.21.167.170" "18.220.103.20")
KEY_PATH="/tmp/chatmrpt-key.pem"

for ip in "${STAGING_IPS[@]}"; do
    echo "📍 Deploying to $ip..."
    
    # Deploy fixed request_interpreter
    scp -i $KEY_PATH -o StrictHostKeyChecking=no \
        app/core/request_interpreter.py \
        ec2-user@$ip:/home/ec2-user/ChatMRPT/app/core/
    
    # Clear cache and restart
    ssh -i $KEY_PATH -o StrictHostKeyChecking=no ec2-user@$ip \
        "cd /home/ec2-user/ChatMRPT && find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true && sudo systemctl restart chatmrpt"
    
    echo "  ✅ Done"
done

echo ""
echo "🎉 CRITICAL FIX DEPLOYED!"
echo ""
echo "TEST NOW:"
echo "1. Go to: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo "2. Complete TPR workflow and transition"
echo "3. Ask 'Check data quality' - SHOULD EXECUTE TOOLS NOW!"
