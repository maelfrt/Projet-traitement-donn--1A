from typing import Union
from src.Common.utils import parse_boolean


class Player:
    def __init__(self, id: int, full_name: str, is_the_goat: Union[str, bool]):
        self.id = id
        self.full_name = full_name
        self.is_the_goat = parse_boolean(is_the_goat)

    def __repr__(self):
        display_string = self.full_name
        if self.is_the_goat:
            display_string += " (GOAT)"
        return display_string
