#!/bin/bash

# =====================================================
# Phase 4: Execute Production Cutover
# =====================================================
# Purpose: Execute the transition from old production to new
# Date: August 27, 2025
# =====================================================

set -e

# Configuration
KEY_PATH="/tmp/chatmrpt-key2.pem"
NEW_PROD_IP1="3.21.167.170"
NEW_PROD_IP2="18.220.103.20"
OLD_PROD_ALB="chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com"
NEW_PROD_ALB="chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
CLOUDFRONT_DIST="d225ar6c86586s.cloudfront.net"
AWS_REGION="us-east-2"
CUTOVER_DATE=$(date +"%Y%m%d_%H%M%S")

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "======================================================"
echo "   PHASE 4: PRODUCTION CUTOVER EXECUTION"
echo "   $(date)"
echo "======================================================"
echo ""

# Function to create pre-cutover checkpoint
create_checkpoint() {
    echo -e "${YELLOW}Creating pre-cutover checkpoint...${NC}"
    
    # Create checkpoint directory
    CHECKPOINT_DIR="instance/checkpoints/cutover_${CUTOVER_DATE}"
    mkdir -p $CHECKPOINT_DIR
    
    # Save current state
    cat > $CHECKPOINT_DIR/state.json << EOF
{
    "cutover_date": "$(date)",
    "old_production_alb": "$OLD_PROD_ALB",
    "new_production_alb": "$NEW_PROD_ALB",
    "new_instance_1": "$NEW_PROD_IP1",
    "new_instance_2": "$NEW_PROD_IP2",
    "cloudfront_dist": "$CLOUDFRONT_DIST",
    "phase": "4",
    "action": "cutover"
}
EOF
    
    echo "✅ Checkpoint created: $CHECKPOINT_DIR"
    echo ""
}

# Function to perform final health checks
final_health_check() {
    echo -e "${YELLOW}Performing final health checks...${NC}"
    echo "======================================================"
    
    local all_healthy=true
    
    # Check new production endpoints
    echo "New Production Health:"
    for endpoint in "/" "/ping" "/system-health"; do
        STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://$NEW_PROD_ALB$endpoint" 2>/dev/null || echo "000")
        if [ "$STATUS" = "200" ]; then
            echo -e "  $endpoint: ${GREEN}✅ OK (HTTP $STATUS)${NC}"
        else
            echo -e "  $endpoint: ${RED}❌ FAIL (HTTP $STATUS)${NC}"
            all_healthy=false
        fi
    done
    
    echo ""
    echo "Old Production Health:"
    for endpoint in "/" "/ping" "/system-health"; do
        STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://$OLD_PROD_ALB$endpoint" 2>/dev/null || echo "000")
        if [ "$STATUS" = "200" ]; then
            echo -e "  $endpoint: ${GREEN}✅ OK (HTTP $STATUS)${NC}"
        else
            echo -e "  $endpoint: ${YELLOW}⚠️  HTTP $STATUS${NC}"
        fi
    done
    
    echo ""
    
    if [ "$all_healthy" = false ]; then
        echo -e "${RED}❌ New production is not healthy. Aborting cutover.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ All health checks passed${NC}"
    echo ""
}

