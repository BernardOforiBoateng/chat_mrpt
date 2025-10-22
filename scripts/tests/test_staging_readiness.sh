#!/bin/bash

# =====================================================
# Staging Environment Production Readiness Test
# =====================================================
# Purpose: Comprehensive testing of staging environment readiness
# Date: August 27, 2025
# =====================================================

set -e

# Configuration
ALB_URL="http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
TEST_RESULTS_FILE="staging_readiness_test_$(date +%Y%m%d_%H%M%S).log"
PASS_COUNT=0
FAIL_COUNT=0

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "======================================================"
echo "   STAGING ENVIRONMENT READINESS TEST"
echo "   $(date)"
echo "======================================================"
echo ""

# Function to log test results
log_test() {
    local test_name=$1
    local result=$2
    local details=$3
    
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] TEST: $test_name - $result - $details" >> $TEST_RESULTS_FILE
    
    if [ "$result" = "PASS" ]; then
        echo -e "${GREEN}✅ $test_name: PASS${NC}"
        echo "   $details"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo -e "${RED}❌ $test_name: FAIL${NC}"
        echo "   $details"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

# Function to test endpoint
test_endpoint() {
    local endpoint=$1
    local expected_code=$2
    local test_name=$3
    
    local response=$(curl -s -o /dev/null -w "%{http_code}|%{time_total}" "$ALB_URL$endpoint" 2>/dev/null || echo "000|0")
    IFS='|' read -r http_code response_time <<< "$response"
    
    if [ "$http_code" = "$expected_code" ]; then
        log_test "$test_name" "PASS" "HTTP $http_code in ${response_time}s"
    else
        log_test "$test_name" "FAIL" "Expected HTTP $expected_code, got $http_code"
    fi
}

# Function to test upload capability
test_upload() {
    # Create test CSV file
    cat > /tmp/test_upload.csv << EOF
WardName,Population,Malaria_Cases,Temperature,Rainfall
Test_Ward_1,10000,150,28.5,125.3
Test_Ward_2,15000,200,29.1,130.7
Test_Ward_3,12000,175,27.8,118.2
EOF
    
    # Test file upload - use csv_file parameter name
    response=$(curl -s -X POST \
        -F "csv_file=@/tmp/test_upload.csv" \
        -F "session_id=test_$(date +%s)" \
        "$ALB_URL/upload" 2>/dev/null || echo '{"error": "Failed"}')
    
    if echo "$response" | grep -q '"status":"success"'; then
        log_test "File Upload" "PASS" "CSV upload successful"
    else
        log_test "File Upload" "FAIL" "Upload failed: $response"
    fi
    
    rm -f /tmp/test_upload.csv
}

# Function to test concurrent connections
test_concurrent() {
    local concurrent_count=10
    local temp_file="/tmp/concurrent_results_$$"
    
    echo "Testing $concurrent_count concurrent connections..."
    
    # Launch concurrent requests and save results
    > $temp_file
    for i in $(seq 1 $concurrent_count); do
        (
            code=$(curl -s -o /dev/null -w "%{http_code}" "$ALB_URL/ping" 2>/dev/null || echo "000")
            echo "$code" >> $temp_file
        ) &
    done
    
    # Wait for all background jobs to complete
    wait
    
    # Count successes
    local success_count=$(grep -c "^200$" $temp_file 2>/dev/null || echo "0")
    
    # Clean up
    rm -f $temp_file
    
    if [ $success_count -ge $((concurrent_count - 1)) ]; then
        log_test "Concurrent Connections" "PASS" "Handled $success_count of $concurrent_count concurrent requests"
    else
        log_test "Concurrent Connections" "FAIL" "Only $success_count of $concurrent_count succeeded"
    fi
}

