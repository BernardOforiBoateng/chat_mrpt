#!/usr/bin/env python3
"""Test Arena functionality with fixed 3-model setup"""

import asyncio
import aiohttp
import json
from app.core.ollama_adapter import OllamaAdapter

async def test_ollama_health():
    """Test Ollama health check"""
    print("=" * 60)
    print("🏥 Testing Ollama Health Check")
    print("=" * 60)
    
    adapter = OllamaAdapter()
    health = await adapter.health_check()
    
    print(f"Status: {health['status']}")
    print(f"Base URL: {health.get('base_url')}")
    
    if health['status'] == 'healthy':
        print(f"Total models available: {health.get('total_models')}")
        print("\nArena models status:")
        for model, available in health.get('arena_models_status', {}).items():
            status = "✅" if available else "❌"
            print(f"  {status} {model}")
        
        if health.get('all_arena_models_ready'):
            print("\n✅ All arena models are ready!")
        else:
            print(f"\n⚠️ {health.get('recommendation')}")
    else:
        print(f"❌ Error: {health.get('error')}")
        print(f"Recommendation: {health.get('recommendation')}")
    
    await adapter.close()
    return health['status'] == 'healthy' and health.get('all_arena_models_ready', False)

async def test_arena_responses():
    """Test getting responses from all 3 models"""
    print("\n" + "=" * 60)
    print("🎮 Testing Arena Model Responses")
    print("=" * 60)
    
    adapter = OllamaAdapter()
    test_prompt = "What is the capital of France? Answer in one sentence."
    
    models = ['llama3.1:8b', 'mistral:7b', 'phi3:mini']
    responses = {}
    
    for model in models:
        print(f"\n📝 Testing {model}...")
        try:
            response = await adapter.generate_async(
                model=model,
                prompt=test_prompt,
                temperature=0.7,
                max_tokens=100
            )
            
            if response.startswith("Error"):
                print(f"  ❌ {response}")
                responses[model] = None
            else:
                print(f"  ✅ Response: {response[:100]}...")
                responses[model] = response
        except Exception as e:
            print(f"  ❌ Exception: {e}")
            responses[model] = None
    
    await adapter.close()
    
    # Check if all models responded
    successful = sum(1 for r in responses.values() if r is not None)
    print(f"\n📊 Results: {successful}/3 models responded successfully")
    
    if successful == 3:
        # Check if responses are different
        unique_responses = len(set(responses.values()))
        if unique_responses == 3:
            print("✅ All models gave different responses (good for arena!)")
        else:
            print("⚠️ Some models gave similar responses")
    
    return successful == 3

async def test_api_endpoint():
    """Test the Flask API endpoint"""
    print("\n" + "=" * 60)
    print("🌐 Testing API Endpoint")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        try:
            # Test health endpoint
            async with session.get('http://localhost:5000/api/arena/ollama-status') as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ API endpoint working")
                    print(f"   Status: {data.get('status')}")
                    print(f"   Recommendation: {data.get('recommendation')}")
                else:
                    print(f"❌ API returned status {resp.status}")
        except Exception as e:
            print(f"❌ Could not reach API: {e}")
            print("   Make sure Flask app is running: python run.py")

async def main():
    """Run all tests"""
    print("\n🚀 Starting Arena Integration Tests\n")
    
    # Test 1: Health check
    health_ok = await test_ollama_health()
    
    if not health_ok:
        print("\n⚠️ Ollama is not properly configured. Please:")
        print("1. Make sure Ollama is running: ollama serve")
        print("2. Pull required models:")
        print("   ollama pull llama3.1:8b")
        print("   ollama pull mistral:7b")
        print("   ollama pull phi3:mini")
        return
    
    # Test 2: Model responses
    responses_ok = await test_arena_responses()
    
    # Test 3: API endpoint
    await test_api_endpoint()
    
    print("\n" + "=" * 60)
    print("📋 Test Summary")
    print("=" * 60)
    print(f"Health Check: {'✅ Passed' if health_ok else '❌ Failed'}")
    print(f"Model Responses: {'✅ Passed' if responses_ok else '❌ Failed'}")
    print("\nIf all tests pass, the arena system is ready to use!")

if __name__ == "__main__":
    asyncio.run(main())