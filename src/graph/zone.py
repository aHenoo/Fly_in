"""Zones du graphe de drones."""

from __future__ import annotations

from enum import Enum


class ZoneType(str, Enum):
    """Types de zones autorises."""

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class Zone:
    """Zone que les drones peuvent occuper."""

    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        zone_type: ZoneType = ZoneType.NORMAL,
        color: str | None = None,
        max_drones: int = 1,
        metadata: dict[str, str] | None = None,
    ) -> None:
        """Initialise une zone."""
        self.name = name
        self.x = x
        self.y = y
        self.zone_type = zone_type
        self.color = color
        self.max_drones = max_drones
        self.metadata = metadata if metadata is not None else {}
        self.validate()

    def validate(self) -> None:
        """Valide la zone."""
        if not self.name:
            raise ValueError("zone name cannot be empty")
        if "-" in self.name or " " in self.name:
            raise ValueError("zone name cannot contain dashes or spaces")
        if self.max_drones < 1:
            raise ValueError("zone max_drones must be a positive integer")

    def get_movement_cost(self) -> int:
        """Renvoie le cout d'entree."""
        if self.zone_type is ZoneType.RESTRICTED:
            return 2
        return 1

    def is_blocked(self) -> bool:
        """Indique si la zone est bloquee."""
        return self.zone_type is ZoneType.BLOCKED

    def is_priority(self) -> bool:
        """Indique si la zone est prioritaire."""
        return self.zone_type is ZoneType.PRIORITY
