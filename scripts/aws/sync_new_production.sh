#!/bin/bash

echo "Syncing fixed code to new production instances..."

NEW_INSTANCES=("172.31.35.51" "172.31.19.192")

for ip in "${NEW_INSTANCES[@]}"; do
    echo "Syncing to $ip..."
    
    # Copy from staging to production
    ssh -i /tmp/chatmrpt-key2.pem -o StrictHostKeyChecking=no ec2-user@3.21.167.170 "
        echo '  Copying critical files...'
        
        # Copy the fixed files
        scp -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no \
            /home/ec2-user/ChatMRPT/app/data_analysis_v3/tools/tpr_analysis_tool.py \
            ec2-user@$ip:/home/ec2-user/ChatMRPT/app/data_analysis_v3/tools/
            
        scp -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no \
            /home/ec2-user/ChatMRPT/app/services/shapefile_fetcher.py \
            ec2-user@$ip:/home/ec2-user/ChatMRPT/app/services/
            
        scp -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no \
            /home/ec2-user/ChatMRPT/app/services/variable_extractor.py \
            ec2-user@$ip:/home/ec2-user/ChatMRPT/app/services/
            
        scp -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no \
            /home/ec2-user/ChatMRPT/app/data_analysis_v3/core/tpr_workflow_handler.py \
            ec2-user@$ip:/home/ec2-user/ChatMRPT/app/data_analysis_v3/core/
            
        scp -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no \
            /home/ec2-user/ChatMRPT/app/config/base.py \
            ec2-user@$ip:/home/ec2-user/ChatMRPT/app/config/
            
        scp -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no \
            /home/ec2-user/ChatMRPT/app/core/tpr_utils.py \
            ec2-user@$ip:/home/ec2-user/ChatMRPT/app/core/
            
        scp -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no \
            /home/ec2-user/ChatMRPT/app/core/llm_adapter.py \
            ec2-user@$ip:/home/ec2-user/ChatMRPT/app/core/
        
        echo '  Restarting service...'
        ssh -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no ec2-user@$ip \
            'sudo systemctl restart chatmrpt'
    "
    
    echo "✅ Synced to $ip"
done

echo ""
echo "Testing services..."
for ip in "${NEW_INSTANCES[@]}"; do
    echo -n "$ip: "
    ssh -i /tmp/chatmrpt-key2.pem -o StrictHostKeyChecking=no ec2-user@3.21.167.170 \
        "curl -s http://$ip:8080/ping | grep -q 'ok' && echo 'OK' || echo 'Failed'"
done