"""Tests for movements, capacities, conflicts, output, and termination."""

import re

import pytest

from src.parser.parser import Parser
from src.simulation.simulation import Simulation, SimulationError


def simulate(content: str) -> tuple[Simulation, list[str]]:
    """Parse and run an inline map."""
    parsed = Parser().parse_text(content)
    simulation = Simulation(parsed.graph, parsed.nb_drones)
    return simulation, simulation.run()


def test_single_drone_linear_output_and_termination() -> None:
    simulation, output = simulate("""
nb_drones: 1
start_hub: start 0 0
hub: middle 1 0
end_hub: goal 2 0
connection: start-middle
connection: middle-goal
""")
    assert output == ["D1-middle", "D1-goal"]
    assert all(drone.is_delivered() for drone in simulation.drones)


def test_stationary_drones_are_omitted() -> None:
    _, output = simulate("""
nb_drones: 3
start_hub: start 0 0
hub: bottleneck 1 0
end_hub: goal 2 0
connection: start-bottleneck
connection: bottleneck-goal
""")
    assert output[0] == "D1-bottleneck"
    assert "D2-" not in output[0]
    assert "D3-" not in output[0]


def test_default_zone_and_connection_capacity_are_enforced() -> None:
    _, output = simulate("""
nb_drones: 3
start_hub: start 0 0
hub: middle 1 0
end_hub: goal 2 0
connection: start-middle
connection: middle-goal
""")
    for line in output:
        assert sum(token.endswith("-middle") for token in line.split()) <= 1


def test_high_zone_and_connection_capacity_allow_simultaneous_moves() -> None:
    _, output = simulate("""
nb_drones: 3
start_hub: start 0 0
hub: middle 1 0 [max_drones=3]
end_hub: goal 2 0
connection: start-middle [max_link_capacity=3]
connection: middle-goal [max_link_capacity=3]
""")
    assert output == [
        "D1-middle D2-middle D3-middle",
        "D1-goal D2-goal D3-goal",
    ]


def test_start_and_end_allow_multiple_drones() -> None:
    _, output = simulate("""
nb_drones: 4
start_hub: start 0 0
end_hub: goal 1 0
connection: start-goal [max_link_capacity=4]
""")
    assert output == ["D1-goal D2-goal D3-goal D4-goal"]


def test_restricted_zone_takes_two_turns_and_reserves_capacity() -> None:
    _, output = simulate("""
nb_drones: 2
start_hub: start 0 0
hub: slow 1 0 [zone=restricted]
end_hub: goal 2 0
connection: start-slow [max_link_capacity=2]
connection: slow-goal
""")
    assert output == [
        "D1-start-slow",
        "D1-slow",
        "D1-goal D2-start-slow",
        "D2-slow",
        "D2-goal",
    ]


def test_competing_drones_never_exceed_zone_occupancy() -> None:
    parsed = Parser().parse_text("""
nb_drones: 6
start_hub: start 0 0
hub: gate 1 0 [max_drones=2]
hub: exit 2 0 [max_drones=2]
end_hub: goal 3 0
connection: start-gate [max_link_capacity=4]
connection: gate-exit [max_link_capacity=4]
connection: exit-goal [max_link_capacity=4]
""")
    simulation = Simulation(parsed.graph, parsed.nb_drones)

    while not simulation._all_delivered():
        assert simulation._run_turn()
        occupancy: dict[str, int] = {}
        for drone in simulation.drones:
            if drone.status.value == "waiting":
                occupancy[drone.current_zone] = (
                    occupancy.get(drone.current_zone, 0) + 1
                )
        assert occupancy.get("gate", 0) <= 2
        assert occupancy.get("exit", 0) <= 2


def test_output_format_contains_only_movements() -> None:
    _, output = simulate("""
nb_drones: 2
start_hub: start 0 0
hub: slow 1 0 [zone=restricted]
end_hub: goal 2 0
connection: start-slow
connection: slow-goal
""")
    token_pattern = re.compile(r"^D[1-9][0-9]*-[^ ]+$")
    assert all(line for line in output)
    assert all(
        token_pattern.fullmatch(token)
        for line in output
        for token in line.split()
    )


def test_disconnected_graph_fails_gracefully() -> None:
    parsed = Parser().parse_text("""
nb_drones: 1
start_hub: start 0 0
hub: isolated 1 0
end_hub: goal 2 0
connection: start-isolated
""")
    with pytest.raises(SimulationError, match="aucun chemin"):
        Simulation(parsed.graph, parsed.nb_drones)


def test_high_capacity_value_is_supported() -> None:
    _, output = simulate("""
nb_drones: 50
start_hub: start 0 0 [max_drones=50]
end_hub: goal 1 0 [max_drones=50]
connection: start-goal [max_link_capacity=50]
""")
    assert len(output) == 1
    assert len(output[0].split()) == 50
