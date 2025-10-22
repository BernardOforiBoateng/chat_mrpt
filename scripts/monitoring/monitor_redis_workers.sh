#!/bin/bash
# Monitor Redis and Workers for ChatMRPT

echo "=== ChatMRPT Redis & Worker Monitor ==="
echo "Press Ctrl+C to stop monitoring"
echo ""

while true; do
    clear
    echo "=== ChatMRPT Redis & Worker Monitor ==="
    echo "Time: $(date)"
    echo ""
    
    # Worker status
    echo "WORKER STATUS:"
    ssh -i ~/tmp/chatmrpt-key2.pem ec2-user@18.117.115.217 "ps aux | grep gunicorn | grep -v grep | wc -l | xargs -I {} echo 'Gunicorn Processes: {}'"
    
    # Memory usage
    echo ""
    echo "MEMORY USAGE:"
    ssh -i ~/tmp/chatmrpt-key2.pem ec2-user@18.117.115.217 "free -h | grep Mem"
    
    # Redis status
    echo ""
    echo "REDIS STATUS:"
    ssh -i ~/tmp/chatmrpt-key2.pem ec2-user@18.117.115.217 "/home/ec2-user/chatmrpt_env/bin/python3 -c 'import redis; r = redis.Redis(host=\"chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com\"); print(\"Connected Clients:\", r.info().get(\"connected_clients\")); print(\"Session Keys:\", r.dbsize())'"
    
    # Recent errors
    echo ""
    echo "RECENT ERRORS (last 5):"
    ssh -i ~/tmp/chatmrpt-key2.pem ec2-user@18.117.115.217 "grep -i error /home/ec2-user/ChatMRPT/gunicorn-error.log 2>/dev/null | tail -5" || echo "No error log found"
    
    # App status
    echo ""
    echo "APP STATUS:"
    curl -s -o /dev/null -w "HTTP Response: %{http_code}\n" http://18.117.115.217:8080/
    
    sleep 10
done