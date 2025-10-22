"""
Test full TPR workflow for multiple states to identify why some states don't show maps
"""

import requests
import json
import time
import sys
from typing import Dict, Tuple

# Production URL
BASE_URL = "https://d225ar6c86586s.cloudfront.net"

def run_full_tpr_workflow(state_name: str, csv_file: str) -> Tuple[bool, Dict]:
    """
    Run complete TPR workflow for a state.

    Returns:
        Tuple of (success, details)
    """
    result = {
        'state': state_name,
        'upload_success': False,
        'state_detected': False,
        'workflow_completed': False,
        'map_generated': False,
        'visualization_stored': False,
        'error': None,
        'session_id': None
    }

    try:
        # Step 1: Upload data
        print(f"\n{'='*60}")
        print(f"Testing {state_name}")
        print(f"{'='*60}")

        with open(csv_file, 'rb') as f:
            files = {'file': (f'{state_name.lower()}_tpr_cleaned.csv', f, 'text/csv')}
            response = requests.post(f"{BASE_URL}/api/data-analysis/upload", files=files)

        if response.status_code != 200:
            result['error'] = f"Upload failed: {response.status_code}"
            return False, result

        upload_result = response.json()
        session_id = upload_result.get('session_id')
        result['session_id'] = session_id
        result['upload_success'] = True
        print(f"✓ Upload successful. Session: {session_id[:16]}...")

        # Step 2: Initial TPR request
        chat_data = {
            'message': 'Run TPR analysis',
            'session_id': session_id
        }

        response = requests.post(
            f"{BASE_URL}/api/v1/data-analysis/chat",
            json=chat_data,
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code != 200:
            result['error'] = f"Initial TPR request failed: {response.status_code}"
            return False, result

        chat_result = response.json()
        response_text = chat_result.get('message', '')

        # Check if state was detected
        if state_name.lower() in response_text.lower():
            result['state_detected'] = True
            print(f"✓ State detected: {state_name}")
        else:
            print(f"✗ State NOT detected in response")

        # Step 3: Select facility level (primary)
        print("  Selecting facility level: primary...")
        chat_data = {
            'message': 'primary',
            'session_id': session_id
        }

        response = requests.post(
            f"{BASE_URL}/api/v1/data-analysis/chat",
            json=chat_data,
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code != 200:
            result['error'] = f"Facility selection failed: {response.status_code}"
            return False, result

        # Step 4: Select age group (under 5)
        print("  Selecting age group: under 5...")
        chat_data = {
            'message': 'u5',
            'session_id': session_id
        }

        response = requests.post(
            f"{BASE_URL}/api/v1/data-analysis/chat",
            json=chat_data,
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code != 200:
            result['error'] = f"Age group selection failed: {response.status_code}"
            return False, result

        final_result = response.json()
        final_text = final_result.get('message', '')

        # Check if workflow completed
        if 'calculated' in final_text.lower() or 'tpr results' in final_text.lower():
            result['workflow_completed'] = True
            print(f"✓ Workflow completed")
        else:
            print(f"✗ Workflow may not have completed properly")

        # Check for map generation
        if 'map' in final_text.lower() or 'visualization' in final_text.lower():
            result['map_generated'] = True
            print(f"✓ Map mentioned in response")
        else:
            print(f"✗ No map mentioned")

        # Check for stored visualizations
        visualizations = final_result.get('visualizations', [])
        if visualizations:
            result['visualization_stored'] = True
            print(f"✓ {len(visualizations)} visualization(s) stored")
            for viz in visualizations:
                print(f"    - {viz.get('type', 'unknown')}: {viz.get('title', 'no title')}")
                if viz.get('html_content'):
                    print(f"      HTML size: {len(viz.get('html_content'))} chars")
        else:
            print(f"✗ No visualizations stored in response")

        # Extract key info from response
        print(f"\nResponse snippet:")
        print(f"  {final_text[:300]}...")

        return result['visualization_stored'], result

    except Exception as e:
        result['error'] = str(e)
        print(f"✗ Error: {e}")
        return False, result

def main():
    """Test multiple states to identify the pattern."""

    # States to test
    working_states = [
        ('Adamawa', '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/www/all_states_cleaned/adamawa_tpr_cleaned.csv'),
        ('Cross River', '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/www/all_states_cleaned/cross_river_tpr_cleaned.csv'),
        ('Sokoto', '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/www/all_states_cleaned/sokoto_tpr_cleaned.csv'),
        ('Zamfara', '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/www/all_states_cleaned/zamfara_tpr_cleaned.csv'),
    ]

    problematic_states = [
        ('Benue', '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/www/all_states_cleaned/benue_tpr_cleaned.csv'),
        ('Ebonyi', '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/www/all_states_cleaned/ebonyi_tpr_cleaned.csv'),
        ('Kebbi', '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/www/all_states_cleaned/kebbi_tpr_cleaned.csv'),
        ('Nasarawa', '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/www/all_states_cleaned/nasarawa_tpr_cleaned.csv'),
        ('Plateau', '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/www/all_states_cleaned/plateau_tpr_cleaned.csv'),
    ]

    print("="*80)
    print("FULL TPR WORKFLOW TEST - COMPARING WORKING VS PROBLEMATIC STATES")
    print("="*80)
    print("\nWorkflow: Upload → TPR Analysis → Select Primary → Select Under 5")

    # Test working states
    print(f"\n{'='*80}")
    print("TESTING WORKING STATES")
    print(f"{'='*80}")

    working_results = []
    for state_name, csv_file in working_states:
        success, details = run_full_tpr_workflow(state_name, csv_file)
        working_results.append(details)
        time.sleep(2)  # Be nice to the server

    # Test problematic states
    print(f"\n{'='*80}")
    print("TESTING PROBLEMATIC STATES")
    print(f"{'='*80}")

    problematic_results = []
    for state_name, csv_file in problematic_states:
        success, details = run_full_tpr_workflow(state_name, csv_file)
        problematic_results.append(details)
        time.sleep(2)

    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY RESULTS")
    print(f"{'='*80}")

    print("\n📊 Working States:")
    for r in working_results:
        status = "✅" if r['visualization_stored'] else "❌"
        print(f"  {status} {r['state']:15} - Upload: {r['upload_success']}, "
              f"Detected: {r['state_detected']}, Workflow: {r['workflow_completed']}, "
              f"Map: {r['map_generated']}, Viz Stored: {r['visualization_stored']}")

    print("\n📊 Problematic States:")
    for r in problematic_results:
        status = "✅" if r['visualization_stored'] else "❌"
        print(f"  {status} {r['state']:15} - Upload: {r['upload_success']}, "
              f"Detected: {r['state_detected']}, Workflow: {r['workflow_completed']}, "
              f"Map: {r['map_generated']}, Viz Stored: {r['visualization_stored']}")

    # Analysis
    print(f"\n{'='*80}")
    print("ANALYSIS")
    print(f"{'='*80}")

    working_success_rate = sum(1 for r in working_results if r['visualization_stored']) / len(working_results) * 100
    problematic_success_rate = sum(1 for r in problematic_results if r['visualization_stored']) / len(problematic_results) * 100

    print(f"\nWorking states success rate: {working_success_rate:.0f}%")
    print(f"Problematic states success rate: {problematic_success_rate:.0f}%")

    # Find patterns
    print("\n🔍 Pattern Analysis:")

    # Check what's different
    working_patterns = {
        'all_detected': all(r['state_detected'] for r in working_results),
        'all_completed': all(r['workflow_completed'] for r in working_results),
        'all_maps': all(r['map_generated'] for r in working_results),
    }

    problematic_patterns = {
        'all_detected': all(r['state_detected'] for r in problematic_results),
        'all_completed': all(r['workflow_completed'] for r in problematic_results),
        'all_maps': all(r['map_generated'] for r in problematic_results),
    }

    print(f"\nWorking states patterns:")
    for key, value in working_patterns.items():
        print(f"  {key}: {value}")

    print(f"\nProblematic states patterns:")
    for key, value in problematic_patterns.items():
        print(f"  {key}: {value}")

    return working_success_rate > problematic_success_rate

if __name__ == "__main__":
    success = main()
    sys.exit(0 if not success else 1)