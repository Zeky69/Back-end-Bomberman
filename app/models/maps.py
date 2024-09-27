# models.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from uuid import uuid4
import asyncio

class Entity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    x: int
    y: int

class Bomb(Entity):
    timer: int = 3  # Par exemple, la bombe explose après 3 secondes
    owner_id: str

class Map(BaseModel):
    name: str
    width: int
    height: int
    tiles: List[List[Optional[int]]] = Field(default_factory=list)
    entities: List[Entity] = Field(default_factory=list)
    bombs: List[Bomb] = Field(default_factory=list)  # Ajout de la liste des bombes

    @root_validator(pre=True)
    def initialize_tiles(cls, values):
        name = values.get('name')
        width = values.get('width')
        height = values.get('height')

        if 'tiles' not in values or not values['tiles']:
            if name == "spawn":
                tiles = [
                    [
                        1 if x == 0 or x == width - 1 or y == 0 or y == height - 1 else 0
                        for y in range(height)
                    ]
                    for x in range(width)
                ]
            elif name == "map":
                tiles = [
                    [
                        1
                        if x == 0
                        or x == width - 1
                        or y == 0
                        or y == height - 1
                        or (x % 2 == 0 and y % 2 == 0)
                        else 0
                        for y in range(height)
                    ]
                    for x in range(width)
                ]
            elif name == "map3":
                tiles = [
                    [
                        1
                        if (
                            x == 0
                            or x == width - 1
                            or y == 0
                            or y == height - 1
                            or (x % 2 == 0 and y % 2 == 0)
                            or (x % 3 == 0 and y % 3 == 0)
                        )
                        else 0
                        for y in range(height)
                    ]
                    for x in range(width)
                ]
            else:
                tiles = [
                    [
                        1 if x == 0 or x == width - 1 or y == 0 or y == height - 1 else 0
                        for y in range(height)
                    ]
                    for x in range(width)
                ]
            values['tiles'] = tiles

        return values

    def add_entity(self, entity: Entity):
        self.entities.append(entity)

    def remove_entity(self, entity: Entity):
        self.entities.remove(entity)

    def add_bomb(self, bomb: Bomb):
        self.bombs.append(bomb)

    def remove_bomb(self, bomb: Bomb):
        self.bombs.remove(bomb)

    def get_entity(self, x: int, y: int) -> Optional[Entity]:
        for entity in self.entities:
            if entity.x == x and entity.y == y:
                return entity
        return None

    def get_tile(self, x: int, y: int) -> Optional[int]:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[x][y]
        raise IndexError("Coordonnées de tuile hors limites")

    def set_tile(self, x: int, y: int, tile: int):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.tiles[x][y] = tile
        else:
            raise IndexError("Coordonnées de tuile hors limites")

    def __str__(self):
        return f'Map {self.name} ({self.width}x{self.height})'
