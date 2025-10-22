# Create a Stable ChatMRPT Instance - Manual Steps

## Quick Solution: Launch New EC2 Instance via AWS Console

### Step 1: Launch Instance from AWS Console

1. **Go to EC2 Console**: https://console.aws.amazon.com/ec2/
2. **Click "Launch Instance"**
3. **Configure with these settings**:
   - **Name**: `ChatMRPT-Stable-20240923`
   - **AMI**: `ami-02c0a366899ceb8d2` (or Amazon Linux 2)
   - **Instance Type**: `t3.large` (or t3.xlarge if you need more power)
   - **Key Pair**: Select `chatmrpt-key`
   - **Network Settings**:
     - VPC: (use default or same as existing)
     - Subnet: `subnet-0713ee8d5af26578a`
     - Security Group: `sg-0b21586985a0bbfbe` (existing security group)
   - **Storage**: 30 GB gp3

4. **Click "Launch Instance"**

### Step 2: Wait for Instance to Start
- Note the **Public IP Address** (e.g., X.X.X.X)
- Wait 2-3 minutes for full initialization

### Step 3: Copy Stable Code to New Instance

Run these commands from your local machine:

```bash
# Set the new instance IP
NEW_IP="X.X.X.X"  # Replace with actual IP

# Copy the backup from Instance 2 to your local machine first
scp -i aws_files/chatmrpt-key.pem ec2-user@18.220.103.20:/home/ec2-user/ChatMRPT_code_only_backup_20250923_161113.tar.gz ./

# Upload to new instance
scp -i aws_files/chatmrpt-key.pem ChatMRPT_code_only_backup_20250923_161113.tar.gz ec2-user@$NEW_IP:/home/ec2-user/

# SSH to new instance
ssh -i aws_files/chatmrpt-key.pem ec2-user@$NEW_IP
```

### Step 4: Setup ChatMRPT on New Instance

Once SSH'd into the new instance:

```bash
# Install dependencies
sudo yum update -y
sudo yum install -y python3 python3-pip python3-devel git
sudo yum install -y gcc gcc-c++ make
sudo yum install -y postgresql-devel

# Create ChatMRPT directory
mkdir -p /home/ec2-user/ChatMRPT
cd /home/ec2-user

# Extract the backup
tar -xzf ChatMRPT_code_only_backup_20250923_161113.tar.gz

# Copy data files from Instance 2
# Run this from your LOCAL machine:
exit  # Exit from new instance first

# Copy essential data folders
ssh -i aws_files/chatmrpt-key.pem ec2-user@18.220.103.20 "cd /home/ec2-user/ChatMRPT && tar -czf ~/data_folders.tar.gz www/ instance/ kano_settlement_data/"
scp -i aws_files/chatmrpt-key.pem ec2-user@18.220.103.20:~/data_folders.tar.gz ./
scp -i aws_files/chatmrpt-key.pem data_folders.tar.gz ec2-user@$NEW_IP:/home/ec2-user/

# SSH back to new instance
ssh -i aws_files/chatmrpt-key.pem ec2-user@$NEW_IP

# Extract data folders
cd /home/ec2-user/ChatMRPT
tar -xzf ../data_folders.tar.gz

# Create virtual environment
python3 -m venv chatmrpt_env
source chatmrpt_env/bin/activate

# Install Python packages
pip install --upgrade pip
pip install -r requirements.txt

# Create systemd service
sudo tee /etc/systemd/system/chatmrpt.service > /dev/null << 'EOL'
[Unit]
Description=ChatMRPT Gunicorn Application
After=network.target

[Service]
User=ec2-user
Group=ec2-user
WorkingDirectory=/home/ec2-user/ChatMRPT
Environment="PATH=/home/ec2-user/chatmrpt_env/bin"
ExecStart=/home/ec2-user/chatmrpt_env/bin/gunicorn run:app --config gunicorn_config.py

[Install]
WantedBy=multi-user.target
EOL

# Start the service
sudo systemctl daemon-reload
sudo systemctl enable chatmrpt
sudo systemctl start chatmrpt

# Check status
sudo systemctl status chatmrpt
```

### Step 5: Configure Security Group for Direct Access

1. Go to EC2 Console → Security Groups
2. Find `sg-0b21586985a0bbfbe`
3. Edit Inbound Rules → Add Rule:
   - Type: Custom TCP
   - Port: 8000
   - Source: 0.0.0.0/0 (or your IP for security)
   - Description: ChatMRPT Stable Direct Access

### Step 6: Access Your Stable Instance

Your stable instance will be available at:
```
http://[NEW_INSTANCE_PUBLIC_IP]:8000
```

For example: `http://54.123.45.67:8000`

## Important Notes

1. **This instance is completely separate** from your production instances
2. **It has the current working code** with all TPR fixes
3. **Changes to Instance 1 and 2 won't affect this stable instance**
4. **Remember to stop this instance when not needed** to save costs
5. **The instance will have its own public IP** that won't change unless stopped

## Cost Consideration

- t3.large: ~$0.0832/hour ($60/month if running 24/7)
- t3.xlarge: ~$0.1664/hour ($120/month if running 24/7)
- **TIP**: Stop the instance when not in use and start when needed

## Quick Commands

```bash
# Stop instance (when not needed)
aws ec2 stop-instances --instance-ids [INSTANCE_ID]

# Start instance (when needed)
aws ec2 start-instances --instance-ids [INSTANCE_ID]

# Get current public IP after starting
aws ec2 describe-instances --instance-ids [INSTANCE_ID] --query 'Reservations[0].Instances[0].PublicIpAddress' --output text
```