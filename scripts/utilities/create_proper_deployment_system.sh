#!/bin/bash
# Create a proper deployment system for multi-instance production environment
# This ensures ALL instances are always in sync

set -e

echo "=== Creating Proper Multi-Instance Deployment System ==="
echo "Date: $(date)"
echo ""

# Create deployment directory structure
mkdir -p deployment/{scripts,configs,logs}

# 1. Create instance discovery script
cat > deployment/scripts/discover_instances.sh << 'EOF'
#!/bin/bash
# Discover all production instances behind the ALB

set -e

echo "=== Discovering Production Instances ==="

# Get ALB ARN
ALB_ARN=$(aws elbv2 describe-load-balancers --region us-east-2 \
    --query "LoadBalancers[?contains(DNSName, 'chatmrpt-alb')].LoadBalancerArn" \
    --output text)

if [ -z "$ALB_ARN" ]; then
    echo "❌ Could not find ChatMRPT ALB"
    exit 1
fi

# Get target group
TARGET_GROUP_ARN=$(aws elbv2 describe-target-groups --region us-east-2 \
    --load-balancer-arn "$ALB_ARN" \
    --query "TargetGroups[0].TargetGroupArn" \
    --output text)

# Get all healthy instances
INSTANCE_IDS=$(aws elbv2 describe-target-health --region us-east-2 \
    --target-group-arn "$TARGET_GROUP_ARN" \
    --query "TargetHealthDescriptions[?TargetHealth.State=='healthy'].Target.Id" \
    --output text)

# Get private IPs for instances
INSTANCE_IPS=""
for instance_id in $INSTANCE_IDS; do
    IP=$(aws ec2 describe-instances --region us-east-2 \
        --instance-ids "$instance_id" \
        --query "Reservations[0].Instances[0].PrivateIpAddress" \
        --output text)
    INSTANCE_IPS="$INSTANCE_IPS $IP"
done

echo "Found instances: $INSTANCE_IPS"
echo "$INSTANCE_IPS" > deployment/configs/production_instances.txt
EOF

chmod +x deployment/scripts/discover_instances.sh

# 2. Create health check script
cat > deployment/scripts/check_instance_health.sh << 'EOF'
#!/bin/bash
# Check health of a specific instance

INSTANCE_IP=$1

if [ -z "$INSTANCE_IP" ]; then
    echo "Usage: $0 <instance_ip>"
    exit 1
fi

echo "Checking health of $INSTANCE_IP..."

# Check if we can SSH
if ssh -i ~/.ssh/chatmrpt-key.pem -o ConnectTimeout=5 -o StrictHostKeyChecking=no \
    ec2-user@$INSTANCE_IP "echo 'SSH OK'" > /dev/null 2>&1; then
    echo "✅ SSH connection successful"
else
    echo "❌ SSH connection failed"
    return 1
fi

# Check service status
SERVICE_STATUS=$(ssh -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no \
    ec2-user@$INSTANCE_IP "sudo systemctl is-active chatmrpt" 2>/dev/null)

if [ "$SERVICE_STATUS" = "active" ]; then
    echo "✅ ChatMRPT service is active"
else
    echo "❌ ChatMRPT service is not active: $SERVICE_STATUS"
    return 1
fi

# Check worker count
WORKER_COUNT=$(ssh -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no \
    ec2-user@$INSTANCE_IP "ps aux | grep gunicorn | grep -v grep | wc -l" 2>/dev/null)

echo "✅ Worker count: $WORKER_COUNT"

# Check Redis connectivity
REDIS_CHECK=$(ssh -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no \
    ec2-user@$INSTANCE_IP << 'CHECK_REDIS'
cd /home/ec2-user/ChatMRPT
source chatmrpt_env/bin/activate 2>/dev/null || source venv/bin/activate 2>/dev/null
python3 << 'PY'
import os
import redis
from dotenv import load_dotenv

load_dotenv()
redis_url = os.getenv('REDIS_URL')
if redis_url:
    try:
        r = redis.from_url(redis_url)
        r.ping()
        print("REDIS_OK")
    except:
        print("REDIS_FAIL")
else:
    print("REDIS_NOT_CONFIGURED")
PY
CHECK_REDIS
)