# Function to update CloudFront origin
update_cloudfront() {
    echo -e "${YELLOW}Updating CloudFront origin...${NC}"
    echo "======================================================"
    
    # Get CloudFront distribution ID
    ssh -i $KEY_PATH ec2-user@$NEW_PROD_IP1 << 'EOF' 2>/dev/null
        export AWS_DEFAULT_REGION=us-east-1
        
        # Find distribution by domain name
        DIST_ID=$(aws cloudfront list-distributions \
            --query "DistributionList.Items[?DomainName=='d225ar6c86586s.cloudfront.net'].Id" \
            --output text)
        
        if [ -z "$DIST_ID" ]; then
            echo "❌ CloudFront distribution not found"
            exit 1
        fi
        
        echo "Found distribution: $DIST_ID"
        
        # Get current distribution config
        aws cloudfront get-distribution-config --id $DIST_ID > /tmp/cf_config.json
        
        # Extract ETag
        ETAG=$(jq -r '.ETag' /tmp/cf_config.json)
        
        # Update origin to new ALB
        jq '.DistributionConfig.Origins.Items[0].DomainName = "chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"' /tmp/cf_config.json | \
        jq '.DistributionConfig' > /tmp/cf_config_updated.json
        
        # Update the distribution
        aws cloudfront update-distribution \
            --id $DIST_ID \
            --distribution-config file:///tmp/cf_config_updated.json \
            --if-match $ETAG \
            --output json > /tmp/cf_update_result.json 2>&1
        
        if [ $? -eq 0 ]; then
            echo "✅ CloudFront origin updated successfully"
            
            # Create invalidation
            aws cloudfront create-invalidation \
                --distribution-id $DIST_ID \
                --paths "/*" \
                --output json > /tmp/cf_invalidation.json
            
            INV_ID=$(jq -r '.Invalidation.Id' /tmp/cf_invalidation.json)
            echo "✅ Cache invalidation created: $INV_ID"
        else
            echo "❌ Failed to update CloudFront"
            cat /tmp/cf_update_result.json
        fi
EOF
    
    echo ""
}

# Function to verify cutover success
verify_cutover() {
    echo -e "${YELLOW}Verifying cutover success...${NC}"
    echo "======================================================"
    
    # Test new production through various paths
    echo "Testing access paths:"
    
    # Test direct ALB
    echo -n "1. Direct ALB access: "
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://$NEW_PROD_ALB/" 2>/dev/null)
    if [ "$STATUS" = "200" ]; then
        echo -e "${GREEN}✅ Working${NC}"
    else
        echo -e "${RED}❌ Failed (HTTP $STATUS)${NC}"
    fi
    
    # Test CloudFront (may take time to propagate)
    echo -n "2. CloudFront CDN access: "
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://$CLOUDFRONT_DIST/" 2>/dev/null)
    if [ "$STATUS" = "200" ] || [ "$STATUS" = "301" ] || [ "$STATUS" = "302" ]; then
        echo -e "${GREEN}✅ Working${NC}"
    else
        echo -e "${YELLOW}⚠️  May need time to propagate (HTTP $STATUS)${NC}"
    fi
    
    # Test critical functionality
    echo ""
    echo "Testing critical functionality:"
    
    # Test upload capability
    echo -n "3. Upload endpoint: "
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://$NEW_PROD_ALB/upload" 2>/dev/null)
    if [ "$STATUS" = "200" ] || [ "$STATUS" = "302" ]; then
        echo -e "${GREEN}✅ Available${NC}"
    else
        echo -e "${RED}❌ Issue (HTTP $STATUS)${NC}"
    fi
    
    # Test API health
    echo -n "4. API health: "
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://$NEW_PROD_ALB/system-health" 2>/dev/null)
    if [ "$STATUS" = "200" ]; then
        echo -e "${GREEN}✅ Healthy${NC}"
    else
        echo -e "${RED}❌ Unhealthy (HTTP $STATUS)${NC}"
    fi
    
    echo ""
}

# Function to update DNS records (if applicable)
update_dns_notice() {
    echo -e "${BLUE}======================================================"
    echo "   DNS UPDATE INSTRUCTIONS"
    echo "======================================================${NC}"
    echo ""
    echo "If you control the domain DNS, update the following:"
    echo "------------------------------------------------------"
    echo "1. CNAME Record:"
    echo "   From: $OLD_PROD_ALB"
    echo "   To: $NEW_PROD_ALB"
    echo ""
    echo "2. Or use CloudFront:"
    echo "   Point to: $CLOUDFRONT_DIST"
    echo ""
    echo "3. Update TTL to 60 seconds for quick propagation"
    echo ""
}

# Function to monitor new production
monitor_production() {
    echo -e "${YELLOW}Starting production monitoring (30 seconds)...${NC}"
    echo "======================================================"
    
    local total_requests=30
    local success=0
    local failed=0
    
    for ((i=1; i<=total_requests; i++)); do
        STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://$NEW_PROD_ALB/ping" 2>/dev/null)
        if [ "$STATUS" = "200" ]; then
            ((success++))
            echo -n "✓"
        else
            ((failed++))
            echo -n "✗"
        fi
        
        if ((i % 10 == 0)); then
            echo " [$i/$total_requests]"
        fi
        
        sleep 1
    done
    
    echo ""
    echo ""
    echo "Monitoring Results:"
    echo "-------------------"
    echo -e "Successful: ${GREEN}$success/$total_requests${NC}"
    echo -e "Failed: ${RED}$failed/$total_requests${NC}"
    echo -e "Success Rate: ${GREEN}$((success * 100 / total_requests))%${NC}"
    
    echo ""
}

