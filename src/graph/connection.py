from __future__ import annotations


class Connection:
    """Lien bidirectionnel entre deux zones."""

    def __init__(
        self,
        zone_a: str,
        zone_b: str,
        max_link_capacity: int = 1,
        metadata: dict[str, str] | None = None,
    ) -> None:
        """Initialise une connexion."""
        self.zone_a = zone_a
        self.zone_b = zone_b
        self.max_link_capacity = max_link_capacity
        self.metadata = metadata if metadata is not None else {}
        self.validate()

    def validate(self) -> None:
        """Valide la connexion."""
        if not self.zone_a or not self.zone_b:
            raise ValueError("connection endpoints cannot be empty")
        if self.zone_a == self.zone_b:
            raise ValueError("connection endpoints must be different")
        if self.max_link_capacity < 1:
            raise ValueError(
                "connection max_link_capacity must be a positive integer"
            )

    def get_name(self) -> str:
        """Renvoie le nom affichable."""
        return f"{self.zone_a}-{self.zone_b}"

    def get_key(self) -> frozenset[str]:
        """Renvoie une clef sans ordre."""
        return frozenset((self.zone_a, self.zone_b))

    def other_end(self, zone_name: str) -> str:
        """Renvoie l'autre extremite."""
        if zone_name == self.zone_a:
            return self.zone_b
        if zone_name == self.zone_b:
            return self.zone_a
        raise ValueError(
            f"{zone_name} is not connected by {self.get_name()}"
        )
