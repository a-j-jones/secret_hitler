import datetime as dt
from enum import StrEnum
from typing import Dict, List

from pydantic import BaseModel, Field

from src.game_types import Message, Policy
from src.players import Player


class EventType(StrEnum):
    fascist_policy_played = "Fascist policy was played"
    liberal_policy_played = "Liberal policy was played"
    chancellor_nominated = "nominated as Chancellor"
    chancellor_elected = "elected as Chancellor"
    president_nominated = "nominated as President"
    president_elected = "elected as President"
    player_executed = "executed"


class Event(BaseModel):
    time: dt.datetime = Field(default_factory=dt.datetime.now)
    event_type: EventType
    actor: Player
    recipient: Player = Field(default=None)

    def description(self) -> str:
        if self.actor and self.recipient:
            return f"{self.recipient} was {self.event_type} by {self.actor}"

        if self.actor:
            return f"{self.event_type} by {self.actor}"

        if self.recipient:
            return f"{self.recipient} was {self.event_type}"


class GameState(BaseModel):
    chancellor: Player = Field(default=None)
    president: Player = Field(default=None)
    hitler: Player = Field(default=None)
    previous_president: Player = Field(default=None)
    previous_chancellor: Player = Field(default=None)
    event_history: List[Event] = Field(default_factory=list)
    public_chat: List[Message] = Field(default_factory=list)
    failed_elections: int = Field(default=1)
    enacted_policies: Dict[Policy, int] = Field(
        default_factory=lambda: {Policy.liberal: 0, Policy.fascist: 0}
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
