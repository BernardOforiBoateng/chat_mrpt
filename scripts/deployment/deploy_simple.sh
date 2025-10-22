#!/bin/bash

echo "=== Simple TPR Transition Deployment ==="

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.137.158.17 'bash -s' << 'EOSSH'
cd /home/ec2-user/ChatMRPT
source /home/ec2-user/chatmrpt_env/bin/activate

echo "1. Moving files into place..."
cp /tmp/tpr_handler_new.py app/tpr_module/integration/tpr_handler.py
cp /tmp/risk_transition_new.py app/tpr_module/integration/risk_transition.py
cp /tmp/request_interpreter_new.py app/core/request_interpreter.py

echo "2. Checking syntax..."
python3 -m py_compile app/tpr_module/integration/tpr_handler.py && echo "✓ tpr_handler.py OK"
python3 -m py_compile app/tpr_module/integration/risk_transition.py && echo "✓ risk_transition.py OK"
python3 -m py_compile app/core/request_interpreter.py && echo "✓ request_interpreter.py OK"

echo "3. Restarting service..."
sudo systemctl restart chatmrpt

echo "4. Waiting for service to start..."
sleep 3

echo "5. Service status:"
sudo systemctl status chatmrpt | head -10

echo ""
echo "✅ Deployment complete!"
EOSSH