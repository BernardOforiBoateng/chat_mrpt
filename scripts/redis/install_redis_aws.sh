#!/bin/bash
# Install and Configure Redis for ChatMRPT on AWS
# This script implements the proper solution for TPR workflow issues

set -e  # Exit on any error

echo "=== ChatMRPT Redis Installation Script ==="
echo "This will install and configure Redis to fix TPR workflow issues"
echo ""

# SSH key path
SSH_KEY="/tmp/chatmrpt-key.pem"
AWS_HOST="ec2-user@3.137.158.17"

# Copy key to /tmp if needed and set permissions
if [ -f "aws_files/chatmrpt-key.pem" ]; then
    cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key.pem
    chmod 600 /tmp/chatmrpt-key.pem
fi

# Check if SSH key exists
if [ ! -f "$SSH_KEY" ]; then
    echo "❌ Error: SSH key not found at $SSH_KEY"
    exit 1
fi

echo "📦 Step 1: Installing Redis on AWS EC2..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$AWS_HOST" << 'INSTALL_REDIS'
    set -e
    
    # Check if Redis is already installed
    if command -v redis6-server &> /dev/null; then
        echo "ℹ️  Redis is already installed"
        redis6-server --version
    else
        echo "Installing Redis 6..."
        # For Amazon Linux 2023, the package is redis6
        sudo dnf install -y redis6
        
        if [ $? -eq 0 ]; then
            echo "✅ Redis installed successfully"
            redis6-server --version
        else
            echo "❌ Failed to install Redis"
            exit 1
        fi
    fi
INSTALL_REDIS

echo ""
echo "⚙️  Step 2: Configuring Redis..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$AWS_HOST" << 'CONFIGURE_REDIS'
    set -e
    
    # Create Redis configuration
    echo "Creating Redis configuration..."
    sudo tee /etc/redis6/redis6.conf > /dev/null << 'REDIS_CONFIG'
# Redis Configuration for ChatMRPT
bind 127.0.0.1
protected-mode yes
port 6379
tcp-backlog 511
timeout 0
tcp-keepalive 300
daemonize no
supervised systemd
pidfile /var/run/redis_6379.pid
loglevel notice
logfile /var/log/redis6/redis6.log
databases 16

# Persistence
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /var/lib/redis6

# Memory Management for Session Storage
maxmemory 256mb
maxmemory-policy allkeys-lru

# Append Only File
appendonly no

# Slow Log
slowlog-log-slower-than 10000
slowlog-max-len 128

# Latency Monitor
latency-monitor-threshold 0

# Event Notification
notify-keyspace-events ""

# Advanced Config
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
list-max-ziplist-size -2
list-compress-depth 0
set-max-intset-entries 512
zset-max-ziplist-entries 128
zset-max-ziplist-value 64
hll-sparse-max-bytes 3000
stream-node-max-bytes 4096
stream-node-max-entries 100
activerehashing yes
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit replica 256mb 64mb 60
client-output-buffer-limit pubsub 32mb 8mb 60
hz 10
dynamic-hz yes
aof-rewrite-incremental-fsync yes
rdb-save-incremental-fsync yes
REDIS_CONFIG

    # Create necessary directories (they should already exist, but just in case)
    sudo mkdir -p /var/log/redis6 /var/lib/redis6
    sudo chown redis6:redis6 /var/log/redis6 /var/lib/redis6
    
    echo "✅ Redis configuration created"
CONFIGURE_REDIS

echo ""
echo "🚀 Step 3: Starting Redis service..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$AWS_HOST" << 'START_REDIS'
    set -e
    
    # Stop Redis if running
    sudo systemctl stop redis6 2>/dev/null || true
    
    # Start Redis
    sudo systemctl start redis6
    
    # Enable Redis to start on boot
    sudo systemctl enable redis6
    
    # Check Redis status
    if sudo systemctl is-active --quiet redis6; then
        echo "✅ Redis is running"
        
        # Test Redis connection
        if redis6-cli ping | grep -q PONG; then
            echo "✅ Redis is responding to ping"
        else
            echo "❌ Redis is not responding"
            exit 1
        fi
    else
        echo "❌ Failed to start Redis"
        sudo systemctl status redis6
        exit 1
    fi
START_REDIS

echo ""
echo "🔧 Step 4: Updating ChatMRPT configuration..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$AWS_HOST" << 'UPDATE_CONFIG'
    set -e
    
    cd /home/ec2-user/ChatMRPT
    
    # Backup current .env
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ Created .env backup"
    
    # Check if Redis config already exists
    if grep -q "REDIS_HOST" .env; then
        echo "ℹ️  Redis configuration already exists in .env"
    else
        # Add Redis configuration
        echo "" >> .env
        echo "# Redis Configuration for Session Management" >> .env
        echo "REDIS_HOST=localhost" >> .env
        echo "REDIS_PORT=6379" >> .env
        echo "REDIS_DB=0" >> .env
        echo "# REDIS_PASSWORD is not set (using localhost only)" >> .env
        echo "✅ Added Redis configuration to .env"
    fi
    
    # Show Redis config
    echo ""
    echo "Current Redis configuration in .env:"
    grep -E "REDIS|SESSION" .env || echo "No Redis/Session config found"
