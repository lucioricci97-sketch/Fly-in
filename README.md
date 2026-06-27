*This project has been created as part of the 42 curriculum by luricci.*

# Fly-in

## Description

**Fly-in** is a drone routing simulator. You feed it a text file
describing a graph of zones and connections, and a number of drones
that must all travel from the `start` zone to the `end` zone. The
program plans paths, runs a turn-by-turn simulation honouring every
movement/capacity rule of the subject, prints the per-turn drone
moves, and optionally opens a `pygame` window so you can watch the
drones move step by step.

The goal is to deliver every drone in as few simulation turns as
possible while respecting:

- **Zone types** — `normal` (1 turn), `priority` (1 turn, preferred),
  `restricted` (2-turn transit), `blocked` (forbidden).
- **Zone capacity** — `max_drones=N` (default 1; start/end uncapped).
- **Connection capacity** — `max_link_capacity=N` (default 1).
- **Simultaneous movement** — drones may move in the same turn as
  long as every capacity constraint is satisfied.

## Instructions

### Requirements

- Python **3.10+** (tested on 3.14).
- `pygame-ce` for the visual window (drop-in replacement for `pygame`
  with prebuilt wheels for newer Python; same `import pygame` API).
- `flake8` + `mypy` for linting.

### Install

```bash
make install
```

This runs `pip install -r requirements.txt` and pulls in `pygame`,
`flake8`, and `mypy`.

### Run

```bash
# Easy default map, with the pygame window
make run

# Pick another map
make run MAP=maps/hard/03_ultimate_challenge.txt

# Direct invocation:
python -m src maps/medium/02_circular_loop.txt
python -m src maps/easy/01_linear_path.txt --no-visual
python -m src maps/easy/01_linear_path.txt -o output.txt
```

### Other make targets

```bash
make debug         # run inside Python's pdb debugger (no pygame window)
make clean         # remove __pycache__ and .mypy_cache
make lint          # flake8 . + mypy with the subject's flags
make lint-strict   # flake8 . + mypy --strict
```

### Visualizer controls

| Key             | Action                       |
|-----------------|------------------------------|
| `SPACE` / `→`   | advance one simulation turn  |
| `A`             | toggle auto-play             |
| `R`             | reset the simulation         |
| `ESC` / `Q`     | quit                         |

Zones are drawn as coloured circles at the coordinates given in the
map file. The interior fill colour identifies a zone's mechanics
(pale red for restricted, pale blue for priority, pale green for
start, pale yellow for end, white for normal, grey for blocked).
A thick outer border ring shows the aesthetic colour from the map's
`color=...` metadata. A legend in the top-right corner explains the
fill colours. Drones appear as dark numbered badges (`D1`, `D2`, …)
and sit at the midpoint of a connection while in flight toward a
restricted zone; multiple drones at the same location spread into a
neat non-overlapping grid.

## How it works

The pipeline has four pieces, each in its own module:

1. **`parser.py`** reads the `.txt` map, validates every line, and
   builds a `Graph` of `Zone` and `Connection` objects. Parsing
   errors include the offending line number.
2. **`pathfinder.py`** computes short paths from start to end using a
   hand-rolled Dijkstra (heap from `heapq` — *not* the forbidden
   `graphlib`). Edge weights are the destination zone's `cost`
   (`restricted = 2`, everything else `= 1`); priority zones receive
   a tiny bonus so they are picked over equal-length normal paths.
   `k_paths` returns several **equal-cost** alternates so drones can
   be spread across parallel routes; we deliberately reject longer
   detours because routing a drone through them just delays it
   without easing the real bottleneck.
