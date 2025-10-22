#!/bin/bash
# Deploy and run the risk analysis fix on the server

echo "Deploying risk analysis multi-worker fix to server..."

# Copy the fix script to the server
echo "1. Copying fix script to server..."
scp -i ~/tmp/chatmrpt-key.pem risk_analysis_fix_server.py ec2-user@3.137.158.17:/home/ec2-user/

# Run the fix on the server
echo -e "\n2. Running fix on server..."
ssh -i ~/tmp/chatmrpt-key.pem ec2-user@3.137.158.17 "python3 /home/ec2-user/risk_analysis_fix_server.py"

# Restart the application
echo -e "\n3. Restarting application..."
ssh -i ~/tmp/chatmrpt-key.pem ec2-user@3.137.158.17 "sudo systemctl restart chatmrpt && sleep 5 && curl -s http://localhost:8080/ping && echo 'Application restarted successfully!'"

echo -e "\n✓ Risk analysis fix deployed!"
echo "Please test the complete workflow now."