UPDATE_CONFIG

echo ""
echo "♻️  Step 5: Restarting ChatMRPT application..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$AWS_HOST" << 'RESTART_APP'
    set -e
    
    # Restart the application
    sudo systemctl restart chatmrpt
    
    # Wait for app to start
    echo "Waiting for application to start..."
    sleep 5
    
    # Check if app is running
    if sudo systemctl is-active --quiet chatmrpt; then
        echo "✅ ChatMRPT is running"
    else
        echo "❌ ChatMRPT failed to start"
        sudo systemctl status chatmrpt
        exit 1
    fi
    
    # Check for Redis initialization in logs
    echo ""
    echo "Checking application logs for Redis initialization..."
    if grep -i "redis session store initialized" /home/ec2-user/ChatMRPT/instance/app.log 2>/dev/null | tail -1; then
        echo "✅ Redis sessions initialized successfully"
    else
        echo "⚠️  Could not confirm Redis initialization in logs"
    fi
RESTART_APP

echo ""
echo "🔍 Step 6: Verifying Redis integration..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$AWS_HOST" << 'VERIFY_REDIS'
    set -e
    
    # Check Redis keys
    echo "Redis database info:"
    redis6-cli INFO keyspace
    
    # Monitor for session keys (run for 5 seconds)
    echo ""
    echo "Monitoring for session keys (5 seconds)..."
    timeout 5 redis6-cli --scan --pattern "chatmrpt:*" 2>/dev/null || true
    
    # Show memory usage
    echo ""
    echo "Redis memory usage:"
    redis6-cli INFO memory | grep -E "used_memory_human|used_memory_peak_human"
    
    # Check Gunicorn workers
    echo ""
    echo "Gunicorn worker configuration:"
    grep "workers =" /home/ec2-user/ChatMRPT/gunicorn.conf.py
    
    echo ""
    echo "Active Gunicorn processes:"
    ps aux | grep gunicorn | grep -v grep | wc -l
VERIFY_REDIS

echo ""
echo "📋 Creating monitoring script..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$AWS_HOST" << 'CREATE_MONITOR'
    set -e
    
    # Create monitoring script
    cat > /home/ec2-user/monitor_redis.sh << 'MONITOR_SCRIPT'
#!/bin/bash
# Redis Monitoring Script for ChatMRPT

echo "=== Redis Health Check ==="
echo "Time: $(date)"
echo ""

# Check Redis status
echo "1. Redis Status:"
if systemctl is-active --quiet redis6; then
    echo "   ✅ Redis is running"
    redis6-cli ping &>/dev/null && echo "   ✅ Redis responding to ping"
else
    echo "   ❌ Redis is not running"
fi

# Memory usage
echo ""
echo "2. Memory Usage:"
redis6-cli INFO memory | grep -E "used_memory_human|maxmemory_human" | sed 's/^/   /'

# Session keys
echo ""
echo "3. Session Keys:"
SESSION_COUNT=$(redis6-cli --scan --pattern "chatmrpt:*" 2>/dev/null | wc -l)
echo "   Total session keys: $SESSION_COUNT"

# Recent session activity
echo ""
echo "4. Recent Sessions (last 5):"
redis6-cli --scan --pattern "chatmrpt:*" 2>/dev/null | tail -5 | sed 's/^/   /'

# Database stats
echo ""
echo "5. Database Stats:"
redis6-cli INFO keyspace | grep -v "^#" | sed 's/^/   /'

# Connection info
echo ""
echo "6. Connected Clients:"
redis6-cli INFO clients | grep connected_clients | sed 's/^/   /'

echo ""
echo "=== End of Health Check ==="
MONITOR_SCRIPT

    chmod +x /home/ec2-user/monitor_redis.sh
    echo "✅ Created monitoring script at /home/ec2-user/monitor_redis.sh"
CREATE_MONITOR

echo ""
echo "✅ === Redis Installation Complete ==="
echo ""
echo "📊 Monitoring Commands:"
echo "   - Check Redis health: ssh -i $SSH_KEY $AWS_HOST './monitor_redis.sh'"
echo "   - Watch Redis keys: ssh -i $SSH_KEY $AWS_HOST 'redis6-cli monitor'"
echo "   - View app logs: ssh -i $SSH_KEY $AWS_HOST 'tail -f /home/ec2-user/ChatMRPT/instance/app.log'"
echo ""
echo "🧪 Testing Instructions:"
echo "1. Visit: http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com/"
echo "2. Upload your NMEP TPR file"
echo "3. Select state (e.g., 'Adamawa State')"
echo "4. Select facility type (e.g., 'Use Primary Health Facilities only')"
echo "5. Select age group (e.g., 'Under 5')"
echo ""
echo "✅ Expected: Workflow completes without 'I understand you're asking about...' messages"
echo ""
echo "💡 Tip: Run the monitoring script to see Redis session keys being created as you use the app"