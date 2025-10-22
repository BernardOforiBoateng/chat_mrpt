#!/bin/bash
# Rollback a single instance to previous state

INSTANCE_IP=$1

if [ -z "$INSTANCE_IP" ]; then
    echo "Usage: $0 <instance_ip>"
    exit 1
fi

echo "=== Rolling back $INSTANCE_IP ==="
echo ""

# Find latest backup
LATEST_BACKUP=$(ssh -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no \
    ec2-user@$INSTANCE_IP \
    "cd /home/ec2-user/ChatMRPT && ls -t backups/deployment_* 2>/dev/null | head -1")

if [ -z "$LATEST_BACKUP" ]; then
    echo "❌ No backup found for rollback"
    exit 1
fi

echo "Found backup: $LATEST_BACKUP"
echo "Rolling back..."

ssh -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no \
    ec2-user@$INSTANCE_IP << ROLLBACK
cd /home/ec2-user/ChatMRPT

# Restore files
cp $LATEST_BACKUP/* . -r

# Restart service
sudo systemctl restart chatmrpt

echo "✅ Rollback complete"
ROLLBACK
