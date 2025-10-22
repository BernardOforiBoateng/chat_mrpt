#!/usr/bin/env python3
"""
Fix Redis configuration in ChatMRPT base config
"""
import sys

# Read the base.py file content from stdin
content = sys.stdin.read()

# Replace SESSION_TYPE line to check for Redis
old_line = "    SESSION_TYPE = 'filesystem'"
new_lines = """    # Session configuration - use Redis if available
    import os
    if os.environ.get('REDIS_HOST'):
        SESSION_TYPE = 'redis'
        import redis
        SESSION_REDIS = redis.StrictRedis(
            host=os.environ.get('REDIS_HOST', 'localhost'),
            port=int(os.environ.get('REDIS_PORT', 6379)),
            db=int(os.environ.get('REDIS_DB', 0)),
            decode_responses=False
        )
    else:
        SESSION_TYPE = 'filesystem'"""

# Replace the line
content = content.replace(old_line, new_lines)

# Write to stdout
print(content)