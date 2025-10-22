#!/bin/bash

echo "Deploying ChatMRPT to new production instances..."

NEW_INSTANCES=("172.31.35.51" "172.31.19.192")

for ip in "${NEW_INSTANCES[@]}"; do
    echo ""
    echo "Deploying to $ip..."
    
    # Copy entire ChatMRPT from staging
    ssh -i /tmp/chatmrpt-key2.pem -o StrictHostKeyChecking=no ec2-user@3.21.167.170 << EOF
        echo "  1. Copying ChatMRPT codebase to $ip..."
        ssh -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no ec2-user@$ip 'mkdir -p /home/ec2-user'
        
        # Use rsync to copy everything
        rsync -avz --exclude '.git' --exclude 'instance/*' --exclude '__pycache__' \
            -e "ssh -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no" \
            /home/ec2-user/ChatMRPT/ ec2-user@$ip:/home/ec2-user/ChatMRPT/
        
        echo "  2. Setting up service on $ip..."
        ssh -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no ec2-user@$ip << 'INNER'
            cd /home/ec2-user/ChatMRPT
            
            # Create instance directories
            mkdir -p instance/uploads instance/exports instance/logs
            chmod -R 777 instance
            
            # Install Python dependencies if needed
            pip install -r requirements.txt
            
            # Create systemd service
            sudo tee /etc/systemd/system/chatmrpt.service > /dev/null << 'SERVICE'
[Unit]
Description=ChatMRPT Flask Application
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/ChatMRPT
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 -m gunicorn 'run:app' --config gunicorn.conf.py
Restart=always

[Install]
WantedBy=multi-user.target
SERVICE
            
            # Start service
            sudo systemctl daemon-reload
            sudo systemctl enable chatmrpt
            sudo systemctl start chatmrpt
            
            echo "  Service started on $ip"
INNER
EOF
    
    echo "✅ Deployed to $ip"
done

echo ""
echo "Deployment complete! Testing services..."

# Test each instance
for ip in "${NEW_INSTANCES[@]}"; do
    echo -n "Testing $ip: "
    ssh -i /tmp/chatmrpt-key2.pem -o StrictHostKeyChecking=no ec2-user@3.21.167.170 \
        "curl -s -o /dev/null -w '%{http_code}' http://$ip:5000/ping" || echo "Failed"
done