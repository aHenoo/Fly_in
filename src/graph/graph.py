"""Graphe des zones et connexions."""

from __future__ import annotations

from src.graph.connection import Connection
from src.graph.zone import Zone


class Graph:
    """Stocke les zones, connexions et voisins."""

    def __init__(self) -> None:
        """Initialise un graphe vide."""
        self.zones: dict[str, Zone] = {}
        self.connections: dict[frozenset[str], Connection] = {}
        self.adjacency: dict[str, list[str]] = {}
        self.start_name: str | None = None
        self.end_name: str | None = None

    def add_zone(self, zone: Zone, is_start: bool = False,
                 is_end: bool = False) -> None:
        """Ajoute une zone au graphe."""
        if zone.name in self.zones:
            raise ValueError(f"duplicate zone: {zone.name}")
        if is_start and self.start_name is not None:
            raise ValueError("start zone is already defined")
        if is_end and self.end_name is not None:
            raise ValueError("end zone is already defined")

        self.zones[zone.name] = zone
        self.adjacency[zone.name] = []
        if is_start:
            self.start_name = zone.name
        if is_end:
            self.end_name = zone.name

    def add_connection(self, connection: Connection) -> None:
        """Ajoute une connexion entre deux zones."""
        if connection.zone_a not in self.zones:
            raise ValueError(f"unknown zone: {connection.zone_a}")
        if connection.zone_b not in self.zones:
            raise ValueError(f"unknown zone: {connection.zone_b}")
        connection_key = connection.get_key()
        if connection_key in self.connections:
            raise ValueError(
                f"duplicate connection: {connection.get_name()}"
            )

        self.connections[connection_key] = connection
        self.adjacency[connection.zone_a].append(connection.zone_b)
        self.adjacency[connection.zone_b].append(connection.zone_a)

    def get_start(self) -> Zone:
        """Renvoie la zone de depart."""
        if self.start_name is None:
            raise ValueError("start zone is not defined")
        return self.zones[self.start_name]

    def get_end(self) -> Zone:
        """Renvoie la zone d'arrivee."""
        if self.end_name is None:
            raise ValueError("end zone is not defined")
        return self.zones[self.end_name]

    def get_zone(self, name: str) -> Zone:
        """Renvoie une zone par son nom."""
        return self.zones[name]

    def get_connection(self, zone_a: str, zone_b: str) -> Connection:
        """Renvoie la connexion entre deux zones."""
        return self.connections[frozenset((zone_a, zone_b))]

    def neighbors(self, zone_name: str) -> list[Zone]:
        """Renvoie les voisins accessibles."""
        return [
            self.zones[name]
            for name in self.adjacency[zone_name]
            if not self.zones[name].is_blocked()
        ]

    def validate_ready(self) -> None:
        """Verifie que start et end existent."""
        if self.start_name is None:
            raise ValueError("missing start zone")
        if self.end_name is None:
            raise ValueError("missing end zone")
