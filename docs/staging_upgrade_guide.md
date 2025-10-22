# Staging Server Upgrade Guide for Qwen3

## Current Specs
- **Instance**: t3.medium (assumed based on 3.7GB RAM)
- **RAM**: 3.7GB
- **CPU**: 2 vCPUs
- **Storage**: 40GB EBS (15GB free)

## Recommended Upgrade Options

### Option A: t3.xlarge (Recommended for Qwen3:8b)
- **RAM**: 16GB
- **CPU**: 4 vCPUs
- **Cost**: ~$0.166/hour ($120/month)
- **Can Run**: Qwen3:8b, Mistral:7b, Llama3:8b

### Option B: t3.2xlarge (Best for Qwen3:30b)
- **RAM**: 32GB
- **CPU**: 8 vCPUs
- **Cost**: ~$0.333/hour ($240/month)
- **Can Run**: Qwen3:30b-a3b, any model under 20GB

### Option C: m5.2xlarge (Production-ready)
- **RAM**: 32GB
- **CPU**: 8 vCPUs
- **Cost**: ~$0.384/hour ($276/month)
- **Better**: More stable performance, no burst limits

## Storage Upgrade
Current 40GB might be tight for multiple models. Recommend:
- **Increase to**: 100GB EBS volume
- **Cost**: Additional $6/month
- **Allows**: Multiple model versions, logs, data

## Step-by-Step Upgrade Process

### 1. Stop the Instance
```bash
# From AWS Console or CLI
aws ec2 stop-instances --instance-ids i-[your-instance-id] --region us-east-2
```

### 2. Change Instance Type (AWS Console)
1. Go to EC2 Dashboard
2. Select staging instance (18.117.115.217)
3. Actions → Instance Settings → Change Instance Type
4. Select t3.xlarge (or your choice)
5. Apply

### 3. Resize EBS Volume (AWS Console)
1. Go to EC2 → Volumes
2. Find volume attached to staging instance
3. Actions → Modify Volume
4. Change size from 40GB to 100GB
5. Apply

### 4. Start Instance
```bash
aws ec2 start-instances --instance-ids i-[your-instance-id] --region us-east-2
```

### 5. Extend Filesystem (After Starting)
```bash
# SSH to instance
ssh -i aws_files/chatmrpt-key.pem ec2-user@18.117.115.217

# Check current disk
df -h

# Grow partition (if needed)
sudo growpart /dev/nvme0n1 1

# Extend filesystem
sudo resize2fs /dev/nvme0n1p1

# Verify
df -h
# Should show 100GB total
```

## Pre-Upgrade Checklist
- [ ] Note current instance ID
- [ ] Backup any important data
- [ ] Inform team about 5-minute downtime
- [ ] Have AWS console access ready

## Post-Upgrade Verification
```bash
# Check new specs
free -h  # Should show 16GB or 32GB
lscpu    # Should show 4 or 8 CPUs
df -h    # Should show 100GB disk

# Verify ChatMRPT still works
curl http://localhost:5000/ping
sudo systemctl status chatmrpt
```

## Quick AWS CLI Commands

### Get Current Instance Details
```bash
aws ec2 describe-instances \
  --instance-ids i-[your-id] \
  --region us-east-2 \
  --query 'Reservations[0].Instances[0].[InstanceType,State.Name,PublicIpAddress]'
```

### Stop, Modify, Start (Full Process)
```bash
# Stop
aws ec2 stop-instances --instance-ids i-[id] --region us-east-2

# Wait for stopped state
aws ec2 wait instance-stopped --instance-ids i-[id] --region us-east-2

# Change type
aws ec2 modify-instance-attribute \
  --instance-id i-[id] \
  --instance-type t3.xlarge \
  --region us-east-2

# Start
aws ec2 start-instances --instance-ids i-[id] --region us-east-2
```

## Estimated Downtime
- Stop instance: 1-2 minutes
- Change type: Instant
- Resize volume: Instant (but needs filesystem resize after)
- Start instance: 1-2 minutes
- **Total**: ~5 minutes

## After Upgrade - Install Ollama
```bash
# With more RAM, we can install bigger models!
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen3:8b    # Now possible with 16GB RAM
ollama pull qwen3:30b   # Possible with 32GB RAM
```

## Cost Comparison
| Instance | RAM | CPU | Monthly | Models Supported |
|----------|-----|-----|---------|-----------------|
| t3.medium (current) | 4GB | 2 | $30 | Only tiny models |
| t3.xlarge | 16GB | 4 | $120 | Qwen3:8b, Mistral:7b |
| t3.2xlarge | 32GB | 8 | $240 | Qwen3:30b, all models |
| +100GB storage | - | - | +$6 | Multiple models |

## Recommendation
For TPR analysis with full data access:
- **Minimum**: t3.xlarge + 100GB storage ($126/month)
- **Optimal**: t3.2xlarge + 100GB storage ($246/month)

This allows running Qwen3:8b or 30b with plenty of room for data processing!