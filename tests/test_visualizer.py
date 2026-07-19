"""Tests for terminal visual feedback."""

from src.parser.parser import Parser
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
    assert "Resultat: 7 tours" in rendered
    assert rendered.startswith("\033[")
