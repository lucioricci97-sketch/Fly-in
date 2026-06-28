import heapq
from typing import Dict, List, Optional, Set, Tuple

from .graph import Graph


class PathFinder:
    """Find one or several short paths from start to end.

    We use Dijkstra (with heapq, *not* the forbidden ``graphlib``) where
    the cost of an edge ``u -> v`` is the destination zone's ``cost``
    (1 for normal/priority, 2 for restricted, blocked zones are skipped).
    Priority zones get a tiny negative tweak so they are preferred when
    two paths are otherwise equal in length.
    """

    PRIORITY_BONUS = 0.01

    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    def _edge_cost(self, dst_name: str, used_edges: Set[Tuple[str, str]],
                   src_name: str) -> Optional[float]:
        """Return the cost to enter ``dst_name`` from ``src_name``.

        Returns ``None`` if blocked. ``used_edges`` adds a penalty so that
        repeated edges are avoided when looking for alternate paths.
        """
        dst = self.graph.zones[dst_name]
        if dst.is_blocked:
            return None
        cost: float = dst.cost
        if dst.zone_type == "priority":
            cost -= self.PRIORITY_BONUS
        edge_key = (min(src_name, dst_name), max(src_name, dst_name))
        if edge_key in used_edges:
            cost += 5.0  # heavy penalty to push the search elsewhere
        return cost

    def shortest_path(
        self,
        used_edges: Optional[Set[Tuple[str, str]]] = None,
    ) -> Optional[List[str]]:
        """Return the cheapest path from start to end, or None."""
        if used_edges is None:
            used_edges = set()
        start = self.graph.start
        end = self.graph.end
        dist: Dict[str, float] = {start: 0.0}
        prev: Dict[str, Optional[str]] = {start: None}
        heap: List[Tuple[float, str]] = [(0.0, start)]
        while heap:
            d, node = heapq.heappop(heap)
            if d > dist.get(node, float("inf")):
                continue
            if node == end:
                break
            for neighbour in self.graph.neighbours(node):
                edge_cost = self._edge_cost(neighbour, used_edges, node)
                if edge_cost is None:
                    continue
                nd = d + edge_cost
                if nd < dist.get(neighbour, float("inf")):
                    dist[neighbour] = nd
                    prev[neighbour] = node
                    heapq.heappush(heap, (nd, neighbour))
        if end not in dist:
            return None
        return self._rebuild(prev, end)

    @staticmethod
    def _rebuild(prev: Dict[str, Optional[str]], end: str) -> List[str]:
        """Walk ``prev`` from end back to start, then reverse."""
        chain: List[str] = []
        cur: Optional[str] = end
        while cur is not None:
            chain.append(cur)
            cur = prev[cur]
        chain.reverse()
        return chain

    def k_paths(self, k: int) -> List[List[str]]:
        """Return up to ``k`` diverse short paths.

        We always keep the shortest path; then we greedily look for
        alternates that share as few edges as possible. An alternate
        is only kept if its real turn cost is within a small slack of
        the shortest path's cost, otherwise sending drones down it
        would make the simulation *slower* instead of faster.
        """
        base = self.shortest_path(set())
        if base is None:
            return []
        base_cost = self.path_cost(self.graph, base)
        results: List[List[str]] = [base]
        used: Set[Tuple[str, str]] = set(
            (min(u, v), max(u, v)) for u, v in zip(base, base[1:])
        )
        # Only keep alternates of (almost) the same cost as the base.
        # Longer detours don't reduce contention on the real bottleneck,
        # they just delay the drones routed through them.
        for _ in range(k - 1):
            path = self.shortest_path(used)
            if path is None or path in results:
                break
            if self.path_cost(self.graph, path) > base_cost:
                break
            results.append(path)
            for u, v in zip(path, path[1:]):
                used.add((min(u, v), max(u, v)))
        return results

    @staticmethod
    def path_cost(graph: Graph, path: List[str]) -> int:
        """Sum the turn cost of a path (1 per normal, 2 per restricted)."""
        total = 0
        for name in path[1:]:
            total += graph.zones[name].cost
        return total
