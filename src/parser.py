import re
from typing import Dict, Optional, Tuple
from .connection import Connection
from .graph import Graph
from .zone import Zone


class ParseError(Exception):
    """Raised when the map file is malformed.

    Carries the offending line number so the user can fix it quickly.
    """

    def __init__(self, line_no: int, message: str) -> None:
        super().__init__(f"line {line_no}: {message}")
        self.line_no = line_no


class MapParser:
    """Reads and converts a map text file into Graph object.

    Usage::

        graph = MapParser(path).parse()

    Each helper method handles one syntactic concern (metadata block,
    zone line, connection line, prefix split). The public ``parse``
    method orchestrates them and validates the final graph.
    """

    _METADATA_RE = re.compile(r"\[([^\]]*)\]")

    def __init__(self, path: str) -> None:
        self.path = path

    def parse(self) -> Graph:
        """Parse the file and return the built ``Graph``.

        Raises:
            ParseError: on any malformed line.
            OSError: if the file cannot be opened.
        """
        graph = Graph()
        nb_drones_seen = False
        with open(self.path, "r", encoding="utf-8") as fp:
            for line_no, raw in enumerate(fp, start=1):
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("nb_drones:"):
                    value = line[len("nb_drones:"):].strip()
                    nb = self._parse_int(value, line_no, "nb_drones")
                    if nb <= 0:
                        raise ParseError(line_no, "nb_drones must be > 0")
                    graph.nb_drones = nb
                    nb_drones_seen = True
                    continue
                self._dispatch(line, line_no, graph)
        if not nb_drones_seen:
            raise ParseError(0, "missing nb_drones declaration")
        try:
            graph.validate()
        except ValueError as exc:
            raise ParseError(0, str(exc)) from exc
        return graph

    def _dispatch(self, line: str, line_no: int, graph: Graph) -> None:
        """Route a single non-comment line to its builder."""
        prefix, body = self._split_prefix(line, line_no)
        try:
            if prefix == "start_hub":
                graph.add_zone(self._parse_zone_line(
                    body, line_no, is_start=True, is_end=False))
            elif prefix == "end_hub":
                graph.add_zone(self._parse_zone_line(
                    body, line_no, is_start=False, is_end=True))
            elif prefix == "hub":
                graph.add_zone(self._parse_zone_line(
                    body, line_no, is_start=False, is_end=False))
            elif prefix == "connection":
                a, b, cap = self._parse_connection_line(body, line_no)
                graph.add_connection(Connection(a, b, cap))
            else:
                raise ParseError(line_no, f"unknown directive '{prefix}'")
        except ValueError as exc:
            raise ParseError(line_no, str(exc)) from exc

    def _parse_metadata(self, raw: str, line_no: int) -> Dict[str, str]:
        """Extract a ``[key=value key2=value2]`` block into a dict."""
        match = self._METADATA_RE.search(raw)
        if not match:
            return {}
        inside = match.group(1).strip()
        if not inside:
            return {}
        meta: Dict[str, str] = {}
        for token in inside.split():
            if "=" not in token:
                raise ParseError(line_no, f"bad metadata token '{token}'")
            key, value = token.split("=", 1)
            key = key.strip()
            value = value.strip()
            if not key or not value:
                raise ParseError(
                    line_no, f"empty metadata key/value '{token}'"
                )
            meta[key] = value
        return meta

    def _strip_metadata(self, raw: str) -> str:
        """Return the line with the metadata block removed."""
        return self._METADATA_RE.sub("", raw).strip()

    def _parse_zone_line(
        self, raw: str, line_no: int, is_start: bool, is_end: bool
    ) -> Zone:
        """Parse a ``start_hub:`` / ``end_hub:`` / ``hub:`` body."""
        meta = self._parse_metadata(raw, line_no)
        body = self._strip_metadata(raw)
        parts = body.split()
        if len(parts) != 3:
            raise ParseError(
                line_no,
                "expected '<name> <x> <y>' after the type prefix",
            )
        name, sx, sy = parts
        if "-" in name or " " in name:
            raise ParseError(line_no, f"zone name '{name}' has dash or space")
        x = self._parse_int(sx, line_no, "x coordinate")
        y = self._parse_int(sy, line_no, "y coordinate")

        zone_type = meta.get("zone", "normal")
        color = meta.get("color")
        max_drones = 1
        if "max_drones" in meta:
            max_drones = self._parse_int(
                meta["max_drones"], line_no, "max_drones"
            )
            if max_drones < 1:
                raise ParseError(line_no, "max_drones must be >= 1")
        try:
            return Zone(
                name=name,
                x=x,
                y=y,
                zone_type=zone_type,
                color=color,
                max_drones=max_drones,
                is_start=is_start,
                is_end=is_end,
            )
        except ValueError as exc:
            raise ParseError(line_no, str(exc)) from exc

    def _parse_connection_line(
        self, raw: str, line_no: int
    ) -> Tuple[str, str, int]:
        """Return ``(zone1, zone2, max_capacity)`` from a connection line."""
        meta = self._parse_metadata(raw, line_no)
        body = self._strip_metadata(raw)
        if body.count("-") != 1:
            raise ParseError(
                line_no,
                f"connection must be '<zone1>-<zone2>' (got '{body}')",
            )
        a, b = body.split("-")
        a = a.strip()
        b = b.strip()
        if not a or not b:
            raise ParseError(line_no, "missing zone name in connection")
        cap = 1
        if "max_link_capacity" in meta:
            cap = self._parse_int(
                meta["max_link_capacity"], line_no, "max_link_capacity"
            )
            if cap < 1:
                raise ParseError(line_no, "max_link_capacity must be >= 1")
        return a, b, cap

    @staticmethod
    def _parse_int(value: str, line_no: int, field: str) -> int:
        try:
            return int(value)
        except ValueError as exc:
            raise ParseError(line_no, f"{field} must be an integer") from exc

    @staticmethod
    def _split_prefix(line: str, line_no: int) -> Tuple[str, str]:
        """Split ``prefix: body`` into ``(prefix, body)``."""
        if ":" not in line:
            raise ParseError(line_no, f"missing ':' in line '{line}'")
        prefix, _, body = line.partition(":")
        return prefix.strip(), body.strip()


def parse_map(path: str) -> Graph:
    """Convenience: ``MapParser(path).parse()``.

    Kept so existing callers can keep using a one-liner.
    """
    return MapParser(path).parse()


def safe_parse_map(path: str) -> Optional[Graph]:
    """Print errors and return ``None`` on failure instead of raising."""
    try:
        return parse_map(path)
    except (ParseError, OSError) as exc:
        print(f"parser error: {exc}")
        return None
