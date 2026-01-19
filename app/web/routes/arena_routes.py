"""
Arena Routes for LLM Model Comparison

Provides API endpoints for the Arena battle system where users can compare
different LLM models side-by-side in a blind testing format.
"""

import asyncio
import time
import logging
import json
from flask import Blueprint, request, jsonify, session, Response, stream_with_context
from typing import Dict, Any
import uuid

# Arena manager removed - migrating to AWS
# from app.core.arena_manager import ArenaManager
from app.core.llm_adapter import LLMAdapter
from app.core.ollama_adapter import OllamaAdapter
from app.interaction.core import InteractionCore

logger = logging.getLogger(__name__)

# Initialize interaction logger for capturing all arena interactions
interaction_core = InteractionCore()

# Create blueprint
arena_bp = Blueprint('arena', __name__, url_prefix='/api/arena')

# Arena manager instance (initialized in init_arena_system)
arena_manager = None


def init_arena_system(app):
    """Initialize arena system with app context (3 locals + optional OpenAI final)."""
    global arena_manager
    try:
        from app.core.arena_manager import ArenaManager
        # Define 3 GPU locals + OpenAI final (providers matter for routing)
        models_config = {
            'mistral:7b': {
                'type': 'ollama',
                'display_name': 'Mistral 7B (A)',
                'label': 'A'
            },
            'llama3.1:8b': {
                'type': 'ollama',
                'display_name': 'Llama 3.1 8B (B)',
                'label': 'B'
            },
            'qwen3:8b': {  # FIXED: Correct model name is qwen3:8b
                'type': 'ollama',
                'display_name': 'Qwen3 8B (C)',
                'label': 'C'
            },
            'gpt-4o': {
                'type': 'openai',
                'display_name': 'GPT-4o (D)',
                'label': 'D',
                'is_final_challenger': True  # Model D is ALWAYS OpenAI
            }
        }
        arena_manager = ArenaManager(models_config)
        logger.info("✅ Arena system initialized (A,B,C: local models | D: OpenAI final challenger)")
    except Exception as e:
        logger.error(f"Failed to initialize Arena system: {e}")
        arena_manager = None


@arena_bp.route('/status', methods=['GET'])
def arena_status():
    """Check if arena mode is available and get current configuration."""
    try:
        if not arena_manager:
            return jsonify({
                'available': False,
                'message': 'Arena system not initialized'
            }), 503
        
        stats = arena_manager.get_statistics()
        
        return jsonify({
            'available': True,
            'active_models': stats['active_models'],
            'total_battles': stats['total_battles'],
            'completed_battles': stats['completed_battles'],
            'leaderboard': stats['leaderboard'][:3]  # Top 3 models
        })
    
    except Exception as e:
        logger.error(f"Error checking arena status: {e}")
        return jsonify({
            'available': False,
            'error': str(e)
        }), 500


@arena_bp.route('/ollama-status', methods=['GET'])
def ollama_status():
    """Check Ollama connectivity and model availability."""
    try:
        from app.core.ollama_adapter import OllamaAdapter
        
        # Create adapter and check health
        ollama_adapter = OllamaAdapter()
        
        # Run async health check
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            health_info = loop.run_until_complete(ollama_adapter.health_check())
        finally:
            loop.close()
        
        # Add recommendation based on health status
        if health_info['status'] == 'healthy':
            if health_info.get('all_arena_models_ready'):
                health_info['recommendation'] = 'All models ready for Arena mode'
            else:
                missing_models = [
                    model for model, available in health_info.get('arena_models_status', {}).items()
                    if not available
                ]
                health_info['recommendation'] = f'Missing models: {", ".join(missing_models)}. Run: ' + \
                    ' && '.join([f'ollama pull {model}' for model in missing_models])
        else:
            health_info['recommendation'] = 'Ollama is not accessible. Check if Ollama service is running.'
        
        return jsonify(health_info)
    
    except Exception as e:
        logger.error(f"Error checking Ollama status: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'recommendation': 'Failed to check Ollama status'
        }), 500


@arena_bp.route('/start_battle', methods=['POST'])
def start_battle():
    """
    Start a new arena battle session.

    Request body:
    {
        "message": "User's query",
        "session_id": "optional-session-id"
    }

    Response:
    {
        "battle_id": "uuid",
        "status": "ready",
        "message": "Battle session created"
    }
    """
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()

        if not user_message:
            return jsonify({
                'error': 'Message is required'
            }), 400

        # 🎯 LOG ARENA USER MESSAGE - CRITICAL FOR COMPLETE INTERACTION CAPTURE
        session_id = data.get('session_id') or session.get('session_id', 'unknown')
        interaction_core.log_message(
            session_id=session_id,
            sender='user',
            content=user_message,
            intent='arena_query',
            entities={
                'message_length': len(user_message),
                'endpoint': '/api/arena/start_battle',
                'workflow': 'arena'
            }
        )
        logger.info(f"✅ Logged arena user message for session {session_id}")
        
        # Check if this should use arena mode
        session_context = {
            'data_loaded': session.get('data_loaded', False),
            'csv_loaded': session.get('csv_loaded', False),
            'shapefile_loaded': session.get('shapefile_loaded', False),
            'tpr_workflow_active': session.get('tpr_workflow_active', False),
            'current_tab': data.get('current_tab', 'main')
        }
        
        # Arena is always available for comparison
        # Intent routing is now handled by Mistral LLM in analysis_routes.py
        
        # Create progressive battle session for tournament-style Arena
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Use start_progressive_battle to create a ProgressiveBattleSession
            # Tournament structure: Models A, B, C (local) compete, winner faces Model D (OpenAI)
            battle_info = loop.run_until_complete(
                arena_manager.start_progressive_battle(
                    user_message,
                    num_models=4,  # 3 local models + Model D (OpenAI/gpt-4o)
                    session_id=data.get('session_id')
                )
            )

            # Pre-generate ALL model responses for smooth UX
            logger.info(f"Pre-generating all responses for battle {battle_info['battle_id']}")
            all_responses = loop.run_until_complete(
                arena_manager.get_all_model_responses(battle_info['battle_id'])
            )

            # Add initial responses to battle_info
            if 'error' not in all_responses:
                # Get the battle to check cached responses
                battle = arena_manager.storage.get_progressive_battle(battle_info['battle_id'])
                if battle:
                    logger.info(f"Cached responses: {list(battle.all_responses.keys())}")
                    logger.info(f"Response lengths: {[(m, len(r)) for m, r in battle.all_responses.items()]}")

                battle_info.update({
                    'response_a': all_responses.get('response_a', ''),
                    'response_b': all_responses.get('response_b', ''),
                    'model_a': all_responses.get('model_a', ''),
                    'model_b': all_responses.get('model_b', ''),
                    'arena_mode': True,
                    'responses_ready': True
                })
                logger.info(f"All responses pre-generated for battle {battle_info['battle_id']}")
                logger.info(f"Initial response_a length: {len(battle_info.get('response_a', ''))}")
                logger.info(f"Initial response_b length: {len(battle_info.get('response_b', ''))}")
            else:
                logger.error(f"Failed to pre-generate responses: {all_responses.get('error')}")
        finally:
            loop.close()
        
        # Store battle ID in session
        session['current_battle_id'] = battle_info['battle_id']
        
        return jsonify(battle_info)
    
    except Exception as e:
        logger.error(f"Error starting battle: {e}")
        return jsonify({
            'error': 'Failed to start battle',
            'details': str(e)
        }), 500


