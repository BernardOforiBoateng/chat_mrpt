#!/bin/bash

# Install missing dependencies on AWS

echo "Installing missing dependencies on AWS..."

cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

for IP in 3.21.167.170 18.220.103.20; do
    echo "Installing on $IP..."
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$IP << 'ENDSSH'
        cd /home/ec2-user/ChatMRPT
        source venv/bin/activate
        
        # Install missing packages
        pip install aiohttp joblib plotly scikit-learn
        
        # Restart service
        sudo systemctl restart chatmrpt
        echo "✅ Done"
ENDSSH
done

rm -f /tmp/chatmrpt-key2.pem

echo "Waiting 10 seconds..."
sleep 10

echo "Testing endpoints..."
curl -s -o /dev/null -w "ALB: %{http_code}\n" http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com/ping
curl -s -o /dev/null -w "CloudFront: %{http_code}\n" https://d225ar6c86586s.cloudfront.net/ping