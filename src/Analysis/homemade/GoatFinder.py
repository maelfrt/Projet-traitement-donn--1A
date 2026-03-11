from src.Model.Player import Player


def find_the_goat(players: list[Player]):
    # Nice use of lambda, an under-used feature of Python...
    # But is it worth it in terms of performance? 😱
    goats = list(filter(lambda player: player.is_the_goat, players))
    if not len(goats) == 1:
        raise ValueError("There can only be one GOAT")
    return goats[0]