@arena_bp.route('/get_responses', methods=['POST'])
def get_battle_responses():
    """
    Get responses from both models for the battle.
    
    This endpoint triggers the actual LLM calls and returns both responses.
    
    Request body:
    {
        "battle_id": "uuid",
        "message": "User's query"
    }
    
    Response:
    {
        "response_a": "Model A's response",
        "response_b": "Model B's response",
        "latency_a": 1234,
        "latency_b": 1456,
        "ready": true
    }
    """
    try:
        data = request.get_json()
        battle_id = data.get('battle_id')
        user_message = data.get('message')
        
        if not battle_id or not user_message:
            return jsonify({
                'error': 'battle_id and message are required'
            }), 400
        
        # Get battle session (try progressive first, then regular)
        battle = None
        if hasattr(arena_manager.storage, 'get_progressive_battle'):
            battle = arena_manager.storage.get_progressive_battle(battle_id)
        
        if not battle:
            battle = arena_manager.get_battle(battle_id)
        
        if not battle:
            return jsonify({
                'error': 'Battle session not found'
            }), 404
        
        # For ProgressiveBattleSession, get current models
        if hasattr(battle, 'current_pair'):
            if battle.current_pair:
                if isinstance(battle.current_pair[0], int):
                    # Indices
                    model_a_idx, model_b_idx = battle.current_pair
                    battle.model_a = battle.all_models[model_a_idx]
                    battle.model_b = battle.all_models[model_b_idx]
                else:
                    # Model names directly
                    battle.model_a, battle.model_b = battle.current_pair
        
        # Get responses from both models in parallel
        responses = {}
        latencies = {}
        
        async def get_model_response(model_name: str, position: str):
            """Get response from a specific model."""
            start_time = time.time()
            
            try:
                # Provider-aware selection
                model_info = arena_manager.available_models.get(model_name, {})
                provider = model_info.get('type', 'ollama')

                if provider == 'openai':
                    # Use LLMAdapter in executor to avoid blocking
                    from app.core.llm_adapter import LLMAdapter
                    loop = asyncio.get_running_loop()
                    def _call_openai():
                        adapter = LLMAdapter(backend='openai', model=model_name)
                        return adapter.generate(prompt=user_message, max_tokens=800, temperature=0.6)
                    response = await loop.run_in_executor(None, _call_openai)
                else:
                    # Use Ollama for local models
                    ollama_adapter = OllamaAdapter()
                    response = await ollama_adapter.generate_async(model_name, user_message)
                
                latency = (time.time() - start_time) * 1000  # ms
                
                # Submit to arena manager
                await arena_manager.submit_response(
                    battle_id, position, response, latency
                )
                
                responses[f'response_{position}'] = response
                latencies[f'latency_{position}'] = latency
                
            except Exception as e:
                logger.error(f"Error getting response from {model_name}: {e}")
                responses[f'response_{position}'] = f"Error: {str(e)}"
                latencies[f'latency_{position}'] = 0
        
        # Run both model queries in parallel
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            tasks = [
                get_model_response(battle.model_a, 'a'),
                get_model_response(battle.model_b, 'b')
            ]
            loop.run_until_complete(asyncio.gather(*tasks))
        finally:
            loop.close()
        
        return jsonify({
            'battle_id': battle_id,
            'response_a': responses.get('response_a', ''),
            'response_b': responses.get('response_b', ''),
            'latency_a': latencies.get('latency_a', 0),
            'latency_b': latencies.get('latency_b', 0),
            'ready': True
        })
    
    except Exception as e:
        logger.error(f"Error getting battle responses: {e}")
        return jsonify({
            'error': 'Failed to get responses',
            'details': str(e)
        }), 500


