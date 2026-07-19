"""Tests for valid path generation and zone-type choices."""

from src.algorithm.pathfinder import PathFinder
from src.parser.parser import Parser


def test_linear_path_is_found() -> None:
    parsed = Parser().parse_text("""
nb_drones: 1
start_hub: start 0 0
hub: middle 1 0
end_hub: goal 2 0
connection: start-middle
connection: middle-goal
""")
    assert PathFinder(parsed.graph).find_paths()[0] == [
        "start", "middle", "goal",
    ]


def test_blocked_zone_is_never_used() -> None:
    parsed = Parser().parse_text("""
nb_drones: 1
start_hub: start 0 0
hub: blocked 1 0 [zone=blocked]
hub: open 1 1
end_hub: goal 2 0
connection: start-blocked
connection: blocked-goal
connection: start-open
connection: open-goal
""")
    paths = PathFinder(parsed.graph).find_paths()
    assert paths == [["start", "open", "goal"]]


def test_priority_zone_is_preferred_for_equal_cost_paths() -> None:
    parsed = Parser().parse_text("""
nb_drones: 1
start_hub: start 0 0
hub: normal 1 0
hub: preferred 1 1 [zone=priority]
end_hub: goal 2 0
connection: start-normal
connection: normal-goal
connection: start-preferred
connection: preferred-goal
""")
    paths = PathFinder(parsed.graph).find_paths()
    assert paths[0] == ["start", "preferred", "goal"]


def test_restricted_cost_is_included_in_path_cost() -> None:
    parsed = Parser().parse_text("""
nb_drones: 1
start_hub: start 0 0
hub: restricted 1 0 [zone=restricted]
end_hub: goal 2 0
connection: start-restricted
connection: restricted-goal
""")
    finder = PathFinder(parsed.graph)
    path = finder.find_paths()[0]
    assert finder.path_cost(path) == 3
