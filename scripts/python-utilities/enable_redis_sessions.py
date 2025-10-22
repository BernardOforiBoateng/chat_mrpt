#!/usr/bin/env python3
"""
Enable Redis sessions for ChatMRPT
This script updates the configuration to use Redis for session storage
"""

import os

# Redis configuration for staging
REDIS_HOST = "chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com"
REDIS_PORT = 6379

# Create .env file with Redis settings
env_content = f"""
# Redis Configuration
REDIS_URL=redis://{REDIS_HOST}:{REDIS_PORT}/0
REDIS_HOST={REDIS_HOST}
REDIS_PORT={REDIS_PORT}
ENABLE_REDIS_SESSIONS=true

# Keep existing settings
FLASK_ENV=development
FLASK_DEBUG=False
"""

print("Redis Session Enabler for ChatMRPT")
print("=" * 50)
print(f"Redis Host: {REDIS_HOST}")
print(f"Redis Port: {REDIS_PORT}")
print("=" * 50)

# Write .env file
with open('.env', 'w') as f:
    f.write(env_content.strip())
print("✅ Created .env file with Redis settings")

# Create session helper for DataFrames
session_helper = '''"""
Session helper for handling DataFrame serialization with Redis
"""
import pandas as pd
import json
from flask import session

class SessionHelper:
    """Helper class for Redis-compatible session management"""
    
    @staticmethod
    def store_dataframe(key, df):
        """Store DataFrame in session as JSON"""
        if df is not None:
            session[key] = df.to_json(orient='split', date_format='iso')
        else:
            session[key] = None
    
    @staticmethod
    def load_dataframe(key):
        """Load DataFrame from session JSON"""
        if key in session and session[key]:
            return pd.read_json(session[key], orient='split')
        return None
    
    @staticmethod
    def store_data(key, data):
        """Store any JSON-serializable data"""
        session[key] = json.dumps(data) if data is not None else None
    
    @staticmethod
    def load_data(key, default=None):
        """Load JSON data from session"""
        if key in session and session[key]:
            return json.loads(session[key])
        return default
    
    @staticmethod
    def clear_analysis_data():
        """Clear analysis-related session data"""
        keys_to_clear = [
            'nmep_data', 'raw_data', 'analysis_results',
            'viz_data', 'current_analysis', 'tpr_data'
        ]
        for key in keys_to_clear:
            session.pop(key, None)
'''

with open('app/core/session_helper.py', 'w') as f:
    f.write(session_helper)
print("✅ Created session helper for DataFrame handling")

print("\nNext steps:")
print("1. Update app initialization to use Redis")
print("2. Replace direct session['dataframe'] calls with SessionHelper")
print("3. Test with multiple workers")