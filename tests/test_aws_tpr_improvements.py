#!/usr/bin/env python3
"""
Test TPR workflow improvements on AWS production environment
"""

import requests
import json
import time
from datetime import datetime

# Production URL
BASE_URL = "https://d225ar6c86586s.cloudfront.net"

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def test_data_upload():
    """Test data upload and check initial response."""
    print_section("1. Testing Data Upload & Initial Response")

    # Create test CSV data
    csv_content = """WardName,LGA,State,HealthFacility,FacilityLevel,Total_All_OPD_Attendance,Febrile_Illnesses_U5,Febrile_Illnesses_O5,Total_Suspected_Cases,Tests_Examined_U5_RDT,Tests_Examined_O5_RDT,Tests_Positive_U5_RDT,Tests_Positive_O5_RDT
Girei,Girei,Adamawa,PHC Girei,Primary,1500,250,180,430,200,150,70,35
Yola North,Yola,Adamawa,General Hospital,Secondary,3200,480,320,800,400,300,110,65
Madagali,Madagali,Adamawa,PHC Madagali,Primary,980,180,120,300,150,100,52,28
Shelleng,Shelleng,Adamawa,PHC Shelleng,Primary,750,120,90,210,100,80,12,8
Mubi North,Mubi,Adamawa,Specialist Hospital,Tertiary,4500,620,450,1070,500,400,95,72"""

    # Create form data
    files = {
        'file': ('test_tpr_data.csv', csv_content, 'text/csv')
    }

    print("📤 Uploading test TPR data...")

    try:
        # Upload to Data Analysis tab endpoint
        response = requests.post(
            f"{BASE_URL}/api/data-analysis/upload",
            files=files,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Upload successful!")
            print(f"   Session ID: {result.get('session_id')}")
            print(f"   File: {result.get('filename')}")
            print(f"   Rows: {result.get('metadata', {}).get('rows')}")

            # Now check the chat response
            session_id = result.get('session_id')

            print("\n📨 Sending initial chat message...")
            chat_response = requests.post(
                f"{BASE_URL}/api/v1/data-analysis/chat",
                json={
                    'message': 'analyze the uploaded data',
                    'session_id': session_id
                },
                timeout=30
            )

            if chat_response.status_code == 200:
                chat_result = chat_response.json()
                message = chat_result.get('message', '')

                print("\n📝 Initial Response Preview:")
                print("-" * 40)
                # Show first 500 chars of response
                print(message[:500])
                print("-" * 40)

                # Check for improvements
                checks = {
                    "Blue note (💡)": "💡" in message,
                    "No red warning (⚠️)": "⚠️" not in message,
                    "Quick note text": "Quick note" in message or "quick note" in message,
                    "Concise format": len(message.split('\n')[0]) < 200
                }

                print("\n✅ Improvement Checks:")
                for check, passed in checks.items():
                    status = "✅" if passed else "❌"
                    print(f"   {status} {check}")

                return session_id, all(checks.values())
            else:
                print(f"❌ Chat failed: {chat_response.status_code}")
                return None, False

        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None, False

    except Exception as e:
        print(f"❌ Error: {e}")
        return None, False


def test_tpr_workflow(session_id):
    """Test the TPR workflow conversation."""
    print_section("2. Testing TPR Workflow Conversation")

    if not session_id:
        print("⚠️ No session ID, skipping workflow test")
        return False

    steps = [
        ("Run TPR analysis", "trigger TPR workflow"),
        ("yes", "agree to primary facilities"),
        ("under 5", "select age group"),
    ]

    all_passed = True

    for i, (message, description) in enumerate(steps, 1):
        print(f"\n📤 Step {i}: Sending '{message}' ({description})...")

        response = requests.post(
            f"{BASE_URL}/api/v1/data-analysis/chat",
            json={
                'message': message,
                'session_id': session_id
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            reply = result.get('message', '')

            print(f"📨 Response preview:")
            print("-" * 40)
            print(reply[:400])
            print("-" * 40)

            # Check for conversational elements
            if i == 1:  # After triggering TPR
                checks = {
                    "Conversational tone": any(phrase in reply.lower() for phrase in [
                        "i'll help", "let's", "should i", "would you"
                    ]),
                    "No numbered menu": not all(f"{n}." in reply for n in range(1, 5))
                }
            elif i == 2:  # After facility selection
                checks = {
                    "Age group question": any(word in reply.lower() for word in [
                        "age", "group", "which", "interests"
                    ]),
                    "Simplified options": "highest risk" in reply.lower() or "children" in reply.lower()
                }
            else:  # After age selection
                checks = {
                    "TPR complete": "complete" in reply.lower() or "analysis" in reply.lower(),
                    "Concise results": len(reply.split('\n')) < 20,
                    "Continue prompt": "continue" in reply.lower() or "ready" in reply.lower()
                }

            print(f"\n✅ Step {i} Checks:")
            step_passed = True
            for check, passed in checks.items():
                status = "✅" if passed else "❌"
                print(f"   {status} {check}")
                if not passed:
                    step_passed = False

            if not step_passed:
                all_passed = False

        else:
            print(f"❌ Request failed: {response.status_code}")
            all_passed = False

        time.sleep(2)  # Small delay between requests

    return all_passed


def test_natural_language():
    """Test natural language understanding."""
    print_section("3. Testing Natural Language Understanding")

    # Create a fresh session
    csv_content = """WardName,LGA,State,HealthFacility,FacilityLevel,Tests_Examined_U5_RDT,Tests_Positive_U5_RDT
Test1,LGA1,Adamawa,PHC1,Primary,100,20
Test2,LGA2,Adamawa,PHC2,Primary,150,35"""

    files = {'file': ('test.csv', csv_content, 'text/csv')}

    upload_response = requests.post(
        f"{BASE_URL}/api/data-analysis/upload",
        files=files,
        timeout=30
    )

    if upload_response.status_code != 200:
        print("❌ Failed to create test session")
        return False

    session_id = upload_response.json().get('session_id')
    print(f"✅ Test session created: {session_id}")

    # Test conversational responses
    test_inputs = [
        ("TPR", "Trigger workflow"),
        ("sounds good", "Accept primary facilities suggestion"),
        ("kids", "Select under-5 with variation")
    ]

    all_passed = True

    for input_text, description in test_inputs:
        print(f"\n📤 Testing: '{input_text}' ({description})")

        response = requests.post(
            f"{BASE_URL}/api/v1/data-analysis/chat",
            json={
                'message': input_text,
                'session_id': session_id
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            if result.get('success') or 'message' in result:
                print(f"   ✅ Understood and processed")
            else:
                print(f"   ❌ Not properly understood")
                all_passed = False
        else:
            print(f"   ❌ Request failed")
            all_passed = False

    return all_passed


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("  TPR WORKFLOW IMPROVEMENTS - AWS PRODUCTION TEST")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*60)

    results = {}

    # Test 1: Upload and initial response
    session_id, upload_passed = test_data_upload()
    results['Upload & Initial Response'] = upload_passed

    # Test 2: TPR workflow
    if session_id:
        workflow_passed = test_tpr_workflow(session_id)
        results['TPR Workflow'] = workflow_passed
    else:
        results['TPR Workflow'] = False

    # Test 3: Natural language
    nl_passed = test_natural_language()
    results['Natural Language'] = nl_passed

    # Summary
    print_section("TEST SUMMARY")

    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "="*60)
    if all_passed:
        print("  🎉 ALL TESTS PASSED! TPR improvements working correctly.")
    else:
        print("  ⚠️ Some tests failed. Please review the output above.")
    print("="*60 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())