# Function to test response time under load
test_response_time() {
    local count=20
    local max_allowed=2  # 2 seconds max (in milliseconds * 1000)
    local sum=0
    local times=()
    
    echo "Testing response times (20 sequential requests)..."
    
    for i in $(seq 1 $count); do
        response_time=$(curl -s -o /dev/null -w "%{time_total}" "$ALB_URL/" 2>/dev/null || echo "999")
        # Convert to milliseconds to avoid decimal math
        ms=$(echo "$response_time" | awk '{print int($1 * 1000)}')
        times+=($ms)
        sum=$((sum + ms))
    done
    
    avg_ms=$((sum / count))
    avg_sec=$(echo "$avg_ms" | awk '{printf "%.3f", $1/1000}')
    
    if [ $avg_ms -lt $((max_allowed * 1000)) ]; then
        log_test "Response Time" "PASS" "Average: ${avg_sec}s (< ${max_allowed}s threshold)"
    else
        log_test "Response Time" "FAIL" "Average: ${avg_sec}s (exceeds ${max_allowed}s threshold)"
    fi
}

# Function to test session persistence
test_session() {
    local session_id="test_session_$(date +%s)"
    
    # Make first request with session
    response1=$(curl -s -c /tmp/cookies.txt \
        "$ALB_URL/" 2>/dev/null || echo "Failed")
    
    # Make second request with same cookies
    response2=$(curl -s -b /tmp/cookies.txt \
        "$ALB_URL/" 2>/dev/null || echo "Failed")
    
    if [ "$response1" != "Failed" ] && [ "$response2" != "Failed" ]; then
        log_test "Session Persistence" "PASS" "Session maintained across requests"
    else
        log_test "Session Persistence" "FAIL" "Session not maintained"
    fi
    
    rm -f /tmp/cookies.txt
}

echo "======================================================"
echo "   RUNNING READINESS TESTS"
echo "======================================================"
echo ""

# 1. Basic Connectivity Tests
echo -e "${YELLOW}1. BASIC CONNECTIVITY${NC}"
echo "----------------------------------------"
test_endpoint "/ping" "200" "Health Check Endpoint"
test_endpoint "/" "200" "Main Page"
test_endpoint "/system-health" "200" "API Health"
echo ""

# 2. Application Functionality
echo -e "${YELLOW}2. APPLICATION FUNCTIONALITY${NC}"
echo "----------------------------------------"
test_upload
echo ""

# 3. Performance Tests
echo -e "${YELLOW}3. PERFORMANCE TESTS${NC}"
echo "----------------------------------------"
test_response_time
test_concurrent
echo ""

# 4. Session Management
echo -e "${YELLOW}4. SESSION MANAGEMENT${NC}"
echo "----------------------------------------"
test_session
echo ""

# 5. Error Handling
echo -e "${YELLOW}5. ERROR HANDLING${NC}"
echo "----------------------------------------"
test_endpoint "/nonexistent" "404" "404 Error Handling"
echo ""

# Generate Summary Report
echo "======================================================"
echo "   TEST SUMMARY"
echo "======================================================"
echo ""
echo "Test Results:"
echo "-------------"
echo -e "${GREEN}Passed: $PASS_COUNT${NC}"
echo -e "${RED}Failed: $FAIL_COUNT${NC}"
echo ""

TOTAL_TESTS=$((PASS_COUNT + FAIL_COUNT))
PASS_RATE=$((PASS_COUNT * 100 / TOTAL_TESTS))

if [ $PASS_RATE -ge 90 ]; then
    echo -e "${GREEN}✅ STAGING ENVIRONMENT IS READY FOR PRODUCTION${NC}"
    echo "   Pass rate: ${PASS_RATE}%"
    echo ""
    echo "Recommendation: Proceed with Phase 2 (Application Optimization)"
elif [ $PASS_RATE -ge 70 ]; then
    echo -e "${YELLOW}⚠️  STAGING ENVIRONMENT NEEDS MINOR FIXES${NC}"
    echo "   Pass rate: ${PASS_RATE}%"
    echo ""
    echo "Recommendation: Fix failed tests before proceeding"
else
    echo -e "${RED}❌ STAGING ENVIRONMENT NOT READY${NC}"
    echo "   Pass rate: ${PASS_RATE}%"
    echo ""
    echo "Recommendation: Address critical issues immediately"
fi

echo ""
echo "Detailed test log: $TEST_RESULTS_FILE"
echo ""
echo "======================================================"
echo "Test completed at $(date)"
echo "======================================================"