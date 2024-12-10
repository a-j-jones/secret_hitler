import datetime as dt
from enum import StrEnum
from typing import TYPE_CHECKING, List, Set

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from src.players import Player


class Party(StrEnum):
    liberal = "Liberal"
    fascist = "Fascist"


class Policy(StrEnum):
    liberal = "Liberal"
    fascist = "Fascist"


class Role(StrEnum):
    liberal = "Liberal"
    fascist = "Fascist"
    hitler = "Hitler"


class PlayerType(StrEnum):
    human = "Human"
    ai = "AI"


class Selection(BaseModel):
    selected: List[Policy]
    discarded: List[Policy]


class Message(BaseModel):
    time: dt.datetime = Field(default_factory=dt.datetime.now)
    author: "Player"
    internal: bool = Field(default=False)
    content: str

    def __hash__(self) -> int:
        return hash((self.time, self.author, self.internal, self.content))


def message_str(
    player: "Player",
    messages: Set[Message],
    thoughts: Set[Message] = None,
    max_messages: int = 75,
) -> str:
    message_list = list(messages)
    if thoughts is not None:
        message_list.extend(list(thoughts))

    message_list = sorted(message_list, key=lambda x: x.time)
    string = ""
    for message in message_list[-max_messages:]:
        string += "\n"
        chat_type = "INTERNAL THOUGHT" if message.internal else "PUBLIC CHAT"
        if message.internal == player:
            string += f"[{chat_type}][Myself]: {message.content}"
        else:
            string += f"[{chat_type}][{message.author}]: {message.content}"

    return string
