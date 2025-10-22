#!/usr/bin/env python3
"""
Comprehensive Production Test Suite for Data Analysis Tab
Following CLAUDE.md guidelines for pytest testing
Tests actual implementation without modifying code
"""

import pytest
import requests
import pandas as pd
import io
import json
import time
from datetime import datetime
from typing import Dict, Tuple, Optional

# Production URL - testing the real deal
PRODUCTION_URL = "http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com"


class TestDataAnalysisProduction:
    """
    Complete test suite for Data Analysis tab on production
    Tests multiple datasets from different regions as per CLAUDE.md
    """
    
    @classmethod
    def setup_class(cls):
        """Setup for all tests"""
        cls.base_url = PRODUCTION_URL
        cls.session = requests.Session()
        cls.test_sessions = {}
        cls.start_time = datetime.now()
        
    @classmethod
    def teardown_class(cls):
        """Cleanup after all tests"""
        cls.session.close()
        duration = (datetime.now() - cls.start_time).seconds
        print(f"\n✅ All tests completed in {duration} seconds")
        
    def test_01_server_health(self):
        """Test that production server is healthy"""
        response = self.session.get(f"{self.base_url}/ping", timeout=5)
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        print("✅ Server health check passed")
        
    def test_02_ui_shows_data_analysis(self):
        """Test that UI shows 'Data Analysis' not 'TPR Analysis'"""
        response = self.session.get(self.base_url, timeout=10)
        assert response.status_code == 200, f"Main page failed: {response.status_code}"
        
        html = response.text
        
        # Check for Data Analysis tab
        assert 'id="data-analysis-tab"' in html, "Data Analysis tab button not found"
        assert "Data Analysis" in html, "Data Analysis text not found"
        
        # Ensure old TPR text is gone
        assert "TPR Analysis" not in html, "Old 'TPR Analysis' text still present"
        
        print("✅ UI correctly shows 'Data Analysis' tab")
        
    def test_03_upload_adamawa_data_with_special_chars(self):
        """Test upload with Adamawa data containing ≥ character"""
        # Create test data for Adamawa (as in original issue)
        data = {
            'State': ['Adamawa'] * 5,
            'LGA': ['Yola North', 'Yola South', 'Mubi North', 'Mubi South', 'Michika'],
            'WardName': ['Ward_1', 'Ward_2', 'Ward_3', 'Ward_4', 'Ward_5'],
            'Persons presenting with fever & tested by RDT <5yrs': [100, 150, 200, 120, 180],
            'Persons presenting with fever & tested by RDT ≥5yrs (excl PW)': [250, 300, 350, 280, 320],
            'Persons presenting with fever & tested by RDT Preg Women (PW)': [50, 75, 100, 60, 85],
            'Confirmed cases by RDT/Microscopy <5yrs': [20, 30, 40, 25, 35],
            'Confirmed cases by RDT/Microscopy ≥5yrs (excl PW)': [45, 55, 65, 50, 60],
            'Confirmed cases by RDT/Microscopy Preg Women (PW)': [10, 15, 20, 12, 18]
        }
        
        session_id = self._upload_data(data, "adamawa_test.csv")
        assert session_id is not None, "Adamawa data upload failed"
        self.test_sessions['adamawa'] = session_id
        print(f"✅ Adamawa data uploaded: {session_id}")
        
    def test_04_upload_kano_data_different_region(self):
        """Test with Kano data (different region) as per CLAUDE.md multi-region testing"""
        data = {
            'State': ['Kano'] * 5,
            'LGA': ['Fagge', 'Nassarawa', 'Dala', 'Gwale', 'Kano Municipal'],
            'WardName': ['Fagge A', 'Tudun Wada', 'Dala', 'Gwale', 'Zango'],
            'Persons presenting with fever & tested by RDT <5yrs': [200, 250, 300, 180, 220],
            'Persons presenting with fever & tested by RDT ≥5yrs (excl PW)': [400, 450, 500, 380, 420],
            'Persons presenting with fever & tested by RDT Preg Women (PW)': [80, 95, 110, 70, 90],
            'Confirmed cases by RDT/Microscopy <5yrs': [40, 50, 60, 35, 45],
            'Confirmed cases by RDT/Microscopy ≥5yrs (excl PW)': [80, 90, 100, 75, 85],
            'Confirmed cases by RDT/Microscopy Preg Women (PW)': [16, 19, 22, 14, 18]
        }
        
        session_id = self._upload_data(data, "kano_test.csv")
        assert session_id is not None, "Kano data upload failed"
        self.test_sessions['kano'] = session_id
        print(f"✅ Kano data uploaded: {session_id}")
        
    def test_05_encoding_not_corrupted(self):
        """Test that ≥ character is not corrupted to â‰¥"""
        if 'adamawa' not in self.test_sessions:
            pytest.skip("No Adamawa session available")
            
        response = self.session.post(
            f"{self.base_url}/api/v1/data-analysis/chat",
            json={
                'message': 'List all the column names in the data',
                'session_id': self.test_sessions['adamawa']
            },
            timeout=30
        )
        
        assert response.status_code == 200, f"Chat failed: {response.status_code}"
        result = response.json()
        message = result.get('message', '')
        
        # Check for encoding corruption
        assert 'â‰¥' not in message, "Encoding corrupted: â‰¥ found instead of ≥"
        assert 'Ã¢â€°Â¥' not in message, "Severe encoding corruption detected"
        
        print("✅ Encoding preserved correctly (no corruption)")
        
    def test_06_all_three_age_groups_recognized(self):
        """Test that all 3 age groups are recognized (critical fix)"""
        if 'adamawa' not in self.test_sessions:
            pytest.skip("No Adamawa session available")
            
        response = self.session.post(
            f"{self.base_url}/api/v1/data-analysis/chat",
            json={
                'message': 'How many age groups are in the data? List them.',
                'session_id': self.test_sessions['adamawa']
            },
            timeout=30
        )
        
        assert response.status_code == 200, f"Chat failed: {response.status_code}"
        result = response.json()
        message = result.get('message', '').lower()
        
        # Check for all 3 age groups
        age_groups_found = []
        if 'under 5' in message or '<5' in message or 'less than 5' in message:
            age_groups_found.append('Under 5')
        if 'over 5' in message or '≥5' in message or 'greater' in message or '5 years and above' in message:
            age_groups_found.append('Over 5')
        if 'pregnant' in message:
            age_groups_found.append('Pregnant Women')
            
        assert len(age_groups_found) >= 3, f"Only found {len(age_groups_found)} age groups: {age_groups_found}. Missing: Over 5 Years group"
        print(f"✅ All 3 age groups recognized: {age_groups_found}")
        
    def test_07_bullet_formatting_correct(self):
        """Test that bullet points are not on single lines"""
        if 'kano' not in self.test_sessions:
            pytest.skip("No Kano session available")
            
        response = self.session.post(
            f"{self.base_url}/api/v1/data-analysis/chat",
            json={
                'message': 'Give me a summary of key findings with bullet points',
                'session_id': self.test_sessions['kano']
            },
            timeout=30
        )
        
        assert response.status_code == 200, f"Chat failed: {response.status_code}"
        result = response.json()
        message = result.get('message', '')
        
        # Check for single-line bullets (the issue we fixed)
        lines = message.split('\n')
        single_line_bullets = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped in ['•', '-', '*', '◦']:
                single_line_bullets.append(f"Line {i+1}: '{stripped}'")
                
        assert len(single_line_bullets) == 0, f"Found {len(single_line_bullets)} single-line bullets: {single_line_bullets}"
        print("✅ Bullet formatting correct (no single-line bullets)")
        
    def test_08_tpr_calculation_works(self):
        """Test TPR calculation functionality"""
        if 'adamawa' not in self.test_sessions:
            pytest.skip("No Adamawa session available")
            
        response = self.session.post(
            f"{self.base_url}/api/v1/data-analysis/chat",
            json={
                'message': 'Calculate the TPR (test positivity rate) for each ward',
                'session_id': self.test_sessions['adamawa']
            },
            timeout=30
        )
        
        assert response.status_code == 200, f"Chat failed: {response.status_code}"
        result = response.json()
        message = result.get('message', '').lower()
        
        # Check for TPR calculation evidence
        has_tpr = any(term in message for term in ['tpr', 'positivity', 'test positive rate', 'percentage'])
        has_numbers = any(char.isdigit() or char == '.' for char in message)
        
        assert has_tpr, "No TPR terminology found in response"
        assert has_numbers, "No numerical values found in TPR response"
        print("✅ TPR calculation functionality working")
        
    def test_09_multi_region_consistency(self):
        """Test that both regions work consistently (CLAUDE.md requirement)"""
        results = {}
        
        for region, session_id in self.test_sessions.items():
            response = self.session.post(
                f"{self.base_url}/api/v1/data-analysis/chat",
                json={
                    'message': 'How many wards are in the data?',
                    'session_id': session_id
                },
                timeout=30
            )
            
            if response.status_code == 200:
                results[region] = "success"
            else:
                results[region] = f"failed: {response.status_code}"
                
        # Both regions should work
        assert all(v == "success" for v in results.values()), f"Region consistency failed: {results}"
        print(f"✅ Multi-region consistency verified: {list(results.keys())}")
        
    def test_10_session_isolation(self):
        """Test that sessions are properly isolated (multi-user support)"""
        if len(self.test_sessions) < 2:
            pytest.skip("Need multiple sessions to test isolation")
            
        # Ask about state in Adamawa session
        response1 = self.session.post(
            f"{self.base_url}/api/v1/data-analysis/chat",
            json={
                'message': 'What state is this data from?',
                'session_id': self.test_sessions['adamawa']
            },
            timeout=30
        )
        
        # Ask about state in Kano session
        response2 = self.session.post(
            f"{self.base_url}/api/v1/data-analysis/chat",
            json={
                'message': 'What state is this data from?',
                'session_id': self.test_sessions['kano']
            },
            timeout=30
        )
        
        assert response1.status_code == 200, "Adamawa session query failed"
        assert response2.status_code == 200, "Kano session query failed"
        
        msg1 = response1.json().get('message', '').lower()
        msg2 = response2.json().get('message', '').lower()
        
        assert 'adamawa' in msg1, "Adamawa session doesn't recognize Adamawa data"
        assert 'kano' in msg2, "Kano session doesn't recognize Kano data"
        
        print("✅ Session isolation verified (multi-user support working)")
        
    def _upload_data(self, data: Dict, filename: str) -> Optional[str]:
        """Helper method to upload data and return session ID"""
        df = pd.DataFrame(data)
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_bytes = csv_buffer.getvalue().encode('utf-8')
        
        files = {'file': (filename, csv_bytes, 'text/csv')}
        response = self.session.post(
            f"{self.base_url}/api/data-analysis/upload",
            files=files,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('session_id')
        return None


if __name__ == "__main__":
    # Run pytest with verbose output
    pytest.main([__file__, "-v", "--tb=short", "-s"])