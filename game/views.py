from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import F
from django.utils import timezone
from datetime import timedelta
import json
import uuid
import random

from .game_logic import (
    ELEMENTS, 
    get_elements_for_mode, 
    determine_winner, 
    get_win_reason,
    GameAI
)
from .models import Player, GameSession, MatchmakingQueue, OnlineGame

# Store AI instances per session
ai_instances = {}


def home(request):
    """Render the home page"""
    # Get top 5 players for display
    top_players = Player.objects.all()[:5]
    return render(request, 'game/home.html', {'top_players': top_players})


def game_view(request):
    """Render the game page"""
    difficulty = request.GET.get('difficulty', 'normal')
    mode = request.GET.get('mode', 'classic')
    player_name = request.GET.get('player', '')
    ai_name = request.GET.get('ai_name', '')  # Custom AI name from auto-match
    auto_match = request.GET.get('auto_match', '')  # Flag for auto-matched AI game
    
    elements = get_elements_for_mode(mode)
    element_data = {key: ELEMENTS[key] for key in elements}
    
    # Get top players for sidebar
    top_players = Player.objects.all()[:10]
    
    context = {
        'difficulty': difficulty,
        'mode': mode,
        'player_name': player_name,
        'ai_name': ai_name,
        'auto_match': auto_match,
        'elements': element_data,
        'elements_json': json.dumps(element_data),
        'top_players': top_players,
    }
    return render(request, 'game/game.html', context)


def pvp_view(request):
    """Render the Player vs Player online matchmaking page"""
    player_name = request.GET.get('player', 'Player')
    
    # Generate unique player ID for this session
    player_id = str(uuid.uuid4())
    
    # Include ALL elements - actual mode will be randomly selected at match time
    all_elements = ELEMENTS
    
    context = {
        'player_name': player_name,
        'player_id': player_id,
        'elements': all_elements,
        'elements_json': json.dumps(all_elements),
    }
    return render(request, 'game/pvp.html', context)


@csrf_exempt
def join_matchmaking(request):
    """Join the matchmaking queue to find an opponent"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        data = json.loads(request.body)
        player_id = data.get('player_id')
        player_name = data.get('player_name', 'Player')
        mode = data.get('mode', 'classic')
        
        # Clean up old/expired entries (older than 60 seconds)
        expiry_time = timezone.now() - timedelta(seconds=60)
        MatchmakingQueue.objects.filter(created_at__lt=expiry_time).delete()
        
        # Check if player is already in queue
        existing = MatchmakingQueue.objects.filter(player_id=player_id).first()
        if existing:
            if existing.status == 'matched' and existing.matched_game_id:
                return JsonResponse({
                    'status': 'matched',
                    'game_id': existing.matched_game_id
                })
            # Update timestamp
            existing.created_at = timezone.now()
            existing.save()
        else:
            # Add to queue
            MatchmakingQueue.objects.create(
                player_id=player_id,
                player_name=player_name,
                mode=mode,
                status='searching'
            )
        
        # Try to find a match (any player searching, regardless of mode)
        potential_match = MatchmakingQueue.objects.filter(
            status='searching'
        ).exclude(player_id=player_id).order_by('created_at').first()
        
        if potential_match:
            # Create a game with a RANDOM mode
            game_id = str(uuid.uuid4())
            random_mode = random.choice(['classic', 'extended', 'full'])
            
            OnlineGame.objects.create(
                game_id=game_id,
                mode=random_mode,
                player1_id=potential_match.player_id,
                player1_name=potential_match.player_name,
                player2_id=player_id,
                player2_name=player_name,
                status='playing',
                round_start_time=timezone.now()  # Start the timer
            )
            
            # Update both queue entries
            potential_match.status = 'matched'
            potential_match.matched_game_id = game_id
            potential_match.save()
            
            MatchmakingQueue.objects.filter(player_id=player_id).update(
                status='matched',
                matched_game_id=game_id
            )
            
            return JsonResponse({
                'status': 'matched',
                'game_id': game_id
            })
        
        # Still searching
        queue_position = MatchmakingQueue.objects.filter(
            mode=mode,
            status='searching',
            created_at__lt=timezone.now()
        ).count()
        
        return JsonResponse({
            'status': 'searching',
            'queue_position': queue_position,
            'players_online': MatchmakingQueue.objects.filter(status='searching').count()
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def leave_matchmaking(request):
    """Leave the matchmaking queue"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        data = json.loads(request.body)
        player_id = data.get('player_id')
        
        MatchmakingQueue.objects.filter(player_id=player_id).delete()
        
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


DISCONNECT_TIMEOUT = 10  # Seconds before considering player disconnected

