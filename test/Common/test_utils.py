from src.Common.utils import parse_boolean


def test_lowercase_string_is_properly_inferred():
    assert parse_boolean("true")
    assert not parse_boolean("false")
