#!/bin/bash

# Deploy corrected routing configuration:
# - Mistral routing ENABLED
# - Fallback patterns DISABLED
# - Debug logging ACTIVE

echo "🚀 Deploying corrected routing configuration..."

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
echo "✨ Deployment complete! Current configuration:"
echo ""
echo "✅ MISTRAL ROUTING: ENABLED"
echo "   - Semantic routing via Mistral:7b model"
echo "   - No hardcoded patterns"
echo ""
echo "❌ FALLBACK PATTERNS: DISABLED"
echo "   - Commented out in route_with_mistral function"
echo "   - If Mistral fails → returns 'needs_clarification'"
echo ""
echo "🔍 DEBUG LOGGING: ACTIVE"
echo "   - ROUTING DEBUG START - shows all session flags"
echo "   - REQUEST INTERPRETER DEBUG - shows decision flow"
echo "   - Clear markers for routing decisions"
echo ""
echo "📊 Monitor logs to see what's happening:"
echo "   ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 'sudo journalctl -u chatmrpt -f | grep -E \"ROUTING DEBUG|REQUEST INTERPRETER|MISTRAL|routing to|WILL USE\"'"
echo ""
echo "⚠️ What to expect:"
echo "   - Mistral makes semantic routing decision"
echo "   - If Mistral fails → user gets clarification prompt"
echo "   - No pattern matching fallback"
echo "   - Pure semantic understanding"