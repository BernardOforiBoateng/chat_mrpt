#!/bin/bash
# Script to verify production deployment of TPR and dashboard fixes

echo "=== Production Deployment Verification ==="
echo "Date: $(date)"
echo ""

# SSH connection details
SSH_KEY="/tmp/chatmrpt-key2.pem"
STAGING="ec2-user@18.117.115.217"
PROD_IP="172.31.44.52"

echo "1. Checking TPR download link generation..."
ssh -i "$SSH_KEY" "$STAGING" "ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP 'grep -n \"download_links.*=.*\\[\\]\" /home/ec2-user/ChatMRPT/app/tpr_module/integration/tpr_handler.py | head -5'" 2>/dev/null

echo ""
echo "2. Checking if HTML report is included in TPR output..."
ssh -i "$SSH_KEY" "$STAGING" "ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP 'grep -B2 -A2 \"TPR Analysis Report\" /home/ec2-user/ChatMRPT/app/tpr_module/integration/tpr_handler.py'" 2>/dev/null

echo ""
echo "3. Checking dashboard generation in export tools..."
ssh -i "$SSH_KEY" "$STAGING" "ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP 'grep -n \"include_dashboard.*True\" /home/ec2-user/ChatMRPT/app/tools/export_tools.py'" 2>/dev/null

echo ""
echo "4. Checking for HTML entities fix..."
ssh -i "$SSH_KEY" "$STAGING" "ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP 'grep -c \"&bull;\" /home/ec2-user/ChatMRPT/app/tools/export_tools.py'" 2>/dev/null

echo ""
echo "5. Checking streaming response for download_links..."
ssh -i "$SSH_KEY" "$STAGING" "ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP 'grep -n \"download_links.*tpr_result.get\" /home/ec2-user/ChatMRPT/app/web/routes/analysis_routes.py | tail -3'" 2>/dev/null

echo ""
echo "6. Recent TPR-related logs..."
ssh -i "$SSH_KEY" "$STAGING" "ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP 'sudo journalctl -u chatmrpt -n 50 | grep -i \"tpr.*handler\\|download.*link\" | tail -10'" 2>/dev/null

echo ""
echo "=== Verification Complete ==="