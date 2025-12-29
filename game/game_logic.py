"""
Game Logic Module - Extended Rock Paper Scissors

Elements and their relationships:
- Rock: Crushes Scissors, Lizard, Fire
- Paper: Covers Rock, Air, Water
- Scissors: Cuts Paper, Air, Lizard
- Fire: Burns Paper, Scissors, Air, Lizard
- Water: Extinguishes Fire, Erodes Rock, Drowns Lizard
- Air: Blows away Paper, Fans Fire, Suffocates Lizard
- Lizard: Eats Paper, Poisons Rock, Breathes Air
- Gun: Shoots Rock, Scissors, Fire, Lizard, Air
- Lightning: Strikes Water, Gun, Scissors
- Shield: Blocks Gun, Rock, Scissors
"""

import random
from collections import Counter


# Define all elements and what they beat
ELEMENTS = {
    'rock': {
        'emoji': '🪨',
        'beats': ['scissors', 'lizard', 'fire'],
        'description': 'Crushes Scissors, Lizard, and Fire'
    },
    'paper': {
        'emoji': '📄',
        'beats': ['rock', 'air', 'water'],
        'description': 'Covers Rock, Air, and Water'
    },
    'scissors': {
        'emoji': '✂️',
        'beats': ['paper', 'air', 'lizard'],
        'description': 'Cuts Paper, Air, and Lizard'
    },
    'fire': {
        'emoji': '🔥',
        'beats': ['paper', 'scissors', 'air', 'lizard'],
        'description': 'Burns Paper, Scissors, Air, and Lizard'
    },
    'water': {
        'emoji': '💧',
        'beats': ['fire', 'rock', 'lizard', 'gun'],
        'description': 'Extinguishes Fire, Erodes Rock, Drowns Lizard, Rusts Gun'
    },
    'air': {
        'emoji': '💨',
        'beats': ['fire', 'rock', 'water'],
        'description': 'Suffocates Fire, Erodes Rock, Evaporates Water'
    },
    'lizard': {
        'emoji': '🦎',
        'beats': ['paper', 'air', 'lightning'],
        'description': 'Eats Paper, Breathes Air, Grounds Lightning'
    },
    'gun': {
        'emoji': '🔫',
        'beats': ['rock', 'scissors', 'fire', 'lizard', 'air', 'lightning'],
        'description': 'Shoots everything except Water and Shield'
    },
    'lightning': {
        'emoji': '⚡',
        'beats': ['water', 'scissors', 'gun', 'fire'],
        'description': 'Strikes Water, Scissors, Gun, and Fire'
    },
    'shield': {
        'emoji': '🛡️',
        'beats': ['gun', 'rock', 'scissors', 'lightning'],
        'description': 'Blocks Gun, Rock, Scissors, and Lightning'
    }
}

# Element sets for different game modes
CLASSIC_ELEMENTS = ['rock', 'paper', 'scissors']
EXTENDED_ELEMENTS = ['rock', 'paper', 'scissors', 'fire', 'water']
FULL_ELEMENTS = list(ELEMENTS.keys())


def get_elements_for_mode(mode='classic'):
    """Get elements based on game mode"""
    if mode == 'classic':
        return CLASSIC_ELEMENTS
    elif mode == 'extended':
        return EXTENDED_ELEMENTS
    else:  # full
        return FULL_ELEMENTS


def determine_winner(player_choice, ai_choice):
    """
    Determine the winner of a round
    Returns: 'win' (player wins), 'lose' (AI wins), 'draw'
    """
    if player_choice == ai_choice:
        return 'draw'
    
    player_beats = ELEMENTS.get(player_choice, {}).get('beats', [])
    
    if ai_choice in player_beats:
        return 'win'
    else:
        return 'lose'


