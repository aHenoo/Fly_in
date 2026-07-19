*This project has been created as part of the 42 curriculum by aheno.*

# Fly-in

## Description

Fly-in is a turn-based drone-routing simulator. It reads a map describing hubs,
connections, capacities, and zone types, then plans and simulates the movement
of every drone from a start hub to an end hub.

The goal is to deliver all drones in as few turns as reasonably possible while
respecting the following constraints:

- a hub cannot contain more drones than its `max_drones` capacity;
- a connection cannot carry more drones per turn than its
  `max_link_capacity`;
- normal and priority zones take one turn to enter;
- restricted zones take two turns to enter;
- blocked zones cannot be used;
- start and end hubs may contain any number of drones.

The program supports maps with multiple paths, loops, dead ends, bottlenecks,
and different zone priorities. Example maps are available in the [`maps`](maps)
directory, grouped by difficulty.

## Features

- Strict parsing of the Fly-in map format
- Clear validation errors with line numbers when possible
- Capacity-aware, turn-based drone simulation
- Weighted pathfinding for normal and restricted zones
- Preference for priority zones when paths have comparable costs
- Avoidance of blocked zones and dead ends
- Distribution of drones across multiple candidate paths
- Optional colored terminal visualization
- Easy, medium, hard, and challenger example maps

## Instructions

### Requirements

- Python 3.10 or later
- `make` for the convenience commands

The simulator itself only uses the Python standard library.

### Installation

To create a virtual environment and install the project together with its
development tools:

```bash
make install
```

This installs the optional development dependencies `pytest`, `flake8`, and
`mypy`.

Installation is not required for a normal execution. The program can be run
directly with Python from the repository root.

### Execution

Run the default example map:

```bash
make run
```

Run a specific map:

```bash
python3 main.py maps/easy/01_linear_path.txt
```

Enable colored visual feedback and turn numbers:

```bash
python3 main.py maps/easy/01_linear_path.txt --visual
```

The map used by `make run` can also be changed on the command line:

```bash
make run MAP=maps/hard/01_maze_nightmare.txt
make run MAP=maps/medium/03_priority_puzzle.txt VISUAL=--visual
```

Run the style and type checks after `make install`:

```bash
make lint
```

## Input Format

Blank lines and text beginning with `#` are ignored. The first useful line must
declare the number of drones:

```text
nb_drones: <positive integer>
```

It is followed by the zone definitions:

```text
start_hub: <name> <x> <y> [metadata]
hub: <name> <x> <y> [metadata]
end_hub: <name> <x> <y> [metadata]
```

Supported zone metadata is:

- `zone=normal|restricted|priority|blocked` (default: `normal`)
- `max_drones=<positive integer>` (default: `1` for regular hubs)
- `color=<color name>`

Connections must be declared after all zones:

```text
connection: <zone1>-<zone2> [max_link_capacity=<positive integer>]
```

The default connection capacity is `1`. Zone names cannot contain spaces or
hyphens because hyphens separate connection endpoints.

## Example

### Input

```text
# Two drones on a linear route
nb_drones: 2

start_hub: start 0 0 [color=green]
hub: waypoint1 1 0 [color=blue]
hub: waypoint2 2 0 [color=blue]
end_hub: goal 3 0 [color=red]

connection: start-waypoint1
connection: waypoint1-waypoint2
connection: waypoint2-goal
```

### Expected output

```text
D1-waypoint1
D1-waypoint2 D2-waypoint1
D1-goal D2-waypoint2
D2-goal
```

Each output line represents one simulation turn. A token in the form
`D<ID>-<zone>` means that a drone entered a zone. When a drone starts a
multi-turn move into a restricted zone, its position on the connection is
shown as `D<ID>-<zone1>-<zone2>`. Drones that do not move during a turn are
omitted.

## Algorithm and Implementation Strategy

### 1. Parsing and graph construction

The parser reads the file once and builds an undirected graph. Zones are stored
by name, connections by their unordered pair of endpoints, and adjacency lists
provide efficient neighbor access.

Parsing is deliberately strict. It rejects unknown metadata, duplicate zones
or connections, invalid capacities, unknown connection endpoints, malformed
lines, and maps without exactly one start and one end hub. This prevents the
simulation from operating on an ambiguous graph.

### 2. Weighted distances to the destination

Before generating routes, the pathfinder runs Dijkstra's algorithm backwards
from the end hub. Entering a normal or priority zone costs one turn, while
entering a restricted zone costs two. Blocked zones are excluded from neighbor
lists.

