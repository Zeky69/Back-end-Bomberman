# app/utils/game_utils.py

def generate_initial_map():
    # Implémentez une logique avancée pour générer une carte de jeu Bomberman
    # Exemple simplifié :
    width = 15
    height = 15
    walls = []
    for x in range(width):
        for y in range(height):
            if x % 2 == 0 and y % 2 == 0:
                walls.append([x, y])
    return {
        "width": width,
        "height": height,
        "walls": walls,
        "bombs": [],
        "explosions": []
    }

def check_collision(position: List[int], game_map: dict) -> bool:
    # Vérifiez si la position donnée est libre de murs
    return position not in game_map["walls"]
