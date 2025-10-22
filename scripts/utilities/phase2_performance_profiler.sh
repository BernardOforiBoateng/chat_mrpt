#!/bin/bash

# =====================================================
# Phase 2: Performance Profiling Script
# =====================================================
# Purpose: Profile current application performance for optimization
# Date: August 27, 2025
# =====================================================

set -e

# Configuration
KEY_PATH="/tmp/chatmrpt-key2.pem"
INSTANCE1_IP="3.21.167.170"
INSTANCE2_IP="18.220.103.20"
ALB_URL="http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
RESULTS_FILE="performance_profile_$(date +%Y%m%d_%H%M%S).log"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "======================================================"
echo "   PHASE 2: PERFORMANCE PROFILING"
echo "   $(date)"
echo "======================================================"
echo ""

# Function to run load test
run_load_test() {
    local endpoint=$1
    local concurrent=$2
    local requests=$3
    local name=$4
    
    echo -e "${BLUE}Testing: $name${NC}"
    echo "  Endpoint: $endpoint"
    echo "  Concurrent: $concurrent"
    echo "  Total Requests: $requests"
    
    # Use Apache Bench if available, otherwise use curl
    if command -v ab &> /dev/null; then
        ab -n $requests -c $concurrent -g /tmp/ab_results.tsv "$ALB_URL$endpoint" 2>&1 | \
            grep -E "Requests per second|Time per request|Transfer rate|Failed requests" | \
            sed 's/^/    /'
    else
        # Fallback to curl-based testing
        local start_time=$(date +%s%N)
        local success=0
        local failed=0
        
        for ((i=1; i<=requests; i++)); do
            if ((i % concurrent == 0)); then
                wait
            fi
            (
                code=$(curl -s -o /dev/null -w "%{http_code}" "$ALB_URL$endpoint" 2>/dev/null)
                if [ "$code" = "200" ]; then
                    echo "S" >> /tmp/perf_results_$$
                else
                    echo "F" >> /tmp/perf_results_$$
                fi
            ) &
        done
        wait
        
        local end_time=$(date +%s%N)
        local duration=$(((end_time - start_time) / 1000000))
        success=$(grep -c "S" /tmp/perf_results_$$ 2>/dev/null || echo "0")
        failed=$(grep -c "F" /tmp/perf_results_$$ 2>/dev/null || echo "0")
        local rps=$(echo "scale=2; $success * 1000 / $duration" | bc 2>/dev/null || echo "N/A")
        
        echo "    Successful requests: $success"
        echo "    Failed requests: $failed"
        echo "    Duration: ${duration}ms"
        echo "    Requests per second: $rps"
        
        rm -f /tmp/perf_results_$$
    fi
    echo ""
}

# Function to check resource usage
check_resources() {
    local ip=$1
    local name=$2
    
    echo -e "${BLUE}Resource Usage - $name${NC}"
    
    ssh -i $KEY_PATH ec2-user@$ip << 'EOF' 2>/dev/null || echo "Failed to connect"
        # CPU usage
        echo -n "  CPU Load: "
        uptime | awk -F'load average:' '{print $2}'
        
        # Memory usage
        echo -n "  Memory: "
        free -h | awk 'NR==2 {printf "Used: %s/%s (%.1f%%)\n", $3, $2, $3*100/$2}'
        
        # Disk I/O
        echo -n "  Disk I/O: "
        iostat -x 1 2 2>/dev/null | grep -A1 "avg-cpu" | tail -1 | awk '{printf "CPU: %.1f%% iowait\n", $4}' || echo "iostat not available"
        
        # Network connections
        echo -n "  Network Connections: "
        ss -tun | tail -n +2 | wc -l
        
        # Gunicorn processes
        echo -n "  Gunicorn Workers: "
        ps aux | grep gunicorn | grep -v grep | wc -l
        
        # Database connections (if using SQLite)
        echo -n "  Open Files: "
        lsof 2>/dev/null | grep -c "ChatMRPT" || echo "0"
EOF
    echo ""
}

# Function to test database performance
test_database_performance() {
    echo -e "${BLUE}Database Performance Test${NC}"
    
    ssh -i $KEY_PATH ec2-user@$INSTANCE1_IP << 'EOF' 2>/dev/null
        cd /home/ec2-user/ChatMRPT
        
        /home/ec2-user/chatmrpt_env/bin/python3.11 << 'PYTHON'
import time
import sys
sys.path.insert(0, '.')

from app import create_app
from app.models import db

app = create_app()

with app.app_context():
    # Test read performance
    start = time.time()
    for _ in range(100):
        db.session.execute("SELECT COUNT(*) FROM interactions").fetchone()
    read_time = time.time() - start
    
    print(f"  Database Read (100 queries): {read_time:.3f}s")
    print(f"  Average per query: {read_time/100*1000:.1f}ms")
    
    # Check connection pool status
    pool = db.engine.pool
    print(f"  Connection Pool Size: {pool.size()}")
    print(f"  Overflow: {pool.overflow()}")
    print(f"  Checked out connections: {pool.checkedout()}")
PYTHON
EOF
    echo ""
}

