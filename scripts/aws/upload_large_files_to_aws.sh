#!/bin/bash

# Script to upload large files to AWS EC2
echo "ChatMRPT Large Files Upload Script"
echo "=================================="

# Check if SSH key is provided
if [ -z "$1" ]; then
    echo "Usage: ./upload_large_files_to_aws.sh /path/to/your-key.pem"
    exit 1
fi

SSH_KEY=$1
AWS_IP="3.137.158.17"

echo "This script will upload:"
echo "1. Raster files (tif/tiff)"
echo "2. Settlement data"
echo "3. Database files"
echo ""
echo "This may take a while due to file sizes..."

# Create a tar of raster files
echo "Creating raster files package..."
if [ -d "rasters" ]; then
    tar -czf rasters.tar.gz rasters/
    echo "Rasters package created: rasters.tar.gz"
fi

# Create a tar of TPR raster database
echo "Creating TPR raster database package..."
if [ -d "app/tpr_module/raster_database" ]; then
    tar -czf tpr_rasters.tar.gz app/tpr_module/raster_database/
    echo "TPR rasters package created: tpr_rasters.tar.gz"
fi

# Create a tar of settlement data
echo "Creating settlement data package..."
if [ -d "kano_settlement_data" ]; then
    tar -czf settlement_data.tar.gz kano_settlement_data/
    echo "Settlement data package created: settlement_data.tar.gz"
fi

# Upload to AWS
echo "Uploading to AWS EC2..."

# Upload rasters
if [ -f "rasters.tar.gz" ]; then
    echo "Uploading rasters (this may take 10-20 minutes)..."
    scp -i "$SSH_KEY" rasters.tar.gz ubuntu@$AWS_IP:~/
fi

# Upload TPR rasters  
if [ -f "tpr_rasters.tar.gz" ]; then
    echo "Uploading TPR rasters..."
    scp -i "$SSH_KEY" tpr_rasters.tar.gz ubuntu@$AWS_IP:~/
fi

# Upload settlement data
if [ -f "settlement_data.tar.gz" ]; then
    echo "Uploading settlement data..."
    scp -i "$SSH_KEY" settlement_data.tar.gz ubuntu@$AWS_IP:~/
fi

# SSH into AWS and extract
echo "Connecting to AWS to extract files..."
ssh -i "$SSH_KEY" ubuntu@$AWS_IP << 'ENDSSH'
    echo "Connected to AWS EC2"
    
    cd /home/ubuntu/ChatMRPT
    
    # Extract rasters
    if [ -f "/home/ubuntu/rasters.tar.gz" ]; then
        echo "Extracting rasters..."
        tar -xzf /home/ubuntu/rasters.tar.gz
        rm /home/ubuntu/rasters.tar.gz
    fi
    
    # Extract TPR rasters
    if [ -f "/home/ubuntu/tpr_rasters.tar.gz" ]; then
        echo "Extracting TPR rasters..."
        tar -xzf /home/ubuntu/tpr_rasters.tar.gz
        rm /home/ubuntu/tpr_rasters.tar.gz
    fi
    
    # Extract settlement data
    if [ -f "/home/ubuntu/settlement_data.tar.gz" ]; then
        echo "Extracting settlement data..."
        tar -xzf /home/ubuntu/settlement_data.tar.gz
        rm /home/ubuntu/settlement_data.tar.gz
    fi
    
    # Set permissions
    echo "Setting permissions..."
    sudo chmod -R 755 rasters/
    sudo chmod -R 755 app/tpr_module/raster_database/
    sudo chmod -R 755 kano_settlement_data/
    
    echo "Large files extraction complete!"
ENDSSH

# Clean up local tar files
rm -f rasters.tar.gz tpr_rasters.tar.gz settlement_data.tar.gz

echo "Upload complete!"