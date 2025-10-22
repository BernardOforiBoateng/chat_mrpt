#!/usr/bin/env python3
"""
Debug why agent can't access healthfacility column
"""

import pandas as pd
import requests
import time

# Load the actual data to verify columns
df = pd.read_csv('www/adamawa_tpr_cleaned.csv')

print("=" * 60)
print("INVESTIGATING FACILITY ACCESS ISSUE")
print("=" * 60)

print("\n1. Checking actual data columns:")
print(f"   Columns: {df.columns.tolist()[:10]}...")

# Check for facility-related columns
facility_cols = [col for col in df.columns if 'facility' in col.lower() or 'health' in col.lower()]
print(f"\n2. Facility-related columns found: {facility_cols}")

if 'healthfacility' in df.columns:
    print(f"\n3. Sample facility names from 'healthfacility' column:")
    facilities = df['healthfacility'].dropna().unique()[:5]
    for i, f in enumerate(facilities, 1):
        print(f"   {i}. {f}")
    print(f"   Total unique facilities: {df['healthfacility'].nunique()}")

# Test what the agent sees
STAGING_URL = "http://3.21.167.170:8080"
session_id = f"debug_{int(time.time())}"

print("\n4. Testing agent's ability to see columns...")
print("   Uploading data...")

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
    
    # Ask agent to list columns
    print("\n5. Asking agent to list columns...")
    response = requests.post(
        f"{STAGING_URL}/api/v1/data-analysis/chat",
        json={
            "message": "What are the exact column names in the data? List them all.",
            "session_id": session_id
        },
        timeout=60
    )
    
    if response.status_code == 200:
        result = response.json()
        message = result.get("message", "")
        print("\n   Agent's response about columns:")
        print("   " + "-" * 40)
        print(message[:500] + "..." if len(message) > 500 else message)
        print("   " + "-" * 40)
    
    # Ask agent to show facility names
    print("\n6. Asking agent to show actual facility names...")
    response = requests.post(
        f"{STAGING_URL}/api/v1/data-analysis/chat",
        json={
            "message": "Show me the first 5 unique values from the 'healthfacility' column. Use code: print(df['healthfacility'].unique()[:5])",
            "session_id": session_id
        },
        timeout=60
    )
    
    if response.status_code == 200:
        result = response.json()
        message = result.get("message", "")
        print("\n   Agent's response about facilities:")
        print("   " + "-" * 40)
        print(message[:800])
        print("   " + "-" * 40)
        
        # Check for "Facility A" pattern
        if "Facility A" in message or "Facility B" in message:
            print("\n   ❌ PROBLEM: Agent is using generic names!")
        else:
            print("\n   ✅ Agent is using real facility names")

print("\n" + "=" * 60)
print("INVESTIGATION SUMMARY")
print("=" * 60)

print("""
Possible causes of hallucination:
1. Column names are being sanitized and agent can't find 'healthfacility'
2. Agent is not executing the code properly
3. Response formatter is replacing real names with generic ones
4. LLM is not receiving the actual output from code execution
""")