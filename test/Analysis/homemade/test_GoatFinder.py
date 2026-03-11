from src.Analysis.homemade.GoatFinder import find_the_goat
from src.Model.Player import Player


def test_find_the_goat():
    player1 = Player(1, "Player 1", False)
    player2 = Player(2, "Player 2", False)
    player3 = Player(3, "Spieler 3", True)
    player4 = Player(4, "Player 4", False)
    players_list = [player1, player2, player3, player4]

    the_goat = find_the_goat(players_list)

    assert the_goat.full_name == "Spieler 3"
