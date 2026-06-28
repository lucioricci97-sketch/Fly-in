from typing import Tuple


class Connection:
    """Connection class: A bidirectional link between two zones.

    Attributes:
        a, b: Names of the two endpoints (order is normalised so a < b).
        max_capacity: How many drones may traverse this link at the same turn.
    """

    def __init__(self, a: str, b: str, max_capacity: int = 1) -> None:
        if max_capacity < 1:
            raise ValueError(
                f"max_link_capacity must be >= 1 (got {max_capacity})"
            )
        # Normalize endpoints so a-b and b-a compare equal.
        if a <= b:
            self.a, self.b = a, b
        else:
            self.a, self.b = b, a
        self.max_capacity = max_capacity

    @property
    def key(self) -> Tuple[str, str]:
        """Canonical key for the edge (ordered tuple)."""
        return (self.a, self.b)

    def other(self, name: str) -> str:
        """Return the endpoint that is not ``name``."""
        if name == self.a:
            return self.b
        if name == self.b:
            return self.a
        raise ValueError(f"{name} is not an endpoint of {self}")

    def label(self) -> str:
        """Human-readable label used in the simulator output (``a-b``)."""
        return f"{self.a}-{self.b}"

    def __repr__(self) -> str:
        return f"Connection({self.a}-{self.b}, cap={self.max_capacity})"
