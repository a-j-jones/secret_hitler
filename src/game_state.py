from typing import Dict, List, Set

from pydantic import BaseModel, ConfigDict, Field

from src.events import Event
from src.game_types import Message, Policy
from src.players import Player


class GameState(BaseModel):
    chancellor: Player = Field(default=None)
    president: Player = Field(default=None)
    hitler: Player = Field(default=None)
    previous_president: Player = Field(default=None)
    previous_chancellor: Player = Field(default=None)
    event_history: Set[Event] = Field(default_factory=set)
    public_chat: Set[Message] = Field(default_factory=set)
    players: List[Player] = Field(default_factory=list)
    failed_elections: int = Field(default=1)
    enacted_policies: Dict[Policy, int] = Field(
        default_factory=lambda: {Policy.liberal: 0, Policy.fascist: 0}
    )

    model_config = ConfigDict(use_enum_values=True)

    def elect_government(self, chancellor: Player, president: Player) -> None:
        # Elect chancellor:
        if self.chancellor:
            self.previous_chancellor = self.chancellor
        self.chancellor = chancellor

        # Elect president:
        if self.president:
            self.previous_president = self.president
        self.president = president


GameState.model_rebuild()
