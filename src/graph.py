from typing import Dict, List, Optional, Tuple
from .connection import Connection
from .zone import Zone


class Graph:
    """Graph class : The drone network.

    Holds all zones, all connections, and lets you ask:
    - which zones are neighbours of zone X
    - which connection links X and Y

    Attributes:
        zones: name -> Zone.
        connections: (a, b) -> Connection (key is sorted endpoints).
        adjacency: name -> list of neighbour names.
        start: name of the start zone.
        end: name of the end zone.
        nb_drones: how many drones to route.
    """

    def __init__(self) -> None:
        self.zones: Dict[str, Zone] = {}
        self.connections: Dict[Tuple[str, str], Connection] = {}
        self.adjacency: Dict[str, List[str]] = {}
        self.start: str = ""
        self.end: str = ""
        self.nb_drones: int = 0

    def add_zone(self, zone: Zone) -> None:
        """Register a zone. Raise if the name already exists."""
        if zone.name in self.zones:
            raise ValueError(f"duplicate zone '{zone.name}'")
        self.zones[zone.name] = zone
        self.adjacency[zone.name] = []
        if zone.is_start:
            if self.start:
                raise ValueError("multiple start zones defined")
            self.start = zone.name
        if zone.is_end:
            if self.end:
                raise ValueError("multiple end zones defined")
            self.end = zone.name

    def add_connection(self, conn: Connection) -> None:
        """Register a connection. Raise if endpoints unknown or duplicate."""
        if conn.a not in self.zones:
            raise ValueError(f"unknown zone '{conn.a}' in connection")
        if conn.b not in self.zones:
            raise ValueError(f"unknown zone '{conn.b}' in connection")
        if conn.a == conn.b:
            raise ValueError(f"self-loop not allowed: {conn.a}-{conn.b}")
        if conn.key in self.connections:
            raise ValueError(f"duplicate connection {conn.a}-{conn.b}")
        self.connections[conn.key] = conn
        self.adjacency[conn.a].append(conn.b)
        self.adjacency[conn.b].append(conn.a)

    def get_connection(self, a: str, b: str) -> Optional[Connection]:
        """Return the connection between a and b (or None)."""
        key = (a, b) if a <= b else (b, a)
        return self.connections.get(key)

    def neighbours(self, zone_name: str) -> List[str]:
        """Return the list of zones directly connected to ``zone_name``."""
        return self.adjacency.get(zone_name, [])

    def validate(self) -> None:
        """Check that start and end are defined."""
        if not self.start:
            raise ValueError("no start zone defined (start_hub:)")
        if not self.end:
            raise ValueError("no end zone defined (end_hub:)")
        if self.nb_drones <= 0:
            raise ValueError("nb_drones must be a positive integer")
