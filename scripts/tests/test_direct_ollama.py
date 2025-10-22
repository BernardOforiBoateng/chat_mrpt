#!/usr/bin/env python3
"""Direct test of Ollama from production"""

import requests
import json

# Test directly against production server's view of Ollama
prod_url = "https://d225ar6c86586s.cloudfront.net"

# First test if Ollama is accessible
print("Testing direct Ollama connection...")
ollama_test = requests.post(
    "http://172.31.45.157:11434/v1/chat/completions",
    json={
        "model": "tinyllama:latest",
        "messages": [{"role": "user", "content": "Say hello"}],
        "max_tokens": 10
    },
    timeout=5
)
print(f"Direct Ollama: {ollama_test.status_code}")
if ollama_test.status_code == 200:
    print(f"Response: {ollama_test.json()['choices'][0]['message']['content']}")

# Now test via production with debug info
print("\n=== Testing via Production ===")
response = requests.post(
    f"{prod_url}/send_message",
    json={
        "message": "What is malaria?",
        "use_arena": True
    },
    timeout=30
)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Response A: {data.get('response_a', 'N/A')[:100]}")
    print(f"Response B: {data.get('response_b', 'N/A')[:100]}")
    print(f"Model A: {data.get('model_a', 'N/A')}")
    print(f"Model B: {data.get('model_b', 'N/A')}")