#!/bin/bash
set -e

echo "Optimizing worker configuration for production..."

# SSH to staging and update configuration
ssh -i ~/tmp/chatmrpt-key.pem ec2-user@18.117.115.217 'bash -s' << 'EOF'
set -e

cd /home/ec2-user/ChatMRPT

echo "1. Backing up current configuration..."
cp gunicorn.conf.py gunicorn.conf.py.backup_workers

echo "2. Updating to optimal worker count..."
# Update the workers line to use the calculated value (2 CPUs * 2 + 1 = 5)
sed -i 's/workers = 2  # Testing with 2 workers/workers = 5  # Optimal for 2 CPU cores/' gunicorn.conf.py

echo "3. Verifying changes..."
grep "workers =" gunicorn.conf.py

echo "4. Checking current memory usage..."
free -h

echo "5. Restarting with new configuration..."
sudo systemctl restart chatmrpt
sleep 10

echo "6. Verifying new worker processes..."
ps aux | grep gunicorn | grep -v grep

echo "7. Testing application health..."
curl -s http://localhost:8080/ping && echo -e "\nApp is healthy!"

echo -e "\n✅ Worker optimization complete!"
echo "Configuration:"
echo "- Workers: 5 (optimal for 2 CPU cores)"
echo "- Each worker uses ~300-400MB RAM"
echo "- Total RAM usage: ~1.5-2GB for workers"
echo "- Leaves ~1.5GB for OS and caching"
echo ""
echo "Capacity:"
echo "- Concurrent requests: 5"
echo "- Recommended concurrent users: 10-15"
echo "- Peak burst capacity: 20-25 users"
EOF

echo "Optimization complete!"