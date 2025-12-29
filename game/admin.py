from django.contrib import admin
from .models import Player, GameSession, GameRound


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ['name', 'score', 'total_wins', 'total_losses', 'total_games', 'best_streak', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name']
    ordering = ['-score']


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'player', 'difficulty', 'mode', 'player_wins', 'ai_wins', 'draws', 'total_rounds', 'created_at']
    list_filter = ['difficulty', 'mode', 'created_at']


@admin.register(GameRound)
class GameRoundAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'player_choice', 'ai_choice', 'result', 'created_at']
    list_filter = ['result', 'created_at']
