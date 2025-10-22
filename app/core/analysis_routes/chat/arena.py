"""Arena-related helpers for analysis chat routes."""

from __future__ import annotations

import asyncio
import logging
import random
import time
import uuid
import json
from typing import Dict, Optional, Tuple

import requests
from flask import Response, current_app, jsonify, session

from app.core.arena_manager import ArenaManager, ProgressiveBattleSession
from app.core.arena_system_prompt import get_arena_system_prompt

logger = logging.getLogger(__name__)


def process_arena_message(
    user_message: str,
    session_id: str,
    is_data_analysis: bool,
    processing_start_time: float,
) -> Tuple[Optional[Dict], Optional[Response]]:
    """Execute Arena comparison flow for a chat message.

    Returns a tuple ``(response_dict, flask_response)``. When Arena completes normally,
    ``response_dict`` contains the response payload and ``flask_response`` is ``None``.
    When the logic falls back to the interpreter directly (e.g. both Arena models need
    tools), ``response_dict`` is ``None`` and ``flask_response`` contains the response.
    """
    arena_manager = ArenaManager()
    arena_system_prompt = get_arena_system_prompt()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        view_index = session.get('arena_view_index', 0)
        battle_result = loop.run_until_complete(
            arena_manager.start_battle(user_message, session_id, view_index)
        )
        battle_id = battle_result['battle_id']
        model_a, model_b = arena_manager.get_model_pair_for_view(view_index)

        responses: Dict[str, str] = {}
        latencies: Dict[str, float] = {}

        ollama_model_map = {
            'llama3.1:8b': 'llama3.1:8b',
            'mistral:7b': 'mistral:7b',
            'phi3:mini': 'phi3:mini',
        }

        # Model A response
        try:
            start = time.time()
            if model_a in ollama_model_map:
                ollama_host = current_app.config.get('OLLAMA_HOST', 'localhost')
                ollama_port = current_app.config.get('OLLAMA_PORT', '11434')
                ollama_url = f"http://{ollama_host}:{ollama_port}/v1/chat/completions"
                ollama_payload = {
                    'model': ollama_model_map[model_a],
                    'messages': [
                        {'role': 'system', 'content': arena_system_prompt},
                        {'role': 'user', 'content': user_message},
                    ],
                    'max_tokens': 500,
                }
                logger.info(
                    "Arena Model A - URL: %s, Model: %s",
                    ollama_url,
                    ollama_model_map[model_a],
                )
                ollama_response = requests.post(ollama_url, json=ollama_payload, timeout=30)
                logger.info("Arena Model A - Status: %s", ollama_response.status_code)
                if ollama_response.status_code == 200:
                    responses['a'] = ollama_response.json()['choices'][0]['message']['content']
                else:
                    logger.error("Arena Model A - Error: %s", ollama_response.text[:200])
                    responses['a'] = f"Error from Ollama: {ollama_response.status_code}"
            else:
                responses['a'] = f"Model {model_a} not available in Ollama"
            latencies['a'] = (time.time() - start) * 1000
        except Exception as exc:
            logger.error("Error calling model A: %s", exc)
            responses['a'] = f"Error: {exc}"
            latencies['a'] = 0

        # Model B response
        try:
            start = time.time()
            if model_b in ollama_model_map:
                ollama_host = current_app.config.get('OLLAMA_HOST', 'localhost')
                ollama_port = current_app.config.get('OLLAMA_PORT', '11434')
                ollama_url = f"http://{ollama_host}:{ollama_port}/v1/chat/completions"
                ollama_payload = {
                    'model': ollama_model_map[model_b],
                    'messages': [
                        {'role': 'system', 'content': arena_system_prompt},
                        {'role': 'user', 'content': user_message},
                    ],
                    'max_tokens': 500,
                }
                logger.info(
                    "Arena Model B - URL: %s, Model: %s",
                    ollama_url,
                    ollama_model_map[model_b],
                )
                ollama_response = requests.post(ollama_url, json=ollama_payload, timeout=30)
                logger.info("Arena Model B - Status: %s", ollama_response.status_code)
                if ollama_response.status_code == 200:
                    responses['b'] = ollama_response.json()['choices'][0]['message']['content']
                else:
                    logger.error("Arena Model B - Error: %s", ollama_response.text[:200])
                    responses['b'] = f"Error from Ollama: {ollama_response.status_code}"
            else:
                responses['b'] = f"Model {model_b} not available in Ollama"
            latencies['b'] = (time.time() - start) * 1000
        except Exception as exc:
            logger.error("Error calling model B: %s", exc)
            responses['b'] = f"Error: {exc}"
            latencies['b'] = 0

        indicators = [
            "i need to see",
            "upload",
            "provide the",
            "i would need",
            "cannot analyze without",
            "don't have access",
            "no data available",
            "please share",
            "i require",
            "unable to access",
            "can't see your",
        ]
        model_a_needs_tools = any(indicator in responses.get('a', '').lower() for indicator in indicators)
        model_b_needs_tools = any(indicator in responses.get('b', '').lower() for indicator in indicators)

        if model_a_needs_tools and model_b_needs_tools:
            loop.close()
            session['last_tool_used'] = True
            session.modified = True

            from app.core.request_interpreter import RequestInterpreter

            interpreter = RequestInterpreter()
            result = interpreter.interpret(user_message, session, is_data_analysis=is_data_analysis)
            processing_time = time.time() - processing_start_time
            payload = {
                'status': 'success',
                'response': result.get('message', result.get('response', '')),
                'message': result.get('message', result.get('response', '')),
                'processing_time': processing_time,
            }
            return None, jsonify(payload)

        loop.run_until_complete(
            arena_manager.submit_response(battle_id, 'a', responses['a'], latencies['a'])
        )
        loop.run_until_complete(
            arena_manager.submit_response(battle_id, 'b', responses['b'], latencies['b'])
        )

        response = {
            'status': 'success',
            'arena_mode': True,
            'battle_id': battle_id,
            'response_a': responses['a'],
            'response_b': responses['b'],
            'latency_a': latencies['a'],
            'latency_b': latencies['b'],
            'view_index': view_index,
            'model_a': model_a,
            'model_b': model_b,
            'response': f"Arena comparison ready. View {view_index + 1} of 3.",
        }
        return response, None
    finally:
        loop.close()


