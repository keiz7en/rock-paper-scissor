# Rock Paper Scissors Ultimate

A Django-based Rock Paper Scissors game with extended elements, AI difficulty levels, and player rankings.

## Features

- **3 Game Modes:**
  - Classic (Rock, Paper, Scissors)
  - Extended (+ Fire, Water)
  - Ultimate (10 elements including Gun, Lightning, Shield, etc.)

- **3 AI Difficulty Levels:**
  - Normal: Random choices
  - Hard: Pattern analysis (40% accuracy)
  - Veteran: Advanced prediction (70% accuracy)

- **Player Rankings & Leaderboard:**
  - Track your wins, losses, and streaks
  - Global leaderboard
  - Score-based ranking system

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run migrations:
```bash
python manage.py migrate
```

3. Start the server:
```bash
python manage.py runserver
```

4. Open http://127.0.0.1:8000

## Deploy to Render.com

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set the following:
   - **Build Command:** `./build.sh`
   - **Start Command:** `gunicorn rps_project.wsgi:application`
4. Add Environment Variables:
   - `DJANGO_SECRET_KEY`: Your secret key
   - `DEBUG`: `False`
   - `DATABASE_URL`: (Render provides this if using PostgreSQL)

## Scoring System

- +10 points per win
- +5 bonus for Veteran wins
- +3 bonus for Hard wins
- -2 points per loss

## Keyboard Shortcuts

| Key | Element |
|-----|---------|
| R | Rock |
| P | Paper |
| S | Scissors |
| F | Fire |
| W | Water |
| A | Air |
| L | Lizard |
| G | Gun |
| E | Lightning |
| D | Shield |
