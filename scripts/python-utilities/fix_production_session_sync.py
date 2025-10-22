#!/usr/bin/env python3
"""
Fix production session synchronization issues for TPR downloads and ITN exports.
This script addresses Redis session state synchronization in multi-worker environments.
"""

import sys
import os
import json
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_redis_session_config():
    """Check current Redis session configuration"""
    print("=== Checking Redis Session Configuration ===")
    print(f"Date: {datetime.now()}")
    print("")
    
    # Check if Redis sessions are enabled
    from app import create_app
    app = create_app()
    
    with app.app_context():
        print(f"Session Type: {app.config.get('SESSION_TYPE', 'filesystem')}")
        print(f"Redis Sessions Enabled: {app.config.get('ENABLE_REDIS_SESSIONS', False)}")
        print(f"Redis URL: {app.config.get('REDIS_URL', 'Not configured')}")
        print(f"Session Cookie Secure: {app.config.get('SESSION_COOKIE_SECURE', False)}")
        print(f"Session Cookie SameSite: {app.config.get('SESSION_COOKIE_SAMESITE', 'None')}")
        print(f"Session Permanent: {app.config.get('SESSION_PERMANENT', True)}")
        print("")
        
        # Test Redis connection
        if app.config.get('ENABLE_REDIS_SESSIONS'):
            try:
                import redis
                r = redis.from_url(app.config['REDIS_URL'])
                r.ping()
                print("✅ Redis connection successful")
                
                # Check session keys
                session_keys = list(r.scan_iter("session:*"))
                print(f"Active sessions in Redis: {len(session_keys)}")
                
                # Sample session data
                if session_keys:
                    sample_key = session_keys[0]
                    session_data = r.get(sample_key)
                    if session_data:
                        print(f"Sample session size: {len(session_data)} bytes")
                
            except Exception as e:
                print(f"❌ Redis connection error: {e}")
        else:
            print("⚠️ Redis sessions not enabled")

def create_session_sync_fix():
    """Create fixes for session synchronization issues"""
    
    print("\n=== Creating Session Synchronization Fixes ===\n")
    
    # Fix 1: Update TPR handler to force session save
    tpr_handler_fix = '''
# Add this to app/tpr_module/integration/tpr_handler.py after line 646
# Force Redis session write
try:
    # Import within try block to handle import context
    from flask import current_app
    if current_app.config.get('ENABLE_REDIS_SESSIONS'):
        # Force immediate Redis write
        from app.core.session_manager import SessionManager
        session_manager = SessionManager()
        session_manager.force_save(session)
        logger.info(f"Forced Redis session save for TPR download links")
except Exception as e:
    logger.warning(f"Could not force session save: {e}")
'''
    
    # Fix 2: Add session manager for Redis operations
    session_manager_content = '''"""
Session Manager for Redis Operations
Handles forced session saves and synchronization in multi-worker environments
"""

import logging
import pickle
import redis
from flask import current_app, session
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages Redis session operations for multi-worker synchronization"""
    
    def __init__(self):
        self.redis_client = None
        self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis connection"""
        try:
            if current_app.config.get('ENABLE_REDIS_SESSIONS'):
                redis_url = current_app.config.get('REDIS_URL')
                if redis_url:
                    self.redis_client = redis.from_url(redis_url)
                    self.redis_client.ping()
                    logger.info("SessionManager: Redis connection established")
        except Exception as e:
            logger.error(f"SessionManager: Failed to connect to Redis: {e}")
    
    def force_save(self, session_data: Dict[str, Any]) -> bool:
        """Force save session to Redis immediately"""
        if not self.redis_client:
            logger.warning("SessionManager: Redis not available")
            return False
        
        try:
            session_id = session_data.get('session_id')
            if not session_id:
                logger.warning("SessionManager: No session_id found")
                return False
            
            # Serialize session data
            session_key = f"session:{session_id}"
            serialized_data = pickle.dumps(dict(session_data))
            
            # Save to Redis with TTL
            ttl = current_app.config.get('PERMANENT_SESSION_LIFETIME', 86400)
            self.redis_client.setex(session_key, ttl, serialized_data)
            
            logger.info(f"SessionManager: Forced save for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"SessionManager: Force save failed: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data from Redis"""
        if not self.redis_client:
            return None
        
        try:
            session_key = f"session:{session_id}"
            data = self.redis_client.get(session_key)
            
            if data:
                return pickle.loads(data)
            return None
            
        except Exception as e:
            logger.error(f"SessionManager: Failed to get session: {e}")
            return None
    
    def refresh_session(self, session_id: str) -> bool:
        """Refresh session TTL"""
        if not self.redis_client:
            return False
        
        try:
            session_key = f"session:{session_id}"
            ttl = current_app.config.get('PERMANENT_SESSION_LIFETIME', 86400)
            return bool(self.redis_client.expire(session_key, ttl))
            
        except Exception as e:
            logger.error(f"SessionManager: Failed to refresh session: {e}")
            return False
'''
    
    # Fix 3: Update streaming response to include session state
    streaming_fix = '''
# Add this to the streaming response handler in analysis_routes.py
# After TPR completion is detected, force session read
if tpr_result.get('stage') == 'completed':
    # Force fresh session read from Redis
    try:
        from app.core.session_manager import SessionManager
        session_manager = SessionManager()
        fresh_session = session_manager.get_session(session_id)
        if fresh_session and 'tpr_download_links' in fresh_session:
            tpr_result['download_links'] = fresh_session['tpr_download_links']
            logger.info(f"Retrieved TPR download links from Redis for streaming response")
    except Exception as e:
        logger.warning(f"Could not retrieve fresh session: {e}")
'''
    
    # Fix 4: Client-side retry mechanism
    client_fix = '''
// Add this to tpr-download-manager.js in checkForExistingDownloads method
// Add retry logic for download links
async checkForExistingDownloads(retryCount = 0) {
    try {
        const response = await fetch('/api/tpr/download-links');
        if (response.ok) {
            const data = await response.json();
            console.log('📥 TPR download links response:', data);
            
            // If no links found and we haven't retried much, retry after delay
            if ((!data.download_links || data.download_links.length === 0) && retryCount < 3) {
                console.log(`⏳ No download links yet, retrying in 2 seconds... (attempt ${retryCount + 1}/3)`);
                setTimeout(() => {
                    this.checkForExistingDownloads(retryCount + 1);
                }, 2000);
                return;
            }
            
            // Process links as before...
        }
    } catch (error) {
        console.error('❌ Error checking for existing downloads:', error);
    }
}
'''
    
    print("Fix 1: TPR Handler Session Force Save")
    print("-" * 50)
    print(tpr_handler_fix)
    print("")
    
    print("Fix 2: Session Manager (save as app/core/session_manager.py)")
    print("-" * 50)
    print("Creating session_manager.py...")
    
    # Write session manager file
    session_manager_path = "app/core/session_manager.py"
    with open(session_manager_path, 'w') as f:
        f.write(session_manager_content)
    print(f"✅ Created {session_manager_path}")
    print("")
    
    print("Fix 3: Streaming Response Session Refresh")
    print("-" * 50)
    print(streaming_fix)
    print("")
    
    print("Fix 4: Client-side Retry Mechanism")
    print("-" * 50)
    print(client_fix)
    print("")
    
    return session_manager_path

