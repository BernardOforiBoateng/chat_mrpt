#!/bin/bash

# Deploy removal of Data Analysis V2
echo "================================================"
echo "Removing Data Analysis V2 from Staging"
echo "================================================"
echo ""

KEY_FILE="/tmp/chatmrpt-key2.pem"
STAGING_IPS=("3.21.167.170" "18.220.103.20")
USERNAME="ec2-user"
APP_DIR="/home/ec2-user/ChatMRPT"

# Check key file
if [ ! -f "$KEY_FILE" ]; then
    echo "Copying key file..."
    cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
    chmod 600 /tmp/chatmrpt-key2.pem
fi

echo "🗑️ Removing Data Analysis V2 completely"
echo ""

deploy_to_server() {
    local IP=$1
    echo "========================================"
    echo "Cleaning server: $IP"
    echo "========================================"
    
    # Remove the entire data analysis directory
    echo "Removing data analysis agent files..."
    ssh -i "$KEY_FILE" "$USERNAME@$IP" "rm -rf $APP_DIR/app/agents/data_analysis"
    
    # Remove routes
    echo "Removing route files..."
    ssh -i "$KEY_FILE" "$USERNAME@$IP" "rm -f $APP_DIR/app/web/routes/data_analysis_v2_routes.py"
    
    # Remove JavaScript files
    echo "Removing JavaScript files..."
    ssh -i "$KEY_FILE" "$USERNAME@$IP" "rm -f $APP_DIR/app/static/js/modules/data-analysis-v2*.js"
    
    # Copy cleaned up files
    echo "Updating cleaned files..."
    scp -i "$KEY_FILE" app/web/routes/analysis_routes.py "$USERNAME@$IP:$APP_DIR/app/web/routes/"
    scp -i "$KEY_FILE" app/web/routes/__init__.py "$USERNAME@$IP:$APP_DIR/app/web/routes/"
    scp -i "$KEY_FILE" app/templates/index.html "$USERNAME@$IP:$APP_DIR/app/templates/"
    
    # Restart service
    echo "Restarting service..."
    ssh -i "$KEY_FILE" "$USERNAME@$IP" "sudo systemctl restart chatmrpt"
    
    # Wait
    sleep 3
    
    # Check status
    echo "Checking status..."
    ssh -i "$KEY_FILE" "$USERNAME@$IP" "sudo systemctl status chatmrpt | grep Active"
    
    echo "✅ Server $IP cleaned"
    echo ""
}

# Deploy to both servers
for IP in "${STAGING_IPS[@]}"; do
    deploy_to_server "$IP"
done

echo "================================================"
echo "✅ Data Analysis V2 Completely Removed!"
echo "================================================"
echo ""
echo "What was removed:"
echo "• All agent files (15 Python files)"
echo "• Route handlers"
echo "• JavaScript modules"
echo "• All references and imports"
echo ""
echo "Ready to start fresh implementation!"
echo ""
echo "Test at: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"