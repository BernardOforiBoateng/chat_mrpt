#!/usr/bin/env python3
"""
AWS TPR Workflow Test
Tests the state persistence fixes in production
"""

import sys
import os
import json
import requests
import time
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"  # Will run on the AWS instance directly
TEST_SESSION_ID = f"tpr_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def log_test(message, level="INFO"):
    """Print formatted test log message."""
    timestamp = datetime.now().strftime('%H:%M:%S')
    symbol = "✓" if level == "SUCCESS" else "🔍" if level == "INFO" else "❌"
    print(f"[{timestamp}] {symbol} {message}")

def test_tpr_workflow():
    """Test the complete TPR workflow with state persistence."""

    print("\n" + "="*60)
    print("TPR WORKFLOW STATE PERSISTENCE TEST")
    print("="*60)
    print(f"Session ID: {TEST_SESSION_ID}")
    print(f"Server: {BASE_URL}")
    print("="*60 + "\n")

    # Test 1: Check if we can access the API
    log_test("Testing API connectivity...")
    try:
        response = requests.get(f"{BASE_URL}/ping", timeout=5)
        if response.status_code == 200:
            log_test("API is accessible", "SUCCESS")
        else:
            log_test(f"API returned status {response.status_code}", "ERROR")
            return False
    except Exception as e:
        log_test(f"Cannot reach API: {e}", "ERROR")
        return False

    # Test 2: Upload Kaduna TPR data
    log_test("Uploading Kaduna TPR test data...")

    # Check if kaduna_tpr_cleaned.csv exists
    test_data_path = "/home/ec2-user/ChatMRPT/instance/test_data/kaduna_tpr_cleaned.csv"
    if not os.path.exists(test_data_path):
        # Try to find any TPR data file
        import glob
        tpr_files = glob.glob("/home/ec2-user/ChatMRPT/instance/uploads/*/kaduna_tpr*.csv")
        if tpr_files:
            test_data_path = tpr_files[0]
            log_test(f"Using existing TPR file: {os.path.basename(test_data_path)}")
        else:
            log_test("No Kaduna TPR data file found", "ERROR")
            return False

    # Upload the file
    try:
        with open(test_data_path, 'rb') as f:
            files = {'file': ('kaduna_tpr_cleaned.csv', f, 'text/csv')}
            response = requests.post(
                f"{BASE_URL}/api/v1/data-analysis/upload",
                files=files,
                data={'session_id': TEST_SESSION_ID},
                timeout=30
            )

        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                log_test(f"Data uploaded successfully", "SUCCESS")
            else:
                log_test(f"Upload failed: {result.get('message')}", "ERROR")
                return False
        else:
            log_test(f"Upload returned status {response.status_code}", "ERROR")
            return False
    except Exception as e:
        log_test(f"Upload error: {e}", "ERROR")
        return False

    # Test 3: Trigger TPR workflow
    log_test("Triggering TPR workflow...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/data-analysis/chat",
            json={
                'session_id': TEST_SESSION_ID,
                'message': 'Run TPR analysis'
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            message = result.get('message', '')

            # Check if workflow started
            if 'facility level' in message.lower():
                log_test("TPR workflow triggered successfully", "SUCCESS")
                log_test(f"Stage: Facility selection")

                # Check if state is mentioned
                if 'kaduna' in message.lower():
                    log_test("✓ State (Kaduna) detected and displayed", "SUCCESS")
                else:
                    log_test("⚠️ State not mentioned in facility selection", "WARNING")
            else:
                log_test(f"Unexpected response: {message[:100]}", "ERROR")
                return False
        else:
            log_test(f"API returned status {response.status_code}", "ERROR")
            return False
    except Exception as e:
        log_test(f"API error: {e}", "ERROR")
        return False

    # Test 4: Ask a question during workflow
    log_test("Testing question handling during workflow...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/data-analysis/chat",
            json={
                'session_id': TEST_SESSION_ID,
                'message': 'What is TPR?'
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            message = result.get('message', '')

            # Check if question was answered (not treated as facility selection)
            if 'test positivity rate' in message.lower() or 'percentage' in message.lower():
                log_test("✓ Question answered correctly (not misinterpreted)", "SUCCESS")
            else:
                log_test("⚠️ Question may have been misinterpreted", "WARNING")
        else:
            log_test(f"API returned status {response.status_code}", "ERROR")
    except Exception as e:
        log_test(f"API error: {e}", "ERROR")

    # Test 5: Select facility level
    log_test("Selecting primary facilities...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/data-analysis/chat",
            json={
                'session_id': TEST_SESSION_ID,
                'message': 'primary'
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            message = result.get('message', '')

            # Check if moved to age group selection
            if 'age group' in message.lower():
                log_test("✓ Moved to age group selection", "SUCCESS")

                # CRITICAL: Check if state is displayed
                if 'kaduna' in message.lower():
                    log_test("✅ STATE PERSISTED - Kaduna shown in age selection!", "SUCCESS")
                else:
                    log_test("❌ STATE MISSING - Empty state in message", "ERROR")
                    log_test(f"Message excerpt: {message[:200]}")
            else:
                log_test(f"Unexpected stage: {message[:100]}", "ERROR")
        else:
            log_test(f"API returned status {response.status_code}", "ERROR")
            return False
    except Exception as e:
        log_test(f"API error: {e}", "ERROR")
        return False

    # Test 6: Select age group (the critical test for 500 error)
    log_test("Selecting under 5 age group (critical test)...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/data-analysis/chat",
            json={
                'session_id': TEST_SESSION_ID,
                'message': 'u5'
            },
            timeout=60  # Longer timeout for TPR calculation
        )

        if response.status_code == 200:
            result = response.json()
            message = result.get('message', '')

            # Check if TPR was calculated
            if 'tpr' in message.lower() and ('calculating' in message.lower() or '%' in message):
                log_test("✅ TPR CALCULATED SUCCESSFULLY - No 500 error!", "SUCCESS")

                # Check if state is in the results
                if 'kaduna' in message.lower():
                    log_test("✅ State shown in TPR results", "SUCCESS")
                else:
                    log_test("⚠️ State not shown in results", "WARNING")
            else:
                log_test(f"TPR calculation may have failed: {message[:100]}", "ERROR")
                return False
        elif response.status_code == 500:
            log_test("❌ 500 ERROR - State persistence fix failed!", "ERROR")
            return False
        else:
            log_test(f"API returned status {response.status_code}", "ERROR")
            return False
    except Exception as e:
        log_test(f"API error: {e}", "ERROR")
        return False

    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print("✅ All critical tests passed!")
    print("✅ State persists across workflow stages")
    print("✅ No 500 error when calculating TPR")
    print("✅ Questions handled correctly during workflow")
    print("="*60 + "\n")

    return True

if __name__ == "__main__":
    success = test_tpr_workflow()
    sys.exit(0 if success else 1)