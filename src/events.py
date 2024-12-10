import datetime as dt
from enum import StrEnum
from typing import TYPE_CHECKING, List

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from src.players import Player


class EventType(StrEnum):
    fascist_policy_enacted = "Fascist policy was enacted"
    liberal_policy_enacted = "Liberal policy was enacted"
    chancellor_nominated = "nominated as Chancellor"
    chancellor_elected = "elected as Chancellor"
    president_nominated = "nominated as President"
    president_elected = "elected as President"
    vote_in_favour = "voted in favour of the new Government"
    vote_against = "voted against the new Government"
    player_executed = "executed"
    loyalty_investigated = "investigated"
    policy_peek = "top 3 policies peeked at"


class Event(BaseModel):
    time: dt.datetime = Field(default_factory=dt.datetime.now)
    event_type: EventType
    actor: "Player"
    recipient: "Player" = Field(default=None)

    model_config = ConfigDict(
        frozen=True,
        use_enum_values=True,
    )

    def __hash__(self) -> int:
        return hash((self.time, self.event_type, self.actor, self.recipient))

    def description(self) -> str:
        if self.actor and self.recipient:
            return f"{self.recipient} was {self.event_type} by {self.actor}"

        if self.actor:
            return f"{self.event_type} by {self.actor}"

        if self.recipient:
            return f"{self.recipient} was {self.event_type}"


def events_str(events: List[Event], max_events: int = 50) -> str:
    events = sorted(events, key=lambda x: x.time)
    string = ""
    for event in events[-max_events:]:
        string += "\n"
        string += f"{event.description()}"

    return string
