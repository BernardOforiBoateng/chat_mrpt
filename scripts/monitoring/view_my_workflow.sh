#!/bin/bash

# Simple script to view your recent workflow logs

echo "======================================"
echo "📊 ChatMRPT Workflow Log Viewer"
echo "======================================"
echo ""

KEY_PATH="/tmp/chatmrpt-key2.pem"
INSTANCE_1="3.21.167.170"
INSTANCE_2="18.220.103.20"

echo "Fetching your recent workflow logs..."
echo ""

# Function to get and display logs
show_logs() {
    local ip=$1
    local name=$2
    
    echo "📍 Instance: $name ($ip)"
    echo "----------------------------------------"
    
    # Get last 200 lines and filter for our debug prefixes
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$ip \
        'sudo journalctl -u chatmrpt -n 200 --no-pager | grep -E "🔧 BACKEND:|📊 ANALYSIS:|🔄 TPR:|🛏️ ITN:|⚡ TOOL:|❌ ERROR:|✅ SUCCESS:|🆔 SESSION:|📂 DATA:|🌐 ROUTE:|📊 STATE:"' 2>/dev/null
    
    echo ""
}

# Show logs from both instances
show_logs "$INSTANCE_1" "Production 1"
show_logs "$INSTANCE_2" "Production 2"

echo "======================================"
echo "📝 To get more detailed logs, run:"
echo "  ./get_workflow_logs.sh"
echo ""
echo "🔍 To watch logs in real-time:"
echo "  ssh -i $KEY_PATH ec2-user@$INSTANCE_1 'sudo journalctl -u chatmrpt -f'"
echo "======================================"