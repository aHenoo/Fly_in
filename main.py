from __future__ import annotations

import sys

from src.parser.parser import ParseError, Parser
from src.simulation.simulation import Simulation, SimulationError
from src.visualization.visualizer import Visualizer


VALID_MODES = {"--visual", "--gui"}


def main() -> int:
    """Lance le parsing puis la simulation."""
    arguments = sys.argv[1:]
    mode: str | None
    filename: str

    if len(arguments) not in (1, 2):
        print(
            "usage: python3 main.py [--visual|--gui] <map_file>",
            file=sys.stderr,
        )
        return 1

    if len(arguments) == 2 and arguments[0].startswith("--"):
        mode, filename = arguments
    else:
        filename = arguments[0]
        mode = arguments[1] if len(arguments) == 2 else None

    if mode is not None and mode not in VALID_MODES:
        print(
            "usage: python3 main.py [--visual|--gui] <map_file>",
            file=sys.stderr,
        )
        return 1

    try:
        parsed_map = Parser().parse_file(filename)
        simulation = Simulation(parsed_map.graph, parsed_map.nb_drones)
        visualizer = Visualizer(parsed_map.graph)
        show_visual = mode == "--visual"
        if mode == "--gui":
            from src.visualization.gui import GUIError, SimulationGUI

            try:
                SimulationGUI(parsed_map.graph, simulation).run()
            except GUIError as error:
                raise SimulationError(
                    f"cannot start graphical interface: {error}",
                ) from error
            return 0
        if show_visual:
            print(visualizer.render_header(simulation))

            def display_turn(turn: int, line: str) -> None:
                print(visualizer.render_dashboard(simulation, turn, line))

            lines = simulation.run(on_turn=display_turn)
            print(visualizer.render_result(len(lines)))
        else:
            lines = simulation.run()
            for line in lines:
                print(line)
    except (ParseError, SimulationError, ValueError, KeyError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
