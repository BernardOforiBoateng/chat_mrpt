#!/bin/bash

# =====================================================
# Phase 4: New Production Monitoring
# =====================================================
# Purpose: Monitor new production environment post-cutover
# Date: August 27, 2025
# =====================================================

set -e

# Configuration
KEY_PATH="/tmp/chatmrpt-key2.pem"
NEW_PROD_IP1="3.21.167.170"
NEW_PROD_IP2="18.220.103.20"
NEW_PROD_ALB="chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
CLOUDFRONT_DIST="https://d225ar6c86586s.cloudfront.net"
AWS_REGION="us-east-2"
MONITOR_DURATION=300  # 5 minutes default

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "======================================================"
echo "   NEW PRODUCTION MONITORING DASHBOARD"
echo "   $(date)"
echo "======================================================"
echo ""

# Function to check instance health
check_instance_health() {
    local ip=$1
    local name=$2
    
    echo -e "${YELLOW}Checking $name ($ip)...${NC}"
    
    # Check if instance is reachable
    if ssh -i $KEY_PATH -o ConnectTimeout=5 ec2-user@$ip 'echo "connected"' &>/dev/null; then
        echo -e "  Connectivity: ${GREEN}✅ OK${NC}"
        
        # Check service status
        SERVICE_STATUS=$(ssh -i $KEY_PATH ec2-user@$ip 'sudo systemctl is-active chatmrpt' 2>/dev/null || echo "inactive")
        if [ "$SERVICE_STATUS" = "active" ]; then
            echo -e "  Service: ${GREEN}✅ Running${NC}"
        else
            echo -e "  Service: ${RED}❌ $SERVICE_STATUS${NC}"
        fi
        
        # Check worker count
        WORKERS=$(ssh -i $KEY_PATH ec2-user@$ip 'ps aux | grep gunicorn | grep -v grep | wc -l' 2>/dev/null || echo "0")
        echo "  Workers: $WORKERS active"
        
        # Check memory usage
        MEM_USAGE=$(ssh -i $KEY_PATH ec2-user@$ip 'free -m | grep Mem | awk "{printf \"%.1f%%\", \$3/\$2 * 100}"' 2>/dev/null)
        echo "  Memory: $MEM_USAGE used"
        
        # Check disk usage
        DISK_USAGE=$(ssh -i $KEY_PATH ec2-user@$ip 'df -h / | tail -1 | awk "{print \$5}"' 2>/dev/null)
        echo "  Disk: $DISK_USAGE used"
        
    else
        echo -e "  Connectivity: ${RED}❌ UNREACHABLE${NC}"
    fi
    
    echo ""
}