def process_arena_streaming(user_message: str) -> Optional[Response]:
    """Run the Arena streaming flow for a message.

    Returns a streaming ``Response`` when Arena handles the request. If Arena should
    not handle the message, ``None`` is returned so the caller can continue with tools.
    """
    arena_manager = ArenaManager()
    arena_system_prompt = get_arena_system_prompt()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        battle_id = str(uuid.uuid4())
        all_models = list(arena_manager.available_models.keys())
        random.shuffle(all_models)

        battle = ProgressiveBattleSession(
            session_id=battle_id,
            user_message=user_message,
            all_models=all_models,
            remaining_models=all_models.copy(),
        )

        model_a, model_b = battle.remaining_models[0], battle.remaining_models[1]
        battle.current_pair = (model_a, model_b)
        battle.current_round = 0
        arena_manager.store_progressive_battle(battle)

        responses = {}
        latencies = {}
        ollama_model_map = {
            'llama3.1:8b': 'llama3.1:8b',
            'mistral:7b': 'mistral:7b',
            'phi3:mini': 'phi3:mini',
        }

        for key, model_name in [('a', model_a), ('b', model_b)]:
            try:
                if model_name in ollama_model_map:
                    ollama_host = current_app.config.get('OLLAMA_HOST', 'localhost')
                    ollama_port = current_app.config.get('OLLAMA_PORT', '11434')
                    ollama_url = f"http://{ollama_host}:{ollama_port}/v1/chat/completions"
                    start = time.time()
                    ollama_response = requests.post(
                        ollama_url,
                        json={
                            'model': ollama_model_map[model_name],
                            'messages': [
                                {'role': 'system', 'content': arena_system_prompt},
                                {'role': 'user', 'content': user_message},
                            ],
                            'max_tokens': 500,
                        },
                        timeout=30,
                    )
                    if ollama_response.status_code == 200:
                        responses[key] = ollama_response.json()['choices'][0]['message']['content']
                    else:
                        responses[key] = f"Error from model: {ollama_response.status_code}"
                    latencies[key] = (time.time() - start) * 1000
                else:
                    responses[key] = f"Model {model_name} not available in Ollama"
                    latencies[key] = 0
            except Exception as exc:
                logger.error("Error calling model %s: %s", key, exc)
                responses[key] = f"Error: {exc}"
                latencies[key] = 0

        tool_indicators = [
            'i need to see',
            'upload',
            'provide the',
            'i would need',
            'cannot analyze without',
            "don't have access",
            'no data available',
            'please share',
            'i require',
            'unable to access',
            "can't see your",
        ]
        needs_tools = all(
            any(indicator in responses.get(key, '').lower() for indicator in tool_indicators)
            for key in ('a', 'b')
        )

        if needs_tools:
            loop.close()
            return None

        arena_manager.storage.store_progressive_battle(battle)

        def generate():
            payload = {
                'status': 'success',
                'arena_mode': True,
                'battle_id': battle_id,
                'response_a': responses['a'],
                'response_b': responses['b'],
                'latency_a': latencies['a'],
                'latency_b': latencies['b'],
                'view_index': 0,
                'model_a': model_a,
                'model_b': model_b,
                'response': 'Arena comparison ready.',
                'done': True,
            }
            yield f"data: {json.dumps(payload)}\n\n"

        response = Response(generate(), mimetype='text/event-stream')
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['Connection'] = 'keep-alive'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['X-Accel-Buffering'] = 'no'
        return response
    finally:
        loop.close()


