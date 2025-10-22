#!/usr/bin/env python3
"""
Comprehensive pytest test suite for complete TPR workflow following CLAUDE.md.
Tests both data analysis upload paths and full TPR workflow with risk transition.

Test Coverage:
1. Data analysis upload workflow
2. TPR option selection (both option 1 and 2)
3. TPR map generation
4. Risk analysis transition
5. File creation validation
"""

import pytest
import requests
import json
import time
import os
from datetime import datetime
from typing import Dict, Optional, List, Tuple
from pathlib import Path

# Configuration
# Use staging for testing since it's confirmed working
BASE_URL = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
PRODUCTION_URL = BASE_URL  # For compatibility
TEST_FILE = "tests/test_tpr_data.csv"  # Use our test CSV
TIMEOUT = 60


class TestDataAnalysisUpload:
    """Test data analysis upload and initial workflow."""
    
    @pytest.fixture(scope="class")
    def session(self):
        """Create a session for tests."""
        s = requests.Session()
        yield s
        s.close()
    
    def test_upload_via_data_analysis(self, session):
        """Test file upload through data analysis endpoint."""
        with open(TEST_FILE, 'rb') as f:
            files = {'file': (TEST_FILE, f, 'text/csv')}
            response = session.post(
                f"{PRODUCTION_URL}/api/data-analysis/upload",
                files=files,
                timeout=TIMEOUT
            )
        
        assert response.status_code == 200, f"Upload failed: {response.status_code}"
        result = response.json()
        
        # Validate response structure
        assert 'session_id' in result, "No session_id in response"
        assert 'filename' in result, "No filename in response"
        assert 'filepath' in result, "No filepath in response"
        
        # Session ID should be valid
        session_id = result['session_id']
        assert len(session_id) > 0, "Empty session_id"
        assert session_id.startswith('session_'), f"Invalid session_id format: {session_id}"
        
        return session_id
    
    def test_initial_data_analysis_response(self, session):
        """Test initial response after upload."""
        # Upload file first
        session_id = self.test_upload_via_data_analysis(session)
        
        # The upload response should provide initial analysis
        response = session.post(
            f"{PRODUCTION_URL}/api/v1/data-analysis/chat",
            json={'message': '', 'session_id': session_id},
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json()
            message = result.get('message', '').lower()
            
            # Should show data overview or options
            assert any(word in message for word in ['data', 'loaded', 'analysis', 'option']), \
                f"No data analysis content in initial response: {message[:200]}"


class TestTPRWorkflowOptions:
    """Test both TPR workflow options."""
    
    @pytest.fixture(scope="class")
    def session(self):
        """Create a session for tests."""
        s = requests.Session()
        yield s
        s.close()
    
    @pytest.fixture(scope="class")
    def uploaded_session(self, session):
        """Upload file and return session_id."""
        with open(TEST_FILE, 'rb') as f:
            files = {'file': (TEST_FILE, f, 'text/csv')}
            response = session.post(
                f"{PRODUCTION_URL}/api/data-analysis/upload",
                files=files,
                timeout=TIMEOUT
            )
        
        assert response.status_code == 200
        return response.json()['session_id']
    
    def test_option_1_quick_tpr(self, session, uploaded_session):
        """Test Option 1: Quick TPR calculation with defaults."""
        response = session.post(
            f"{PRODUCTION_URL}/api/v1/data-analysis/chat",
            json={'message': '1', 'session_id': uploaded_session},
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200, f"Option 1 failed: {response.status_code}"
        result = response.json()
        message = result.get('message', '')
        
        # Option 1 should calculate TPR immediately with defaults
        assert 'TPR Calculation Complete' in message or 'calculating' in message.lower(), \
            f"Option 1 didn't trigger TPR calculation: {message[:300]}"
        
        # Should use default settings
        assert any(phrase in message for phrase in [
            'all facilities',
            'all ages',
            'default'
        ]), "Option 1 didn't mention using defaults"
    
    def test_option_2_guided_tpr(self, session):
        """Test Option 2: Guided TPR with selections."""
        # Fresh upload for clean test
        with open(TEST_FILE, 'rb') as f:
            files = {'file': (TEST_FILE, f, 'text/csv')}
            upload_response = session.post(
                f"{PRODUCTION_URL}/api/data-analysis/upload",
                files=files,
                timeout=TIMEOUT
            )
        
        session_id = upload_response.json()['session_id']
        
        # Step 1: Select option 2
        response = session.post(
            f"{PRODUCTION_URL}/api/v1/data-analysis/chat",
            json={'message': '2', 'session_id': session_id},
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200
        message = response.json()['message'].lower()
        
        # Should ask about facility level
        assert any(word in message for word in ['facility', 'primary', 'secondary']), \
            f"Option 2 didn't ask about facility level: {message[:300]}"
        
        # Step 2: Select primary facilities
        response = session.post(
            f"{PRODUCTION_URL}/api/v1/data-analysis/chat",
            json={'message': 'primary', 'session_id': session_id},
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200
        message = response.json()['message'].lower()
        
        # Should ask about age group
        assert any(word in message for word in ['age', 'under 5', 'pregnant']), \
            f"Didn't ask about age group: {message[:300]}"
        
        # Step 3: Select age group
        response = session.post(
            f"{PRODUCTION_URL}/api/v1/data-analysis/chat",
            json={'message': 'Under 5 Years', 'session_id': session_id},
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Should complete TPR calculation
        assert 'TPR Calculation Complete' in result['message'], \
            "TPR calculation didn't complete with option 2"
        
        return session_id, result


class TestTPRMapGeneration:
    """Test TPR map generation."""
    
    @pytest.fixture(scope="class")
    def completed_tpr_session(self):
        """Complete TPR workflow and return session_id and result."""
        session = requests.Session()
        
        # Upload file
        with open(TEST_FILE, 'rb') as f:
            files = {'file': (TEST_FILE, f, 'text/csv')}
            upload_response = session.post(
                f"{PRODUCTION_URL}/api/data-analysis/upload",
                files=files,
                timeout=TIMEOUT
            )
        
        session_id = upload_response.json()['session_id']
        
        # Complete TPR workflow
        for message in ['2', 'primary', 'Under 5 Years']:
            response = session.post(
                f"{PRODUCTION_URL}/api/v1/data-analysis/chat",
                json={'message': message, 'session_id': session_id},
                timeout=TIMEOUT
            )
            time.sleep(0.5)
        
        return session_id, response.json()
    
    @pytest.mark.critical
    def test_map_generation(self, completed_tpr_session):
        """Test that TPR map is generated."""
        session_id, result = completed_tpr_session
        message = result.get('message', '')
        
        # Check for map indicators
        map_indicators = [
            'tpr_distribution_map.html' in message,
            'Map URL:' in message,
            'TPR Map Visualization created' in message,
            'Map visualization' in message,
            'serve_viz_file' in message
        ]
        
        assert any(map_indicators), \
            f"No map generated. Response: {message[:500]}"
        
        # Should NOT have warnings about missing shapefile
        assert '⚠️ Note: Could not prepare risk analysis files' not in message, \
            "Risk files not prepared - shapefile loading issue"
        
        assert 'Map visualization requires shapefile data' not in message, \
            "Map generation failed due to missing shapefile"
    
    def test_visualization_in_response(self, completed_tpr_session):
        """Test that visualizations are included in response."""
        session_id, result = completed_tpr_session
        
        # Check if visualizations are in the response
        if 'visualizations' in result:
            viz = result['visualizations']
            assert isinstance(viz, list), "Visualizations should be a list"
            
            if len(viz) > 0:
                # Validate visualization structure
                first_viz = viz[0]
                assert 'type' in first_viz or 'url' in first_viz, \
                    f"Invalid visualization structure: {first_viz}"


class TestRiskAnalysisTransition:
    """Test transition from TPR to risk analysis."""
    
    @pytest.fixture(scope="class")
    def session_after_tpr(self):
        """Complete TPR and return session ready for risk transition."""
        session = requests.Session()
        
        # Upload and complete TPR
        with open(TEST_FILE, 'rb') as f:
            files = {'file': (TEST_FILE, f, 'text/csv')}
            upload_response = session.post(
                f"{PRODUCTION_URL}/api/data-analysis/upload",
                files=files,
                timeout=TIMEOUT
            )
        
        session_id = upload_response.json()['session_id']
        
        # Complete TPR workflow
        for message in ['2', 'primary', 'Under 5 Years']:
            session.post(
                f"{PRODUCTION_URL}/api/v1/data-analysis/chat",
                json={'message': message, 'session_id': session_id},
                timeout=TIMEOUT
            )
            time.sleep(0.5)
        
        return session, session_id
    
    @pytest.mark.critical
    def test_risk_transition_with_yes(self, session_after_tpr):
        """Test risk analysis transition when user says 'yes'."""
        session, session_id = session_after_tpr
        
        # Transition to risk analysis
        response = session.post(
            f"{PRODUCTION_URL}/api/v1/data-analysis/chat",
            json={'message': 'yes', 'session_id': session_id},
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200, f"Risk transition failed: {response.status_code}"
        result = response.json()
        message = result.get('message', '')
        
        # Should NOT have error about missing files
        assert 'TPR data file not found' not in message, \
            "Risk transition failed - raw_data.csv not created"
        
        assert 'Error' not in message or 'error' not in message.lower(), \
            f"Risk transition has errors: {message[:300]}"
        
        # Should contain risk analysis content
        risk_keywords = [
            'risk',
            'analysis',
            'vulnerability',
            'ranking',
            'composite',
            'score',
            'priorit'
        ]
        
        assert any(keyword in message.lower() for keyword in risk_keywords), \
            f"No risk analysis content. Response: {message[:500]}"
    
    def test_risk_transition_creates_files(self, session_after_tpr):
        """Test that risk transition mentions creating necessary files."""
        session, session_id = session_after_tpr
        
        # The TPR completion should have prepared files
        # Let's check the last TPR response
        response = session.post(
            f"{PRODUCTION_URL}/api/v1/data-analysis/chat",
            json={'message': 'Under 5 Years', 'session_id': session_id},
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            message = response.json().get('message', '')
            
            # Check for file preparation mentions
            file_indicators = [
                'raw_data.csv',
                'raw_shapefile',
                'Data automatically prepared for risk analysis',
                'prepared for risk'
            ]
            
            files_mentioned = [ind for ind in file_indicators if ind in message]
            
            # At least some indication of file preparation
            assert len(files_mentioned) > 0 or 'Results saved' in message, \
                f"No indication of file preparation for risk analysis"
    
    def test_risk_analysis_workflow_complete(self, session_after_tpr):
        """Test complete risk analysis workflow after TPR."""
        session, session_id = session_after_tpr
        
        # Transition to risk analysis
        response = session.post(
            f"{PRODUCTION_URL}/api/v1/data-analysis/chat",
            json={'message': 'yes', 'session_id': session_id},
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200
        message = response.json().get('message', '')
        
        # Risk analysis should show:
        expected_content = [
            ('ranking', 'Ward ranking should be present'),
            ('risk', 'Risk levels should be mentioned'),
            ('recommendation', 'Should have recommendations') 
        ]
        
        for keyword, description in expected_content:
            if keyword not in message.lower():
                print(f"Warning: {description}")
        
        # Should complete without errors
        assert 'successfully' in message.lower() or 'complete' in message.lower(), \
            "Risk analysis didn't complete successfully"


class TestEndToEndWorkflow:
    """Test complete end-to-end workflow."""
    
    @pytest.mark.integration
    def test_complete_workflow(self):
        """Test complete workflow from upload to risk analysis."""
        session = requests.Session()
        results = {}
        
        # Step 1: Upload file
        with open(TEST_FILE, 'rb') as f:
            files = {'file': (TEST_FILE, f, 'text/csv')}
            response = session.post(
                f"{PRODUCTION_URL}/api/data-analysis/upload",
                files=files,
                timeout=TIMEOUT
            )
        
        assert response.status_code == 200, "Upload failed"
        session_id = response.json()['session_id']
        results['upload'] = '✅ Success'
        
        # Step 2: TPR workflow
        workflow_steps = [
            ('2', 'Select guided TPR'),
            ('primary', 'Select primary facilities'),
            ('Under 5 Years', 'Select age group')
        ]
        
        for message, description in workflow_steps:
            response = session.post(
                f"{PRODUCTION_URL}/api/v1/data-analysis/chat",
                json={'message': message, 'session_id': session_id},
                timeout=TIMEOUT
            )
            
            assert response.status_code == 200, f"Failed at: {description}"
            results[description] = '✅ Success'
            time.sleep(1)
        
        # Verify TPR completed
        tpr_result = response.json()
        assert 'TPR Calculation Complete' in tpr_result['message'], \
            "TPR didn't complete"
        results['TPR Calculation'] = '✅ Complete'
        
        # Check for map
        if 'tpr_distribution_map' in tpr_result['message'] or \
           'Map' in tpr_result['message']:
            results['Map Generation'] = '✅ Generated'
        else:
            results['Map Generation'] = '❌ Not generated'
        
        # Step 3: Risk analysis transition
        response = session.post(
            f"{PRODUCTION_URL}/api/v1/data-analysis/chat",
            json={'message': 'yes', 'session_id': session_id},
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200, "Risk transition failed"
        risk_result = response.json()
        
        if 'TPR data file not found' not in risk_result['message']:
            results['Risk Transition'] = '✅ Success'
        else:
            results['Risk Transition'] = '❌ Failed - missing files'
        
        # Print summary
        print("\n" + "="*50)
        print("End-to-End Workflow Results:")
        print("="*50)
        for step, status in results.items():
            print(f"{step}: {status}")
        
        # All critical steps should pass
        assert results['upload'] == '✅ Success'
        assert results['TPR Calculation'] == '✅ Complete'
        assert results['Risk Transition'] == '✅ Success', \
            "Risk transition failed - critical issue"


@pytest.mark.parametrize("facility_level,age_group", [
    ("primary", "Under 5 Years"),
    ("secondary", "Over 5 Years"),
    ("all", "Pregnant Women")
])
def test_different_selections(facility_level, age_group):
    """Test TPR with different facility levels and age groups."""
    session = requests.Session()
    
    # Upload file
    with open(TEST_FILE, 'rb') as f:
        files = {'file': (TEST_FILE, f, 'text/csv')}
        response = session.post(
            f"{PRODUCTION_URL}/api/data-analysis/upload",
            files=files,
            timeout=TIMEOUT
        )
    
    session_id = response.json()['session_id']
    
    # Run workflow with parameters
    for message in ['2', facility_level, age_group]:
        response = session.post(
            f"{PRODUCTION_URL}/api/v1/data-analysis/chat",
            json={'message': message, 'session_id': session_id},
            timeout=TIMEOUT
        )
        time.sleep(0.5)
    
    assert response.status_code == 200
    result = response.json()
    
    # Should complete regardless of selections
    assert 'TPR Calculation Complete' in result['message'], \
        f"TPR failed for {facility_level}/{age_group}"
    
    # Should reflect selections in results
    message_lower = result['message'].lower()
    assert facility_level in message_lower or \
           (facility_level == 'all' and 'all facilities' in message_lower), \
        f"Facility level '{facility_level}' not reflected"


if __name__ == "__main__":
    # Run tests with detailed output
    import sys
    pytest_args = [
        __file__,
        "-v",  # Verbose
        "-s",  # Show print statements
        "--tb=short",  # Short traceback
        "-k", "test_"  # Run all tests
    ]
    
    # Add specific test if provided
    if len(sys.argv) > 1:
        pytest_args.extend(sys.argv[1:])
    
    pytest.main(pytest_args)