@arena_bp.route('/get_responses_streaming', methods=['POST'])
def get_battle_responses_streaming():
    """
    Stream responses from both models simultaneously.
    
    Uses Server-Sent Events to stream both model responses in real-time.
    """
    data = request.get_json()
    battle_id = data.get('battle_id')
    user_message = data.get('message')  # optional

    if not battle_id:
        return jsonify({'error': 'battle_id is required'}), 400

    def generate():
        """Generate SSE stream for current matchup (progressive battle)."""
        # Get battle (progressive preferred)
        battle = None
        if hasattr(arena_manager.storage, 'get_progressive_battle'):
            battle = arena_manager.storage.get_progressive_battle(battle_id)
        if not battle:
            battle = arena_manager.get_battle(battle_id)
        if not battle:
            yield f"data: {json.dumps({'error': 'Battle not found'})}\n\n"
            return

        # Determine models
        if hasattr(battle, 'current_pair') and battle.current_pair:
            if isinstance(battle.current_pair[0], int):
                model_a_idx, model_b_idx = battle.current_pair
                model_a = battle.all_models[model_a_idx]
                model_b = battle.all_models[model_b_idx]
            else:
                model_a, model_b = battle.current_pair
        else:
            model_a = getattr(battle, 'model_a', None)
            model_b = getattr(battle, 'model_b', None)

        if not model_a or not model_b:
            yield f"data: {json.dumps({'error': 'No active matchup'})}\n\n"
            return

        # Init event (include cached responses for instant fallback rendering)
        init_payload = {
            'arena_mode': True,
            'battle_id': battle_id,
            'model_a': model_a,
            'model_b': model_b,
            'response_a': (battle.all_responses.get(model_a) if hasattr(battle, 'all_responses') else '') or '',
            'response_b': (battle.all_responses.get(model_b) if hasattr(battle, 'all_responses') else '') or '',
            'done': False
        }
        yield f"data: {json.dumps(init_payload)}\n\n"

        # Get responses (cached or compute)
        response_a = battle.all_responses.get(model_a) if hasattr(battle, 'all_responses') else None
        response_b = battle.all_responses.get(model_b) if hasattr(battle, 'all_responses') else None

        if not response_a or not response_b:
            try:
                from app.core.ollama_adapter import OllamaAdapter
                from app.core.llm_adapter import LLMAdapter
                from app.core.arena_system_prompt import get_arena_system_prompt
                from app.core.arena_context_manager import get_arena_context_manager
                oa = OllamaAdapter()
                # Use a single, uniform system prompt (no personas, no context augmentation)
                system_prompt = get_arena_system_prompt()

                def get_resp(model_name: str) -> str:
                    info = arena_manager.available_models.get(model_name, {})
                    provider = info.get('type', 'ollama')

                    # CRITICAL: Log and validate provider detection
                    logger.info(f"🔍 Streaming - Model: {model_name}, Provider: {provider}")

                    # CRITICAL: Force-correct GPT-4o routing
                    if model_name == 'gpt-4o' and provider != 'openai':
                        logger.error(f"❌ CRITICAL: GPT-4o routed to {provider} in streaming!")
                        provider = 'openai'
                        logger.info(f"✅ Force-corrected to OpenAI")

                    if provider == 'openai':
                        try:
                            logger.info(f"🤖 Calling OpenAI (streaming) with model: {model_name}")
                            adapter = LLMAdapter(backend='openai', model=model_name)
                            # Pass system prompt as proper system role
                            user_q = (user_message or getattr(battle, 'user_message', ''))
                            response = adapter.generate(prompt=user_q, max_tokens=800, temperature=0.6, system_message=system_prompt)
                            logger.info(f"✅ OpenAI (streaming) responded: {len(response)} chars")
                            return response
                        except Exception as e:
                            logger.error(f"❌ OpenAI API call failed in streaming: {e}")
                            return f"⚠️ OpenAI API error: {str(e)}. Please check API key and quota."
                    else:
                        # Build simple ChatML-style prompt for generate API
                        u = (user_message or getattr(battle, 'user_message', ''))
                        full_prompt = (
                            f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
                            f"<|im_start|>user\n{u}<|im_end|>\n"
                            f"<|im_start|>assistant\n"
                        )
                        loop = asyncio.new_event_loop()
                        try:
                            asyncio.set_event_loop(loop)
                            raw = loop.run_until_complete(oa.generate_async(model_name, full_prompt))
                            # Apply readability formatting for Ollama output
                            from app.core.arena_manager import ArenaManager as _AM
                            return _AM.format_readable_text(raw)
                        finally:
                            loop.close()

                # Ensure readable formatting for both providers
                def _format_text(t: str) -> str:
                    if not t:
                        return t
                    import re
                    # Normalize newlines
                    s = t.replace('\r\n', '\n').replace('\r', '\n').strip()
                    # Normalize bullet markers
                    s = re.sub(r'^\*\s+', '- ', s, flags=re.MULTILINE)
                    s = re.sub(r'^•\s*', '- ', s, flags=re.MULTILINE)
                    s = re.sub(r'^(\s*)[•\u2022\u2023\u25CF\u25E6\u25A0\u25A1]+\s*', r'\1- ', s, flags=re.MULTILINE)
                    s = re.sub(r'^-\s+', '- ', s, flags=re.MULTILINE)
                    # Collapse >2 blank lines into a single blank line
                    s = re.sub(r'\n{3,}', '\n\n', s)
                    # Preserve ordered lists (lines starting with \d+\.)
                    # Avoid inserting extra spaces mid-paragraph
                    return s

                if not response_a:
                    response_a = _format_text(get_resp(model_a))
                else:
                    response_a = _format_text(response_a)
                if not response_b:
                    response_b = _format_text(get_resp(model_b))
                else:
                    response_b = _format_text(response_b)

                if hasattr(battle, 'all_responses'):
                    battle.all_responses[model_a] = response_a
                    battle.all_responses[model_b] = response_b
                    if hasattr(arena_manager.storage, 'update_progressive_battle'):
                        arena_manager.storage.update_progressive_battle(battle)
            except Exception as e:
                yield f"data: {json.dumps({'error': f'Failed to compute responses: {str(e)}'})}\n\n"
                return

        # Interleaved chunk streaming (slowed for readability)
        a_text = response_a or ''
        b_text = response_b or ''
        a_idx = 0
        b_idx = 0
        a_chunks = 0
        b_chunks = 0
        # Smaller chunks + slight delay make streaming feel natural
        chunk_size = 80
        while a_idx < len(a_text) or b_idx < len(b_text):
            if a_idx < len(a_text):
                a_chunk = a_text[a_idx:a_idx+chunk_size]
                a_idx += len(a_chunk)
                yield f"data: {json.dumps({'arena_mode': True, 'battle_id': battle_id, 'stream': True, 'side': 'a', 'delta': a_chunk, 'done': False})}\n\n"
                time.sleep(0.08)
                a_chunks += 1
            if b_idx < len(b_text):
                b_chunk = b_text[b_idx:b_idx+chunk_size]
                b_idx += len(b_chunk)
                yield f"data: {json.dumps({'arena_mode': True, 'battle_id': battle_id, 'stream': True, 'side': 'b', 'delta': b_chunk, 'done': False})}\n\n"
                time.sleep(0.08)
                b_chunks += 1

        # Final event includes full responses for safety (FE can fall back if any streaming chunk missed)
        final_payload = {
            'arena_mode': True,
            'battle_id': battle_id,
            'arena_complete': True,
            'model_a': model_a,
            'model_b': model_b,
            'response_a': a_text,
            'response_b': b_text,
            'done': True
        }
        yield f"data: {json.dumps(final_payload)}\n\n"

        # 🎯 LOG ARENA ASSISTANT RESPONSES - CRITICAL FOR COMPLETE INTERACTION CAPTURE
        try:
            session_id = session.get('session_id', 'unknown')

            # Log Model A response
            interaction_core.log_message(
                session_id=session_id,
                sender='assistant',
                content=a_text,
                intent='arena_response',
                entities={
                    'response_length': len(a_text),
                    'endpoint': '/api/arena/get_responses_streaming',
                    'workflow': 'arena',
                    'battle_id': battle_id,
                    'model': model_a,
                    'position': 'model_a',
                    'chunks_streamed': a_chunks
                }
            )

            # Log Model B response
            interaction_core.log_message(
                session_id=session_id,
                sender='assistant',
                content=b_text,
                intent='arena_response',
                entities={
                    'response_length': len(b_text),
                    'endpoint': '/api/arena/get_responses_streaming',
                    'workflow': 'arena',
                    'battle_id': battle_id,
                    'model': model_b,
                    'position': 'model_b',
                    'chunks_streamed': b_chunks
                }
            )

            logger.info(f"✅ Logged arena responses for session {session_id}: Model A ({len(a_text)} chars), Model B ({len(b_text)} chars)")
        except Exception as log_err:
            logger.error(f"Failed to log arena responses: {log_err}")

        try:
            logger.info(f"Arena stream complete: battle={battle_id}, a_chunks={a_chunks}, b_chunks={b_chunks}, a_len={len(a_text)}, b_len={len(b_text)}")
            if b_chunks == 0 and len(b_text) > 0:
                logger.warning(f"Arena stream anomaly: No B chunks streamed but B text length={len(b_text)} (battle={battle_id})")
        except Exception:
            pass

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )


