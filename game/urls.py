from django.urls import path
from . import views

app_name = 'game'

urlpatterns = [
    path('', views.home, name='home'),
    path('play/', views.game_view, name='play'),
    path('pvp/', views.pvp_view, name='pvp'),
    path('api/play/', views.play_round, name='play_round'),
    path('api/reset/', views.reset_game, name='reset_game'),
    path('api/elements/', views.get_elements, name='get_elements'),
    path('api/leaderboard/', views.get_leaderboard_data, name='get_leaderboard_data'),
    # Online matchmaking APIs
    path('api/matchmaking/join/', views.join_matchmaking, name='join_matchmaking'),
    path('api/matchmaking/leave/', views.leave_matchmaking, name='leave_matchmaking'),
    path('api/game/state/', views.get_game_state, name='get_game_state'),
    path('api/game/choice/', views.make_choice, name='make_choice'),
    path('api/game/next/', views.next_round, name='next_round'),
    path('api/game/forfeit/', views.forfeit_game, name='forfeit_game'),
    path('rules/', views.rules, name='rules'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
]
