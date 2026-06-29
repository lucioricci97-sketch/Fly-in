import argparse
import sys
from typing import List, Optional

from .parser import safe_parse_map
from .simulator import Simulator


def _build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fly-in",
        description="Route drones from start to end across a zone graph.",
    )
    parser.add_argument("map_file", help="path to the map .txt file")
    parser.add_argument(
        "--no-visual",
        action="store_true",
        help="skip the pygame window (terminal output only)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="write the turn-by-turn output to this file",
    )
    parser.add_argument(
        "--capacity-info", action="store_true", help="Display capacity usage per turn"
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Program entry. Returns the process exit code."""
    args = _build_argparser().parse_args(argv)
    graph = safe_parse_map(args.map_file)
    if graph is None:
        return 1
    try:
        simulator = Simulator(graph)
        if not args.capacity_info:
            total_turns = simulator.run()
        else:
            while not simulator.all_delivered():
                moves = simulator.step()
                simulator.turn_log.append(moves)

                print(f"--- Turn {simulator.turn} ---")
                
                # 1. Stampa movimenti
                move_tokens = [f"{d.label}-{label}" for d, label in moves]
                if move_tokens:
                    print(" ".join(move_tokens))
                
                # 2. Ciclo accoppiato Zona + Connessione
                for z_name, zone in graph.zones.items():
                    if not zone.is_start and not zone.is_end:
                        # Info Zona
                        load = simulator.zone_load.get(z_name, 0)
                        
                        # Cerchiamo la connessione collegata a questa zona (prendiamo la prima per brevità)
                        # O meglio, iteriamo su tutte le connessioni della zona
                        for conn in graph.connections.values():
                            if z_name in (conn.a, conn.b):
                                load_link = simulator.link_load.get(conn.key, 0)
                                print(f"Zone {z_name}: {load}/{zone.max_drones} drones, "
                                      f"Connection {conn.label()}: {load_link}/{conn.max_capacity} capacity used")
                print()
            total_turns = simulator.turn
    except RuntimeError as exc:
        print(f"simulation error: {exc}")
        return 2
    output = simulator.format_output()
    if not args.capacity_info:
        print(output)
        print()
        print(f"=> Map solved in {total_turns} turns "
          f"with {graph.nb_drones} drones.")
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as fp:
                fp.write(output)
                fp.write("\n")
        except OSError as exc:
            print(f"could not write output file: {exc}")
            return 3
    if not args.no_visual:
        try:
            from .visualizer import Visualizer
        except ImportError as exc:
            print(f"pygame not available, skipping visual: {exc}")
            return 0
        # Rebuild the simulator so the visualizer can step from turn 0.
        Visualizer(graph).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
