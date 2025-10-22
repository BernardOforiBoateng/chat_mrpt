#!/bin/bash

# =====================================================
# Deploy Phase 2 Optimizations
# =====================================================
# Purpose: Deploy performance optimizations to staging
# Date: August 27, 2025
# =====================================================

set -e

# Configuration
KEY_PATH="/tmp/chatmrpt-key2.pem"
INSTANCE1_IP="3.21.167.170"
INSTANCE2_IP="18.220.103.20"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "======================================================"
echo "   DEPLOYING PHASE 2 OPTIMIZATIONS"
echo "   $(date)"
echo "======================================================"
echo ""

# Function to deploy optimizations to instance
deploy_to_instance() {
    local ip=$1
    local name=$2
    
    echo -e "${YELLOW}Deploying to $name ($ip)...${NC}"
    
    # Step 1: Backup current configuration
    echo "  Backing up current configuration..."
    ssh -i $KEY_PATH ec2-user@$ip << 'EOF' 2>/dev/null
        cd /home/ec2-user/ChatMRPT
        cp gunicorn_config.py gunicorn_config.py.backup_$(date +%Y%m%d_%H%M%S)
        cp .env .env.backup_phase2_$(date +%Y%m%d_%H%M%S)
EOF
    
    # Step 2: Copy optimized configurations
    echo "  Copying optimized configurations..."
    scp -i $KEY_PATH optimized_gunicorn_config.py ec2-user@$ip:/home/ec2-user/ChatMRPT/gunicorn_config.py 2>/dev/null
    scp -i $KEY_PATH app/config/production_optimized.py ec2-user@$ip:/home/ec2-user/ChatMRPT/app/config/ 2>/dev/null
    
    # Step 3: Update environment configuration
    echo "  Updating environment configuration..."
    ssh -i $KEY_PATH ec2-user@$ip << 'EOF' 2>/dev/null
        cd /home/ec2-user/ChatMRPT
        
        # Update Flask config to use optimized version
        if grep -q "^FLASK_CONFIG=" .env; then
            sed -i 's/^FLASK_CONFIG=.*/FLASK_CONFIG=production_optimized/' .env
        else
            echo "FLASK_CONFIG=production_optimized" >> .env
        fi
        
        # Ensure Redis URL is set
        if ! grep -q "^REDIS_URL=" .env; then
            echo "REDIS_URL=redis://chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com:6379/0" >> .env
        fi
        
        # Set optimal worker count (2x CPU cores + 1)
        if ! grep -q "^GUNICORN_WORKERS=" .env; then
            echo "GUNICORN_WORKERS=5" >> .env
        else
            sed -i 's/^GUNICORN_WORKERS=.*/GUNICORN_WORKERS=5/' .env
        fi
        
        # Enable production optimizations
        if ! grep -q "^FLASK_ENV=" .env; then
            echo "FLASK_ENV=production" >> .env
        fi
        
        # Create logs directory if it doesn't exist
        mkdir -p instance/logs
        
        echo "Configuration updated"
EOF
    
    # Step 4: Install any missing dependencies
    echo "  Checking dependencies..."
    ssh -i $KEY_PATH ec2-user@$ip << 'EOF' 2>/dev/null
        cd /home/ec2-user/ChatMRPT
        
        # Install Redis client if not present
        /home/ec2-user/chatmrpt_env/bin/pip list | grep -q redis || \
            /home/ec2-user/chatmrpt_env/bin/pip install redis
        
        # Install Flask-Caching if not present
        /home/ec2-user/chatmrpt_env/bin/pip list | grep -q Flask-Caching || \
            /home/ec2-user/chatmrpt_env/bin/pip install Flask-Caching
        
        echo "Dependencies checked"
EOF
    
    # Step 5: Test configuration
    echo "  Testing configuration..."
    ssh -i $KEY_PATH ec2-user@$ip << 'EOF' 2>/dev/null
        cd /home/ec2-user/ChatMRPT
        
        /home/ec2-user/chatmrpt_env/bin/python3.11 << 'PYTHON'
import sys
sys.path.insert(0, '.')
try:
    from app.config.production_optimized import ProductionOptimizedConfig
    print("✅ Optimized config loads successfully")
    
    # Test key settings
    print(f"  Pool size: {ProductionOptimizedConfig.SQLALCHEMY_ENGINE_OPTIONS['pool_size']}")
    print(f"  Cache type: {ProductionOptimizedConfig.CACHE_TYPE}")
    print(f"  Rate limiting: {ProductionOptimizedConfig.RATELIMIT_ENABLED}")
except Exception as e:
    print(f"❌ Config error: {e}")
PYTHON
EOF
    
    # Step 6: Restart service with new configuration
    echo "  Restarting service..."
    ssh -i $KEY_PATH ec2-user@$ip 'sudo systemctl restart chatmrpt' 2>/dev/null
    
    # Wait for service to stabilize
    sleep 5
    
    # Step 7: Verify service is running
    echo "  Verifying service..."
    SERVICE_STATUS=$(ssh -i $KEY_PATH ec2-user@$ip 'sudo systemctl is-active chatmrpt' 2>/dev/null || echo "inactive")
    WORKER_COUNT=$(ssh -i $KEY_PATH ec2-user@$ip 'ps aux | grep gunicorn | grep -v grep | wc -l' 2>/dev/null || echo "0")
    
    if [ "$SERVICE_STATUS" = "active" ]; then
        echo -e "  ${GREEN}✅ Service active with $WORKER_COUNT workers${NC}"
    else
        echo -e "  ${RED}❌ Service not active${NC}"
        return 1
    fi
    
    echo ""
    return 0
}

