from __future__ import annotations

from enum import Enum


class DroneStatus(str, Enum):
    """Etats possibles d'un drone."""

    WAITING = "waiting"
    MOVING = "moving"
    DELIVERED = "delivered"


class Drone:
    """Drone qui avance dans le graphe."""

    def __init__(
        self,
        identifier: int,
        current_zone: str,
        status: DroneStatus = DroneStatus.WAITING,
        target_zone: str | None = None,
        current_connection: str | None = None,
        turns_remaining: int = 0,
    ) -> None:
        """Initialise un drone."""
        self.identifier = identifier
        self.current_zone = current_zone
        self.status = status
        self.target_zone = target_zone
        self.current_connection = current_connection
        self.turns_remaining = turns_remaining
        self.validate()

    def validate(self) -> None:
        """Valide le drone."""
        if self.identifier < 1:
            raise ValueError("drone identifier must be positive")
        if not self.current_zone:
            raise ValueError("drone current_zone cannot be empty")
        if self.turns_remaining < 0:
            raise ValueError("turns_remaining cannot be negative")

    def get_label(self) -> str:
        """Renvoie le label du drone."""
        return f"D{self.identifier}"

    def is_delivered(self) -> bool:
        """Indique si le drone est arrive."""
        return self.status is DroneStatus.DELIVERED

    def is_in_transit(self) -> bool:
        """Indique si le drone est en transit."""
        return self.status is DroneStatus.MOVING

    def start_move(self, target_zone: str, connection_name: str,
                   movement_cost: int) -> None:
        """Demarre un deplacement."""
        if movement_cost < 1:
            raise ValueError("movement_cost must be positive")
        self.target_zone = target_zone
        self.current_connection = connection_name
        self.turns_remaining = movement_cost
        self.status = DroneStatus.MOVING

    def advance_turn(self) -> None:
        """Avance le deplacement d'un tour."""
        if self.status is not DroneStatus.MOVING:
            return
        self.turns_remaining -= 1
        if self.turns_remaining <= 0:
            self.arrive()

    def arrive(self) -> None:
        """Termine le deplacement en cours."""
        if self.target_zone is None:
            raise ValueError("moving drone has no target zone")
        self.current_zone = self.target_zone
        self.target_zone = None
        self.current_connection = None
        self.turns_remaining = 0
        self.status = DroneStatus.WAITING

    def mark_delivered(self) -> None:
        """Marque le drone comme livre."""
        self.status = DroneStatus.DELIVERED
        self.target_zone = None
        self.current_connection = None
        self.turns_remaining = 0
