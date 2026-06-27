"""Standalone checker: re-runs every map, verifies every subject rule.

It is NOT part of the deliverable (gitignored). It just confirms the
solver respects every constraint in the subject:

- output format is exactly D<id>-<zone> or D<id>-<connection_label>
- a drone never appears twice in one turn
- zone capacity is never exceeded
- link capacity is never exceeded
- blocked zones are never entered
- restricted zones take 2 turns (enter connection, then arrive)
- a drone that arrives from a restricted-zone transit does not move
  again the same turn
- all nb_drones eventually reach the end zone
- the simulation finishes at or below the subject target
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from src.parser import parse_map  # noqa: E402

TARGETS = {
    "maps/easy/01_linear_path.txt": 6,
    "maps/easy/02_simple_fork.txt": 8,
    "maps/easy/03_basic_capacity.txt": 6,
    "maps/medium/01_dead_end_trap.txt": 12,
    "maps/medium/02_circular_loop.txt": 15,
    "maps/medium/03_priority_puzzle.txt": 12,
    "maps/hard/01_maze_nightmare.txt": 30,
    "maps/hard/02_capacity_hell.txt": 35,
    "maps/hard/03_ultimate_challenge.txt": 45,
}


def run_solver(map_path: str) -> Tuple[List[str], int]:
    """Invoke `python -m src <map>` and capture the turn-by-turn output."""
    proc = subprocess.run(
        [sys.executable, "-m", "src", map_path, "--no-visual"],
        capture_output=True, text=True, cwd=ROOT,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"solver failed: {proc.stderr.strip()}")
    lines = proc.stdout.strip().splitlines()
    summary = lines[-1]
    turn_lines = []
    for line in lines[:-1]:
        if line.strip() and line.startswith("D"):
            turn_lines.append(line.strip())
    # parse turn count from summary: "=> Map solved in N turns ..."
    parts = summary.split()
    turns = int(parts[parts.index("in") + 1])
    return turn_lines, turns


def verify(map_path: str, turn_lines: List[str]) -> List[str]:
    """Return a list of violations (empty if everything is fine)."""
    violations: List[str] = []
    graph = parse_map(str(ROOT / map_path))
    nb_drones = graph.nb_drones

    # Track drone state across turns.
    drone_pos: Dict[int, str] = {
        i: graph.start for i in range(1, nb_drones + 1)
    }
    drone_flight: Dict[int, str] = {}  # drone_id -> connection label
    delivered: Set[int] = set()

    # Zone occupancy (start has unlimited cap, but track for sanity).
    def zone_load() -> Dict[str, int]:
        load: Dict[str, int] = {}
        for d in range(1, nb_drones + 1):
            if d in delivered:
                continue
            if d in drone_flight:
                # In flight: occupies the destination (reserved).
                dst = drone_flight[d].split("|")[1]
                load[dst] = load.get(dst, 0) + 1
            else:
                load[drone_pos[d]] = load.get(drone_pos[d], 0) + 1
        return load

    for turn_idx, line in enumerate(turn_lines, start=1):
        tokens = line.split()
        drones_acted_this_turn: Set[int] = set()
        # Per-turn link usage
        link_use_this_turn: Dict[Tuple[str, str], int] = {}

        # 1. Parse all moves of this turn
        moves = []
        for tok in tokens:
            if not tok.startswith("D"):
                violations.append(f"turn {turn_idx}: bad token '{tok}'")
                continue
            try:
                id_str, rest = tok[1:].split("-", 1)
                drone_id = int(id_str)
            except ValueError:
                violations.append(f"turn {turn_idx}: malformed '{tok}'")
                continue
            if drone_id in drones_acted_this_turn:
                violations.append(
                    f"turn {turn_idx}: drone D{drone_id} appears twice")
            drones_acted_this_turn.add(drone_id)
            moves.append((drone_id, rest))

        # 2. Apply each move
        for drone_id, rest in moves:
            if drone_id in delivered:
                violations.append(
                    f"turn {turn_idx}: D{drone_id} already delivered")
                continue
            # Is rest a zone or a connection label?
            if rest in graph.zones:
                # Arriving at a zone (normal move or transit completion)
                if drone_id in drone_flight:
                    # transit completion - the label should match
                    pending_label = drone_flight[drone_id].split("|")[0]
                    a, b = pending_label.split("-")
                    target = drone_flight[drone_id].split("|")[1]
                    if rest != target:
                        violations.append(
                            f"turn {turn_idx}: D{drone_id} arrived at {rest}"
                            f" but was in flight to {target}")
                    # connection traversal: link counts for this turn
                    key = (min(a, b), max(a, b))
                    link_use_this_turn[key] = (
                        link_use_this_turn.get(key, 0) + 1
                    )
                    drone_pos[drone_id] = rest
                    del drone_flight[drone_id]
                else:
                    # normal 1-turn move from drone_pos[drone_id] to rest
                    src = drone_pos[drone_id]
                    conn = graph.get_connection(src, rest)
                    if conn is None:
                        violations.append(
                            f"turn {turn_idx}: D{drone_id} {src}->{rest}"
                            " has no such connection")
                        continue
                    dst_zone = graph.zones[rest]
                    if dst_zone.is_blocked:
                        violations.append(
                            f"turn {turn_idx}: D{drone_id} entered "
                            f"blocked zone {rest}")
                    if dst_zone.zone_type == "restricted":
                        violations.append(
                            f"turn {turn_idx}: D{drone_id} immediate move to "
                            f"restricted zone {rest} (should be 2-turn)")
                    key = conn.key
                    link_use_this_turn[key] = (
                        link_use_this_turn.get(key, 0) + 1
                    )
                    if link_use_this_turn[key] > conn.max_capacity:
                        violations.append(
                            f"turn {turn_idx}: link {conn.label()} over "
                            f"capacity ({link_use_this_turn[key]} > "
                            f"{conn.max_capacity})")
                    drone_pos[drone_id] = rest
                    if rest == graph.end:
                        delivered.add(drone_id)
            else:
                # Connection label: drone is entering transit toward
                # a restricted zone. Format "a-b".
                if "-" not in rest:
                    violations.append(
                        f"turn {turn_idx}: D{drone_id} unknown token "
                        f"'{rest}' (not a zone or connection)")
                    continue
                a, b = rest.split("-", 1)
                if a not in graph.zones or b not in graph.zones:
                    violations.append(
                        f"turn {turn_idx}: D{drone_id} connection '{rest}' "
                        f"has unknown endpoints")
                    continue
                src = drone_pos[drone_id]
                # Which endpoint is the destination?
                if src == a:
                    dst = b
                elif src == b:
                    dst = a
                else:
                    violations.append(
                        f"turn {turn_idx}: D{drone_id} flight '{rest}' from "
                        f"{src} but drone is not on either endpoint")
                    continue
                if graph.zones[dst].zone_type != "restricted":
                    violations.append(
                        f"turn {turn_idx}: D{drone_id} transit to "
                        f"non-restricted zone {dst}")
                conn = graph.get_connection(a, b)
                if conn is None:
                    violations.append(
                        f"turn {turn_idx}: connection '{rest}' does not exist")
                    continue
                key = conn.key
                link_use_this_turn[key] = link_use_this_turn.get(key, 0) + 1
                if link_use_this_turn[key] > conn.max_capacity:
                    violations.append(
                        f"turn {turn_idx}: link {conn.label()} over capacity")
                # Mark drone in flight
                drone_flight[drone_id] = f"{a}-{b}|{dst}"

        # 3. After applying moves, check zone capacities
        load = zone_load()
        for z_name, count in load.items():
            zone = graph.zones[z_name]
            cap = zone.effective_capacity()
            if zone.is_blocked and count > 0:
                violations.append(
                    f"turn {turn_idx}: blocked zone {z_name} has "
                    f"{count} drones")
            if count > cap:
                violations.append(
                    f"turn {turn_idx}: zone {z_name} over capacity "
                    f"({count} > {cap})")

    # All drones must end at the end zone.
    for d in range(1, nb_drones + 1):
        if d not in delivered:
            violations.append(
                f"drone D{d} never reached the end zone "
                f"(final pos: {drone_pos.get(d)})")

    return violations


def main() -> int:
    overall_ok = True
    print(f"{'Map':50} {'Drones':>7} {'Target':>7} {'Ours':>5}  Status")
    print("-" * 90)
    for map_path, target in TARGETS.items():
        try:
            turn_lines, turns = run_solver(map_path)
            graph = parse_map(str(ROOT / map_path))
            violations = verify(map_path, turn_lines)
        except Exception as exc:
            print(f"{map_path:50} CRASH: {exc}")
            overall_ok = False
            continue
        within = "OK" if turns <= target else "OVER"
        clean = "clean" if not violations else f"{len(violations)} issue(s)"
        status = f"[{within}] {clean}"
        if violations or turns > target:
            overall_ok = False
        print(
            f"{map_path:50} {graph.nb_drones:>7} {target:>7} {turns:>5}  "
            f"{status}"
        )
        for v in violations:
            print(f"    -> {v}")
    print()
    if overall_ok:
        print("ALL MAPS PASS every subject rule and every performance target.")
        return 0
    else:
        print("SOMETHING FAILED — see above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
