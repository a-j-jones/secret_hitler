from collections import defaultdict

from src.game import Game
from src.players import Role


def test_player_counts():
    liberal_mapping = {5: 3, 6: 4, 7: 4, 8: 5, 9: 5, 10: 6}

    for player_count in liberal_mapping.keys():
        player_names = [f"Player{str(i+1)}" for i in range(player_count)]
        game = Game(player_names, [])

        role_counts = defaultdict(int)
        for player in game.players:
            role_counts[player.role] += 1

        assert role_counts[Role.liberal] == liberal_mapping[player_count]
        assert role_counts[Role.hitler] == 1
