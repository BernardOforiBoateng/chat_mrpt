#!/usr/bin/env python3
"""
Check what conversations are stored in Redis
"""

import redis
import json
import time

# Connect to Redis
r = redis.StrictRedis(
    host='chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com',
    port=6379,
    decode_responses=True
)

# Get all conversation keys
keys = r.keys('chatmrpt:conversation_state:*')
print(f"\nTotal conversation state keys: {len(keys)}")

if keys:
    print("\nLast 5 conversations:")
    print("-" * 60)

    for key in keys[-5:]:
        session_id = key.split(':')[-1]
        value = r.get(key)

        if value:
            try:
                data = json.loads(value)
                history = data.get('history', [])
                print(f"\nSession: ...{session_id[-12:]}")
                print(f"  Exchanges: {len(history)}")

                if history:
                    last = history[-1]
                    if 'user' in last:
                        print(f"  Last user: {last['user'][:60]}...")
                    if 'assistant' in last:
                        print(f"  Last asst: {last['assistant'][:60]}...")

            except Exception as e:
                print(f"  Error parsing: {e}")
        else:
            print(f"\nSession: ...{session_id[-12:]}")
            print(f"  No data")

# Check for our test sessions
print("\n" + "=" * 60)
print("Checking test sessions:")

test_patterns = [
    'flow-test-*',
    'context-test-*',
    'prompt-test-*',
    'actual-test-*'
]

for pattern in test_patterns:
    test_keys = r.keys(f'chatmrpt:conversation_state:{pattern}')
    if test_keys:
        print(f"  {pattern}: Found {len(test_keys)} keys")
        for key in test_keys[:2]:
            print(f"    - {key}")
    else:
        print(f"  {pattern}: No keys found")