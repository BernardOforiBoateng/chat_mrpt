import asyncio
import sys
sys.path.insert(0, '.')

from app.core.arena_manager import ArenaManager

async def test():
    manager = ArenaManager()
    
    # Check available models
    print('Available models:', list(manager.available_models.keys()))
    
    # Check gpt-4o config
    gpt4o_config = manager.available_models.get('gpt-4o')
    print(f'gpt-4o config: {gpt4o_config}')
    
    # Check what provider it would use
    model_name = 'gpt-4o'
    model_info = manager.available_models.get(model_name, {})
    provider = model_info.get('type', 'ollama')
    print(f'Provider for gpt-4o: {provider}')

asyncio.run(test())
