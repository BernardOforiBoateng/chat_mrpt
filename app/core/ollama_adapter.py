"""
Ollama Adapter for Arena Mode
Provides async interface to Ollama models for the Arena battle system
"""

import aiohttp
import asyncio
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class OllamaAdapter:
    """
    Adapter for Ollama models in Arena mode.
    Maps Arena model names to available Ollama models.
    """
    
    def __init__(self, base_url: str = None):
        # Get base URL from environment or use default
        import os
        if base_url:
            self.base_url = base_url
        else:
            # Check for AWS Ollama instance
            aws_ollama_host = os.environ.get('AWS_OLLAMA_HOST')
            if aws_ollama_host:
                self.base_url = f"http://{aws_ollama_host}:11434"
            else:
                # Fall back to config or localhost
                ollama_host = os.environ.get('OLLAMA_HOST', 'localhost')
                ollama_port = os.environ.get('OLLAMA_PORT', '11434')
                self.base_url = f"http://{ollama_host}:{ollama_port}"
        
        logger.info(f"Ollama adapter initialized with base URL: {self.base_url}")
        
        # Direct model mapping - only the 3 Ollama models we actually have
        self.model_mapping = {
            # Primary 3 models (exact Ollama names)
            'llama3.1:8b': 'llama3.1:8b',      # Meta's Llama 3.1
            'mistral:7b': 'mistral:7b',        # Mistral 7B
            'phi3:mini': 'phi3:mini',          # Microsoft Phi-3
        }
        
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _ensure_session(self):
        """Ensure we have an active session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def check_model_available(self, model: str) -> bool:
        """Check if a model is available in Ollama"""
        try:
            session = await self._ensure_session()
            async with session.get(
                f"{self.base_url}/api/tags",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    available_models = [m['name'] for m in data.get('models', [])]
                    actual_model = self.model_mapping.get(model, model)
                    return actual_model in available_models
                return False
        except Exception as e:
            logger.error(f"Failed to check model availability: {e}")
            return False
    
    async def generate_async(self, model: str, prompt: str, 
                            temperature: float = 0.7,
                            max_tokens: int = 2048) -> str:
        """
        Generate response from Ollama model asynchronously.
        
        Args:
            model: Arena model name
            prompt: User prompt
            temperature: Generation temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response text
        """
        actual_model = self.model_mapping.get(model, model)
        
        logger.info(f"Generating with Ollama model: {actual_model} (mapped from {model})")
        
        session = await self._ensure_session()
        
        payload = {
            "model": actual_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            async with session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)  # Increased timeout for model loading
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    response_text = data.get('response', '')
                    logger.info(f"Ollama {actual_model} generated {len(response_text)} chars")
                    return response_text
                else:
                    error_text = await response.text()
                    logger.error(f"Ollama error {response.status}: {error_text}")
                    return f"Error: Model {actual_model} returned status {response.status}"
                    
        except asyncio.TimeoutError:
            logger.error(f"Timeout generating with {actual_model}")
            return "Error: Request timed out. The model may be loading, please try again."
        except Exception as e:
            logger.error(f"Ollama generation failed for {actual_model}: {e}")
            return f"Error generating response: {str(e)}"
    
    async def generate_streaming(self, model: str, prompt: str,
                                temperature: float = 0.7,
                                max_tokens: int = 2048):
        """
        Generate streaming response from Ollama model.
        
        Yields:
            Response chunks as they're generated
        """
        actual_model = self.model_mapping.get(model, model)
        
        session = await self._ensure_session()
        
        payload = {
            "model": actual_model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            async with session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                if response.status == 200:
                    async for line in response.content:
                        if line:
                            try:
                                data = json.loads(line)
                                if 'response' in data:
                                    yield data['response']
                                if data.get('done', False):
                                    break
                            except json.JSONDecodeError:
                                continue
                else:
                    yield f"Error: Status {response.status}"
                    
        except Exception as e:
            logger.error(f"Streaming failed for {actual_model}: {e}")
            yield f"Error: {str(e)}"
    
    async def list_available_models(self) -> Dict[str, Any]:
        """List all available Ollama models with their Arena mappings"""
        try:
            session = await self._ensure_session()
            async with session.get(
                f"{self.base_url}/api/tags",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    ollama_models = [m['name'] for m in data.get('models', [])]
                    
                    # Check which Arena models are available
                    arena_models = {}
                    for arena_name, ollama_name in self.model_mapping.items():
                        if ollama_name in ollama_models:
                            arena_models[arena_name] = {
                                'available': True,
                                'ollama_model': ollama_name
                            }
                        else:
                            arena_models[arena_name] = {
                                'available': False,
                                'ollama_model': ollama_name
                            }
                    
                    return {
                        'ollama_models': ollama_models,
                        'arena_models': arena_models
                    }
                return {'error': f'Status {response.status}'}
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return {'error': str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check Ollama health and available models.
        
        Returns:
            Dictionary with health status and available models
        """
        try:
            session = await self._ensure_session()
            
            # Check if Ollama is reachable
            async with session.get(
                f"{self.base_url}/api/tags",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    available_models = [m['name'] for m in data.get('models', [])]
                    
                    # Check which of our 3 models are available
                    our_models_status = {}
                    for model in self.model_mapping.keys():
                        our_models_status[model] = model in available_models
                    
                    return {
                        'status': 'healthy',
                        'base_url': self.base_url,
                        'total_models': len(available_models),
                        'available_models': available_models,
                        'arena_models_status': our_models_status,
                        'all_arena_models_ready': all(our_models_status.values())
                    }
                else:
                    return {
                        'status': 'unhealthy',
                        'error': f'Ollama returned status {response.status}',
                        'base_url': self.base_url
                    }
        except asyncio.TimeoutError:
            return {
                'status': 'unhealthy',
                'error': 'Connection timeout - Ollama may not be running',
                'base_url': self.base_url
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'base_url': self.base_url
            }
    
    async def close(self):
        """Close the HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    def __del__(self):
        """Cleanup on deletion"""
        if hasattr(self, '_session') and self._session:
            try:
                asyncio.create_task(self._session.close())
            except:
                pass