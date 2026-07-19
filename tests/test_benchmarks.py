"""Regression tests for the maps and turn targets in the evaluation grid."""

import pytest

from src.parser.parser import Parser
from src.simulation.simulation import Simulation

from conftest import MAPS


BENCHMARKS = [
    ("easy/01_linear_path.txt", 6),
    ("easy/02_simple_fork.txt", 6),
    ("easy/03_basic_capacity.txt", 8),
    ("medium/01_dead_end_trap.txt", 15),
    ("medium/02_circular_loop.txt", 20),
    ("medium/03_priority_puzzle.txt", 12),
    ("hard/01_maze_nightmare.txt", 45),
    ("hard/02_capacity_hell.txt", 60),
    ("hard/03_ultimate_challenge.txt", 35),
]


@pytest.mark.parametrize(("relative_path", "maximum_turns"), BENCHMARKS)
def test_reference_map_meets_turn_target(
    relative_path: str,
    maximum_turns: int,
) -> None:
    parsed = Parser().parse_file(str(MAPS / relative_path))
    output = Simulation(parsed.graph, parsed.nb_drones).run()
    assert len(output) <= maximum_turns


def test_easy_medium_and_hard_average_ranges() -> None:
    results: dict[str, list[int]] = {"easy": [], "medium": [], "hard": []}
    for relative_path, _target in BENCHMARKS:
        parsed = Parser().parse_file(str(MAPS / relative_path))
        turns = len(Simulation(parsed.graph, parsed.nb_drones).run())
        results[relative_path.split("/", 1)[0]].append(turns)

    assert sum(results["easy"]) / len(results["easy"]) < 10
    assert 10 <= sum(results["medium"]) / len(results["medium"]) <= 30
    assert sum(results["hard"]) / len(results["hard"]) < 60


def test_challenger_map_completes() -> None:
    parsed = Parser().parse_file(
        str(MAPS / "challenger/01_the_impossible_dream.txt")
    )
    simulation = Simulation(parsed.graph, parsed.nb_drones)
    output = simulation.run()
    assert output
    assert all(drone.is_delivered() for drone in simulation.drones)
    assert len(output) <= 45
