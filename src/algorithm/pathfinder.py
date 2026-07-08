from __future__ import annotations

from heapq import heappop, heappush

from src.graph.graph import Graph
from src.graph.zone import Zone


class PathFinder:
    """Trouve des chemins candidats dans le graphe."""

    def __init__(self, graph: Graph) -> None:
        """Initialise le pathfinder."""
        self.graph = graph
        self._counter = 0
        self._distance_to_end = self._build_distances_to_end()

    def find_paths(self, max_paths: int = 32) -> list[list[str]]:
        """Renvoie plusieurs chemins start -> end."""
        start = self.graph.get_start().name
        end = self.graph.get_end().name
        queue: list[tuple[int, int, int, list[str]]] = []
        results: list[list[str]] = []

        heappush(queue, (0, 0, self._next_counter(), [start]))
        while queue and len(results) < max_paths:
            cost, priority_score, _counter, path = heappop(queue)
            current = path[-1]

            if current == end:
                results.append(path)
                continue

            for neighbor in self._sorted_neighbors(current):
                if neighbor.name in path:
                    continue
                if not self._moves_toward_end(current, neighbor.name):
                    continue
                next_path = path + [neighbor.name]
                next_cost = cost + neighbor.get_movement_cost()
                next_priority = priority_score + self._priority_penalty(
                    neighbor,
                )
                heappush(
                    queue,
                    (
                        next_cost,
                        next_priority,
                        self._next_counter(),
                        next_path,
                    ),
                )

        return results

    def path_cost(self, path: list[str]) -> int:
        """Calcule le cout d'un chemin."""
        cost = 0
        for zone_name in path[1:]:
            cost += self.graph.get_zone(zone_name).get_movement_cost()
        return cost

    def _sorted_neighbors(self, zone_name: str) -> list[Zone]:
        """Trie les voisins pour favoriser les zones priority."""
        neighbors = self.graph.neighbors(zone_name)
        return sorted(
            neighbors,
            key=lambda zone: (
                self._priority_penalty(zone),
                zone.get_movement_cost(),
                zone.name,
            ),
        )

    def _priority_penalty(self, zone: Zone) -> int:
        """Renvoie un petit malus hors zone priority."""
        if zone.is_priority():
            return 0
        return 1

    def _moves_toward_end(self, current: str, neighbor: str) -> bool:
        """Evite les detours qui eloignent de l'arrivee."""
        current_distance = self._distance_to_end.get(current)
        neighbor_distance = self._distance_to_end.get(neighbor)
        if current_distance is None or neighbor_distance is None:
            return False
        return neighbor_distance < current_distance

    def _build_distances_to_end(self) -> dict[str, int]:
        """Calcule le cout minimal de chaque zone vers end."""
        end = self.graph.get_end().name
        distances: dict[str, int] = {end: 0}
        queue: list[tuple[int, int, str]] = []
        heappush(queue, (0, self._next_counter(), end))

        while queue:
            cost, _counter, zone_name = heappop(queue)
            if cost != distances[zone_name]:
                continue
            for neighbor in self.graph.neighbors(zone_name):
                next_cost = cost + self.graph.get_zone(
                    zone_name,
                ).get_movement_cost()
                known_cost = distances.get(neighbor.name)
                if known_cost is None or next_cost < known_cost:
                    distances[neighbor.name] = next_cost
                    heappush(
                        queue,
                        (next_cost, self._next_counter(), neighbor.name),
                    )

        return distances

    def _next_counter(self) -> int:
        """Renvoie un compteur stable pour heapq."""
        self._counter += 1
        return self._counter
