#!/bin/bash
# Monitor Redis cluster creation status

SSH_KEY="/tmp/chatmrpt-key2.pem"
STAGING_HOST="ec2-user@18.117.115.217"

echo "Monitoring Redis cluster creation..."
echo "This typically takes 5-10 minutes..."
echo ""

while true; do
    STATUS=$(ssh -i "$SSH_KEY" "$STAGING_HOST" 'aws elasticache describe-cache-clusters --cache-cluster-id chatmrpt-redis-production --show-cache-node-info --region us-east-2 --query "CacheClusters[0].[CacheClusterStatus,CacheNodes[0].Endpoint.Address,CacheNodes[0].Endpoint.Port]" --output text')
    
    CLUSTER_STATUS=$(echo "$STATUS" | awk '{print $1}')
    ENDPOINT=$(echo "$STATUS" | awk '{print $2}')
    PORT=$(echo "$STATUS" | awk '{print $3}')
    
    echo "[$(date '+%H:%M:%S')] Status: $CLUSTER_STATUS"
    
    if [ "$CLUSTER_STATUS" == "available" ]; then
        echo ""
        echo "✅ Redis cluster is ready!"
        echo "Endpoint: $ENDPOINT:$PORT"
        echo ""
        echo "Now run:"
        echo "./implement_production_redis.sh UPDATE $ENDPOINT:$PORT"
        break
    elif [ "$CLUSTER_STATUS" == "failed" ]; then
        echo "❌ Redis cluster creation failed!"
        exit 1
    fi
    
    sleep 30
done