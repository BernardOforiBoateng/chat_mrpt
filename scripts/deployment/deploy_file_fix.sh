#\!/bin/bash

echo "=========================================="
echo "DEPLOYING FILE PATH FIX"
echo "=========================================="

STAGING_IP_1="3.21.167.170"
STAGING_IP_2="18.220.103.20"
KEY_PATH="/tmp/chatmrpt-key2.pem"

cp aws_files/chatmrpt-key.pem $KEY_PATH
chmod 600 $KEY_PATH

deploy_to_instance() {
    local IP=$1
    echo "📤 Deploying to $IP..."
    
    scp -o StrictHostKeyChecking=no -i $KEY_PATH \
        app/data_analysis_module/executor.py \
        ec2-user@$IP:/home/ec2-user/ChatMRPT/app/data_analysis_module/
    
    ssh -o StrictHostKeyChecking=no -i $KEY_PATH ec2-user@$IP \
        "sudo systemctl restart chatmrpt && echo '✅ Restarted'"
}

deploy_to_instance $STAGING_IP_1
deploy_to_instance $STAGING_IP_2

rm -f $KEY_PATH
echo "✅ FILE PATH FIX DEPLOYED\!"
