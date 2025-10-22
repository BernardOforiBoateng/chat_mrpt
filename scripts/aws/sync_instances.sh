#!/bin/bash
echo "Syncing code from instance 1 to instance 2..."

# Critical files to sync
FILES=(
    "app/data_analysis_v3/tools/tpr_analysis_tool.py"
    "app/services/shapefile_fetcher.py"
    "app/services/variable_extractor.py"
    "app/data_analysis_v3/core/tpr_workflow_handler.py"
    "app/config/base.py"
    "app/core/tpr_utils.py"
    "app/core/llm_adapter.py"
)

for file in "${FILES[@]}"; do
    echo "Syncing $file..."
    # Copy from instance 1 to instance 2
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.43.200 \
        "scp -i ~/.ssh/chatmrpt-key.pem /home/ec2-user/ChatMRPT/$file ec2-user@172.31.19.192:/home/ec2-user/ChatMRPT/$file"
done

# Restart service on instance 2
echo "Restarting service on instance 2..."
ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.19.192 'sudo systemctl restart chatmrpt'

echo "Done! Both instances should now have identical code."
