from abc import ABC, abstractmethod
from typing import List

from pydantic import BaseModel, ConfigDict, Field

from src.gametypes import Party, Policy, Role


class GameState:
    def __init__(self) -> None:
        pass


class Player(BaseModel, ABC):
    name: str
    party: Party
    role: Role
    alive: bool = Field(default=True)

    model_config = ConfigDict(use_enum_values=True)

    @abstractmethod
    def nominate_chancellor(self, game_state: GameState, valid_players: List["Player"]) -> "Player":
        pass

    @abstractmethod
    def vote_on_government(
        self, game_state: GameState, president: "Player", chancellor: "Player"
    ) -> bool:
        pass

    @abstractmethod
    def propose_policies(self, game_state: GameState, policy_cards: List[Policy]) -> List[Policy]:
        pass

    @abstractmethod
    def enact_policy(self, game_state: GameState, policy_cards: List[Policy]) -> Policy:
        pass


class HumanPlayer(Player):
    def nominate_chancellor(self, game_state: GameState, valid_players: List["Player"]) -> "Player":
        print("Nominate a chancellor:")
        for i, player in enumerate(valid_players, start=1):
            print(f"\t{i} - {player.name}")

        while True:
            try:
                choice = input("Which player? ")
                choice_index = int(choice)
                if 1 <= choice_index <= len(valid_players):
                    return valid_players[choice_index - 1]
                print(f"Please enter a number between 1 and {len(valid_players)}")
            except ValueError:
                print("Please enter a valid number")

    def vote_on_government(
        self, game_state: GameState, president: "Player", chancellor: "Player"
    ) -> bool:
        while True:
            vote = input(
                f"Vote on government (president: {president.name}, chancellor: {chancellor.name}) [y/n]? "
            ).lower()
            if vote in ["y", "n"]:
                return vote == "y"
            print("Please enter 'y' or 'n'")

    def propose_policies(self, game_state: GameState, policy_cards: List[Policy]) -> List[Policy]:
        print("Choose policies to discard (you must discard one):")
        for i, policy in enumerate(policy_cards, start=1):
            print(f"\t{i} - {policy}")

        while True:
            try:
                choice = input("Which policy to discard (1-3)? ")
                choice_index = int(choice)
                if 1 <= choice_index <= len(policy_cards):
                    return [p for i, p in enumerate(policy_cards) if i != choice_index - 1]
                print(f"Please enter a number between 1 and {len(policy_cards)}")
            except ValueError:
                print("Please enter a valid number")

    def enact_policy(self, game_state: GameState, policy_cards: List[Policy]) -> Policy:
        print("Choose a policy to enact:")
        for i, policy in enumerate(policy_cards, start=1):
            print(f"\t{i} - {policy}")

        while True:
            try:
                choice = input("Which policy to enact (1-2)? ")
                choice_index = int(choice)
                if 1 <= choice_index <= len(policy_cards):
                    return policy_cards[choice_index - 1]
                print(f"Please enter a number between 1 and {len(policy_cards)}")
            except ValueError:
                print("Please enter a valid number")


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
