#!/bin/bash

# Deploy routing decision fix to AWS instances
# This fixes the issue where request_interpreter ignores Mistral routing decision

echo "🚀 Deploying routing decision fix to AWS instances..."

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
echo "1. request_interpreter now respects routing_decision parameter"
echo "2. When routing_decision='needs_tools', data_loaded check is skipped"
echo "3. analysis_routes passes routing_decision to interpreter"
echo ""
echo "🧪 Test with queries like:"
echo "   - 'Tell me about the variables in my data'"
echo "   - 'Run the risk analysis'"
echo "   - 'Plot me the map distribution for the evi variable'"
echo ""
echo "📊 Monitor logs with:"
echo "   ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 'sudo journalctl -u chatmrpt -f | grep -E \"Routing decision|data_loaded\"'"