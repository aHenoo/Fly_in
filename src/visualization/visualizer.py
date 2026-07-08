from __future__ import annotations

from src.graph.graph import Graph


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
        label = f"Resultat: {turn_count} tours"
        return self._color_text(label, "36")

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
