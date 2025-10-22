#!/bin/bash

echo "Checking ALB connectivity and configuration..."

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.137.158.17 << 'EOF'
echo "=== Checking instance details ==="

# 1. Check instance metadata
echo "1. Instance ID and region:"
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
INSTANCE_ID=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id)
REGION=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/placement/region)
echo "Instance ID: $INSTANCE_ID"
echo "Region: $REGION"

# 2. Check security group rules
echo ""
echo "2. Security group configuration:"
aws ec2 describe-security-groups --region $REGION --group-ids $(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/security-groups | head -1) 2>/dev/null | grep -E "GroupId|IpProtocol|FromPort|ToPort|CidrIp" | head -20 || echo "AWS CLI not configured"

# 3. Check if application is actually listening
echo ""
echo "3. Application listening ports:"
sudo ss -tlnp | grep -E "8080|80|443"

# 4. Test application response with full headers
echo ""
echo "4. Testing application response:"
curl -I -v http://localhost:8080/ 2>&1 | grep -E "HTTP|Connected|Content-Length"

# 5. Check for any firewall rules
echo ""
echo "5. Checking iptables rules:"
sudo iptables -L -n | head -20

# 6. Check recent access attempts
echo ""
echo "6. Recent access logs (if any):"
cd /home/ec2-user/ChatMRPT
if [ -f gunicorn-access.log ]; then
    echo "Recent requests:"
    tail -n 20 gunicorn-access.log
else
    echo "No access log file yet"
fi

# 7. Check error logs
echo ""
echo "7. Recent error logs:"
if [ -f gunicorn-error.log ]; then
    tail -n 20 gunicorn-error.log | grep -v DEBUG
else
    echo "No error log file"
fi

# 8. Try to restart with simpler config
echo ""
echo "8. Restarting with minimal configuration..."
pkill -f gunicorn
sleep 2

cd /home/ec2-user/ChatMRPT
source /home/ec2-user/chatmrpt_env/bin/activate

# Start with minimal config
echo "Starting gunicorn with minimal config..."
gunicorn 'run:app' --bind 0.0.0.0:8080 --workers 1 --timeout 120 --access-logfile - --error-logfile - &

sleep 3

# Test one more time
echo ""
echo "9. Final test:"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:8080/

EOF