def create_deployment_script():
    """Create deployment script for the fixes"""
    
    deployment_script = '''#!/bin/bash
# Deploy session synchronization fixes to production

set -e

echo "=== Deploying Session Synchronization Fixes ==="
echo "Date: $(date)"
echo ""

SSH_KEY="/tmp/chatmrpt-key2.pem"
STAGING_HOST="ec2-user@18.117.115.217"
PROD_IP="172.31.44.52"

# Ensure we have the SSH key
if [ ! -f "$SSH_KEY" ]; then
    cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
    chmod 600 /tmp/chatmrpt-key2.pem
fi

echo "📋 Step 1: Backing up current files..."
ssh -i "$SSH_KEY" "$STAGING_HOST" << 'BACKUP'
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 << 'PROD_BACKUP'
        cd /home/ec2-user/ChatMRPT
        
        # Backup current files
        cp app/tpr_module/integration/tpr_handler.py app/tpr_module/integration/tpr_handler.py.backup_$(date +%Y%m%d_%H%M%S)
        cp app/web/routes/analysis_routes.py app/web/routes/analysis_routes.py.backup_$(date +%Y%m%d_%H%M%S)
        
        echo "✅ Backups created"
PROD_BACKUP
BACKUP

echo ""
echo "📋 Step 2: Copying new files..."

# Copy session manager
scp -i "$SSH_KEY" app/core/session_manager.py "$STAGING_HOST":~/
ssh -i "$SSH_KEY" "$STAGING_HOST" 'scp -i ~/.ssh/chatmrpt-key.pem ~/session_manager.py ec2-user@172.31.44.52:~/ChatMRPT/app/core/'

echo ""
echo "📋 Step 3: Applying fixes..."
echo "Please manually apply the code changes shown above to:"
echo "1. app/tpr_module/integration/tpr_handler.py (after line 646)"
echo "2. app/web/routes/analysis_routes.py (in streaming response handler)"
echo "3. app/static/js/modules/data/tpr-download-manager.js (update checkForExistingDownloads)"

echo ""
echo "📋 Step 4: After applying fixes, restart the service:"
echo "ssh -i $SSH_KEY $STAGING_HOST 'ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 \\"sudo systemctl restart chatmrpt\\"'"

echo ""
echo "✅ Deployment script ready. Apply the fixes and test!"
'''
    
    script_path = "deploy_session_sync_fix.sh"
    with open(script_path, 'w') as f:
        f.write(deployment_script)
    os.chmod(script_path, 0o755)
    
    print(f"\n✅ Created deployment script: {script_path}")
    return script_path

def main():
    """Main function"""
    print("ChatMRPT Production Session Synchronization Fix")
    print("=" * 50)
    print("")
    
    # Check current configuration
    check_redis_session_config()
    
    # Create fixes
    session_manager_path = create_session_sync_fix()
    
    # Create deployment script
    deployment_script = create_deployment_script()
    
    print("\n=== Summary ===")
    print("The session synchronization issues are caused by:")
    print("1. Session state not being immediately written to Redis")
    print("2. Different workers not seeing updated session state")
    print("3. No retry mechanism on the client side")
    print("")
    print("Fixes created:")
    print(f"1. Session Manager: {session_manager_path}")
    print(f"2. Deployment Script: {deployment_script}")
    print("")
    print("Next steps:")
    print("1. Review the code changes above")
    print("2. Apply the fixes to the respective files")
    print("3. Run the deployment script")
    print("4. Test TPR downloads and ITN exports")

if __name__ == "__main__":
    main()