# Function to monitor endpoints
monitor_endpoints() {
    echo -e "${YELLOW}Endpoint Monitoring...${NC}"
    echo "======================================================"
    
    local endpoints=(
        "/" "Homepage"
        "/ping" "Health"
        "/system-health" "System"
        "/upload" "Upload"
    )
    
    for ((i=0; i<${#endpoints[@]}; i+=2)); do
        local endpoint="${endpoints[i]}"
        local name="${endpoints[i+1]}"
        
        # Test response time and status
        local start_time=$(date +%s%N)
        local status=$(curl -s -o /dev/null -w "%{http_code}" "http://$NEW_PROD_ALB$endpoint" 2>/dev/null || echo "000")
        local end_time=$(date +%s%N)
        local response_time=$(((end_time - start_time) / 1000000))
        
        printf "%-15s: " "$name"
        
        if [ "$status" = "200" ] || [ "$status" = "302" ]; then
            echo -e "HTTP $status ${GREEN}✅${NC} (${response_time}ms)"
        else
            echo -e "HTTP $status ${RED}❌${NC}"
        fi
    done
    
    echo ""
}

# Function to check Redis connectivity
check_redis() {
    echo -e "${YELLOW}Redis Cache Status...${NC}"
    echo "======================================================"
    
    ssh -i $KEY_PATH ec2-user@$NEW_PROD_IP1 << 'EOF' 2>/dev/null
        REDIS_HOST="chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com"
        
        # Test Redis ping
        REDIS_PING=$(redis-cli -h $REDIS_HOST ping 2>/dev/null || echo "FAIL")
        if [ "$REDIS_PING" = "PONG" ]; then
            echo -e "  Connection: ✅ Connected"
            
            # Get memory usage
            MEM_USED=$(redis-cli -h $REDIS_HOST info memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
            echo "  Memory Used: $MEM_USED"
            
            # Get key count
            KEY_COUNT=$(redis-cli -h $REDIS_HOST dbsize | awk '{print $2}')
            echo "  Total Keys: $KEY_COUNT"
        else
            echo -e "  Connection: ❌ Failed"
        fi
EOF
    
    echo ""
}

# Function to monitor CloudWatch metrics
monitor_cloudwatch() {
    echo -e "${YELLOW}CloudWatch Metrics (Last 5 minutes)...${NC}"
    echo "======================================================"
    
    ssh -i $KEY_PATH ec2-user@$NEW_PROD_IP1 << 'EOF' 2>/dev/null
        export AWS_DEFAULT_REGION=us-east-2
        
        # Get ALB request count
        END_TIME=$(date -u +"%Y-%m-%dT%H:%M:%S")
        START_TIME=$(date -u -d '5 minutes ago' +"%Y-%m-%dT%H:%M:%S")
        
        # Target group ARN suffix for metrics
        TG_ARN_SUFFIX="targetgroup/chatmrpt-staging-tg/7c4f7a9d59bc1e04"
        
        # Get request count
        REQUEST_COUNT=$(aws cloudwatch get-metric-statistics \
            --namespace AWS/ApplicationELB \
            --metric-name RequestCount \
            --dimensions Name=TargetGroup,Value=$TG_ARN_SUFFIX \
            --start-time $START_TIME \
            --end-time $END_TIME \
            --period 300 \
            --statistics Sum \
            --query 'Datapoints[0].Sum' \
            --output text 2>/dev/null || echo "N/A")
        
        echo "  Request Count: $REQUEST_COUNT"
        
        # Get average response time
        RESPONSE_TIME=$(aws cloudwatch get-metric-statistics \
            --namespace AWS/ApplicationELB \
            --metric-name TargetResponseTime \
            --dimensions Name=TargetGroup,Value=$TG_ARN_SUFFIX \
            --start-time $START_TIME \
            --end-time $END_TIME \
            --period 300 \
            --statistics Average \
            --query 'Datapoints[0].Average' \
            --output text 2>/dev/null || echo "N/A")
        
        if [ "$RESPONSE_TIME" != "N/A" ] && [ "$RESPONSE_TIME" != "None" ]; then
            RESPONSE_TIME=$(printf "%.3f" $RESPONSE_TIME)
            echo "  Avg Response Time: ${RESPONSE_TIME}s"
        else
            echo "  Avg Response Time: N/A"
        fi
        
        # Get error count
        ERROR_COUNT=$(aws cloudwatch get-metric-statistics \
            --namespace AWS/ApplicationELB \
            --metric-name HTTPCode_Target_5XX_Count \
            --dimensions Name=TargetGroup,Value=$TG_ARN_SUFFIX \
            --start-time $START_TIME \
            --end-time $END_TIME \
            --period 300 \
            --statistics Sum \
            --query 'Datapoints[0].Sum' \
            --output text 2>/dev/null || echo "0")
        
        if [ "$ERROR_COUNT" = "None" ]; then
            ERROR_COUNT="0"
        fi
        
        echo "  5XX Errors: $ERROR_COUNT"
EOF
    
    echo ""
}

# Function for continuous monitoring
continuous_monitor() {
    local duration=$1
    local interval=10  # Check every 10 seconds
    local iterations=$((duration / interval))
    
    echo -e "${BLUE}Starting continuous monitoring for ${duration} seconds...${NC}"
    echo ""
    
    # Initialize counters
    local total_checks=0
    local successful_checks=0
    local failed_checks=0
    local response_times=()
    
    for ((i=1; i<=iterations; i++)); do
        # Quick health check
        local start_time=$(date +%s%N)
        local status=$(curl -s -o /dev/null -w "%{http_code}" "http://$NEW_PROD_ALB/ping" 2>/dev/null || echo "000")
        local end_time=$(date +%s%N)
        local response_time=$(((end_time - start_time) / 1000000))
        
        ((total_checks++))
        
        if [ "$status" = "200" ]; then
            ((successful_checks++))
            response_times+=($response_time)
            echo -ne "\r[${GREEN}✓${NC}] Check $i/$iterations - Response: ${response_time}ms "
        else
            ((failed_checks++))
            echo -ne "\r[${RED}✗${NC}] Check $i/$iterations - Failed (HTTP $status) "
        fi
        
        sleep $interval
    done
    
    echo -e "\n"
    echo "Monitoring Summary:"
    echo "------------------"
    echo "Total Checks: $total_checks"
    echo -e "Successful: ${GREEN}$successful_checks${NC}"
    echo -e "Failed: ${RED}$failed_checks${NC}"
    
    if [ ${#response_times[@]} -gt 0 ]; then
        # Calculate average response time
        local sum=0
        for rt in "${response_times[@]}"; do
            sum=$((sum + rt))
        done
        local avg=$((sum / ${#response_times[@]}))
        echo "Average Response Time: ${avg}ms"
    fi
    
    local success_rate=$((successful_checks * 100 / total_checks))
    echo -e "Success Rate: ${GREEN}${success_rate}%${NC}"
    
    echo ""
}

# Function to check recent logs
check_recent_logs() {
    echo -e "${YELLOW}Recent Application Logs...${NC}"
    echo "======================================================"
    
    ssh -i $KEY_PATH ec2-user@$NEW_PROD_IP1 << 'EOF' 2>/dev/null
        # Check for recent errors
        ERROR_COUNT=$(sudo journalctl -u chatmrpt -n 100 --no-pager | grep -c ERROR || echo "0")
        WARNING_COUNT=$(sudo journalctl -u chatmrpt -n 100 --no-pager | grep -c WARNING || echo "0")
        
        echo "  Errors (last 100 lines): $ERROR_COUNT"
        echo "  Warnings (last 100 lines): $WARNING_COUNT"
        
        # Show last 5 error messages if any
        if [ "$ERROR_COUNT" -gt 0 ]; then
            echo ""
            echo "  Recent errors:"
            sudo journalctl -u chatmrpt -n 100 --no-pager | grep ERROR | tail -5 | sed 's/^/    /'
        fi
EOF
    
    echo ""
}

# Function to generate monitoring report
generate_report() {
    local report_file="production_monitoring_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "======================================================"
        echo "NEW PRODUCTION MONITORING REPORT"
        echo "Generated: $(date)"
        echo "======================================================"
        echo ""
        echo "Environment:"
        echo "  ALB: $NEW_PROD_ALB"
        echo "  Instance 1: $NEW_PROD_IP1"
        echo "  Instance 2: $NEW_PROD_IP2"
        echo "  CloudFront: $CLOUDFRONT_DIST"
        echo ""
        
        # Run all checks and capture output
        check_instance_health $NEW_PROD_IP1 "Instance 1"
        check_instance_health $NEW_PROD_IP2 "Instance 2"
        monitor_endpoints
        check_redis
        monitor_cloudwatch
        check_recent_logs
        
    } | tee $report_file
    
    echo ""
    echo "Report saved to: $report_file"
}

# Main menu
show_menu() {
    echo "Select monitoring option:"
    echo "========================="
    echo "1) Quick Status Check"
    echo "2) Full System Check"
    echo "3) Continuous Monitoring (5 minutes)"
    echo "4) Custom Duration Monitoring"
    echo "5) Generate Full Report"
    echo "0) Exit"
    echo ""
}

# Main execution
while true; do
    clear
    echo "======================================================"
    echo "   NEW PRODUCTION MONITORING DASHBOARD"
    echo "======================================================"
    echo ""
    
    show_menu
    read -p "Enter choice [0-5]: " choice
    
    case $choice in
        1)
            echo ""
            monitor_endpoints
            ;;
        2)
            echo ""
            check_instance_health $NEW_PROD_IP1 "Instance 1"
            check_instance_health $NEW_PROD_IP2 "Instance 2"
            monitor_endpoints
            check_redis
            monitor_cloudwatch
            check_recent_logs
            ;;
        3)
            echo ""
            continuous_monitor 300
            ;;
        4)
            read -p "Enter duration in seconds: " custom_duration
            echo ""
            continuous_monitor $custom_duration
            ;;
        5)
            echo ""
            generate_report
            ;;
        0)
            echo "Exiting monitoring dashboard..."
            exit 0
            ;;
        *)
            echo "Invalid option"
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
done