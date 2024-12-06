from src.game import Game

if __name__ == "__main__":
    human_players = ["Adam", "Lauren", "Ed", "Ben", "Tom", "Tegan"]
    ai_players = []
    game = Game(human_players, ai_players)

    print("Players:")
    for player in game.players:
        print(player)

    game.play_game()
