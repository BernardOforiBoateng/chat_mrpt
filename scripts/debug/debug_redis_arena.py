#!/usr/bin/env python3
"""
Debug Redis Arena Storage Implementation
Tests Redis storage operations directly
"""

import sys
import os
import json
import redis
import asyncio
from datetime import datetime, timedelta
import uuid

# Add the app directory to path
sys.path.insert(0, '/home/ec2-user/ChatMRPT')

def test_redis_connection():
    """Test basic Redis connectivity"""
    print("\n=== Testing Redis Connection ===")
    try:
        r = redis.StrictRedis(
            host='chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com',
            port=6379,
            db=1,
            socket_connect_timeout=5,
            decode_responses=True
        )
        
        # Test ping
        r.ping()
        print("✅ Redis ping successful")
        
        # Test set/get
        test_key = f"test_{uuid.uuid4().hex[:8]}"
        test_value = {"test": "data", "timestamp": datetime.now().isoformat()}
        r.setex(test_key, 60, json.dumps(test_value))
        retrieved = json.loads(r.get(test_key))
        print(f"✅ Set/Get test successful: {retrieved}")
        
        # Clean up
        r.delete(test_key)
        return True
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False


def test_arena_manager():
    """Test ArenaManager with Redis storage"""
    print("\n=== Testing ArenaManager ===")
    
    try:
        from app.core.arena_manager_redis import ArenaManager, BattleSession
        
        # Initialize manager
        models_config = {
            'llama3.2-3b': {'type': 'ollama', 'display_name': 'Llama 3.1 8B'},
            'phi3-mini': {'type': 'ollama', 'display_name': 'Phi-3 Mini'},
        }
        
        manager = ArenaManager(models_config)
        print(f"✅ ArenaManager initialized")
        print(f"   Storage status: {manager.storage_status}")
        
        # Test battle creation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def create_test_battle():
            battle_info = await manager.start_battle(
                "Test query: What is 2+2?",
                session_id=f"test_{uuid.uuid4().hex[:8]}"
            )
            return battle_info
        
        battle_info = loop.run_until_complete(create_test_battle())
        loop.close()
        
        print(f"✅ Battle created: {battle_info['battle_id'][:8]}...")
        
        # Test battle retrieval from dict
        battle_from_dict = manager.battle_sessions.get(battle_info['battle_id'])
        if battle_from_dict:
            print(f"✅ Battle found in memory dict")
        else:
            print(f"⚠️  Battle not in memory dict")
        
        # Test battle retrieval from Redis
        if hasattr(manager, 'storage') and manager.storage:
            retrieved_battle = manager.storage.get_battle(battle_info['battle_id'])
            if retrieved_battle:
                print(f"✅ Battle retrieved from Redis")
                print(f"   Models: {retrieved_battle.model_a} vs {retrieved_battle.model_b}")
            else:
                print(f"❌ Battle not found in Redis")
        else:
            print(f"❌ No Redis storage configured in manager")
        
        return battle_info['battle_id']
        
    except Exception as e:
        print(f"❌ ArenaManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_battle_retrieval(battle_id=None):
    """Test retrieving battle from different contexts"""
    print("\n=== Testing Battle Retrieval ===")
    
    if not battle_id:
        print("⚠️  No battle_id provided, creating new one")
        battle_id = test_arena_manager()
        if not battle_id:
            print("❌ Failed to create test battle")
            return
    
    try:
        from app.core.arena_manager_redis import ArenaManager, RedisStorage
        
        # Test direct Redis retrieval
        storage = RedisStorage()
        battle = storage.get_battle(battle_id)
        
        if battle:
            print(f"✅ Direct Redis retrieval successful")
            print(f"   Battle ID: {battle.session_id[:8]}...")
            print(f"   Models: {battle.model_a} vs {battle.model_b}")
            print(f"   Status: {battle.status}")
        else:
            print(f"❌ Direct Redis retrieval failed")
            
            # Check if key exists
            r = redis.StrictRedis(
                host='chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com',
                port=6379,
                db=1,
                decode_responses=True
            )
            
            keys = r.keys("arena:battle:*")
            print(f"   Found {len(keys)} battle keys in Redis:")
            for key in keys[:5]:  # Show first 5
                print(f"     - {key}")
                
    except Exception as e:
        print(f"❌ Battle retrieval test failed: {e}")
        import traceback
        traceback.print_exc()


def test_route_handler():
    """Test the actual route handler logic"""
    print("\n=== Testing Route Handler Logic ===")
    
    try:
        # Import Flask app to get proper context
        import sys
        sys.path.insert(0, '/home/ec2-user/ChatMRPT')
        
        from app import create_app
        from app.web.routes.arena_routes import arena_manager
        
        app = create_app()
        
        with app.app_context():
            print(f"Arena manager initialized: {arena_manager is not None}")
            
            if arena_manager:
                print(f"Storage configured: {hasattr(arena_manager, 'storage')}")
                if hasattr(arena_manager, 'storage'):
                    print(f"Storage type: {type(arena_manager.storage)}")
                    print(f"Storage status: {arena_manager.storage_status}")
                    
                # Check battle_sessions attribute
                print(f"Has battle_sessions dict: {hasattr(arena_manager, 'battle_sessions')}")
                
    except Exception as e:
        print(f"❌ Route handler test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("="*60)
    print("REDIS ARENA STORAGE DEBUG")
    print("="*60)
    
    # Run tests
    redis_ok = test_redis_connection()
    
    if redis_ok:
        battle_id = test_arena_manager()
        if battle_id:
            test_battle_retrieval(battle_id)
        test_route_handler()
    
    print("\n" + "="*60)
    print("DEBUG COMPLETE")
    print("="*60)