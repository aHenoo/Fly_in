from __future__ import annotations

from collections.abc import Callable

from src.algorithm.pathfinder import PathFinder
from src.graph.connection import Connection
from src.graph.graph import Graph
from src.graph.zone import Zone
from src.simulation.drone import Drone, DroneStatus


class SimulationError(Exception):
    """Erreur pendant la simulation."""


class Simulation:
    """Planifie les drones jusqu'a la zone finale."""

    def __init__(self, graph: Graph, nb_drones: int) -> None:
        """Initialise la simulation."""
        if nb_drones < 1:
            raise SimulationError("nb_drones doit etre positif")
        self.graph = graph
        self.nb_drones = nb_drones
        self.drones = self._create_drones()
        self.paths = self._assign_paths()
        self.path_index: dict[int, int] = {}
        for drone in self.drones:
            self.path_index[drone.identifier] = 0

    def run(
        self,
        max_turns: int = 10000,
        on_turn: Callable[[int, str], None] | None = None,
    ) -> list[str]:
        """Lance la simulation et renvoie les lignes de sortie."""
        output: list[str] = []
        turns = 0

        while not self._all_delivered():
            if turns >= max_turns:
                raise SimulationError("simulation trop longue")
            line = self.run_turn()
            output.append(line)
            turns += 1
            if on_turn is not None:
                on_turn(turns, line)

        return output

    def run_turn(self) -> str:
        """Execute un seul tour pour les interfaces interactives."""
        if self._all_delivered():
            raise SimulationError("simulation deja terminee")
        line = self._run_turn()
        if not line:
            raise SimulationError("aucun mouvement possible")
        return line

    def is_complete(self) -> bool:
        """Indique publiquement si tous les drones sont arrives."""
        return self._all_delivered()

    def _create_drones(self) -> list[Drone]:
        """Cree les drones au depart."""
        start_name = self.graph.get_start().name
        drones: list[Drone] = []
        for identifier in range(1, self.nb_drones + 1):
            drones.append(Drone(identifier, start_name))
        return drones

    def _assign_paths(self) -> dict[int, list[str]]:
        """Distribue les drones sur les chemins candidats."""
        finder = PathFinder(self.graph)
        paths = finder.find_paths(128)
        if not paths:
            raise SimulationError("aucun chemin vers l'arrivee")

        loads = [0 for _path in paths]
        assigned: dict[int, list[str]] = {}
        for identifier in range(1, self.nb_drones + 1):
            path_index = self._best_path_index(finder, paths, loads)
            assigned[identifier] = paths[path_index]
            loads[path_index] += 1

        return assigned

    def _best_path_index(
        self,
        finder: PathFinder,
        paths: list[list[str]],
        loads: list[int],
    ) -> int:
        """Choisit le chemin le moins charge."""
        best_index = 0
        best_score: int | None = None

        for index, path in enumerate(paths):
            score = finder.path_cost(path) + loads[index]
            if best_score is None or score < best_score:
                best_score = score
                best_index = index

        return best_index

    def _run_turn(self) -> str:
        """Execute un tour de simulation."""
        movements: list[str] = []
        connection_usage: dict[frozenset[str], int] = {}
        occupancy = self._build_occupancy()

        arrived_ids = self._finish_transits(
            movements,
            connection_usage,
            occupancy,
        )
        reserved = self._build_reserved_arrivals()
        self._schedule_waiting_drones(
            movements,
            connection_usage,
            occupancy,
            reserved,
            arrived_ids,
        )

        return " ".join(movements)

    def _finish_transits(
        self,
        movements: list[str],
        connection_usage: dict[frozenset[str], int],
        occupancy: dict[str, int],
    ) -> set[int]:
        """Fait arriver les drones deja en transit."""
        arrived_ids: set[int] = set()
        for drone in self.drones:
            if not drone.is_in_transit():
                continue
            if drone.target_zone is None:
                raise SimulationError("drone en transit sans cible")

            connection = self.graph.get_connection(
                drone.current_zone,
                drone.target_zone,
            )
            self._use_connection(connection_usage, connection)
            drone.advance_turn()
            arrived_ids.add(drone.identifier)
            movements.append(f"{drone.get_label()}-{drone.current_zone}")
            self._advance_path_index(drone)

            if drone.current_zone == self.graph.get_end().name:
                drone.mark_delivered()
            else:
                occupancy[drone.current_zone] = (
                    occupancy.get(drone.current_zone, 0) + 1
                )
        return arrived_ids

    def _schedule_waiting_drones(
        self,
        movements: list[str],
        connection_usage: dict[frozenset[str], int],
        occupancy: dict[str, int],
        reserved: dict[str, int],
        arrived_ids: set[int],
    ) -> None:
        """Planifie les drones prets a bouger."""
        for drone in self._ordered_waiting_drones():
            if drone.identifier in arrived_ids:
                continue
            path = self.paths[drone.identifier]
            index = self.path_index[drone.identifier]
            if index >= len(path) - 1:
                continue

            current_name = drone.current_zone
            next_name = path[index + 1]
            target = self.graph.get_zone(next_name)
            connection = self.graph.get_connection(current_name, next_name)

            if not self._can_use_connection(connection_usage, connection):
                continue
            if not self._has_zone_capacity(target, occupancy, reserved):
                continue

            self._move_drone(
                drone,
                target,
                connection,
                movements,
                connection_usage,
                occupancy,
                reserved,
            )

    def _move_drone(
        self,
        drone: Drone,
        target: Zone,
        connection: Connection,
        movements: list[str],
        connection_usage: dict[frozenset[str], int],
        occupancy: dict[str, int],
        reserved: dict[str, int],
    ) -> None:
        """Deplace un drone si possible."""
        self._leave_zone(drone.current_zone, occupancy)
        self._use_connection(connection_usage, connection)

        if target.get_movement_cost() == 2:
            drone.start_move(target.name, connection.get_name(), 1)
            reserved[target.name] = reserved.get(target.name, 0) + 1
            movements.append(f"{drone.get_label()}-{connection.get_name()}")
            return

        drone.current_zone = target.name
        movements.append(f"{drone.get_label()}-{target.name}")
        self._advance_path_index(drone)

        if target.name == self.graph.get_end().name:
            drone.mark_delivered()
        else:
            occupancy[target.name] = occupancy.get(target.name, 0) + 1

    def _ordered_waiting_drones(self) -> list[Drone]:
        """Trie les drones pour liberer les fins de chemin."""
        drones = [
            drone
            for drone in self.drones
            if drone.status is DroneStatus.WAITING
        ]
        return sorted(drones, key=self._remaining_path_length)

    def _remaining_path_length(self, drone: Drone) -> int:
        """Calcule le chemin restant."""
        path = self.paths[drone.identifier]
        index = self.path_index[drone.identifier]
        return len(path) - index

    def _build_occupancy(self) -> dict[str, int]:
        """Compte les drones presents dans chaque zone."""
        occupancy: dict[str, int] = {}
        start = self.graph.get_start().name
        end = self.graph.get_end().name

        for drone in self.drones:
            if drone.status is not DroneStatus.WAITING:
                continue
            if drone.current_zone in (start, end):
                continue
            occupancy[drone.current_zone] = (
                occupancy.get(drone.current_zone, 0) + 1
            )

        return occupancy

    def _build_reserved_arrivals(self) -> dict[str, int]:
        """Compte les arrivees deja reservees."""
        reserved: dict[str, int] = {}
        for drone in self.drones:
            if not drone.is_in_transit() or drone.target_zone is None:
                continue
            reserved[drone.target_zone] = (
                reserved.get(drone.target_zone, 0) + 1
            )
        return reserved

    def _has_zone_capacity(
        self,
        zone: Zone,
        occupancy: dict[str, int],
        reserved: dict[str, int],
    ) -> bool:
        """Verifie la capacite de la zone cible."""
        special_zones = self._special_zone_names()
        if zone.name in special_zones:
            return True
        used = occupancy.get(zone.name, 0) + reserved.get(zone.name, 0)
        return used < zone.max_drones

    def _leave_zone(
        self,
        zone_name: str,
        occupancy: dict[str, int],
    ) -> None:
        """Libere une place dans une zone."""
        special_zones = self._special_zone_names()
        if zone_name in special_zones:
            return
        occupancy[zone_name] = occupancy.get(zone_name, 0) - 1
        if occupancy[zone_name] <= 0:
            del occupancy[zone_name]

    def _special_zone_names(self) -> tuple[str, str]:
        """Renvoie start et end."""
        return (self.graph.get_start().name, self.graph.get_end().name)

    def _can_use_connection(
        self,
        connection_usage: dict[frozenset[str], int],
        connection: Connection,
    ) -> bool:
        """Verifie la capacite d'une connexion."""
        used = connection_usage.get(connection.get_key(), 0)
        return used < connection.max_link_capacity

    def _use_connection(
        self,
        connection_usage: dict[frozenset[str], int],
        connection: Connection,
    ) -> None:
        """Occupe une connexion pour ce tour."""
        key = connection.get_key()
        connection_usage[key] = connection_usage.get(key, 0) + 1

    def _advance_path_index(self, drone: Drone) -> None:
        """Avance l'index du chemin du drone."""
        path = self.paths[drone.identifier]
        index = self.path_index[drone.identifier]
        if index < len(path) - 1:
            self.path_index[drone.identifier] = index + 1

    def _all_delivered(self) -> bool:
        """Indique si tous les drones sont arrives."""
        return all(drone.is_delivered() for drone in self.drones)
