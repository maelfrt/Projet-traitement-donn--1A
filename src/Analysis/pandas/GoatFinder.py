import pandas as pd

from src.Model.Player import Player


def find_the_goat_in_df(players: pd.DataFrame) -> Player:
    goats: pd.DataFrame = players[players["is_the_goat"]]
    if not len(goats) == 1:
        raise ValueError("There can only be one GOAT")
    the_goat: pd.Series = goats.iloc[0]
    return Player(
        id=the_goat.at["id"],
        full_name=the_goat.at["full_name"],
        is_the_goat=the_goat.at["is_the_goat"],
    )
