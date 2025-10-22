#!/bin/bash

# =====================================================
# ChatMRPT Staging Environment Health Check
# =====================================================
# Purpose: Comprehensive health check for staging environment
# Date: August 27, 2025
# =====================================================

set -e

# Configuration
KEY_PATH="/tmp/chatmrpt-key2.pem"
INSTANCE1_IP="3.21.167.170"
INSTANCE2_IP="18.220.103.20"
ALB_URL="http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
REDIS_ENDPOINT="chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "======================================================"
echo "   CHATMRPT STAGING HEALTH CHECK"
echo "   $(date)"
echo "======================================================"
echo ""

# Function to check instance health
check_instance() {
    local ip=$1
    local name=$2
    
    echo -e "${YELLOW}Checking $name ($ip)...${NC}"
    echo "----------------------------------------"
    
    # Check SSH connectivity
    if ssh -o ConnectTimeout=5 -i $KEY_PATH ec2-user@$ip 'echo "SSH: OK"' 2>/dev/null; then
        echo -e "${GREEN}✅ SSH Connection: OK${NC}"
    else
        echo -e "${RED}❌ SSH Connection: FAILED${NC}"
        return 1
    fi
    
    # Check service status
    SERVICE_STATUS=$(ssh -i $KEY_PATH ec2-user@$ip 'sudo systemctl is-active chatmrpt' 2>/dev/null || echo "inactive")
    if [ "$SERVICE_STATUS" = "active" ]; then
        echo -e "${GREEN}✅ ChatMRPT Service: ACTIVE${NC}"
    else
        echo -e "${RED}❌ ChatMRPT Service: $SERVICE_STATUS${NC}"
    fi
    
    # Check Gunicorn workers
    WORKER_COUNT=$(ssh -i $KEY_PATH ec2-user@$ip 'ps aux | grep gunicorn | grep -v grep | wc -l' 2>/dev/null || echo "0")
    if [ "$WORKER_COUNT" -gt "0" ]; then
        echo -e "${GREEN}✅ Gunicorn Workers: $WORKER_COUNT active${NC}"
    else
        echo -e "${RED}❌ Gunicorn Workers: None running${NC}"
    fi
    
    # Check disk usage
    DISK_USAGE=$(ssh -i $KEY_PATH ec2-user@$ip 'df -h / | awk "NR==2 {print \$5}"' 2>/dev/null || echo "Unknown")
    DISK_PCT=${DISK_USAGE%\%}
    if [ "$DISK_PCT" != "Unknown" ] && [ "$DISK_PCT" -lt "80" ]; then
        echo -e "${GREEN}✅ Disk Usage: $DISK_USAGE${NC}"
    elif [ "$DISK_PCT" != "Unknown" ]; then
        echo -e "${YELLOW}⚠️  Disk Usage: $DISK_USAGE (High)${NC}"
    else
        echo -e "${RED}❌ Disk Usage: Unknown${NC}"
    fi
    
    # Check memory usage
    MEM_USAGE=$(ssh -i $KEY_PATH ec2-user@$ip 'free -m | awk "NR==2 {printf \"%.1f%%\", \$3*100/\$2}"' 2>/dev/null || echo "Unknown")
    echo -e "   Memory Usage: $MEM_USAGE"
    
    # Check CPU load
    CPU_LOAD=$(ssh -i $KEY_PATH ec2-user@$ip 'uptime | awk -F"load average:" "{print \$2}"' 2>/dev/null || echo "Unknown")
    echo -e "   CPU Load: $CPU_LOAD"
    
    # Check Redis connectivity from instance
    REDIS_CHECK=$(ssh -i $KEY_PATH ec2-user@$ip "redis-cli -h $REDIS_ENDPOINT ping 2>/dev/null" || echo "Failed")
    if [ "$REDIS_CHECK" = "PONG" ]; then
        echo -e "${GREEN}✅ Redis Connection: OK${NC}"
    else
        echo -e "${RED}❌ Redis Connection: Failed${NC}"
    fi
    
    echo ""
}

