#!/bin/bash

# Deploy debugging changes to AWS instances
# This adds comprehensive debugging and disables Mistral routing temporarily

echo "🔍 Deploying routing debug changes to AWS instances..."

# Copy the key
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

# Files to update
FILES="app/core/request_interpreter.py app/web/routes/analysis_routes.py"

# Production instances (former staging)
PRODUCTION_IPS="3.21.167.170 18.220.103.20"

echo "📦 Updating production instances..."

for ip in $PRODUCTION_IPS; do
    echo ""
    echo "📍 Deploying to $ip..."

    # Copy updated files
    for file in $FILES; do
        echo "   📄 Copying $file..."
        scp -o StrictHostKeyChecking=no -i /tmp/chatmrpt-key2.pem "$file" "ec2-user@$ip:/home/ec2-user/ChatMRPT/$file"
    done

    # Restart service
    echo "   🔄 Restarting service..."
    ssh -o StrictHostKeyChecking=no -i /tmp/chatmrpt-key2.pem "ec2-user@$ip" "sudo systemctl restart chatmrpt"

    echo "   ✅ Instance $ip updated"
done

echo ""
echo "✨ Deployment complete! Changes deployed:"
echo ""
echo "🔍 DEBUGGING ENHANCEMENTS:"
echo "   1. Comprehensive routing debug logs in analysis_routes.py"
echo "   2. Request interpreter debug logs showing decision flow"
echo "   3. Clear markers for TOOLS vs CONVERSATIONAL mode"
echo ""
echo "⚠️ MISTRAL ROUTING DISABLED:"
echo "   - Using simple heuristic: if any data flags true → tools, else → arena"
echo "   - Mistral code commented out but preserved"
echo ""
echo "📊 Monitor logs to see what's happening:"
echo "   ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 'sudo journalctl -u chatmrpt -f | grep -E \"ROUTING DEBUG|REQUEST INTERPRETER|routing to|WILL USE\"'"
echo ""
echo "🔎 What to look for in logs:"
echo "   - ROUTING DEBUG START - shows session flags"
echo "   - routing to TOOLS/ARENA - shows decision"
echo "   - REQUEST INTERPRETER DEBUG - shows what interpreter receives"
echo "   - WILL USE TOOLS/CONVERSATIONAL - shows final path"