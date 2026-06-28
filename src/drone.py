from typing import List, Optional


class Drone:
    """Drone class: tracks a single drone moving through the network.

    Attributes:
        id: Numeric drone ID (D1, D2, ...).
        position: Name of the zone the drone currently sits in.
        path: Planned sequence of zone names from current pos to end.
        in_flight_to: When traversing into a restricted zone, target zone name.
        in_flight_via: Label of the connection used while in flight.
        delivered: True once the drone has reached the end zone.
    """

    def __init__(
        self, drone_id: int, start_zone: str, path: List[str]
    ) -> None:
        self.id = drone_id
        self.position = start_zone
        self.path = path[:]
        self.path_index = 0
        self.in_flight_to: Optional[str] = None
        self.in_flight_via: Optional[str] = None
        self.delivered = False

    @property
    def label(self) -> str:
        """Drone identifier used in the output (``D1``)."""
        return f"D{self.id}"

    @property
    def next_zone(self) -> Optional[str]:
        """Next planned zone, or None if the path is finished."""
        next_index = self.path_index + 1
        if next_index >= len(self.path):
            return None
        return self.path[next_index]

    def __repr__(self) -> str:
        flight = ""
        if self.in_flight_to is not None:
            flight = f" -> {self.in_flight_to}"
        return f"D{self.id}@{self.position}{flight}"
