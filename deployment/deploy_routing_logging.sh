#!/bin/bash
# Deploy Routing Logging to Production
# Date: October 20, 2025

echo "=========================================="
echo "Deploying Routing Logging to Production"
echo "=========================================="
echo ""

KEY="/tmp/chatmrpt-key2.pem"
INSTANCES=("3.21.167.170" "18.220.103.20")

# Files to deploy
FILES=(
    "app/interaction/core.py"
    "app/core/analysis_routes.py"
    "tests/test_routing_logging.py"
    "scripts/check_routing_logs.py"
    "scripts/export_routing_data.py"
    "ROUTING_LOGGING_IMPLEMENTATION.md"
)

echo "Files to deploy:"
for file in "${FILES[@]}"; do
    echo "  - $file"
done
echo ""

# Deploy to each instance
for ip in "${INSTANCES[@]}"; do
    echo "=========================================="
    echo "Deploying to $ip..."
    echo "=========================================="

    # Backup database first
    echo "1. Backing up database..."
    ssh -i "$KEY" ec2-user@$ip 'cd ChatMRPT && cp instance/interactions.db instance/interactions.db.backup_$(date +%Y%m%d_%H%M%S)'

    # Copy files
    echo "2. Copying files..."
    for file in "${FILES[@]}"; do
        echo "   - $file"
        scp -i "$KEY" "$file" ec2-user@$ip:/home/ec2-user/ChatMRPT/$file
    done

    # Restart service
    echo "3. Restarting service..."
    ssh -i "$KEY" ec2-user@$ip 'sudo systemctl restart chatmrpt'

    # Wait for service to start
    echo "4. Waiting for service to start..."
    sleep 5

    # Check service status
    echo "5. Checking service status..."
    ssh -i "$KEY" ec2-user@$ip 'sudo systemctl status chatmrpt | head -10'

    # Verify routing_decisions table exists
    echo "6. Verifying routing_decisions table..."
    ssh -i "$KEY" ec2-user@$ip 'sqlite3 /home/ec2-user/ChatMRPT/instance/interactions.db "SELECT name FROM sqlite_master WHERE type='"'"'table'"'"' AND name='"'"'routing_decisions'"'"';"'

    echo "✓ Deployment to $ip complete!"
    echo ""
done

echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Test routing logging by sending messages through production"
echo "2. Run monitoring script: ssh ec2-user@3.21.167.170 'cd ChatMRPT && python3 scripts/check_routing_logs.py'"
echo "3. After pretest, export data: ssh ec2-user@3.21.167.170 'cd ChatMRPT && python3 scripts/export_routing_data.py'"
echo ""
