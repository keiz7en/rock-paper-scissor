from django.db import models


class Player(models.Model):
    """Store player data for rankings"""
    name = models.CharField(max_length=50, unique=True)
    total_wins = models.IntegerField(default=0)
    total_losses = models.IntegerField(default=0)
    total_draws = models.IntegerField(default=0)
    total_games = models.IntegerField(default=0)
    
    # Stats by difficulty
    normal_wins = models.IntegerField(default=0)
    hard_wins = models.IntegerField(default=0)
    veteran_wins = models.IntegerField(default=0)
    
    # Streak tracking
    current_streak = models.IntegerField(default=0)
    best_streak = models.IntegerField(default=0)
    
    # Score calculation: wins*10 + veteran_wins*5 + hard_wins*3 - losses*2
    score = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-score', '-total_wins', 'total_losses']
    
    def __str__(self):
        return f"{self.name} - Score: {self.score}"
    
    def calculate_score(self):
        """Calculate player score based on performance"""
        self.score = (
            self.total_wins * 10 +
            self.veteran_wins * 5 +
            self.hard_wins * 3 -
            self.total_losses * 2
        )
        return self.score
    
    def win_rate(self):
        """Calculate win rate percentage"""
        if self.total_games == 0:
            return 0
        return round((self.total_wins / self.total_games) * 100, 1)
    
    def update_stats(self, result, difficulty):
        """Update player stats after a game"""
        self.total_games += 1
        
        if result == 'win':
            self.total_wins += 1
            self.current_streak += 1
            if self.current_streak > self.best_streak:
                self.best_streak = self.current_streak
            
            if difficulty == 'normal':
                self.normal_wins += 1
            elif difficulty == 'hard':
                self.hard_wins += 1
            elif difficulty == 'veteran':
                self.veteran_wins += 1
                
        elif result == 'lose':
            self.total_losses += 1
            self.current_streak = 0
        else:
            self.total_draws += 1
        
        self.calculate_score()
        self.save()


class GameSession(models.Model):
    """Store game session data"""
    DIFFICULTY_CHOICES = [
        ('normal', 'Normal'),
        ('hard', 'Hard'),
        ('veteran', 'Veteran'),
    ]
    
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='sessions', null=True, blank=True)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='normal')
    mode = models.CharField(max_length=20, default='classic')
    player_wins = models.IntegerField(default=0)
    ai_wins = models.IntegerField(default=0)
    draws = models.IntegerField(default=0)
    total_rounds = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Game Session {self.id} - {self.difficulty}"


class GameRound(models.Model):
    """Store individual round data"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='rounds')
    player_choice = models.CharField(max_length=20)
    ai_choice = models.CharField(max_length=20)
    result = models.CharField(max_length=10)  # win, lose, draw
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Round {self.id}: {self.player_choice} vs {self.ai_choice}"


class MatchmakingQueue(models.Model):
    """Queue for players searching for online matches"""
    player_id = models.CharField(max_length=100, unique=True)  # Unique session ID
    player_name = models.CharField(max_length=50)
    mode = models.CharField(max_length=20, default='classic')
    status = models.CharField(max_length=20, default='searching')  # searching, matched, expired
    matched_game_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.player_name} - {self.status}"


class OnlineGame(models.Model):
    """Online PvP game session"""
    game_id = models.CharField(max_length=100, unique=True)
    mode = models.CharField(max_length=20, default='classic')
    
    player1_id = models.CharField(max_length=100)
    player1_name = models.CharField(max_length=50)
    player1_choice = models.CharField(max_length=20, null=True, blank=True)
    player1_score = models.IntegerField(default=0)
    player1_ready = models.BooleanField(default=False)
    player1_last_seen = models.DateTimeField(null=True, blank=True)  # Track activity
    
    player2_id = models.CharField(max_length=100)
    player2_name = models.CharField(max_length=50)
    player2_choice = models.CharField(max_length=20, null=True, blank=True)
    player2_score = models.IntegerField(default=0)
    player2_ready = models.BooleanField(default=False)
    player2_last_seen = models.DateTimeField(null=True, blank=True)  # Track activity
    
    current_round = models.IntegerField(default=1)
    max_rounds = models.IntegerField(default=5)  # First to 3 wins
    status = models.CharField(max_length=20, default='waiting')  # waiting, playing, round_complete, finished, forfeit
    winner = models.CharField(max_length=50, null=True, blank=True)
    forfeit_by = models.CharField(max_length=50, null=True, blank=True)  # Who forfeited
    
    round_result = models.CharField(max_length=100, null=True, blank=True)  # JSON string of last round result
    round_start_time = models.DateTimeField(null=True, blank=True)  # When the current round started
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Game {self.game_id}: {self.player1_name} vs {self.player2_name}"
