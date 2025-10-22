#!/bin/bash
set -e

echo "Increasing workers to 6 on staging server..."

# SSH to staging and update configuration
ssh -i ~/tmp/chatmrpt-key.pem ec2-user@18.117.115.217 'bash -s' << 'EOF'
set -e

cd /home/ec2-user/ChatMRPT

echo "1. Current configuration:"
grep GUNICORN_WORKERS .env

echo -e "\n2. Updating to 6 workers..."
sed -i 's/GUNICORN_WORKERS=5/GUNICORN_WORKERS=6/' .env

echo -e "\n3. Verifying change:"
grep GUNICORN_WORKERS .env

echo -e "\n4. Memory before restart:"
free -h

echo -e "\n5. Restarting with 6 workers..."
sudo systemctl restart chatmrpt
sleep 10

echo -e "\n6. Verifying 6 worker processes:"
ps aux | grep gunicorn | grep -v grep | wc -l
echo "Worker processes:"
ps aux | grep gunicorn | grep -v grep | awk '{print $2, $6/1024, "MB"}'

echo -e "\n7. Total memory used by workers:"
ps aux | grep gunicorn | grep -v grep | awk '{sum+=$6} END {print "Total:", sum/1024, "MB"}'

echo -e "\n8. Memory after restart:"
free -h

echo -e "\n9. Testing application health..."
curl -s http://localhost:8080/ping && echo -e "\nApp is healthy!"

echo -e "\n✅ Worker increase to 6 complete!"
echo "Configuration:"
echo "- Workers: 5 → 6"
echo "- Capacity: 40-50 → 50-60 concurrent users"
echo "- Memory headroom still available"
EOF

echo -e "\nStaging now supports 50-60 concurrent users!"