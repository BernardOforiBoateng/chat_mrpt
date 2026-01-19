#!/usr/bin/env python3
"""
Test script for progressive arena battle system.
Tests the 3-model progressive comparison workflow.
"""

import asyncio
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.arena_manager import ArenaManager, ProgressiveBattleSession
from app.core.ollama_adapter import OllamaAdapter


async def test_progressive_battle():
    """Test the progressive battle workflow with 3 models."""
    
    print("=" * 60)
    print("PROGRESSIVE ARENA BATTLE TEST")
    print("=" * 60)
    
    # Initialize arena manager
    arena_manager = ArenaManager()
    print(f"\n✅ Arena Manager initialized with {len(arena_manager.available_models)} models")
    print(f"Models: {list(arena_manager.available_models.keys())}")
    
    # Test query
    test_query = "What is the capital of France and why is it significant?"
    print(f"\n📝 Test Query: {test_query}")
    
    # Start progressive battle
    print("\n🚀 Starting progressive battle...")
    battle_info = await arena_manager.start_progressive_battle(
        user_message=test_query,
        num_models=3
    )
    
    battle_id = battle_info['battle_id']
    print(f"Battle ID: {battle_id}")
    print(f"Total models to compare: {battle_info['total_models']}")
    
    # Get all model responses
    print("\n🤖 Fetching responses from all models...")
    print("(This may take a minute as models generate responses...)")
    
    try:
        responses = await arena_manager.get_all_model_responses(battle_id)
        
        if 'error' in responses:
            print(f"❌ Error: {responses['error']}")
            return
        
        print(f"\n✅ All responses fetched!")
        print(f"Round {responses['current_round']}:")
        print(f"  Model A: {responses['model_a']}")
        print(f"  Response A: {responses['response_a'][:100]}...")
        print(f"  Latency A: {responses['latency_a']:.2f}ms")
        print(f"\n  Model B: {responses['model_b']}")
        print(f"  Response B: {responses['response_b'][:100]}...")
        print(f"  Latency B: {responses['latency_b']:.2f}ms")
        
        # Simulate user choices
        print("\n" + "=" * 60)
        print("SIMULATING USER CHOICES")
        print("=" * 60)
        
        # Round 1: Choose left (Model A wins)
        print(f"\nRound 1: Choosing LEFT ({responses['model_a']})")
        result = arena_manager.submit_progressive_choice(battle_id, 'left')
        
        if result['status'] == 'continue':
            print(f"✅ {result.get('eliminated_model')} eliminated")
            print(f"Next matchup: {result['model_a']} vs {result['model_b']}")
            print(f"Remaining comparisons: {result['remaining_comparisons']}")
            
            # Round 2: Choose right (Model B wins)
            print(f"\nRound 2: Choosing RIGHT ({result['model_b']})")
            result = arena_manager.submit_progressive_choice(battle_id, 'right')
            
            if result['status'] == 'completed':
                print("\n🏆 BATTLE COMPLETED!")
                print(f"Final Ranking:")
                for i, model in enumerate(result['final_ranking'], 1):
                    print(f"  {i}. {model}")
                print(f"\nWinner: {result['winner']}")
                print(f"Total rounds: {result['total_rounds']}")
            else:
                print(f"Status: {result['status']}")
        
        print("\n✅ Progressive battle test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()


async def test_ollama_connection():
    """Test Ollama adapter connection."""
    print("\n" + "=" * 60)
    print("TESTING OLLAMA CONNECTION")
    print("=" * 60)
    
    adapter = OllamaAdapter()
    print(f"Base URL: {adapter.base_url}")
    
    # List available models
    models_info = await adapter.list_available_models()
    
    if 'error' in models_info:
        print(f"❌ Error connecting to Ollama: {models_info['error']}")
        print("\n⚠️  Make sure:")
        print("1. Ollama is running on the AWS instance")
        print("2. AWS_OLLAMA_HOST environment variable is set to the AWS instance IP")
        print("3. The required models are pulled in Ollama")
        return False
    
    print(f"\n✅ Connected to Ollama!")
    print(f"Available Ollama models: {models_info['ollama_models']}")
    print("\nArena model mappings:")
    for arena_name, info in models_info['arena_models'].items():
        status = "✅" if info['available'] else "❌"
        print(f"  {status} {arena_name} -> {info['ollama_model']}")
    
    # Close the adapter
    await adapter.close()
    return True


async def main():
    """Main test function."""
    # First test Ollama connection
    if await test_ollama_connection():
        # Then test progressive battle
        await test_progressive_battle()
    else:
        print("\n⚠️  Skipping progressive battle test due to Ollama connection issues")


if __name__ == "__main__":
    # Run the test
    asyncio.run(main())