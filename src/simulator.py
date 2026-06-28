from typing import Dict, List, Optional, Set, Tuple
from .drone import Drone
from .graph import Graph
from .pathfinder import PathFinder


Move = Tuple[Drone, str]  # (drone, label printed at end of turn)


class Simulator:
    """Turn-by-turn drone simulation engine

    Strategy (kept intentionally simple):

    1.  ``PathFinder.k_paths`` gives us several diverse short routes.
    2.  We assign each drone to a path so that the longest queue is
        as short as possible (load balancing).
    3.  Each turn:
        a.  Drones in transit toward a restricted zone arrive.
        b.  Drones standing in a real zone try to advance one step
            along their planned path. We process drones farther along
            their path first so they free up space behind them
            (this matches the subject's rule that "drones moving out
            of a zone free up capacity for that same turn").
    """

    DEADLOCK_LIMIT = 1000

    def __init__(self, graph: Graph) -> None:
        self.graph = graph
        self.drones: List[Drone] = []
        self.zone_load: Dict[str, int] = {z: 0 for z in graph.zones}
        self.link_load: Dict[Tuple[str, str], int] = {}
        self.turn = 0
        self.turn_log: List[List[Move]] = []
        self.paths: List[List[str]] = []
        self._build_drones()

    def _build_drones(self) -> None:
        """Create drones and plan their paths."""
        finder = PathFinder(self.graph)
        # Up to nb_drones diverse paths, capped so search is bounded.
        k = min(self.graph.nb_drones, 8)
        self.paths = finder.k_paths(max(k, 1))
        if not self.paths:
            raise RuntimeError("no path from start to end")
        # Assign each drone to the path with the smallest projected finish.
        finish_turn: List[int] = [0] * len(self.paths)
        path_cost = [PathFinder.path_cost(self.graph, p) for p in self.paths]
        for drone_id in range(1, self.graph.nb_drones + 1):
            # Pick the path whose next-drone arrival turn is earliest.
            best_index = min(
                range(len(self.paths)),
                key=lambda i: max(finish_turn[i] + 1, path_cost[i]),
            )
            chosen = self.paths[best_index]
            self.drones.append(Drone(drone_id, self.graph.start, chosen))
            finish_turn[best_index] = max(
                finish_turn[best_index] + 1, path_cost[best_index]
            )
        # All drones start at the start hub; it has infinite cap so loading
        # the count is fine but unused. Keep it at 0 to skip start tracking.

    def run(self) -> int:
        """Run until all drones are delivered. Return the turn count."""
        stalled = 0
        while not self.all_delivered():
            moves = self.step()
            self.turn_log.append(moves)
            if not moves:
                stalled += 1
                if stalled > 5:
                    raise RuntimeError("simulation deadlocked")
            else:
                stalled = 0
            if self.turn > self.DEADLOCK_LIMIT:
                raise RuntimeError("simulation exceeded turn limit")
        return self.turn

    def all_delivered(self) -> bool:
        """True once every drone has reached the end zone."""
        return all(d.delivered for d in self.drones)

    def step(self) -> List[Move]:
        """Advance one turn. Return the list of moves to print.

        ``self.link_load`` only tracks drones still mid-flight toward a
        restricted zone (those occupy the connection across turns).
        For the rest of the check we copy it into ``turn_link_use``,
        which counts every drone using a link during this single turn.
        Drones that just completed a transit do not move again this
        turn -- arriving is considered their action.
        """
        arrivals, just_arrived = self._complete_transits()
        turn_link_use: Dict[Tuple[str, str], int] = dict(self.link_load)
        new_moves = self._advance_ready_drones(turn_link_use, just_arrived)
        self.turn += 1
        return arrivals + new_moves

    def _complete_transits(self) -> Tuple[List[Move], Set[int]]:
        """Phase 1: drones in flight to a restricted zone arrive now."""
        out: List[Move] = []
        just_arrived: Set[int] = set()
        for drone in self.drones:
            if drone.delivered:
                continue
            if drone.in_flight_to is None:
                continue
            target = drone.in_flight_to
            link_label = drone.in_flight_via or ""
            link_key = self._link_key_from_label(link_label)
            if link_key is not None:
                self.link_load[link_key] = max(
                    0, self.link_load.get(link_key, 0) - 1
                )
            drone.position = target
            drone.path_index += 1
            drone.in_flight_to = None
            drone.in_flight_via = None
            just_arrived.add(drone.id)
            out.append((drone, target))
            if target == self.graph.end:
                drone.delivered = True
                self.zone_load[target] = max(0, self.zone_load[target] - 1)
        return out, just_arrived

    def _advance_ready_drones(
        self,
        turn_link_use: Dict[Tuple[str, str], int],
        just_arrived: Set[int],
    ) -> List[Move]:
        """Phase 2: try to move every non-delivered, non-in-flight drone.

        Drones in ``just_arrived`` already used their turn by arriving
        from a 2-turn restricted-zone transit, so they cannot move again.
        """
        ready = [
            d for d in self.drones
            if not d.delivered
            and d.in_flight_to is None
            and d.id not in just_arrived
        ]
        # Drones farther along their path go first so they free room behind.
        ready.sort(key=lambda d: -d.path_index)
        out: List[Move] = []
        for drone in ready:
            move = self._try_move(drone, turn_link_use)
            if move is not None:
                out.append(move)
        return out

    def _try_move(
        self,
        drone: Drone,
        turn_link_use: Dict[Tuple[str, str], int],
    ) -> Optional[Move]:
        """Try to advance ``drone`` one step. Return the move or None."""
        next_name = drone.next_zone
        if next_name is None:
            return None
        zone = self.graph.zones[next_name]
        if zone.is_blocked:
            return None
        link = self.graph.get_connection(drone.position, next_name)
        if link is None:
            return None
        if turn_link_use.get(link.key, 0) >= link.max_capacity:
            return None
        cap = zone.effective_capacity()
        if self.zone_load.get(next_name, 0) + 1 > cap:
            return None
        # Commit: free origin slot, reserve target slot, use link this turn.
        if drone.position != self.graph.start:
            self.zone_load[drone.position] = max(
                0, self.zone_load[drone.position] - 1
            )
        self.zone_load[next_name] = self.zone_load.get(next_name, 0) + 1
        turn_link_use[link.key] = turn_link_use.get(link.key, 0) + 1
        if zone.zone_type == "restricted":
            # 2-turn transit: drone arrives next turn. The connection
            # stays occupied until then -> bump persistent link_load.
            self.link_load[link.key] = self.link_load.get(link.key, 0) + 1
            drone.in_flight_to = next_name
            drone.in_flight_via = link.label()
            return (drone, link.label())
        # 1-turn move: drone arrives now.
        drone.position = next_name
        drone.path_index += 1
        if drone.position == self.graph.end:
            drone.delivered = True
            self.zone_load[next_name] = max(
                0, self.zone_load[next_name] - 1
            )
        return (drone, next_name)

    @staticmethod
    def _link_key_from_label(label: str) -> Optional[Tuple[str, str]]:
        if "-" not in label:
            return None
        a, b = label.split("-", 1)
        if a <= b:
            return (a, b)
        return (b, a)

    def format_output(self) -> str:
        """Return the textual turn-by-turn output required by the subject."""
        lines: List[str] = []
        for moves in self.turn_log:
            if not moves:
                continue
            tokens = [f"{d.label}-{label}" for d, label in moves]
            lines.append(" ".join(tokens))
        return "\n".join(lines)
