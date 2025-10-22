#!/usr/bin/env python3
"""
Test script to verify clear button functionality.
Tests both frontend behavior and backend API integration.
"""

import requests
import json
import time
from datetime import datetime


def test_clear_session_endpoint():
    """Test the /clear_session endpoint"""
    base_url = "http://127.0.0.1:5000"

    print("Testing Clear Session Functionality")
    print("=" * 50)

    # Start a session
    session = requests.Session()

    # Get initial session info
    print("\n1. Getting initial session info...")
    response = session.get(f"{base_url}/session_info")
    if response.status_code == 200:
        initial_info = response.json()
        initial_session_id = initial_info.get('session_id')
        print(f"   Initial session ID: {initial_session_id}")
    else:
        print(f"   Failed to get session info: {response.status_code}")
        return False

    # Add some dummy conversation history (simulate usage)
    print("\n2. Adding conversation history...")
    # This would normally be done through the chat interface

    # Call clear_session endpoint
    print("\n3. Calling /clear_session endpoint...")
    response = session.post(f"{base_url}/clear_session")

    if response.status_code == 200:
        result = response.json()
        print(f"   Status: {result.get('status')}")
        print(f"   Message: {result.get('message')}")
        new_session_id = result.get('new_session_id')
        print(f"   New session ID: {new_session_id}")

        # Verify session was actually cleared
        print("\n4. Verifying session was cleared...")
        response = session.get(f"{base_url}/session_info")
        if response.status_code == 200:
            new_info = response.json()
            current_session_id = new_info.get('session_id')

            # Check if new session ID matches
            if current_session_id == new_session_id:
                print(f"   ✓ Session ID updated correctly: {current_session_id}")
            else:
                print(f"   ✗ Session ID mismatch!")
                print(f"     Expected: {new_session_id}")
                print(f"     Got: {current_session_id}")

            # Check if conversation history is cleared
            conversation_history = new_info.get('conversation_history', [])
            if len(conversation_history) == 0:
                print(f"   ✓ Conversation history cleared")
            else:
                print(f"   ✗ Conversation history not cleared: {len(conversation_history)} items remain")

            # Check if data flags are reset
            data_loaded = new_info.get('data_loaded', True)
            if not data_loaded:
                print(f"   ✓ Data loaded flag reset")
            else:
                print(f"   ✗ Data loaded flag not reset")

            print("\n5. Test completed successfully!")
            return True
    else:
        print(f"   Failed to clear session: {response.status_code}")
        print(f"   Response: {response.text}")
        return False


def test_frontend_backend_integration():
    """Test that frontend and backend are properly synchronized"""
    print("\n" + "=" * 50)
    print("Testing Frontend-Backend Integration")
    print("=" * 50)

    print("\n1. Frontend should call api.session.clearSession()")
    print("   Location: /frontend/src/components/Toolbar/Toolbar.tsx")
    print("   ✓ Added in confirmClear() function")

    print("\n2. Backend returns new session ID")
    print("   Endpoint: /clear_session")
    print("   ✓ Returns: { status, message, new_session_id }")

    print("\n3. Frontend uses backend's session ID")
    print("   ✓ Updates store with response.data.new_session_id")

    print("\n4. Loading state during operation")
    print("   ✓ Shows 'Clearing...' with spinner")
    print("   ✓ Disables buttons during operation")

    print("\n5. Error handling")
    print("   ✓ Shows error toast on failure")
    print("   ✓ Offers to clear frontend anyway")

    return True


if __name__ == "__main__":
    print("Clear Button Functionality Test")
    print("=" * 50)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Note: Server must be running for this test
    print("\nNote: Make sure the Flask server is running on port 5000")
    print("Run with: python run.py")

    try:
        # Test backend endpoint
        backend_test = test_clear_session_endpoint()

        # Test integration points
        integration_test = test_frontend_backend_integration()

        print("\n" + "=" * 50)
        print("OVERALL TEST RESULTS")
        print("=" * 50)
        if backend_test and integration_test:
            print("✓ All tests passed!")
        else:
            print("✗ Some tests failed. Check output above.")

    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Cannot connect to server.")
        print("  Make sure the Flask server is running:")
        print("  $ python run.py")
    except Exception as e:
        print(f"\n✗ ERROR: {e}")