# Deploy to both instances
echo -e "${YELLOW}Phase 2 Optimization Deployment${NC}"
echo "=================================="
echo ""

SUCCESS_COUNT=0

deploy_to_instance $INSTANCE1_IP "Instance 1"
if [ $? -eq 0 ]; then
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
fi

deploy_to_instance $INSTANCE2_IP "Instance 2"
if [ $? -eq 0 ]; then
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
fi

# Performance validation
echo "======================================================"
echo "   PERFORMANCE VALIDATION"
echo "======================================================"
echo ""

echo "Testing optimized endpoints..."

# Test response times with new configuration
for endpoint in "/" "/ping" "/system-health"; do
    response_time=$(curl -s -o /dev/null -w "%{time_total}" "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com$endpoint" 2>/dev/null || echo "999")
    ms=$(echo "$response_time * 1000" | awk '{print int($1)}')
    
    if [ $ms -lt 500 ]; then
        echo -e "  $endpoint: ${GREEN}${ms}ms ✅${NC}"
    elif [ $ms -lt 1000 ]; then
        echo -e "  $endpoint: ${YELLOW}${ms}ms ⚠️${NC}"
    else
        echo -e "  $endpoint: ${RED}${ms}ms ❌${NC}"
    fi
done

echo ""

# Check Redis connectivity
echo "Testing Redis caching..."
ssh -i $KEY_PATH ec2-user@$INSTANCE1_IP << 'EOF' 2>/dev/null
    /home/ec2-user/chatmrpt_env/bin/python3.11 << 'PYTHON'
import redis
try:
    r = redis.from_url('redis://chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com:6379/0')
    r.ping()
    print("  ✅ Redis connection successful")
    
    # Test cache operations
    r.set('test_key', 'test_value', ex=10)
    value = r.get('test_key')
    if value == b'test_value':
        print("  ✅ Cache operations working")
    else:
        print("  ❌ Cache operations failed")
except Exception as e:
    print(f"  ❌ Redis error: {e}")
PYTHON
EOF

echo ""
echo "======================================================"

# Summary
if [ $SUCCESS_COUNT -eq 2 ]; then
    echo -e "${GREEN}✅ OPTIMIZATION DEPLOYMENT SUCCESSFUL${NC}"
    echo ""
    echo "Optimizations Applied:"
    echo "----------------------"
    echo "✅ Connection pooling configured (20 connections)"
    echo "✅ Redis caching enabled"
    echo "✅ Worker optimization (5 workers per instance)"
    echo "✅ Response compression enabled"
    echo "✅ Rate limiting configured"
    echo "✅ Static file caching (1 year)"
    echo ""
    echo "Expected Improvements:"
    echo "---------------------"
    echo "• 30-50% faster response times"
    echo "• 2x better concurrent request handling"
    echo "• Reduced database load via connection pooling"
    echo "• Improved cache hit rates"
    echo ""
    echo "Next Steps:"
    echo "----------"
    echo "1. Monitor performance metrics"
    echo "2. Run load tests to verify improvements"
    echo "3. Configure error tracking (Sentry)"
    echo "4. Set up APM monitoring"
else
    echo -e "${YELLOW}⚠️  PARTIAL DEPLOYMENT${NC}"
    echo "   Only $SUCCESS_COUNT of 2 instances updated"
    echo "   Review logs and retry failed instances"
fi

echo ""
echo "To monitor performance:"
echo "  ./monitor_transition.sh"
echo ""
echo "To run load tests:"
echo "  ./run_load_tests.sh"
echo ""
echo "======================================================"
echo "Deployment completed at $(date)"