@arena_bp.route('/loading_status/<battle_id>', methods=['GET'])
def get_loading_status(battle_id):
    """Get the current loading status of models for a battle."""
    try:
        battle = arena_manager.storage.get_progressive_battle(battle_id)
        if not battle:
            return jsonify({'error': 'Battle not found'}), 404

        loaded_models = list(battle.all_responses.keys())
        pending_models = [m for m in battle.all_models if m not in battle.all_responses]

        return jsonify({
            'loaded_models': loaded_models,
            'pending_models': pending_models,
            'total_models': len(battle.all_models),
            'progress_percentage': (len(loaded_models) / len(battle.all_models)) * 100,
            'all_loaded': len(pending_models) == 0
        })
    except Exception as e:
        logger.error(f"Error getting loading status: {e}")
        return jsonify({'error': str(e)}), 500


@arena_bp.route('/vote', methods=['POST'])
def record_vote():
    """
    Record user's preference vote for a tournament-style battle.
    Supports both 'vote' and 'preference' parameters for compatibility.
    
    Request body:
    {
        "battle_id": "uuid",
        "vote": "a" | "b" | "tie" | "bad"  // or
        "preference": "left" | "right" | "tie" | "both_bad"
    }
    """
    try:
        data = request.get_json()
        battle_id = data.get('battle_id')
        
        # Support both 'vote' and 'preference' parameters
        vote = data.get('vote') or data.get('preference')
        
        # Map old preference values to new vote values
        vote_mapping = {
            'left': 'a',
            'right': 'b',
            'both_bad': 'bad',
            'a': 'a',
            'b': 'b',
            'tie': 'tie',
            'bad': 'bad'
        }
        
        if vote in vote_mapping:
            vote = vote_mapping[vote]
        
        if not battle_id or not vote:
            return jsonify({
                'error': 'battle_id and preference are required'
            }), 400
        
        if vote not in ['a', 'b', 'tie', 'bad']:
            return jsonify({
                'error': f'Invalid vote value: {vote}'
            }), 400

        # 🎯 LOG ARENA VOTE - CRITICAL FOR COMPLETE INTERACTION CAPTURE
        try:
            session_id = session.get('session_id', 'unknown')
            vote_message = f"Arena vote: {vote}"

            interaction_core.log_message(
                session_id=session_id,
                sender='user',
                content=vote_message,
                intent='arena_vote',
                entities={
                    'message_length': len(vote_message),
                    'endpoint': '/api/arena/vote',
                    'workflow': 'arena',
                    'battle_id': battle_id,
                    'vote_choice': vote
                }
            )
            logger.info(f"✅ Logged arena vote for session {session_id}: {vote}")
        except Exception as log_err:
            logger.error(f"Failed to log arena vote: {log_err}")

        # Ensure arena_manager is initialized
        if not arena_manager:
            from flask import current_app
            init_arena_system(current_app)
        
        # Get the battle from storage (try progressive first, then regular)
        battle = None
        if hasattr(arena_manager.storage, 'get_progressive_battle'):
            battle = arena_manager.storage.get_progressive_battle(battle_id)
        
        if not battle:
            battle = arena_manager.get_battle(battle_id)
        
        if not battle:
            return jsonify({'error': 'Battle not found'}), 404

        # Use centralized progressive choice handling (schedules OpenAI final as D)
        if hasattr(battle, 'record_choice'):
            choice = 'left' if vote == 'a' else 'right' if vote == 'b' else vote
            result = arena_manager.submit_progressive_choice(battle_id, choice)
            if 'error' in result:
                return jsonify(result), 404
            if result.get('status') == 'continue':
                model_a = result.get('model_a')
                model_b = result.get('model_b')
                response_a = result.get('response_a') or ''
                response_b = result.get('response_b') or ''
                current_round = result.get('current_round', 0)
                display_round = (current_round or 0) + 1

                # Simple, clear labels for tournament progression
                # Round 1: A vs B
                # Round 2: Winner stays in their position, C joins
                # Round 3+: Winner stays in their position, D joins

                if current_round == 1:
                    # First round: simple A vs B
                    label_a, label_b = ('A', 'B')
                elif current_round == 2:
                    # Round 2: Winner from round 1 vs C
                    # Keep it simple - winner on left, new challenger on right
                    label_a, label_b = ('Winner (A/B)', 'C')
                elif current_round >= 3:
                    # Round 3+: Winner vs D (usually OpenAI)
                    label_a, label_b = ('Winner', 'D')
                else:
                    # Default fallback
                    label_a, label_b = ('Model 1', 'Model 2')

                # Determine if we already have solid cached responses for the next round
                needs_resp = False
                a_empty = not response_a or (isinstance(response_a, str) and response_a.strip() == '')
                b_empty = not response_b or (isinstance(response_b, str) and response_b.strip() == '')
                a_error = isinstance(response_a, str) and response_a.startswith("Error:")
                b_error = isinstance(response_b, str) and response_b.startswith("Error:")
                if a_empty or b_empty or a_error or b_error:
                    needs_resp = True

                # Enrich meta arrays from battle state to avoid nulls on frontend
                bstate = arena_manager.storage.get_progressive_battle(battle_id)
                eliminated_models = getattr(bstate, 'eliminated_models', []) or []
                winner_chain = getattr(bstate, 'winner_chain', []) or []
                remaining_models = getattr(bstate, 'remaining_models', []) or []
                previous_winner = winner_chain[-1] if winner_chain else None

                # If either side is empty/error, signal frontend to stream-compute
                a_empty = not response_a or (isinstance(response_a, str) and response_a.strip() == '')
                b_empty = not response_b or (isinstance(response_b, str) and response_b.strip() == '')
                a_error = isinstance(response_a, str) and response_a.startswith('Error:')
                b_error = isinstance(response_b, str) and response_b.startswith('Error:')
                needs_resp = a_empty or b_empty or a_error or b_error

                return jsonify({
                    'continue_battle': True,
                    'needs_responses': needs_resp,
                    'round': display_round,
                    'model_a': model_a,
                    'model_b': model_b,
                    'response_a': response_a,
                    'response_b': response_b,
                    'response_label_a': label_a,
                    'response_label_b': label_b,
                    'battle_id': battle_id,
                    'eliminated_models': eliminated_models,
                    'winner_chain': winner_chain,
                    'remaining_models': remaining_models,
                    'previous_winner': previous_winner
                })
            else:
                return jsonify({
                    'continue_battle': False,
                    'final_ranking': result.get('final_ranking', []) or [],
                    'winner_chain': result.get('winner_chain', []) or [],
                    'eliminated_models': result.get('eliminated_models', []) or []
                })

        # Legacy fallback (should not be reached due to early return above)
        if hasattr(battle, 'record_choice'):
            # Tournament-style battle
            logger.info(f"Recording tournament vote: battle={battle_id}, vote={vote}")
            
            # Map vote to choice format expected by record_choice
            choice = 'left' if vote == 'a' else 'right' if vote == 'b' else vote
            
            # Record the choice and check if there are more rounds
            more_rounds = battle.record_choice(choice)
            
            if more_rounds and battle.current_pair:
                # Get next matchup
                # current_pair can be either indices or model names
                if isinstance(battle.current_pair[0], int):
                    # Indices
                    model_a_idx, model_b_idx = battle.current_pair
                    model_a = battle.all_models[model_a_idx]
                    model_b = battle.all_models[model_b_idx]
                else:
                    # Model names directly
                    model_a, model_b = battle.current_pair
                
                # The backend returns (winner, challenger) - we keep this ordering
                # No need to swap positions - frontend handles display correctly
                logger.info(f"Next round: {model_a} vs {model_b}")
                logger.info(f"Vote was: {vote}, winner is: {battle.winner_chain[-1] if battle.winner_chain else 'unknown'}")
                logger.info(f"Battle state - remaining_models: {battle.remaining_models}")
                logger.info(f"Battle state - winner_chain: {battle.winner_chain}")
                logger.info(f"Battle state - eliminated_models: {battle.eliminated_models}")
                
                # Update progressive battle in storage BEFORE retrieving responses
                # This ensures the latest state is saved
                if hasattr(arena_manager.storage, 'update_progressive_battle'):
                    arena_manager.storage.update_progressive_battle(battle)
                else:
                    arena_manager.update_battle(battle)
                
                # Log detailed cache state
                logger.info(f"=== CACHE STATE DEBUG ===")
                logger.info(f"Total models in battle: {battle.all_models}")
                logger.info(f"Available responses in cache: {list(battle.all_responses.keys())}")
                logger.info(f"Cache has {len(battle.all_responses)} responses")
                
                # Log each cached response
                for model_name, response in battle.all_responses.items():
                    logger.info(f"  - {model_name}: {len(response) if response else 0} chars")
                
                logger.info(f"Retrieving responses for matchup: {model_a} vs {model_b}")
                
                # Get responses from cache
                response_a = battle.all_responses.get(model_a, '')
                response_b = battle.all_responses.get(model_b, '')
                
                # Detailed logging for debugging
                logger.info(f"Response A ({model_a}): {'FOUND' if response_a else 'MISSING'} - {len(response_a) if response_a else 0} chars")
                logger.info(f"Response B ({model_b}): {'FOUND' if response_b else 'MISSING'} - {len(response_b) if response_b else 0} chars")
                
                # If responses are missing, try to fetch them as fallback
                if not response_a or not response_b:
                    logger.warning(f"=== FALLBACK: Fetching missing responses ===")
                    logger.warning(f"Model A ({model_a}): {'MISSING - will fetch' if not response_a else 'OK'}")
                    logger.warning(f"Model B ({model_b}): {'MISSING - will fetch' if not response_b else 'OK'}")
                    
                    # Provider-aware fallback fetching
                    from app.core.ollama_adapter import OllamaAdapter
                    ollama_adapter = OllamaAdapter()
                    
                    # Fetch missing responses synchronously
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        async def fetch_missing_response(model_name):
                            """Fetch a single model's response."""
                            try:
                                response = await ollama_adapter.generate_async(
                                    model_name,
                                    battle.user_message,
                                    temperature=0.7,
                                    max_tokens=2048
                                )
                                return response
                            except Exception as e:
                                logger.error(f"Failed to fetch response for {model_name}: {e}")
                                return f"Error fetching response from {model_name}: {str(e)}"
                        
                        # Fetch missing responses
                        if not response_a:
                            logger.info(f"Fetching response for {model_a}...")
                            response_a = loop.run_until_complete(fetch_missing_response(model_a))
                            battle.all_responses[model_a] = response_a
                            logger.info(f"Fetched response for {model_a}: {len(response_a)} chars")
                        
                        if not response_b:
                            logger.info(f"Fetching response for {model_b}...")
                            response_b = loop.run_until_complete(fetch_missing_response(model_b))
                            battle.all_responses[model_b] = response_b
                            logger.info(f"Fetched response for {model_b}: {len(response_b)} chars")
                        
                        # Update battle with new responses
                        if hasattr(arena_manager.storage, 'update_progressive_battle'):
                            arena_manager.storage.update_progressive_battle(battle)
                        else:
                            arena_manager.update_battle(battle)
                            
                    finally:
                        loop.close()
                
                # Final check - ensure we have responses
                if not response_a:
                    response_a = f"⏳ {model_a} is still loading in the background. Please wait a moment and try again."
                if not response_b:
                    response_b = f"⏳ {model_b} is still loading in the background. Please wait a moment and try again."

                # Log the final state
                logger.info(f"=== VOTE RESPONSE ===")
                logger.info(f"Round {len(battle.winner_chain) + 1} responses ready")
                logger.info(f"Model A ({model_a}): {len(response_a)} chars")
                logger.info(f"Model B ({model_b}): {len(response_b)} chars")
                
                # Calculate proper response labels for progressive tournament
                current_round = len(battle.winner_chain) + 1

                # Map round numbers to response letters
                # Round 1: A vs B, Round 2: Winner vs C, Round 3 (final): Winner vs D (OpenAI)
                if current_round == 1:
                    label_a, label_b = ('A', 'B')
                elif current_round == 2:
                    label_a, label_b = ('Winner', 'C')
                elif current_round == 3:
                    # Ensure OpenAI is always labeled D
                    if model_b == 'gpt-4o':
                        label_a, label_b = ('Winner', 'D')
                    elif model_a == 'gpt-4o':
                        label_a, label_b = ('D', 'Winner')
                    else:
                        label_a, label_b = ('Winner', 'D')
                else:
                    label_a, label_b = ('Winner', 'Challenger')

                # Stream next round responses even if cached, for consistent UX
                return jsonify({
                    'continue_battle': True,
                    'needs_responses': True,
                    'round': current_round,
                    'model_a': model_a,
                    'model_b': model_b,
                    'battle_id': battle_id,
                    'eliminated_models': battle.eliminated_models,
                    'winner_chain': battle.winner_chain,
                    'remaining_models': battle.remaining_models,
                    'previous_winner': battle.winner_chain[-1] if battle.winner_chain else None,
                    'eliminated_side': 'right' if vote == 'a' else 'left'
                })
            else:
                # Battle complete
                # ProgressiveBattleSession has final_ranking as an attribute, not a method
                final_ranking = battle.final_ranking if battle.final_ranking else (battle.winner_chain + battle.eliminated_models[::-1])
                logger.info(f"Tournament complete: {final_ranking}")
                
                return jsonify({
                    'continue_battle': False,
                    'final_ranking': final_ranking,
                    'winner_chain': battle.winner_chain,
                    'eliminated_models': battle.eliminated_models
                })
        else:
            # Fall back to old style for compatibility
            result = arena_manager.record_preference(battle_id, vote)
            
            if 'error' in result:
                return jsonify(result), 404
            
            return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error recording vote: {e}")
        return jsonify({
            'error': 'Failed to record vote',
            'details': str(e)
        }), 500


