#!/bin/bash

# =====================================================
# ChatMRPT Transition Monitoring Script
# =====================================================
# Purpose: Continuous monitoring during staging-to-production transition
# Date: August 27, 2025
# =====================================================

# Configuration
KEY_PATH="/tmp/chatmrpt-key2.pem"
INSTANCE1_IP="3.21.167.170"
INSTANCE2_IP="18.220.103.20"
ALB_URL="http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
LOG_FILE="transition_monitor_$(date +%Y%m%d).log"
CHECK_INTERVAL=300  # Check every 5 minutes

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Initialize log file
echo "=====================================================" | tee -a $LOG_FILE
echo "ChatMRPT Transition Monitoring Started" | tee -a $LOG_FILE
echo "Start Time: $(date)" | tee -a $LOG_FILE
echo "=====================================================" | tee -a $LOG_FILE

# Function to log with timestamp
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

# Function to check service status
check_service() {
    local ip=$1
    local name=$2
    
    # Check service
    SERVICE_STATUS=$(ssh -o ConnectTimeout=5 -i $KEY_PATH ec2-user@$ip 'sudo systemctl is-active chatmrpt' 2>/dev/null || echo "inactive")
    
    # Check workers
    WORKER_COUNT=$(ssh -o ConnectTimeout=5 -i $KEY_PATH ec2-user@$ip 'ps aux | grep gunicorn | grep -v grep | wc -l' 2>/dev/null || echo "0")
    
    # Check memory
    MEM_PCT=$(ssh -o ConnectTimeout=5 -i $KEY_PATH ec2-user@$ip 'free | grep Mem | awk "{print int(\$3/\$2 * 100)}"' 2>/dev/null || echo "0")
    
    # Check disk
    DISK_PCT=$(ssh -o ConnectTimeout=5 -i $KEY_PATH ec2-user@$ip 'df -h / | awk "NR==2 {print int(\$5)}"' 2>/dev/null || echo "0")
    
    echo "$name|$SERVICE_STATUS|$WORKER_COUNT|$MEM_PCT|$DISK_PCT"
}

# Function to check ALB
check_alb() {
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$ALB_URL/ping" 2>/dev/null || echo "000")
    RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" --max-time 10 "$ALB_URL/ping" 2>/dev/null || echo "0")
    
    echo "$HTTP_CODE|$RESPONSE_TIME"
}

# Function to send alert (placeholder - can integrate with SNS/email)
send_alert() {
    local severity=$1
    local message=$2
    
    log_message "ALERT [$severity]: $message"
    
    # If critical, also display prominently
    if [ "$severity" = "CRITICAL" ]; then
        echo ""
        echo -e "${RED}=============================================${NC}"
        echo -e "${RED}CRITICAL ALERT: $message${NC}"
        echo -e "${RED}=============================================${NC}"
        echo ""
    fi
}

# Function to analyze metrics and trigger alerts
analyze_metrics() {
    local instance=$1
    local status=$2
    local workers=$3
    local mem=$4
    local disk=$5
    
    # Check for critical conditions
    if [ "$status" != "active" ]; then
        send_alert "CRITICAL" "$instance service is down!"
        return 1
    fi
    
    if [ "$workers" -lt "3" ]; then
        send_alert "WARNING" "$instance has only $workers workers running (expected 6+)"
    fi
    
    if [ "$mem" -gt "80" ]; then
        send_alert "WARNING" "$instance memory usage is high: ${mem}%"
    fi
    
    if [ "$disk" -gt "85" ]; then
        send_alert "WARNING" "$instance disk usage is high: ${disk}%"
    fi
    
    return 0
}

# Main monitoring loop
monitor_loop() {
    local iteration=0
    local failures=0
    
    while true; do
        iteration=$((iteration + 1))
        
        echo ""
        echo "Check #$iteration - $(date '+%Y-%m-%d %H:%M:%S')"
        echo "----------------------------------------"
        
        # Check Instance 1
        INST1_DATA=$(check_service $INSTANCE1_IP "Instance1")
        IFS='|' read -r name1 status1 workers1 mem1 disk1 <<< "$INST1_DATA"
        
        if analyze_metrics "Instance1" "$status1" "$workers1" "$mem1" "$disk1"; then
            echo -e "Instance 1: ${GREEN}✅${NC} Service=$status1 Workers=$workers1 Mem=${mem1}% Disk=${disk1}%"
            log_message "Instance1: OK - Service=$status1 Workers=$workers1 Mem=${mem1}% Disk=${disk1}%"
        else
            echo -e "Instance 1: ${RED}❌${NC} Service=$status1"
            failures=$((failures + 1))
        fi
        
        # Check Instance 2
        INST2_DATA=$(check_service $INSTANCE2_IP "Instance2")
        IFS='|' read -r name2 status2 workers2 mem2 disk2 <<< "$INST2_DATA"
        
        if analyze_metrics "Instance2" "$status2" "$workers2" "$mem2" "$disk2"; then
            echo -e "Instance 2: ${GREEN}✅${NC} Service=$status2 Workers=$workers2 Mem=${mem2}% Disk=${disk2}%"
            log_message "Instance2: OK - Service=$status2 Workers=$workers2 Mem=${mem2}% Disk=${disk2}%"
        else
            echo -e "Instance 2: ${RED}❌${NC} Service=$status2"
            failures=$((failures + 1))
        fi
        
        # Check ALB
        ALB_DATA=$(check_alb)
        IFS='|' read -r http_code response_time <<< "$ALB_DATA"
        
        if [ "$http_code" = "200" ]; then
            echo -e "ALB:        ${GREEN}✅${NC} HTTP=$http_code Response=${response_time}s"
            log_message "ALB: OK - HTTP=$http_code Response=${response_time}s"
        else
            echo -e "ALB:        ${RED}❌${NC} HTTP=$http_code"
            log_message "ALB: FAILED - HTTP=$http_code"
            send_alert "CRITICAL" "ALB health check failed with HTTP $http_code"
            failures=$((failures + 1))
        fi
        
        # Summary
        if [ $failures -gt 2 ]; then
            send_alert "CRITICAL" "Multiple failures detected! Consider rollback."
        elif [ $failures -gt 0 ]; then
            echo -e "${YELLOW}⚠️  Some issues detected, monitoring closely...${NC}"
        else
            echo -e "${GREEN}✅ All systems operational${NC}"
        fi
        
        # Reset failure counter if it was a transient issue
        if [ $failures -eq 0 ]; then
            failures=0
        fi
        
        # Sleep before next check
        echo ""
        echo "Next check in $CHECK_INTERVAL seconds (Press Ctrl+C to stop)..."
        sleep $CHECK_INTERVAL
    done
}

# Function to generate final report
generate_report() {
    echo ""
    echo "=====================================================" | tee -a $LOG_FILE
    echo "Monitoring Session Ended" | tee -a $LOG_FILE
    echo "End Time: $(date)" | tee -a $LOG_FILE
    echo "=====================================================" | tee -a $LOG_FILE
    echo ""
    echo "Log file saved: $LOG_FILE"
}

# Trap to handle script termination
trap generate_report EXIT

# Start monitoring
echo ""
echo -e "${GREEN}Starting continuous monitoring...${NC}"
echo "Press Ctrl+C to stop monitoring"
echo ""

monitor_loop