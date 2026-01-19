#!/usr/bin/env python3
"""
Simple Ollama connectivity test for AWS.
Tests basic connection and model availability.
"""

import asyncio
import aiohttp
import json
import os

async def test_ollama_connection():
    """Test basic Ollama connectivity."""
    
    # Get Ollama host from environment or use localhost
    ollama_host = os.environ.get('OLLAMA_HOST', 'localhost')
    ollama_port = os.environ.get('OLLAMA_PORT', '11434')
    base_url = f"http://{ollama_host}:{ollama_port}"
    
    print("=" * 60)
    print("OLLAMA CONNECTIVITY TEST")
    print("=" * 60)
    print(f"Testing connection to: {base_url}")
    print()
    
    async with aiohttp.ClientSession() as session:
        try:
            # Test API endpoint
            async with session.get(
                f"{base_url}/api/tags",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get('models', [])
                    
                    print(f"✅ Connected to Ollama!")
                    print(f"Found {len(models)} models:")
                    print()
                    
                    for model in models:
                        name = model.get('name', 'unknown')
                        size = model.get('size', 0) / (1024**3)  # Convert to GB
                        print(f"  • {name} ({size:.1f} GB)")
                    
                    # Test the 3 required models
                    print()
                    print("Testing required models for progressive arena:")
                    print("-" * 40)
                    
                    required_models = ['llama3.1:8b', 'mistral:7b', 'phi3:mini']
                    available_model_names = [m.get('name') for m in models]
                    
                    all_available = True
                    for model in required_models:
                        if model in available_model_names:
                            print(f"  ✅ {model} - Available")
                        else:
                            print(f"  ❌ {model} - Not found")
                            all_available = False
                    
                    print()
                    if all_available:
                        print("✅ All required models are available!")
                        print("The progressive arena system should work correctly.")
                    else:
                        print("⚠️  Some required models are missing.")
                        print("Run './setup_ollama_models.sh' to install them.")
                    
                    # Test a simple generation
                    print()
                    print("Testing model generation with phi3:mini...")
                    print("-" * 40)
                    
                    payload = {
                        "model": "phi3:mini",
                        "prompt": "Hello! Please respond with a single sentence.",
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "num_predict": 50
                        }
                    }
                    
                    async with session.post(
                        f"{base_url}/api/generate",
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as gen_response:
                        if gen_response.status == 200:
                            gen_data = await gen_response.json()
                            response_text = gen_data.get('response', '')
                            print(f"Response: {response_text}")
                            print()
                            print("✅ Model generation successful!")
                        else:
                            print(f"❌ Generation failed with status {gen_response.status}")
                    
                else:
                    print(f"❌ Failed to connect: HTTP {response.status}")
                    
        except asyncio.TimeoutError:
            print("❌ Connection timed out")
            print("Make sure Ollama is running and accessible")
        except Exception as e:
            print(f"❌ Error: {e}")
            print()
            print("Troubleshooting:")
            print("1. Check if Ollama is running: 'systemctl status ollama' or 'ollama serve'")
            print("2. Check firewall/security groups for port 11434")
            print("3. Verify OLLAMA_HOST environment variable")

if __name__ == "__main__":
    asyncio.run(test_ollama_connection())