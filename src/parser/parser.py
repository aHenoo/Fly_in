from __future__ import annotations

from pathlib import Path
from typing import NoReturn

from src.graph.connection import Connection
from src.graph.graph import Graph
from src.graph.zone import Zone, ZoneType


class ParseError(Exception):
    """Erreur de parsing avec contexte."""


class ParsedMap:
    """Resultat du parsing d'une carte."""

    def __init__(self, nb_drones: int, graph: Graph) -> None:
        """Initialise le resultat."""
        self.nb_drones = nb_drones
        self.graph = graph


class Parser:
    """Transforme un fichier texte en graphe."""

    ZONE_KEYS = {"zone", "color", "max_drones"}
    CONNECTION_KEYS = {"max_link_capacity"}

    def parse_file(self, filename: str) -> ParsedMap:
        """Parse une carte depuis un fichier."""
        try:
            with Path(filename).open("r", encoding="utf-8") as file:
                return self.parse_text(file.read())
        except OSError as error:
            raise ParseError(f"cannot read file: {error}") from error

    def parse_text(self, content: str) -> ParsedMap:
        """Parse une carte depuis une chaine."""
        graph = Graph()
        nb_drones: int | None = None
        found_map_line = False
        reading_connections = False

        for line_number, raw_line in enumerate(content.splitlines(), 1):
            line = self._clean_line(raw_line)
            if not line:
                continue

            if not found_map_line:
                found_map_line = True
                nb_drones = self._parse_nb_drones(line, line_number)
                continue

            if line.startswith("nb_drones:"):
                self._line_error(line_number, "nb_drones est defini deux fois")
            if line.startswith("connection:"):
                reading_connections = True
                connection = self._parse_connection(line, line_number)
                self._add_connection(graph, connection, line_number)
                continue
            if self._is_zone_line(line):
                if reading_connections:
                    self._line_error(
                        line_number,
                        "une zone ne peut pas etre apres une connexion",
                    )
                zone, is_start, is_end = self._parse_zone(line, line_number)
                self._add_zone(graph, zone, is_start, is_end, line_number)
                continue

            self._line_error(line_number, "ligne inconnue")

        if nb_drones is None:
            raise ParseError("fichier vide ou nb_drones manquant")
        self._validate_graph(graph)
        return ParsedMap(nb_drones, graph)

    def _clean_line(self, raw_line: str) -> str:
        """Retire commentaires et espaces."""
        content = raw_line.split("#", 1)[0]
        return content.strip()

    def _parse_nb_drones(self, line: str, line_number: int) -> int:
        """Parse la ligne nb_drones."""
        prefix = "nb_drones:"
        if not line.startswith(prefix):
            self._line_error(
                line_number,
                "la premiere ligne utile doit definir nb_drones",
            )
        value = line[len(prefix):].strip()
        return self._parse_positive_int(value, line_number, "nb_drones")

    def _is_zone_line(self, line: str) -> bool:
        """Indique si la ligne decrit une zone."""
        return (
            line.startswith("start_hub:")
            or line.startswith("end_hub:")
            or line.startswith("hub:")
        )

    def _parse_zone(
        self,
        line: str,
        line_number: int,
    ) -> tuple[Zone, bool, bool]:
        """Parse une zone."""
        prefix = self._get_zone_prefix(line, line_number)
        body = line[len(prefix):].strip()
        data, metadata = self._split_metadata(body, line_number)
        parts = data.split()

        if len(parts) != 3:
            self._line_error(line_number, "zone invalide")

        name = parts[0]
        self._validate_zone_name(name, line_number)
        x = self._parse_int(parts[1], line_number, "x")
        y = self._parse_int(parts[2], line_number, "y")
        self._validate_metadata_keys(metadata, self.ZONE_KEYS, line_number)

        zone_type = self._parse_zone_type(
            metadata.get("zone", ZoneType.NORMAL.value),
            line_number,
        )
        color = metadata.get("color")
        is_start = prefix == "start_hub:"
        is_end = prefix == "end_hub:"
        max_drones = self._parse_max_drones(metadata, line_number, is_start,
                                            is_end)

        try:
            zone = Zone(name, x, y, zone_type, color, max_drones, metadata)
        except ValueError as error:
            self._line_error(line_number, str(error))

        return zone, is_start, is_end

    def _parse_max_drones(
        self,
        metadata: dict[str, str],
        line_number: int,
        is_start: bool,
        is_end: bool,
    ) -> int:
        """Parse max_drones, ignore sur start/end."""
        if is_start or is_end:
            return 1
        return self._parse_positive_int(
            metadata.get("max_drones", "1"),
            line_number,
            "max_drones",
        )

    def _get_zone_prefix(self, line: str, line_number: int) -> str:
        """Renvoie le prefixe de zone."""
        for prefix in ("start_hub:", "end_hub:", "hub:"):
            if line.startswith(prefix):
                return prefix
        self._line_error(line_number, "type de zone invalide")

    def _parse_connection(
        self,
        line: str,
        line_number: int,
    ) -> Connection:
        """Parse une connexion."""
        prefix = "connection:"
        body = line[len(prefix):].strip()
        data, metadata = self._split_metadata(body, line_number)
        self._validate_metadata_keys(
            metadata,
            self.CONNECTION_KEYS,
            line_number,
        )

        endpoints = data.split("-")
        if len(endpoints) != 2:
            self._line_error(line_number, "connexion invalide")
        zone_a = endpoints[0].strip()
        zone_b = endpoints[1].strip()
        self._validate_zone_name(zone_a, line_number)
        self._validate_zone_name(zone_b, line_number)

        max_link_capacity = self._parse_positive_int(
            metadata.get("max_link_capacity", "1"),
            line_number,
            "max_link_capacity",
        )

        try:
            return Connection(zone_a, zone_b, max_link_capacity, metadata)
        except ValueError as error:
            self._line_error(line_number, str(error))

    def _split_metadata(
        self,
        body: str,
        line_number: int,
    ) -> tuple[str, dict[str, str]]:
        """Separe le contenu et les metadonnees."""
        if "[" not in body and "]" not in body:
            return body.strip(), {}
        if body.count("[") != 1 or body.count("]") != 1:
            self._line_error(line_number, "bloc metadata invalide")
        if not body.endswith("]"):
            self._line_error(line_number, "metadata doit etre en fin de ligne")

        start_index = body.index("[")
        end_index = body.index("]")
        if start_index > end_index:
            self._line_error(line_number, "bloc metadata invalide")

        data = body[:start_index].strip()
        metadata_body = body[start_index + 1:end_index].strip()
        metadata = self._parse_metadata(metadata_body, line_number)
        return data, metadata

    def _parse_metadata(
        self,
        metadata_body: str,
        line_number: int,
    ) -> dict[str, str]:
        """Parse les tags entre crochets."""
        metadata: dict[str, str] = {}
        if not metadata_body:
            self._line_error(line_number, "metadata vide")

        for token in metadata_body.split():
            if token.count("=") != 1:
                self._line_error(line_number, "metadata invalide")
            key, value = token.split("=", 1)
            if not key or not value:
                self._line_error(line_number, "metadata invalide")
            if key in metadata:
                self._line_error(line_number, f"metadata dupliquee: {key}")
            if " " in value or "\t" in value:
                self._line_error(line_number, "metadata invalide")
            metadata[key] = value

        return metadata

    def _validate_metadata_keys(
        self,
        metadata: dict[str, str],
        allowed_keys: set[str],
        line_number: int,
    ) -> None:
        """Verifie les cles metadata."""
        for key in metadata:
            if key not in allowed_keys:
                self._line_error(line_number, f"metadata inconnue: {key}")

    def _parse_zone_type(self, value: str, line_number: int) -> ZoneType:
        """Parse le type de zone."""
        try:
            return ZoneType(value)
        except ValueError:
            self._line_error(line_number, f"type de zone invalide: {value}")

    def _parse_int(self, value: str, line_number: int, name: str) -> int:
        """Parse un entier."""
        try:
            return int(value)
        except ValueError:
            self._line_error(line_number, f"{name} doit etre un entier")

    def _parse_positive_int(
        self,
        value: str,
        line_number: int,
        name: str,
    ) -> int:
        """Parse un entier positif."""
        number = self._parse_int(value, line_number, name)
        if number <= 0:
            self._line_error(line_number, f"{name} doit etre positif")
        return number

    def _validate_zone_name(self, name: str, line_number: int) -> None:
        """Verifie le nom d'une zone."""
        if not name:
            self._line_error(line_number, "nom de zone vide")
        if "-" in name or " " in name:
            self._line_error(
                line_number,
                "un nom de zone ne peut pas contenir '-' ou un espace",
            )

    def _add_zone(
        self,
        graph: Graph,
        zone: Zone,
        is_start: bool,
        is_end: bool,
        line_number: int,
    ) -> None:
        """Ajoute une zone avec erreur de ligne."""
        try:
            graph.add_zone(zone, is_start, is_end)
        except ValueError as error:
            self._line_error(line_number, str(error))

    def _add_connection(
        self,
        graph: Graph,
        connection: Connection,
        line_number: int,
    ) -> None:
        """Ajoute une connexion avec erreur de ligne."""
        try:
            graph.add_connection(connection)
        except ValueError as error:
            self._line_error(line_number, str(error))

    def _validate_graph(self, graph: Graph) -> None:
        """Verifie le graphe final."""
        try:
            graph.validate_ready()
        except ValueError as error:
            raise ParseError(str(error)) from error

    def _line_error(self, line_number: int, message: str) -> NoReturn:
        """Leve une erreur avec numero de ligne."""
        raise ParseError(f"line {line_number}: {message}")
