from __future__ import annotations

import sys

from src.parser.parser import ParseError, Parser
from src.simulation.simulation import Simulation, SimulationError
from src.visualization.visualizer import Visualizer


def main() -> int:
    """Lance le parsing puis la simulation."""
    if len(sys.argv) not in (2, 3):
        print("usage: python3 main.py <map_file> [--visual]", file=sys.stderr)
        return 1
    if len(sys.argv) == 3 and sys.argv[2] != "--visual":
        print("usage: python3 main.py <map_file> [--visual]", file=sys.stderr)
        return 1

    try:
        parsed_map = Parser().parse_file(sys.argv[1])
        simulation = Simulation(parsed_map.graph, parsed_map.nb_drones)
        visualizer = Visualizer(parsed_map.graph)
        show_visual = len(sys.argv) == 3
        lines = simulation.run()
        for turn, line in enumerate(lines, 1):
            if show_visual:
                print(visualizer.render_turn(turn, line, True))
            else:
                print(line)
        if show_visual:
            print(visualizer.render_result(len(lines)))
    except (ParseError, SimulationError, ValueError, KeyError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