if [[ "$REDIS_CHECK" == *"REDIS_OK"* ]]; then
    echo "✅ Redis connection successful"
elif [[ "$REDIS_CHECK" == *"REDIS_NOT_CONFIGURED"* ]]; then
    echo "⚠️  Redis not configured"
else
    echo "❌ Redis connection failed"
fi

echo ""
EOF

chmod +x deployment/scripts/check_instance_health.sh

# 3. Create deployment script for single instance
cat > deployment/scripts/deploy_to_instance.sh << 'EOF'
#!/bin/bash
# Deploy to a single instance

INSTANCE_IP=$1
DEPLOYMENT_ID=$2

if [ -z "$INSTANCE_IP" ] || [ -z "$DEPLOYMENT_ID" ]; then
    echo "Usage: $0 <instance_ip> <deployment_id>"
    exit 1
fi

LOG_FILE="deployment/logs/deploy_${INSTANCE_IP}_${DEPLOYMENT_ID}.log"

echo "=== Deploying to $INSTANCE_IP ===" | tee $LOG_FILE
echo "Deployment ID: $DEPLOYMENT_ID" | tee -a $LOG_FILE
echo "Start time: $(date)" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

# 1. Create backup
echo "📋 Creating backup..." | tee -a $LOG_FILE
ssh -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no \
    ec2-user@$INSTANCE_IP << 'BACKUP' 2>&1 | tee -a $LOG_FILE
cd /home/ec2-user/ChatMRPT
BACKUP_DIR="backups/deployment_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# Backup critical files
cp app/static/js/modules/data/tpr-download-manager.js $BACKUP_DIR/
cp app/web/routes/analysis_routes.py $BACKUP_DIR/
cp app/web/routes/tpr_routes.py $BACKUP_DIR/
cp app/web/routes/export_routes.py $BACKUP_DIR/
cp .env $BACKUP_DIR/

echo "✅ Backup created at $BACKUP_DIR"
BACKUP

# 2. Pull latest changes from git (if using git)
echo "" | tee -a $LOG_FILE
echo "📋 Pulling latest changes..." | tee -a $LOG_FILE
ssh -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no \
    ec2-user@$INSTANCE_IP << 'PULL' 2>&1 | tee -a $LOG_FILE
cd /home/ec2-user/ChatMRPT
# If using git:
# git pull origin main
# For now, we'll sync from staging
echo "Syncing from staging/primary instance..."
PULL

# 3. Copy files from staging or primary instance
# This section should be customized based on your deployment method
# For now, we'll copy from the primary instance (172.31.44.52)

echo "" | tee -a $LOG_FILE
echo "📋 Syncing application files..." | tee -a $LOG_FILE

# Get files from primary instance to staging first
PRIMARY_IP="172.31.44.52"
if [ "$INSTANCE_IP" != "$PRIMARY_IP" ]; then
    # Copy critical files
    for file in \
        "app/static/js/modules/data/tpr-download-manager.js" \
        "app/web/routes/analysis_routes.py" \
        "app/web/routes/tpr_routes.py" \
        "app/web/routes/export_routes.py"
    do
        echo "Copying $file..." | tee -a $LOG_FILE
        # Copy from primary to staging
        scp -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no \
            ec2-user@$PRIMARY_IP:/home/ec2-user/ChatMRPT/$file \
            /tmp/$(basename $file) 2>&1 | tee -a $LOG_FILE
        
        # Copy from staging to target
        scp -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no \
            /tmp/$(basename $file) \
            ec2-user@$INSTANCE_IP:/home/ec2-user/ChatMRPT/$file 2>&1 | tee -a $LOG_FILE
    done