@arena_bp.route('/start_progressive', methods=['POST'])
def start_progressive_battle():
    """
    Start a progressive battle session with 5 models.
    
    Request body:
    {
        "message": "User's query",
        "num_models": 5  # Optional, defaults to 5
    }
    
    Response:
    {
        "battle_id": "uuid",
        "status": "initialized",
        "total_models": 5,
        "message": "Progressive battle session created"
    }
    """
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        num_models = data.get('num_models', 3)
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Create progressive battle session
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            battle_info = loop.run_until_complete(
                arena_manager.start_progressive_battle(
                    user_message,
                    num_models=num_models,
                    session_id=data.get('session_id')
                )
            )
        finally:
            loop.close()
        
        # Store battle ID in session
        session['current_progressive_battle_id'] = battle_info['battle_id']
        
        return jsonify(battle_info)
    
    except Exception as e:
        logger.error(f"Error starting progressive battle: {e}")
        return jsonify({
            'error': 'Failed to start progressive battle',
            'details': str(e)
        }), 500


@arena_bp.route('/get_progressive_responses', methods=['POST'])
def get_progressive_responses():
    """
    Get all model responses for a progressive battle.
    Pre-fetches all responses for smooth transitions.
    
    Request body:
    {
        "battle_id": "uuid"
    }
    
    Response:
    {
        "battle_id": "uuid",
        "current_round": 0,
        "model_a": "llama3.1-8b",
        "model_b": "mistral-7b",
        "response_a": "...",
        "response_b": "...",
        "remaining_comparisons": 1
    }
    """
    try:
        data = request.get_json()
        battle_id = data.get('battle_id')
        
        if not battle_id:
            return jsonify({'error': 'battle_id is required'}), 400
        
        # Get all model responses
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            responses = loop.run_until_complete(
                arena_manager.get_all_model_responses(battle_id)
            )
        finally:
            loop.close()
        
        if 'error' in responses:
            return jsonify(responses), 404
        
        return jsonify(responses)
    
    except Exception as e:
        logger.error(f"Error getting progressive responses: {e}")
        return jsonify({
            'error': 'Failed to get responses',
            'details': str(e)
        }), 500


