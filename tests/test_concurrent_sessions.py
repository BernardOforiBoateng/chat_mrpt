"""
Test Concurrent Sessions
Verifies that multiple concurrent uploads get unique session IDs and don't interfere with each other.
"""

import asyncio
import aiohttp
import os
from pathlib import Path
import json
from typing import List, Dict

# Test configuration
BASE_URL = "http://127.0.0.1:5000"  # Local test server
# BASE_URL = "https://d225ar6c86586s.cloudfront.net"  # Production URL

# Test data files
TEST_FILES = [
    "benue_tpr_cleaned.csv",
    "kebbi_tpr_cleaned.csv",
    "ebonyi_tpr_cleaned.csv",
    "nasarawa_tpr_cleaned.csv",
    "plateau_tpr_cleaned.csv"
]

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

async def upload_file(session: aiohttp.ClientSession, file_name: str, file_index: int) -> Dict:
    """
    Upload a single file and return the session ID received.
    """
    try:
        # Create form data
        data = aiohttp.FormData()

        # Add the file (using a dummy CSV for testing)
        csv_content = f"State,LGA,WardName,Test\n{file_name.split('_')[0]},TestLGA,TestWard,{file_index}\n"
        data.add_field('file', csv_content.encode(), filename=file_name, content_type='text/csv')

        # Upload to data analysis endpoint
        async with session.post(f"{BASE_URL}/api/data-analysis/upload", data=data) as response:
            result = await response.json()

            if result.get('status') == 'success':
                session_id = result.get('session_id', 'NO_SESSION_ID')
                print(f"{Colors.OKGREEN}✓{Colors.ENDC} Upload {file_index} ({file_name}): Session ID = {session_id[:8]}...")
                return {
                    'file': file_name,
                    'index': file_index,
                    'session_id': session_id,
                    'success': True
                }
            else:
                print(f"{Colors.FAIL}✗{Colors.ENDC} Upload {file_index} ({file_name}): Failed - {result.get('message')}")
                return {
                    'file': file_name,
                    'index': file_index,
                    'error': result.get('message'),
                    'success': False
                }

    except Exception as e:
        print(f"{Colors.FAIL}✗{Colors.ENDC} Upload {file_index} ({file_name}): Exception - {str(e)}")
        return {
            'file': file_name,
            'index': file_index,
            'error': str(e),
            'success': False
        }

async def test_concurrent_uploads():
    """
    Test that concurrent uploads get unique session IDs.
    """
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== Testing Concurrent Session Isolation ==={Colors.ENDC}")
    print(f"Testing with {len(TEST_FILES)} concurrent uploads...\n")

    async with aiohttp.ClientSession() as session:
        # Launch all uploads concurrently
        tasks = [
            upload_file(session, file_name, i+1)
            for i, file_name in enumerate(TEST_FILES)
        ]

        results = await asyncio.gather(*tasks)

    # Analyze results
    print(f"\n{Colors.HEADER}=== Results Analysis ==={Colors.ENDC}")

    successful_uploads = [r for r in results if r.get('success')]
    failed_uploads = [r for r in results if not r.get('success')]

    if failed_uploads:
        print(f"\n{Colors.WARNING}Failed uploads: {len(failed_uploads)}{Colors.ENDC}")
        for failure in failed_uploads:
            print(f"  - {failure['file']}: {failure.get('error', 'Unknown error')}")

    if successful_uploads:
        session_ids = [r['session_id'] for r in successful_uploads]
        unique_session_ids = set(session_ids)

        print(f"\nSuccessful uploads: {len(successful_uploads)}")
        print(f"Unique session IDs: {len(unique_session_ids)}")

        # Check for duplicates
        if len(unique_session_ids) == len(session_ids):
            print(f"{Colors.OKGREEN}{Colors.BOLD}✓ SUCCESS: All uploads got unique session IDs!{Colors.ENDC}")
            print("\nSession IDs:")
            for r in successful_uploads:
                print(f"  {r['index']}. {r['file']}: {r['session_id'][:16]}...")
        else:
            print(f"{Colors.FAIL}{Colors.BOLD}✗ FAILURE: Session ID reuse detected!{Colors.ENDC}")

            # Find duplicates
            from collections import Counter
            id_counts = Counter(session_ids)
            duplicates = {sid: count for sid, count in id_counts.items() if count > 1}

            print(f"\nDuplicated session IDs:")
            for sid, count in duplicates.items():
                print(f"  {sid}: used {count} times")
                affected_files = [r['file'] for r in successful_uploads if r['session_id'] == sid]
                print(f"    Affected files: {', '.join(affected_files)}")

    # Return test status
    return len(unique_session_ids) == len(successful_uploads) and len(successful_uploads) == len(TEST_FILES)

async def test_sequential_uploads():
    """
    Test that sequential uploads (simulating multiple tabs) also get unique session IDs.
    """
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== Testing Sequential Uploads (Multiple Tabs Simulation) ==={Colors.ENDC}")
    print("Simulating user opening multiple tabs and uploading...\n")

    results = []

    # Create separate sessions (simulating different tabs)
    for i, file_name in enumerate(TEST_FILES[:3], 1):
        async with aiohttp.ClientSession() as session:
            result = await upload_file(session, file_name, i)
            results.append(result)
            await asyncio.sleep(0.5)  # Small delay between tabs

    # Analyze results
    successful_uploads = [r for r in results if r.get('success')]
    if successful_uploads:
        session_ids = [r['session_id'] for r in successful_uploads]
        unique_session_ids = set(session_ids)

        if len(unique_session_ids) == len(session_ids):
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}✓ SUCCESS: Sequential uploads got unique session IDs!{Colors.ENDC}")
        else:
            print(f"\n{Colors.FAIL}{Colors.BOLD}✗ FAILURE: Session ID reuse in sequential uploads!{Colors.ENDC}")

    return len(set([r['session_id'] for r in successful_uploads])) == len(successful_uploads)

async def main():
    """
    Run all concurrent session tests.
    """
    print(f"{Colors.OKCYAN}{Colors.BOLD}")
    print("=" * 60)
    print("     CONCURRENT SESSION ISOLATION TEST SUITE")
    print("=" * 60)
    print(f"{Colors.ENDC}")

    # Test 1: Concurrent uploads
    test1_passed = await test_concurrent_uploads()

    # Test 2: Sequential uploads (multiple tabs)
    test2_passed = await test_sequential_uploads()

    # Summary
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== Test Summary ==={Colors.ENDC}")
    print(f"Concurrent uploads test: {'✓ PASSED' if test1_passed else '✗ FAILED'}")
    print(f"Sequential uploads test: {'✓ PASSED' if test2_passed else '✗ FAILED'}")

    if test1_passed and test2_passed:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! Session isolation is working correctly.{Colors.ENDC}")
        return 0
    else:
        print(f"\n{Colors.FAIL}{Colors.BOLD}❌ TESTS FAILED! Session isolation issues detected.{Colors.ENDC}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)