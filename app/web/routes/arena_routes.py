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

from app.core.arena_manager import ArenaManager
from app.core.hybrid_llm_router import HybridLLMRouter, RouterConfig
from app.core.llm_adapter import LLMAdapter

logger = logging.getLogger(__name__)

# Create blueprint
arena_bp = Blueprint('arena', __name__, url_prefix='/api/arena')

# Initialize managers (will be properly initialized in app factory)
arena_manager = None
hybrid_router = None


def init_arena_system(app):
    """Initialize arena system with app context."""
    global arena_manager, hybrid_router
    
    # Initialize arena manager
    models_config = app.config.get('ARENA_MODELS', {
        'gpt-4o': {'type': 'openai', 'display_name': 'GPT-4o'},
        'llama-3.1-8b': {'type': 'local', 'display_name': 'Llama 3.1 8B'},
        'mistral-7b': {'type': 'local', 'display_name': 'Mistral 7B'},
        'qwen-2.5-7b': {'type': 'local', 'display_name': 'Qwen 2.5 7B'},
    })
    
    arena_manager = ArenaManager(models_config)
    hybrid_router = HybridLLMRouter(arena_manager)
    
    logger.info("Arena system initialized")


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
        
        # Check if this should use arena mode
        session_context = {
            'data_loaded': session.get('data_loaded', False),
            'csv_loaded': session.get('csv_loaded', False),
            'shapefile_loaded': session.get('shapefile_loaded', False),
            'tpr_workflow_active': session.get('tpr_workflow_active', False),
            'current_tab': data.get('current_tab', 'main')
        }
        
        if not hybrid_router.should_use_arena(user_message, session_context):
            return jsonify({
                'error': 'Query not suitable for arena mode',
                'redirect_to': 'openai'
            }), 400
        
        # Create battle session
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            battle_info = loop.run_until_complete(
                arena_manager.start_battle(
                    user_message,
                    session_id=data.get('session_id')
                )
            )
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
        
        # Get battle session
        battle = arena_manager.battle_sessions.get(battle_id)
        if not battle:
            return jsonify({
                'error': 'Battle session not found'
            }), 404
        
        # Get responses from both models in parallel
        responses = {}
        latencies = {}
        
        async def get_model_response(model_name: str, position: str):
            """Get response from a specific model."""
            start_time = time.time()
            
            try:
                # Initialize appropriate LLM adapter
                if model_name == 'gpt-4o':
                    adapter = LLMAdapter(backend='openai')
                else:
                    # Local models via vLLM
                    adapter = LLMAdapter(backend='vllm', model=model_name)
                
                # Get response
                response = await adapter.generate_async(user_message)
                
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
    user_message = data.get('message')
    
    if not battle_id or not user_message:
        return jsonify({'error': 'battle_id and message are required'}), 400
    
    def generate():
        """Generate SSE stream for both models."""
        battle = arena_manager.battle_sessions.get(battle_id)
        if not battle:
            yield f"data: {json.dumps({'error': 'Battle not found'})}\n\n"
            return
        
        # Stream responses from both models
        try:
            # This would be implemented with actual streaming from models
            # For now, simulating with chunks
            response_a = "This is Assistant A's response to your query about..."
            response_b = "Assistant B here! Let me help you with..."
            
            # Simulate streaming
            for i in range(max(len(response_a), len(response_b))):
                chunk_data = {}
                
                if i < len(response_a):
                    chunk_data['a'] = response_a[i]
                    
                if i < len(response_b):
                    chunk_data['b'] = response_b[i]
                
                yield f"data: {json.dumps(chunk_data)}\n\n"
                time.sleep(0.01)  # Simulate typing delay
            
            # Send completion signal
            yield f"data: {json.dumps({'done': True})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )


@arena_bp.route('/vote', methods=['POST'])
def record_vote():
    """
    Record user's preference vote for a battle.
    
    Request body:
    {
        "battle_id": "uuid",
        "preference": "left" | "right" | "tie" | "both_bad"
    }
    
    Response reveals the models after voting:
    {
        "success": true,
        "models_revealed": {
            "model_a": {"name": "gpt-4o", "rating": 1650},
            "model_b": {"name": "llama-3.1", "rating": 1550}
        }
    }
    """
    try:
        data = request.get_json()
        battle_id = data.get('battle_id')
        preference = data.get('preference')
        
        if not battle_id or not preference:
            return jsonify({
                'error': 'battle_id and preference are required'
            }), 400
        
        if preference not in ['left', 'right', 'tie', 'both_bad']:
            return jsonify({
                'error': 'Invalid preference value'
            }), 400
        
        # Record preference and get results
        result = arena_manager.record_preference(battle_id, preference)
        
        if 'error' in result:
            return jsonify(result), 404
        
        # Clear battle from session
        if session.get('current_battle_id') == battle_id:
            session.pop('current_battle_id', None)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error recording vote: {e}")
        return jsonify({
            'error': 'Failed to record vote',
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
        
        # Get routing decision
        decision = hybrid_router.route_query(user_message, session_context)
        
        return jsonify({
            'route': decision.route,
            'query_type': decision.query_type.value,
            'reasoning': decision.reasoning,
            'confidence': decision.confidence,
            'use_arena': decision.use_arena
        })
    
    except Exception as e:
        logger.error(f"Error checking routing: {e}")
        return jsonify({
            'error': 'Failed to check routing',
            'details': str(e)
        }), 500