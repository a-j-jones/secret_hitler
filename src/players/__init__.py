from src.players.base import Player
from src.players.gemini import GeminiPlayer
from src.players.terminal import TerminalPlayer

base_players = [Player]
players = [TerminalPlayer, GeminiPlayer]

Player.model_rebuild()
TerminalPlayer.model_rebuild()
GeminiPlayer.model_rebuild()
