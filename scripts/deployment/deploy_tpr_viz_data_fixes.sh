#!/bin/bash
echo "🚀 DEPLOYING TPR VISUALIZATION & DATA ACCESS FIXES TO STAGING"
echo "============================================================="
echo ""
echo "Fixes being deployed:"
echo "1. TPR map visualization display in chat"
echo "2. Data access in main workflow after V3 transition"
echo "3. Correct column detection (not generic columns)"
echo ""

# Staging IPs (updated Jan 7, 2025)
STAGING_IPS=("3.21.167.170" "18.220.103.20")
KEY_PATH="/tmp/chatmrpt-key.pem"

# Copy key if needed
if [ ! -f "$KEY_PATH" ]; then
    cp aws_files/chatmrpt-key.pem $KEY_PATH
    chmod 600 $KEY_PATH
    echo "✅ SSH key prepared"
fi

echo "📦 Deploying to ${#STAGING_IPS[@]} staging instances..."
echo ""

for ip in "${STAGING_IPS[@]}"; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📍 Deploying to instance: $ip"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Deploy JavaScript fixes
    echo "  📄 Uploading message-handler.js (visualization transfer fix)..."
    scp -i $KEY_PATH -o StrictHostKeyChecking=no \
        app/static/js/modules/chat/core/message-handler.js \
        ec2-user@$ip:/home/ec2-user/ChatMRPT/app/static/js/modules/chat/core/
    
    echo "  📄 Uploading api-client.js (visualization passing fix)..."
    scp -i $KEY_PATH -o StrictHostKeyChecking=no \
        app/static/js/modules/utils/api-client.js \
        ec2-user@$ip:/home/ec2-user/ChatMRPT/app/static/js/modules/utils/
    
    # Deploy Python fixes
    echo "  📄 Uploading request_interpreter.py (data access fix)..."
    scp -i $KEY_PATH -o StrictHostKeyChecking=no \
        app/core/request_interpreter.py \
        ec2-user@$ip:/home/ec2-user/ChatMRPT/app/core/
    
    # Clear Python cache
    echo "  🧹 Clearing Python cache..."
    ssh -i $KEY_PATH -o StrictHostKeyChecking=no ec2-user@$ip \
        "cd /home/ec2-user/ChatMRPT && find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true"
    
    # Update cache busting for JavaScript
    echo "  🔄 Updating cache busting..."
    TIMESTAMP=$(date +%s)
    ssh -i $KEY_PATH -o StrictHostKeyChecking=no ec2-user@$ip \
        "cd /home/ec2-user/ChatMRPT && sed -i 's/app\\.js?v=[0-9]*/app.js?v=$TIMESTAMP/' app/templates/index.html 2>/dev/null || true"
    
    # Restart service
    echo "  🔄 Restarting ChatMRPT service..."
    ssh -i $KEY_PATH -o StrictHostKeyChecking=no ec2-user@$ip \
        "sudo systemctl restart chatmrpt"
    
    # Check service status
    echo "  ✅ Checking service status..."
    ssh -i $KEY_PATH -o StrictHostKeyChecking=no ec2-user@$ip \
        "sudo systemctl status chatmrpt | grep Active"
    
    echo "  ✅ Deployment complete for $ip"
    echo ""
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 DEPLOYMENT COMPLETE TO ALL STAGING INSTANCES!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 TESTING INSTRUCTIONS:"
echo "1. Go to: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo "2. IMPORTANT: Hard refresh browser (Ctrl+F5 or Cmd+Shift+R)"
echo "3. Switch to 'Data Analysis' tab"
echo "4. Upload TPR data (e.g., adamawa_tpr_cleaned.csv)"
echo "5. Complete TPR calculation workflow"
echo ""
echo "✅ EXPECTED RESULTS:"
echo "   • TPR map should appear as iframe in chat after calculation"
echo "   • After saying 'yes' to risk analysis, data should be accessible"
echo "   • 'Check data quality' should show actual columns (WardName, TPR, etc.)"
echo "   • NO generic columns (ward_id, pfpr, housing_quality)"
echo ""
echo "🔍 If issues persist, check logs with:"
echo "   ssh -i $KEY_PATH ec2-user@3.21.167.170 'sudo journalctl -u chatmrpt -f'"