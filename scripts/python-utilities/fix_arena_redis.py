#!/usr/bin/env python3
"""
Fix Arena Redis Implementation
Adds missing methods and properties to ArenaManager
"""

import os
import sys

def fix_arena_manager():
    """Add get_battle method and storage_status property to ArenaManager"""
    
    # The code to add to ArenaManager class
    new_methods = '''
    def get_battle(self, battle_id: str) -> Optional[BattleSession]:
        """
        Get battle from Redis storage (or fallback).
        
        Args:
            battle_id: Battle session ID
            
        Returns:
            BattleSession object or None if not found
        """
        # First try Redis storage
        if self.storage:
            battle = self.storage.get_battle(battle_id)
            if battle:
                return battle
        
        # Fall back to in-memory dict if not in Redis
        return self.battle_sessions.get(battle_id)
    
    @property
    def storage_status(self) -> str:
        """Get current storage status."""
        if self.storage and self.storage.connected:
            return "Redis Connected"
        elif self.storage:
            return "Redis Fallback (In-Memory)"
        else:
            return "In-Memory Only"
'''
    
    print("Methods to add to ArenaManager:")
    print(new_methods)
    print("\n" + "="*60)
    
    # Fix for arena_routes.py
    route_fix = '''
# In arena_routes.py, line 179-180, replace:
#     battle = arena_manager.battle_sessions.get(battle_id)
# With:
#     battle = arena_manager.get_battle(battle_id)

# Also in arena_routes.py, add to the status endpoint response (around line 61):
#     'storage_status': arena_manager.storage_status,
'''
    
    print("Fixes needed in arena_routes.py:")
    print(route_fix)
    print("\n" + "="*60)
    
    # Create deployment script
    deployment_script = '''#!/bin/bash
# Deploy Arena Redis Fixes

echo "Deploying Arena Redis fixes..."

INSTANCES="3.21.167.170 18.220.103.20"
KEY_PATH="/tmp/chatmrpt-key2.pem"

for IP in $INSTANCES; do
    echo "Fixing $IP..."
    
    # Add get_battle and storage_status to ArenaManager
    ssh -o StrictHostKeyChecking=no -i "$KEY_PATH" ec2-user@$IP << 'EOFFIX'
        cd /home/ec2-user/ChatMRPT
        
        # Backup current files
        cp app/core/arena_manager_redis.py app/core/arena_manager_redis.py.backup
        cp app/web/routes/arena_routes.py app/web/routes/arena_routes.py.backup
        
        # Add get_battle method to ArenaManager (after line 548)
        sed -i '548a\\
    \\
    def get_battle(self, battle_id: str) -> Optional[BattleSession]:\\
        """\\
        Get battle from Redis storage (or fallback).\\
        \\
        Args:\\
            battle_id: Battle session ID\\
            \\
        Returns:\\
            BattleSession object or None if not found\\
        """\\
        # First try Redis storage\\
        if self.storage:\\
            battle = self.storage.get_battle(battle_id)\\
            if battle:\\
                return battle\\
        \\
        # Fall back to in-memory dict if not in Redis\\
        return self.battle_sessions.get(battle_id)\\
    \\
    @property\\
    def storage_status(self) -> str:\\
        """Get current storage status."""\\
        if self.storage and self.storage.connected:\\
            return "Redis Connected"\\
        elif self.storage:\\
            return "Redis Fallback (In-Memory)"\\
        else:\\
            return "In-Memory Only"' app/core/arena_manager_redis.py
        
        # Fix arena_routes.py to use get_battle
        sed -i 's/arena_manager\.battle_sessions\.get(battle_id)/arena_manager.get_battle(battle_id)/' app/web/routes/arena_routes.py
        
        # Add storage_status to status endpoint
        sed -i "/return jsonify({/,/})/ {
            /'"'"'available'"'"': True,/a\\
            '"'"'storage_status'"'"': arena_manager.storage_status if arena_manager else '"'"'Unknown'"'"',
        }" app/web/routes/arena_routes.py
        
        # Restart service
        sudo systemctl restart chatmrpt
        
        echo "✅ Fixed $IP"
EOFFIX
    
done

echo "✅ All instances updated"
'''
    
    print("Deployment script:")
    print(deployment_script)
    
    # Write deployment script
    with open('deploy_arena_redis_fix.sh', 'w') as f:
        f.write(deployment_script)
    
    os.chmod('deploy_arena_redis_fix.sh', 0o755)
    print("\n✅ Created deployment script: deploy_arena_redis_fix.sh")

if __name__ == "__main__":
    fix_arena_manager()