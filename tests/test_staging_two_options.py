"""
Test Data Analysis V3 Two-Option Workflow on Staging
Following CLAUDE.md pytest standards
"""

import pytest
import requests
import pandas as pd
import io
from datetime import datetime
import time
import sys
sys.path.insert(0, '.')


class TestStagingTwoOptions:
    """Test suite for two-option workflow on staging server."""
    
    # Staging server URL
    BASE_URL = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
    
    @pytest.fixture
    def session_id(self):
        """Generate unique session ID for each test."""
        return f"pytest_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{time.time_ns()}"
    
    def get_test_data(self):
        """Create test data for upload."""
        df = pd.DataFrame({
            'wardname': ['Ikeja', 'Surulere', 'Yaba', 'Victoria Island', 'Lekki'],
            'healthfacility': ['General Hospital Ikeja', 'Surulere Health Center', 
                              'Yaba Clinic', 'Victoria Island Medical', 'Lekki Primary Care'],
            'total_tested': [250, 180, 320, 150, 290],
            'confirmed_cases': [45, 28, 62, 18, 51],
            'lga': ['Ikeja LGA', 'Surulere LGA', 'Mainland LGA', 'Eti-Osa LGA', 'Eti-Osa LGA'],
            'state': ['Lagos', 'Lagos', 'Lagos', 'Lagos', 'Lagos'],
            'month': ['January', 'January', 'January', 'January', 'January'],
            'year': [2024, 2024, 2024, 2024, 2024]
        })
        return df
    
    def upload_file(self, session_id, df):
        """Helper to upload CSV file to staging."""
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        
        files = {'file': ('test_data.csv', csv_buffer.getvalue(), 'text/csv')}
        data = {'session_id': session_id}
        
        response = requests.post(
            f"{self.BASE_URL}/api/data-analysis/upload",
            files=files,
            data=data,
            timeout=15
        )
        
        assert response.status_code == 200, f"Upload failed: {response.status_code} - {response.text[:200]}"
        return response.json()
    
    def send_chat_message(self, session_id, message, timeout=30):
        """Helper to send chat message to Data Analysis V3."""
        response = requests.post(
            f"{self.BASE_URL}/api/v1/data-analysis/chat",
            json={
                'message': message,
                'session_id': session_id
            },
            timeout=timeout
        )
        
        assert response.status_code == 200, f"Chat request failed: {response.status_code}"
        return response.json()
    
    def test_initial_upload_shows_two_options(self, session_id, test_data):
        """Test that initial data upload triggers two-option response."""
        print(f"\n🧪 Testing initial upload response for session {session_id}")
        
        # Upload file
        upload_result = self.upload_file(session_id, test_data)
        assert upload_result['status'] == 'success', "File upload failed"
        print(f"✅ File uploaded: {upload_result['filename']}")
        
        # Send initial message using the trigger that works
        chat_result = self.send_chat_message(
            session_id, 
            "__DATA_UPLOADED__"
        )
        
        assert chat_result['success'] == True, f"Chat failed: {chat_result.get('error')}"
        
        message = chat_result.get('message', '')
        print(f"✅ Got response: {len(message)} characters")
        
        # Verify TWO options are present
        has_option_1 = any(x in message for x in ['Option 1', '1.', 'Guided TPR Analysis'])
        has_option_2 = any(x in message for x in ['Option 2', '2.', 'Flexible Data Exploration'])
        
        assert has_option_1, "Option 1 (Guided TPR Analysis) not found"
        assert has_option_2, "Option 2 (Flexible Data Exploration) not found"
        
        # Verify NO Option 3 or 4
        assert 'Option 3' not in message, "Found Option 3 - should only have 2 options"
        assert 'Option 4' not in message, "Found Option 4 - should only have 2 options"
        
        # Verify key terms (risk assessment is mentioned)
        # Note: 'risk assessment' might be cut off in preview
        assert 'risk' in message.lower() or 'TPR' in message, "Risk/TPR context not mentioned"
        
        print("✅ Two options displayed correctly")
        print(f"   Option 1 (TPR): {has_option_1}")
        print(f"   Option 2 (Exploration): {has_option_2}")
        
        return True
    
    def test_option_1_triggers_tpr_workflow(self, session_id, test_data):
        """Test that selecting Option 1 triggers TPR workflow."""
        print(f"\n🧪 Testing Option 1 (TPR workflow) for session {session_id}")
        
        # Upload and get initial options
        self.upload_file(session_id, test_data)
        self.send_chat_message(session_id, "__DATA_UPLOADED__")
        
        # Select Option 1
        result = self.send_chat_message(session_id, "1")
        
        assert result['success'] == True, "Option 1 request failed"
        
        message = result.get('message', '').lower()
        
        # Verify TPR workflow triggered
        tpr_keywords = ['tpr', 'test positivity', 'calculate', 'age group', 'test method', 
                       'facility level', 'all ages', 'under 5']
        
        found_keywords = [kw for kw in tpr_keywords if kw in message]
        assert len(found_keywords) > 0, f"TPR workflow not triggered. Message: {message[:300]}..."
        
        # Verify it's NOT just exploration
        assert 'calculate' in message or 'calculation' in message, \
            "Option 1 should mention TPR calculation"
        
        print(f"✅ Option 1 correctly triggered TPR workflow")
        print(f"   Found keywords: {found_keywords}")
        
        return True
    
    def test_option_2_triggers_exploration(self, session_id, test_data):
        """Test that selecting Option 2 triggers exploration workflow."""
        print(f"\n🧪 Testing Option 2 (Exploration) for session {session_id}")
        
        # Upload and get initial options
        self.upload_file(session_id, test_data)
        self.send_chat_message(session_id, "__DATA_UPLOADED__")
        
        # Select Option 2
        result = self.send_chat_message(session_id, "2")
        
        assert result['success'] == True, "Option 2 request failed"
        
        message = result.get('message', '').lower()
        
        # Verify exploration triggered
        exploration_keywords = ['explore', 'pattern', 'insight', 'analysis', 'visualization',
                               'trend', 'distribution', 'correlation']
        
        found_keywords = [kw for kw in exploration_keywords if kw in message]
        assert len(found_keywords) > 0, f"Exploration not triggered. Message: {message[:300]}..."
        
        # Verify it's NOT TPR calculation
        assert 'calculate tpr' not in message and 'calculating test positivity rate' not in message, \
            "Option 2 should NOT jump to TPR calculation"
        
        print(f"✅ Option 2 correctly triggered exploration workflow")
        print(f"   Found keywords: {found_keywords}")
        
        return True
    
    def test_no_hallucinated_facility_names(self, session_id, test_data):
        """Test that agent uses real facility names, not generic ones."""
        print(f"\n🧪 Testing for hallucinated names in session {session_id}")
        
        # Upload file
        self.upload_file(session_id, test_data)
        
        # Ask for facility analysis
        result = self.send_chat_message(
            session_id,
            "Show me the top facilities by number of tests"
        )
        
        assert result['success'] == True, "Analysis request failed"
        
        message = result.get('message', '')
        
        # Check for generic/hallucinated names
        generic_patterns = [
            'Facility A', 'Facility B', 'Facility C',
            'Hospital A', 'Hospital B', 'Hospital C',
            'Ward A', 'Ward B', 'Ward C',
            'Location 1', 'Location 2', 'Location 3'
        ]
        
        for pattern in generic_patterns:
            assert pattern not in message, f"Found hallucinated name: {pattern}"
        
        # Should contain real names from our data
        real_facilities = ['Ikeja', 'Surulere', 'Yaba', 'Victoria', 'Lekki']
        found_real = [f for f in real_facilities if f in message]
        
        assert len(found_real) > 0, "No real facility names found in response"
        
        print(f"✅ No hallucinated names found")
        print(f"   Real facilities mentioned: {found_real}")
        
        return True
    
    def test_workflow_persistence_across_messages(self, session_id, test_data):
        """Test that workflow choice persists across multiple messages."""
        print(f"\n🧪 Testing workflow persistence for session {session_id}")
        
        # Upload and select Option 1 (TPR)
        self.upload_file(session_id, test_data)
        self.send_chat_message(session_id, "__DATA_UPLOADED__")
        
        # Choose TPR workflow
        tpr_result = self.send_chat_message(session_id, "1")
        assert 'tpr' in tpr_result.get('message', '').lower(), "TPR not triggered"
        
        # Send follow-up - should stay in TPR context
        followup = self.send_chat_message(session_id, "Show me results for under 5 age group")
        followup_msg = followup.get('message', '').lower()
        
        assert 'under 5' in followup_msg or 'u5' in followup_msg or 'age' in followup_msg, \
            "Follow-up didn't maintain TPR context"
        
        print("✅ Workflow context persists across messages")
        
        return True


