#!/bin/bash

echo "=== Getting Streaming Endpoint Code ==="

cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 << 'EOF'

ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 << 'CHECK'
cd /home/ec2-user/ChatMRPT

echo "Getting sendMessageStreaming implementation:"
sed -n '/sendMessageStreaming/,/^    \}/p' app/static/js/modules/utils/api-client.js | head -30

CHECK

EOF
