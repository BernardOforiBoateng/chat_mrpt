#!/bin/bash
echo "Re-enabling visualization handler..."

# Production Instance IPs
INSTANCE1="3.21.167.170"
INSTANCE2="18.220.103.20"
KEY="/tmp/chatmrpt-key2.pem"

for IP in $INSTANCE1 $INSTANCE2; do
    echo "Updating $IP..."
    
    # Copy the updated file
    scp -i "$KEY" app/static/js/visualization_handler.js "ec2-user@$IP:/home/ec2-user/ChatMRPT/app/static/js/"
    
    # Restart service
    ssh -i "$KEY" "ec2-user@$IP" "sudo systemctl restart chatmrpt"
done

echo "✅ Done! Test at https://d225ar6c86586s.cloudfront.net"
