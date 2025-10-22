#!/bin/bash

echo "============================================"
echo "Deploying General Knowledge Fix"
echo "============================================"

# File to deploy
FILE="app/core/request_interpreter.py"

# Staging instances
STAGING_IPS=(
    "172.31.46.84"
    "172.31.24.195"
)

# Production instances
PRODUCTION_IPS=(
    "172.31.44.52"
    "172.31.43.200"
)

echo ""
echo "📋 Fix Summary:"
echo "   - Model will answer general malaria questions without requiring data"
echo "   - WHO statistics and epidemiological knowledge available immediately"
echo "   - Data uploads only required for user-specific data analysis"
echo ""

echo "📦 File to deploy: $FILE"
echo ""

# Deploy to staging first
echo "🎯 Deploying to STAGING..."
for ip in "${STAGING_IPS[@]}"; do
    echo "   Deploying to $ip..."
    scp -i ~/.ssh/chatmrpt-key.pem "$FILE" "ec2-user@$ip:/home/ec2-user/ChatMRPT/$FILE"
    ssh -i ~/.ssh/chatmrpt-key.pem "ec2-user@$ip" "sudo systemctl restart chatmrpt"
    echo "   ✅ Done"
done

echo ""
echo "✅ Staging deployment complete!"
echo ""
echo "📋 Test on staging:"
echo "   1. Visit http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo "   2. Ask: 'According to WHO, what countries are most affected by malaria?'"
echo "   3. Ask: 'How many people die from malaria each year?'"
echo "   4. Verify model provides statistics without asking for uploads"
echo ""

read -p "Deploy to PRODUCTION? (yes/no): " confirm

if [ "$confirm" = "yes" ]; then
    echo ""
    echo "🎯 Deploying to PRODUCTION..."
    for ip in "${PRODUCTION_IPS[@]}"; do
        echo "   Deploying to $ip..."
        scp -i ~/.ssh/chatmrpt-key.pem "$FILE" "ec2-user@$ip:/home/ec2-user/ChatMRPT/$FILE"
        ssh -i ~/.ssh/chatmrpt-key.pem "ec2-user@$ip" "sudo systemctl restart chatmrpt"
        echo "   ✅ Done"
    done
    
    echo ""
    echo "✅ Production deployment complete!"
    echo "   CloudFront: https://d225ar6c86586s.cloudfront.net"
else
    echo "Production deployment skipped."
fi

echo ""
echo "🎉 Deployment complete!"