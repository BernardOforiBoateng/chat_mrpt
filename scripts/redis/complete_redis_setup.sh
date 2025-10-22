#!/bin/bash
# Complete Redis setup once the cluster is available

set -e

SSH_KEY="/tmp/chatmrpt-key2.pem"
STAGING_HOST="ec2-user@18.117.115.217"

echo "=== Redis Production Setup Completion Script ==="
echo ""

# Check if key exists
if [ ! -f "$SSH_KEY" ]; then
    cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
    chmod 600 /tmp/chatmrpt-key2.pem
fi

# Check Redis status
echo "Checking Redis cluster status..."
STATUS_INFO=$(ssh -i "$SSH_KEY" "$STAGING_HOST" 'aws elasticache describe-cache-clusters --cache-cluster-id chatmrpt-redis-production --show-cache-node-info --region us-east-2 --query "CacheClusters[0].[CacheClusterStatus,CacheNodes[0].Endpoint.Address,CacheNodes[0].Endpoint.Port]" --output text')

CLUSTER_STATUS=$(echo "$STATUS_INFO" | awk '{print $1}')
ENDPOINT=$(echo "$STATUS_INFO" | awk '{print $2}')
PORT=$(echo "$STATUS_INFO" | awk '{print $3}')

echo "Status: $CLUSTER_STATUS"

if [ "$CLUSTER_STATUS" != "available" ]; then
    echo ""
    echo "❌ Redis cluster is not ready yet (Status: $CLUSTER_STATUS)"
    echo "Please wait a few more minutes and run this script again."
    echo ""
    echo "You can check the status in AWS Console:"
    echo "https://us-east-2.console.aws.amazon.com/elasticache/home?region=us-east-2#/redis/chatmrpt-redis-production"
    exit 1
fi

echo "✅ Redis cluster is available!"
echo "Endpoint: $ENDPOINT:$PORT"
echo ""

# Now update production
echo "Updating production configuration..."
./implement_production_redis.sh UPDATE "$ENDPOINT:$PORT"