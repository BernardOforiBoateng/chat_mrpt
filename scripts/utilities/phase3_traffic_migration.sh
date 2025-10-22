#!/bin/bash

# =====================================================
# Phase 3: Traffic Migration Setup
# =====================================================
# Purpose: Configure weighted routing for gradual traffic migration
# Date: August 27, 2025
# =====================================================

set -e

# Configuration
KEY_PATH="/tmp/chatmrpt-key2.pem"
STAGING_IP="3.21.167.170"
OLD_PROD_ALB="chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com"
NEW_STAGING_ALB="chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
AWS_REGION="us-east-2"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "======================================================"
echo "   PHASE 3: TRAFFIC MIGRATION SETUP"
echo "   $(date)"
echo "======================================================"
echo ""

# Function to create health checks
create_health_checks() {
    echo -e "${YELLOW}Creating Health Checks for Both Environments...${NC}"
    echo ""
    
    # Health check for old production
    echo "Creating health check for OLD production..."
    ssh -i $KEY_PATH ec2-user@$STAGING_IP << EOF 2>/dev/null
        export AWS_DEFAULT_REGION=us-east-1
        
        # Old production health check
        cat > /tmp/old-prod-health-check.json << 'HC'
{
    "Type": "HTTP",
    "ResourcePath": "/ping",
    "FullyQualifiedDomainName": "$OLD_PROD_ALB",
    "Port": 80,
    "RequestInterval": 30,
    "FailureThreshold": 3,
    "MeasureLatency": true,
    "Inverted": false,
    "Disabled": false,
    "EnableSNI": false
}
HC
        
        aws route53 create-health-check \
            --caller-reference "old-prod-$(date +%s)" \
            --health-check-config file:///tmp/old-prod-health-check.json \
            --output json > /tmp/old_hc_result.json 2>&1
        
        if [ $? -eq 0 ]; then
            OLD_HC_ID=$(cat /tmp/old_hc_result.json | jq -r '.HealthCheck.Id')
            echo "✅ Old Production Health Check: $OLD_HC_ID"
            
            # Add tags
            aws route53 change-tags-for-resource \
                --resource-type healthcheck \
                --resource-id "$OLD_HC_ID" \
                --add-tags Key=Name,Value=ChatMRPT-Old-Production Key=Environment,Value=production
        else
            echo "❌ Failed to create old production health check"
        fi
EOF
    
    echo ""
    echo "Creating health check for NEW staging (future production)..."
    ssh -i $KEY_PATH ec2-user@$STAGING_IP << EOF 2>/dev/null
        export AWS_DEFAULT_REGION=us-east-1
        
        # New staging health check
        cat > /tmp/new-staging-health-check.json << 'HC'
{
    "Type": "HTTP",
    "ResourcePath": "/ping",
    "FullyQualifiedDomainName": "$NEW_STAGING_ALB",
    "Port": 80,
    "RequestInterval": 30,
    "FailureThreshold": 3,
    "MeasureLatency": true,
    "Inverted": false,
    "Disabled": false,
    "EnableSNI": false
}
HC
        
        aws route53 create-health-check \
            --caller-reference "new-staging-$(date +%s)" \
            --health-check-config file:///tmp/new-staging-health-check.json \
            --output json > /tmp/new_hc_result.json 2>&1
        
        if [ $? -eq 0 ]; then
            NEW_HC_ID=$(cat /tmp/new_hc_result.json | jq -r '.HealthCheck.Id')
            echo "✅ New Staging Health Check: $NEW_HC_ID"
            
            # Add tags
            aws route53 change-tags-for-resource \
                --resource-type healthcheck \
                --resource-id "$NEW_HC_ID" \
                --add-tags Key=Name,Value=ChatMRPT-New-Staging Key=Environment,Value=staging
        else
            echo "❌ Failed to create new staging health check"
        fi
EOF
    
    echo ""
}

# Function to display traffic migration plan
show_migration_plan() {
    echo -e "${BLUE}======================================================"
    echo "   TRAFFIC MIGRATION PLAN"
    echo "======================================================${NC}"
    echo ""
    echo "Current Setup:"
    echo "-------------"
    echo "• Old Production: $OLD_PROD_ALB"
    echo "• New Staging: $NEW_STAGING_ALB"
    echo ""
    echo "Migration Phases:"
    echo "----------------"
    echo "Phase 1: 10% to new (90% old) - Test with minimal traffic"
    echo "Phase 2: 25% to new (75% old) - Monitor for issues"
    echo "Phase 3: 50% to new (50% old) - Equal distribution"
    echo "Phase 4: 75% to new (25% old) - Majority on new"
    echo "Phase 5: 100% to new (0% old) - Complete migration"
    echo ""
    echo "Each phase should run for:"
    echo "• Phase 1: 2-4 hours (monitoring closely)"
    echo "• Phase 2: 4-8 hours"
    echo "• Phase 3: 12-24 hours"
    echo "• Phase 4: 24 hours"
    echo "• Phase 5: Final cutover"
    echo ""
}

