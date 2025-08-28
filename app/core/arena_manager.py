"""
LLM Arena Manager for Model Comparison

Manages battle sessions, model selection, preference tracking, and ELO ratings.
Based on LM Arena / Chatbot Arena design patterns.
"""

import random
import uuid
import logging
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
import json
import os

logger = logging.getLogger(__name__)


@dataclass
class BattleSession:
    """Represents a single battle session between two models."""
    session_id: str
    model_a: str
    model_b: str
    user_message: str
    response_a: str = ""
    response_b: str = ""
    latency_a: float = 0.0
    latency_b: float = 0.0
    tokens_a: int = 0
    tokens_b: int = 0
    user_preference: Optional[str] = None  # 'left', 'right', 'tie', 'both_bad'
    timestamp: datetime = field(default_factory=datetime.now)
    conversation_history: List[Dict] = field(default_factory=list)


class ELORatingSystem:
    """ELO rating system for model comparison."""
    
    def __init__(self, k_factor: int = 32):
        self.k_factor = k_factor
        self.ratings = {}  # model_name -> rating
        self.match_history = []
        
    def get_rating(self, model: str) -> float:
        """Get current ELO rating for a model."""
        if model not in self.ratings:
            self.ratings[model] = 1500.0  # Starting ELO
        return self.ratings[model]
    
    def update_ratings(self, winner: str, loser: str, is_tie: bool = False):
        """Update ELO ratings after a match."""
        rating_winner = self.get_rating(winner)
        rating_loser = self.get_rating(loser)
        
        # Calculate expected scores
        expected_winner = 1 / (1 + 10 ** ((rating_loser - rating_winner) / 400))
        expected_loser = 1 / (1 + 10 ** ((rating_winner - rating_loser) / 400))
        
        # Actual scores (1 for win, 0.5 for tie, 0 for loss)
        if is_tie:
            score_winner = 0.5
            score_loser = 0.5
        else:
            score_winner = 1.0
            score_loser = 0.0
        
        # Update ratings
        self.ratings[winner] = rating_winner + self.k_factor * (score_winner - expected_winner)
        self.ratings[loser] = rating_loser + self.k_factor * (score_loser - expected_loser)
        
        # Log match
        self.match_history.append({
            'winner': winner if not is_tie else 'tie',
            'loser': loser if not is_tie else 'tie',
            'winner_rating_before': rating_winner,
            'loser_rating_before': rating_loser,
            'winner_rating_after': self.ratings[winner],
            'loser_rating_after': self.ratings[loser],
            'timestamp': datetime.now().isoformat()
        })


