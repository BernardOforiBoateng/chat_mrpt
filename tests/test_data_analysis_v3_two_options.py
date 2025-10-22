"""
Test Data Analysis V3 Two-Option Response
Following CLAUDE.md testing standards
"""

import pytest
import asyncio
import os
import shutil
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
sys.path.insert(0, '.')

from app.data_analysis_v3.core.agent import DataAnalysisAgent


class TestDataAnalysisV3TwoOptions:
    """Test that Data Analysis V3 shows exactly TWO options after file upload."""
    
    @pytest.fixture
    def setup_test_session(self):
        """Setup test session with sample data."""
        session_id = 'test_two_options'
        upload_dir = f'instance/uploads/{session_id}'
        
        # Cleanup before test
        if os.path.exists(upload_dir):
            shutil.rmtree(upload_dir)
        
        # Create test directory
        os.makedirs(upload_dir, exist_ok=True)
        
        # Create sample CSV file
        df = pd.DataFrame({
            'wardname': ['Ikeja', 'Surulere', 'Yaba', 'Victoria Island', 'Lekki'],
            'healthfacility': ['General Hospital Ikeja', 'Primary Health Center Surulere', 
                              'Yaba Health Clinic', 'Victoria Island Medical Center', 
                              'Lekki Primary Care'],
            'total_tested': [250, 180, 320, 150, 290],
            'confirmed_cases': [45, 28, 62, 18, 51],
            'lga': ['Ikeja', 'Surulere', 'Mainland', 'Eti-Osa', 'Eti-Osa'],
            'state': ['Lagos', 'Lagos', 'Lagos', 'Lagos', 'Lagos']
        })
        
        csv_path = os.path.join(upload_dir, 'malaria_data.csv')
        df.to_csv(csv_path, index=False)
        
        yield session_id, upload_dir, csv_path
        
        # Cleanup after test
        if os.path.exists(upload_dir):
            shutil.rmtree(upload_dir)
    
    @pytest.mark.asyncio
    async def test_initial_upload_shows_two_options(self, setup_test_session):
        """Test that initial data upload message triggers two-option response."""
        session_id, upload_dir, csv_path = setup_test_session
        
        # Create agent
        agent = DataAnalysisAgent(session_id)
        
        # Test initial upload message
        result = await agent.analyze("Show me what's in the uploaded data")
        
        # Verify success
        assert result.get('success') == True, f"Analysis failed: {result.get('message')}"
        
        # Get the message
        message = result.get('message', '')
        
        # Check that TWO options are presented
        assert 'Option 1' in message or '1.' in message or 'Guided TPR Analysis' in message, \
            "Option 1 (Guided TPR Analysis) not found in response"
        
        assert 'Option 2' in message or '2.' in message or 'Flexible Data Exploration' in message, \
            "Option 2 (Flexible Data Exploration) not found in response"
        
        # Ensure no Option 3 or Option 4 (old 4-option format)
        assert 'Option 3' not in message and '3.' not in message.split('Option')[0], \
            "Found Option 3 - should only have 2 options"
        
        assert 'Option 4' not in message and '4.' not in message.split('Option')[0], \
            "Found Option 4 - should only have 2 options"
        
        # Check that TPR workflow is mentioned
        assert 'TPR' in message or 'Test Positivity Rate' in message, \
            "TPR workflow not mentioned in options"
        
        # Check that risk assessment is mentioned
        assert 'risk' in message.lower() or 'assessment' in message.lower(), \
            "Risk assessment workflow not mentioned"
        
        print("\n✅ Test Passed: Two options displayed correctly")
        print(f"\nAgent Response Preview:\n{message[:500]}...")
    
    @pytest.mark.asyncio
    async def test_option_1_triggers_tpr_workflow(self, setup_test_session):
        """Test that selecting Option 1 triggers TPR workflow."""
        session_id, upload_dir, csv_path = setup_test_session
        
        # Create agent
        agent = DataAnalysisAgent(session_id)
        
        # First get the initial options
        initial_result = await agent.analyze("Show me what's in the uploaded data")
        assert initial_result.get('success') == True
        
        # Select Option 1
        result = await agent.analyze("1")
        
        # Verify response mentions TPR calculation
        message = result.get('message', '')
        assert any(keyword in message.lower() for keyword in ['tpr', 'test positivity', 'calculate']), \
            "Option 1 didn't trigger TPR workflow"
        
        print("\n✅ Test Passed: Option 1 triggers TPR workflow")
    
    @pytest.mark.asyncio  
    async def test_option_2_triggers_exploration(self, setup_test_session):
        """Test that selecting Option 2 triggers data exploration."""
        session_id, upload_dir, csv_path = setup_test_session
        
        # Create agent
        agent = DataAnalysisAgent(session_id)
        
        # First get the initial options
        initial_result = await agent.analyze("Show me what's in the uploaded data")
        assert initial_result.get('success') == True
        
        # Select Option 2
        result = await agent.analyze("2")
        
        # Verify response is about exploration/analysis
        message = result.get('message', '')
        
        # Option 2 should NOT trigger TPR workflow
        assert 'calculate TPR' not in message, \
            "Option 2 incorrectly triggered TPR calculation"
        
        print("\n✅ Test Passed: Option 2 triggers exploration mode")
    
    @pytest.mark.asyncio
    async def test_no_hallucinated_names(self, setup_test_session):
        """Test that agent doesn't use generic names like 'Facility A'."""
        session_id, upload_dir, csv_path = setup_test_session
        
        # Create agent
        agent = DataAnalysisAgent(session_id)
        
        # Request top facilities
        result = await agent.analyze("Show me the top 5 facilities by tests")
        
        message = result.get('message', '')
        
        # Check for hallucinated/generic names
        generic_patterns = [
            'Facility A', 'Facility B', 'Facility C',
            'Ward A', 'Ward B', 'Ward C',
            'Location 1', 'Location 2'
        ]
        
        for pattern in generic_patterns:
            assert pattern not in message, \
                f"Found hallucinated name '{pattern}' in response"
        
        # Should contain real facility names from our test data
        expected_facilities = ['Ikeja', 'Surulere', 'Yaba', 'Victoria', 'Lekki']
        found_any = any(facility in message for facility in expected_facilities)
        assert found_any, "No real facility names found in response"
        
        print("\n✅ Test Passed: No hallucinated names in response")


