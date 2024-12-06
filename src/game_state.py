from typing import List

from pydantic import BaseModel

from src.game_types import Message
from src.players import Player


class GameState(BaseModel):
    elected_chancellor: Player
    elected_president: Player
    previous_president: Player
    previous_president: Player
    public_chat: List[Message]
