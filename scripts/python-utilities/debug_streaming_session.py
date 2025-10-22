#!/usr/bin/env python3
"""Debug streaming endpoint session handling"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from flask import session
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create app
app = create_app('development')

def test_streaming_session_update():
    """Test if streaming endpoint updates session correctly"""
    
    with app.test_client() as client:
        with app.app_context():
            # 1. Initialize session
            response = client.get('/')
            print(f"1. Initial request - Session ID: {session.get('session_id', 'NOT SET')}")
            
            # 2. Check debug endpoint
            response = client.get('/debug/session_state')
            data = response.get_json()
            print(f"2. Debug state: {data}")
            
            # 3. Simulate analysis via streaming
            print("\n3. Testing streaming endpoint session update...")
            
            # Mock the streaming endpoint behavior
            with client.session_transaction() as sess:
                sess['session_id'] = 'test-session-id'
                sess['csv_loaded'] = True
                sess['shapefile_loaded'] = True
                print(f"   Session before analysis: {dict(sess)}")
            
            # Simulate what happens in streaming endpoint
            with client.session_transaction() as sess:
                # This is what the streaming endpoint should do
                sess['analysis_complete'] = True
                sess['analysis_type'] = 'composite'
                sess.modified = True
                print(f"   Session after analysis update: {dict(sess)}")
            
            # 4. Check if session persisted
            response = client.get('/debug/session_state')
            data = response.get_json()
            print(f"\n4. Debug state after analysis: {data}")
            
            # 5. Check if analysis_complete is true
            if data['session_state']['analysis_complete']:
                print("\n✅ SUCCESS: Session update persisted!")
            else:
                print("\n❌ FAILURE: Session update did not persist!")
                
            # 6. Test actual streaming endpoint
            print("\n6. Testing actual streaming endpoint...")
            response = client.post('/send_message_streaming', 
                                 json={'message': 'hello'},
                                 headers={'Content-Type': 'application/json'})
            print(f"   Streaming response status: {response.status_code}")

if __name__ == "__main__":
    test_streaming_session_update()