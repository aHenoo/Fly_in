"""Point d'entree du projet Fly-in."""

from __future__ import annotations

import sys

from src.parser.parser import ParseError, Parser
from src.simulation.simulation import Simulation, SimulationError


def main() -> int:
    """Lance le parsing puis la simulation."""
    if len(sys.argv) != 2:
        print("usage: python3 main.py <map_file>", file=sys.stderr)
        return 1

    try:
        parsed_map = Parser().parse_file(sys.argv[1])
        simulation = Simulation(parsed_map.graph, parsed_map.nb_drones)
        for turn, line in enumerate(simulation.run(), 1):
            print(f"Tour {turn}: {line}")
    except (ParseError, SimulationError, ValueError, KeyError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
