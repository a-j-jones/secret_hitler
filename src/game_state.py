from pydantic import BaseModel

from src.players import Player


class GameState(BaseModel):
    chancellor: Player
