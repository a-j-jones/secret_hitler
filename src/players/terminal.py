from typing import TYPE_CHECKING, List

from src.events import Event, EventType
from src.game_types import Message, Policy, Selection
from src.players.base import POLICY_MAPPING, VOTE_MAPPING, Player

if TYPE_CHECKING:
    from src.game_state import GameState


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

        chosen_player = players[choice_idx]
        game_state.event_history.append(
            Event(event_type=EventType.chancellor_nominated, actor=self, recipient=chosen_player)
        )
        game_state.public_chat.append(
            Message(author=self, content=f"I've nominated {chosen_player.name} as chancellor")
        )

        return chosen_player

    def vote_on_government(
        self, game_state: "GameState", president: Player, chancellor: Player
    ) -> bool:
        while True:
            vote = input(
                f"f\n{self.name} - Vote on government (president: {president.name}, chancellor: {chancellor.name}) [y/n]? "
            ).lower()
            if vote in ["y", "n"]:
                vote_result = vote == "y"
                game_state.event_history.append(
                    Event(event_type=VOTE_MAPPING[vote_result], actor=self)
                )
                return vote_result

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
        game_state.event_history.append(Event(event_type=POLICY_MAPPING[selected[0]], actor=self))

        return Selection(selected=selected, discarded=policy_cards)

    def action_investigate_loyalty(self, game_state: "GameState", players: List[Player]):
        choice_idx = get_choice_idx(
            title_message=f"{self.name} - Choose a player to investigate:",
            input_message="Which player?",
            choices=players,
        )

        player = players[choice_idx]
        game_state.event_history.append(
            Event(event_type=EventType.loyalty_investigated, actor=self, recipient=player)
        )
        print(f"\n{player.name} is a {player.party}")

    def action_execution(self, game_state: "GameState", players: List[Player]) -> Player:
        choice_idx = get_choice_idx(
            title_message=f"{self.name} - Choose a player to execute:",
            input_message="Which player?",
            choices=players,
        )

        player = players[choice_idx]
        game_state.event_history.append(
            Event(event_type=EventType.player_executed, actor=self, recipient=player)
        )
        print(f"\n{player.name} has been executed")
        return player

    def action_policy_peek(self, game_state: "GameState", policy_cards: List[Policy]) -> None:
        print("\nThe next 3 policies are:")
        for idx, card in enumerate(policy_cards[-3:], start=1):
            print(f"{idx} - {card}")

        game_state.event_history.append(Event(event_type=EventType.policy_peek, actor=self))

    def discuss(self, game_state):
        return super().discuss(game_state)
