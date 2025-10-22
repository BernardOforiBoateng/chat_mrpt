#!/usr/bin/env python3
"""Test the arena tournament logic with 5 models."""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from datetime import datetime

@dataclass
class ProgressiveBattleSession:
    """Test version of ProgressiveBattleSession."""
    session_id: str
    user_message: str
    all_models: List[str]
    all_responses: Dict[str, str] = field(default_factory=dict)
    comparison_history: List[Dict] = field(default_factory=list)
    current_round: int = 0
    current_pair: Tuple[str, str] = None
    eliminated_models: List[str] = field(default_factory=list)
    winner_chain: List[str] = field(default_factory=list)
    remaining_models: List[str] = field(default_factory=list)
    final_ranking: List[str] = field(default_factory=list)
    completed: bool = False

    def get_next_matchup(self) -> Optional[Tuple[str, str]]:
        """Get the next pair of models to compare."""
        if self.current_round == 0:
            # First round: show first two models
            if len(self.remaining_models) >= 2:
                return (self.remaining_models[0], self.remaining_models[1])
        else:
            # Subsequent rounds: winner vs next challenger
            if self.winner_chain and len(self.remaining_models) >= 2:
                current_winner = self.winner_chain[-1]

                # Find models that haven't competed yet
                # A model has competed if it's in winner_chain or eliminated_models
                models_that_competed = set(self.winner_chain + self.eliminated_models)
                unused_models = [m for m in self.all_models if m not in models_that_competed]

                print(f"Round {self.current_round + 1} matchup selection:")
                print(f"  Current winner: {current_winner}")
                print(f"  Models that competed: {models_that_competed}")
                print(f"  Unused models: {unused_models}")

                # If there are unused models, pick the first one
                if unused_models:
                    challenger = unused_models[0]
                    print(f"  Selected challenger: {challenger}")
                    return (current_winner, challenger)
                else:
                    # All models have competed - this shouldn't happen in progressive
                    print(f"All models have competed but tournament not complete")
                    # Fallback: find any model that isn't the current winner
                    for model in self.remaining_models:
                        if model != current_winner:
                            return (current_winner, model)
        return None

    def record_choice(self, choice: str) -> bool:
        """Record user's choice and update state."""
        if not self.current_pair:
            return False
            
        model_a, model_b = self.current_pair
        
        # Determine winner and loser
        if choice == 'left':
            winner = model_a
            loser = model_b
        else:  # 'right'
            winner = model_b
            loser = model_a
            
        # Update state
        if winner not in self.winner_chain:
            self.winner_chain.append(winner)
        self.eliminated_models.append(loser)
        
        # Remove only the loser from remaining models
        if loser in self.remaining_models:
            self.remaining_models.remove(loser)
        
        # Check if more comparisons needed
        self.current_round += 1

        # Log current state
        print(f"\nRound {self.current_round} complete:")
        print(f"  Winner: {winner}, Loser: {loser}")
        print(f"  Winner chain: {self.winner_chain}")
        print(f"  Eliminated: {self.eliminated_models}")
        print(f"  Remaining: {self.remaining_models}")

        # Progressive tournament: need num_models - 1 rounds total
        expected_rounds = len(self.all_models) - 1
        if self.current_round < expected_rounds and len(self.remaining_models) > 1:
            # Set up next matchup
            self.current_pair = self.get_next_matchup()
            if self.current_pair:
                print(f"  Next matchup: {self.current_pair[0]} vs {self.current_pair[1]}")
                return True
            else:
                print(f"  ERROR: Could not get next matchup")

        # Tournament complete
        self.completed = True
        # Build final ranking: last winner is #1, then eliminated models in reverse order
        if self.winner_chain:
            champion = self.winner_chain[-1]
            self.final_ranking = [champion] + self.eliminated_models[::-1]
        else:
            self.final_ranking = self.eliminated_models[::-1]
        print(f"\nTournament complete! Final ranking: {self.final_ranking}")
        return False


def test_5_model_tournament():
    """Test a tournament with 5 models."""
    print("Testing 5-Model Progressive Tournament")
    print("=" * 50)
    
    models = ["gemma2:9b", "qwen2.5:7b", "phi3:mini", "llama3.1:8b", "mistral:7b"]
    
    # Create battle session
    battle = ProgressiveBattleSession(
        session_id="test-123",
        user_message="hi",
        all_models=models,
        remaining_models=models.copy()
    )
    
    # Get initial matchup
    battle.current_pair = battle.get_next_matchup()
    print(f"\nInitial matchup: {battle.current_pair[0]} vs {battle.current_pair[1]}")
    
    # Simulate tournament
    round_num = 1
    choices = ['right', 'left', 'right', 'left']  # Simulate user choices
    
    for choice in choices:
        print(f"\n{'='*30}")
        print(f"ROUND {round_num}: {battle.current_pair[0]} vs {battle.current_pair[1]}")
        print(f"User chooses: {choice}")
        
        has_more = battle.record_choice(choice)
        
        if not has_more:
            print("\nTournament ended!")
            break
        round_num += 1
    
    print(f"\n{'='*50}")
    print("TOURNAMENT SUMMARY")
    print(f"Total rounds played: {battle.current_round}")
    print(f"Expected rounds for {len(models)} models: {len(models) - 1}")
    print(f"All models participated: {set(battle.winner_chain + battle.eliminated_models) == set(models)}")
    print(f"Final ranking: {battle.final_ranking}")


if __name__ == "__main__":
    test_5_model_tournament()