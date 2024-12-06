import random
from typing import List

from src.gametypes import Policy, Role
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
        self.enacted_policies = {Policy.liberal: 0, Policy.fascist: 0}

        self.players = self.assign_roles(all_players)

    def create_policy_deck(self) -> List[Policy]:
        policy_deck = []
        policy_deck.extend([Policy.liberal for _ in range(LIBERAL_POLICY_COUNT)])
        policy_deck.extend([Policy.fascist for _ in range(FASCIST_POLICY_COUNT)])
        random.shuffle(policy_deck)

        return policy_deck

    def reshuffle_deck(self) -> None:
        self.policy_deck.extend(self.discard_deck)
        self.discard_deck = []
        random.shuffle(self.policy_deck)

    def assign_roles(self, player_names: List[str]) -> List[Player]:
        player_count = len(player_names)
        num_liberals = (player_count // 2) + 1

        players = []
        random.shuffle(player_names)
        for i, name in enumerate(player_names):
            if i < num_liberals:
                party = Policy.liberal
                role = Role.liberal
            elif i == num_liberals:
                party = Policy.fascist
                role = Role.hitler
            else:
                party = Policy.fascist
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

    def valid_players(self) -> List[Player]:
        return [p for p in self.players if p.alive]

    def valid_voters(self, president: Player, chancellor: Player) -> List[Player]:
        return [p for p in self.valid_players() if p not in [president, chancellor]]

    def valid_chancellors(
        self, president: Player, previous_president: Player, previous_chancellor: Player
    ) -> List[Player]:
        invalid_choices = [president, previous_president, previous_chancellor]
        return [p for p in self.valid_players() if p not in invalid_choices]

    def draw_policies(self) -> List[Policy]:
        if len(self.policy_deck) < 3:
            self.reshuffle_deck()

        hand = []
        for _ in range(3):
            hand.append(self.policy_deck.pop())

        return hand

    def take_action(self, player: Player) -> None:
        fascist_count = self.enacted_policies[Policy.fascist]
        match fascist_count:
            case 3:
                player.action_investigate_loyalty(
                    1, players=[p for p in self.valid_players() if p != player]
                )
            case 4:
                return
            case 5:
                return
            case _:
                return

    def play_game(self) -> None:
        elected_chancellor = None
        elected_president = None

        game_state = 1
        turn_num = 0
        while True:
            # Current state:
            print(f"\n{' NEW ROUND ':-^80}")
            print(
                f"\nFacist policies: {self.enacted_policies[Policy.fascist]} / Liberal policies: {self.enacted_policies[Policy.liberal]}"
            )

            # Cycle president:
            nominated_president = self.players[turn_num % len(self.players)]
            if not self.valid_president(nominated_president):
                turn_num += 1
                continue

            # Nominate a chancellor:
            print("President: ", nominated_president.name)
            print(
                f"Valid chancellors = ({', '.join([x.name for x in self.valid_chancellors(nominated_president, elected_president, elected_chancellor)])})"
            )
            nominated_chancellor = nominated_president.nominate_chancellor(
                game_state,
                self.valid_chancellors(nominated_president, elected_president, elected_chancellor),
            )

            # Vote in the current government:
            voters = self.valid_voters(nominated_president, nominated_chancellor)
            # votes = [
            #     p.vote_on_government(game_state, nominated_president, nominated_chancellor)
            #     for p in voters
            # ]
            votes = [True for v in voters]
            if sum(votes) > len(votes) // 2:
                print("The government was elected successfully")
                elected_chancellor = nominated_chancellor
                elected_president = nominated_president
                nominated_chancellor = None
                nominated_president = None
            else:
                print("The government was not elected")
                continue

            # President selects policy options:
            policy_options = self.draw_policies()
            policy_proposal = elected_president.propose_policies(game_state, policy_options)
            self.discard_deck.extend(policy_proposal.discarded)

            # Chancellor enacts policy:
            policy_selection = elected_chancellor.enact_policy(game_state, policy_proposal.selected)
            self.discard_deck.extend(policy_selection.discarded)
            policy = policy_selection.selected[0]

            self.enacted_policies[policy] += 1

            # Action to be taken:
            if policy == Policy.fascist:
                self.take_action(elected_president)

            turn_num += 1
            if turn_num > 10:
                break
