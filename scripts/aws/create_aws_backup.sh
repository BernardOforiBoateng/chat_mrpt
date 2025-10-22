#!/bin/bash

echo "=== Creating AWS Backup of Current Stable State ==="
echo "Date: $(date)"
echo ""

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)

# Backup both production instances
for ip in 3.21.167.170 18.220.103.20; do
    instance_num=$([[ "$ip" == "3.21.167.170" ]] && echo "1" || echo "2")
    
    echo ">>> Creating backup on Instance $instance_num ($ip)..."
    
    ssh -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no ec2-user@$ip "
        cd /home/ec2-user
        
        # Create backup with descriptive name
        BACKUP_NAME='ChatMRPT_stable_survey_button_fixed_${BACKUP_DATE}.tar.gz'
        
        echo 'Creating backup: \$BACKUP_NAME'
        tar -czf \$BACKUP_NAME ChatMRPT/ \
            --exclude='ChatMRPT/instance/uploads/*' \
            --exclude='ChatMRPT/chatmrpt_venv*' \
            --exclude='ChatMRPT/venv*' \
            --exclude='ChatMRPT/__pycache__' \
            --exclude='*.pyc' \
            --exclude='ChatMRPT/.git'
        
        # List backup
        ls -lh \$BACKUP_NAME
        echo '✅ Backup created on Instance $instance_num'
    "
    echo ""
done

echo "=== Backup Complete ==="
echo "Backup name: ChatMRPT_stable_survey_button_fixed_${BACKUP_DATE}.tar.gz"
echo "This backup contains the stable state with:"
echo "  - Survey button correctly positioned at end of navigation"
echo "  - All TPR analysis fixes"
echo "  - Working CloudFront configuration"