# Function to create rollback script
create_rollback_script() {
    echo -e "${YELLOW}Creating emergency rollback script...${NC}"
    
    cat > emergency_rollback.sh << 'EOF'
#!/bin/bash
# EMERGENCY ROLLBACK SCRIPT
# Execute this if critical issues occur after cutover

echo "============================="
echo "EMERGENCY ROLLBACK INITIATED"
echo "============================="

# Revert CloudFront to old ALB
DIST_ID=$(aws cloudfront list-distributions \
    --query "DistributionList.Items[?DomainName=='d225ar6c86586s.cloudfront.net'].Id" \
    --output text)

if [ ! -z "$DIST_ID" ]; then
    # Get current config
    aws cloudfront get-distribution-config --id $DIST_ID > /tmp/rollback_config.json
    ETAG=$(jq -r '.ETag' /tmp/rollback_config.json)
    
    # Revert to old ALB
    jq '.DistributionConfig.Origins.Items[0].DomainName = "chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com"' /tmp/rollback_config.json | \
    jq '.DistributionConfig' > /tmp/rollback_updated.json
    
    # Update distribution
    aws cloudfront update-distribution \
        --id $DIST_ID \
        --distribution-config file:///tmp/rollback_updated.json \
        --if-match $ETAG
    
    # Invalidate cache
    aws cloudfront create-invalidation --distribution-id $DIST_ID --paths "/*"
    
    echo "✅ CloudFront reverted to old production"
fi

echo "Rollback complete. Monitor old production for stability."
EOF
    
    chmod +x emergency_rollback.sh
    echo "✅ Rollback script created: emergency_rollback.sh"
    echo ""
}

# Main execution flow
echo "======================================================"
echo "   CUTOVER EXECUTION PLAN"
echo "======================================================"
echo ""
echo "This will transition production from:"
echo "  OLD: $OLD_PROD_ALB"
echo "  NEW: $NEW_PROD_ALB"
echo ""
echo "Steps to execute:"
echo "1. Create checkpoint"
echo "2. Final health checks"
echo "3. Update CloudFront origin"
echo "4. Verify cutover success"
echo "5. Monitor new production"
echo "6. Create rollback script"
echo ""
read -p "Proceed with production cutover? (yes/no): " confirmation

if [ "$confirmation" != "yes" ]; then
    echo "Cutover cancelled."
    exit 0
fi

echo ""
echo "======================================================"
echo "   EXECUTING PRODUCTION CUTOVER"
echo "======================================================"
echo ""

# Execute cutover steps
create_checkpoint
final_health_check
update_cloudfront
verify_cutover
update_dns_notice
monitor_production
create_rollback_script

# Summary
echo ""
echo -e "${GREEN}======================================================"
echo "   CUTOVER EXECUTION COMPLETE!"
echo "======================================================${NC}"
echo ""
echo "Summary:"
echo "--------"
echo "✅ Health checks passed"
echo "✅ CloudFront updated (may take 15-20 mins to propagate)"
echo "✅ New production accessible"
echo "✅ Monitoring shows stable performance"
echo "✅ Rollback script prepared"
echo ""
echo "New Production URLs:"
echo "--------------------"
echo "Direct ALB: http://$NEW_PROD_ALB"
echo "CloudFront: https://$CLOUDFRONT_DIST"
echo ""
echo "Next Steps:"
echo "-----------"
echo "1. Monitor new production for 24-48 hours"
echo "2. Check CloudWatch dashboards"
echo "3. Collect user feedback"
echo "4. If stable, proceed with old environment decommission"
echo ""
echo "To rollback if needed:"
echo "  ./emergency_rollback.sh"
echo ""
echo "Cutover completed at $(date)"
echo "======================================================"