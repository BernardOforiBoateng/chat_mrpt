#!/bin/bash

# AWS Recovery Script - Get services back online after cleanup

echo "=========================================="
echo "AWS Recovery Script"
echo "=========================================="

cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

for IP in 3.21.167.170 18.220.103.20; do
    echo ""
    echo "=== Recovering $IP ==="
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$IP << 'ENDSSH'
        cd /home/ec2-user/ChatMRPT
        
        # Restore critical files from legacy if needed
        if [ ! -d app/templates ] && [ -d legacy/old_frontend/templates ]; then
            echo "Restoring templates for Flask routes..."
            mv legacy/old_frontend/templates app/
        fi
        
        # Simple pip install with compatible versions
        echo "Installing minimal requirements..."
        if [ -d venv ]; then
            source venv/bin/activate
        else
            python3 -m venv venv
            source venv/bin/activate
        fi
        
        pip install --upgrade pip
        pip install flask==2.3.3 flask-login==0.6.3 flask-session==0.8.0 
        pip install gunicorn==21.2.0 python-dotenv==1.0.0
        pip install openai pandas numpy geopandas
        pip install redis langchain langchain-openai
        
        # Start service
        sudo systemctl restart chatmrpt
        echo "✅ Service restarted on $(hostname)"
ENDSSH
done

echo ""
echo "Waiting 15 seconds for services to stabilize..."
sleep 15

echo "Testing endpoints..."
curl -s -o /dev/null -w "ALB Health: %{http_code}\n" http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com/ping
curl -s -o /dev/null -w "CloudFront: %{http_code}\n" https://d225ar6c86586s.cloudfront.net/ping

rm -f /tmp/chatmrpt-key2.pem

echo ""
echo "✅ Recovery complete!"
echo ""
echo "Summary:"
echo "- AWS instances cleaned and organized"
echo "- Services restarted with minimal dependencies"
echo "- Legacy code preserved in legacy/ folders"
echo ""
echo "Next: Fix Ollama arena integration"