@arena_bp.route('/submit_progressive_choice', methods=['POST'])
def submit_progressive_choice():
    """
    Submit user's choice in a progressive battle.
    
    Request body:
    {
        "battle_id": "uuid",
        "choice": "left" | "right" | "tie"
    }
    
    Response (if more comparisons):
    {
        "status": "continue",
        "current_round": 1,
        "model_a": "llama3.1-8b",  # Winner from previous round
        "model_b": "phi3-mini",     # New challenger
        "response_a": "...",
        "response_b": "...",
        "eliminated_model": "mistral-7b"
    }
    
    Response (if completed):
    {
        "status": "completed",
        "final_ranking": ["llama3.1-8b", "phi3-mini", "mistral-7b"],
        "winner": "llama3.1-8b",
        "total_rounds": 2
    }
    """
    try:
        data = request.get_json()
        battle_id = data.get('battle_id')
        choice = data.get('choice')
        
        if not battle_id or not choice:
            return jsonify({'error': 'battle_id and choice are required'}), 400
        
        if choice not in ['left', 'right', 'tie']:
            return jsonify({'error': 'Invalid choice value'}), 400
        
        # Submit choice and get next matchup or results
        result = arena_manager.submit_progressive_choice(battle_id, choice)
        
        if 'error' in result:
            return jsonify(result), 404
        
        # Clear session if completed
        if result.get('status') == 'completed':
            if session.get('current_progressive_battle_id') == battle_id:
                session.pop('current_progressive_battle_id', None)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error submitting progressive choice: {e}")
        return jsonify({
            'error': 'Failed to submit choice',
            'details': str(e)
        }), 500


