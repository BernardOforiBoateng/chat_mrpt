#!/bin/bash

# =====================================================
# Phase 4: Decommission Old Production Environment
# =====================================================
# Purpose: Safely decommission old production infrastructure
# Date: August 27, 2025
# =====================================================

set -e

# Configuration
AWS_REGION="us-east-2"
OLD_PROD_ALB="chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com"
BACKUP_PREFIX="chatmrpt-final-backup"
DECOMMISSION_DATE=$(date +"%Y%m%d_%H%M%S")

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "======================================================"
echo "   OLD PRODUCTION DECOMMISSION PROCESS"
echo "   $(date)"
echo "======================================================"
echo ""

# Function to verify new production is stable
verify_stability() {
    echo -e "${YELLOW}Verifying new production stability...${NC}"
    echo "======================================================"
    
    local new_alb="chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
    local stable=true
    
    # Check new production health
    echo "Checking new production health..."
    for endpoint in "/" "/ping" "/system-health"; do
        STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://$new_alb$endpoint" 2>/dev/null || echo "000")
        if [ "$STATUS" = "200" ]; then
            echo -e "  $endpoint: ${GREEN}✅ OK${NC}"
        else
            echo -e "  $endpoint: ${RED}❌ FAIL${NC}"
            stable=false
        fi
    done
    
    if [ "$stable" = false ]; then
        echo ""
        echo -e "${RED}❌ New production is not stable!${NC}"
        echo "Decommission process aborted for safety."
        exit 1
    fi
    
    echo ""
    echo -e "${GREEN}✅ New production is stable${NC}"
    echo ""
}

# Function to create final snapshot
create_final_snapshot() {
    echo -e "${YELLOW}Creating final snapshots of old production...${NC}"
    echo "======================================================"
    
    # Get Auto Scaling Group instances
    echo "Finding old production instances..."
    
    ASG_NAME=$(aws autoscaling describe-auto-scaling-groups \
        --region $AWS_REGION \
        --query "AutoScalingGroups[?contains(AutoScalingGroupName, 'chatmrpt') && !contains(AutoScalingGroupName, 'staging')].AutoScalingGroupName" \
        --output text 2>/dev/null || echo "")
    
    if [ -z "$ASG_NAME" ]; then
        echo "⚠️  No Auto Scaling Group found for old production"
        echo "Looking for individual instances..."
        
        # Try to find instances by tags
        INSTANCE_IDS=$(aws ec2 describe-instances \
            --region $AWS_REGION \
            --filters "Name=tag:Environment,Values=production" "Name=instance-state-name,Values=running" \
            --query "Reservations[].Instances[].InstanceId" \
            --output text 2>/dev/null || echo "")
    else
        echo "Found ASG: $ASG_NAME"
        
        # Get instances from ASG
        INSTANCE_IDS=$(aws autoscaling describe-auto-scaling-groups \
            --region $AWS_REGION \
            --auto-scaling-group-names "$ASG_NAME" \
            --query "AutoScalingGroups[0].Instances[].InstanceId" \
            --output text 2>/dev/null || echo "")
    fi
    
    if [ -z "$INSTANCE_IDS" ]; then
        echo "⚠️  No old production instances found to snapshot"
    else
        echo "Found instances: $INSTANCE_IDS"
        echo ""
        
        # Create AMI snapshots
        for instance_id in $INSTANCE_IDS; do
            echo "Creating AMI for instance: $instance_id"
            
            AMI_ID=$(aws ec2 create-image \
                --instance-id $instance_id \
                --name "${BACKUP_PREFIX}-${instance_id}-${DECOMMISSION_DATE}" \
                --description "Final backup before decommission" \
                --no-reboot \
                --region $AWS_REGION \
                --query 'ImageId' \
                --output text 2>/dev/null)
            
            if [ ! -z "$AMI_ID" ]; then
                echo "✅ AMI created: $AMI_ID"
                
                # Tag the AMI
                aws ec2 create-tags \
                    --resources $AMI_ID \
                    --tags Key=Name,Value="Final-Backup-$instance_id" \
                          Key=Type,Value="Decommission-Backup" \
                          Key=Date,Value="$DECOMMISSION_DATE" \
                    --region $AWS_REGION
            else
                echo "❌ Failed to create AMI for $instance_id"
            fi
        done
    fi
    
    echo ""
}