3. **`simulator.py`** runs the discrete-turn simulation. Each turn:
   1. **Arrival phase** — drones in flight toward a restricted zone
      complete their transit and free the connection.
   2. **Move phase** — every other drone tries to take one step
      along its planned path, sorted by how far along the path they
      are (drones closer to the end go first, so they vacate space
      for the drones behind them — the subject explicitly says
      *"drones moving out of a zone free up capacity for that same
      turn"*).
   - Zone capacity, connection capacity, blocked zones, and the
     2-turn transit rule are all enforced. Drones that arrive from
     a transit do **not** move again the same turn (one action per
     turn).
4. **`visualizer.py`** (pygame) draws the graph and steps the
   simulation interactively.

### Why this algorithm

It's the simplest design that still meets every reference target:

- **Dijkstra** is the textbook shortest-path. Implementing it with a
  heap keeps it close to optimal (`O((V + E) log V)`) without
  pulling in `networkx`.
- **Equal-cost alternates** give parallel pipelining on maps with a
  real fork (`easy/02_simple_fork`, `hard/01_maze_nightmare`, ...)
  while leaving single-path maps alone (`medium/02_circular_loop`).
- **Greedy turn order** (drones farther along the path move first)
  emulates the subject's "leaving frees the slot" rule without a
  global solver.
- **One action per turn** matches the subject's output spec and
  prevents the same drone from appearing twice on a line.

A full max-flow / time-expanded-graph approach (like the reference
student) is more sophisticated but considerably more code and is
not required to clear the targets.

## Performance

Measured on the maps that ship with the subject:

| Map                                | Drones | Target  | This solver |
|------------------------------------|--------|---------|-------------|
| `easy/01_linear_path.txt`          | 2      | ≤ 6     | **4**       |
| `easy/02_simple_fork.txt`          | 4      | ≤ 8     | **4**       |
| `easy/03_basic_capacity.txt`       | 4      | ≤ 6     | **4**       |
| `medium/01_dead_end_trap.txt`      | 5      | ≤ 12    | **8**       |
| `medium/02_circular_loop.txt`      | 6      | ≤ 15    | **15**      |
| `medium/03_priority_puzzle.txt`    | 5      | ≤ 12    | **8**       |
| `hard/01_maze_nightmare.txt`       | 8      | ≤ 30    | **13**      |
| `hard/02_capacity_hell.txt`        | 12     | ≤ 35    | **16**      |
| `hard/03_ultimate_challenge.txt`   | 15     | ≤ 45    | **26**      |

Every target is met.

### Complexity

- **Reading the map:** The program looks at every zone and connection exactly once to build the map.
- **Finding paths:** We use Dijkstra's algorithm up to 8 times to find alternative routes. The time it takes depends on how many zones and connections the map has, but it handles large maps very quickly.
- **Running the simulation:** During each turn, the program only checks the drones that haven't reached the end yet. The total time depends on the number of drones multiplied by the total number of turns they take.
- **Memory usage:** We only calculate the paths once at the very beginning and save them. During the simulation, we only keep track of a few numbers: how many drones are in each zone, how full the connections are, and what step each drone is on. This makes our memory usage incredibly small and efficient.

## Visual representation

The pygame window displays:

- the whole graph laid out using each zone's `(x, y)` coordinates on a light graph-paper background;
- the internal fill colour of a zone immediately identifies its mechanics (e.g. pale red for restricted, pale blue for priority);
- a thick outer border displays the aesthetic colour requested by the map's `color=...` metadata (to satisfy the subject's display rule without causing cognitive overload);
- a clear Legend in the top right corner;
- drones as dark badges that form neat, non-overlapping grids when multiple drones queue in the same zone.

It enhances the user experience because the textual output alone
(`D1-roof1 D2-corridorA`) is hard to follow on dense maps —
watching drones queue at a bottleneck zone, take a restricted
shortcut, or split across a fork makes the algorithm's decisions
immediately legible.

## Project layout

```
fly-in/
├── Makefile
├── README.md
├── requirements.txt
├── .gitignore
├── maps/                      # provided maps (easy/medium/hard)
└── src/
    ├── __init__.py
    ├── __main__.py            # python -m src ...
    ├── main.py                # CLI, glue
    ├── zone.py                # Zone class
    ├── connection.py          # Connection class
    ├── drone.py               # Drone class
    ├── graph.py               # Graph (zones + connections + neighbours)
    ├── parser.py              # map-file -> Graph, with line-aware errors
    ├── pathfinder.py          # hand-rolled Dijkstra + k-paths
    ├── simulator.py           # turn-by-turn engine
    └── visualizer.py          # pygame window
```

## Resources

- [Dijkstra's algorithm — Wikipedia](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)
- [BFS / DFS / shortest paths — CP-Algorithms](https://cp-algorithms.com/graph/dijkstra.html)
- [Python `heapq` module](https://docs.python.org/3/library/heapq.html)
- [pygame docs](https://www.pygame.org/docs/)
- [PEP 257 — Docstring conventions](https://peps.python.org/pep-0257/)
- [mypy documentation](https://mypy.readthedocs.io/)

### AI usage

I used an AI assistant to:

- talk through how to encode the restricted-zone 2-turn transit so
  the connection stays busy for one whole turn while the
  destination zone reserves a slot;
- review my Dijkstra implementation for correctness with the heap;
- pair-review the simulator's turn-resolution order (process drones
  closer to the end first so they free space for the ones behind);
- check the README for clarity and completeness before submission.

Every line of code and every algorithmic decision was reviewed and
understood end-to-end — I can defend any part of the project during
the peer evaluation.
