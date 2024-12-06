import datetime as dt
from enum import StrEnum
from typing import List

from pydantic import BaseModel


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
    time: dt.datetime
    author: str
    content: str
