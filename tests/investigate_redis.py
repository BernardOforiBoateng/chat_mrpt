#!/usr/bin/env python3
"""
Investigate Redis connectivity and conversation storage
"""

import redis
import json
import os

def test_redis_connection():
    """Test if we can connect to Redis from local environment"""

    print("\n🔍 REDIS INVESTIGATION")
    print("=" * 60)

    # Redis configuration from production
    redis_host = "chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com"
    redis_port = 6379

    print(f"Testing connection to: {redis_host}:{redis_port}")

    try:
        # Try to connect
        client = redis.StrictRedis(
            host=redis_host,
            port=redis_port,
            db=0,
            socket_connect_timeout=5,
            socket_timeout=5,
            decode_responses=True,
        )

        # Test ping
        print("Attempting ping...")
        client.ping()
        print("✅ Redis ping successful!")

        # Test write
        test_key = "chatmrpt:test:connection"
        test_value = "test_value_12345"
        print(f"\nTesting write: {test_key} = {test_value}")
        client.set(test_key, test_value, ex=60)  # Expire in 60 seconds
        print("✅ Write successful")

        # Test read
        print(f"Testing read: {test_key}")
        retrieved = client.get(test_key)
        print(f"Retrieved: {retrieved}")

        if retrieved == test_value:
            print("✅ Read successful - values match!")
        else:
            print("❌ Read failed - values don't match")

        # List all ChatMRPT keys
        print("\n📋 Existing ChatMRPT keys in Redis:")
        keys = client.keys("chatmrpt:*")
        if keys:
            for key in keys[:10]:  # Show first 10
                print(f"  - {key}")
            if len(keys) > 10:
                print(f"  ... and {len(keys) - 10} more")
        else:
            print("  No keys found")

        # Check for conversation state keys specifically
        print("\n🗣️ Conversation state keys:")
        conv_keys = client.keys("chatmrpt:conversation_state:*")
        if conv_keys:
            for key in conv_keys[:5]:
                print(f"  - {key}")
                # Try to read the value
                try:
                    value = client.get(key)
                    if value:
                        data = json.loads(value)
                        print(f"    History entries: {len(data.get('history', []))}")
                        if 'last_message' in data:
                            print(f"    Last message: {data['last_message'][:50]}...")
                except:
                    pass
        else:
            print("  No conversation state keys found")

        print("\n✅ Redis is accessible from outside AWS!")
        return True

    except redis.ConnectionError as e:
        print(f"\n❌ Connection failed: {e}")
        print("\nPossible issues:")
        print("1. Redis might be behind a VPC that blocks external access")
        print("2. Security group might not allow external connections")
        print("3. ElastiCache might be configured for VPC-only access")
        return False

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

def analyze_redis_config():
    """Analyze what the Redis configuration should be"""

    print("\n📝 Redis Configuration Analysis")
    print("=" * 60)

    print("Expected Redis setup:")
    print("- Host: chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com")
    print("- Port: 6379")
    print("- Database: 0")
    print("")
    print("ElastiCache characteristics:")
    print("- Usually VPC-only (not internet accessible)")
    print("- Requires connection from within same VPC")
    print("- EC2 instances in same VPC can connect")
    print("")
    print("This means:")
    print("1. ✅ EC2 instances SHOULD be able to connect")
    print("2. ❌ External connections (like this test) will likely FAIL")
    print("3. 🔧 Need to test FROM the EC2 instances themselves")

if __name__ == "__main__":
    test_redis_connection()
    analyze_redis_config()