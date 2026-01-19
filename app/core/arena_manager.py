"""
LLM Arena Manager with Redis Storage
Manages battle sessions with distributed Redis storage for multi-worker environments
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


@dataclass
class ProgressiveBattleSession:
    """Represents a progressive battle session with multiple models."""
    session_id: str
    user_message: str
    all_models: List[str]  # All models to compare (e.g., 3 or 5)
    all_responses: Dict[str, str] = field(default_factory=dict)  # model -> response
    all_latencies: Dict[str, float] = field(default_factory=dict)  # model -> latency
    comparison_history: List[Dict] = field(default_factory=list)  # History of comparisons
    current_round: int = 0
    current_pair: Tuple[str, str] = None  # Current models being compared
    eliminated_models: List[str] = field(default_factory=list)
    winner_chain: List[str] = field(default_factory=list)  # Winners in order
    remaining_models: List[str] = field(default_factory=list)
    final_ranking: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    completed: bool = False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for Redis storage."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        # Handle tuple serialization
        if self.current_pair:
            data['current_pair'] = list(self.current_pair)
        # Ensure all_responses is properly serialized
        if self.all_responses:
            data['all_responses'] = dict(self.all_responses)
            logger.info(f"Serializing {len(self.all_responses)} responses: {list(self.all_responses.keys())}")
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ProgressiveBattleSession':
        """Create instance from dictionary."""
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        # Handle tuple deserialization
        if 'current_pair' in data and isinstance(data['current_pair'], list):
            data['current_pair'] = tuple(data['current_pair']) if data['current_pair'] else None
        # Ensure all_responses is properly deserialized
        if 'all_responses' in data and data['all_responses']:
            logger.info(f"Deserializing {len(data['all_responses'])} responses: {list(data['all_responses'].keys())}")
        return cls(**data)
    
    def get_next_matchup(self) -> Optional[Tuple[str, str]]:
        """Get the next pair of models to compare following tournament structure."""
        # Tournament structure:
        # Round 1: Model A vs Model B (first two local models - NEVER gpt-4o)
        # Round 2: Winner vs Model C (third local model - NEVER gpt-4o)
        # Round 3: Winner vs Model D (gpt-4o - final challenger)

        # Check if Model D (gpt-4o) is in the tournament
        has_model_d = 'gpt-4o' in self.all_models
        model_d_position = self.all_models.index('gpt-4o') if has_model_d else -1

        if self.current_round == 0:
            # First round: ALWAYS use first two NON-GPT-4O models
            # CRITICAL: gpt-4o should NEVER appear in round 1
            local_models = [m for m in self.all_models if m != 'gpt-4o']

            if len(local_models) >= 2:
                logger.info(f"Round 1 matchup: {local_models[0]} vs {local_models[1]} (excluding gpt-4o)")
                return (local_models[0], local_models[1])
            elif len(self.all_models) >= 2:
                # Fallback if somehow we don't have enough non-gpt-4o models
                logger.warning(f"Not enough local models for round 1, using first two available")
                return (self.all_models[0], self.all_models[1])
        else:
            # Subsequent rounds: winner vs next challenger
            if self.winner_chain:
                current_winner = self.winner_chain[-1]

                # Find models that haven't competed yet
                models_that_competed = set(self.winner_chain + self.eliminated_models)
                unused_models = [m for m in self.all_models if m not in models_that_competed]

                logger.info(f"Round {self.current_round + 1} matchup selection:")
                logger.info(f"  Current winner: {current_winner}")
                logger.info(f"  Models that competed: {models_that_competed}")
                logger.info(f"  Unused models: {unused_models}")

                # CRITICAL: Model D (gpt-4o) should ONLY appear in the FINAL round
                if has_model_d and 'gpt-4o' in unused_models:
                    # Check if this is the final round (only Model D left unused)
                    unused_local_models = [m for m in unused_models if m != 'gpt-4o']

                    if len(unused_local_models) == 0:
                        # This is the final round - all local models have competed
                        logger.info(f"  ✅ FINAL ROUND: {current_winner} vs Model D (gpt-4o)")
                        return (current_winner, 'gpt-4o')
                    else:
                        # NOT the final round yet - use a local model challenger
                        challenger = unused_local_models[0]
                        logger.info(f"  Round {self.current_round + 1}: {current_winner} vs {challenger} (saving Model D for final)")
                        return (current_winner, challenger)
                else:
                    # Regular selection: pick first unused model
                    if unused_models:
                        challenger = unused_models[0]
                        logger.info(f"  Selected challenger: {challenger}")
                        return (current_winner, challenger)

        return None
    
    def record_choice(self, choice: str) -> bool:
        """Record user's choice and update state. Returns True if more comparisons needed."""
        if not self.current_pair:
            return False
            
        model_a, model_b = self.current_pair
        
        # Record comparison
        comparison = {
            'round': self.current_round,
            'model_a': model_a,
            'model_b': model_b,
            'choice': choice,
            'timestamp': datetime.now().isoformat()
        }
        self.comparison_history.append(comparison)
        
        # Determine winner and loser
        if choice == 'left':
            winner = model_a
            loser = model_b
        elif choice == 'right':
            winner = model_b
            loser = model_a
        else:  # tie - randomly pick winner for now
            import random
            winner = model_a if random.random() > 0.5 else model_b
            loser = model_b if winner == model_a else model_a
        
        # Update state
        if winner not in self.winner_chain:
            self.winner_chain.append(winner)
        self.eliminated_models.append(loser)
        
        # Remove only the loser from remaining models (winner stays for next round)
        if loser in self.remaining_models:
            self.remaining_models.remove(loser)
        
        # Check if more comparisons needed
        self.current_round += 1

        # Log current state for debugging
        logger.info(f"Round {self.current_round} complete. Winner chain: {self.winner_chain}, "
                   f"Eliminated: {self.eliminated_models}, Remaining: {self.remaining_models}")

        # Progressive tournament: need num_models - 1 rounds total
        # Continue if we haven't had all models compete yet
        expected_rounds = len(self.all_models) - 1
        if self.current_round < expected_rounds and len(self.remaining_models) > 1:
            # Set up next matchup
            self.current_pair = self.get_next_matchup()
            if self.current_pair:
                logger.info(f"Next matchup for round {self.current_round + 1}: {self.current_pair}")
                return True
            else:
                logger.warning(f"Could not get next matchup despite having {len(self.remaining_models)} models remaining")

        # Tournament complete
        self.completed = True
        # Build final ranking: last winner is #1, then eliminated models in reverse order
        if self.winner_chain:
            # The last winner is the champion
            champion = self.winner_chain[-1]
            # Get eliminated models in reverse order (most recent eliminated = higher rank)
            self.final_ranking = [champion] + self.eliminated_models[::-1]
        else:
            self.final_ranking = self.eliminated_models[::-1]
        logger.info(f"Tournament complete after {self.current_round} rounds. Final ranking: {self.final_ranking}")
        return False


