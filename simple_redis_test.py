#!/usr/bin/env python3
"""
Simple Redis test that doesn't require Flask
"""

import redis
import json
import time
import traceback

def test_redis():
    """Simple Redis test"""

    print("\n🔍 SIMPLE REDIS TEST")
    print("=" * 60)

    # Hardcoded Redis settings
    host = "chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com"
    port = 6379

    print(f"Host: {host}")
    print(f"Port: {port}")

    try:
        print("\n1. Attempting connection...")
        client = redis.StrictRedis(
            host=host,
            port=port,
            db=0,
            socket_connect_timeout=5,
            socket_timeout=5,
            decode_responses=True
        )

        print("2. Testing ping...")
        result = client.ping()
        print(f"   Ping result: {result}")

        print("\n3. Testing write...")
        test_key = f"test:simple:{int(time.time())}"
        test_value = "Hello from ChatMRPT test"
        client.set(test_key, test_value, ex=60)
        print(f"   Wrote: {test_key} = {test_value}")

        print("\n4. Testing read...")
        retrieved = client.get(test_key)
        print(f"   Read: {retrieved}")

        if retrieved == test_value:
            print("   ✅ Values match!")
        else:
            print("   ❌ Values don't match!")

        print("\n5. Checking for ChatMRPT keys...")
        keys = client.keys("chatmrpt:*")
        print(f"   Found {len(keys)} ChatMRPT keys")

        if keys:
            print("\n   First 5 keys:")
            for key in keys[:5]:
                print(f"   - {key}")

        # Check conversation states specifically
        conv_keys = client.keys("chatmrpt:conversation_state:*")
        print(f"\n6. Found {len(conv_keys)} conversation state keys")

        if conv_keys:
            print("\n   Checking first conversation state:")
            first_key = conv_keys[0]
            print(f"   Key: {first_key}")

            value = client.get(first_key)
            if value:
                try:
                    data = json.loads(value)
                    print(f"   History entries: {len(data.get('history', []))}")
                    if 'last_message' in data:
                        print(f"   Last message: {data['last_message'][:50]}...")
                    if 'history' in data and data['history']:
                        print(f"   First exchange:")
                        first = data['history'][0]
                        if 'user' in first:
                            print(f"     User: {first['user'][:50]}...")
                        if 'assistant' in first:
                            print(f"     Assistant: {first['assistant'][:50]}...")
                except:
                    print("   Could not parse conversation data")

        print("\n✅ Redis is working!")
        return True

    except redis.ConnectionError as e:
        print(f"\n❌ Connection Error: {e}")
        return False

    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_redis()