#!/bin/bash

# Fast AWS Cleanup - Run on both instances in parallel

echo "=========================================="
echo "Fast AWS Production Cleanup"
echo "=========================================="

# Copy key
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

# Create lightweight cleanup script (no backup)
cat << 'EOF' > /tmp/cleanup_fast.sh
#!/bin/bash
cd /home/ec2-user/ChatMRPT

echo "=== Fast cleanup on $(hostname) ==="

# Create directories
mkdir -p scripts/{deployment,checks,fixes,setup,tests}
mkdir -p legacy/{vllm,old_frontend,arena,misc}

# Quick moves (no searching)
mv *vllm* legacy/vllm/ 2>/dev/null
mv deploy_*.sh scripts/deployment/ 2>/dev/null
mv check_*.sh scripts/checks/ 2>/dev/null
mv fix_*.sh scripts/fixes/ 2>/dev/null
mv setup_*.sh scripts/setup/ 2>/dev/null
mv test_*.{py,sh,html} scripts/tests/ 2>/dev/null

# Move Flask stuff if exists
[ -d app/templates ] && mv app/templates legacy/old_frontend/
[ -d app/static/archived_old_frontend ] && mv app/static/archived_old_frontend legacy/old_frontend/
[ -d app/static/css ] && mv app/static/css legacy/old_frontend/
[ -d app/static/js ] && mv app/static/js legacy/old_frontend/

# Move arena duplicates
mv app/core/arena_manager_{memory_backup,redis,redis_fixed}.py legacy/arena/ 2>/dev/null
mv arena_manager_update.py legacy/arena/ 2>/dev/null

# Fix .env
sed -i '/VLLM_/d' .env 2>/dev/null
sed -i 's/ARENA_MODELS=.*/ARENA_MODELS=llama3.1:8b,mistral:7b,phi3:mini/' .env 2>/dev/null

echo "✅ Cleanup done - $(ls -1 | wc -l) items in root (was 500+)"
EOF

# Run on both instances in parallel
echo "Cleaning both instances in parallel..."

for IP in 3.21.167.170 18.220.103.20; do
    (
        echo "Starting cleanup on $IP..."
        scp -q -i /tmp/chatmrpt-key2.pem /tmp/cleanup_fast.sh ec2-user@$IP:/tmp/
        ssh -q -i /tmp/chatmrpt-key2.pem ec2-user@$IP 'bash /tmp/cleanup_fast.sh'
        ssh -q -i /tmp/chatmrpt-key2.pem ec2-user@$IP 'sudo systemctl restart chatmrpt'
        echo "✅ Done: $IP"
    ) &
done

# Wait for both to complete
wait

echo ""
echo "=========================================="
echo "✅ Both AWS instances cleaned!"
echo "=========================================="

# Test the endpoints
echo ""
echo "Testing endpoints..."
curl -s -o /dev/null -w "ALB Response: %{http_code}\n" http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com/ping
curl -s -o /dev/null -w "CloudFront Response: %{http_code}\n" https://d225ar6c86586s.cloudfront.net/ping

rm -f /tmp/chatmrpt-key2.pem /tmp/cleanup_fast.sh