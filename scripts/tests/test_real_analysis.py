#!/usr/bin/env python3
"""Test real analysis flow with actual data"""

import requests
import json
import time
import os

BASE_URL = "http://127.0.0.1:5013"

def test_real_analysis():
    """Test with actual uploaded data"""
    
    session = requests.Session()
    
    # 1. Initialize session
    print("1. Getting homepage to initialize session...")
    response = session.get(f"{BASE_URL}/")
    print(f"   Status: {response.status_code}")
    
    # 2. Check initial session state
    print("\n2. Checking initial session state...")
    response = session.get(f"{BASE_URL}/debug/session_state")
    initial_state = response.json()
    print(f"   Session ID: {initial_state['session_state']['session_id']}")
    print(f"   Analysis complete: {initial_state['session_state']['analysis_complete']}")
    
    # 3. Check if we have existing data
    session_id = initial_state['session_state']['session_id']
    session_folder = f"instance/uploads/{session_id}"
    
    # Create test data if needed
    if not os.path.exists(session_folder):
        print(f"\n3. Creating test session data...")
        os.makedirs(session_folder, exist_ok=True)
        
        # Copy sample data from existing session
        sample_session = "59b18890-638c-4c1e-862b-82a900cea3e9"
        sample_folder = f"instance/uploads/{sample_session}"
        
        if os.path.exists(sample_folder):
            # Copy CSV file
            os.system(f"cp {sample_folder}/raw_data.csv {session_folder}/")
            # Copy shapefile
            os.system(f"cp -r {sample_folder}/shapefile {session_folder}/")
            print("   Test data copied")
        else:
            print("   Warning: No sample data found")
    
    # 4. Mark data as loaded in session
    print("\n4. Marking data as loaded...")
    with session.post(f"{BASE_URL}/send_message", 
                     json={'message': '__DATA_UPLOADED__'},
                     headers={'Content-Type': 'application/json'}) as resp:
        print(f"   Data loaded response: {resp.status_code}")
    
    # 5. Send analysis request via streaming
    print("\n5. Sending analysis request via streaming endpoint...")
    
    tools_found = []
    chunks_received = 0
    
    with session.post(f"{BASE_URL}/send_message_streaming",
                     json={'message': 'Run complete malaria risk analysis using both methods'},
                     headers={'Content-Type': 'application/json'},
                     stream=True) as resp:
        
        print(f"   Streaming response status: {resp.status_code}")
        
        for line in resp.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        chunk = json.loads(line_str[6:])
                        chunks_received += 1
                        
                        # Track tools
                        if chunk.get('tools_used'):
                            tools_found.extend(chunk['tools_used'])
                            print(f"   Chunk {chunks_received}: tools_used = {chunk['tools_used']}")
                        
                        # Check if done
                        if chunk.get('done'):
                            print(f"   Final chunk received (chunk {chunks_received})")
                            if chunk.get('tools_used'):
                                print(f"   Final chunk includes tools: {chunk['tools_used']}")
                            
                    except json.JSONDecodeError as e:
                        print(f"   Error parsing chunk: {e}")
    
    print(f"\n   Total chunks: {chunks_received}")
    print(f"   Tools found: {tools_found}")
    
    # 6. Check session state after streaming
    time.sleep(1)  # Give it a moment to process
    
    print("\n6. Checking session state after analysis...")
    response = session.get(f"{BASE_URL}/debug/session_state")
    final_state = response.json()
    print(f"   Session ID: {final_state['session_state']['session_id']}")
    print(f"   Analysis complete: {final_state['session_state']['analysis_complete']}")
    
    # 7. Verdict
    print("\n7. Test Result:")
    if final_state['session_state']['analysis_complete']:
        print("   ✅ SUCCESS: Session properly updated after streaming!")
    else:
        print("   ❌ FAILURE: Session not updated despite tools being used")
        print(f"   Tools that were used: {tools_found}")
        
        # Check if analysis tools were in the list
        analysis_tools = ['run_composite_analysis', 'run_pca_analysis', 'runcompleteanalysis']
        found_analysis_tools = [t for t in tools_found if t in analysis_tools]
        print(f"   Analysis tools found: {found_analysis_tools}")

if __name__ == "__main__":
    time.sleep(2)  # Let Flask fully start
    test_real_analysis()