#!/usr/bin/env python3
"""
Update base.py to use Redis when available
"""
import re
import sys

# Read the base.py file
with open('app/config/base.py', 'r') as f:
    content = f.read()

# Find the SESSION_TYPE line and replace with Redis-aware configuration
old_pattern = r"(\s+# Session Configuration\s+)SESSION_TYPE = 'filesystem'"
new_config = r'''\1# Session configuration - use Redis if available
    import os
    if os.environ.get('REDIS_HOST'):
        SESSION_TYPE = 'redis'
        try:
            import redis
            SESSION_REDIS = redis.StrictRedis(
                host=os.environ.get('REDIS_HOST', 'localhost'),
                port=int(os.environ.get('REDIS_PORT', 6379)),
                db=int(os.environ.get('REDIS_DB', 0)),
                decode_responses=False
            )
            print("Redis session store configured")
        except Exception as e:
            print(f"Failed to configure Redis: {e}")
            SESSION_TYPE = 'filesystem'
    else:
        SESSION_TYPE = 'filesystem' '''

# Replace the configuration
content = re.sub(old_pattern, new_config, content, flags=re.MULTILINE)

# Write back
with open('app/config/base.py', 'w') as f:
    f.write(content)

print("Configuration updated successfully")