import random
from typing import List

from src.gametypes import Party, Role
from src.players import ComputerPlayer, HumanPlayer, Player

LIBERAL_POLICY_COUNT = 6
FASCIST_POLICY_COUNT = 11


class Game:
    def __init__(self, human_players: List[str], ai_players: List[str]) -> None:
        # Validate and assign player roles
        self.human_set = set(human_players)
        self.ai_set = set(ai_players)
        all_players = human_players + ai_players
        if len(self.human_set | self.ai_set) != len(all_players):
            raise ValueError("All player names must be unique.")

        # Create deck(s) and track the policies played:
        self.policy_deck = self.create_policy_deck()
        self.discard_deck = []
        self.enacted_policies = {Party.liberal: 0, Party.fascist: 0}

        self.players = self.assign_roles(all_players)

    def create_policy_deck(self) -> List[Party]:
        policy_deck = []
        policy_deck.extend([Party.liberal for _ in range(LIBERAL_POLICY_COUNT)])
        policy_deck.extend([Party.fascist for _ in range(FASCIST_POLICY_COUNT)])
        random.shuffle(policy_deck)

        return policy_deck

    def assign_roles(self, player_names: List[str]) -> List[Player]:
        player_count = len(player_names)
        num_liberals = (player_count // 2) + 1

        players = []
        random.shuffle(player_names)
        for i, name in enumerate(player_names):
            if i < num_liberals:
                party = Party.liberal
                role = Role.liberal
            elif i == num_liberals:
                party = Party.fascist
                role = Role.hitler
            else:
                party = Party.fascist
                role = Role.fascist

            if name in self.human_set:
                player_class = HumanPlayer
            else:
                player_class = ComputerPlayer

            players.append(player_class(name=name, party=party, role=role))

        random.shuffle(players)
        return players

    def valid_president(self, player: Player) -> bool:
        if not player.alive:
            return False

        return True

    def valid_voters(self, president: Player, chancellor: Player) -> List[Player]:
        return [p for p in self.players if p not in [president, chancellor] and p.alive]

    def play_game(self) -> None:
        game_state = 1
        turn_num = 0
        while True:
            # Cycle president:
            president = self.players[turn_num % len(self.players)]
            if not self.valid_president(president):
                turn_num += 1
                continue

            # Nominate a chancellor:
            print("President: ", president.name)
            nominated_chancellor = president.nominate_chancellor(
                game_state, [p for p in self.players if p != president]
            )

            # Vote in the current government:
            voters = self.valid_voters(president, nominated_chancellor)
            votes = [
                p.vote_on_government(game_state, president, nominated_chancellor) for p in voters
            ]
            if sum(votes) > len(votes) // 2:
                print("The government was elected successfully")
            else:
                print("The government was no elected")

            turn_num += 1
            if turn_num > 10:
                break
