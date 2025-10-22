#!/bin/bash

echo "Checking ALB target health and connectivity..."

# First, let's test if we can access the EC2 instance directly
echo "1. Testing direct IP access from your machine:"
echo "Try accessing: http://3.137.158.17:8080/"
echo ""

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.137.158.17 << 'EOF'
echo "=== Checking ALB and Network Configuration ==="

# 1. Get instance details
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
INSTANCE_ID=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id)
echo "Instance ID: $INSTANCE_ID"

# 2. Check if AWS CLI is available and configured
echo ""
echo "2. Checking AWS CLI availability:"
if command -v aws &> /dev/null; then
    echo "AWS CLI is available"
    
    # Try to check target health
    echo ""
    echo "3. Attempting to check ALB target health:"
    aws elbv2 describe-target-health --target-group-arn $(aws elbv2 describe-target-groups --region us-east-2 --query "TargetGroups[?contains(TargetGroupArn, 'chatmrpt')].TargetGroupArn" --output text) --region us-east-2 2>/dev/null || echo "Cannot check ALB health (AWS CLI not configured)"
else
    echo "AWS CLI not available"
fi

# 3. Check current service status
echo ""
echo "4. Current service status:"
sudo systemctl status chatmrpt --no-pager | grep -E "Active:|Main PID:"

# 4. Check if firewall is blocking
echo ""
echo "5. Checking firewall status:"
sudo systemctl status firewalld 2>/dev/null || echo "Firewalld not installed"

# 5. Check listening ports
echo ""
echo "6. Listening ports:"
sudo ss -tlnp | grep -E "8080|80"

# 6. Test local connectivity
echo ""
echo "7. Testing local connectivity:"
curl -v http://localhost:8080/ping 2>&1 | grep -E "Connected|HTTP"

# 7. Check recent access logs for ALB health checks
echo ""
echo "8. Recent access logs (looking for ALB health checks):"
cd /home/ec2-user/ChatMRPT
if [ -f gunicorn-access.log ]; then
    echo "Last 20 access log entries:"
    tail -n 20 gunicorn-access.log
    echo ""
    echo "ALB health check requests (if any):"
    grep -i "ELB-HealthChecker" gunicorn-access.log | tail -n 5 || echo "No ALB health checks found"
else
    echo "No access log found"
fi

# 8. Check error logs
echo ""
echo "9. Recent error logs:"
tail -n 10 gunicorn-error.log 2>/dev/null | grep -v DEBUG || echo "No recent errors"

# 9. Security group check
echo ""
echo "10. Security group info:"
SECURITY_GROUP=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/security-groups)
echo "Security group: $SECURITY_GROUP"

# 10. Test with different binding
echo ""
echo "11. Restarting service with explicit 0.0.0.0 binding:"
sudo systemctl restart chatmrpt
sleep 3
sudo systemctl status chatmrpt --no-pager | grep "Active:"

# Final test
echo ""
echo "12. Final connectivity test:"
for i in {1..3}; do
    echo -n "Attempt $i: "
    curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/
    sleep 1
done

EOF