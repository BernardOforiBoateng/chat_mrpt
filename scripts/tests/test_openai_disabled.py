#!/usr/bin/env python3
"""Test that OpenAI is disabled and vLLM is working."""

import os
import sys
sys.path.insert(0, '/home/ec2-user/ChatMRPT')

# Set environment
os.environ['USE_VLLM'] = 'true'
os.environ['USE_OLLAMA'] = 'false'
os.environ['VLLM_BASE_URL'] = 'http://172.31.45.157:8000'
os.environ['VLLM_MODEL'] = 'Qwen/Qwen3-8B'

print("\n" + "="*60)
print("TESTING OPENAI DISABLED + vLLM ENABLED")
print("="*60)

# Test 1: Try to create adapter with OpenAI
from app.core.llm_adapter import LLMAdapter

print("\n1. Testing auto-detection (should use vLLM)...")
try:
    adapter = LLMAdapter()  # Auto-detect
    print(f"   ✅ Backend: {adapter.backend}")
    print(f"   ✅ Model: {adapter.model}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n2. Testing OpenAI backend (should fail)...")
try:
    adapter = LLMAdapter(backend='openai')
    print(f"   ❌ FAILED - OpenAI was allowed!")
except ValueError as e:
    print(f"   ✅ GOOD - OpenAI blocked: {e}")
except Exception as e:
    print(f"   ❌ Unexpected error: {e}")

print("\n3. Testing vLLM backend explicitly...")
try:
    adapter = LLMAdapter(backend='vllm')
    print(f"   ✅ Backend: {adapter.backend}")
    print(f"   ✅ Model: {adapter.model}")
    
    # Test generation
    response = adapter.generate("What is 2+2?", max_tokens=10)
    print(f"   ✅ Test response: {response[:50]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n4. Testing with USE_VLLM=false (should fail)...")
os.environ['USE_VLLM'] = 'false'
try:
    adapter = LLMAdapter()  # Auto-detect
    print(f"   ❌ FAILED - Should have thrown error!")
except ValueError as e:
    print(f"   ✅ GOOD - No fallback to OpenAI: {e}")

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)