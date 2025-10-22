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
