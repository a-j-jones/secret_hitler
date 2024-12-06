from enum import StrEnum


class Party(StrEnum):
    liberal = "Liberal"
    fascist = "Fascist"


class Policy(type(Party)):
    pass


class Role(StrEnum):
    liberal = "Liberal"
    fascist = "Fascist"
    hitler = "Hitler"


class PlayerType(StrEnum):
    human = "Human"
    ai = "AI"
