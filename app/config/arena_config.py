"""
Arena Configuration Settings
Centralized configuration for Arena mode performance optimization
"""

import os

# GPU Instance Configuration (DISABLED - Instance stopped to save costs)
GPU_INSTANCE_HOST = os.environ.get('AWS_OLLAMA_HOST', '172.31.45.157')
USE_GPU_INSTANCE = False  # DISABLED: GPU instance stopped (was costing ~$200-400/month)

# Model Configuration - Order matters for performance!
ARENA_MODELS = {
    'mistral:7b': {
        'display_name': 'Mistral 7B (A)',
        'type': 'local',
        'provider': 'ollama',
        'typical_latency': 3000,  # ~3s
        'label': 'A'
    },
    'qwen3:8b': {  # FIXED: Correct model name
        'display_name': 'Qwen3 8B (B)',
        'type': 'local',
        'provider': 'ollama',
        'typical_latency': 5000,  # ~5s
        'label': 'B'
    },
    'llama3.1:8b': {
        'display_name': 'Llama 3.1 8B (C)',
        'type': 'local',
        'provider': 'ollama',
        'typical_latency': 8000,  # ~8s
        'label': 'C'
    },
    'gpt-4o': {
        'display_name': 'GPT-4o (D)',
        'type': 'openai',
        'provider': 'openai',
        'typical_latency': 2000,  # ~2s but via API
        'label': 'D',
        'is_final_challenger': True  # Always the final model in tournament
    }
}

# Performance Settings
PARALLEL_LOADING = True  # Load all models in parallel
CACHE_RESPONSES = True   # Cache all responses for instant switching
MAX_RESPONSE_LENGTH = 800  # Max tokens per response
RESPONSE_TIMEOUT = 15  # Timeout per model in seconds
OPENAI_TIMEOUT = 30    # Longer timeout for OpenAI

# Tournament Structure (DISABLED - Arena mode turned off)
DEFAULT_NUM_MODELS = 0  # DISABLED: Arena mode turned off to save GPU costs
INCLUDE_OPENAI_FINAL = False  # DISABLED: Arena mode turned off

def get_ollama_url():
    """Get the Ollama URL based on configuration"""
    if USE_GPU_INSTANCE and GPU_INSTANCE_HOST:
        return f"http://{GPU_INSTANCE_HOST}:11434"
    else:
        host = os.environ.get('OLLAMA_HOST', 'localhost')
        port = os.environ.get('OLLAMA_PORT', '11434')
        return f"http://{host}:{port}"

def get_optimized_model_order(include_openai=False):
    """
    Get models in optimized order for loading.
    Fastest models first for better perceived performance.
    """
    order = ['mistral:7b', 'qwen3:8b', 'llama3.1:8b']  # FIXED: qwen3:8b
    if include_openai:
        order.append('gpt-4o')  # Model D is always OpenAI
    return order

def get_tournament_structure():
    """
    Get the tournament structure with proper labeling.
    Returns model configuration with A, B, C, D labels.
    """
    models = list(ARENA_MODELS.keys())[:3]  # First 3 are local

    if INCLUDE_OPENAI_FINAL:
        models.append('gpt-4o')  # Model D

    return {
        'models': models,
        'labels': ['A', 'B', 'C', 'D'][:len(models)],
        'total_rounds': len(models) - 1  # Number of comparison rounds
    }