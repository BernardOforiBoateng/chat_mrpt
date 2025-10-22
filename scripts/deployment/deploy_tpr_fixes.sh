#!/bin/bash
# Deploy TPR session persistence fixes to AWS

echo "=== Deploying TPR Session Persistence Fixes ==="
echo "This script implements both Phase 1 and Phase 2 fixes"
echo ""

# Navigate to project directory
cd ~/ChatMRPT
source chatmrpt_venv_new/bin/activate

# Create backups
echo "=== Creating Backups ==="
mkdir -p backups/$(date +%Y%m%d_%H%M%S)
cp app/web/routes/upload_routes.py backups/$(date +%Y%m%d_%H%M%S)/
cp app/tpr_module/core/tpr_conversation_manager.py backups/$(date +%Y%m%d_%H%M%S)/
cp app/static/js/modules/upload/file-uploader.js backups/$(date +%Y%m%d_%H%M%S)/
cp app/__init__.py backups/$(date +%Y%m%d_%H%M%S)/

# Phase 1: Apply session.modified fixes
echo ""
echo "=== Phase 1: Applying Session Modification Fixes ==="

# 1. Update upload_routes.py - Add session.modified = True after TPR flags
echo "Updating upload_routes.py..."
sed -i '/session\['\''should_ask_analysis_permission'\''\] = False/a\    \n    # CRITICAL: Force session update for multi-worker environment\n    session.modified = True' app/web/routes/upload_routes.py

# 2. Update tpr_conversation_manager.py - Add _update_stage method
echo "Updating tpr_conversation_manager.py..."
# First, add the _update_stage method after __init__
cat > /tmp/update_stage_method.txt << 'EOFMETHOD'
    def _update_stage(self, new_stage: ConversationStage) -> None:
        """Update conversation stage and force session update for multi-worker environment."""
        self.current_stage = new_stage
        
        # Force session update in multi-worker environment
        try:
            from flask import session
            session.modified = True
            logger.debug(f"Updated stage to {new_stage.value} and marked session as modified")
        except ImportError:
            # Not in Flask context, likely in tests
            pass
        except Exception as e:
            logger.warning(f"Could not mark session as modified: {e}")
EOFMETHOD

# Now replace all direct stage assignments with _update_stage calls
sed -i 's/self\.current_stage = ConversationStage\./self._update_stage(ConversationStage./g' app/tpr_module/core/tpr_conversation_manager.py

# 3. Update file-uploader.js - Add verifyTPRSessionState method
echo "Updating file-uploader.js..."
# Add the method before the reset() method
cat > /tmp/verify_tpr_method.js << 'EOFJS'
    /**
     * Verify TPR session state in backend (multi-worker fix)
     * Forces a check with the backend to ensure TPR workflow flags are properly set
     */
    async verifyTPRSessionState() {
        try {
            // Make a lightweight request to check session state
            const response = await fetch('/api/session/verify-tpr', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'same-origin' // Important for session cookies
            });
            
            if (!response.ok) {
                console.warn('⚠️ Could not verify TPR session state');
                return;
            }
            
            const data = await response.json();
            
            // If TPR workflow is not active in backend, force a reload
            if (!data.tpr_workflow_active) {
                console.warn('⚠️ TPR workflow not active in backend session, forcing reload...');
                // Small delay to ensure session writes are complete
                setTimeout(() => {
                    window.location.reload();
                }, 500);
            } else {
                console.log('✅ TPR workflow verified active in backend session');
            }
        } catch (error) {
            console.error('Error verifying TPR session state:', error);
            // Don't break the flow, just log the error
        }
    }

EOFJS

# Insert the method into file-uploader.js
awk '/sendProactiveMessage.*\{/{p=1} p{print} /^\s*\}$/{if(p==1){print ""; system("cat /tmp/verify_tpr_method.js"); p=0}}' app/static/js/modules/upload/file-uploader.js > /tmp/file-uploader-new.js
mv /tmp/file-uploader-new.js app/static/js/modules/upload/file-uploader.js

# 4. Create session_routes.py
echo "Creating session_routes.py..."
cat > app/web/routes/session_routes.py << 'EOFSESSION'
# app/web/routes/session_routes.py
"""
Session Routes module for session state verification.

This module provides endpoints for verifying session state
in multi-worker environments.
"""

import logging
from flask import Blueprint, session, jsonify
from ...core.decorators import handle_errors

logger = logging.getLogger(__name__)

# Create the session routes blueprint
session_bp = Blueprint('session', __name__)


