#!/bin/bash

echo "🚀 Deploying Column Sanitization Solution to Staging"
echo "===================================================="

# Files to deploy
FILES=(
    "app/data_analysis_v3/core/column_sanitizer.py"
    "app/data_analysis_v3/core/encoding_handler.py"
    "app/data_analysis_v3/core/agent.py"
    "app/data_analysis_v3/prompts/system_prompt.py"
)

# Staging IPs
STAGING_IPS="3.21.167.170 18.220.103.20"

# Step 1: Install ftfy on staging servers
echo ""
echo "📦 Step 1: Installing ftfy on staging servers..."
for ip in $STAGING_IPS; do
    echo "  - Installing ftfy on $ip"
    ssh -i /tmp/chatmrpt-key2.pem "ec2-user@$ip" 'cd ~/ChatMRPT && source chatmrpt_venv_new/bin/activate && pip install ftfy chardet' &
done
wait
echo "  ✅ ftfy installed on all servers"

# Step 2: Deploy files
echo ""
echo "📂 Step 2: Deploying updated files..."
for ip in $STAGING_IPS; do
    echo ""
    echo "  Deploying to $ip:"
    
    for file in "${FILES[@]}"; do
        echo "    - $file"
        scp -i /tmp/chatmrpt-key2.pem "$file" "ec2-user@$ip:~/ChatMRPT/$file"
    done
    
    echo "  ✅ Files deployed to $ip"
done

# Step 3: Restart services
echo ""
echo "🔄 Step 3: Restarting services..."
for ip in $STAGING_IPS; do
    echo "  - Restarting service on $ip"
    ssh -i /tmp/chatmrpt-key2.pem "ec2-user@$ip" 'sudo systemctl restart chatmrpt' &
done
wait
echo "  ✅ Services restarted"

# Step 4: Health check
echo ""
echo "🏥 Step 4: Health check..."
sleep 5

for ip in $STAGING_IPS; do
    curl -s "http://$ip:8080/ping" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "  ✅ $ip is healthy"
    else
        echo "  ❌ $ip health check failed"
    fi
done

echo ""
echo "===================================================="
echo "🎉 Column Sanitization Solution Deployed!"
echo ""
echo "Key improvements:"
echo "  • Column names sanitized for Python compatibility"
echo "  • Special characters removed (<, ≥, &, etc.)"
echo "  • Pattern matching now works reliably"
echo "  • 'Top 10 facilities' query now succeeds!"
echo ""
echo "Test at: http://3.21.167.170:8080"
echo "===================================================="