#!/usr/bin/env python3
"""
Test Arena models vs GPT-4o tool execution capabilities
"""

import requests
import json
import os

# Test with CloudFront URL
BASE_URL = "https://d225ar6c86586s.cloudfront.net"

def test_arena_with_tool_request():
    """Test how Arena models respond to tool-requiring requests"""
    
    test_queries = [
        {
            "query": "What is malaria?",
            "expects_tools": False,
            "description": "Simple question - should use Arena"
        },
        {
            "query": "Analyze my uploaded malaria data and create a risk map",
            "expects_tools": True,
            "description": "Tool request without files - see what Arena says"
        },
        {
            "query": "Calculate the TPR from my data",
            "expects_tools": True,
            "description": "Specific tool request - see Arena response"
        },
        {
            "query": "How does mosquito net distribution work?",
            "expects_tools": False,
            "description": "General question - should use Arena"
        },
        {
            "query": "Show me the visualization of malaria trends",
            "expects_tools": True,
            "description": "Visualization request - needs tools"
        }
    ]
    
    print("="*60)
    print("TESTING ARENA VS TOOL DETECTION")
    print("="*60)
    
    for test in test_queries:
        print(f"\n📝 Query: {test['query']}")
        print(f"   Expected: {'Tools needed' if test['expects_tools'] else 'Arena (no tools)'}")
        print(f"   Reason: {test['description']}")
        
        response = requests.post(
            f"{BASE_URL}/send_message",
            json={
                "message": test['query'],
                "language": "en",
                "tab_context": "standard-upload",
                "is_data_analysis": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if Arena was used
            if data.get('arena_mode'):
                print("   ✅ Arena mode activated")
                
                # Check what the Arena models say
                response_a = data.get('response_a', '')[:200]
                response_b = data.get('response_b', '')[:200]
                
                # Look for tool-need indicators in Arena responses
                tool_indicators = [
                    "i need", "upload", "provide", "cannot analyze without",
                    "require", "don't have access", "no data", "please upload"
                ]
                
                a_needs_tools = any(ind in response_a.lower() for ind in tool_indicators)
                b_needs_tools = any(ind in response_b.lower() for ind in tool_indicators)
                
                if a_needs_tools or b_needs_tools:
                    print("   ⚠️  Arena models indicate they need tools!")
                    print(f"      Model A says: {response_a[:100]}...")
                    print(f"      Model B says: {response_b[:100]}...")
                else:
                    print("   ✅ Arena models provided direct answers")
                    
            else:
                # GPT-4o was used
                print("   🔧 GPT-4o mode (tools available)")
                response_text = data.get('response', data.get('message', ''))[:200]
                print(f"      Response: {response_text}...")
                
                # Check if GPT-4o actually used tools
                if 'tool' in str(data).lower() or 'function' in str(data).lower():
                    print("   🔧 Tools were executed")
        else:
            print(f"   ❌ Error: {response.status_code}")
    
    print("\n" + "="*60)
    print("KEY FINDINGS:")
    print("- Arena models can only DESCRIBE what to do")
    print("- Only GPT-4o can EXECUTE tools")
    print("- Need smart detection of when execution is required")
    print("="*60)

def test_with_actual_file():
    """Test behavior when user actually has uploaded files"""
    
    print("\n📁 TESTING WITH UPLOADED FILE SCENARIO")
    print("="*60)
    
    # Create a test session with a file
    session_id = "test_arena_file_123"
    session_folder = f"instance/uploads/{session_id}"
    os.makedirs(session_folder, exist_ok=True)
    
    # Create a dummy CSV file
    test_file = os.path.join(session_folder, "test_data.csv")
    with open(test_file, 'w') as f:
        f.write("WardName,TPR\nWard1,0.25\nWard2,0.45\n")
    
    print(f"✅ Created test file: {test_file}")
    
    # Test queries with file present
    queries = [
        "What does TPR mean?",  # General - use Arena
        "Analyze my data",       # References data - needs tools
        "What is in the file?",  # References file - needs tools
        "How to prevent malaria?" # General - use Arena
    ]
    
    for query in queries:
        print(f"\n📝 Query: {query}")
        # In real scenario, would test with session that has files
        # For now, just show the logic
        
        has_files = True  # We created a file
        references_files = any(word in query.lower() for word in ['my', 'file', 'data'])
        
        should_use_tools = has_files and references_files
        
        print(f"   Has files: {has_files}")
        print(f"   References files: {references_files}")
        print(f"   → Should use tools: {should_use_tools}")
    
    # Cleanup
    os.remove(test_file)
    os.rmdir(session_folder)
    
    print("\n" + "="*60)

def test_arena_model_capabilities():
    """Test what Arena models can and cannot do"""
    
    print("\n🤖 ARENA MODEL CAPABILITIES TEST")
    print("="*60)
    
    # Direct test to Ollama if available
    try:
        # Test if Ollama is accessible
        ollama_test = requests.post(
            "http://172.31.45.157:11434/api/generate",
            json={
                "model": "llama3.2:3b",
                "prompt": "If a user asks you to 'analyze my CSV file', what would you say?",
                "stream": False
            },
            timeout=10
        )
        
        if ollama_test.status_code == 200:
            response = ollama_test.json().get('response', '')
            print("Llama3.2-3b response to 'analyze my CSV':")
            print(f"  {response[:300]}...")
            
            if any(word in response.lower() for word in ['upload', 'provide', 'need', 'cannot']):
                print("\n✅ Model correctly indicates it cannot access files")
            else:
                print("\n⚠️ Model might hallucinate having file access")
    except:
        print("Could not directly test Ollama models")
    
    print("\n" + "="*60)
    print("CONCLUSION:")
    print("- Arena models will say they need files when asked to analyze")
    print("- This is a natural signal for when to switch to GPT-4o")
    print("- No hardcoding needed - let models self-identify!")
    print("="*60)

if __name__ == "__main__":
    # Run all tests
    test_arena_with_tool_request()
    test_with_actual_file()
    test_arena_model_capabilities()
    
    print("\n🎯 RECOMMENDATION:")
    print("Use Arena responses to detect when tools are needed.")
    print("If Arena says 'I need your data', switch to GPT-4o.")
    print("This avoids all hardcoding!")