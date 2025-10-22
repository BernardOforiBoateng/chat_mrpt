#!/bin/bash
# Check production virtual environment

SSH_KEY="/tmp/chatmrpt-key2.pem"
STAGING_HOST="ec2-user@18.117.115.217"

if [ ! -f "$SSH_KEY" ]; then
    cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
    chmod 600 /tmp/chatmrpt-key2.pem
fi

echo "Checking production Python environment..."
ssh -i "$SSH_KEY" "$STAGING_HOST" << 'CHECK'
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 << 'PROD_CHECK'
        echo "Current directory:"
        pwd
        echo ""
        echo "ChatMRPT directory contents:"
        ls -la /home/ec2-user/ChatMRPT/ | grep -E "venv|env"
        echo ""
        echo "Python executables:"
        which python3
        which python
        echo ""
        echo "Checking for virtual environment:"
        if [ -d /home/ec2-user/ChatMRPT/venv ]; then
            echo "Found venv directory"
            ls -la /home/ec2-user/ChatMRPT/venv/bin/python*
        fi
        if [ -d /home/ec2-user/ChatMRPT/chatmrpt_env ]; then
            echo "Found chatmrpt_env directory"
            ls -la /home/ec2-user/ChatMRPT/chatmrpt_env/bin/python*
        fi
        echo ""
        echo "Checking systemd service for python path:"
        grep -E "ExecStart|python" /etc/systemd/system/chatmrpt.service
PROD_CHECK
CHECK