class RedisStorage:
    """Redis storage backend for battle sessions."""
    
    def __init__(self, redis_host: str = None, redis_port: int = 6379, 
                 redis_password: str = None, redis_db: int = 1):
        """
        Initialize Redis storage.
        
        Args:
            redis_host: Redis server host
            redis_port: Redis server port
            redis_password: Redis password (optional)
            redis_db: Redis database number (default 1 to avoid conflict with Flask sessions)
        """
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
    
    def _get_progressive_key(self, session_id: str) -> str:
        """Generate Redis key for progressive battle."""
        return f"arena:progressive:{session_id}"
    
    def store_battle(self, battle: BattleSession, ttl_hours: int = 24) -> bool:
        """
        Store battle session in Redis.
        
        Args:
            battle: BattleSession object to store
            ttl_hours: Time to live in hours (default 24)
            
        Returns:
            True if stored successfully
        """
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
        """
        Retrieve battle session from Redis.
        
        Args:
            battle_id: Battle session ID
            
        Returns:
            BattleSession object or None if not found
        """
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
        """
        Delete battle session from Redis.
        
        Args:
            battle_id: Battle session ID
            
        Returns:
            True if deleted successfully
        """
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
    
    def count_battles(self) -> int:
        """Count total number of battles."""
        if self.connected:
            try:
                redis_count = self.redis_client.scard("arena:active_battles")
                fallback_count = len(self.fallback_storage)
                return max(redis_count, fallback_count)
            except:
                pass
        
        return len(self.fallback_storage)
    
    def store_progressive_battle(self, battle: ProgressiveBattleSession, ttl_hours: int = 24) -> bool:
        """Store progressive battle session in Redis."""
        key = self._get_progressive_key(battle.session_id)
        
        if self.connected:
            try:
                battle_json = json.dumps(battle.to_dict())
                self.redis_client.setex(
                    key,
                    timedelta(hours=ttl_hours),
                    battle_json
                )
                self.redis_client.sadd("arena:progressive_battles", battle.session_id)
                return True
            except Exception as e:
                logger.error(f"Failed to store progressive battle in Redis: {e}")
                self.fallback_storage[f"prog_{battle.session_id}"] = battle
                return True
        else:
            self.fallback_storage[f"prog_{battle.session_id}"] = battle
            return True
    
    def get_progressive_battle(self, session_id: str) -> Optional[ProgressiveBattleSession]:
        """Retrieve progressive battle session from Redis."""
        if self.connected:
            try:
                key = self._get_progressive_key(session_id)
                battle_json = self.redis_client.get(key)
                
                if battle_json:
                    battle_dict = json.loads(battle_json)
                    return ProgressiveBattleSession.from_dict(battle_dict)
                
                if f"prog_{session_id}" in self.fallback_storage:
                    return self.fallback_storage[f"prog_{session_id}"]
                    
                return None
            except Exception as e:
                logger.error(f"Failed to retrieve progressive battle from Redis: {e}")
                return self.fallback_storage.get(f"prog_{session_id}")
        else:
            return self.fallback_storage.get(f"prog_{session_id}")
    
    def update_progressive_battle(self, battle: ProgressiveBattleSession) -> bool:
        """Update existing progressive battle session."""
        return self.store_progressive_battle(battle)
    
    def cleanup_expired(self) -> int:
        """Clean up expired battles (called periodically)."""
        cleaned = 0
        
        if self.connected:
            try:
                # Get all active battle IDs
                battle_ids = self.redis_client.smembers("arena:active_battles")
                
                for battle_id in battle_ids:
                    key = self._get_key(battle_id.decode() if isinstance(battle_id, bytes) else battle_id)
                    
                    # Check if key still exists (not expired)
                    if not self.redis_client.exists(key):
                        self.redis_client.srem("arena:active_battles", battle_id)
                        cleaned += 1
                        
            except Exception as e:
                logger.error(f"Failed to cleanup expired battles: {e}")
        
        return cleaned


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
    Manages LLM battle sessions with Redis storage for multi-worker support.
    
    Features:
    - Distributed battle storage using Redis
    - Random model pairing with equal probability
    - Blind testing (models hidden until vote)
    - ELO rating system
    - Session management across multiple workers
    """
    
    def __init__(self, models_config: Optional[Dict] = None):
        """
        Initialize Arena Manager with Redis storage.
        
        Args:
            models_config: Configuration for available models
        """
        # Initialize interaction tracking
        self.db_manager = DatabaseManager()
        self.event_logger = EventLogger(self.db_manager)
        
        # Initialize Redis storage
        self.storage = RedisStorage()
        
        # FINAL: Use the correct models that are actually installed
        self.available_models = models_config or {
            'mistral:7b': {
                'type': 'ollama',
                'display_name': 'Mistral 7B',
                'port': 11434,
                'huggingface': 'mistralai/Mistral-7B-Instruct-v0.2',
                'strengths': 'Fast and accurate with strong performance across tasks'
            },
            'llama3.1:8b': {
                'type': 'ollama',
                'display_name': 'Llama 3.1 8B',
                'port': 11434,
                'huggingface': 'meta-llama/Llama-3.1-8B-Instruct',
                'strengths': 'Meta\'s latest model with strong reasoning capabilities'
            },
            'qwen3:8b': {  # FIXED: Correct model name
                'type': 'ollama',
                'display_name': 'Qwen3 8B',
                'port': 11434,
                'huggingface': 'Qwen/Qwen-8B-Instruct',
                'strengths': 'Alibaba\'s model with excellent performance'

            }
        }
        
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
        
        # Log battle to database
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
        # Get battle from Redis
        battle = self.storage.get_battle(battle_id)
        
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
        
        # Update database
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
        """Record user's preference for a battle."""
        # Get battle from Redis
        battle = self.storage.get_battle(battle_id)
        
        if not battle:
            return {'error': 'Battle session not found'}
        
        battle.user_preference = preference
        
        # Update preference stats
        self.preference_stats[preference] += 1
        
        # Get ELO ratings before update
        elo_before_a = self.elo_system.get_rating(battle.model_a)
        elo_before_b = self.elo_system.get_rating(battle.model_b)
        
        # Update ELO ratings
        if preference == 'left':
            self.elo_system.update_ratings(battle.model_a, battle.model_b)
        elif preference == 'right':
            self.elo_system.update_ratings(battle.model_b, battle.model_a)
        elif preference == 'tie':
            self.elo_system.update_ratings(battle.model_a, battle.model_b, is_tie=True)
        
        # Get ELO ratings after update
        elo_after_a = self.elo_system.get_rating(battle.model_a)
        elo_after_b = self.elo_system.get_rating(battle.model_b)
        
        # Update battle in Redis
        self.storage.update_battle(battle)
        
        # Log preference to database
        self.event_logger.log_arena_battle(
            battle_id=battle_id,
            session_id=battle.session_id,
            user_message=battle.user_message,
            model_a=battle.model_a,
            model_b=battle.model_b,
            user_preference=preference,
            elo_before_a=elo_before_a,
            elo_before_b=elo_before_b,
            elo_after_a=elo_after_a,
            elo_after_b=elo_after_b
        )
        
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
    
    def get_battle(self, battle_id: str) -> Optional[BattleSession]:
        """
        Get battle session by ID.
        Delegates to storage backend.
        """
        return self.storage.get_battle(battle_id)
    
    def update_battle(self, battle: BattleSession) -> bool:
        """
        Update battle session in storage.
        Delegates to storage backend.
        """
        return self.storage.update_battle(battle)
    
    def store_progressive_battle(self, battle: 'ProgressiveBattleSession', ttl_hours: int = 24) -> bool:
        """
        Store a progressive battle session.
        Delegates to storage backend.
        """
        return self.storage.store_progressive_battle(battle, ttl_hours)
    
    def get_leaderboard(self) -> List[Dict[str, Any]]:
        """Get current model leaderboard sorted by ELO rating."""
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
                'rank': 0,
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
        """Get comprehensive arena statistics."""
        # Get all battles from Redis
        all_battles = self.storage.get_all_battles()
        total_battles = len(all_battles)
        completed_battles = sum(1 for b in all_battles if b.user_preference is not None)
        
        return {
            'total_battles': total_battles,
            'completed_battles': completed_battles,
            'completion_rate': (completed_battles / total_battles * 100) if total_battles > 0 else 0,
            'preference_distribution': self.preference_stats,
            'model_usage': self.model_usage_stats,
            'leaderboard': self.get_leaderboard(),
            'active_models': len(self.available_models),
            'models_per_page': self.models_per_page,
            'total_views': 3,
            'storage_status': 'Redis' if self.storage.connected else 'In-Memory Fallback'
        }
    
    def _save_stats(self):
        """Save statistics to disk for persistence."""
        stats_file = 'instance/arena_stats.json'
        os.makedirs('instance', exist_ok=True)
        
        try:
            with open(stats_file, 'w') as f:
                json.dump({
                    'elo_ratings': self.elo_system.ratings,
                    'match_history': self.elo_system.match_history[-1000:],
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
    
    def export_training_data(self, export_type='dpo', format='jsonl'):
        """Export battle data for model training."""
        return self.event_logger.export_arena_training_data(export_type, format)
    
    async def start_progressive_battle(self, user_message: str, num_models: int = 3,
                                      session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Start a new progressive battle session with multiple models.
        Model D is ALWAYS OpenAI (gpt-4o) for the final challenge.

        Args:
            user_message: The user's query
            num_models: Number of models to compare (default 3)
            session_id: Optional session ID

        Returns:
            Battle initialization info
        """
        if not session_id:
            session_id = str(uuid.uuid4())

        # Tournament structure: 3 local models compete, winner faces Model D (OpenAI)
        # Models A, B, C are local Ollama models
        # Model D is ALWAYS OpenAI (gpt-4o)

        # FIXED: Use correct model name qwen3:8b (not qwen:8b)
        local_models = ['mistral:7b', 'qwen3:8b', 'llama3.1:8b']

        # Check which local models are available
        available = list(self.available_models.keys())
        selected_models = []

        # Select local models (A, B, C) - EXPLICITLY EXCLUDE gpt-4o
        for model in local_models:
            if model in available and model != 'gpt-4o':
                selected_models.append(model)

        # Ensure we have at least 3 local models
        if len(selected_models) < 3:
            logger.warning(f"Only {len(selected_models)} local models available")
            # Fill with any other available models (EXCLUDING gpt-4o)
            for model in available:
                if model not in selected_models and model != 'gpt-4o' and len(selected_models) < 3:
                    selected_models.append(model)

        # Randomize the first 3 (local models) for variety
        # This happens BEFORE adding Model D
        if len(selected_models) >= 2:
            import random
            # Shuffle only the local models
            random.shuffle(selected_models)

        # IMPORTANT: Only add OpenAI as Model D AFTER shuffling local models
        # This ensures gpt-4o is ALWAYS in the last position
        if num_models >= 4:
            # Ensure we have exactly 3 local models
            selected_models = selected_models[:3]

            # Check if OpenAI is available
            if 'gpt-4o' in available:
                selected_models.append('gpt-4o')  # Model D is ALWAYS LAST
                logger.info(f"✅ Tournament structure: {selected_models[:3]} (local) + {selected_models[3]} (Model D)")
            else:
                # If OpenAI not configured, still try to add it for Model D
                selected_models.append('gpt-4o')
                logger.warning("⚠️ Model D (gpt-4o) added but may not be configured - check OPENAI_API_KEY")

        logger.info(f"Final tournament models: {selected_models}")
        logger.info(f"Model D (gpt-4o) position: {selected_models.index('gpt-4o') if 'gpt-4o' in selected_models else 'Not in tournament'}")
        
        # Create progressive battle session
        battle = ProgressiveBattleSession(
            session_id=session_id,
            user_message=user_message,
            all_models=selected_models,
            remaining_models=selected_models.copy()
        )
        
        # Get initial matchup
        battle.current_pair = battle.get_next_matchup()
        
        # Store in Redis
        self.storage.store_progressive_battle(battle)
        
        logger.info(f"Started progressive battle {session_id} with models: {selected_models}")
        
        return {
            'battle_id': session_id,
            'status': 'initialized',
            'total_models': num_models,
            'current_round': 0,
            'message': 'Progressive battle session created'
        }
    
    async def get_all_model_responses(self, battle_id: str) -> Dict[str, Any]:
        """
        Get responses from all models in a progressive battle.
        Optimized: Load all models in parallel with proper timeouts and GPU support.
        """
        battle = self.storage.get_progressive_battle(battle_id)
        if not battle:
            return {'error': 'Battle session not found'}

        # Determine the current matchup models
        if battle.current_pair:
            model_a, model_b = battle.current_pair
        else:
            # Use first two NON-GPT-4O models for initial round
            local_models = [m for m in battle.all_models if m != 'gpt-4o']
            model_a = local_models[0] if len(local_models) > 0 else battle.all_models[0]
            model_b = local_models[1] if len(local_models) > 1 else battle.all_models[1]
            battle.current_pair = (model_a, model_b)

        # Check if responses are already cached
        if len(battle.all_responses) == len(battle.all_models):
            logger.info(f"All {len(battle.all_models)} responses already cached, returning immediately")

            return {
                'battle_id': battle_id,
                'current_round': battle.current_round,
                'model_a': model_a,
                'model_b': model_b,
                'response_a': battle.all_responses.get(model_a, ''),
                'response_b': battle.all_responses.get(model_b, ''),
                'latency_a': battle.all_latencies.get(model_a, 0),
                'latency_b': battle.all_latencies.get(model_b, 0),
                'all_cached': True
            }

        # Import adapters for different model types
        from app.core.ollama_adapter import OllamaAdapter
        from app.core.llm_adapter import LLMAdapter
        from app.core.arena_system_prompt import get_arena_system_prompt

        # Get enhanced system prompt
        system_prompt = get_arena_system_prompt()

        # Check for GPU instance availability
        import os
        gpu_host = os.environ.get('AWS_OLLAMA_HOST', os.environ.get('OLLAMA_HOST'))
        if gpu_host:
            logger.info(f"🚀 Using GPU instance at {gpu_host} for faster inference")
            ollama_adapter = OllamaAdapter(base_url=f"http://{gpu_host}:11434")
        else:
            logger.info("Using local Ollama instance")
            ollama_adapter = OllamaAdapter()

        # Fetch responses from all models in parallel
        async def get_model_response(model_name: str):
            try:
                start_time = time.time()

                # Check if it's an OpenAI model
                model_info = self.available_models.get(model_name, {})
                if model_info.get('type') == 'openai':
                    # Use LLMAdapter for OpenAI
                    adapter = LLMAdapter(backend='openai', model=model_name)
                    response = adapter.generate(
                        prompt=f"{system_prompt}\n\nUser: {battle.user_message}\nAssistant:",
                        max_tokens=800,
                        temperature=0.7
                    )
                else:
                    # Use Ollama for local models with enhanced prompt
                    full_prompt = f"{system_prompt}\n\nUser: {battle.user_message}\nAssistant:"
                    response = await ollama_adapter.generate_async(
                        model_name,
                        full_prompt,
                        temperature=0.7,
                        max_tokens=800
                    )

                latency = (time.time() - start_time) * 1000
                logger.info(f"✓ {model_name} responded in {latency:.0f}ms ({len(response)} chars)")
                return model_name, response, latency

            except asyncio.TimeoutError:
                logger.error(f"Timeout getting response from {model_name}")
                return model_name, f"Error: Model {model_name} timed out", 0
            except Exception as e:
                logger.error(f"Error getting response from {model_name}: {e}")
                return model_name, f"Error: {str(e)}", 0

        # Load all models in parallel with individual timeouts
        logger.info(f"Pre-loading {len(battle.all_models)} models in parallel: {battle.all_models}")

        # Create tasks with timeout wrapper
        tasks = []
        for model in battle.all_models:
            # Skip if already cached
            if model in battle.all_responses and battle.all_responses[model]:
                logger.info(f"Skipping {model} - already cached")
                continue
            # Set per-model timeout (15s for most, 30s for OpenAI)
            timeout = 30 if self.available_models.get(model, {}).get('type') == 'openai' else 15
            task = asyncio.wait_for(get_model_response(model), timeout=timeout)
            tasks.append(task)

        # Execute all tasks in parallel
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            results = []

        # Process results and store responses in battle session
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Task exception: {result}")
                continue
            if isinstance(result, tuple) and len(result) == 3:
                model_name, response, latency = result
                battle.all_responses[model_name] = response
                battle.all_latencies[model_name] = latency
        
        # Update battle in storage
        self.storage.update_progressive_battle(battle)
        
        # Return current pair's responses
        if battle.current_pair:
            model_a, model_b = battle.current_pair
            return {
                'battle_id': battle_id,
                'current_round': battle.current_round,
                'model_a': model_a,
                'model_b': model_b,
                'response_a': battle.all_responses.get(model_a, ''),
                'response_b': battle.all_responses.get(model_b, ''),
                'latency_a': battle.all_latencies.get(model_a, 0),
                'latency_b': battle.all_latencies.get(model_b, 0),
                'remaining_comparisons': len(battle.remaining_models)
            }
        
        return {'error': 'No models to compare'}
    
    def submit_progressive_choice(self, battle_id: str, choice: str) -> Dict[str, Any]:
        """
        Submit user's choice in a progressive battle and get next matchup.
        
        Args:
            battle_id: Progressive battle session ID
            choice: 'left', 'right', or 'tie'
            
        Returns:
            Next matchup info or final results
        """
        battle = self.storage.get_progressive_battle(battle_id)
        if not battle:
            return {'error': 'Battle session not found'}
        
        # Record the choice
        more_comparisons = battle.record_choice(choice)
        
        # Update ELO ratings for the comparison
        if battle.current_pair and choice in ['left', 'right']:
            model_a, model_b = battle.current_pair
            if choice == 'left':
                self.elo_system.update_ratings(model_a, model_b)
            else:
                self.elo_system.update_ratings(model_b, model_a)
        
        # Save updated battle
        self.storage.update_progressive_battle(battle)
        
        if more_comparisons and battle.current_pair:
            # Return next matchup
            model_a, model_b = battle.current_pair
            return {
                'status': 'continue',
                'current_round': battle.current_round,
                'model_a': model_a,
                'model_b': model_b,
                'response_a': battle.all_responses.get(model_a, ''),
                'response_b': battle.all_responses.get(model_b, ''),
                'latency_a': battle.all_latencies.get(model_a, 0),
                'latency_b': battle.all_latencies.get(model_b, 0),
                'remaining_comparisons': len(battle.remaining_models),
                'eliminated_model': battle.eliminated_models[-1] if battle.eliminated_models else None
            }
        else:
            # All comparisons done, return final ranking
            return {
                'status': 'completed',
                'final_ranking': battle.final_ranking,
                'comparison_history': battle.comparison_history,
                'winner': battle.winner_chain[0] if battle.winner_chain else None,
                'total_rounds': battle.current_round
            }