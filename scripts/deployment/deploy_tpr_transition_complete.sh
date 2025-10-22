#!/bin/bash

echo "=== Deploying Complete TPR Transition Implementation ==="
echo "Includes: Transition prompts, dynamic confirmation, and file path fixes"

# Copy files to AWS
echo "1. Copying updated files to AWS..."
scp -i /tmp/chatmrpt-key2.pem \
    app/tpr_module/integration/tpr_handler.py \
    app/tpr_module/integration/risk_transition.py \
    app/core/request_interpreter.py \
    ec2-user@3.137.158.17:/tmp/

# Deploy on AWS
ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.137.158.17 << 'EOSSH'
cd /home/ec2-user/ChatMRPT
source /home/ec2-user/chatmrpt_env/bin/activate

echo "2. Backing up existing files..."
cp app/tpr_module/integration/tpr_handler.py app/tpr_module/integration/tpr_handler.py.backup_complete
cp app/tpr_module/integration/risk_transition.py app/tpr_module/integration/risk_transition.py.backup_complete
cp app/core/request_interpreter.py app/core/request_interpreter.py.backup_complete

echo "3. Deploying new files..."
cp /tmp/tpr_handler.py app/tpr_module/integration/
cp /tmp/risk_transition.py app/tpr_module/integration/
cp /tmp/request_interpreter.py app/core/

echo "4. Verifying syntax..."
python3 -m py_compile app/tpr_module/integration/tpr_handler.py
if [ $? -ne 0 ]; then
    echo "✗ Syntax error in tpr_handler.py"
    exit 1
fi

python3 -m py_compile app/tpr_module/integration/risk_transition.py
if [ $? -ne 0 ]; then
    echo "✗ Syntax error in risk_transition.py"
    exit 1
fi

python3 -m py_compile app/core/request_interpreter.py
if [ $? -ne 0 ]; then
    echo "✗ Syntax error in request_interpreter.py"
    exit 1
fi

echo "✓ All files pass syntax check"

echo "5. Cleaning up temp files..."
rm -f /tmp/tpr_handler.py /tmp/risk_transition.py /tmp/request_interpreter.py

echo "6. Restarting service..."
sudo systemctl restart chatmrpt

sleep 3

echo "7. Checking service status..."
sudo systemctl status chatmrpt | head -15

echo ""
echo "=== Deployment Complete! ==="
echo ""
echo "Key features deployed:"
echo "✓ TPR completion shows transition prompt"
echo "✓ Dynamic confirmation detection (accepts 'yes proceed', 'ok let's go', etc.)"
echo "✓ Fixed file paths (*_plus.csv and *_state.zip)"
echo "✓ Clears TPR flags after successful transition"
echo "✓ Permission system shows normal upload workflow response"
echo ""
echo "Test flow:"
echo "1. Complete TPR analysis"
echo "2. See prompt: 'Would you like to proceed to the risk analysis...'"
echo "3. Say 'yes proceed' or similar"
echo "4. Should see: 'I've loaded your data from {state}...'"
EOSSH

echo ""
echo "Deployment script complete!"