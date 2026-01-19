#!/bin/bash

# AWS EC2 Initial Setup Script for ChatMRPT
# Run this on the EC2 instance after first SSH

echo "ChatMRPT AWS EC2 Setup Script"
echo "============================="

# Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required system packages
echo "Installing system dependencies..."
sudo apt install -y python3 python3-pip python3-venv nginx git
sudo apt install -y gdal-bin libgdal-dev python3-gdal
sudo apt install -y libgeos-dev libproj-dev
sudo apt install -y build-essential libssl-dev libffi-dev

# Install Node.js (for any JavaScript dependencies)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Create application directory
echo "Creating application directory..."
sudo mkdir -p /home/ubuntu/ChatMRPT
sudo chown ubuntu:ubuntu /home/ubuntu/ChatMRPT

# Set up systemd service
echo "Setting up systemd service..."
sudo cp /home/ubuntu/ChatMRPT/chatmrpt.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable chatmrpt

# Set up Nginx
echo "Configuring Nginx..."
sudo tee /etc/nginx/sites-available/chatmrpt << 'EOF'
server {
    listen 80;
    server_name _;
    
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
    
    location /static {
        alias /home/ubuntu/ChatMRPT/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/chatmrpt /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

# Set up firewall
echo "Configuring firewall..."
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable

# Create .env file template
echo "Creating .env template..."
cat > /home/ubuntu/.env.template << 'EOF'
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key-here
DATABASE_URL=sqlite:///instance/app.db
EOF

echo "Setup complete!"
echo "Next steps:"
echo "1. Deploy your code using deploy_to_aws.sh"
echo "2. Copy .env.template to ChatMRPT/.env and add your API keys"
echo "3. Start the service with: sudo systemctl start chatmrpt"
echo "4. Check status with: sudo systemctl status chatmrpt"
echo "5. View logs with: sudo journalctl -u chatmrpt -f"