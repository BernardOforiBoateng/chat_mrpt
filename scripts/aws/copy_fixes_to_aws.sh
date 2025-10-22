#!/bin/bash

# Copy fixed files to AWS using your SSH method

KEY_PATH="/tmp/chatmrpt-key2.pem"
AWS_HOST="ec2-user@3.137.158.17"

echo "Copying fixed files to AWS..."

# Copy the three fixed files
scp -i "$KEY_PATH" app/web/routes/export_routes.py "$AWS_HOST":/home/ec2-user/ChatMRPT/app/web/routes/
scp -i "$KEY_PATH" app/web/routes/reports_api_routes.py "$AWS_HOST":/home/ec2-user/ChatMRPT/app/web/routes/
scp -i "$KEY_PATH" app/static/js/app.js "$AWS_HOST":/home/ec2-user/ChatMRPT/app/static/js/

echo "Files copied successfully!"
echo ""
echo "Now SSH into the server and restart the service:"
echo "ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.137.158.17"
echo ""
echo "Then run:"
echo "cd /home/ec2-user/ChatMRPT"
echo "source /home/ec2-user/chatmrpt_env/bin/activate"
echo "pkill -f gunicorn"
echo "nohup gunicorn 'run:app' --bind=0.0.0.0:8080 --timeout 300 --workers 3 > gunicorn.log 2>&1 &"