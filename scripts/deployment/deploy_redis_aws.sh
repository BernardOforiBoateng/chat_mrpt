#!/bin/bash
# Deploy Redis configuration to AWS EC2

echo "Deploying Redis configuration to AWS..."

# Variables
KEY_PATH="/tmp/chatmrpt-key2.pem"
EC2_USER="ec2-user"
EC2_IP="3.137.158.17"

# 1. First, install Redis on AWS
echo "Uploading Redis installation script..."
scp -i "$KEY_PATH" install_redis_aws.sh "$EC2_USER@$EC2_IP:~/"

# 2. SSH and install Redis
echo "Installing Redis on EC2..."
ssh -i "$KEY_PATH" "$EC2_USER@$EC2_IP" << 'EOF'
chmod +x install_redis_aws.sh
./install_redis_aws.sh

# Get Redis password
REDIS_PASSWORD=$(sudo grep requirepass /etc/redis/redis.conf | awk '{print $2}')
echo "Redis password: $REDIS_PASSWORD"

# Save to .env file for the application
echo "# Redis Configuration" >> ~/ChatMRPT/.env
echo "REDIS_HOST=localhost" >> ~/ChatMRPT/.env
echo "REDIS_PORT=6379" >> ~/ChatMRPT/.env
echo "REDIS_PASSWORD=$REDIS_PASSWORD" >> ~/ChatMRPT/.env
echo "REDIS_DB=0" >> ~/ChatMRPT/.env

# Install Python Redis package
cd ~/ChatMRPT
source chatmrpt_venv_new/bin/activate
pip install redis==5.0.1

# Restart the application
sudo systemctl restart gunicorn

# Check Redis status
sudo systemctl status redis
EOF

echo "Redis deployment complete!"
echo ""
echo "Next steps:"
echo "1. SSH into the server to verify Redis is running: sudo systemctl status redis"
echo "2. Check application logs: tail -f ~/ChatMRPT/instance/app.log"
echo "3. Test Redis connection: curl http://3.137.158.17/api/session/redis-status"