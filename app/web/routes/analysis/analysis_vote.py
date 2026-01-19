"""Arena voting endpoints for the analysis blueprint."""

from __future__ import annotations

import os
import time

import requests
from flask import current_app, jsonify, request, session

from app.auth.decorators import require_auth
from ...core.decorators import handle_errors, validate_session

from . import analysis_bp, logger


@analysis_bp.route('/api/vote_arena', methods=['POST'])
@require_auth
@validate_session
@handle_errors
def vote_arena():
    """Record a user vote for progressive Arena battles."""
    if os.getenv('CHATMRPT_ARENA', '0') == '0':
        return jsonify({'status': 'disabled', 'message': 'Arena is disabled by configuration.'}), 404

    try:
        data = request.json or {}
        battle_id = data.get('battle_id')
        vote = data.get('vote')
        session_id = session.get('session_id', 'unknown')

        logger.info("Arena vote received: battle_id=%s, vote=%s, session=%s", battle_id, vote, session_id)

        from app.core.arena_manager import ArenaManager
        from app.core.arena_system_prompt import get_arena_system_prompt
        from app.core.arena_context_manager import get_arena_context_manager

        arena_manager = ArenaManager()
        battle = arena_manager.storage.get_progressive_battle(battle_id)
        if not battle:
            return jsonify({'success': False, 'error': 'Battle session not found'}), 404

        base_prompt = get_arena_system_prompt()
        context_manager = get_arena_context_manager()
        session_context = context_manager.get_session_context(session_id=session_id, session_data=dict(session))
        context_enhancement = context_manager.format_context_for_prompt(session_context)
        arena_prompt = base_prompt + context_enhancement

        if vote == 'a':
            choice = 'left'
        elif vote == 'b':
            choice = 'right'
        else:
            choice = 'left' if os.urandom(1)[0] > 127 else 'right'

        more_rounds = battle.record_choice(choice)

        model_a, model_b = battle.current_pair
        winner = model_a if choice == 'left' else model_b
        loser = model_b if choice == 'left' else model_a

        logger.info("Battle %s: %s beat %s", battle_id, winner, loser)

        if more_rounds and battle.current_pair:
            next_model_a, next_model_b = battle.current_pair

            if next_model_a in battle.all_responses and next_model_b in battle.all_responses:
                responses = {
                    'a': battle.all_responses[next_model_a],
                    'b': battle.all_responses[next_model_b],
                }
                latencies = {
                    'a': battle.all_latencies.get(next_model_a, 0),
                    'b': battle.all_latencies.get(next_model_b, 0),
                }
            else:
                responses = {}
                latencies = {}
                for key, model_name in [('a', next_model_a), ('b', next_model_b)]:
                    if model_name in battle.all_responses:
                        responses[key] = battle.all_responses[model_name]
                        latencies[key] = battle.all_latencies.get(model_name, 0)
                        continue

                    logger.info("Fetching response for model %s", model_name)
                    ollama_host = current_app.config.get('OLLAMA_HOST', 'localhost')
                    ollama_port = current_app.config.get('OLLAMA_PORT', '11434')
                    ollama_url = f"http://{ollama_host}:{ollama_port}/v1/chat/completions"

                    start = time.time()
                    try:
                        api_response = requests.post(
                            ollama_url,
                            json={
                                "model": model_name,
                                "messages": [
                                    {"role": "system", "content": arena_prompt},
                                    {"role": "user", "content": battle.user_message},
                                ],
                                "max_tokens": 500,
                            },
                            timeout=30,
                        )
                        if api_response.status_code == 200:
                            content = api_response.json()['choices'][0]['message']['content']
                        else:
                            content = f"Error from model: {api_response.status_code}"
                    except Exception as exc:  # pragma: no cover - network failure
                        logger.error("Error calling model %s: %s", model_name, exc)
                        content = f"Error: {exc}"
                    latency = (time.time() - start) * 1000

                    responses[key] = content
                    latencies[key] = latency
                    battle.all_responses[model_name] = content
                    battle.all_latencies[model_name] = latency

                arena_manager.storage.update_progressive_battle(battle)

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
                'previous_loser': loser,
            })

        battle.completed = True
        battle.final_ranking = battle.winner_chain + battle.eliminated_models[::-1]
        arena_manager.storage.update_progressive_battle(battle)

        if hasattr(current_app, 'services') and current_app.services.interaction_logger:
            current_app.services.interaction_logger.log_analysis_event(
                session_id=session_id,
                event_type='arena_complete',
                details={
                    'battle_id': battle_id,
                    'final_ranking': battle.final_ranking,
                    'rounds': battle.current_round,
                },
                success=True,
            )

        ranking_display = " > ".join(battle.final_ranking)

        return jsonify({
            'success': True,
            'continue_battle': False,
            'final_ranking': battle.final_ranking,
            'comparison_history': battle.comparison_history,
            'message': f'Tournament complete! Ranking: {ranking_display}',
        })

    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Error processing arena vote: %s", exc)
        return jsonify({'success': False, 'error': str(exc)}), 500
