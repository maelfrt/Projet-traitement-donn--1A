from src.Parsers.parse_csv import parse_players_csv


def test_parse_players_csv_returns_an_ordered_list_of_players():
    players = parse_players_csv("./players.csv")
    assert len(players) == 2
    assert players[0].name == "Ousmane Dembélé"
    assert players[1].name == "Stéphane Guivarc'h"