@csrf_exempt
def get_game_state(request):
    """Get the current state of an online game"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        data = json.loads(request.body)
        game_id = data.get('game_id')
        player_id = data.get('player_id')
        
        game = OnlineGame.objects.filter(game_id=game_id).first()
        if not game:
            return JsonResponse({'error': 'Game not found'}, status=404)
        
        # Determine which player this is
        is_player1 = game.player1_id == player_id
        
        # Update last seen time for this player
        now = timezone.now()
        if is_player1:
            game.player1_last_seen = now
        else:
            game.player2_last_seen = now
        
        # Check if opponent has disconnected (only if game is still active)
        if game.status in ['playing', 'round_complete']:
            opponent_last_seen = game.player2_last_seen if is_player1 else game.player1_last_seen
            if opponent_last_seen:
                time_since_seen = (now - opponent_last_seen).total_seconds()
                if time_since_seen > DISCONNECT_TIMEOUT:
                    # Opponent disconnected - they forfeit
                    opponent_name = game.player2_name if is_player1 else game.player1_name
                    my_name = game.player1_name if is_player1 else game.player2_name
                    game.status = 'forfeit'
                    game.winner = my_name
                    game.forfeit_by = opponent_name
        
        game.save()
        
        response = {
            'game_id': game.game_id,
            'status': game.status,
            'mode': game.mode,
            'current_round': game.current_round,
            'max_rounds': game.max_rounds,
            'player1_name': game.player1_name,
            'player2_name': game.player2_name,
            'player1_score': game.player1_score,
            'player2_score': game.player2_score,
            'is_player1': is_player1,
            'your_name': game.player1_name if is_player1 else game.player2_name,
            'opponent_name': game.player2_name if is_player1 else game.player1_name,
            'your_score': game.player1_score if is_player1 else game.player2_score,
            'opponent_score': game.player2_score if is_player1 else game.player1_score,
            'you_chose': bool(game.player1_choice if is_player1 else game.player2_choice),
            'opponent_chose': bool(game.player2_choice if is_player1 else game.player1_choice),
            'winner': game.winner,
            'forfeit_by': game.forfeit_by,
            'round_start_time': game.round_start_time.isoformat() if game.round_start_time else None,
        }
        
        # If round is complete, include the result
        if game.status == 'round_complete' and game.round_result:
            result_data = json.loads(game.round_result)
            response['round_result'] = result_data
        
        return JsonResponse(response)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def make_choice(request):
    """Make a choice in an online game"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        data = json.loads(request.body)
        game_id = data.get('game_id')
        player_id = data.get('player_id')
        choice = data.get('choice', '').lower()
        
        game = OnlineGame.objects.filter(game_id=game_id).first()
        if not game:
            return JsonResponse({'error': 'Game not found'}, status=404)
        
        if game.status not in ['playing', 'round_complete']:
            return JsonResponse({'error': 'Game is not active'}, status=400)
        
        # Validate choice
        available_elements = get_elements_for_mode(game.mode)
        if choice not in available_elements:
            return JsonResponse({'error': 'Invalid choice'}, status=400)
        
        # Determine which player and update their choice
        is_player1 = game.player1_id == player_id
        
        if is_player1:
            game.player1_choice = choice
        else:
            game.player2_choice = choice
        
        # Check if both players have chosen
        if game.player1_choice and game.player2_choice:
            # Determine winner of this round
            result = determine_winner(game.player1_choice, game.player2_choice)
            
            if result == 'win':
                game.player1_score += 1
                round_winner = game.player1_name
                reason = get_win_reason(game.player1_choice, game.player2_choice)
            elif result == 'lose':
                game.player2_score += 1
                round_winner = game.player2_name
                reason = get_win_reason(game.player2_choice, game.player1_choice)
            else:
                round_winner = None
                reason = "It's a draw!"
            
            # Store round result
            game.round_result = json.dumps({
                'player1_choice': game.player1_choice,
                'player1_emoji': ELEMENTS[game.player1_choice]['emoji'],
                'player2_choice': game.player2_choice,
                'player2_emoji': ELEMENTS[game.player2_choice]['emoji'],
                'round_winner': round_winner,
                'reason': reason,
            })
            
            # Check if game is over (first to 3)
            if game.player1_score >= 3:
                game.status = 'finished'
                game.winner = game.player1_name
            elif game.player2_score >= 3:
                game.status = 'finished'
                game.winner = game.player2_name
            else:
                game.status = 'round_complete'
        
        game.save()
        
        return JsonResponse({
            'status': 'success',
            'choice_made': True,
            'waiting_for_opponent': not (game.player1_choice and game.player2_choice)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def next_round(request):
    """Move to the next round in an online game"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        data = json.loads(request.body)
        game_id = data.get('game_id')
        player_id = data.get('player_id')
        
        game = OnlineGame.objects.filter(game_id=game_id).first()
        if not game:
            return JsonResponse({'error': 'Game not found'}, status=404)
        
        # Mark this player as ready for next round
        is_player1 = game.player1_id == player_id
        
        if is_player1:
            game.player1_ready = True
        else:
            game.player2_ready = True
        
        # If both players are ready, start next round
        if game.player1_ready and game.player2_ready:
            game.current_round += 1
            game.player1_choice = None
            game.player2_choice = None
            game.player1_ready = False
            game.player2_ready = False
            game.round_result = None
            game.status = 'playing'
            game.round_start_time = timezone.now()  # Reset timer for new round
        
        game.save()
        
        return JsonResponse({
            'status': 'success',
            'both_ready': game.player1_ready and game.player2_ready
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def forfeit_game(request):
    """Handle player forfeiting due to timeout"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        data = json.loads(request.body)
        game_id = data.get('game_id')
        player_id = data.get('player_id')
        forfeit_player_id = data.get('forfeit_player_id')  # Who timed out
        
        game = OnlineGame.objects.filter(game_id=game_id).first()
        if not game:
            return JsonResponse({'error': 'Game not found'}, status=404)
        
        if game.status in ['finished', 'forfeit']:
            return JsonResponse({'status': 'already_ended'})
        
        # Determine who forfeited
        if forfeit_player_id == game.player1_id:
            forfeit_name = game.player1_name
            winner_name = game.player2_name
        else:
            forfeit_name = game.player2_name
            winner_name = game.player1_name
        
        # Update game status
        game.status = 'forfeit'
        game.winner = winner_name
        game.forfeit_by = forfeit_name
        game.save()
        
        return JsonResponse({
            'status': 'success',
            'forfeit_by': forfeit_name,
            'winner': winner_name
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def play_round(request):
    """Handle a round of the game"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        data = json.loads(request.body)
        player_choice = data.get('choice', '').lower()
        difficulty = data.get('difficulty', 'normal')
        mode = data.get('mode', 'classic')
        session_id = data.get('session_id', 'default')
        player_name = data.get('player_name', '').strip()
        
        # Validate choice
        available_elements = get_elements_for_mode(mode)
        if player_choice not in available_elements:
            return JsonResponse({'error': 'Invalid choice'}, status=400)
        
        # Get or create AI instance for this session
        ai_key = f"{session_id}_{difficulty}"
        if ai_key not in ai_instances:
            ai_instances[ai_key] = GameAI(difficulty)
        
        ai = ai_instances[ai_key]
        
        # Get AI choice
        ai_choice = ai.get_choice(available_elements)
        
        # Determine winner
        result = determine_winner(player_choice, ai_choice)
        
        # Get win reason
        if result == 'win':
            reason = get_win_reason(player_choice, ai_choice)
        elif result == 'lose':
            reason = get_win_reason(ai_choice, player_choice)
        else:
            reason = "It's a draw!"
        
        # Add to AI history
        ai.add_to_history(player_choice)
        
        # Update player stats if player name provided
        player_data = None
        if player_name:
            player, created = Player.objects.get_or_create(name=player_name)
            player.update_stats(result, difficulty)
            player_data = {
                'name': player.name,
                'score': player.score,
                'total_wins': player.total_wins,
                'total_games': player.total_games,
                'win_rate': player.win_rate(),
                'current_streak': player.current_streak,
                'best_streak': player.best_streak,
                'rank': get_player_rank(player)
            }
        
        response = {
            'player_choice': player_choice,
            'player_emoji': ELEMENTS[player_choice]['emoji'],
            'ai_choice': ai_choice,
            'ai_emoji': ELEMENTS[ai_choice]['emoji'],
            'result': result,
            'reason': reason,
            'player_data': player_data,
        }
        
        return JsonResponse(response)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_player_rank(player):
    """Get player's current rank"""
    rank = Player.objects.filter(score__gt=player.score).count() + 1
    return rank


@csrf_exempt
def reset_game(request):
    """Reset the game session"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id', 'default')
        difficulty = data.get('difficulty', 'normal')
        
        ai_key = f"{session_id}_{difficulty}"
        if ai_key in ai_instances:
            ai_instances[ai_key].reset()
        
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_elements(request):
    """Return all elements data"""
    mode = request.GET.get('mode', 'classic')
    elements = get_elements_for_mode(mode)
    element_data = {key: ELEMENTS[key] for key in elements}
    return JsonResponse(element_data)


def rules(request):
    """Render the rules page"""
    return render(request, 'game/rules.html', {'elements': ELEMENTS})


def leaderboard(request):
    """Render the leaderboard page"""
    players = Player.objects.all()[:100]
    
    # Get statistics
    total_players = Player.objects.count()
    total_games = sum(p.total_games for p in Player.objects.all())
    
    context = {
        'players': players,
        'total_players': total_players,
        'total_games': total_games,
    }
    return render(request, 'game/leaderboard.html', context)


def get_leaderboard_data(request):
    """API endpoint for leaderboard data"""
    limit = int(request.GET.get('limit', 10))
    players = Player.objects.all()[:limit]
    
    data = [{
        'rank': idx + 1,
        'name': p.name,
        'score': p.score,
        'wins': p.total_wins,
        'losses': p.total_losses,
        'draws': p.total_draws,
        'games': p.total_games,
        'win_rate': p.win_rate(),
        'best_streak': p.best_streak,
    } for idx, p in enumerate(players)]
    
    return JsonResponse({'leaderboard': data})
