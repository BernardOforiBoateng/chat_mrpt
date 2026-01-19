#!/usr/bin/env python3
"""
Verification script for Arena mode with 5 models
Tests that all required Ollama models are available and accessible
"""

import asyncio
import aiohttp
import json
import sys
import os

# Arena model mapping
ARENA_MODELS = {
    'llama3.1:8b': 'llama3.1:8b',
    'mistral:7b': 'mistral:7b',
    'phi3:mini': 'phi3:mini',
    'gemma2:9b': 'gemma2:9b',
    'qwen2.5:7b': 'qwen2.5:7b'
}

async def check_ollama_health(base_url='http://172.31.45.157:11434'):
    """Check if Ollama is running and accessible"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/api/tags", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return True, data.get('models', [])
                return False, []
    except Exception as e:
        return False, str(e)

async def verify_arena_models():
    """Verify all 5 Arena models are available"""
    print("=" * 60)
    print("Arena Mode 5-Model Verification")
    print("=" * 60)
    
    # Check Ollama health
    print("\n1. Checking Ollama service...")
    healthy, models_or_error = await check_ollama_health()
    
    if not healthy:
        print(f"   ❌ Ollama is not accessible: {models_or_error}")
        return False
    
    print(f"   ✅ Ollama is running")
    
    # Extract model names
    available_models = [m['name'] for m in models_or_error] if isinstance(models_or_error, list) else []
    print(f"   📊 Total models available: {len(available_models)}")
    
    # Check each Arena model
    print("\n2. Verifying Arena models:")
    all_ready = True
    ready_count = 0
    
    for arena_name, ollama_name in ARENA_MODELS.items():
        if ollama_name in available_models:
            print(f"   ✅ {arena_name} -> {ollama_name} [READY]")
            ready_count += 1
        else:
            print(f"   ❌ {arena_name} -> {ollama_name} [MISSING]")
            all_ready = False
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"Arena Models Ready: {ready_count}/5")
    
    if all_ready:
        print("✅ All 5 Arena models are installed and ready!")
        print("\nArena mode is fully operational with:")
        for i, model in enumerate(ARENA_MODELS.keys(), 1):
            print(f"  {i}. {model}")
    else:
        print("⚠️  Some models are missing. Please install:")
        for arena_name, ollama_name in ARENA_MODELS.items():
            if ollama_name not in available_models:
                print(f"  - ollama pull {ollama_name}")
    
    return all_ready

async def test_model_response(model_name, prompt="Hello, can you introduce yourself briefly?"):
    """Test a specific model's response"""
    base_url = 'http://172.31.45.157:11434'
    
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": ARENA_MODELS.get(model_name, model_name),
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 100
                }
            }
            
            async with session.post(
                f"{base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    response = data.get('response', '')
                    return True, response[:150] + "..." if len(response) > 150 else response
                else:
                    return False, f"Error: Status {resp.status}"
    except Exception as e:
        return False, str(e)

async def main():
    """Main verification routine"""
    # Verify models are installed
    models_ready = await verify_arena_models()
    
    if models_ready and len(sys.argv) > 1 and sys.argv[1] == '--test-responses':
        print("\n" + "=" * 60)
        print("TESTING MODEL RESPONSES")
        print("=" * 60)
        
        for model in ARENA_MODELS.keys():
            print(f"\nTesting {model}...")
            success, response = await test_model_response(model)
            if success:
                print(f"  ✅ Response: {response}")
            else:
                print(f"  ❌ Failed: {response}")
    
    return 0 if models_ready else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)