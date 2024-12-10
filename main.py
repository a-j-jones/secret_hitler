from src.game import Game

if __name__ == "__main__":
    human_players = ["Adam"]
    ai_players = ["Ed", "Ben", "Tom", "Brogan", "Dan"]
    game = Game(human_players, ai_players)

    print("Players:")
    for player in game.players:
        print(repr(player))

    game.play_game()