__all__ = ['process_arena_message', 'process_arena_streaming', 'handle_vote_arena']


def handle_vote_arena():
    """
    Record user vote for Arena model comparison in tournament style.
    After voting, either returns the next matchup or final results.
    """
    try:
        data = request.json
        battle_id = data.get('battle_id')
        vote = data.get('vote')  # 'a', 'b', 'tie', or 'bad'
        session_id = session.get('session_id', 'unknown')
        
        # Log the vote
        logger.info(f"Arena vote received: battle_id={battle_id}, vote={vote}, session={session_id}")
        
        # Get Arena manager and progressive battle
        from app.core.arena_manager import ArenaManager
        from app.core.arena_system_prompt import get_arena_system_prompt
        arena_manager = ArenaManager()
        arena_system_prompt = get_arena_system_prompt()
        
        # Get the progressive battle
        battle = arena_manager.storage.get_progressive_battle(battle_id)
        if not battle:
            return jsonify({
                'success': False,
                'error': 'Battle session not found'
            }), 404
        
        # Map vote to choice for progressive battle
        if vote == 'a':
            choice = 'left'
        elif vote == 'b':
            choice = 'right'
        else:  # tie or bad - pick random winner
            import random
            choice = 'left' if random.random() > 0.5 else 'right'
        
        # Record the choice
        more_rounds = battle.record_choice(choice)
        
        # Get winner and loser from current matchup
        model_a, model_b = battle.current_pair
        winner = model_a if choice == 'left' else model_b
        loser = model_b if choice == 'left' else model_a
        
        logger.info(f"Battle {battle_id}: {winner} beat {loser}")
        
        # Check if more rounds needed
        if more_rounds and battle.current_pair:
            # Get next matchup
            next_model_a, next_model_b = battle.current_pair
            
            # Get responses for next round
            import requests
            import time
            
            responses = {}
            latencies = {}
            
            ollama_host = current_app.config.get('OLLAMA_HOST', 'localhost')
            ollama_port = current_app.config.get('OLLAMA_PORT', '11434')
            ollama_url = f"http://{ollama_host}:{ollama_port}/v1/chat/completions"
            
            for model_key, model_name in [('a', next_model_a), ('b', next_model_b)]:
                try:
                    start = time.time()
                    ollama_response = requests.post(
                        ollama_url,
                        json={
                            "model": model_name,
                            "messages": [
                                {"role": "system", "content": arena_system_prompt},
                                {"role": "user", "content": battle.user_message}
                            ],
                            "max_tokens": 500
                        },
                        timeout=30
                    )
                    
                    if ollama_response.status_code == 200:
                        responses[model_key] = ollama_response.json()['choices'][0]['message']['content']
                    else:
                        responses[model_key] = f"Error from model: {ollama_response.status_code}"
                    
                    latencies[model_key] = (time.time() - start) * 1000
                except Exception as e:
                    logger.error(f"Error calling model {model_key}: {e}")
                    responses[model_key] = f"Error: {str(e)}"
                    latencies[model_key] = 0
            
            # Store responses in battle
            battle.all_responses[next_model_a] = responses['a']
            battle.all_responses[next_model_b] = responses['b']
            battle.all_latencies[next_model_a] = latencies['a']
            battle.all_latencies[next_model_b] = latencies['b']
            
            # Save updated battle
            arena_manager.storage.update_progressive_battle(battle)
            
            # Return next matchup
            return jsonify({
                'success': True,
                'continue_battle': True,
                'round': battle.current_round,
                'model_a': next_model_a,
                'model_b': next_model_b,
                'response_a': responses['a'],
                'response_b': responses['b'],
                'latency_a': latencies['a'],
                'latency_b': latencies['b'],
                'eliminated_models': battle.eliminated_models,
                'winner_chain': battle.winner_chain,
                'remaining_models': battle.remaining_models,
                'previous_winner': winner,
                'previous_loser': loser
            })
        else:
            # Battle complete - determine final ranking
            battle.completed = True
            battle.final_ranking = battle.winner_chain + battle.eliminated_models[::-1]
            
            # Save final state
            arena_manager.storage.update_progressive_battle(battle)
            
            # Log completion
            if hasattr(current_app, 'services') and current_app.services.interaction_logger:
                current_app.services.interaction_logger.log_analysis_event(
                    session_id=session_id,
                    event_type='arena_complete',
                    details={
                        'battle_id': battle_id,
                        'final_ranking': battle.final_ranking,
                        'rounds': battle.current_round
                    },
                    success=True
                )
            
            # Return final results
            return jsonify({
                'success': True,
                'continue_battle': False,
                'final_ranking': battle.final_ranking,
                'comparison_history': battle.comparison_history,
                'message': f'Tournament complete! Ranking: {" > ".join(battle.final_ranking)}'
            })
        
    except Exception as e:
        logger.error(f"Error processing arena vote: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
