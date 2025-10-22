#!/bin/bash

# Cleanup old Data Analysis and test new V2 on AWS Staging
# This removes old flawed implementation and verifies new system

echo "================================================"
echo "Data Analysis V2 - Staging Cleanup & Test"
echo "================================================"
echo ""

# Set variables
KEY_FILE="/tmp/chatmrpt-key2.pem"
STAGING_IPS=("3.21.167.170" "18.220.103.20")
USERNAME="ec2-user"
APP_DIR="/home/ec2-user/ChatMRPT"

# Check if key file exists
if [ ! -f "$KEY_FILE" ]; then
    echo "Copying key file to /tmp..."
    cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
    chmod 600 /tmp/chatmrpt-key2.pem
fi

echo "🧹 Cleaning up old flawed implementation on STAGING servers..."
echo ""

# Function to cleanup old files on a server
cleanup_server() {
    local IP=$1
    echo "========================================"
    echo "Cleaning up staging server: $IP"
    echo "========================================"
    
    ssh -i "$KEY_FILE" "$USERNAME@$IP" << 'EOF'
        cd /home/ec2-user/ChatMRPT
        
        echo "Removing old flawed files..."
        
        # Remove old data analysis agent
        if [ -f "app/services/data_analysis_agent.py" ]; then
            rm -f app/services/data_analysis_agent.py
            echo "✅ Removed app/services/data_analysis_agent.py"
        fi
        
        # Remove old routes
        if [ -f "app/web/routes/data_analysis_routes.py" ]; then
            rm -f app/web/routes/data_analysis_routes.py
            echo "✅ Removed app/web/routes/data_analysis_routes.py"
        fi
        
        # Remove old frontend
        if [ -f "app/static/js/modules/data-analysis-upload.js" ]; then
            rm -f app/static/js/modules/data-analysis-upload.js
            echo "✅ Removed app/static/js/modules/data-analysis-upload.js"
        fi
        
        # Install dependencies with the correct virtual environment
        echo "Installing Python dependencies..."
        if [ -d "chatmrpt_venv_new" ]; then
            source chatmrpt_venv_new/bin/activate
        elif [ -d "chatmrpt_env" ]; then
            source chatmrpt_env/bin/activate
        else
            echo "Warning: Virtual environment not found"
        fi
        
        pip install langgraph langchain-core plotly RestrictedPython scipy
        echo "✅ Dependencies installed"
        
        # Show what's in the data analysis module now
        echo ""
        echo "New Data Analysis V2 module structure:"
        ls -la app/agents/data_analysis/ 2>/dev/null || echo "Module not found"
        
        echo ""
        echo "Cleanup complete for this server"
EOF
    
    # Restart the application
    echo "Restarting application..."
    ssh -i "$KEY_FILE" "$USERNAME@$IP" "sudo systemctl restart chatmrpt"
    
    echo "✅ Cleanup completed for $IP"
    echo ""
}

# Cleanup both staging servers
for IP in "${STAGING_IPS[@]}"; do
    cleanup_server "$IP"
done

echo "================================================"
echo "Testing Data Analysis V2 on Staging"
echo "================================================"
echo ""

# Test health endpoint
echo "Testing health endpoint via ALB..."
curl -s http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com/api/data-analysis-v2/health | python3 -m json.tool 2>/dev/null || echo "Health check failed or python3 not available for formatting"

echo ""
echo "Testing health endpoint on Instance 1..."
curl -s http://3.21.167.170:5000/api/data-analysis-v2/health 2>/dev/null || echo "Could not reach instance 1 directly"

echo ""
echo "================================================"
echo "✅ Cleanup & Testing Complete!"
echo "================================================"
echo ""
echo "STAGING ONLY - Production untouched"
echo ""
echo "Next steps:"
echo "1. Go to: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo "2. Click on 'Data Analysis' tab"
echo "3. Upload a CSV or Excel file"
echo "4. Test various queries"
echo ""
echo "To monitor logs:"
echo "  ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170"
echo "  sudo journalctl -u chatmrpt -f | grep -E 'data.*analysis|Data.*Analysis|orchestrator'"
echo ""
echo "To check if routes are registered:"
echo "  ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170"
echo "  sudo journalctl -u chatmrpt | grep 'Data Analysis V2 routes registered'"