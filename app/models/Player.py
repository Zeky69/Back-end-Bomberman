from typing import Optional

from pydantic import BaseModel


class Player(BaseModel):
    id: str
    username: str
    x: float
    y: float
    life: int = 3
    bomb_capacity: int = 1
    bomb_range: int = 3
    is_alive: bool = True
    is_invincible: bool = False
    is_bot: bool = False
    moving_direction: Optional[str] = None  # 'up', 'down', 'left', 'right'


    def move(self, direction: str):
        if direction == "up":
            self.y -= 1
        elif direction == "down":
            self.y += 1
        elif direction == "left":
            self.x -= 1
        elif direction == "right":
            self.x += 1
        else:
            raise ValueError("Invalid direction. Must be 'up', 'down', 'left' or 'right'.")

    def place_bomb(self):
        pass


