#!/bin/bash

# Script to resize Instance 2 disk from 40GB to 100GB
# REQUIRES: AWS CLI with appropriate permissions

INSTANCE_ID="i-0f3b25b72f18a5037"
REGION="us-east-2"
NEW_SIZE=100

echo "=========================================="
echo "Resizing Instance 2 Disk to 100GB"
echo "=========================================="
echo "Instance ID: $INSTANCE_ID"
echo "Region: $REGION"
echo "New Size: ${NEW_SIZE}GB"
echo ""

# Step 1: Get the volume ID
echo "Step 1: Getting volume ID..."
VOLUME_ID=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --region $REGION \
    --query "Reservations[0].Instances[0].BlockDeviceMappings[0].Ebs.VolumeId" \
    --output text)

if [ -z "$VOLUME_ID" ]; then
    echo "❌ Failed to get volume ID"
    exit 1
fi

echo "✅ Volume ID: $VOLUME_ID"
echo ""

# Step 2: Check current volume state
echo "Step 2: Checking current volume state..."
CURRENT_SIZE=$(aws ec2 describe-volumes \
    --volume-ids $VOLUME_ID \
    --region $REGION \
    --query "Volumes[0].Size" \
    --output text)

echo "Current size: ${CURRENT_SIZE}GB"

if [ "$CURRENT_SIZE" -eq "$NEW_SIZE" ]; then
    echo "✅ Volume is already ${NEW_SIZE}GB"
    exit 0
fi

# Step 3: Stop the instance
echo ""
echo "Step 3: Stopping instance..."
aws ec2 stop-instances --instance-ids $INSTANCE_ID --region $REGION
echo "⏳ Waiting for instance to stop..."
aws ec2 wait instance-stopped --instance-ids $INSTANCE_ID --region $REGION
echo "✅ Instance stopped"

# Step 4: Modify the volume
echo ""
echo "Step 4: Modifying volume to ${NEW_SIZE}GB..."
aws ec2 modify-volume \
    --volume-id $VOLUME_ID \
    --size $NEW_SIZE \
    --region $REGION

# Wait for modification to complete
echo "⏳ Waiting for volume modification to complete..."
sleep 30

# Check modification state
MOD_STATE=$(aws ec2 describe-volumes-modifications \
    --volume-ids $VOLUME_ID \
    --region $REGION \
    --query "VolumesModifications[0].ModificationState" \
    --output text)

echo "Modification state: $MOD_STATE"

# Step 5: Start the instance
echo ""
echo "Step 5: Starting instance..."
aws ec2 start-instances --instance-ids $INSTANCE_ID --region $REGION
echo "⏳ Waiting for instance to start..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $REGION
echo "✅ Instance running"

# Step 6: Get the public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --region $REGION \
    --query "Reservations[0].Instances[0].PublicIpAddress" \
    --output text)

echo ""
echo "=========================================="
echo "✅ Volume resize initiated successfully!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Wait 2-3 minutes for instance to fully boot"
echo "2. SSH to the instance: ssh -i <key> ec2-user@$PUBLIC_IP"
echo "3. Extend the filesystem:"
echo "   sudo growpart /dev/nvme0n1 1"
echo "   sudo xfs_growfs /"
echo "4. Verify with: df -h /"
echo ""