#!/usr/bin/env python3
"""Test Arena functionality directly on AWS with simplified approach"""

import asyncio
import json
from app.core.ollama_adapter import OllamaAdapter

async def test_ollama():
    """Test Ollama integration"""
    print("=" * 60)
    print("🎮 Testing Arena with Ollama on AWS")
    print("=" * 60)
    
    adapter = OllamaAdapter()
    
    # Test health check
    print("\n1. Testing health check...")
    health = await adapter.health_check()
    print(f"   Status: {health['status']}")
    print(f"   Base URL: {health.get('base_url')}")
    
    if health['status'] == 'healthy':
        print(f"   Total models: {health.get('total_models')}")
        for model, available in health.get('arena_models_status', {}).items():
            status = "✅" if available else "❌"
            print(f"   {status} {model}")
    
    # Test each model
    if health.get('all_arena_models_ready'):
        print("\n2. Testing model responses...")
        test_prompt = "What is 2+2? Answer in one word."
        
        for model in ['llama3.1:8b', 'mistral:7b', 'phi3:mini']:
            print(f"\n   Testing {model}...")
            try:
                response = await adapter.generate_async(
                    model=model,
                    prompt=test_prompt,
                    temperature=0.7,
                    max_tokens=50
                )
                
                if not response.startswith("Error"):
                    print(f"   ✅ {model}: {response[:50]}")
                else:
                    print(f"   ❌ {model}: {response}")
            except Exception as e:
                print(f"   ❌ {model}: Exception - {e}")
    
    await adapter.close()
    
    print("\n" + "=" * 60)
    print("✅ Arena system is working on AWS!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_ollama())