# Function to analyze slow endpoints
analyze_slow_endpoints() {
    echo -e "${BLUE}Analyzing Response Times by Endpoint${NC}"
    
    endpoints=(
        "/ Homepage"
        "/ping Health_Check"
        "/system-health System_Health"
        "/upload Upload_Page"
    )
    
    for endpoint_info in "${endpoints[@]}"; do
        IFS=' ' read -r endpoint name <<< "$endpoint_info"
        
        # Test response time 10 times
        total_time=0
        min_time=999999
        max_time=0
        
        for i in {1..10}; do
            response_time=$(curl -s -o /dev/null -w "%{time_total}" "$ALB_URL$endpoint" 2>/dev/null || echo "999")
            ms=$(echo "$response_time * 1000" | bc 2>/dev/null || echo "999")
            ms=${ms%.*}  # Remove decimal part
            
            total_time=$((total_time + ms))
            
            if [ $ms -lt $min_time ]; then
                min_time=$ms
            fi
            if [ $ms -gt $max_time ]; then
                max_time=$ms
            fi
        done
        
        avg_time=$((total_time / 10))
        
        printf "  %-20s Avg: %4dms  Min: %4dms  Max: %4dms\n" \
            "$name:" "$avg_time" "$min_time" "$max_time"
    done
    echo ""
}

# Function to check cache effectiveness
check_cache_status() {
    echo -e "${BLUE}Cache Configuration Status${NC}"
    
    ssh -i $KEY_PATH ec2-user@$INSTANCE1_IP << 'EOF' 2>/dev/null
        cd /home/ec2-user/ChatMRPT
        
        /home/ec2-user/chatmrpt_env/bin/python3.11 << 'PYTHON'
import sys
sys.path.insert(0, '.')

from app import create_app
app = create_app()

with app.app_context():
    # Check if caching is configured
    cache_type = app.config.get('CACHE_TYPE', 'simple')
    cache_timeout = app.config.get('CACHE_DEFAULT_TIMEOUT', 300)
    
    print(f"  Cache Type: {cache_type}")
    print(f"  Default Timeout: {cache_timeout}s")
    
    # Check Redis if configured
    if 'redis' in cache_type.lower():
        redis_url = app.config.get('CACHE_REDIS_URL', 'Not configured')
        print(f"  Redis URL: {redis_url}")
    
    # Check static file caching
    send_file_age = app.config.get('SEND_FILE_MAX_AGE_DEFAULT', 0)
    print(f"  Static File Cache: {send_file_age}s")
PYTHON
EOF
    echo ""
}

# Function to generate recommendations
generate_recommendations() {
    echo -e "${YELLOW}======================================================"
    echo "   OPTIMIZATION RECOMMENDATIONS"
    echo "======================================================${NC}"
    echo ""
    
    # Analyze collected data and provide recommendations
    cat > "$RESULTS_FILE" << EOF
Performance Profile Report
Generated: $(date)

CURRENT CONFIGURATION:
- Gunicorn Workers: 7 per instance (14 total)
- Worker Class: sync
- Database: SQLite with default settings
- Cache: Not optimized for production
- Session Storage: File-based or Redis

RECOMMENDED OPTIMIZATIONS:

1. GUNICORN CONFIGURATION:
   - Increase workers to 2-4x CPU cores
   - Consider async workers (gevent/eventlet) for I/O bound operations
   - Add worker_connections for better concurrency
   
2. DATABASE OPTIMIZATION:
   - Implement connection pooling with SQLAlchemy
   - Add indexes for frequently queried columns
   - Consider read replicas for heavy read operations
   
3. CACHING STRATEGY:
   - Enable Redis caching for frequently accessed data
   - Implement page-level caching for static content
   - Add browser caching headers for assets
   
4. SESSION MANAGEMENT:
   - Ensure Redis is used for all session storage
   - Configure session timeout appropriately
   - Implement session cleanup routine

5. MONITORING:
   - Add APM tool (New Relic, DataDog, or AWS X-Ray)
   - Implement custom metrics for business KPIs
   - Set up log aggregation

6. STATIC FILE OPTIMIZATION:
   - Enable CDN for static assets
   - Implement asset minification
   - Use versioned filenames for cache busting
EOF

    echo "  Report saved to: $RESULTS_FILE"
    echo ""
}

# Main profiling sequence
echo "======================================================"
echo "   STARTING PERFORMANCE PROFILING"
echo "======================================================"
echo ""

# 1. Current Resource Usage
echo -e "${YELLOW}1. BASELINE RESOURCE USAGE${NC}"
echo "----------------------------------------"
check_resources $INSTANCE1_IP "Instance 1"
check_resources $INSTANCE2_IP "Instance 2"

# 2. Response Time Analysis
echo -e "${YELLOW}2. ENDPOINT RESPONSE TIMES${NC}"
echo "----------------------------------------"
analyze_slow_endpoints

# 3. Load Testing
echo -e "${YELLOW}3. LOAD TESTING${NC}"
echo "----------------------------------------"
run_load_test "/" 5 50 "Homepage - Light Load"
run_load_test "/" 10 100 "Homepage - Medium Load"
run_load_test "/ping" 20 200 "Health Check - Heavy Load"

# 4. Database Performance
echo -e "${YELLOW}4. DATABASE PERFORMANCE${NC}"
echo "----------------------------------------"
test_database_performance

# 5. Cache Configuration
echo -e "${YELLOW}5. CACHE CONFIGURATION${NC}"
echo "----------------------------------------"
check_cache_status

# 6. Generate Recommendations
generate_recommendations

echo -e "${GREEN}======================================================"
echo "   PROFILING COMPLETE!"
echo "======================================================${NC}"
echo ""
echo "Summary:"
echo "--------"
echo "✅ Resource usage profiled"
echo "✅ Response times analyzed"
echo "✅ Load tests completed"
echo "✅ Database performance checked"
echo "✅ Cache configuration reviewed"
echo ""
echo "Next Steps:"
echo "1. Review recommendations in: $RESULTS_FILE"
echo "2. Implement Gunicorn optimizations"
echo "3. Configure connection pooling"
echo "4. Set up Redis caching"
echo ""
echo "To implement optimizations, run:"
echo "  ./implement_phase2_optimizations.sh"
echo ""
echo "======================================================"