from __future__ import annotations

from src.graph.graph import Graph
from src.simulation.drone import Drone, DroneStatus
from src.simulation.simulation import Simulation


class Visualizer:
    """Colore les mouvements avec les couleurs des zones."""

    COLORS = {
        "black": "30",
        "red": "31",
        "green": "32",
        "yellow": "33",
        "blue": "34",
        "purple": "35",
        "magenta": "35",
        "cyan": "36",
        "white": "37",
        "gray": "90",
        "grey": "90",
        "orange": "33",
        "gold": "33",
        "lime": "92",
        "brown": "33",
        "darkred": "31",
        "maroon": "31",
        "violet": "35",
        "crimson": "31",
    }

    RESET = "\033[0m"

    def __init__(self, graph: Graph) -> None:
        """Initialise le visualiseur."""
        self.graph = graph

    def render_turn(self, turn: int, line: str, show_turn: bool) -> str:
        """Renvoie une ligne coloree."""
        rendered_line = self.render_line(line)
        if show_turn:
            return f"Tour {turn}: {rendered_line}"
        return rendered_line

    def render_result(self, turn_count: int) -> str:
        """Affiche le nombre total de tours."""
        separator = "=" * 52
        label = f"SIMULATION COMPLETE - {turn_count} turns"
        return "\n".join((
            self._color_text(separator, "36"),
            self._color_text(label.center(52), "32"),
            self._color_text(separator, "36"),
        ))

    def render_header(self, simulation: Simulation) -> str:
        """Affiche le contexte de la carte avant la simulation."""
        separator = "=" * 52
        routes = self._group_routes(simulation)
        lines = [
            self._color_text(separator, "36"),
            self._color_text("FLY-IN SIMULATION".center(52), "36"),
            self._color_text(separator, "36"),
            f"Drones: {simulation.nb_drones}",
            f"Start: {self.graph.get_start().name}",
            f"End: {self.graph.get_end().name}",
            f"Zones: {len(self.graph.zones)}",
            f"Connections: {len(self.graph.connections)}",
            "",
            "LEGEND",
            "  [N] normal (1 turn)      [P] priority (1 turn)",
            "  [R] restricted (2 turns) [X] blocked",
            "  capacity: current/maximum; start and end are unlimited",
            "",
            "ASSIGNED ROUTES",
        ]
        for path, drone_count in routes:
            lines.append(f"  {drone_count} drone(s): {' -> '.join(path)}")
        return "\n".join(lines)

    def render_dashboard(
        self,
        simulation: Simulation,
        turn: int,
        movement_line: str,
    ) -> str:
        """Affiche mouvements, positions, occupation et progression."""
        separator = "-" * 52
        lines = [
            "",
            self._color_text(f"TURN {turn}".center(52, "-"), "36"),
            "",
            "MOVEMENTS",
        ]
        for movement in movement_line.split():
            lines.append(f"  {self._render_readable_movement(movement)}")

        lines.extend(("", "DRONE POSITIONS"))
        for drone in simulation.drones:
            position = self._drone_position(drone)
            lines.append(f"  {drone.get_label():<4} {position}")

        lines.extend(("", "OCCUPIED ZONES"))
        occupied = self._occupied_zones(simulation)
        for zone_name, labels in occupied.items():
            zone = self.graph.get_zone(zone_name)
            if zone_name in (self.graph.start_name, self.graph.end_name):
                capacity = "unlimited"
            else:
                capacity = f"{len(labels)}/{zone.max_drones}"
                if len(labels) >= zone.max_drones:
                    capacity += " FULL"
            colored_zone = self._color_zone_name(zone_name)
            lines.append(
                f"  {colored_zone:<20} [{', '.join(labels)}] "
                f"capacity {capacity}"
            )

        delivered = sum(
            drone.is_delivered()
            for drone in simulation.drones
        )
        progress = self._progress_bar(delivered, simulation.nb_drones)
        lines.extend((
            "",
            "PROGRESS",
            f"  Delivered: {delivered}/{simulation.nb_drones} {progress}",
            separator,
        ))
        return "\n".join(lines)

    def render_line(self, line: str) -> str:
        """Colore chaque mouvement d'une ligne."""
        movements = line.split()
        rendered_movements = [
            self.render_movement(movement)
            for movement in movements
        ]
        return " ".join(rendered_movements)

    def render_movement(self, movement: str) -> str:
        """Colore un mouvement si possible."""
        zone_name = self._extract_zone_name(movement)
        color = self._get_zone_color(zone_name)
        if color is None:
            return movement
        return self._color_text(movement, color)

    def _render_readable_movement(self, movement: str) -> str:
        """Transforme un token de mouvement en phrase lisible."""
        drone_label, destination = movement.split("-", 1)
        if destination in self.graph.zones:
            target = self._color_zone_name(destination)
            return f"{drone_label}: entered {target}"
        source, target_name = destination.rsplit("-", 1)
        target = self._color_zone_name(target_name)
        return f"{drone_label}: {source} -> {target} (in transit)"

    def _drone_position(self, drone: Drone) -> str:
        """Renvoie une position humaine pour un drone."""
        if drone.status is DroneStatus.DELIVERED:
            zone = self._color_zone_name(drone.current_zone)
            return f"at {zone} (delivered)"
        if drone.status is DroneStatus.MOVING:
            if drone.target_zone is None:
                return f"at {drone.current_zone} (invalid transit)"
            return (
                f"{drone.current_zone} -> "
                f"{self._color_zone_name(drone.target_zone)} "
                f"(in transit, {drone.turns_remaining} turn left)"
            )
        return f"at {self._color_zone_name(drone.current_zone)}"

    def _occupied_zones(
        self,
        simulation: Simulation,
    ) -> dict[str, list[str]]:
        """Regroupe les drones qui se trouvent actuellement dans une zone."""
        occupied: dict[str, list[str]] = {}
        for drone in simulation.drones:
            if drone.status is DroneStatus.MOVING:
                continue
            occupied.setdefault(drone.current_zone, []).append(
                drone.get_label(),
            )
        return occupied

    def _group_routes(
        self,
        simulation: Simulation,
    ) -> list[tuple[list[str], int]]:
        """Regroupe les chemins identiques et leur nombre de drones."""
        route_counts: dict[tuple[str, ...], int] = {}
        for path in simulation.paths.values():
            key = tuple(path)
            route_counts[key] = route_counts.get(key, 0) + 1
        return [(list(path), count) for path, count in route_counts.items()]

    def _progress_bar(self, delivered: int, total: int) -> str:
        """Construit une barre de progression compacte."""
        width = 20
        completed = int(width * delivered / total)
        return f"[{'#' * completed}{'.' * (width - completed)}]"

    def _color_zone_name(self, zone_name: str) -> str:
        """Colore un nom de zone avec sa metadata si elle est reconnue."""
        color = self._get_zone_color(zone_name)
        if color is None:
            return zone_name
        return self._color_text(zone_name, color)

    def _extract_zone_name(self, movement: str) -> str:
        """Recupere la zone cible."""
        destination = movement.split("-", 1)[1]
        if destination in self.graph.zones:
            return destination
        return destination.rsplit("-", 1)[-1]

    def _get_zone_color(self, zone_name: str) -> str | None:
        """Renvoie la couleur ANSI de la zone."""
        if zone_name not in self.graph.zones:
            return None
        color = self.graph.get_zone(zone_name).color
        if color is None:
            return None
        return self.COLORS.get(color.lower())

    def _color_text(self, text: str, color: str) -> str:
        """Applique une couleur ANSI."""
        return f"\033[{color}m{text}{self.RESET}"
