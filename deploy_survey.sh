#!/bin/bash

# Deploy Survey Module to AWS Production Instances
# ================================================

echo "=========================================="
echo "Deploying Survey Module to AWS Production"
echo "=========================================="

# Configuration
KEY_PATH="/tmp/chatmrpt-key2.pem"
INSTANCES=("3.21.167.170" "18.220.103.20")
REMOTE_DIR="/home/ec2-user/ChatMRPT"

# Files to deploy
SURVEY_FILES=(
    "app/survey/__init__.py"
    "app/survey/models.py"
    "app/survey/questions.py"
    "app/survey/routes.py"
    "app/templates/survey/index.html"
    "app/static/css/survey.css"
    "app/static/js/survey.js"
    "app/static/js/survey_button.js"
    "app/static/react/index.html"
    "app/web/routes/__init__.py"
)

# Check if key exists
if [ ! -f "$KEY_PATH" ]; then
    echo "Setting up SSH key..."
    cp aws_files/chatmrpt-key.pem "$KEY_PATH"
    chmod 600 "$KEY_PATH"
fi

# Deploy to each instance
for INSTANCE in "${INSTANCES[@]}"; do
    echo ""
    echo "Deploying to instance: $INSTANCE"
    echo "-----------------------------------"

    # Create survey directories
    echo "Creating survey directories..."
    ssh -o StrictHostKeyChecking=no -i "$KEY_PATH" "ec2-user@$INSTANCE" << 'SSHEOF'
        cd /home/ec2-user/ChatMRPT
        mkdir -p app/survey
        mkdir -p app/templates/survey
        mkdir -p app/static/css
        mkdir -p app/static/js
SSHEOF

    # Copy survey files
    echo "Copying survey files..."
    for FILE in "${SURVEY_FILES[@]}"; do
        echo "  - $FILE"
        scp -o StrictHostKeyChecking=no -i "$KEY_PATH" "$FILE" "ec2-user@$INSTANCE:$REMOTE_DIR/$FILE"
    done

    # Restart service
    echo "Restarting ChatMRPT service..."
    ssh -o StrictHostKeyChecking=no -i "$KEY_PATH" "ec2-user@$INSTANCE" << 'SSHEOF'
        sudo systemctl restart chatmrpt
        sleep 3
        sudo systemctl status chatmrpt | head -10
SSHEOF

    echo "✅ Deployment to $INSTANCE completed"
done

echo ""
echo "=========================================="
echo "Survey Module Deployment Complete!"
echo "=========================================="
echo ""
echo "Test URLs:"
echo "  - https://d225ar6c86586s.cloudfront.net/survey/"
echo "  - http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com/survey/"
echo ""
echo "Next steps:"
echo "1. Test survey page loads correctly"
echo "2. Verify survey button appears in ChatMRPT interface"
echo "3. Test survey triggers from arena mode"
echo "4. Monitor logs: sudo journalctl -u chatmrpt -f"
echo ""
