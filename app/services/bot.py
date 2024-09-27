# services/bot.py
import random
import asyncio
from app.models import Game

async def bot_logic(game: Game, bot_id: str):
    """
    Logique simple pour les bots : ils se déplacent aléatoirement et posent des bombes de temps en temps.
    """
    actions = ["up", "down", "left", "right", "place_bomb"]
    while game.is_active:
        action = random.choice(actions)
        update_game_state(game, bot_id, action)
        await asyncio.sleep(1)  # Les bots agissent toutes les secondes
