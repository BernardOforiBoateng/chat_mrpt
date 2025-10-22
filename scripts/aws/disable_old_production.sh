#!/bin/bash

# Script to disable old production instances
# These instances are no longer in use - staging is the new production

echo "================================================"
echo "🛑 Disabling Old Production Instances"
echo "================================================"
echo ""
echo "This script will stop the old production instances that are no longer in use."
echo "The 'staging' environment is now the active production."
echo ""

# Old production instance IDs
OLD_PROD_INSTANCES=(
    "i-06d3edfcc85a1f1c7"  # Old production instance 1
    "i-0183aaf795bf8f24e"  # Old production instance 2
)

echo "Old production instances to disable:"
echo "  - Instance 1: i-06d3edfcc85a1f1c7 (172.31.44.52)"
echo "  - Instance 2: i-0183aaf795bf8f24e (172.31.43.200)"
echo ""

read -p "Are you sure you want to STOP these old production instances? (yes/no): " CONFIRM

if [[ "$CONFIRM" != "yes" ]]; then
    echo "❌ Operation cancelled"
    exit 1
fi

echo ""
echo "🔄 Stopping old production instances..."

# Stop instances using AWS CLI
for INSTANCE_ID in "${OLD_PROD_INSTANCES[@]}"; do
    echo "Stopping instance: $INSTANCE_ID"
    aws ec2 stop-instances --instance-ids $INSTANCE_ID --region us-east-2 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo "✅ Stop command sent for $INSTANCE_ID"
    else
        echo "⚠️  Failed to stop $INSTANCE_ID - may need AWS CLI configured or manual stop via console"
    fi
done

echo ""
echo "================================================"
echo "📋 Next Steps:"
echo "================================================"
echo ""
echo "1. Verify instances are stopped in AWS Console:"
echo "   EC2 → Instances → Check status of old production instances"
echo ""
echo "2. Update any monitoring/alerts to remove old production"
echo ""
echo "3. Consider terminating instances after verification period"
echo "   (Keep them stopped for now in case rollback is needed)"
echo ""
echo "4. Update documentation and deployment scripts to remove references to old production"
echo ""
echo "================================================"
echo "✅ Current Active Production (formerly staging):"
echo "================================================"
echo "  - Instance 1: i-0994615951d0b9563 (3.21.167.170)"
echo "  - Instance 2: i-0f3b25b72f18a5037 (18.220.103.20)"
echo "  - ALB: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo "  - CloudFront: https://d225ar6c86586s.cloudfront.net"
echo ""
echo "All future deployments should target these instances only."
echo "================================================"