#!/bin/bash
# Worker scaling test script for ChatMRPT staging

echo "=== ChatMRPT Worker Scaling Test Script ==="
echo "Testing on STAGING instance: 18.117.115.217"
echo ""

# SSH command function
run_ssh() {
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@18.117.115.217 "$1"
}

# Step 1: Backup current config
echo "Step 1: Backing up current gunicorn config..."
run_ssh "cd /home/ec2-user/ChatMRPT && cp gunicorn.conf.py gunicorn.conf.py.backup && echo 'Backup created'"

# Step 2: Check current worker count
echo ""
echo "Step 2: Checking current worker configuration..."
run_ssh "cd /home/ec2-user/ChatMRPT && grep -E '^workers|^worker_class' gunicorn.conf.py || echo 'workers = 1'"

# Step 3: Update to 2 workers
echo ""
echo "Step 3: Updating to 2 workers..."
run_ssh "cd /home/ec2-user/ChatMRPT && sed -i 's/^workers = .*/workers = 2/' gunicorn.conf.py"

# Step 4: Add worker class and preload if not present
echo ""
echo "Step 4: Adding worker configuration..."
run_ssh "cd /home/ec2-user/ChatMRPT && grep -q 'worker_class' gunicorn.conf.py || echo -e '\nworker_class = \"sync\"\npreload_app = True' >> gunicorn.conf.py"

# Step 5: Show new config
echo ""
echo "Step 5: New configuration:"
run_ssh "cd /home/ec2-user/ChatMRPT && grep -E '^workers|^worker_class|^preload_app' gunicorn.conf.py"

# Step 6: Restart service
echo ""
echo "Step 6: Restarting ChatMRPT service..."
run_ssh "sudo systemctl restart chatmrpt"

# Step 7: Check status
echo ""
echo "Step 7: Checking service status..."
run_ssh "sudo systemctl status chatmrpt --no-pager | head -20"

# Step 8: Check processes
echo ""
echo "Step 8: Verifying worker processes..."
run_ssh "ps aux | grep gunicorn | grep -v grep | wc -l"

echo ""
echo "=== Worker scaling test complete ==="
echo ""
echo "Next steps:"
echo "1. Test the application at http://18.117.115.217:8080"
echo "2. Upload a file and run through complete workflow"
echo "3. Monitor for any errors"
echo "4. If stable after 2 hours, increase to 4 workers"
echo ""
echo "To increase to 4 workers later, run:"
echo "ssh -i /tmp/chatmrpt-key2.pem ec2-user@18.117.115.217 \"cd /home/ec2-user/ChatMRPT && sed -i 's/^workers = .*/workers = 4/' gunicorn.conf.py && sudo systemctl restart chatmrpt\""
echo ""
echo "To rollback if issues occur:"
echo "ssh -i /tmp/chatmrpt-key2.pem ec2-user@18.117.115.217 \"cd /home/ec2-user/ChatMRPT && cp gunicorn.conf.py.backup gunicorn.conf.py && sudo systemctl restart chatmrpt\""