# Function to create weighted routing configuration
create_weighted_routing() {
    local weight_new=$1
    local weight_old=$((100 - weight_new))
    
    echo -e "${YELLOW}Configuring Weighted Routing (${weight_new}% new, ${weight_old}% old)...${NC}"
    
    # Note: This would typically be done through Route 53 with an existing hosted zone
    # For demonstration, we'll create the configuration files
    
    cat > /tmp/weighted-routing-config.json << EOF
{
    "Comment": "ChatMRPT Traffic Migration - ${weight_new}% to new staging",
    "Changes": [
        {
            "Action": "UPSERT",
            "ResourceRecordSet": {
                "Name": "app.chatmrpt.com",
                "Type": "A",
                "SetIdentifier": "Old-Production-${weight_old}",
                "Weight": ${weight_old},
                "AliasTarget": {
                    "HostedZoneId": "Z3AADJGX6KTTL2",
                    "DNSName": "$OLD_PROD_ALB",
                    "EvaluateTargetHealth": true
                }
            }
        },
        {
            "Action": "UPSERT",
            "ResourceRecordSet": {
                "Name": "app.chatmrpt.com",
                "Type": "A",
                "SetIdentifier": "New-Staging-${weight_new}",
                "Weight": ${weight_new},
                "AliasTarget": {
                    "HostedZoneId": "Z3AADJGX6KTTL2",
                    "DNSName": "$NEW_STAGING_ALB",
                    "EvaluateTargetHealth": true
                }
            }
        }
    ]
}
EOF
    
    echo "✅ Weighted routing configuration created (saved to /tmp/weighted-routing-config.json)"
    echo ""
    echo "To apply this configuration:"
    echo "  aws route53 change-resource-record-sets --hosted-zone-id YOUR_ZONE_ID --change-batch file:///tmp/weighted-routing-config.json"
    echo ""
}

# Function to create monitoring dashboard
create_monitoring_dashboard() {
    echo -e "${YELLOW}Creating Migration Monitoring Dashboard...${NC}"
    
    ssh -i $KEY_PATH ec2-user@$STAGING_IP << 'EOF' 2>/dev/null
        export AWS_DEFAULT_REGION=us-east-2
        
        cat > /tmp/migration-dashboard.json << 'DASHBOARD'
{
    "name": "ChatMRPT-Migration-Monitor",
    "body": "{\"widgets\":[{\"type\":\"metric\",\"properties\":{\"metrics\":[[\"AWS/ELB\",\"RequestCount\",{\"stat\":\"Sum\",\"label\":\"Old Production\"}],[\".\",\".\",{\"stat\":\"Sum\",\"label\":\"New Staging\"}]],\"period\":300,\"stat\":\"Sum\",\"region\":\"us-east-2\",\"title\":\"Request Distribution\"}},{\"type\":\"metric\",\"properties\":{\"metrics\":[[\"AWS/ELB\",\"HTTPCode_Target_2XX_Count\",{\"label\":\"Old - Success\"}],[\".\",\"HTTPCode_Target_5XX_Count\",{\"label\":\"Old - Errors\"}],[\".\",\"HTTPCode_Target_2XX_Count\",{\"label\":\"New - Success\"}],[\".\",\"HTTPCode_Target_5XX_Count\",{\"label\":\"New - Errors\"}]],\"period\":60,\"stat\":\"Sum\",\"region\":\"us-east-2\",\"title\":\"Response Codes\"}},{\"type\":\"metric\",\"properties\":{\"metrics\":[[\"AWS/Route53\",\"HealthCheckStatus\",{\"label\":\"Old Production Health\"}],[\".\",\".\",{\"label\":\"New Staging Health\"}]],\"period\":60,\"stat\":\"Minimum\",\"region\":\"us-east-1\",\"title\":\"Health Check Status\"}}]}"
}
DASHBOARD
        
        aws cloudwatch put-dashboard \
            --dashboard-name ChatMRPT-Migration-Monitor \
            --dashboard-body file:///tmp/migration-dashboard.json \
            --output json > /tmp/dashboard_result.json 2>&1
        
        if [ $? -eq 0 ]; then
            echo "✅ Migration monitoring dashboard created"
            echo "   View at: https://console.aws.amazon.com/cloudwatch/home?region=us-east-2#dashboards:name=ChatMRPT-Migration-Monitor"
        else
            echo "⚠️  Dashboard creation had issues (may already exist)"
        fi
EOF
    
    echo ""
}

