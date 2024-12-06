from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List

from pydantic import BaseModel, ConfigDict, Field

from src.game_types import Policy, Role, Selection

if TYPE_CHECKING:
    from src.game_state import GameState


class Player(BaseModel, ABC):
    name: str
    party: Policy
    role: Role
    alive: bool = Field(default=True)

    model_config = ConfigDict(use_enum_values=True)

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

    def __str__(self) -> str:
        return self.name


def get_choice_idx(title_message: str, input_message: str, choices: List[Player | Policy]) -> int:
    print(f"\n{title_message}")
    for i, choice in enumerate(choices, start=1):
        print(f"\t{i} - {choice}")

    while True:
        try:
            choice = input(f"\n{input_message} ")
            choice_idx = int(choice) - 1
            if 0 <= choice_idx <= len(choices) - 1:
                return choice_idx

            print(f"Please enter a number between 1 and {len(choices)}")
        except ValueError:
            print("Please enter a valid number")


class TerminalPlayer(Player):
    def nominate_chancellor(self, game_state: "GameState", players: List[Player]) -> Player:
        choice_idx = get_choice_idx(
            title_message=f"{self.name} - Nominate a chancellor:",
            input_message="Which player?",
            choices=players,
        )

        return players[choice_idx]

    def vote_on_government(
        self, game_state: "GameState", president: Player, chancellor: Player
    ) -> bool:
        while True:
            vote = input(
                f"f\n{self.name} - Vote on government (president: {president.name}, chancellor: {chancellor.name}) [y/n]? "
            ).lower()
            if vote in ["y", "n"]:
                return vote == "y"
            print("Please enter 'y' or 'n'")

    def propose_policies(self, game_state: "GameState", policy_cards: List[Policy]) -> Selection:
        choice_idx = get_choice_idx(
            title_message=f"{self.name} - Choose policies to discard (you must discard one):",
            input_message="Which policy to discard (1-3)?",
            choices=policy_cards,
        )

        discarded = [policy_cards.pop(choice_idx)]
        return Selection(selected=policy_cards, discarded=discarded)

    def enact_policy(self, game_state: "GameState", policy_cards: List[Policy]) -> Policy:
        choice_idx = get_choice_idx(
            title_message=f"{self.name} - Choose a policy to enact:",
            input_message="Which policy to discard (1-2)?",
            choices=policy_cards,
        )
        selected = [policy_cards.pop(choice_idx)]
        return Selection(selected=selected, discarded=policy_cards)

    def action_investigate_loyalty(self, game_state: "GameState", players: List[Player]):
        choice_idx = get_choice_idx(
            title_message=f"{self.name} - Choose a player to investigate:",
            input_message="Which player?",
            choices=players,
        )

        player = players[choice_idx]
        print(f"\n{player.name} is a {player.party}")

    def action_execution(self, game_state: "GameState", players: List[Player]):
        choice_idx = get_choice_idx(
            title_message=f"{self.name} - Choose a player to execute:",
            input_message="Which player?",
            choices=players,
        )

        player = players[choice_idx]
        player.alive = False
        print(f"\n{player.name} has been killed")

    def action_policy_peek(self, game_state: "GameState", policy_cards: List[Policy]) -> None:
        print("\nThe next 3 policies are:")
        for idx, card in enumerate(policy_cards[-3:], start=1):
            print(f"{idx} - {card}")


class ComputerPlayer(Player):
    def __init__(self):
        super().__init__()

    def nominate_chancellor(self, game_state, valid_players):
        print("Nominate a chancellor:")
        for i, player in enumerate(valid_players, start=1):
            print(f"\t{i} - {player.name}")

        choice = input("Which player?")
        choice_index = int(choice)

        return valid_players[choice_index - 1]

    def enact_policy(self, game_state, policy_cards):
        return super().enact_policy(game_state, policy_cards)

    def propose_policies(self, game_state, policy_cards):
        return super().propose_policies(game_state, policy_cards)

    def vote_on_government(self, game_state, president, chancellor):
        return super().vote_on_government(game_state, president, chancellor)
