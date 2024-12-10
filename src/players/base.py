import datetime as dt
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Set

from pydantic import BaseModel, ConfigDict, Field

from src.events import EventType
from src.game_types import Message, Party, Policy, Role, Selection

if TYPE_CHECKING:
    from src.game_state import GameState

VOTE_MAPPING = {True: EventType.vote_in_favour, False: EventType.vote_against}
POLICY_MAPPING = {
    Policy.fascist: EventType.fascist_policy_enacted,
    Policy.liberal: EventType.liberal_policy_enacted,
}


class Player(BaseModel, ABC):
    name: str
    party: Party
    role: Role
    alive: bool = Field(default=True)
    thoughts: Set[Message] = Field(default_factory=set)
    last_logged_message_dt: dt.datetime = Field(default_factory=dt.datetime.now)

    model_config = ConfigDict(use_enum_values=True)

    def __hash__(self) -> int:
        return hash((self.name,))

    @abstractmethod
    def nominate_chancellor(self, game_state: "GameState", players: List["Player"]) -> "Player":
        pass

    @abstractmethod
    def vote_on_government(
        self, game_state: "GameState", president: "Player", chancellor: "Player"
    ) -> bool:
        pass

    @abstractmethod
    def propose_policies(self, game_state: "GameState", policy_cards: List[Policy]) -> Selection:
        pass

    @abstractmethod
    def enact_policy(self, game_state: "GameState", policy_cards: List[Policy]) -> Selection:
        pass

    @abstractmethod
    def action_investigate_loyalty(self, game_state: "GameState", players: List["Player"]) -> None:
        pass

    @abstractmethod
    def action_execution(self, game_state: "GameState", players: List["Player"]) -> None:
        pass

    @abstractmethod
    def action_policy_peek(self, game_state: "GameState", policies: List["Policy"]) -> None:
        pass

    @abstractmethod
    def discuss(self, game_state: "GameState") -> None:
        pass

    def __str__(self) -> str:
        return self.name


Player.model_rebuild()