# Function to check ALB health
check_alb() {
    echo -e "${YELLOW}Checking Application Load Balancer...${NC}"
    echo "----------------------------------------"
    
    # Check ALB endpoint
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$ALB_URL/ping" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✅ ALB Health Check: OK (HTTP $HTTP_CODE)${NC}"
    else
        echo -e "${RED}❌ ALB Health Check: Failed (HTTP $HTTP_CODE)${NC}"
    fi
    
    # Check response time
    RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" --max-time 10 "$ALB_URL/ping" 2>/dev/null || echo "timeout")
    if [ "$RESPONSE_TIME" != "timeout" ]; then
        echo "   Response Time: ${RESPONSE_TIME}s"
    fi
    
    # Test main page
    MAIN_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$ALB_URL/" 2>/dev/null || echo "000")
    if [ "$MAIN_CODE" = "200" ]; then
        echo -e "${GREEN}✅ Main Page: OK (HTTP $MAIN_CODE)${NC}"
    else
        echo -e "${RED}❌ Main Page: Failed (HTTP $MAIN_CODE)${NC}"
    fi
    
    echo ""
}

# Function to check AWS resources
check_aws_resources() {
    echo -e "${YELLOW}Checking AWS Resources...${NC}"
    echo "----------------------------------------"
    
    # Check target group health via AWS
    ssh -i $KEY_PATH ec2-user@$INSTANCE1_IP << 'EOF' 2>/dev/null || echo "AWS check failed"
        export AWS_DEFAULT_REGION=us-east-2
        
        # Get target health
        echo "Target Group Health:"
        aws elbv2 describe-target-health \
            --target-group-arn arn:aws:elasticloadbalancing:us-east-2:008239714173:targetgroup/chatmrpt-staging-targets/dc7f0a7e27d6e7f2 \
            --query 'TargetHealthDescriptions[*].[Target.Id,TargetHealth.State]' \
            --output table 2>/dev/null || echo "  Unable to check target health"
        
        # Check Redis cluster status
        echo ""
        echo "Redis Cluster Status:"
        aws elasticache describe-cache-clusters \
            --cache-cluster-id chatmrpt-redis-staging \
            --show-cache-node-info \
            --query 'CacheClusters[0].CacheClusterStatus' \
            --output text 2>/dev/null || echo "  Unable to check Redis status"
EOF
    
    echo ""
}

# Function to generate summary
generate_summary() {
    echo "======================================================"
    echo "   HEALTH CHECK SUMMARY"
    echo "======================================================"
    
    # Count issues
    ISSUES=0
    
    # Re-check critical components for summary
    SSH1=$(ssh -o ConnectTimeout=5 -i $KEY_PATH ec2-user@$INSTANCE1_IP 'echo "OK"' 2>/dev/null || echo "FAIL")
    SSH2=$(ssh -o ConnectTimeout=5 -i $KEY_PATH ec2-user@$INSTANCE2_IP 'echo "OK"' 2>/dev/null || echo "FAIL")
    ALB=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$ALB_URL/ping" 2>/dev/null || echo "000")
    
    if [ "$SSH1" != "OK" ]; then ((ISSUES++)); fi
    if [ "$SSH2" != "OK" ]; then ((ISSUES++)); fi
    if [ "$ALB" != "200" ]; then ((ISSUES++)); fi
    
    if [ $ISSUES -eq 0 ]; then
        echo -e "${GREEN}✅ STAGING ENVIRONMENT: HEALTHY${NC}"
        echo "   All critical components are operational"
    elif [ $ISSUES -lt 2 ]; then
        echo -e "${YELLOW}⚠️  STAGING ENVIRONMENT: DEGRADED${NC}"
        echo "   Some components need attention"
    else
        echo -e "${RED}❌ STAGING ENVIRONMENT: CRITICAL${NC}"
        echo "   Multiple components are failing"
    fi
    
    echo ""
    echo "Recommendations:"
    if [ $ISSUES -eq 0 ]; then
        echo "- Environment is ready for production workload"
        echo "- Continue with Phase 1 implementation"
    else
        echo "- Fix identified issues before proceeding"
        echo "- Check logs for detailed error information"
        echo "- Verify security group configurations"
    fi
    
    echo "======================================================"
}

# Main execution
check_instance $INSTANCE1_IP "Instance 1"
check_instance $INSTANCE2_IP "Instance 2"
check_alb
check_aws_resources
generate_summary

echo ""
echo "Health check completed at $(date)"