The resulting distance table serves two purposes:

- it identifies zones from which the destination is reachable;
- it prevents candidate routes from moving away from the destination.

Only neighbors whose distance is strictly lower than the current zone's
distance are considered. This avoids cycles and dead ends while keeping route
generation focused on efficient paths.

### 3. Candidate path generation

Candidate paths are explored with a priority queue. They are ordered primarily
by total movement cost and secondarily by a priority score. Priority zones add
no preference penalty, whereas other accessible zones do, so priority hubs are
favored when costs are otherwise similar.

Path generation is capped at 128 candidate paths. This limit prevents maps
with many branches from causing uncontrolled path enumeration while still
offering enough alternatives for drone distribution.

### 4. Drone distribution

Each drone is assigned to the path with the smallest score:

```text
path movement cost + number of drones already assigned to that path
```

This lightweight load-balancing strategy spreads drones across useful routes
instead of sending every drone through the same shortest-path bottleneck.

### 5. Turn-based scheduling

At the beginning of each turn, the simulator calculates current zone occupancy
and reservations for drones already moving toward restricted zones. Drones
already in transit are advanced first, then waiting drones are considered for
new movements.

A movement is scheduled only if:

- the target zone has free or reserved capacity;
- the connection has remaining capacity for the current turn;
- the drone is ready to advance on its assigned path.

Waiting drones with the least remaining path length are considered first. This
helps drones near the destination leave intermediate zones quickly and frees
capacity for following drones.

For a restricted destination, the first output records the drone on the
connection. Its arrival is recorded on the following turn. Target capacity is
reserved during transit so another drone cannot take the same place.

The simulation stops as soon as all drones reach the end hub. If no movement is
possible before that point, it reports an error instead of looping forever.

### Complexity

Let `V` be the number of zones, `E` the number of connections, `D` the number
of drones, `P` the number of generated candidate paths, and `T` the number of
simulation turns.

- Parsing and graph construction: `O(V + E)`
- Weighted distance calculation: `O((V + E) log V)`
- Candidate path exploration: dependent on graph branching and path count;
  bounded in practice by `P <= 128`
- Path assignment: `O(D * P)`
- Simulation: approximately `O(T * D)`, excluding small dictionary operations
- Graph storage: `O(V + E)`

The route generator deliberately trades exhaustive global optimization for
predictable runtime. The result may not always be the theoretical minimum
number of turns, but it performs well on maps with capacities, bottlenecks,
loops, and multiple routes.

## Visual Representation

The optional `--visual` mode improves readability without changing the
machine-friendly default output.

It provides:

- an initial map summary, legend, and list of assigned routes;
- a separate dashboard for every numbered turn;
- readable movement descriptions, including multi-turn transit;
- the current position and status of every drone;
- zone occupancy with current and maximum capacities;
- a delivery counter and progress bar;
- ANSI colors derived from each destination zone's `color` metadata;
- a final colored summary showing the total number of turns.

For example, a drone entering a blue hub is displayed in blue, while entry into
a red destination is displayed in red. Common names such as `red`, `green`,
`blue`, `cyan`, `orange`, `gold`, and `purple` are mapped to suitable terminal
colors. If a color is absent or unsupported, the movement remains readable as
plain text.

The dashboard makes waiting drones and full bottleneck zones visible, while
restricted-zone movements explicitly show when a drone is still in transit.
This provides the context needed to understand why drones do not all move at
the same time.

Because ANSI escape sequences are only enabled with `--visual`, the standard
output remains suitable for scripts, automated evaluation, and comparison
tools.

## Project Structure

```text
.
├── main.py                    Command-line entry point
├── maps/                      Example and benchmark maps
├── src/
│   ├── algorithm/             Weighted pathfinding
│   ├── graph/                 Zone, connection, and graph models
│   ├── parser/                Input parsing and validation
│   ├── simulation/            Drone state and turn scheduler
│   └── visualization/         ANSI terminal rendering
├── Makefile
└── pyproject.toml
```

## Resources

### References

- [Dijkstra's shortest path algorithm](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)

These resources were used to review graph representation, priority-queue-based
shortest paths, terminal color rendering, Python project organization, and the
complexity terminology used in this documentation.

### Use of AI

AI assistance was used to design and execute additional parser and simulation test scenarios, identify edge cases, measure the supplied benchmark maps, and help draft and
structure this README.