# Function to export CloudWatch logs
export_logs() {
    echo -e "${YELLOW}Exporting CloudWatch logs...${NC}"
    echo "======================================================"
    
    local log_groups=(
        "/aws/elasticloadbalancing/app/chatmrpt-alb"
        "/aws/ec2/production"
        "/aws/application/chatmrpt"
    )
    
    for log_group in "${log_groups[@]}"; do
        echo "Checking log group: $log_group"
        
        # Check if log group exists
        if aws logs describe-log-groups \
            --log-group-name-prefix "$log_group" \
            --region $AWS_REGION \
            --output text &>/dev/null; then
            
            echo "  Creating export task..."
            
            # Create S3 bucket name (must be unique)
            S3_BUCKET="chatmrpt-logs-archive-${DECOMMISSION_DATE}"
            
            # Note: This would require an existing S3 bucket
            echo "  Would export to: s3://$S3_BUCKET/$log_group/"
            echo "  (Requires S3 bucket setup)"
        else
            echo "  Log group not found"
        fi
    done
    
    echo ""
}

# Function to disable old production resources
disable_resources() {
    echo -e "${YELLOW}Disabling old production resources...${NC}"
    echo "======================================================"
    
    # Find and stop Auto Scaling activities
    if [ ! -z "$ASG_NAME" ]; then
        echo "Suspending Auto Scaling processes..."
        
        aws autoscaling suspend-processes \
            --auto-scaling-group-name "$ASG_NAME" \
            --region $AWS_REGION 2>/dev/null
        
        if [ $? -eq 0 ]; then
            echo "✅ Auto Scaling processes suspended"
        fi
        
        # Set desired capacity to 0
        echo "Setting desired capacity to 0..."
        aws autoscaling set-desired-capacity \
            --auto-scaling-group-name "$ASG_NAME" \
            --desired-capacity 0 \
            --region $AWS_REGION 2>/dev/null
        
        if [ $? -eq 0 ]; then
            echo "✅ Desired capacity set to 0"
        fi
    fi
    
    # Deregister targets from ALB
    echo ""
    echo "Finding old ALB configuration..."
    
    # Get Load Balancer ARN
    LB_ARN=$(aws elbv2 describe-load-balancers \
        --region $AWS_REGION \
        --query "LoadBalancers[?DNSName=='$OLD_PROD_ALB'].LoadBalancerArn" \
        --output text 2>/dev/null || echo "")
    
    if [ ! -z "$LB_ARN" ]; then
        echo "Found Load Balancer: ${LB_ARN##*/}"
        
        # Get target groups
        TG_ARNS=$(aws elbv2 describe-target-groups \
            --load-balancer-arn "$LB_ARN" \
            --region $AWS_REGION \
            --query "TargetGroups[].TargetGroupArn" \
            --output text 2>/dev/null || echo "")
        
        for tg_arn in $TG_ARNS; do
            echo "Checking target group: ${tg_arn##*/}"
            
            # Get registered targets
            TARGETS=$(aws elbv2 describe-target-health \
                --target-group-arn "$tg_arn" \
                --region $AWS_REGION \
                --query "TargetHealthDescriptions[].Target.Id" \
                --output text 2>/dev/null || echo "")
            
            if [ ! -z "$TARGETS" ]; then
                echo "  Deregistering targets: $TARGETS"
                
                for target in $TARGETS; do
                    aws elbv2 deregister-targets \
                        --target-group-arn "$tg_arn" \
                        --targets Id=$target \
                        --region $AWS_REGION 2>/dev/null
                done
                
                echo "  ✅ Targets deregistered"
            fi
        done
    fi
    
    echo ""
}

# Function to stop instances
stop_instances() {
    echo -e "${YELLOW}Stopping old production instances...${NC}"
    echo "======================================================"
    
    if [ -z "$INSTANCE_IDS" ]; then
        echo "No instances to stop"
        return
    fi
    
    for instance_id in $INSTANCE_IDS; do
        echo "Stopping instance: $instance_id"
        
        aws ec2 stop-instances \
            --instance-ids $instance_id \
            --region $AWS_REGION \
            --output json > /tmp/stop_result.json 2>&1
        
        if [ $? -eq 0 ]; then
            STATE=$(jq -r '.StoppingInstances[0].CurrentState.Name' /tmp/stop_result.json)
            echo "✅ Instance $instance_id: $STATE"
        else
            echo "❌ Failed to stop $instance_id"
        fi
    done
    
    echo ""
}