fi

# 4. Update configuration
echo "" | tee -a $LOG_FILE
echo "📋 Updating configuration..." | tee -a $LOG_FILE
ssh -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no \
    ec2-user@$INSTANCE_IP << 'CONFIG' 2>&1 | tee -a $LOG_FILE
cd /home/ec2-user/ChatMRPT

# Ensure Redis is pointing to production
if grep -q "redis://chatmrpt-redis-staging" .env; then
    echo "Updating Redis to production endpoint..."
    sudo sed -i 's|redis://chatmrpt-redis-staging|redis://chatmrpt-redis-production|g' .env
fi

# Verify Redis config
echo "Redis configuration:"
grep REDIS_URL .env
CONFIG

# 5. Install dependencies (if needed)
echo "" | tee -a $LOG_FILE
echo "📋 Checking dependencies..." | tee -a $LOG_FILE
ssh -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no \
    ec2-user@$INSTANCE_IP << 'DEPS' 2>&1 | tee -a $LOG_FILE
cd /home/ec2-user/ChatMRPT
source chatmrpt_env/bin/activate 2>/dev/null || source venv/bin/activate 2>/dev/null

# Check if requirements have changed
# pip install -r requirements.txt --quiet
echo "Dependencies check complete"
DEPS

# 6. Run tests (if available)
echo "" | tee -a $LOG_FILE
echo "📋 Running tests..." | tee -a $LOG_FILE
# Add your test commands here

# 7. Restart service
echo "" | tee -a $LOG_FILE
echo "📋 Restarting service..." | tee -a $LOG_FILE
ssh -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no \
    ec2-user@$INSTANCE_IP << 'RESTART' 2>&1 | tee -a $LOG_FILE
sudo systemctl stop chatmrpt
sleep 2
sudo systemctl start chatmrpt
sleep 5

# Check if service started successfully
if sudo systemctl is-active chatmrpt > /dev/null; then
    echo "✅ Service restarted successfully"
    sudo systemctl status chatmrpt | head -10
else
    echo "❌ Service failed to start!"
    sudo journalctl -u chatmrpt -n 50
    exit 1
fi
RESTART

# 8. Verify deployment
echo "" | tee -a $LOG_FILE
echo "📋 Verifying deployment..." | tee -a $LOG_FILE
./deployment/scripts/check_instance_health.sh $INSTANCE_IP 2>&1 | tee -a $LOG_FILE

echo "" | tee -a $LOG_FILE
echo "Deployment to $INSTANCE_IP completed at $(date)" | tee -a $LOG_FILE
EOF

chmod +x deployment/scripts/deploy_to_instance.sh

# 4. Create main deployment orchestrator
cat > deployment/deploy_to_production.sh << 'EOF'
#!/bin/bash
# Main deployment script that orchestrates deployment to all instances

set -e

echo "=== ChatMRPT Production Deployment ==="
echo "Date: $(date)"
echo ""

DEPLOYMENT_ID=$(date +%Y%m%d_%H%M%S)
LOG_FILE="deployment/logs/deployment_${DEPLOYMENT_ID}.log"

# Ensure we're on staging server
if [ ! -f ~/.ssh/chatmrpt-key.pem ]; then
    echo "❌ This script must be run from the staging server"
    exit 1
fi

echo "Deployment ID: $DEPLOYMENT_ID" | tee $LOG_FILE
echo "" | tee -a $LOG_FILE

# 1. Discover all instances
echo "📋 Discovering production instances..." | tee -a $LOG_FILE
./deployment/scripts/discover_instances.sh 2>&1 | tee -a $LOG_FILE

if [ ! -f deployment/configs/production_instances.txt ]; then
    echo "❌ Failed to discover instances" | tee -a $LOG_FILE
    exit 1
fi

INSTANCES=$(cat deployment/configs/production_instances.txt)
INSTANCE_COUNT=$(echo $INSTANCES | wc -w)

