#!/bin/bash
echo "======================================"
echo "CHECKING PRODUCTION INSTANCES"
echo "======================================"

echo ""
echo "1. Instance 172.31.43.200 (Original):"
echo "--------------------------------------"
ssh -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no ec2-user@172.31.43.200 << 'INNER'
echo "Port: $(sudo netstat -tlnp | grep python | awk '{print $4}' | cut -d: -f2)"
echo "Service: $(systemctl is-active chatmrpt)"
echo "Working Dir: $(grep WorkingDirectory /etc/systemd/system/chatmrpt.service)"
echo "ExecStart: $(grep ExecStart /etc/systemd/system/chatmrpt.service)"
echo "Code exists: $([ -d /home/ec2-user/ChatMRPT ] && echo 'YES' || echo 'NO')"
INNER

echo ""
echo "2. Instance 172.31.19.192 (ASG):"
echo "---------------------------------"
ssh -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no ec2-user@172.31.19.192 << 'INNER'
echo "Port: $(sudo netstat -tlnp | grep python | awk '{print $4}' | cut -d: -f2)"
echo "Service: $(systemctl is-active chatmrpt)"
echo "Working Dir: $(grep WorkingDirectory /etc/systemd/system/chatmrpt.service)"
echo "ExecStart: $(grep ExecStart /etc/systemd/system/chatmrpt.service)"
echo "Code exists: $([ -d /home/ec2-user/ChatMRPT ] && echo 'YES' || echo 'NO')"
INNER
