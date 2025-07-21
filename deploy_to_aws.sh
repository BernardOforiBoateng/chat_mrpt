#!/bin/bash

# AWS Deployment Script for ChatMRPT
# This script helps deploy the latest code to AWS EC2

echo "ChatMRPT AWS Deployment Script"
echo "=============================="

# Check if IP address is provided
if [ -z "$1" ]; then
    echo "Reading IP from aws_files/Public IPv4 address.txt..."
    AWS_IP=$(cat "aws_files/Public IPv4 address.txt" | tr -d '\n\r ')
else
    AWS_IP=$1
fi

echo "Deploying to: $AWS_IP"

# Check if SSH key path is provided
if [ -z "$2" ]; then
    echo "Please provide the path to your AWS SSH key (.pem file) as the second argument"
    echo "Usage: ./deploy_to_aws.sh [IP_ADDRESS] /path/to/your-key.pem"
    exit 1
fi

SSH_KEY=$2

# Create a deployment package INCLUDING large files
echo "Creating deployment package (this will take time due to large files)..."
echo "Including raster files, settlement data, and TPR data..."
tar -czf chatmrpt_deploy.tar.gz \
    --exclude='.git*' \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='chatmrpt_venv*' \
    --exclude='instance/*.db' \
    --exclude='instance/uploads/*' \
    --exclude='*.log' \
    --exclude='*.tar.gz' \
    --exclude='*.zip' \
    .

echo "Package created: chatmrpt_deploy.tar.gz"

# Upload to AWS
echo "Uploading to AWS (this may take 5-10 minutes due to large files)..."
scp -i "$SSH_KEY" chatmrpt_deploy.tar.gz ec2-user@$AWS_IP:~/

# SSH into AWS and deploy
echo "Connecting to AWS to deploy..."
ssh -i "$SSH_KEY" ec2-user@$AWS_IP << 'ENDSSH'
    echo "Connected to AWS EC2 instance"
    
    # Stop the application
    echo "Stopping application..."
    # Kill gunicorn processes
    pkill -f gunicorn || true
    
    # Backup current deployment
    echo "Backing up current deployment..."
    if [ -d "/home/ec2-user/ChatMRPT" ]; then
        mv /home/ec2-user/ChatMRPT /home/ec2-user/ChatMRPT.backup.$(date +%Y%m%d_%H%M%S)
    fi
    
    # Create new directory
    echo "Creating new deployment directory..."
    mkdir -p /home/ec2-user/ChatMRPT
    cd /home/ec2-user/ChatMRPT
    
    # Extract new code
    echo "Extracting new code..."
    tar -xzf ../chatmrpt_deploy.tar.gz
    
    # Create necessary directories with proper permissions
    echo "Creating directories..."
    mkdir -p instance/uploads
    mkdir -p instance/reports
    mkdir -p instance/logs
    mkdir -p instance/exports
    mkdir -p sessions
    mkdir -p data
    mkdir -p kano_settlement_data
    
    # Set permissions
    echo "Setting permissions..."
    sudo chmod -R 777 instance/
    sudo chmod -R 777 sessions/
    sudo chmod -R 777 data/
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment and install dependencies
    echo "Installing dependencies..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Set environment variables
    echo "Setting environment variables..."
    if [ ! -f ".env" ]; then
        cp .env.production .env
        echo "Please edit .env file to add your OPENAI_API_KEY"
    fi
    
    # Start the application
    echo "Starting application..."
    sudo systemctl start chatmrpt || echo "Service not configured. Please set up systemd service."
    
    echo "Deployment complete!"
ENDSSH

# Clean up
rm chatmrpt_deploy.tar.gz

echo "Deployment script finished!"