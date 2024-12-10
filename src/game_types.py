import datetime as dt
from enum import StrEnum
from typing import TYPE_CHECKING, List

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


def message_str(
    player: "Player",
    messages: List[Message],
    thoughts: List[Message] = None,
    max_messages: int = 75,
) -> str:
    if thoughts is not None:
        messages.extend(thoughts)

    messages = sorted(messages, key=lambda x: x.time)
    string = ""
    for message in messages[-max_messages:]:
        string += "\n"
        chat_type = "INTERNAL THOUGHT" if message.internal else "PUBLIC CHAT"
        if message.internal == player:
            string += f"[{chat_type}][Myself]: {message.content}"
        else:
            string += f"[{chat_type}][{message.author}]: {message.content}"

    return string
