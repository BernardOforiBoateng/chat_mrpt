#!/bin/bash

# Backup script before implementing newcomer helpers
echo "==========================================="
echo "Creating Backup Before Helper Implementation"
echo "==========================================="
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Production instances
INSTANCE1="3.21.167.170"
INSTANCE2="18.220.103.20"
KEY_FILE="/tmp/chatmrpt-key2.pem"

# Backup name with timestamp
BACKUP_NAME="ChatMRPT_before_helpers_$(date +%Y%m%d_%H%M%S)"

echo "📦 Creating backup: $BACKUP_NAME"
echo ""

# Function to create backup on instance
create_backup() {
    local INSTANCE=$1
    local INSTANCE_NUM=$2

    echo "=== Instance $INSTANCE_NUM: $INSTANCE ==="

    # SSH command to create backup
    ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no "ec2-user@$INSTANCE" << 'EOF'
        cd /home/ec2-user
        BACKUP_NAME="ChatMRPT_before_helpers_$(date +%Y%m%d_%H%M%S)"

        echo "Creating backup: $BACKUP_NAME.tar.gz"

        # Create backup excluding large/temporary files
        tar -czf "${BACKUP_NAME}.tar.gz" ChatMRPT/ \
            --exclude="ChatMRPT/instance/uploads/*" \
            --exclude="ChatMRPT/chatmrpt_venv*" \
            --exclude="ChatMRPT/venv*" \
            --exclude="ChatMRPT/__pycache__" \
            --exclude="*.pyc" \
            --exclude="ChatMRPT/.git" \
            --exclude="ChatMRPT/kano_settlement_data/*"

        # Check file size
        if [ -f "${BACKUP_NAME}.tar.gz" ]; then
            SIZE=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)
            echo "✅ Backup created: ${BACKUP_NAME}.tar.gz (Size: $SIZE)"

            # List existing backups
            echo ""
            echo "Existing backups:"
            ls -lh ChatMRPT*.tar.gz 2>/dev/null | tail -5
        else
            echo "❌ Backup creation failed"
        fi
EOF

    echo ""
}

# Create backups on both instances
create_backup "$INSTANCE1" "1"
create_backup "$INSTANCE2" "2"

echo "==========================================="
echo "✨ Backup Process Complete!"
echo "==========================================="
echo ""
echo "📝 Backup Details:"
echo "  - Purpose: Before implementing newcomer helpers"
echo "  - Features being added:"
echo "    • Welcome onboarding for first-time users"
echo "    • Data requirements validation"
echo "    • Workflow progress tracking"
echo "    • Reprioritization planning tool"
echo "    • Proactive help system"
echo ""
echo "🔄 To restore from backup if needed:"
echo "  ssh -i $KEY_FILE ec2-user@<instance-ip>"
echo "  tar -xzf ChatMRPT_before_helpers_*.tar.gz"
echo "  sudo systemctl restart chatmrpt"
echo ""