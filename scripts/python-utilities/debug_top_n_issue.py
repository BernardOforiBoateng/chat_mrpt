#!/usr/bin/env python3
"""
Debug why "top 10" only shows 3 items
"""

import requests
import time
import re

STAGING_URL = "http://3.21.167.170:8080"
session_id = f"debug_topn_{int(time.time())}"

print("=" * 60)
print("INVESTIGATING TOP N TRUNCATION ISSUE")
print("=" * 60)

# Upload data
print("\n1. Uploading data...")
with open('www/adamawa_tpr_cleaned.csv', 'rb') as f:
    files = {'file': ('test.csv', f)}
    data = {'session_id': session_id}
    
    response = requests.post(
        f"{STAGING_URL}/api/data-analysis/upload",
        files=files,
        data=data,
        timeout=30
    )
    
    if response.status_code == 200:
        print("   ✅ Upload successful")

time.sleep(3)

# Test different "top N" queries
test_queries = [
    {
        "query": "Show me EXACTLY 10 facilities. Use this code: for i, name in enumerate(df['healthfacility'].unique()[:10], 1): print(f'{i}. {name}')",
        "expected": 10,
        "description": "Explicit code with loop"
    },
    {
        "query": "List the top 10 health facilities by total testing volume",
        "expected": 10,
        "description": "Natural language request"
    },
    {
        "query": "Show me the first 5 rows of the dataframe",
        "expected": 5,
        "description": "DataFrame head request"
    }
]

for idx, test in enumerate(test_queries, 1):
    print(f"\n{idx}. Testing: {test['description']}")
    print(f"   Query: {test['query'][:80]}...")
    
    response = requests.post(
        f"{STAGING_URL}/api/v1/data-analysis/chat",
        json={
            "message": test['query'],
            "session_id": session_id
        },
        timeout=60
    )
    
    if response.status_code == 200:
        result = response.json()
        message = result.get("message", "")
        
        # Count numbered items
        numbered_items = re.findall(r'^\s*\d+\.', message, re.MULTILINE)
        
        print(f"   Expected: {test['expected']} items")
        print(f"   Found: {len(numbered_items)} numbered items")
        
        if len(numbered_items) < test['expected']:
            print(f"   ❌ TRUNCATION DETECTED!")
            print(f"\n   Response preview:")
            print("   " + "-" * 40)
            # Show the response to see where it cuts off
            lines = message.split('\n')
            for line in lines[:20]:  # Show first 20 lines
                if line.strip():
                    print(f"   {line}")
            print("   " + "-" * 40)
        else:
            print(f"   ✅ Correct number of items")

print("\n" + "=" * 60)
print("FINDINGS")
print("=" * 60)

# Now check specific files for limits
print("\nChecking for hardcoded limits in code...")

# Files to check
files_to_check = [
    "app/data_analysis_v3/formatters/response_formatter.py",
    "app/data_analysis_v3/core/executor.py",
    "app/data_analysis_v3/prompts/system_prompt.py",
    "app/data_analysis_v3/core/agent.py"
]

import os
for file_path in files_to_check:
    if os.path.exists(file_path):
        print(f"\nChecking {file_path}...")
        with open(file_path, 'r') as f:
            content = f.read()
            
            # Look for patterns that might limit output
            patterns = [
                (r'\.head\(\d+\)', 'head() limit'),
                (r'\[:(\d+)\]', 'slice limit'),
                (r'range\(\d+\)', 'range limit'),
                (r'limit.*=.*\d+', 'limit variable'),
                (r'max.*=.*\d+', 'max variable'),
                (r'insights\[:\d+\]', 'insights slice')
            ]
            
            for pattern, description in patterns:
                import re
                matches = re.findall(pattern, content)
                if matches:
                    print(f"   Found {description}: {matches[:3]}")

print("\n" + "=" * 60)