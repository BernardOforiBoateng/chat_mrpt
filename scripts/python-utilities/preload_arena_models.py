#!/usr/bin/env python3
"""
Arena Model Preloader Script
Loads all 5 Arena models into GPU memory for optimal performance
"""

import asyncio
import aiohttp
import subprocess
import time
import sys
import json
from typing import Dict, List, Tuple

# Arena models configuration
ARENA_MODELS = {
    'llama3.1:8b': {'size': '4.9GB', 'priority': 1},
    'mistral:7b': {'size': '4.4GB', 'priority': 2},
    'phi3:mini': {'size': '2.2GB', 'priority': 5},
    'gemma2:9b': {'size': '5.4GB', 'priority': 3},
    'qwen2.5:7b': {'size': '4.7GB', 'priority': 4}
}

OLLAMA_URL = "http://localhost:11434"

async def check_gpu_memory() -> Tuple[int, int]:
    """Check GPU memory usage using nvidia-smi"""
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,nounits,noheader'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            used, total = map(int, result.stdout.strip().split(','))
            return used, total
    except Exception as e:
        print(f"Error checking GPU memory: {e}")
    return 0, 0

async def test_model(session: aiohttp.ClientSession, model_name: str) -> bool:
    """Test a model by sending a simple prompt"""
    try:
        print(f"  Testing {model_name}...", end='', flush=True)

        payload = {
            "model": model_name,
            "prompt": "Hello",
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 10,
                "num_gpu": 999  # Use all GPU layers
            }
        }

        async with session.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=90)
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f" ✅ Response: {data['response'][:30]}...")
                return True
            else:
                print(f" ❌ Status: {response.status}")
                return False

    except asyncio.TimeoutError:
        print(f" ❌ Timeout")
        return False
    except Exception as e:
        print(f" ❌ Error: {str(e)}")
        return False

async def load_model(session: aiohttp.ClientSession, model_name: str) -> bool:
    """Load a model into GPU memory"""
    print(f"\n📥 Loading {model_name} ({ARENA_MODELS[model_name]['size']})...")

    # Check GPU memory before loading
    used_before, total = await check_gpu_memory()
    print(f"  GPU Memory before: {used_before}MB / {total}MB")

    # Test the model (this will load it)
    success = await test_model(session, model_name)

    if success:
        # Check GPU memory after loading
        used_after, _ = await check_gpu_memory()
        increase = used_after - used_before
        print(f"  GPU Memory after: {used_after}MB / {total}MB (+{increase}MB)")

    return success

async def keep_models_warm(session: aiohttp.ClientSession, models: List[str]):
    """Keep models warm by sending periodic requests"""
    print("\n🔥 Keeping models warm...")

    tasks = []
    for model in models:
        payload = {
            "model": model,
            "prompt": "1+1=",
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 5,
                "num_gpu": 999
            }
        }

        task = session.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        tasks.append(task)

    # Execute all warmup requests in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)

    success_count = sum(1 for r in results if not isinstance(r, Exception) and r.status == 200)
    print(f"  Warmed up {success_count}/{len(models)} models")

    # Close responses
    for result in results:
        if not isinstance(result, Exception):
            await result.read()

async def main():
    """Main preloader function"""
    print("=" * 60)
    print("Arena Model Preloader - GPU Edition")
    print("=" * 60)

    # Check initial GPU state
    used, total = await check_gpu_memory()
    print(f"\n🎮 GPU Status: {used}MB / {total}MB used")
    available = total - used
    print(f"   Available: {available}MB")

    # Calculate total model size
    total_size = 21.6  # GB
    print(f"\n📊 Total model size: {total_size}GB")

    if available < total_size * 1024:
        print(f"⚠️  Warning: May not fit all models in GPU memory")
    else:
        print(f"✅ Sufficient GPU memory for all models")

    # Create HTTP session
    connector = aiohttp.TCPConnector(limit=10)
    async with aiohttp.ClientSession(connector=connector) as session:

        # Load models in priority order
        sorted_models = sorted(
            ARENA_MODELS.items(),
            key=lambda x: x[1]['priority']
        )

        loaded_models = []
        failed_models = []

        print("\n" + "=" * 60)
        print("Loading Models")
        print("=" * 60)

        for model_name, _ in sorted_models:
            success = await load_model(session, model_name)
            if success:
                loaded_models.append(model_name)
            else:
                failed_models.append(model_name)

            # Small delay between loads
            await asyncio.sleep(2)

        # Final GPU memory check
        print("\n" + "=" * 60)
        print("Final Status")
        print("=" * 60)

        final_used, final_total = await check_gpu_memory()
        print(f"\n🎮 GPU Memory Usage: {final_used}MB / {final_total}MB ({(final_used/final_total*100):.1f}%)")

        print(f"\n✅ Successfully loaded: {len(loaded_models)}/{len(ARENA_MODELS)}")
        for model in loaded_models:
            print(f"   • {model}")

        if failed_models:
            print(f"\n❌ Failed to load: {len(failed_models)}")
            for model in failed_models:
                print(f"   • {model}")

        if loaded_models:
            print("\n🔄 Starting warmup cycle...")
            # Keep models warm with periodic requests
            for i in range(3):
                await keep_models_warm(session, loaded_models)
                if i < 2:
                    print(f"   Waiting 10 seconds before next warmup...")
                    await asyncio.sleep(10)

        print("\n" + "=" * 60)
        print("Preloading Complete!")
        print("=" * 60)

        if len(loaded_models) == len(ARENA_MODELS):
            print("✅ All Arena models are loaded and ready in GPU memory!")
            return 0
        else:
            print(f"⚠️  Only {len(loaded_models)}/{len(ARENA_MODELS)} models loaded successfully")
            return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Preloading interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        sys.exit(1)