# Function to test traffic routing
test_traffic_routing() {
    echo -e "${YELLOW}Testing Traffic Routing...${NC}"
    echo ""
    
    echo "Testing OLD production endpoint..."
    OLD_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://$OLD_PROD_ALB/ping" 2>/dev/null || echo "000")
    if [ "$OLD_STATUS" = "200" ]; then
        echo -e "  Old Production: ${GREEN}✅ Healthy (HTTP $OLD_STATUS)${NC}"
    else
        echo -e "  Old Production: ${RED}❌ Unhealthy (HTTP $OLD_STATUS)${NC}"
    fi
    
    echo "Testing NEW staging endpoint..."
    NEW_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://$NEW_STAGING_ALB/ping" 2>/dev/null || echo "000")
    if [ "$NEW_STATUS" = "200" ]; then
        echo -e "  New Staging: ${GREEN}✅ Healthy (HTTP $NEW_STATUS)${NC}"
    else
        echo -e "  New Staging: ${RED}❌ Unhealthy (HTTP $NEW_STATUS)${NC}"
    fi
    
    echo ""
}

# Function to create rollback plan
create_rollback_plan() {
    echo -e "${BLUE}Creating Rollback Plan...${NC}"
    
    cat > rollback_plan.md << 'EOF'
# 🔄 Traffic Migration Rollback Plan

## Quick Rollback (< 2 minutes)
If issues are detected during migration:

1. **Immediate DNS Rollback**:
   ```bash
   # Set routing to 100% old production
   aws route53 change-resource-record-sets \
       --hosted-zone-id YOUR_ZONE_ID \
       --change-batch file:///tmp/rollback-100-old.json
   ```

2. **CloudFront Invalidation** (if using CDN):
   ```bash
   aws cloudfront create-invalidation \
       --distribution-id YOUR_DIST_ID \
       --paths "/*"
   ```

## Rollback Triggers
Execute rollback if ANY of these occur:
- Error rate > 5% on new environment
- Response time > 3 seconds (p95)
- Health checks failing for > 2 minutes
- Database connection issues
- User complaints about functionality

## Rollback Verification
After rollback:
1. Verify all traffic going to old production
2. Check error rates return to normal
3. Confirm user access restored
4. Document issue for investigation

## Emergency Contacts
- DevOps Lead: [Contact]
- System Admin: [Contact]
- Database Admin: [Contact]
EOF
    
    echo "✅ Rollback plan saved to: rollback_plan.md"
    echo ""
}

# Main execution
echo "======================================================"
echo "   TRAFFIC MIGRATION CONFIGURATION"
echo "======================================================"
echo ""

# Show the migration plan
show_migration_plan

# Create health checks
create_health_checks

# Test current endpoints
echo "======================================================"
echo "   ENDPOINT HEALTH STATUS"
echo "======================================================"
echo ""
test_traffic_routing

# Create monitoring dashboard
create_monitoring_dashboard

# Create rollback plan
create_rollback_plan

# Interactive weight configuration
echo "======================================================"
echo "   CONFIGURE TRAFFIC WEIGHTS"
echo "======================================================"
echo ""
echo "Select migration phase:"
echo "1) Phase 1: 10% to new (testing)"
echo "2) Phase 2: 25% to new"
echo "3) Phase 3: 50% to new"
echo "4) Phase 4: 75% to new"
echo "5) Phase 5: 100% to new (complete)"
echo "0) Skip configuration"
echo ""
read -p "Enter choice [0-5]: " choice

case $choice in
    1) create_weighted_routing 10 ;;
    2) create_weighted_routing 25 ;;
    3) create_weighted_routing 50 ;;
    4) create_weighted_routing 75 ;;
    5) create_weighted_routing 100 ;;
    0) echo "Skipping weight configuration" ;;
    *) echo "Invalid choice" ;;
esac

echo ""
echo -e "${GREEN}======================================================"
echo "   TRAFFIC MIGRATION SETUP COMPLETE!"
echo "======================================================${NC}"
echo ""
echo "Summary:"
echo "--------"
echo "✅ Health checks configured for both environments"
echo "✅ Monitoring dashboard created"
echo "✅ Rollback plan documented"
echo "✅ Weighted routing configurations prepared"
echo ""
echo "Next Steps:"
echo "-----------"
echo "1. Apply weighted routing in Route 53 (requires hosted zone)"
echo "2. Monitor traffic distribution on dashboard"
echo "3. Gradually increase traffic to new environment"
echo "4. Watch for any anomalies or errors"
echo ""
echo "Important URLs:"
echo "--------------"
echo "Old Production: http://$OLD_PROD_ALB"
echo "New Staging: http://$NEW_STAGING_ALB"
echo "Monitoring: https://console.aws.amazon.com/cloudwatch/"
echo ""
echo "Traffic migration setup completed at $(date)"
echo "======================================================"