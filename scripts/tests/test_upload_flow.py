#!/usr/bin/env python3
"""Test script to diagnose upload issues on AWS"""

import os
import sys
import requests
from pathlib import Path

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_local_data_handler():
    """Test data handler locally"""
    print("\n=== Testing DataHandler Locally ===")
    try:
        from app.services.data_handler import UnifiedDataHandler
        from flask import Flask
        
        # Create minimal Flask app
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test'
        
        with app.app_context():
            # Create handler
            handler = UnifiedDataHandler(session_id='test-session')
            print(f"DataHandler created with session_id: {handler.session_id}")
            print(f"Upload path: {handler.upload_path}")
            print(f"Upload path exists: {os.path.exists(handler.upload_path)}")
            
            # Check if it can find files
            csv_files = list(Path(handler.upload_path).glob("*.csv"))
            print(f"CSV files found: {len(csv_files)}")
            for f in csv_files[:3]:
                print(f"  - {f.name}")
                
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

def test_session_persistence():
    """Test if sessions persist across requests"""
    print("\n=== Testing Session Persistence ===")
    base_url = "http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com"
    
    # Start a session
    session = requests.Session()
    
    # Make initial request
    resp1 = session.get(f"{base_url}/")
    print(f"Initial request status: {resp1.status_code}")
    print(f"Cookies received: {dict(resp1.cookies)}")
    
    # Check if session persists
    resp2 = session.get(f"{base_url}/api/session-info")
    if resp2.status_code == 200:
        print(f"Session info: {resp2.json()}")
    else:
        print(f"Session info request failed: {resp2.status_code}")

def check_file_system():
    """Check file system setup"""
    print("\n=== File System Check ===")
    
    paths_to_check = [
        "instance",
        "instance/uploads",
        "instance/reports",
        "instance/exports",
        "sessions"
    ]
    
    for path in paths_to_check:
        if os.path.exists(path):
            stat = os.stat(path)
            perms = oct(stat.st_mode)[-3:]
            print(f"{path}: exists, perms={perms}, owner={stat.st_uid}")
        else:
            print(f"{path}: DOES NOT EXIST")
    
    # Check if we can write
    test_file = "instance/uploads/test_write.txt"
    try:
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        print("\nWrite test: SUCCESS")
    except Exception as e:
        print(f"\nWrite test: FAILED - {e}")

def check_data_loading():
    """Check how data is loaded"""
    print("\n=== Data Loading Logic ===")
    
    # Check the data handler's load method
    handler_file = "app/services/data_handler.py"
    if os.path.exists(handler_file):
        with open(handler_file, 'r') as f:
            content = f.read()
            
        # Find load_data method
        if "def load_data" in content:
            print("Found load_data method")
            # Extract relevant parts
            lines = content.split('\n')
            in_method = False
            for i, line in enumerate(lines):
                if "def load_data" in line:
                    in_method = True
                    print(f"\nLine {i+1}: {line}")
                    for j in range(i+1, min(i+20, len(lines))):
                        if lines[j].strip() and not lines[j].startswith(' '):
                            break
                        if "csv" in lines[j].lower() or "raw_data" in lines[j]:
                            print(f"Line {j+1}: {lines[j]}")

if __name__ == "__main__":
    print("ChatMRPT Upload Diagnostic Tool")
    print("=" * 40)
    
    test_local_data_handler()
    check_file_system()
    check_data_loading()
    
    # Only test remote if requested
    if "--remote" in sys.argv:
        test_session_persistence()