def run_tests():
    """Run all tests with detailed output."""
    print("=" * 60)
    print("Testing Data Analysis V3 Two-Option Response")
    print("=" * 60)
    
    # Run pytest with verbose output
    import subprocess
    result = subprocess.run(
        ['chatmrpt_venv_new/bin/python', '-m', 'pytest', 
         'tests/test_data_analysis_v3_two_options.py', 
         '-v', '--tb=short', '-s'],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    
    return result.returncode == 0


if __name__ == "__main__":
    # For direct execution
    test = TestDataAnalysisV3TwoOptions()
    
    # Run setup
    import tempfile
    session_id = 'test_direct'
    upload_dir = f'instance/uploads/{session_id}'
    
    # Cleanup
    if os.path.exists(upload_dir):
        shutil.rmtree(upload_dir)
    
    os.makedirs(upload_dir, exist_ok=True)
    
    # Create test data
    df = pd.DataFrame({
        'wardname': ['Ikeja', 'Surulere', 'Yaba'],
        'healthfacility': ['General Hospital', 'Health Center', 'Clinic'],
        'total_tested': [250, 180, 320],
        'confirmed_cases': [45, 28, 62]
    })
    df.to_csv(f'{upload_dir}/test.csv', index=False)
    
    # Run async test
    async def main():
        agent = DataAnalysisAgent(session_id)
        result = await agent.analyze("Show me what's in the uploaded data")
        
        print("\n" + "=" * 60)
        print("DIRECT TEST RESULT")
        print("=" * 60)
        print(f"Success: {result.get('success')}")
        print(f"\nMessage:\n{result.get('message')}")
        
        # Verify two options
        message = result.get('message', '')
        has_option_1 = 'Guided TPR Analysis' in message or 'Option 1' in message
        has_option_2 = 'Flexible Data Exploration' in message or 'Option 2' in message
        has_option_3 = 'Option 3' in message or '3.' in message.split('\n')[0:20]
        
        print("\n" + "=" * 60)
        print("VALIDATION")
        print("=" * 60)
        print(f"✅ Has Option 1 (TPR): {has_option_1}")
        print(f"✅ Has Option 2 (Exploration): {has_option_2}")
        print(f"✅ No Option 3: {not has_option_3}")
        print(f"✅ Exactly 2 options: {has_option_1 and has_option_2 and not has_option_3}")
    
    asyncio.run(main())
    
    # Cleanup
    if os.path.exists(upload_dir):
        shutil.rmtree(upload_dir)