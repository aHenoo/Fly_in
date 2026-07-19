"""Tests for valid input parsing and parser error handling."""

import pytest

from src.graph.zone import ZoneType
from src.parser.parser import ParseError, Parser


VALID_MAP = """
# Comments and blank lines must be ignored.
nb_drones: 3

start_hub: start 0 0 [color=green max_drones=3]
hub: normal 1 0
hub: special 2 0 [zone=priority color=cyan max_drones=2]
end_hub: goal 3 0 [color=red max_drones=3]

connection: start-normal
connection: normal-special [max_link_capacity=2]
connection: special-goal
"""


def test_valid_format_metadata_comments_and_defaults(parser: Parser) -> None:
    parsed = parser.parse_text(VALID_MAP)

    assert parsed.nb_drones == 3
    assert parsed.graph.start_name == "start"
    assert parsed.graph.end_name == "goal"
    assert parsed.graph.get_zone("normal").zone_type is ZoneType.NORMAL
    assert parsed.graph.get_zone("normal").max_drones == 1
    assert parsed.graph.get_zone("special").zone_type is ZoneType.PRIORITY
    assert parsed.graph.get_zone("special").color == "cyan"
    assert parsed.graph.get_zone("special").max_drones == 2
    default_connection = parsed.graph.get_connection("start", "normal")
    custom_connection = parsed.graph.get_connection("normal", "special")
    assert default_connection.max_link_capacity == 1
    assert custom_connection.max_link_capacity == 2


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("", "nb_drones manquant"),
        ("start_hub: start 0 0", "premiere ligne utile"),
        ("nb_drones: one", "nb_drones doit etre un entier"),
        ("nb_drones: 1\nthis is invalid", "ligne inconnue"),
        (
            "nb_drones: 1\nstart_hub: start 0 0\nend_hub: goal 1 0"
            "\nconnection: start-goal\nhub: late 2 0",
            "zone ne peut pas etre apres une connexion",
        ),
    ],
)
def test_malformed_inputs_are_rejected(content: str, message: str) -> None:
    with pytest.raises(ParseError, match=message):
        Parser().parse_text(content)


@pytest.mark.parametrize("zone_type", ["fast", "dangerous", "NORMAL"])
def test_invalid_zone_types_are_rejected(zone_type: str) -> None:
    content = f"""
nb_drones: 1
start_hub: start 0 0
hub: middle 1 0 [zone={zone_type}]
end_hub: goal 2 0
connection: start-middle
connection: middle-goal
"""
    with pytest.raises(ParseError, match="type de zone invalide"):
        Parser().parse_text(content)


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("nb_drones: 1\nend_hub: goal 1 0", "missing start zone"),
        ("nb_drones: 1\nstart_hub: start 0 0", "missing end zone"),
    ],
)
def test_missing_start_or_end_is_rejected(content: str, message: str) -> None:
    with pytest.raises(ParseError, match=message):
        Parser().parse_text(content)


@pytest.mark.parametrize("value", ["0", "-1", "many"])
@pytest.mark.parametrize("prefix", ["start_hub", "hub", "end_hub"])
def test_invalid_zone_capacities_are_rejected(
    value: str,
    prefix: str,
) -> None:
    lines = ["nb_drones: 1"]
    lines.append("start_hub: start 0 0" if prefix != "start_hub" else
                 f"start_hub: start 0 0 [max_drones={value}]")
    if prefix == "hub":
        lines.append(f"hub: middle 1 0 [max_drones={value}]")
    lines.append("end_hub: goal 2 0" if prefix != "end_hub" else
                 f"end_hub: goal 2 0 [max_drones={value}]")

    with pytest.raises(ParseError, match="max_drones doit etre"):
        Parser().parse_text("\n".join(lines))


@pytest.mark.parametrize("value", ["0", "-2", "many"])
def test_invalid_connection_capacities_are_rejected(value: str) -> None:
    content = f"""
nb_drones: 1
start_hub: start 0 0
end_hub: goal 1 0
connection: start-goal [max_link_capacity={value}]
"""
    with pytest.raises(ParseError, match="max_link_capacity doit etre"):
        Parser().parse_text(content)


def test_duplicate_zone_is_rejected() -> None:
    content = """
nb_drones: 1
start_hub: start 0 0
hub: start 1 0
end_hub: goal 2 0
connection: start-goal
"""
    with pytest.raises(ParseError, match="duplicate zone"):
        Parser().parse_text(content)


def test_duplicate_connection_in_reverse_is_rejected() -> None:
    content = """
nb_drones: 1
start_hub: start 0 0
end_hub: goal 1 0
connection: start-goal
connection: goal-start
"""
    with pytest.raises(ParseError, match="duplicate connection"):
        Parser().parse_text(content)


def test_connection_to_unknown_zone_is_rejected() -> None:
    content = """
nb_drones: 1
start_hub: start 0 0
end_hub: goal 1 0
connection: start-unknown
"""
    with pytest.raises(ParseError, match="unknown zone"):
        Parser().parse_text(content)
