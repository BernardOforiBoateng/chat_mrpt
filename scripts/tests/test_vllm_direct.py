#!/usr/bin/env python3
"""
Direct test of vLLM server
"""
import requests
import json

VLLM_BASE_URL = "http://172.31.45.157:8000"

def test_vllm():
    """Test vLLM directly."""
    
    print("=" * 60)
    print("Testing vLLM Server Directly")
    print(f"Server: {VLLM_BASE_URL}")
    print("=" * 60)
    
    # Test 1: Check if server is up
    print("\n1. Checking server status...")
    try:
        response = requests.get(f"{VLLM_BASE_URL}/v1/models", timeout=5)
        if response.status_code == 200:
            print("✓ Server is up")
            models = response.json()
            print(f"  Available models: {models.get('data', [])}")
        else:
            print(f"✗ Server returned status {response.status_code}")
    except Exception as e:
        print(f"✗ Cannot reach server: {e}")
        return
    
    # Test 2: Generate completion
    print("\n2. Testing code generation...")
    
    prompts_to_test = [
        # Simplest possible
        "print(1+1)",
        
        # Explicit Python code request
        "Python code only:\nprint('Hello')",
        
        # Data analysis style
        """Generate executable Python code:
import pandas as pd
print("Starting analysis")
""",
    ]
    
    for i, prompt in enumerate(prompts_to_test, 1):
        print(f"\n  Test 2.{i}: {prompt[:50]}...")
        
        payload = {
            "model": "Qwen/Qwen3-8B",
            "prompt": prompt,
            "max_tokens": 200,
            "temperature": 0.1,
            "stop": ["```", "\n\n\n"]
        }
        
        try:
            response = requests.post(
                f"{VLLM_BASE_URL}/v1/completions",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result['choices'][0]['text']
                
                print(f"    Response length: {len(generated_text)}")
                print(f"    First 200 chars: {generated_text[:200]}")
                
                # Check what we got
                if "```" in generated_text:
                    print("    ⚠️  Contains markdown code blocks")
                if "**" in generated_text or "##" in generated_text:
                    print("    ⚠️  Contains markdown formatting")
                if generated_text.strip().startswith("-") or generated_text.strip().startswith("*"):
                    print("    ⚠️  Looks like markdown list")
                    
            else:
                print(f"    ✗ Error: {response.status_code}")
                print(f"    {response.text[:200]}")
                
        except Exception as e:
            print(f"    ✗ Request failed: {e}")
    
    print("\n" + "=" * 60)
    print("Test complete")

if __name__ == "__main__":
    test_vllm()