@session_bp.route('/api/session/verify-tpr', methods=['GET'])
@handle_errors
def verify_tpr_session():
    """
    Verify TPR workflow session state.
    
    This endpoint is used by the frontend to check if TPR workflow
    is active in the backend session. Critical for multi-worker
    environments where session state may not be properly shared.
    
    Returns:
        JSON response with TPR workflow status
    """
    # Get TPR workflow state from session
    tpr_workflow_active = session.get('tpr_workflow_active', False)
    tpr_session_id = session.get('tpr_session_id')
    
    # Log the verification request
    logger.debug(f"TPR session verification: active={tpr_workflow_active}, session_id={tpr_session_id}")
    
    # Additional checks for TPR state
    tpr_loaded = session.get('tprLoaded', False)
    upload_type = session.get('upload_type')
    
    # Consider TPR workflow active if any TPR-related flags are set
    is_tpr_active = (
        tpr_workflow_active or 
        tpr_loaded or 
        upload_type in ['tpr_excel', 'tpr_shapefile']
    )
    
    return jsonify({
        'tpr_workflow_active': is_tpr_active,
        'tpr_session_id': tpr_session_id,
        'session_flags': {
            'tpr_workflow_active': tpr_workflow_active,
            'tprLoaded': tpr_loaded,
            'upload_type': upload_type
        }
    })


@session_bp.route('/api/session/status', methods=['GET'])
@handle_errors
def get_session_status():
    """
    Get general session status.
    
    Returns:
        JSON response with session status information
    """
    return jsonify({
        'session_id': session.get('session_id'),
        'data_loaded': session.get('data_loaded', False),
        'csv_loaded': session.get('csv_loaded', False),
        'shapefile_loaded': session.get('shapefile_loaded', False),
        'analysis_complete': session.get('analysis_complete', False),
        'upload_type': session.get('upload_type'),
        'tpr_workflow_active': session.get('tpr_workflow_active', False)
    })


@session_bp.route('/api/session/redis-status', methods=['GET'])
@handle_errors
def get_redis_status():
    """
    Get Redis session store status.
    
    Returns:
        JSON response with Redis connection information
    """
    from flask import current_app
    from ...config.redis_config import RedisConfig
    
    redis_info = RedisConfig.get_redis_info(current_app)
    
    # Add session type information
    session_type = current_app.config.get('SESSION_TYPE', 'filesystem')
    redis_info['session_type'] = session_type
    redis_info['session_prefix'] = current_app.config.get('SESSION_KEY_PREFIX', 'session:')
    
    return jsonify(redis_info)
EOFSESSION

# 5. Register session blueprint in routes __init__.py
echo "Registering session blueprint..."
# Add import
sed -i '/from \.export_routes import export_bp/a from .session_routes import session_bp' app/web/routes/__init__.py
# Add to __all__
sed -i "/\'export_bp\',/a\    \'session_bp\'," app/web/routes/__init__.py
# Register blueprint
sed -i '/app\.register_blueprint(export_bp)/a\    \n    # Register session routes (session state verification)\n    app.register_blueprint(session_bp)' app/web/routes/__init__.py

echo ""
echo "=== Phase 2: Installing Redis ==="

# Check if Redis is already installed
if command -v redis-server &> /dev/null; then
    echo "Redis is already installed"
else
    echo "Installing Redis..."
    sudo amazon-linux-extras install redis6 -y
fi

# Configure Redis
echo "Configuring Redis..."
sudo cp /etc/redis/redis.conf /etc/redis/redis.conf.backup

# Generate Redis password
REDIS_PASSWORD=$(openssl rand -base64 32)
echo "Generated Redis password: $REDIS_PASSWORD"

# Create Redis configuration
sudo tee /etc/redis/redis.conf > /dev/null << EOF
# Basic Configuration
bind 127.0.0.1
protected-mode yes
port 6379
tcp-backlog 511
timeout 0
tcp-keepalive 300

# General
daemonize yes
supervised systemd
pidfile /var/run/redis/redis.pid
loglevel notice
logfile /var/log/redis/redis.log

# Snapshotting
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /var/lib/redis

# Security
requirepass $REDIS_PASSWORD

# Memory Management
maxmemory 256mb
maxmemory-policy allkeys-lru

# Append Only Mode
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
EOF

# Start Redis
sudo systemctl enable redis
sudo systemctl restart redis

# Add Redis configuration to .env
echo "" >> .env
echo "# Redis Configuration" >> .env
echo "REDIS_HOST=localhost" >> .env
echo "REDIS_PORT=6379" >> .env
echo "REDIS_PASSWORD=$REDIS_PASSWORD" >> .env
echo "REDIS_DB=0" >> .env