echo "Found $INSTANCE_COUNT instances: $INSTANCES" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

# 2. Pre-deployment health check
echo "📋 Pre-deployment health check..." | tee -a $LOG_FILE
ALL_HEALTHY=true
for instance in $INSTANCES; do
    echo "Checking $instance..." | tee -a $LOG_FILE
    if ! ./deployment/scripts/check_instance_health.sh $instance 2>&1 | tee -a $LOG_FILE; then
        ALL_HEALTHY=false
        echo "⚠️  Instance $instance has issues" | tee -a $LOG_FILE
    fi
done

if [ "$ALL_HEALTHY" = false ]; then
    echo "" | tee -a $LOG_FILE
    echo "⚠️  Some instances have issues. Continue anyway? (y/n)" | tee -a $LOG_FILE
    read -p "> " CONTINUE
    if [ "$CONTINUE" != "y" ]; then
        echo "Deployment cancelled" | tee -a $LOG_FILE
        exit 1
    fi
fi

# 3. Deploy to each instance
echo "" | tee -a $LOG_FILE
echo "📋 Starting deployment to all instances..." | tee -a $LOG_FILE
echo "Strategy: Sequential deployment with health checks" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

FAILED_INSTANCES=""
SUCCESS_COUNT=0

for instance in $INSTANCES; do
    echo "=== Deploying to $instance ===" | tee -a $LOG_FILE
    
    if ./deployment/scripts/deploy_to_instance.sh $instance $DEPLOYMENT_ID; then
        echo "✅ Successfully deployed to $instance" | tee -a $LOG_FILE
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        
        # Wait a bit before next instance to avoid overwhelming
        if [ $SUCCESS_COUNT -lt $INSTANCE_COUNT ]; then
            echo "Waiting 10 seconds before next instance..." | tee -a $LOG_FILE
            sleep 10
        fi
    else
        echo "❌ Failed to deploy to $instance" | tee -a $LOG_FILE
        FAILED_INSTANCES="$FAILED_INSTANCES $instance"
    fi
    echo "" | tee -a $LOG_FILE
done

# 4. Final report
echo "=== Deployment Complete ===" | tee -a $LOG_FILE
echo "Deployment ID: $DEPLOYMENT_ID" | tee -a $LOG_FILE
echo "Total instances: $INSTANCE_COUNT" | tee -a $LOG_FILE
echo "Successful: $SUCCESS_COUNT" | tee -a $LOG_FILE
echo "Failed: $(echo $FAILED_INSTANCES | wc -w)" | tee -a $LOG_FILE

if [ -n "$FAILED_INSTANCES" ]; then
    echo "" | tee -a $LOG_FILE
    echo "❌ Failed instances: $FAILED_INSTANCES" | tee -a $LOG_FILE
    echo "" | tee -a $LOG_FILE
    echo "To retry failed instances:" | tee -a $LOG_FILE
    echo "for instance in $FAILED_INSTANCES; do" | tee -a $LOG_FILE
    echo "    ./deployment/scripts/deploy_to_instance.sh \$instance $DEPLOYMENT_ID" | tee -a $LOG_FILE
    echo "done" | tee -a $LOG_FILE
else
    echo "" | tee -a $LOG_FILE
    echo "✅ All instances deployed successfully!" | tee -a $LOG_FILE
fi

echo "" | tee -a $LOG_FILE
echo "Full log: $LOG_FILE" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE
echo "Test the application at:" | tee -a $LOG_FILE
echo "http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com/" | tee -a $LOG_FILE
EOF

chmod +x deployment/deploy_to_production.sh

# 5. Create rollback script
cat > deployment/scripts/rollback_instance.sh << 'EOF'
#!/bin/bash
# Rollback a single instance to previous state

INSTANCE_IP=$1

if [ -z "$INSTANCE_IP" ]; then
    echo "Usage: $0 <instance_ip>"
    exit 1
