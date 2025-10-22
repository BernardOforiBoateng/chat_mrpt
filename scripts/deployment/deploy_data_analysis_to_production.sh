#!/bin/bash

# Deploy Data Analysis Tab Updates to Production
# This script deploys ONLY the Data Analysis tab changes

set -e

echo "=== Deploying Data Analysis Tab to Production ==="
echo "This will update ONLY the Data Analysis tab functionality"

# Files to deploy
BACKEND_FILES=(
    "app/data_analysis_v3/core/encoding_handler.py"
    "app/data_analysis_v3/core/formatters.py"
    "app/data_analysis_v3/tools/tpr_analysis_tool.py"
    "app/data_analysis_v3/core/tpr_workflow_handler.py"
    "requirements.txt"
)

FRONTEND_FILES=(
    "app/static/js/modules/chat/core/message-handler.js"
)

# Production instances (accessed via staging)
STAGING_IP="3.21.167.170"
PROD_INSTANCE_1="172.31.44.52"
PROD_INSTANCE_2="172.31.43.200"

KEY_PATH="/tmp/chatmrpt-key2.pem"

echo "Files to deploy:"
echo "Backend: ${BACKEND_FILES[@]}"
echo "Frontend: ${FRONTEND_FILES[@]}"
echo ""

# Step 1: Copy files to staging first
echo "Step 1: Copying files to staging..."
for file in "${BACKEND_FILES[@]}" "${FRONTEND_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  Copying $file to staging..."
        scp -i $KEY_PATH "$file" ec2-user@$STAGING_IP:/tmp/
    fi
done

# Step 2: Copy from staging to production instance 1
echo ""
echo "Step 2: Deploying to Production Instance 1 ($PROD_INSTANCE_1)..."
ssh -i $KEY_PATH ec2-user@$STAGING_IP << 'EOF'
    # Copy files to production instance 1
    for file in app/data_analysis_v3/core/encoding_handler.py \
                app/data_analysis_v3/core/formatters.py \
                app/data_analysis_v3/tools/tpr_analysis_tool.py \
                app/data_analysis_v3/core/tpr_workflow_handler.py \
                requirements.txt \
                app/static/js/modules/chat/core/message-handler.js; do
        
        filename=$(basename $file)
        if [ -f "/tmp/$filename" ]; then
            echo "  Copying $filename to production instance 1..."
            # Create directory structure if needed
            dir=$(dirname $file)
            ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 "mkdir -p /home/ec2-user/ChatMRPT/$dir"
            # Copy file
            scp -i ~/.ssh/chatmrpt-key.pem /tmp/$filename ec2-user@172.31.44.52:/home/ec2-user/ChatMRPT/$file
        fi
    done
    
    # Install ftfy if needed
    echo "  Installing ftfy on instance 1..."
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 "/home/ec2-user/chatmrpt_env/bin/pip install ftfy chardet"
    
    # Restart service
    echo "  Restarting service on instance 1..."
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 "sudo systemctl restart chatmrpt"
    echo "  Instance 1 updated successfully!"
EOF

# Step 3: Test instance 1
echo ""
echo "Step 3: Testing Production Instance 1..."
sleep 10
ssh -i $KEY_PATH ec2-user@$STAGING_IP "ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 'sudo systemctl is-active chatmrpt'"

# Step 4: Deploy to production instance 2
echo ""
read -p "Instance 1 is updated. Deploy to Instance 2? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Step 4: Deploying to Production Instance 2 ($PROD_INSTANCE_2)..."
    ssh -i $KEY_PATH ec2-user@$STAGING_IP << 'EOF'
        # Copy files to production instance 2
        for file in app/data_analysis_v3/core/encoding_handler.py \
                    app/data_analysis_v3/core/formatters.py \
                    app/data_analysis_v3/tools/tpr_analysis_tool.py \
                    app/data_analysis_v3/core/tpr_workflow_handler.py \
                    requirements.txt \
                    app/static/js/modules/chat/core/message-handler.js; do
            
            filename=$(basename $file)
            if [ -f "/tmp/$filename" ]; then
                echo "  Copying $filename to production instance 2..."
                # Create directory structure if needed
                dir=$(dirname $file)
                ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.43.200 "mkdir -p /home/ec2-user/ChatMRPT/$dir"
                # Copy file
                scp -i ~/.ssh/chatmrpt-key.pem /tmp/$filename ec2-user@172.31.43.200:/home/ec2-user/ChatMRPT/$file
            fi
        done
        
        # Install ftfy if needed
        echo "  Installing ftfy on instance 2..."
        ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.43.200 "/home/ec2-user/chatmrpt_env/bin/pip install ftfy chardet"
        
        # Restart service
        echo "  Restarting service on instance 2..."
        ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.43.200 "sudo systemctl restart chatmrpt"
        echo "  Instance 2 updated successfully!"
EOF
else
    echo "Skipping Instance 2 deployment"
fi

echo ""
echo "=== Data Analysis Tab Deployment Complete ==="
echo "The Data Analysis tab (formerly TPR) has been updated on production"
echo "Test at: http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com"