# Install Redis Python package
pip install redis==5.0.1

# Create redis_config.py
echo "Creating Redis configuration module..."
mkdir -p app/config
cat > app/config/redis_config.py << 'EOFREDIS'
# app/config/redis_config.py
"""
Redis configuration for Flask-Session.

This module provides Redis session configuration for multi-worker
environments to ensure session persistence across Gunicorn workers.
"""

import os
import redis
from flask_session import Session

class RedisConfig:
    """Redis configuration for session management."""
    
    # Redis connection settings
    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)
    REDIS_DB = int(os.environ.get('REDIS_DB', 0))
    
    # Session configuration
    SESSION_TYPE = 'redis'
    SESSION_REDIS = None  # Will be set in init_redis_session
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'chatmrpt:'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours in seconds
    
    # Additional Redis settings
    SESSION_REDIS_SOCKET_TIMEOUT = 30
    SESSION_REDIS_RETRY_ON_TIMEOUT = True
    SESSION_REDIS_HEALTH_CHECK = True
    
    @classmethod
    def init_redis_session(cls, app):
        """Initialize Redis session store."""
        try:
            # Create Redis client
            redis_client = redis.StrictRedis(
                host=cls.REDIS_HOST,
                port=cls.REDIS_PORT,
                password=cls.REDIS_PASSWORD,
                db=cls.REDIS_DB,
                decode_responses=False,  # Required for Flask-Session
                socket_connect_timeout=cls.SESSION_REDIS_SOCKET_TIMEOUT,
                socket_timeout=cls.SESSION_REDIS_SOCKET_TIMEOUT,
                retry_on_timeout=cls.SESSION_REDIS_RETRY_ON_TIMEOUT,
                health_check_interval=30 if cls.SESSION_REDIS_HEALTH_CHECK else 0
            )
            
            # Test connection
            redis_client.ping()
            
            # Configure Flask app
            app.config['SESSION_TYPE'] = cls.SESSION_TYPE
            app.config['SESSION_REDIS'] = redis_client
            app.config['SESSION_PERMANENT'] = cls.SESSION_PERMANENT
            app.config['SESSION_USE_SIGNER'] = cls.SESSION_USE_SIGNER
            app.config['SESSION_KEY_PREFIX'] = cls.SESSION_KEY_PREFIX
            app.config['PERMANENT_SESSION_LIFETIME'] = cls.PERMANENT_SESSION_LIFETIME
            
            # Initialize Flask-Session
            Session(app)
            
            app.logger.info(f"✅ Redis session store initialized at {cls.REDIS_HOST}:{cls.REDIS_PORT}")
            return True
            
        except redis.ConnectionError as e:
            app.logger.error(f"❌ Failed to connect to Redis: {e}")
            app.logger.warning("⚠️ Falling back to filesystem sessions")
            return False
        except Exception as e:
            app.logger.error(f"❌ Redis session initialization error: {e}")
            return False
    
    @classmethod
    def get_redis_info(cls, app):
        """Get Redis server information."""
        try:
            if app.config.get('SESSION_REDIS'):
                info = app.config['SESSION_REDIS'].info()
                return {
                    'connected': True,
                    'version': info.get('redis_version'),
                    'used_memory': info.get('used_memory_human'),
                    'connected_clients': info.get('connected_clients'),
                    'db_keys': app.config['SESSION_REDIS'].dbsize()
                }
        except:
            pass
        return {'connected': False}
EOFREDIS

# Update app/__init__.py to use Redis
echo "Updating app initialization for Redis..."
# Add Redis initialization in app/__init__.py
sed -i '/# --- Initialize Extensions ---/,/Session(app)/{
s/Session(app)/# Try to initialize Redis sessions, fall back to filesystem if Redis is not available\
    from .config.redis_config import RedisConfig\
    redis_initialized = RedisConfig.init_redis_session(app)\
    \
    if not redis_initialized:\
        # Fall back to filesystem sessions\
        Session(app)/
}' app/__init__.py

# Restart Gunicorn
echo ""
echo "=== Restarting Application ==="
sudo systemctl restart gunicorn

# Check status
echo ""
echo "=== Checking Status ==="
sudo systemctl status gunicorn --no-pager
sudo systemctl status redis --no-pager

echo ""
echo "=== Deployment Complete! ==="
echo ""
echo "Redis password saved in .env file"
echo "To test Redis connection: redis-cli -a '$REDIS_PASSWORD' ping"
echo "To check session status: curl http://localhost/api/session/redis-status"
echo ""
echo "TPR workflow fixes have been deployed!"