@arena_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """
    Get the current model leaderboard.
    
    Response:
    {
        "leaderboard": [
            {
                "rank": 1,
                "model": "gpt-4o",
                "display_name": "GPT-4o",
                "elo_rating": 1650.5,
                "battles_fought": 42,
                "win_rate": 65.3
            },
            ...
        ]
    }
    """
    try:
        if not arena_manager:
            return jsonify({
                'error': 'Arena system not initialized'
            }), 503
        
        leaderboard = arena_manager.get_leaderboard()
        
        return jsonify({
            'leaderboard': leaderboard,
            'last_updated': time.time()
        })
    
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        return jsonify({
            'error': 'Failed to get leaderboard',
            'details': str(e)
        }), 500


@arena_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """
    Get comprehensive arena statistics.
    
    Response includes preference distribution, model usage, and more.
    """
    try:
        if not arena_manager:
            return jsonify({
                'error': 'Arena system not initialized'
            }), 503
        
        stats = arena_manager.get_statistics()
        
        return jsonify(stats)
    
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return jsonify({
            'error': 'Failed to get statistics',
            'details': str(e)
        }), 500


@arena_bp.route('/check_routing', methods=['POST'])
def check_routing():
    """
    Check how a query would be routed (for debugging/testing).
    
    Request body:
    {
        "message": "User's query"
    }
    
    Response:
    {
        "route": "arena" | "openai",
        "query_type": "general_chat",
        "reasoning": "Why this route was chosen",
        "confidence": 0.95
    }
    """
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({
                'error': 'Message is required'
            }), 400
        
        # Get session context
        session_context = {
            'data_loaded': session.get('data_loaded', False),
            'csv_loaded': session.get('csv_loaded', False),
            'shapefile_loaded': session.get('shapefile_loaded', False),
            'tpr_workflow_active': session.get('tpr_workflow_active', False),
            'current_tab': data.get('current_tab', 'main')
        }
        
        # Routing decision is now handled by Mistral LLM in analysis_routes.py
        # This endpoint can be deprecated
        return jsonify({
            'message': 'Routing is now handled by Mistral LLM in analysis routes',
            'deprecated': True
        })
    
    except Exception as e:
        logger.error(f"Error checking routing: {e}")
        return jsonify({
            'error': 'Failed to check routing',
            'details': str(e)
        }), 500


@arena_bp.route('/export_training_data', methods=['GET'])
def export_training_data():
    """
    Export Arena battle data for model training.
    
    Query params:
    - type: Export type ('dpo', 'rlhf', 'analytics')
    - format: Output format ('jsonl', 'json', 'csv')
    
    Response:
    {
        "success": true,
        "file_path": "/path/to/exported/file",
        "export_type": "dpo",
        "format": "jsonl",
        "battles_included": 100,
        "examples_generated": 150
    }
    """
    try:
        if not arena_manager:
            return jsonify({
                'error': 'Arena system not initialized'
            }), 503
        
        export_type = request.args.get('type', 'dpo')
        format_type = request.args.get('format', 'jsonl')
        
        # Validate export type
        if export_type not in ['dpo', 'rlhf', 'analytics']:
            return jsonify({
                'error': f'Invalid export type: {export_type}',
                'valid_types': ['dpo', 'rlhf', 'analytics']
            }), 400
        
        # Validate format
        if format_type not in ['jsonl', 'json', 'csv']:
            return jsonify({
                'error': f'Invalid format: {format_type}',
                'valid_formats': ['jsonl', 'json', 'csv']
            }), 400
        
        # Export the data
        result = arena_manager.export_training_data(export_type, format_type)
        
        if result.get('success'):
            # Return the export info
            return jsonify(result)
        else:
            return jsonify({
                'error': 'Export failed',
                'details': result.get('error', 'Unknown error')
            }), 500
    
    except Exception as e:
        logger.error(f"Error exporting training data: {e}")
        return jsonify({
            'error': 'Failed to export training data',
            'details': str(e)
        }), 500

@arena_bp.route('/debug/health', methods=['GET'])
def debug_health():
    """Simple health check that returns any startup errors."""
    import sys
    import traceback
    try:
        # Test if arena_manager is accessible
        manager_status = "initialized" if arena_manager else "not_initialized"

        # Try to access available_models
        models_available = []
        if arena_manager and hasattr(arena_manager, 'available_models'):
            models_available = list(arena_manager.available_models.keys())

        return jsonify({
            'status': 'healthy',
            'arena_manager': manager_status,
            'models': models_available,
            'python_version': sys.version,
            'imports_ok': True
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc(),
            'type': type(e).__name__
        }), 500


@arena_bp.route('/debug/model_config/<model_name>', methods=['GET'])
def debug_model_config(model_name):
    """Debug endpoint to inspect model configuration."""
    import traceback
    try:
        if not arena_manager:
            return jsonify({
                'error': 'Arena manager not initialized',
                'manager_exists': arena_manager is not None
            }), 500

        config = arena_manager.available_models.get(model_name, {})
        provider = config.get('type', 'ollama')

        return jsonify({
            'model_name': model_name,
            'config': config,
            'detected_provider': provider,
            'all_models': list(arena_manager.available_models.keys()),
            'full_config': {k: {'type': v.get('type', 'unknown'), 'display_name': v.get('display_name', 'unknown')}
                           for k, v in arena_manager.available_models.items()}
        })
    except Exception as e:
        logger.error(f"Error in debug endpoint: {e}")
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc(),
            'type': type(e).__name__
        }), 500


