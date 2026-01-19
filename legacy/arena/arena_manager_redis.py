"""
LLM Arena Manager with Redis Storage - FIXED VERSION
Includes get_battle method and storage_status property
"""

import random
import uuid
import logging
import asyncio
import time
import json
import redis
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field, asdict
import pickle

# Import interaction tracking
from app.interaction.core import DatabaseManager
from app.interaction.events import EventLogger

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
    status: str = "active"  # Add status field
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for Redis storage."""
        data = asdict(self)
        # Convert datetime to ISO format string
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'BattleSession':
        """Create instance from dictionary."""
        # Convert ISO string back to datetime
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class RedisStorage:
    """Redis storage backend for battle sessions."""
    
    def __init__(self, redis_host: str = None, redis_port: int = 6379, 
                 redis_password: str = None, redis_db: int = 1):
        """Initialize Redis storage."""
        # Get Redis configuration from environment or use defaults
        self.redis_host = redis_host or os.environ.get('REDIS_HOST', 'chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com')
        self.redis_port = redis_port or int(os.environ.get('REDIS_PORT', 6379))
        self.redis_password = redis_password or os.environ.get('REDIS_PASSWORD', None)
        self.redis_db = redis_db
        
        self.redis_client = None
        self.connected = False
        self.fallback_storage = {}  # Fallback to in-memory if Redis fails
        
        # Try to connect to Redis
        self._connect()
    
    def _connect(self) -> bool:
        """Establish Redis connection."""
        try:
            self.redis_client = redis.StrictRedis(
                host=self.redis_host,
                port=self.redis_port,
                password=self.redis_password,
                db=self.redis_db,
                decode_responses=False,  # We'll handle encoding/decoding
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            self.redis_client.ping()
            self.connected = True
            logger.info(f"✅ Connected to Redis at {self.redis_host}:{self.redis_port}")
            return True
            
        except redis.ConnectionError as e:
            logger.warning(f"⚠️ Could not connect to Redis: {e}")
            logger.warning("Falling back to in-memory storage")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"❌ Redis connection error: {e}")
            self.connected = False
            return False
    
    def _get_key(self, battle_id: str) -> str:
        """Generate Redis key for battle."""
        return f"arena:battle:{battle_id}"
    
    def store_battle(self, battle: BattleSession, ttl_hours: int = 24) -> bool:
        """Store battle session in Redis."""
        key = self._get_key(battle.session_id)
        
        if self.connected:
            try:
                # Convert to JSON for storage
                battle_json = json.dumps(battle.to_dict())
                
                # Store with TTL
                self.redis_client.setex(
                    key,
                    timedelta(hours=ttl_hours),
                    battle_json
                )
                
                # Also maintain a set of active battles
                self.redis_client.sadd("arena:active_battles", battle.session_id)
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to store battle in Redis: {e}")
                # Fall back to in-memory
                self.fallback_storage[battle.session_id] = battle
                return True
        else:
            # Use fallback storage
            self.fallback_storage[battle.session_id] = battle
            return True
    
    def get_battle(self, battle_id: str) -> Optional[BattleSession]:
        """Retrieve battle session from Redis."""
        if self.connected:
            try:
                key = self._get_key(battle_id)
                battle_json = self.redis_client.get(key)
                
                if battle_json:
                    battle_dict = json.loads(battle_json)
                    return BattleSession.from_dict(battle_dict)
                
                # Check fallback if not in Redis
                if battle_id in self.fallback_storage:
                    return self.fallback_storage[battle_id]
                    
                return None
                
            except Exception as e:
                logger.error(f"Failed to retrieve battle from Redis: {e}")
                # Check fallback
                return self.fallback_storage.get(battle_id)
        else:
            # Use fallback storage
            return self.fallback_storage.get(battle_id)
    
    def update_battle(self, battle: BattleSession) -> bool:
        """Update existing battle session."""
        return self.store_battle(battle)
    
    def delete_battle(self, battle_id: str) -> bool:
        """Delete battle session from Redis."""
        if self.connected:
            try:
                key = self._get_key(battle_id)
                self.redis_client.delete(key)
                self.redis_client.srem("arena:active_battles", battle_id)
                
                # Also remove from fallback
                if battle_id in self.fallback_storage:
                    del self.fallback_storage[battle_id]
                    
                return True
                
            except Exception as e:
                logger.error(f"Failed to delete battle from Redis: {e}")
                
        # Remove from fallback
        if battle_id in self.fallback_storage:
            del self.fallback_storage[battle_id]
            return True
            
        return False
    
    def get_all_battles(self) -> List[BattleSession]:
        """Get all active battle sessions."""
        battles = []
        
        if self.connected:
            try:
                # Get all active battle IDs
                battle_ids = self.redis_client.smembers("arena:active_battles")
                
                for battle_id in battle_ids:
                    battle = self.get_battle(battle_id.decode() if isinstance(battle_id, bytes) else battle_id)
                    if battle:
                        battles.append(battle)
                        
            except Exception as e:
                logger.error(f"Failed to get all battles from Redis: {e}")
        
        # Add fallback battles
        for battle in self.fallback_storage.values():
            if battle.session_id not in [b.session_id for b in battles]:
                battles.append(battle)
                
        return battles


class ELORatingSystem:
    """ELO rating system for model performance tracking."""
    
    def __init__(self, k_factor: float = 32.0, initial_rating: float = 1500.0):
        self.k_factor = k_factor
        self.initial_rating = initial_rating
        self.ratings = {}
        
    def get_rating(self, model: str) -> float:
        """Get current rating for a model."""
        if model not in self.ratings:
            self.ratings[model] = self.initial_rating
        return self.ratings[model]
    
    def update_ratings(self, winner: str, loser: str, is_tie: bool = False) -> Tuple[float, float]:
        """Update ratings after a battle."""
        rating_winner = self.get_rating(winner)
        rating_loser = self.get_rating(loser)
        
        # Calculate expected scores
        expected_winner = 1 / (1 + 10 ** ((rating_loser - rating_winner) / 400))
        expected_loser = 1 / (1 + 10 ** ((rating_winner - rating_loser) / 400))
        
        # Actual scores
        if is_tie:
            score_winner = 0.5
            score_loser = 0.5
        else:
            score_winner = 1.0
            score_loser = 0.0
        
        # Update ratings
        new_rating_winner = rating_winner + self.k_factor * (score_winner - expected_winner)
        new_rating_loser = rating_loser + self.k_factor * (score_loser - expected_loser)
        
        self.ratings[winner] = new_rating_winner
        self.ratings[loser] = new_rating_loser
        
        return new_rating_winner, new_rating_loser


class ArenaManager:
    """Manages LLM battle sessions with Redis storage."""
    
    def __init__(self, models_config: Optional[Dict] = None):
        """Initialize Arena manager with Redis storage."""
        
        # Initialize Redis storage
        self.storage = RedisStorage()
        
        # Keep in-memory dict as secondary cache
        self.battle_sessions = {}
        
        # Configure available models
        if models_config:
            self.available_models = models_config
        else:
            # Default configuration for 5 models
            self.available_models = {
                'llama3.2-3b': {'type': 'ollama', 'display_name': 'Llama 3.1 8B'},
                'phi3-mini': {'type': 'ollama', 'display_name': 'Phi-3 Mini'},
                'gemma2-2b': {'type': 'ollama', 'display_name': 'Gemma 2 2B'},
                'qwen2.5-3b': {'type': 'ollama', 'display_name': 'Qwen 3 8B'},
                'mistral-7b': {'type': 'ollama', 'display_name': 'Mistral 7B'}
            }
        
        # Database tracking
        try:
            self.db_manager = DatabaseManager()
            self.event_logger = EventLogger(self.db_manager)
        except Exception as e:
            logger.warning(f"Could not initialize database tracking: {e}")
            self.db_manager = None
            self.event_logger = None
        
        # Track current view for pagination
        self.current_view_index = 0
        self.models_per_page = 2
        
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
        logger.info(f"Redis storage: {'Connected' if self.storage.connected else 'Using fallback'}")
    
    def get_battle(self, battle_id: str) -> Optional[BattleSession]:
        """
        Get battle from Redis storage (or fallback).
        
        Args:
            battle_id: Battle session ID
            
        Returns:
            BattleSession object or None if not found
        """
        # First try Redis storage
        if self.storage:
            battle = self.storage.get_battle(battle_id)
            if battle:
                # Also cache in memory for faster access
                self.battle_sessions[battle_id] = battle
                return battle
        
        # Fall back to in-memory dict if not in Redis
        return self.battle_sessions.get(battle_id)
    
    @property
    def storage_status(self) -> str:
        """Get current storage status."""
        if self.storage and self.storage.connected:
            return "Redis Connected"
        elif self.storage:
            return "Redis Fallback (In-Memory)"
        else:
            return "In-Memory Only"
    
    def get_model_pair_for_view(self, view_index: int) -> Tuple[str, str]:
        """Get specific model pair based on view index."""
        models = list(self.available_models.keys())
        
        if view_index == 0:
            return models[0], models[1]  # llama3.2-3b vs phi3-mini
        elif view_index == 1:
            return models[2], models[3]  # gemma2-2b vs qwen2.5-3b
        else:
            return models[4], models[0]  # mistral-7b vs llama3.2-3b
    
    def get_random_model_pair(self, exclude_models: Optional[List[str]] = None) -> Tuple[str, str]:
        """Select two random models ensuring equal probability over time."""
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
    
    async def start_battle(self, user_message: str, session_id: Optional[str] = None,
                          view_index: Optional[int] = None) -> Dict[str, Any]:
        """Start a new battle session and store in Redis."""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Select models
        if view_index is not None:
            model_a, model_b = self.get_model_pair_for_view(view_index)
        else:
            model_a, model_b = self.get_random_model_pair()
        
        # Create battle session
        battle = BattleSession(
            session_id=session_id,
            model_a=model_a,
            model_b=model_b,
            user_message=user_message
        )
        
        # Store in Redis (or fallback)
        self.storage.store_battle(battle)
        
        # Also keep in memory for quick access
        self.battle_sessions[session_id] = battle
        
        # Log battle to database
        if self.event_logger:
            self.event_logger.log_arena_battle(
                battle_id=session_id,
                session_id=session_id,
                user_message=user_message,
                model_a=model_a,
                model_b=model_b,
                view_index=view_index
            )
        
        logger.info(f"Started battle {session_id}: {model_a} vs {model_b}")
        
        return {
            'battle_id': session_id,
            'status': 'ready',
            'message': 'Battle session created. Waiting for model responses.',
            'view_index': view_index if view_index is not None else -1,
            'models_hidden': True
        }
    
    async def submit_response(self, battle_id: str, model_position: str, 
                            response: str, latency: float = 0, tokens: int = 0) -> bool:
        """Submit a model's response to a battle."""
        # Get battle from Redis (or memory)
        battle = self.get_battle(battle_id)
        
        if not battle:
            logger.error(f"Battle {battle_id} not found")
            return False
        
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
        
        # Update in Redis
        self.storage.update_battle(battle)
        
        # Update in memory cache
        self.battle_sessions[battle_id] = battle
        
        # Update database
        if self.event_logger:
            self.event_logger.log_arena_battle(
                battle_id=battle_id,
                session_id=battle.session_id,
                user_message=battle.user_message,
                model_a=battle.model_a,
                model_b=battle.model_b,
                response_a=battle.response_a if model_position == 'a' else None,
                response_b=battle.response_b if model_position == 'b' else None,
                latency_a=latency if model_position == 'a' else None,
                latency_b=latency if model_position == 'b' else None,
                tokens_a=tokens if model_position == 'a' else None,
                tokens_b=tokens if model_position == 'b' else None
            )
        
        return True
    
    def record_preference(self, battle_id: str, preference: str) -> Dict[str, Any]:
        """Record user preference and reveal models."""
        battle = self.get_battle(battle_id)
        
        if not battle:
            return {'error': 'Battle not found'}
        
        battle.user_preference = preference
        
        # Update preference stats
        self.preference_stats[preference] += 1
        
        # Update ELO ratings based on preference
        if preference == 'left':
            self.elo_system.update_ratings(battle.model_a, battle.model_b)
        elif preference == 'right':
            self.elo_system.update_ratings(battle.model_b, battle.model_a)
        elif preference == 'tie':
            self.elo_system.update_ratings(battle.model_a, battle.model_b, is_tie=True)
        # 'both_bad' doesn't affect ratings
        
        # Mark battle as completed
        battle.status = 'completed'
        
        # Update in Redis
        self.storage.update_battle(battle)
        
        # Save stats
        self._save_stats()
        
        # Log preference to database
        if self.event_logger:
            self.event_logger.log_arena_battle(
                battle_id=battle_id,
                session_id=battle.session_id,
                user_message=battle.user_message,
                model_a=battle.model_a,
                model_b=battle.model_b,
                preference=preference
            )
        
        return {
            'success': True,
            'models_revealed': {
                'model_a': {
                    'name': battle.model_a,
                    'display_name': self.available_models[battle.model_a]['display_name'],
                    'rating': round(self.elo_system.get_rating(battle.model_a), 1)
                },
                'model_b': {
                    'name': battle.model_b,
                    'display_name': self.available_models[battle.model_b]['display_name'],
                    'rating': round(self.elo_system.get_rating(battle.model_b), 1)
                }
            },
            'preference_recorded': preference
        }
    
    def get_leaderboard(self) -> List[Dict[str, Any]]:
        """Get current model rankings."""
        leaderboard = []
        
        for model in self.available_models:
            rating = self.elo_system.get_rating(model)
            battles = self.model_usage_stats.get(model, 0)
            
            # Calculate win rate from battle history
            wins = 0
            total = 0
            
            # Get all battles from storage
            all_battles = self.storage.get_all_battles() if self.storage else list(self.battle_sessions.values())
            
            for battle in all_battles:
                if battle.user_preference:
                    if battle.model_a == model or battle.model_b == model:
                        total += 1
                        if (battle.model_a == model and battle.user_preference == 'left') or \
                           (battle.model_b == model and battle.user_preference == 'right'):
                            wins += 1
                        elif battle.user_preference == 'tie':
                            wins += 0.5
            
            win_rate = (wins / total * 100) if total > 0 else 0
            
            leaderboard.append({
                'model': model,
                'display_name': self.available_models[model]['display_name'],
                'elo_rating': round(rating, 1),
                'battles_fought': battles,
                'win_rate': round(win_rate, 1)
            })
        
        # Sort by ELO rating
        leaderboard.sort(key=lambda x: x['elo_rating'], reverse=True)
        
        # Add rank
        for i, entry in enumerate(leaderboard):
            entry['rank'] = i + 1
        
        return leaderboard
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive arena statistics."""
        all_battles = self.storage.get_all_battles() if self.storage else list(self.battle_sessions.values())
        total_battles = len(all_battles)
        completed_battles = sum(1 for b in all_battles if b.user_preference)
        
        return {
            'total_battles': total_battles,
            'completed_battles': completed_battles,
            'active_models': len(self.available_models),
            'preference_distribution': dict(self.preference_stats),
            'model_usage': dict(self.model_usage_stats),
            'leaderboard': self.get_leaderboard(),
            'storage_status': self.storage_status
        }
    
    def export_training_data(self, export_type: str = 'dpo', 
                            format_type: str = 'jsonl') -> Dict[str, Any]:
        """Export battle data for model training."""
        all_battles = self.storage.get_all_battles() if self.storage else list(self.battle_sessions.values())
        completed = [b for b in all_battles if b.user_preference]
        
        if export_type == 'dpo':
            # Direct Preference Optimization format
            examples = []
            for battle in completed:
                if battle.user_preference in ['left', 'right']:
                    chosen = battle.response_a if battle.user_preference == 'left' else battle.response_b
                    rejected = battle.response_b if battle.user_preference == 'left' else battle.response_a
                    
                    examples.append({
                        'prompt': battle.user_message,
                        'chosen': chosen,
                        'rejected': rejected,
                        'metadata': {
                            'chosen_model': battle.model_a if battle.user_preference == 'left' else battle.model_b,
                            'rejected_model': battle.model_b if battle.user_preference == 'left' else battle.model_a,
                            'timestamp': battle.timestamp.isoformat()
                        }
                    })
            
            # Save to file
            filename = f"arena_dpo_export_{int(time.time())}.{format_type}"
            filepath = f"instance/exports/{filename}"
            
            os.makedirs("instance/exports", exist_ok=True)
            
            if format_type == 'jsonl':
                with open(filepath, 'w') as f:
                    for example in examples:
                        f.write(json.dumps(example) + '\n')
            else:
                with open(filepath, 'w') as f:
                    json.dump(examples, f, indent=2)
            
            return {
                'success': True,
                'file_path': filepath,
                'export_type': export_type,
                'format': format_type,
                'battles_included': len(completed),
                'examples_generated': len(examples)
            }
        
        return {'success': False, 'error': f'Export type {export_type} not implemented'}
    
    def _load_stats(self):
        """Load persisted statistics."""
        try:
            stats_file = 'instance/arena_stats.json'
            if os.path.exists(stats_file):
                with open(stats_file, 'r') as f:
                    data = json.load(f)
                    self.elo_system.ratings = data.get('elo_ratings', {})
                    self.model_usage_stats = data.get('model_usage', self.model_usage_stats)
                    self.preference_stats = data.get('preferences', self.preference_stats)
        except Exception as e:
            logger.warning(f"Could not load arena stats: {e}")
    
    def _save_stats(self):
        """Save statistics to file."""
        try:
            os.makedirs('instance', exist_ok=True)
            stats_file = 'instance/arena_stats.json'
            with open(stats_file, 'w') as f:
                json.dump({
                    'elo_ratings': self.elo_system.ratings,
                    'model_usage': self.model_usage_stats,
                    'preferences': self.preference_stats
                }, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save arena stats: {e}")
