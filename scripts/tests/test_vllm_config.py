#!/usr/bin/env python3
"""Test vLLM configuration on staging server."""

from dotenv import load_dotenv
import os
import sys

# Load environment
load_dotenv()

print("\n" + "="*60)
print("ENVIRONMENT CONFIGURATION CHECK")
print("="*60)
print(f"USE_VLLM: {os.environ.get('USE_VLLM', 'not set')}")
print(f"USE_OLLAMA: {os.environ.get('USE_OLLAMA', 'not set')}")
print(f"USE_LLM_TPR: {os.environ.get('USE_LLM_TPR', 'not set')}")
print(f"VLLM_BASE_URL: {os.environ.get('VLLM_BASE_URL', 'not set')}")
print(f"VLLM_MODEL: {os.environ.get('VLLM_MODEL', 'not set')}")

# Test which backend gets selected
sys.path.insert(0, '/home/ec2-user/ChatMRPT')
from app.core.llm_adapter import create_llm_adapter

print("\n" + "="*60)
print("LLM ADAPTER SELECTION")
print("="*60)

adapter = create_llm_adapter()
print(f"Selected Backend: {adapter.backend}")
print(f"Model: {adapter.model}")
print(f"Base URL: {adapter.base_url}")

# Test connection
import requests
print("\n" + "="*60)
print("VLLM CONNECTION TEST")
print("="*60)

try:
    response = requests.get("http://172.31.45.157:8000/v1/models", timeout=3)
    if response.status_code == 200:
        print("✅ vLLM Server: CONNECTED")
        data = response.json()
        if data.get("data"):
            print(f"   Model loaded: {data['data'][0]['id']}")
    else:
        print(f"❌ vLLM Server: HTTP {response.status_code}")
except Exception as e:
    print(f"❌ vLLM Server: {e}")

print("="*60)