@arena_bp.route('/get_next_responses', methods=['POST'])
def get_next_responses():
    """
    Get model responses for the next round of a tournament.
    This is called after voting to get responses for the next matchup.
    """
    try:
        data = request.get_json()
        battle_id = data.get('battle_id')
        
        if not battle_id:
            return jsonify({'error': 'battle_id is required'}), 400
        
        # Ensure arena_manager is initialized
        if not arena_manager:
            from flask import current_app
            init_arena_system(current_app)
        
        # Get the progressive battle
        battle = None
        if hasattr(arena_manager.storage, 'get_progressive_battle'):
            battle = arena_manager.storage.get_progressive_battle(battle_id)
        
        if not battle:
            return jsonify({'error': 'Battle not found'}), 404
        
        # Get current matchup models
        if battle.current_pair:
            if isinstance(battle.current_pair[0], int):
                model_a = battle.all_models[battle.current_pair[0]]
                model_b = battle.all_models[battle.current_pair[1]]
            else:
                model_a, model_b = battle.current_pair
            
            logger.info(f"Getting responses for: {model_a} vs {model_b}")
            logger.info(f"User message: {battle.user_message[:100]}...")
            
            # Call models using Ollama API with GPU instance
            import requests
            import time
            import os
            from app.core.arena_system_prompt import get_arena_system_prompt
            from app.core.arena_context_manager import get_arena_context_manager
            
            # Get base Arena system prompt
            base_arena_prompt = get_arena_system_prompt()
            
            # Get session context to enhance the prompt
            context_manager = get_arena_context_manager()
            session_context = context_manager.get_session_context(
                session_id=session.get('session_id', 'unknown'),
                session_data=dict(session)
            )
            
            # Format context for inclusion in prompt
            context_enhancement = context_manager.format_context_for_prompt(session_context)
            
            # Use a single, uniform system prompt (no context augmentation)
            enhanced_arena_prompt = base_arena_prompt
            
            # Log context inclusion
            if context_enhancement:
                logger.info(f"Enhanced Arena prompt with session context ({len(context_enhancement)} chars)")
            else:
                logger.info("No session context available for Arena models")
            
            # Use GPU instance if configured, otherwise fallback
            ollama_host = os.environ.get('OLLAMA_HOST', os.environ.get('AWS_OLLAMA_HOST', '172.31.45.157'))
            ollama_url = f"http://{ollama_host}:11434/v1/chat/completions"
            logger.info(f"Using Ollama at: {ollama_url}")
            
            logger.info("Starting parallel model calls...")
            
            # Get responses - run in parallel with threads for speed
            import concurrent.futures
            import threading
            
            response_a = ""
            response_b = ""
            
            def call_model(model_name):
                """Call a model using its configured provider and return response."""
                try:
                    # Get provider with comprehensive logging
                    provider = 'ollama'
                    model_config = {}

                    if hasattr(arena_manager, 'available_models'):
                        model_config = arena_manager.available_models.get(model_name, {})
                        provider = model_config.get('type', 'ollama')

                    # CRITICAL: Log provider detection for debugging
                    logger.info(f"🔍 Model: {model_name}")
                    logger.info(f"📋 Config: {model_config}")
                    logger.info(f"🎯 Detected Provider: {provider}")
                    logger.info(f"📚 All Models: {list(arena_manager.available_models.keys())}")

                    # CRITICAL: Validate GPT-4o routing
                    if model_name == 'gpt-4o' and provider != 'openai':
                        logger.error(f"❌ CRITICAL: GPT-4o routed to {provider} instead of OpenAI!")
                        logger.error(f"❌ Model config: {model_config}")
                        logger.error(f"❌ This will cause 404 error from Ollama!")
                        # Force correct provider
                        provider = 'openai'
                        logger.info(f"✅ Force-corrected provider to: openai")

                    if provider == 'openai':
                        # Use OpenAI via LLMAdapter, allow config/env override for model id
                        try:
                            from flask import current_app
                            effective_model = current_app.config.get('OPENAI_MODEL_NAME', model_name)
                        except Exception:
                            import os
                            effective_model = os.environ.get('OPENAI_MODEL_NAME', model_name)

                        logger.info(f"🤖 Calling OpenAI with model: {effective_model}")

                        try:
                            adapter = LLMAdapter(backend='openai', model=effective_model)
                            response = adapter.generate(prompt=battle.user_message, max_tokens=800, temperature=0.7, context=None, system_message=enhanced_arena_prompt)
                            logger.info(f"✅ OpenAI responded: {len(response)} chars")
                            return response
                        except Exception as e:
                            logger.error(f"❌ OpenAI API call failed: {e}")
                            return f"⚠️ OpenAI API error: {str(e)}. Please check API key and quota."
                    else:
                        # Default: Ollama-compatible chat completions
                        ollama_payload = {
                            "model": model_name,
                            "messages": [
                                {"role": "system", "content": enhanced_arena_prompt},
                                {"role": "user", "content": battle.user_message}
                            ],
                            "temperature": 0.7,
                            "max_tokens": 800
                        }
                        resp = requests.post(ollama_url, json=ollama_payload, timeout=60)
                        if resp.status_code == 200:
                            return resp.json()['choices'][0]['message']['content']
                        else:
                            return f"Error: {resp.status_code}"
                except Exception as e:
                    logger.error(f"Error calling model {model_name}: {e}")
                    return f"Error: {str(e)}"
            
            # Call both models in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                future_a = executor.submit(call_model, model_a)
                future_b = executor.submit(call_model, model_b)
                
                # Wait for both with timeout
                try:
                    response_a = future_a.result(timeout=65)
                    response_b = future_b.result(timeout=65)
                except concurrent.futures.TimeoutError:
                    logger.error("Timeout waiting for model responses")
                    response_a = response_a or "Error: Timeout"
                    response_b = response_b or "Error: Timeout"
            
            # Store responses - ProgressiveBattleSession uses all_responses
            battle.all_responses[model_a] = response_a
            battle.all_responses[model_b] = response_b
            
            # Update battle in storage
            if hasattr(arena_manager.storage, 'update_progressive_battle'):
                arena_manager.storage.update_progressive_battle(battle)
            
            return jsonify({
                'success': True,
                'model_a': model_a,
                'model_b': model_b,
                'response_a': response_a,
                'response_b': response_b
            })
        else:
            return jsonify({'error': 'No current matchup'}), 400
    
    except Exception as e:
        logger.error(f"Error getting next responses: {e}")
        return jsonify({'error': str(e)}), 500
