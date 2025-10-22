#!/bin/bash

echo "=== Fixing Frontend to Use Correct Endpoint ==="
echo "Will update api-client.js to use V3 endpoint when data analysis is active"
echo ""

# Copy key
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

# Connect to staging first to copy the fix
ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 << 'EOF'

# Fix both production instances
for INSTANCE_IP in 172.31.44.52 172.31.43.200; do
    echo "Fixing instance: $INSTANCE_IP"
    
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$INSTANCE_IP << 'FIX'
    cd /home/ec2-user/ChatMRPT
    
    # Backup the file
    cp app/static/js/modules/utils/api-client.js app/static/js/modules/utils/api-client.js.backup.$(date +%Y%m%d_%H%M%S)
    
    # Create the fix
    cat > /tmp/api_client_fix.py << 'PYTHON'
import re

# Read the file
with open('app/static/js/modules/utils/api-client.js', 'r') as f:
    content = f.read()

# Find the fetch call and make it conditional
old_fetch = "        fetch('/send_message_streaming', {"

new_fetch = """        // Check if we're in data analysis mode
        const hasDataAnalysis = sessionStorage.getItem('has_data_analysis_file') === 'true';
        const endpoint = hasDataAnalysis ? '/api/v1/data-analysis/chat' : '/send_message_streaming';
        
        console.log(`🔥 Using endpoint: ${endpoint} (Data Analysis Mode: ${hasDataAnalysis})`);
        
        fetch(endpoint, {"""

# Replace the fetch call
content = content.replace(old_fetch, new_fetch)

# Write back
with open('app/static/js/modules/utils/api-client.js', 'w') as f:
    f.write(content)

print("✅ Fixed api-client.js to use correct endpoint")
PYTHON
    
    python3 /tmp/api_client_fix.py
    
    # Verify the change
    echo ""
    echo "Verifying the fix:"
    grep -B2 -A2 "hasDataAnalysis\|'/api/v1/data-analysis/chat'" app/static/js/modules/utils/api-client.js | head -10
    
    # Restart the service
    echo ""
    echo "Restarting service..."
    sudo systemctl restart chatmrpt
    
    echo "✅ Instance $INSTANCE_IP fixed"
    echo "-----------------------------------"
FIX
done

echo ""
echo "=== Frontend Fix Complete ==="
echo "Both production instances now check for data analysis mode"
echo "Will use /api/v1/data-analysis/chat when data is uploaded"
echo ""
echo "The '2' selection issue should now be fixed!"

EOF