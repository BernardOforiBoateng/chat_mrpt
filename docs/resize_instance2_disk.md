# Resize Instance 2 Disk from 40GB to 100GB

## Current Status
- **Instance 1** (3.21.167.170): 100GB disk, 86GB used, 15GB free
- **Instance 2** (18.220.103.20): 40GB disk, 35GB used, 5.7GB free ⚠️

## Steps to Resize Instance 2 Disk

### 1. AWS Console Steps (Manual Required)

1. **Go to EC2 Console**
   - https://console.aws.amazon.com/ec2/
   - Region: us-east-2 (Ohio)

2. **Find Instance 2**
   - Instance ID: `i-0f3b25b72f18a5037`
   - Name: Look for instance with IP 18.220.103.20

3. **Stop the Instance**
   - Select instance → Actions → Instance State → Stop
   - Wait for instance to fully stop

4. **Modify the Volume**
   - Go to EC2 → Elastic Block Store → Volumes
   - Find the volume attached to instance `i-0f3b25b72f18a5037`
   - Select volume → Actions → Modify Volume
   - Change size from 40 GiB to **100 GiB**
   - Click Modify → Yes

5. **Start the Instance**
   - Go back to Instances
   - Select instance → Actions → Instance State → Start
   - Wait for instance to be running

### 2. Extend Filesystem (After Instance Starts)

Once the instance is running again, SSH in and extend the filesystem:

```bash
# SSH to instance
ssh -i /tmp/chatmrpt-key2.pem ec2-user@18.220.103.20

# Check current disk status
df -h /

# Grow the partition (if needed)
sudo growpart /dev/nvme0n1 1

# Extend the filesystem
sudo resize2fs /dev/nvme0n1p1

# Or if using XFS:
# sudo xfs_growfs /

# Verify new size
df -h /
```

### 3. Alternative: AWS CLI Commands

If you have AWS CLI configured:

```bash
# Get instance and volume info
aws ec2 describe-instances --instance-ids i-0f3b25b72f18a5037 --query "Reservations[0].Instances[0].BlockDeviceMappings[0].Ebs.VolumeId" --output text

# Stop instance
aws ec2 stop-instances --instance-ids i-0f3b25b72f18a5037

# Wait for stop
aws ec2 wait instance-stopped --instance-ids i-0f3b25b72f18a5037

# Modify volume (replace vol-xxxxx with actual volume ID)
aws ec2 modify-volume --volume-id vol-xxxxx --size 100

# Start instance
aws ec2 start-instances --instance-ids i-0f3b25b72f18a5037

# Wait for start
aws ec2 wait instance-running --instance-ids i-0f3b25b72f18a5037
```

## Important Notes

⚠️ **Downtime Required**: The instance will be unavailable during resize (5-10 minutes)

⚠️ **Load Balancer**: The ALB will route all traffic to Instance 1 during downtime

⚠️ **Cost Impact**: Larger EBS volume will increase monthly costs slightly (~$6/month for extra 60GB)

## After Resize

Once completed, Instance 2 will have:
- 100GB total disk space
- ~65GB available for use
- Same capacity as Instance 1

This will prevent future "No space left on device" errors and allow for growth.