#!/usr/bin/env python3
"""Test script to diagnose production issues"""

import requests
import json
import time

# Production URL
BASE_URL = "http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com"

def test_tpr_download_links():
    """Test if TPR download links are returned in streaming response"""
    print("Testing TPR download links...")
    
    # This would require a full TPR workflow simulation
    # For now, just check the endpoint exists
    response = requests.get(f"{BASE_URL}/api/tpr/download-links")
    print(f"Download links endpoint status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Download links response: {json.dumps(data, indent=2)}")
    
def test_session_data():
    """Test if session has analysis data"""
    print("\nTesting session data...")
    
    # Would need actual session ID from browser
    # This is a placeholder test
    response = requests.get(f"{BASE_URL}/ping")
    print(f"Health check: {response.status_code}")

def check_static_files():
    """Check if JavaScript files are accessible"""
    print("\nChecking static files...")
    
    js_files = [
        "/static/js/modules/data/tpr-download-manager.js",
        "/static/js/modules/chat/core/message-handler.js"
    ]
    
    for js_file in js_files:
        response = requests.head(f"{BASE_URL}{js_file}")
        print(f"{js_file}: {response.status_code}")
        if response.status_code == 200:
            # Check last modified header
            last_modified = response.headers.get('Last-Modified', 'Unknown')
            print(f"  Last-Modified: {last_modified}")

if __name__ == "__main__":
    print("Production Diagnostics")
    print("=" * 50)
    
    test_tpr_download_links()
    test_session_data()
    check_static_files()