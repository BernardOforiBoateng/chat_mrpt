#!/bin/bash
# Monitor all instances after deployment

echo "=== Monitoring Production Instances ==="
echo "Press Ctrl+C to stop monitoring"
echo ""

if [ ! -f deployment/configs/production_instances.txt ]; then
    ./deployment/scripts/discover_instances.sh
fi

INSTANCES=$(cat deployment/configs/production_instances.txt)

while true; do
    clear
    echo "=== ChatMRPT Production Monitor ==="
    echo "Time: $(date)"
    echo ""
    
    for instance in $INSTANCES; do
        echo "Instance: $instance"
        
        # Get basic stats
        STATS=$(ssh -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no \
            ec2-user@$instance << 'STATS' 2>/dev/null
# Service status
SERVICE_STATUS=$(sudo systemctl is-active chatmrpt)

# Worker count
WORKERS=$(ps aux | grep gunicorn | grep -v grep | wc -l)

# Memory usage
MEM_USAGE=$(free -m | awk 'NR==2{printf "%.1f%%", $3*100/$2}')

# Redis sessions (sample)
REDIS_SESSIONS=$(cd /home/ec2-user/ChatMRPT && \
    source chatmrpt_env/bin/activate 2>/dev/null || source venv/bin/activate 2>/dev/null && \
    python3 -c "
import redis, os
from dotenv import load_dotenv
load_dotenv()
try:
    r = redis.from_url(os.getenv('REDIS_URL'))
    print(len(list(r.scan_iter('session:*'))))
except:
    print('N/A')
" 2>/dev/null || echo "N/A")

echo "SERVICE:$SERVICE_STATUS|WORKERS:$WORKERS|MEM:$MEM_USAGE|SESSIONS:$REDIS_SESSIONS"
STATS
)
        
        if [ -n "$STATS" ]; then
            SERVICE=$(echo $STATS | cut -d'|' -f1 | cut -d':' -f2)
            WORKERS=$(echo $STATS | cut -d'|' -f2 | cut -d':' -f2)
            MEM=$(echo $STATS | cut -d'|' -f3 | cut -d':' -f2)
            SESSIONS=$(echo $STATS | cut -d'|' -f4 | cut -d':' -f2)
            
            printf "  Service: %-8s Workers: %-3s Memory: %-6s Sessions: %s\n" \
                "$SERVICE" "$WORKERS" "$MEM" "$SESSIONS"
        else
            echo "  Status: Unable to connect"
        fi
        echo ""
    done
    
    sleep 30
done