class ArenaManager:
    """
    Manages LLM battle sessions for model comparison.
    
    Features:
    - Random model pairing with equal probability
    - Blind testing (models hidden until vote)
    - ELO rating system
    - Session management
    - Preference tracking
    """
    
    def __init__(self, models_config: Optional[Dict] = None):
        """
        Initialize Arena Manager.
        
        Args:
            models_config: Configuration for available models
        """
        # Default model pool (will be connected to actual models later)
        self.available_models = models_config or {
            'gpt-4o': {'type': 'openai', 'display_name': 'GPT-4o'},
            'llama-3.1-8b': {'type': 'local', 'display_name': 'Llama 3.1 8B'},
            'mistral-7b': {'type': 'local', 'display_name': 'Mistral 7B'},
            'qwen-2.5-7b': {'type': 'local', 'display_name': 'Qwen 2.5 7B'},
        }
        
        self.battle_sessions = {}  # session_id -> BattleSession
        self.elo_system = ELORatingSystem()
        self.model_usage_stats = {model: 0 for model in self.available_models}
        self.preference_stats = {
            'left': 0,
            'right': 0,
            'tie': 0,
            'both_bad': 0
        }
        
        # Load persisted data if exists
        self._load_stats()
        
        logger.info(f"Arena Manager initialized with {len(self.available_models)} models")
    
    def get_random_model_pair(self, exclude_models: Optional[List[str]] = None) -> Tuple[str, str]:
        """
        Select two random models ensuring equal probability over time.
        
        Args:
            exclude_models: List of model names to exclude from selection
            
        Returns:
            Tuple of (model_a, model_b)
        """
        available = list(self.available_models.keys())
        
        if exclude_models:
            available = [m for m in available if m not in exclude_models]
        
        if len(available) < 2:
            raise ValueError("Not enough models available for comparison")
        
        # Weight selection by inverse of usage count for fairness
        weights = []
        min_usage = min(self.model_usage_stats.values()) or 1
        
        for model in available:
            usage = self.model_usage_stats.get(model, 0)
            # Inverse weight: less used models get higher probability
            weight = max(1, min_usage * 2 - usage)
            weights.append(weight)
        
        # Select two different models
        model_a = random.choices(available, weights=weights, k=1)[0]
        remaining = [m for m in available if m != model_a]
        remaining_weights = [w for i, w in enumerate(weights) if available[i] != model_a]
        model_b = random.choices(remaining, weights=remaining_weights, k=1)[0]
        
        # Update usage stats
        self.model_usage_stats[model_a] += 1
        self.model_usage_stats[model_b] += 1
        
        # Randomly swap positions to avoid position bias
        if random.random() > 0.5:
            return model_b, model_a
        return model_a, model_b
    
    async def start_battle(self, user_message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Start a new battle session.
        
        Args:
            user_message: The user's query
            session_id: Optional session ID (generates new if not provided)
            
        Returns:
            Dict containing battle information and initial state
        """
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Select random models
        model_a, model_b = self.get_random_model_pair()
        
        # Create battle session
        battle = BattleSession(
            session_id=session_id,
            model_a=model_a,
            model_b=model_b,
            user_message=user_message
        )
        
        self.battle_sessions[session_id] = battle
        
        logger.info(f"Started battle {session_id}: {model_a} vs {model_b}")
        
        return {
            'battle_id': session_id,
            'status': 'ready',
            'message': 'Battle session created. Waiting for model responses.',
            # Don't reveal models yet (blind testing)
            'models_hidden': True
        }
    
    async def submit_response(self, battle_id: str, model_position: str, 
                            response: str, latency: float = 0, tokens: int = 0) -> bool:
        """
        Submit a model's response to a battle.
        
        Args:
            battle_id: The battle session ID
            model_position: 'a' or 'b'
            response: The model's response
            latency: Response time in milliseconds
            tokens: Number of tokens used
            
        Returns:
            Boolean indicating success
        """
        if battle_id not in self.battle_sessions:
            logger.error(f"Battle {battle_id} not found")
            return False
        
        battle = self.battle_sessions[battle_id]
        
        if model_position == 'a':
            battle.response_a = response
            battle.latency_a = latency
            battle.tokens_a = tokens
        elif model_position == 'b':
            battle.response_b = response
            battle.latency_b = latency
            battle.tokens_b = tokens
        else:
            logger.error(f"Invalid model position: {model_position}")
            return False
        
        return True
    
    def record_preference(self, battle_id: str, preference: str) -> Dict[str, Any]:
        """
        Record user's preference for a battle.
        
        Args:
            battle_id: The battle session ID
            preference: 'left', 'right', 'tie', or 'both_bad'
            
        Returns:
            Dict with results including revealed models and updated ratings
        """
        if battle_id not in self.battle_sessions:
            return {'error': 'Battle session not found'}
        
        battle = self.battle_sessions[battle_id]
        battle.user_preference = preference
        
        # Update preference stats
        self.preference_stats[preference] += 1
        
        # Update ELO ratings
        if preference == 'left':
            self.elo_system.update_ratings(battle.model_a, battle.model_b)
        elif preference == 'right':
            self.elo_system.update_ratings(battle.model_b, battle.model_a)
        elif preference == 'tie':
            self.elo_system.update_ratings(battle.model_a, battle.model_b, is_tie=True)
        # 'both_bad' doesn't affect ratings
        
        # Reveal models after voting
        result = {
            'success': True,
            'preference_recorded': preference,
            'models_revealed': {
                'model_a': {
                    'name': battle.model_a,
                    'display_name': self.available_models[battle.model_a]['display_name'],
                    'rating': self.elo_system.get_rating(battle.model_a)
                },
                'model_b': {
                    'name': battle.model_b,
                    'display_name': self.available_models[battle.model_b]['display_name'],
                    'rating': self.elo_system.get_rating(battle.model_b)
                }
            },
            'battle_stats': {
                'latency_a': battle.latency_a,
                'latency_b': battle.latency_b,
                'tokens_a': battle.tokens_a,
                'tokens_b': battle.tokens_b
            }
        }
        
        # Save stats
        self._save_stats()
        
        logger.info(f"Preference recorded for battle {battle_id}: {preference}")
        
        return result
    
    def get_leaderboard(self) -> List[Dict[str, Any]]:
        """
        Get current model leaderboard sorted by ELO rating.
        
        Returns:
            List of model stats sorted by rating
        """
        leaderboard = []
        
        for model_name in self.available_models:
            rating = self.elo_system.get_rating(model_name)
            usage = self.model_usage_stats.get(model_name, 0)
            
            # Calculate win rate
            wins = sum(1 for match in self.elo_system.match_history 
                      if match['winner'] == model_name)
            total_matches = sum(1 for match in self.elo_system.match_history 
                              if model_name in [match['winner'], match['loser']])
            win_rate = (wins / total_matches * 100) if total_matches > 0 else 0
            
            leaderboard.append({
                'rank': 0,  # Will be set after sorting
                'model': model_name,
                'display_name': self.available_models[model_name]['display_name'],
                'elo_rating': round(rating, 1),
                'battles_fought': usage,
                'win_rate': round(win_rate, 1)
            })
        
        # Sort by ELO rating
        leaderboard.sort(key=lambda x: x['elo_rating'], reverse=True)
        
        # Add ranks
        for i, entry in enumerate(leaderboard, 1):
            entry['rank'] = i
        
        return leaderboard
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive arena statistics.
        
        Returns:
            Dict containing various statistics
        """
        total_battles = len(self.battle_sessions)
        completed_battles = sum(1 for b in self.battle_sessions.values() 
                              if b.user_preference is not None)
        
        return {
            'total_battles': total_battles,
            'completed_battles': completed_battles,
            'completion_rate': (completed_battles / total_battles * 100) if total_battles > 0 else 0,
            'preference_distribution': self.preference_stats,
            'model_usage': self.model_usage_stats,
            'leaderboard': self.get_leaderboard(),
            'active_models': len(self.available_models)
        }
    
    def _save_stats(self):
        """Save statistics to disk for persistence."""
        stats_file = 'instance/arena_stats.json'
        os.makedirs('instance', exist_ok=True)
        
        try:
            with open(stats_file, 'w') as f:
                json.dump({
                    'elo_ratings': self.elo_system.ratings,
                    'match_history': self.elo_system.match_history[-1000:],  # Keep last 1000
                    'model_usage': self.model_usage_stats,
                    'preference_stats': self.preference_stats
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save arena stats: {e}")
    
    def _load_stats(self):
        """Load statistics from disk if available."""
        stats_file = 'instance/arena_stats.json'
        
        if os.path.exists(stats_file):
            try:
                with open(stats_file, 'r') as f:
                    data = json.load(f)
                    self.elo_system.ratings = data.get('elo_ratings', {})
                    self.elo_system.match_history = data.get('match_history', [])
                    self.model_usage_stats.update(data.get('model_usage', {}))
                    self.preference_stats.update(data.get('preference_stats', {}))
                logger.info("Loaded arena stats from disk")
            except Exception as e:
                logger.error(f"Failed to load arena stats: {e}")