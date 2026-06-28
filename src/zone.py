from typing import Optional


class Zone:
    """Zone class: a single node in the drone network,where drones can rest or pass through.

    Attributes:
        name: Unique zone name (no dashes, no spaces).
        x, y: Integer coordinates used by the visualizer.
        zone_type: ``normal``, ``priority``, ``restricted``, or ``blocked``.
        color: Optional color string (any single word, e.g. ``red``).
        max_drones: Maximum drones allowed at the same time.
        is_start: True if this is the start hub.
        is_end: True if this is the end hub.
    """

    VALID_TYPES = ("normal", "priority", "restricted", "blocked")

    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        zone_type: str = "normal",
        color: Optional[str] = None,
        max_drones: int = 1,
        is_start: bool = False,
        is_end: bool = False,
    ) -> None:
        if zone_type not in self.VALID_TYPES:
            raise ValueError(f"invalid zone type '{zone_type}'")
        if max_drones < 1:
            raise ValueError(f"max_drones must be >= 1 (got {max_drones})")
        self.name = name
        self.x = x
        self.y = y
        self.zone_type = zone_type
        self.color = color
        self.max_drones = max_drones
        self.is_start = is_start
        self.is_end = is_end

    @property
    def cost(self) -> int:
        """Movement cost in turns to *arrive* at this zone."""
        if self.zone_type == "restricted":
            return 2
        return 1

    @property
    def is_blocked(self) -> bool:
        """True if drones cannot enter this zone."""
        return self.zone_type == "blocked"

    def effective_capacity(self) -> float:
        """Capacity to use during simulation. Start/end are unlimited."""
        if self.is_start or self.is_end:
            return float("inf")
        return float(self.max_drones)

    def __repr__(self) -> str:
        return f"Zone({self.name}, {self.zone_type}, cap={self.max_drones})"
