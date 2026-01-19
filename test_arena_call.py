import asyncio
import sys
import os
sys.path.insert(0, '.')

# Set up environment
os.environ['FLASK_ENV'] = 'production'

from app.core.arena_manager import ArenaManager, ArenaBattle
from app.core.ollama_adapter import OllamaAdapter

async def test():
    manager = ArenaManager()
    battle = ArenaBattle('test-battle', 'Hello world', session_id='test')
    
    # Set up models
    battle.current_matchup = {
        'model_a': 'mistral:7b',
        'model_b': 'gpt-4o'
    }
    
    print('Testing model responses...')
    
    # Create Ollama adapter
    ollama_adapter = OllamaAdapter()
    
    # Test the get_model_response function inline
    model_name = 'gpt-4o'
    model_info = manager.available_models.get(model_name, {})
    provider = model_info.get('type', 'ollama')
    
    print(f'Model: {model_name}')
    print(f'Provider: {provider}')
    
    if provider == 'openai':
        print('Should use OpenAI path')
        
        # Try the OpenAI call
        from app.core.llm_adapter import LLMAdapter
        adapter = LLMAdapter(backend='openai', model='gpt-4o')
        response = adapter.generate(
            prompt='Say hello',
            max_tokens=800,
            temperature=0.7
        )
        print(f'OpenAI response: {response}')
    else:
        print('Would use Ollama path - THIS IS THE BUG!')

asyncio.run(test())
