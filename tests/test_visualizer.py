"""Tests for terminal visual feedback."""

from src.parser.parser import Parser
from src.simulation.simulation import Simulation
from src.visualization.visualizer import Visualizer


def test_zone_metadata_color_is_used() -> None:
    parsed = Parser().parse_text("""
nb_drones: 1
start_hub: start 0 0 [color=green]
end_hub: goal 1 0 [color=red]
connection: start-goal
""")
    visualizer = Visualizer(parsed.graph)
    rendered = visualizer.render_turn(1, "D1-goal", True)

    assert rendered.startswith("Tour 1: ")
    assert "\033[31mD1-goal\033[0m" in rendered


def test_visual_result_displays_total_turns() -> None:
    parsed = Parser().parse_text("""
nb_drones: 1
start_hub: start 0 0
end_hub: goal 1 0
connection: start-goal
""")
    rendered = Visualizer(parsed.graph).render_result(7)
    assert "SIMULATION COMPLETE - 7 turns" in rendered
    assert rendered.startswith("\033[")


def test_dashboard_explains_positions_capacity_and_progress() -> None:
    parsed = Parser().parse_text("""
nb_drones: 2
start_hub: start 0 0 [color=green]
hub: middle 1 0 [color=blue]
end_hub: goal 2 0 [color=red]
connection: start-middle
connection: middle-goal
""")
    simulation = Simulation(parsed.graph, parsed.nb_drones)
    movement = simulation._run_turn()
    rendered = Visualizer(parsed.graph).render_dashboard(
        simulation,
        1,
        movement,
    )

    assert "TURN 1" in rendered
    assert "D1: entered" in rendered
    assert "DRONE POSITIONS" in rendered
    assert "OCCUPIED ZONES" in rendered
    assert "capacity 1/1 FULL" in rendered
    assert "Delivered: 0/2" in rendered