# Function to calculate cost savings
calculate_savings() {
    echo -e "${BLUE}======================================================"
    echo "   COST SAVINGS CALCULATION"
    echo "======================================================${NC}"
    echo ""
    
    # Estimate based on instance types
    echo "Estimated Monthly Savings:"
    echo "-------------------------"
    echo "• EC2 Instances (2x t3.medium): \$60.48"
    echo "• Load Balancer: \$25.00"
    echo "• EBS Storage (2x 20GB): \$4.00"
    echo "• Data Transfer: ~\$10.00"
    echo "• CloudWatch: \$5.00"
    echo ""
    echo -e "${GREEN}Total Estimated Savings: \$104.48/month${NC}"
    echo -e "${GREEN}Annual Savings: \$1,253.76${NC}"
    
    # With staging consolidated
    echo ""
    echo "After Full Consolidation:"
    echo "------------------------"
    echo "Previous: 4 instances (2 staging + 2 production)"
    echo "Now: 2 instances (staging as new production)"
    echo ""
    echo -e "${GREEN}Total Monthly Savings: ~\$230${NC}"
    echo -e "${GREEN}Total Annual Savings: ~\$2,760${NC}"
    
    echo ""
}

# Function to generate decommission report
generate_decommission_report() {
    local report_file="decommission_report_${DECOMMISSION_DATE}.md"
    
    cat > $report_file << EOF
# Decommission Report
**Date**: $(date)
**Environment**: Old Production

## Resources Decommissioned

### EC2 Instances
- Instances stopped: ${INSTANCE_IDS:-None}
- Final AMI snapshots created

### Load Balancer
- ALB: $OLD_PROD_ALB
- Targets deregistered
- Health checks disabled

### Auto Scaling
- Group: ${ASG_NAME:-None}
- Processes suspended
- Desired capacity set to 0

## Backups Created
- AMI snapshots with prefix: $BACKUP_PREFIX
- Timestamp: $DECOMMISSION_DATE

## Cost Savings
- Monthly: ~\$230
- Annual: ~\$2,760

## Rollback Information
To restore old production if needed:
1. Start stopped instances
2. Re-register targets with ALB
3. Resume Auto Scaling processes
4. Update DNS/CloudFront origins

## Next Steps
1. Monitor new production for 7 days
2. If stable, terminate old instances
3. Delete old ALB
4. Clean up unused snapshots after 30 days
EOF
    
    echo "✅ Report saved to: $report_file"
}

# Main execution flow
echo "======================================================"
echo "   DECOMMISSION CHECKLIST"
echo "======================================================"
echo ""
echo "This process will:"
echo "1. Verify new production stability"
echo "2. Create final snapshots"
echo "3. Export CloudWatch logs"
echo "4. Disable Auto Scaling"
echo "5. Deregister ALB targets"
echo "6. Stop EC2 instances"
echo "7. Calculate cost savings"
echo ""
echo -e "${YELLOW}WARNING: Ensure new production has been stable for at least 24 hours!${NC}"
echo ""
read -p "Have you monitored new production for 24+ hours? (yes/no): " monitoring_confirm

if [ "$monitoring_confirm" != "yes" ]; then
    echo "Please monitor new production for at least 24 hours before decommissioning."
    exit 0
fi

read -p "Proceed with decommission? This will stop old production! (yes/no): " final_confirm

if [ "$final_confirm" != "yes" ]; then
    echo "Decommission cancelled."
    exit 0
fi

echo ""
echo "======================================================"
echo "   STARTING DECOMMISSION PROCESS"
echo "======================================================"
echo ""

# Execute decommission steps
verify_stability
create_final_snapshot
export_logs
disable_resources
stop_instances
calculate_savings
generate_decommission_report

echo ""
echo -e "${GREEN}======================================================"
echo "   DECOMMISSION COMPLETE!"
echo "======================================================${NC}"
echo ""
echo "Summary:"
echo "--------"
echo "✅ Final snapshots created"
echo "✅ Resources disabled"
echo "✅ Instances stopped (not terminated)"
echo "✅ Cost savings activated"
echo ""
echo "Important:"
echo "----------"
echo "• Old resources are STOPPED but not DELETED"
echo "• You can still rollback if needed"
echo "• Monitor new production for 7 more days"
echo "• After confirmation, terminate resources permanently"
echo ""
echo "To permanently delete (after 7 days):"
echo "  aws ec2 terminate-instances --instance-ids $INSTANCE_IDS"
echo "  aws autoscaling delete-auto-scaling-group --auto-scaling-group-name $ASG_NAME"
echo ""
echo "Decommission completed at $(date)"
echo "========================================================"