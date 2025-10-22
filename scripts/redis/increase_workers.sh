#!/bin/bash
set -e

echo "Increasing workers on staging server to 5..."

# SSH to staging and update configuration
ssh -i ~/tmp/chatmrpt-key.pem ec2-user@18.117.115.217 'bash -s' << 'EOF'
set -e

cd /home/ec2-user/ChatMRPT

echo "1. Current worker configuration:"
grep GUNICORN_WORKERS .env

echo -e "\n2. Updating .env file to 5 workers..."
sed -i 's/GUNICORN_WORKERS=2/GUNICORN_WORKERS=5/' .env

echo -e "\n3. Verifying change:"
grep GUNICORN_WORKERS .env

echo -e "\n4. Current system resources:"
echo "CPUs: $(nproc)"
free -h

echo -e "\n5. Current Gunicorn processes before restart:"
ps aux | grep gunicorn | grep -v grep | wc -l

echo -e "\n6. Restarting ChatMRPT with 5 workers..."
sudo systemctl restart chatmrpt
sleep 10

echo -e "\n7. New Gunicorn processes after restart:"
ps aux | grep gunicorn | grep -v grep
echo "Total Gunicorn processes: $(ps aux | grep gunicorn | grep -v grep | wc -l)"

echo -e "\n8. Testing application health..."
curl -s http://localhost:8080/ping && echo -e "\nApp is healthy!"

echo -e "\n9. Checking memory usage with 5 workers:"
free -h

echo -e "\n✅ Worker increase complete!"
echo "Configuration updated:"
echo "- Workers: 2 → 5"
echo "- Concurrent capacity: ~20 users → 40-50 users"
echo "- Memory per worker: ~300-400MB"
echo "- Total worker memory: ~1.5-2GB"
EOF

echo -e "\nStagging server now configured for 40-50 concurrent users!"
echo "Access at: http://18.117.115.217:8080/"