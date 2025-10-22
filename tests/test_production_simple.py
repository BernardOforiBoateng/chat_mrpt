#!/usr/bin/env python3
"""
Simple Production Test - Direct and Fast
Tests actual production deployment
"""

import pytest
import requests
import json
import pandas as pd
import io
from datetime import datetime

PRODUCTION_URL = "http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com"

class TestProductionSimple:
    """Simple tests for production"""
    
    def test_server_health(self):
        """Test 1: Server is alive"""
        response = requests.get(f"{PRODUCTION_URL}/ping", timeout=5)
        assert response.status_code == 200, f"Server health check failed: {response.status_code}"
        print("✅ Server is healthy")
    
    def test_main_page(self):
        """Test 2: Main page loads"""
        response = requests.get(PRODUCTION_URL, timeout=5)
        assert response.status_code == 200, f"Main page failed: {response.status_code}"
        assert "ChatMRPT" in response.text, "ChatMRPT not found in response"
        print("✅ Main page loads")
    
    def test_data_analysis_tab(self):
        """Test 3: Data Analysis tab exists"""
        response = requests.get(PRODUCTION_URL, timeout=5)
        assert "Data Analysis" in response.text or "data-analysis" in response.text.lower(), \
            "Data Analysis tab not found"
        print("✅ Data Analysis tab exists")
    
    def test_file_upload(self):
        """Test 4: File upload works"""
        # Create simple test data
        data = {
            'State': ['Adamawa'],
            'LGA': ['Yola North'],
            'WardName': ['Ward_1'],
            'Persons presenting with fever & tested by RDT <5yrs': [100],
            'Persons presenting with fever & tested by RDT  ≥5yrs (excl PW)': [200],
            'Persons presenting with fever & tested by RDT Preg Women (PW)': [50],
        }
        
        df = pd.DataFrame(data)
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_bytes = csv_buffer.getvalue().encode('utf-8')
        
        # Get session
        session_response = requests.get(PRODUCTION_URL, timeout=5)
        cookies = session_response.cookies
        
        # Upload file
        files = {'file': ('test.csv', csv_bytes, 'text/csv')}
        response = requests.post(
            f"{PRODUCTION_URL}/api/data-analysis/upload",
            files=files,
            cookies=cookies,
            timeout=10
        )
        
        assert response.status_code == 200, f"Upload failed: {response.status_code}"
        result = response.json()
        assert result.get('success') == True or result.get('status') == 'success', \
            f"Upload not successful: {result}"
        
        session_id = result.get('session_id')
        assert session_id, "No session ID returned"
        
        print(f"✅ File upload works (Session: {session_id})")
        
        # Store for other tests
        self.__class__.session_id = session_id
        self.__class__.cookies = cookies
        
        return session_id
    
    def test_chat_endpoint(self):
        """Test 5: Chat endpoint responds"""
        if not hasattr(self.__class__, 'session_id'):
            pytest.skip("No session ID from upload test")
        
        response = requests.post(
            f"{PRODUCTION_URL}/api/v1/data-analysis/chat",
            json={'message': 'hello', 'session_id': self.__class__.session_id},
            cookies=self.__class__.cookies,
            timeout=10
        )
        
        # Check if endpoint exists (not 404)
        assert response.status_code != 404, "Chat endpoint not found (404)"
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Chat endpoint works: {result.get('success')}")
        else:
            print(f"⚠️ Chat endpoint returned: {response.status_code}")
    
    def test_encoding(self):
        """Test 6: Special characters work"""
        test_string = "Test ≥5 years"
        
        # Test that we can send and receive special characters
        if hasattr(self.__class__, 'session_id'):
            response = requests.post(
                f"{PRODUCTION_URL}/api/v1/data-analysis/chat",
                json={'message': test_string, 'session_id': self.__class__.session_id},
                cookies=self.__class__.cookies,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                message = result.get('message', '')
                
                # Check encoding isn't corrupted
                assert 'â‰¥' not in message, "Encoding corrupted: â‰¥ found"
                print("✅ Encoding works correctly")
            else:
                print(f"⚠️ Could not test encoding: {response.status_code}")
        else:
            print("⏭️ Skipping encoding test (no session)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])