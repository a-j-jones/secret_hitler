from typing import Dict, List

from pydantic import BaseModel, Field

from src.game_types import Message, Policy
from src.players import Player


class GameState(BaseModel):
    chancellor: Player = Field(default=None)
    president: Player = Field(default=None)
    previous_president: Player = Field(default=None)
    previous_chancellor: Player = Field(default=None)
    public_chat: List[Message] = Field(default_factory=list)
    enacted_policies: Dict[Policy, int] = Field(
        default_factory=lambda x: {Policy.liberal: 0, Policy.fascist: 0}
    )

    def elect_government(self, chancellor: Player, president: Player) -> None:
        # Elect chancellor:
        if self.chancellor:
            self.previous_chancellor = self.chancellor
        self.chancellor = chancellor

        # Elect president:
        if self.president:
            self.previous_president = self.president
        self.president = president