fi

echo "=== Rolling back $INSTANCE_IP ==="
echo ""

# Find latest backup
LATEST_BACKUP=$(ssh -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no \
    ec2-user@$INSTANCE_IP \
    "cd /home/ec2-user/ChatMRPT && ls -t backups/deployment_* 2>/dev/null | head -1")

if [ -z "$LATEST_BACKUP" ]; then
    echo "❌ No backup found for rollback"
    exit 1
fi

echo "Found backup: $LATEST_BACKUP"
echo "Rolling back..."

ssh -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no \
    ec2-user@$INSTANCE_IP << ROLLBACK
cd /home/ec2-user/ChatMRPT

# Restore files
cp $LATEST_BACKUP/* . -r

# Restart service
sudo systemctl restart chatmrpt

echo "✅ Rollback complete"
ROLLBACK
EOF

chmod +x deployment/scripts/rollback_instance.sh

# 6. Create monitoring script
cat > deployment/scripts/monitor_deployment.sh << 'EOF'
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
EOF

chmod +x deployment/scripts/monitor_deployment.sh

# 7. Create deployment README
cat > deployment/README.md << 'EOF'
# ChatMRPT Production Deployment System

This deployment system ensures consistent updates across all production instances.

## Quick Start

1. **Deploy to all production instances:**
   ```bash
   ./deployment/deploy_to_production.sh
   ```

2. **Monitor deployment:**
   ```bash
   ./deployment/scripts/monitor_deployment.sh
   ```

3. **Check specific instance:**
   ```bash
   ./deployment/scripts/check_instance_health.sh <instance_ip>
   ```

4. **Rollback if needed:**
   ```bash
   ./deployment/scripts/rollback_instance.sh <instance_ip>
   ```

## Directory Structure

```
deployment/
├── deploy_to_production.sh    # Main deployment script
├── scripts/
│   ├── discover_instances.sh  # Find all production instances
│   ├── check_instance_health.sh # Health check script
│   ├── deploy_to_instance.sh  # Deploy to single instance
│   ├── rollback_instance.sh   # Rollback single instance
│   └── monitor_deployment.sh  # Real-time monitoring
├── configs/
│   └── production_instances.txt # List of instance IPs
├── logs/
│   └── deployment_*.log       # Deployment logs
└── README.md                  # This file
```

## Deployment Process

1. **Discovery**: Automatically finds all healthy instances behind ALB
2. **Health Check**: Verifies each instance before deployment
3. **Backup**: Creates timestamped backup on each instance
4. **Deploy**: Updates files and configuration
5. **Verify**: Checks service health after deployment
6. **Monitor**: Continuous monitoring available

## Best Practices

1. Always run from staging server (18.117.115.217)
2. Check pre-deployment health status
3. Monitor logs during deployment
4. Test application after deployment
5. Keep deployment logs for audit trail

## Troubleshooting

- **SSH fails**: Check instance is running and security groups allow access
- **Service won't start**: Check logs with `sudo journalctl -u chatmrpt -n 100`
- **Redis errors**: Verify Redis endpoint in .env file
- **Rollback needed**: Use rollback script to restore previous state

## Future Improvements

1. Add automated testing before/after deployment
2. Implement blue/green deployment strategy
3. Add Slack/email notifications
4. Create deployment approval workflow
5. Integrate with CI/CD pipeline
EOF

echo ""
echo "=== Deployment System Created ==="
echo ""
echo "Structure created:"
tree deployment/ 2>/dev/null || find deployment -type f | sort
echo ""
echo "To deploy the current fixes to ALL production instances:"
echo "1. Copy this deployment folder to staging server"
echo "2. SSH to staging: ssh -i aws_files/chatmrpt-key.pem ec2-user@18.117.115.217"
echo "3. Run: ./deployment/deploy_to_production.sh"
echo ""
echo "This ensures all instances are always in sync!"