def run_staging_tests():
    """Run all staging tests with detailed output."""
    print("=" * 60)
    print("Testing Two-Option Workflow on Staging Server")
    print("=" * 60)
    print(f"Target: {TestStagingTwoOptions.BASE_URL}")
    print("=" * 60)
    
    test_suite = TestStagingTwoOptions()
    
    # Generate unique session IDs for each test
    from datetime import datetime
    import time
    
    tests = [
        ("Initial Upload Shows Two Options", test_suite.test_initial_upload_shows_two_options),
        ("Option 1 Triggers TPR Workflow", test_suite.test_option_1_triggers_tpr_workflow),
        ("Option 2 Triggers Exploration", test_suite.test_option_2_triggers_exploration),
        ("No Hallucinated Facility Names", test_suite.test_no_hallucinated_facility_names),
        ("Workflow Persistence", test_suite.test_workflow_persistence_across_messages)
    ]
    
    passed = 0
    failed = 0
    
    # Create test data once
    test_data = test_suite.get_test_data()
    
    for name, test_func in tests:
        try:
            # Generate unique session ID for this test
            session_id = f"pytest_{datetime.now().strftime('%H%M%S')}_{passed}_{time.time_ns()}"
            
            print(f"\n{'='*60}")
            print(f"Running: {name}")
            print(f"Session: {session_id}")
            print('='*60)
            
            test_func(session_id, test_data)
            passed += 1
            print(f"✅ PASSED: {name}")
            
        except AssertionError as e:
            print(f"❌ FAILED: {name}")
            print(f"   Error: {e}")
            failed += 1
            
        except Exception as e:
            print(f"❌ ERROR in {name}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
        
        # Small delay between tests
        time.sleep(1)
    
    print("\n" + "=" * 60)
    print("STAGING TEST RESULTS")
    print("=" * 60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 ALL STAGING TESTS PASSED!")
        return True
    else:
        print(f"\n❌ {failed} test(s) failed")
        return False


if __name__ == "__main__":
    # Option 1: Run with custom runner
    success = run_staging_tests()
    
    # Option 2: Run with pytest (uncomment to use)
    # import subprocess
    # result = subprocess.run(
    #     ['pytest', __file__, '-v', '--tb=short'],
    #     capture_output=False
    # )
    # success = result.returncode == 0
    
    exit(0 if success else 1)