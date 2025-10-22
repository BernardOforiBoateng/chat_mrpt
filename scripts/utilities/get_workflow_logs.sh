#!/bin/bash

# Script to retrieve ChatMRPT workflow logs from AWS instances

echo "======================================"
echo "ChatMRPT Workflow Log Retrieval"
echo "======================================"

# Configuration
KEY_PATH="/tmp/chatmrpt-key2.pem"
INSTANCE_1="3.21.167.170"
INSTANCE_2="18.220.103.20"
LOG_DIR="workflow_logs_$(date +%Y%m%d_%H%M%S)"

# Create local directory for logs
mkdir -p "$LOG_DIR"

echo ""
echo "Which instance do you want to get logs from?"
echo "1) Instance 1 ($INSTANCE_1)"
echo "2) Instance 2 ($INSTANCE_2)"
echo "3) Both instances"
read -p "Enter choice (1-3): " choice

# Function to get logs from an instance
get_logs() {
    local ip=$1
    local instance_name=$2
    
    echo ""
    echo "Fetching logs from $instance_name ($ip)..."
    
    # Get last 500 lines of logs (adjust as needed)
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$ip \
        "sudo journalctl -u chatmrpt -n 500 --no-pager" > "$LOG_DIR/${instance_name}_full.log" 2>/dev/null
    
    # Get filtered logs for different components
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$ip \
        "sudo journalctl -u chatmrpt -n 500 --no-pager | grep 'FRONTEND:'" > "$LOG_DIR/${instance_name}_frontend.log" 2>/dev/null
    
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$ip \
        "sudo journalctl -u chatmrpt -n 500 --no-pager | grep 'BACKEND:'" > "$LOG_DIR/${instance_name}_backend.log" 2>/dev/null
    
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$ip \
        "sudo journalctl -u chatmrpt -n 500 --no-pager | grep 'ANALYSIS:'" > "$LOG_DIR/${instance_name}_analysis.log" 2>/dev/null
    
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$ip \
        "sudo journalctl -u chatmrpt -n 500 --no-pager | grep 'TPR:'" > "$LOG_DIR/${instance_name}_tpr.log" 2>/dev/null
    
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$ip \
        "sudo journalctl -u chatmrpt -n 500 --no-pager | grep 'ITN:'" > "$LOG_DIR/${instance_name}_itn.log" 2>/dev/null
    
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$ip \
        "sudo journalctl -u chatmrpt -n 500 --no-pager | grep 'ERROR'" > "$LOG_DIR/${instance_name}_errors.log" 2>/dev/null
    
    echo "✅ Logs saved to $LOG_DIR/"
}

# Execute based on choice
case $choice in
    1)
        get_logs "$INSTANCE_1" "instance1"
        ;;
    2)
        get_logs "$INSTANCE_2" "instance2"
        ;;
    3)
        get_logs "$INSTANCE_1" "instance1"
        get_logs "$INSTANCE_2" "instance2"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "======================================"
echo "Log files created in: $LOG_DIR/"
echo "======================================"
echo ""
echo "Files created:"
ls -la "$LOG_DIR/"
echo ""
echo "To view logs:"
echo "  Full logs: cat $LOG_DIR/*_full.log"
echo "  Frontend: cat $LOG_DIR/*_frontend.log"
echo "  Backend: cat $LOG_DIR/*_backend.log"
echo "  Analysis: cat $LOG_DIR/*_analysis.log"
echo "  Errors: cat $LOG_DIR/*_errors.log"