def get_win_reason(winner_choice, loser_choice):
    """Get a description of why one element beats another"""
    winner_data = ELEMENTS.get(winner_choice, {})
    descriptions = {
        ('rock', 'scissors'): 'Rock crushes Scissors!',
        ('rock', 'lizard'): 'Rock crushes Lizard!',
        ('rock', 'fire'): 'Rock smothers Fire!',
        ('paper', 'rock'): 'Paper covers Rock!',
        ('paper', 'air'): 'Paper catches Air!',
        ('paper', 'water'): 'Paper absorbs Water!',
        ('scissors', 'paper'): 'Scissors cuts Paper!',
        ('scissors', 'air'): 'Scissors cuts through Air!',
        ('scissors', 'lizard'): 'Scissors decapitates Lizard!',
        ('fire', 'paper'): 'Fire burns Paper!',
        ('fire', 'scissors'): 'Fire melts Scissors!',
        ('fire', 'air'): 'Fire consumes Air!',
        ('fire', 'lizard'): 'Fire roasts Lizard!',
        ('water', 'fire'): 'Water extinguishes Fire!',
        ('water', 'rock'): 'Water erodes Rock!',
        ('water', 'lizard'): 'Water drowns Lizard!',
        ('water', 'gun'): 'Water rusts Gun!',
        ('air', 'fire'): 'Air suffocates Fire!',
        ('air', 'rock'): 'Air erodes Rock!',
        ('air', 'water'): 'Air evaporates Water!',
        ('lizard', 'paper'): 'Lizard eats Paper!',
        ('lizard', 'air'): 'Lizard breathes Air!',
        ('lizard', 'lightning'): 'Lizard grounds Lightning!',
        ('gun', 'rock'): 'Gun shatters Rock!',
        ('gun', 'scissors'): 'Gun destroys Scissors!',
        ('gun', 'fire'): 'Gun blows out Fire!',
        ('gun', 'lizard'): 'Gun shoots Lizard!',
        ('gun', 'air'): 'Gun pierces Air!',
        ('gun', 'lightning'): 'Gun conducts Lightning!',
        ('lightning', 'water'): 'Lightning electrifies Water!',
        ('lightning', 'scissors'): 'Lightning melts Scissors!',
        ('lightning', 'gun'): 'Lightning magnetizes Gun!',
        ('lightning', 'fire'): 'Lightning outshines Fire!',
        ('shield', 'gun'): 'Shield blocks Gun!',
        ('shield', 'rock'): 'Shield deflects Rock!',
        ('shield', 'scissors'): 'Shield blocks Scissors!',
        ('shield', 'lightning'): 'Shield grounds Lightning!',
    }
    return descriptions.get((winner_choice, loser_choice), f'{winner_data.get("emoji", "")} {winner_choice.capitalize()} beats {loser_choice.capitalize()}!')


class GameAI:
    """AI opponent with different difficulty levels"""
    
    def __init__(self, difficulty='normal'):
        self.difficulty = difficulty
        self.player_history = []
        self.pattern_length = 5
    
    def add_to_history(self, player_choice):
        """Add player's choice to history"""
        self.player_history.append(player_choice)
        # Keep history manageable
        if len(self.player_history) > 100:
            self.player_history = self.player_history[-50:]
    
    def get_choice(self, available_elements):
        """Get AI's choice based on difficulty"""
        if self.difficulty == 'normal':
            return self._normal_choice(available_elements)
        elif self.difficulty == 'hard':
            return self._hard_choice(available_elements)
        else:  # veteran
            return self._veteran_choice(available_elements)
    
    def _normal_choice(self, available_elements):
        """Normal: Pure random choice"""
        return random.choice(available_elements)
    
    def _hard_choice(self, available_elements):
        """Hard: Analyzes player patterns with 40% accuracy"""
        if len(self.player_history) < 3 or random.random() > 0.4:
            return random.choice(available_elements)
        
        # Simple frequency analysis
        recent = self.player_history[-10:]
        counts = Counter(recent)
        most_common = counts.most_common(1)[0][0]
        
        # Find what beats the most common choice
        return self._find_counter(most_common, available_elements)
    
    def _veteran_choice(self, available_elements):
        """Veteran: Advanced pattern recognition with 70% accuracy"""
        if len(self.player_history) < 5 or random.random() > 0.7:
            return random.choice(available_elements)
        
        # Pattern matching - look for sequences
        predicted = self._predict_next_move(available_elements)
        if predicted:
            return self._find_counter(predicted, available_elements)
        
        # Fall back to frequency analysis
        recent = self.player_history[-15:]
        counts = Counter(recent)
        most_common = counts.most_common(1)[0][0]
        return self._find_counter(most_common, available_elements)
    
    def _predict_next_move(self, available_elements):
        """Predict player's next move based on patterns"""
        if len(self.player_history) < self.pattern_length:
            return None
        
        # Look for repeating patterns
        recent = self.player_history[-self.pattern_length:]
        history_str = ''.join(self.player_history)
        pattern_str = ''.join(recent[:-1])
        
        # Find all occurrences of the pattern
        next_moves = []
        idx = 0
        while True:
            idx = history_str.find(pattern_str, idx)
            if idx == -1 or idx + len(pattern_str) >= len(history_str):
                break
            next_move = history_str[idx + len(pattern_str)]
            if next_move in available_elements:
                next_moves.append(next_move)
            idx += 1
        
        if next_moves:
            return Counter(next_moves).most_common(1)[0][0]
        return None
    
    def _find_counter(self, player_choice, available_elements):
        """Find an element that beats the player's choice"""
        for element in available_elements:
            if player_choice in ELEMENTS[element]['beats']:
                return element
        return random.choice(available_elements)
    
    def reset(self):
        """Reset AI history"""
        self.player_history = []
