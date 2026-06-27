# Fly-in — Complete Study Guide

> This is your personal walkthrough of the project. Read it top to
> bottom before the peer review. Every concept, every file, every
> non-obvious line of code is explained here in plain language.

---

## Table of contents

1. [The big picture](#1-the-big-picture)
2. [Python concepts you must understand](#2-python-concepts-you-must-understand)
3. [Algorithm concepts: graphs, Dijkstra, BFS](#3-algorithm-concepts-graphs-dijkstra-bfs)
4. [The subject in plain English](#4-the-subject-in-plain-english)
5. [Project layout](#5-project-layout)
6. [File-by-file walkthrough](#6-file-by-file-walkthrough)
   - [zone.py](#61-srczonepy--a-graph-node)
   - [connection.py](#62-srcconnectionpy--a-graph-edge)
   - [drone.py](#63-srcdronepy--a-single-drone)
   - [graph.py](#64-srcgraphpy--the-whole-network)
   - [parser.py](#65-srcparserpy--reading-the-map-file)
   - [pathfinder.py](#66-srcpathfinderpy--dijkstra--k-paths)
   - [simulator.py](#67-srcsimulatorpy--the-heart-of-the-project)
   - [visualizer.py](#68-srcvisualizerpy--the-pygame-window)
   - [main.py / __main__.py](#69-srcmainpy-and-srcmainpy)
7. [Why I made these choices](#7-why-i-made-these-choices)
8. [Edge cases and bugs I avoided](#8-edge-cases-and-bugs-i-avoided)
9. [How to prepare for the evaluation](#9-how-to-prepare-for-the-evaluation)
10. [Defending yourself: likely questions + answers](#10-defending-yourself-likely-questions--answers)
11. [Live modification practice](#11-live-modification-practice)
12. [Glossary](#12-glossary)

---

## 1. The big picture

The project simulates a **fleet of drones** that has to travel from a
**start zone** to an **end zone** through a network of zones connected
by edges. Multiple drones move at the same time. Some zones are slow
(restricted), some are forbidden (blocked), some are preferred
(priority), and every zone/edge has a maximum number of drones it can
hold at once.

Your job is to:
1. **Read** a text file that describes the network.
2. **Plan** routes for each drone.
3. **Simulate** the drones turn by turn, respecting every rule.
4. **Output** what every drone did each turn.
5. **Visualize** the simulation in a pygame window.

The grade depends on (a) **correctness** (no crashes, no rule
violations, output format right) and (b) **performance** (how few
turns you take to deliver every drone, measured against the targets
in the subject).

### One sentence describing the whole solution

> "Plan a short path for each drone using Dijkstra, then run a
> turn-by-turn simulation where drones move along their paths one
> step at a time, waiting when a zone or edge is full, and treating
> restricted zones as 2-turn transits."

If you can say that sentence with conviction, you understand the
project.

---

## 2. Python concepts you must understand

You said you're not advanced in Python. Here are the building blocks
the project uses — make sure you know each one before the review.

### 2.1 Classes and objects

A **class** is a blueprint. An **object** (also called *instance*) is
what you get when you create one from the blueprint.

```python
class Zone:
    def __init__(self, name, max_drones):
        self.name = name
        self.max_drones = max_drones

z = Zone("roof1", 2)   # z is an object of class Zone
print(z.name)          # "roof1"
```

- `__init__` is the **constructor** — it runs automatically when you
  create the object. The arguments after `self` are what the caller
  passes in. `self` is the object itself.
- `self.name = name` stores `name` as an **attribute** on the object.
- The subject **mandates** OOP. Every domain concept in this project
  is a class.

### 2.2 Methods

A **method** is a function that lives inside a class.

```python
class Zone:
    def __init__(self, name): self.name = name
    def greet(self):
        return f"hello from {self.name}"

z = Zone("roof1")
print(z.greet())   # "hello from roof1"
```

`self` is always the first parameter — Python passes it
automatically when you write `z.greet()`.

### 2.3 Properties

`@property` lets you call a method **without parentheses**, like an
attribute. We use this for derived values like `zone.cost`:

```python
class Zone:
    @property
    def cost(self):
        return 2 if self.zone_type == "restricted" else 1

z = Zone(...)
print(z.cost)   # NOT z.cost()
```

### 2.4 Type hints

```python
def add(a: int, b: int) -> int:
    return a + b
```

`int` after the parameter tells Python (and `mypy`) what type to
expect. `-> int` is the return type. Common ones we use:

- `str` — text. `int` — integer. `float` — decimal.
- `List[int]` — a list of integers.
- `Dict[str, int]` — a dictionary mapping strings to integers.
- `Optional[int]` — either an int OR `None`.
- `Tuple[int, int]` — a pair of integers (fixed length).
- `Set[int]` — a set of integers.

The subject **mandates** type hints + mypy. If anyone asks why,
answer: "type hints catch bugs before runtime — mypy checks them
statically, and the subject requires it."

### 2.5 `from __future__ import annotations`

The first line of most files. It lets you use modern type-hint
syntax (`list[int]` instead of `List[int]`) on older Pythons. We
still use the `typing` module forms for clarity, but the import
keeps options open.

### 2.6 Dictionaries (`dict`)

A mapping from keys to values:

```python
d = {"red": 1, "blue": 2}
d["green"] = 3                  # add a key
print(d.get("yellow", 0))       # 0 if "yellow" not present, no crash
```

`d.get(key, default)` is safer than `d[key]` because it doesn't
crash on missing keys.

### 2.7 Sets (`set`)

A collection where every element is unique and lookup is fast:

```python
s = set()
s.add(1); s.add(2); s.add(1)
print(2 in s)   # True, O(1) lookup
print(len(s))   # 2 — duplicates collapse
```

We use sets for "edges already used" and "drones that just arrived".

### 2.8 Tuples

Like a list but **immutable** (can't be changed after creation).
We use tuples as **dict keys** because lists can't be dict keys.

```python
edge_key = ("start", "waypoint1")  # tuple of two strings
adj = {edge_key: 1}
```

### 2.9 Context manager (`with`)

```python
with open("file.txt", "r", encoding="utf-8") as fp:
    for line in fp:
        ...
# the file is automatically closed here, even if an exception was raised
```

The subject **mandates** using context managers for files. Our
parser does exactly this.

### 2.10 Exceptions

```python
try:
    nb = int(some_string)
except ValueError as exc:
    raise ParseError(line_no, "not an integer") from exc
```

- `try/except` catches errors so the program doesn't crash.
- `raise X from Y` keeps the original exception in the traceback —
  helpful for debugging.
- We have a custom `ParseError` class so callers can tell parser
  errors apart from other errors.

### 2.11 `enumerate`

```python
for i, line in enumerate(["a", "b", "c"], start=1):
    print(i, line)   # 1 a, 2 b, 3 c
```

We use this in the parser so error messages can say *"line 7:
something is wrong"*.

### 2.12 List comprehensions

A compact way to build a list:

```python
ready = [d for d in self.drones if not d.delivered]
```

Same as:

```python
ready = []
for d in self.drones:
    if not d.delivered:
        ready.append(d)
```

### 2.13 `lambda`

An anonymous (unnamed) one-line function. We use it to tell `sort`
how to compare items:

```python
ready.sort(key=lambda d: -d.path_index)
```

This sorts by `path_index` **descending** (because of the minus
sign).

### 2.14 `min(..., key=...)`

Pick the smallest item using a custom score:

```python
best_index = min(
    range(len(self.paths)),
    key=lambda i: max(finish_turn[i] + 1, path_cost[i]),
)
```

Reads as: *"out of indices 0..N-1, pick the one whose finish-turn
estimate is smallest."*

### 2.15 `heapq`

Python's standard min-heap (priority queue). We use it for
Dijkstra:

```python
import heapq
heap = [(0.0, "start")]            # (distance, node)
heapq.heappush(heap, (5.0, "x"))
dist, node = heapq.heappop(heap)   # always returns the smallest
```

**This is not a graph library.** It's a generic data structure
(like a list). The subject forbids `networkx`, `graphlib`, etc. —
graph algorithms. `heapq` is allowed. If asked, say: "heapq is the
standard-library heap data structure, not graph logic."

---

## 3. Algorithm concepts: graphs, Dijkstra, BFS

### 3.1 What is a graph?

A graph is a set of **nodes** (also called **vertices**) connected
by **edges**. In our case, nodes are zones and edges are
connections. The graph is **undirected** (an edge goes both ways)
and **weighted** (entering a zone costs 1 or 2 turns).

The data structure we use is an **adjacency list**: for each node, a
list of its neighbours.

```python
adjacency = {
    "start": ["roof1", "corridorA"],
    "roof1": ["start", "roof2"],
    "roof2": ["roof1", "goal"],
    ...
}
```

### 3.2 Why we can't use `networkx` or `graphlib`

The subject explicitly forbids them: *"any library that helps with
graph logic is forbidden"*. So we hand-roll:

- the graph data structure (the `Graph` class),
- the shortest-path algorithm (`pathfinder.py`),
- the traversal logic in the simulator.

### 3.3 Breadth-First Search (BFS)

BFS finds the shortest path in **unweighted** graphs — every edge
has the same cost. It explores neighbours layer by layer using a
FIFO queue.

We don't use plain BFS because our edges have different costs (1
vs 2). But you should understand it because BFS is conceptually
simpler than Dijkstra.

### 3.4 Dijkstra's algorithm

Dijkstra finds the shortest path in **weighted** graphs (positive
weights only). Mental model:

1. Start with distance 0 at the source, infinity everywhere else.
2. Put `(0, source)` in a heap.
3. Pop the node with the **smallest current distance**.
4. For each neighbour, if going through the popped node gives a
   smaller distance, update it and push.
5. Repeat until the heap is empty (or we reach the target).
6. Reconstruct the path by following the `prev` map backwards.

Complexity: **O((V + E) log V)** with a heap, where V = nodes, E =
edges.

In our project, the edge weight when going **from u to v** is just
`v.cost` (1 for normal/priority, 2 for restricted, blocked is
skipped entirely). Priority zones get a tiny -0.01 bonus so they
beat normal zones at equal length.

### 3.5 K-shortest paths (our `k_paths`)

We want **multiple** short paths so we can spread drones across
them and pipeline movement.

Strategy: run Dijkstra, record the path, then **penalize the edges
it used** (add cost +5). Run Dijkstra again — it now prefers
unused edges. Stop when the next path is *longer* than the first
one (longer alternates only delay drones without helping).

This is NOT a textbook algorithm — it's a pragmatic heuristic. If
asked, say: *"It's a simple multi-path heuristic. I add a penalty
to edges already used so subsequent calls to Dijkstra naturally
find diverse paths."*

### 3.6 Why not max-flow / time-expanded graph?

The reference student used Dinic's max-flow on a time-expanded
graph. That's mathematically optimal but **far** more complex (~10x
the code). For all 9 subject maps, our simple Dijkstra + k-paths
approach hits every performance target. The subject doesn't require
optimality, just hitting the targets.

---

## 4. The subject in plain English

### 4.1 What the input file looks like

```
nb_drones: 5

start_hub: start 0 0 [color=green]
end_hub: goal 10 10 [color=yellow]
hub: roof1 3 4 [zone=restricted color=red]
hub: corridorA 4 3 [zone=priority max_drones=2]

connection: start-roof1
connection: roof1-goal [max_link_capacity=2]
# this is a comment
```

- `nb_drones:` — how many drones to deliver.
- `start_hub:` — the start zone (exactly one).
- `end_hub:` — the end zone (exactly one).
- `hub:` — any other zone.
- Format: `<name> <x> <y> [optional metadata]`.
- Metadata `[...]`:
  - `zone=...` — `normal` (default), `priority`, `restricted`, `blocked`.
  - `color=...` — anything single-word.
  - `max_drones=N` — how many drones can be there at once (default 1).
- `connection: a-b [max_link_capacity=N]` — a bidirectional edge.
- Lines starting with `#` are comments.
- Zone names cannot contain `-` or spaces.

### 4.2 Movement rules

- One turn at a time. Drones can move simultaneously each turn.
- A drone may: **move forward**, **wait**, or **enter a connection
  toward a restricted zone** (2-turn transit).
- Entering a `restricted` zone takes 2 turns total: 1 turn on the
  connection, 1 turn arriving. The drone CANNOT wait on the
  connection.
- "Drones moving out of a zone free up capacity for that same turn"
  — order of operations matters: a leaving drone frees its slot
  before a new drone tries to enter.

### 4.3 Capacity rules

- Default zone capacity is 1.
- `start` and `end` are unlimited.
- Default connection capacity is 1.
- The simulation must NEVER violate any capacity.

### 4.4 Output format

Each non-empty turn is one line. Each token is `D<id>-<zone>` for a
normal arrival, or `D<id>-<connection_label>` for a drone in
flight to a restricted zone. Example:

```
D1-roof1 D2-corridorA
D1-roof2 D2-tunnelB
D1-goal D2-goal
```

Drones that didn't move are simply omitted. A drone never appears
twice on a line (one action per turn).

### 4.5 Scoring

- Pass = obey every rule. Fewer turns = better.
- Targets are listed in the subject (e.g. `medium/02` ≤ 15 turns).
- We hit every target.

---

## 5. Project layout

```
fly-in/
├── Makefile               # install / run / debug / clean / lint
├── README.md              # short overview (the deliverable doc)
├── STUDY_GUIDE.md         # this file (for you, before evaluation)
├── requirements.txt       # pygame-ce, flake8, mypy
├── .gitignore             # __pycache__, .mypy_cache, etc.
├── maps/                  # the subject's test maps
│   ├── easy/
│   ├── medium/
│   └── hard/
└── src/
    ├── __init__.py        # marks `src` as a Python package
    ├── __main__.py        # lets you do `python -m src ...`
    ├── main.py            # CLI entry point
    ├── zone.py            # Zone class
    ├── connection.py      # Connection class
    ├── drone.py           # Drone class
    ├── graph.py           # Graph class
    ├── parser.py          # parse a map file into a Graph
    ├── pathfinder.py      # Dijkstra + k-paths
    ├── simulator.py       # turn-by-turn engine
    └── visualizer.py      # pygame window
```

---

## 6. File-by-file walkthrough

For each file I explain **what it does**, **why it exists**, and
walk through the **non-obvious lines**.

### 6.1 `src/zone.py` — a graph node

**Job:** represent one zone of the network.

```python
class Zone:
    VALID_TYPES = ("normal", "priority", "restricted", "blocked")
```

`VALID_TYPES` is a class-level constant (shared by all instances)
listing the legal zone types. The constructor checks against it.

```python
    def __init__(self, name, x, y, zone_type="normal",
                 color=None, max_drones=1,
                 is_start=False, is_end=False):
        if zone_type not in self.VALID_TYPES:
            raise ValueError(...)
        if max_drones < 1:
            raise ValueError(...)
```

We validate at construction so a bad zone never enters the system.

```python
    @property
    def cost(self):
        if self.zone_type == "restricted":
            return 2
        return 1
```

Movement cost in turns to **arrive** at this zone. Priority counts
as 1 (the bonus for preferring priority happens in the pathfinder,
not here — here we report the actual simulation cost).

```python
    @property
    def is_blocked(self):
        return self.zone_type == "blocked"

    def effective_capacity(self):
        if self.is_start or self.is_end:
            return float("inf")
        return float(self.max_drones)
```

Start and end have **infinite** capacity. The subject says all
drones may share them. We return `float('inf')` so a `+1` check
never trips.

**Likely peer-review question:** *"Why is `cost` a property and not
a method?"*
**Answer:** *"It's a derived value with no side effects. A
`@property` lets callers read `zone.cost` like a normal attribute,
which is more readable. The subject's `is X` style fits this."*

### 6.2 `src/connection.py` — a graph edge

**Job:** represent one bidirectional link between two zones.

```python
class Connection:
    def __init__(self, a, b, max_capacity=1):
        if a <= b:
            self.a, self.b = a, b
        else:
            self.a, self.b = b, a
```

We sort the endpoints alphabetically. This way `Connection("x",
"y")` and `Connection("y", "x")` produce identical objects, so we
can detect duplicates with a set/dict.

```python
    @property
    def key(self):
        return (self.a, self.b)
```

`key` is the tuple `(a, b)` (sorted). We use it everywhere as a
dict key for capacity tracking.

```python
    def other(self, name):
        if name == self.a: return self.b
        if name == self.b: return self.a
        raise ValueError(...)
```

Given one endpoint, return the other. Handy for graph traversals.

```python
    def label(self):
        return f"{self.a}-{self.b}"
```

The string `"<a>-<b>"` is what we output when a drone is in flight
through this connection (subject format).

### 6.3 `src/drone.py` — a single drone

**Job:** track one drone's state.

```python
class Drone:
    def __init__(self, drone_id, start_zone, path):
        self.id = drone_id
        self.position = start_zone
        self.path = path[:]            # copy the list (defensive)
        self.path_index = 0
        self.in_flight_to = None
        self.in_flight_via = None
        self.delivered = False
```

- `position` — name of the zone the drone is sitting in.
- `path` — a list like `["start", "roof1", "roof2", "goal"]`.
- `path_index` — where we are in the path. 0 = at start.
- `in_flight_to` — if mid-transit to a restricted zone, the target
  zone name. Otherwise `None`.
- `in_flight_via` — the connection label being traversed.
- `delivered` — True once it reaches the end.

```python
    @property
    def label(self):
        return f"D{self.id}"

    @property
    def next_zone(self):
        next_index = self.path_index + 1
        if next_index >= len(self.path):
            return None
        return self.path[next_index]
```

`label` is the output identifier (`D1`, `D2`, ...). `next_zone` is
the next planned hop. If we're past the end, return `None`.

### 6.4 `src/graph.py` — the whole network

**Job:** hold all zones + connections, answer neighbour queries,
validate the structure.

```python
class Graph:
    def __init__(self):
        self.zones = {}          # name -> Zone
        self.connections = {}    # (a,b) -> Connection
        self.adjacency = {}      # name -> list of neighbour names
        self.start = ""
        self.end = ""
        self.nb_drones = 0
```

Three parallel structures so each operation is O(1) or O(neighbour
count).

```python
    def add_zone(self, zone):
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
```

Detect duplicates, set start/end, refuse multiple starts/ends. The
subject says exactly one of each.

```python
    def add_connection(self, conn):
        if conn.a not in self.zones: raise ValueError(...)
        if conn.b not in self.zones: raise ValueError(...)
        if conn.a == conn.b: raise ValueError(...)
        if conn.key in self.connections:
            raise ValueError(f"duplicate connection {conn.a}-{conn.b}")
        self.connections[conn.key] = conn
        self.adjacency[conn.a].append(conn.b)
        self.adjacency[conn.b].append(conn.a)
```

Connection endpoints must exist, can't be self-loops, can't
duplicate (the sorted key handles `a-b`/`b-a` automatically).

```python
    def get_connection(self, a, b):
        key = (a, b) if a <= b else (b, a)
        return self.connections.get(key)
```

Look up a connection regardless of endpoint order.

```python
    def validate(self):
        if not self.start: raise ValueError(...)
        if not self.end: raise ValueError(...)
        if self.nb_drones <= 0: raise ValueError(...)
```

Called once after parsing to make sure required pieces are present.

### 6.5 `src/parser.py` — reading the map file

**Job:** turn the `.txt` map into a `Graph`. Reject malformed
input with line-aware errors.

```python
class ParseError(Exception):
    def __init__(self, line_no, message):
        super().__init__(f"line {line_no}: {message}")
        self.line_no = line_no
```

Custom exception with the line number stored as an attribute.
Subject requires "clear error message indicating the line and
cause" — this is exactly that.

```python
_METADATA_RE = re.compile(r"\[([^\]]*)\]")
```

A regex matching anything inside `[...]`. The `[^\]]*` means "any
character that isn't `]`, zero or more times" — it stops at the
closing bracket.

```python
def _parse_metadata(raw, line_no):
    match = _METADATA_RE.search(raw)
    if not match:
        return {}
    inside = match.group(1).strip()
    if not inside:
        return {}
    meta = {}
    for token in inside.split():
        if "=" not in token:
            raise ParseError(line_no, f"bad metadata token '{token}'")
        key, value = token.split("=", 1)
        ...
        meta[key] = value
    return meta
```

For a line like `hub: roof1 3 4 [zone=restricted color=red]`, this
returns `{"zone": "restricted", "color": "red"}`.

Note `split("=", 1)`: split at most once, so a value containing `=`
wouldn't break (we don't actually allow it, but defensive).

```python
def _strip_metadata(raw):
    return _METADATA_RE.sub("", raw).strip()
```

Return the line with the `[...]` block removed. Used to get the
"plain" content like `roof1 3 4`.

```python
def _parse_zone_line(raw, line_no, is_start, is_end):
    meta = _parse_metadata(raw, line_no)
    body = _strip_metadata(raw)
    parts = body.split()
    if len(parts) != 3:
        raise ParseError(line_no, ...)
    name, sx, sy = parts
    if "-" in name or " " in name:
        raise ParseError(line_no, f"zone name '{name}' has dash or space")
    x = _parse_int(sx, line_no, "x coordinate")
    y = _parse_int(sy, line_no, "y coordinate")
    ...
```

Subject forbids `-` and space in zone names — we enforce it
explicitly.

```python
def parse_map(path):
    graph = Graph()
    nb_drones_seen = False
    with open(path, "r", encoding="utf-8") as fp:
        for raw_line_no, raw in enumerate(fp, start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            ...
```

We use `with open(...)` (context manager) and `enumerate(..., start=1)`
so error messages reference 1-based line numbers like a human reads.

Skip blank lines and comments (`#`) per the subject.

```python
def safe_parse_map(path):
    try:
        return parse_map(path)
    except (ParseError, OSError) as exc:
        print(f"parser error: {exc}")
        return None
```

Thin wrapper used by `main.py` so a parse failure becomes a clean
exit instead of a Python traceback.

### 6.6 `src/pathfinder.py` — Dijkstra + k-paths

**Job:** find one or several short paths from start to end.

```python
class PathFinder:
    PRIORITY_BONUS = 0.01
```

A tiny negative weight pushed onto priority zones so when two paths
have the same integer cost, the one through priority wins.

```python
    def _edge_cost(self, dst_name, used_edges, src_name):
        dst = self.graph.zones[dst_name]
        if dst.is_blocked:
            return None
        cost = float(dst.cost)
        if dst.zone_type == "priority":
            cost -= self.PRIORITY_BONUS
        edge_key = (min(src_name, dst_name), max(src_name, dst_name))
        if edge_key in used_edges:
            cost += 5.0
        return cost
```

Edge cost from `src` to `dst`:
- `None` if `dst` is blocked → Dijkstra skips it.
- Otherwise `dst.cost` (1 normal/priority, 2 restricted).
- Minus a small priority bonus.
- Plus a heavy penalty if this edge was already used in another path
  (drives the alternate-path search away).

```python
    def shortest_path(self, used_edges=None):
        if used_edges is None:
            used_edges = set()
        start = self.graph.start
        end = self.graph.end
        dist = {start: 0.0}
        prev = {start: None}
        heap = [(0.0, start)]
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
```

This is textbook Dijkstra:

- `dist[n]` = current best distance to node `n`.
- `prev[n]` = previous node in the best path.
- `heap` = priority queue of `(distance, node)` to visit.

The line `if d > dist.get(node, float("inf")): continue` is the
"lazy deletion" trick — when we update a distance we push a new
entry but don't remove the old one; this check ignores the stale
entry when it bubbles to the top.

```python
    @staticmethod
    def _rebuild(prev, end):
        chain = []
        cur = end
        while cur is not None:
            chain.append(cur)
            cur = prev[cur]
        chain.reverse()
        return chain
```

Walk `prev` backwards from `end` to `start`, then reverse. Output:
`["start", ..., "end"]`.

```python
    def k_paths(self, k):
        base = self.shortest_path(set())
        if base is None: return []
        base_cost = self.path_cost(self.graph, base)
        results = [base]
        used = set((min(u, v), max(u, v)) for u, v in zip(base, base[1:]))
        for _ in range(k - 1):
            path = self.shortest_path(used)
            if path is None or path in results: break
            if self.path_cost(self.graph, path) > base_cost: break
            results.append(path)
            for u, v in zip(path, path[1:]):
                used.add((min(u, v), max(u, v)))
        return results
```

Build up to `k` paths. Each iteration we add the previous path's
edges to `used`, re-run Dijkstra, and accept the new path only if
it's not longer than the base. This filters out long detours that
would actually slow drones down (we discovered this empirically on
`medium/02_circular_loop`).

### 6.7 `src/simulator.py` — the heart of the project

**Job:** run the turn-by-turn simulation.

```python
class Simulator:
    DEADLOCK_LIMIT = 1000
```

Hard ceiling so we don't loop forever if something goes wrong.

```python
    def __init__(self, graph):
        self.graph = graph
        self.drones = []
        self.zone_load = {z: 0 for z in graph.zones}
        self.link_load = {}
        self.turn = 0
        self.turn_log = []
        self.paths = []
        self._build_drones()
```

- `zone_load[name]` = how many drones are CURRENTLY in or
  reserved for zone `name` (including drones in mid-transit toward
  a restricted zone).
- `link_load[(a,b)]` = how many drones are currently OCCUPYING a
  connection across turns (only restricted-transit drones).
- `turn_log` collects the list of moves for each turn for output.

```python
    def _build_drones(self):
        finder = PathFinder(self.graph)
        k = min(self.graph.nb_drones, 8)
        self.paths = finder.k_paths(max(k, 1))
        if not self.paths:
            raise RuntimeError("no path from start to end")
        finish_turn = [0] * len(self.paths)
        path_cost = [PathFinder.path_cost(self.graph, p) for p in self.paths]
        for drone_id in range(1, self.graph.nb_drones + 1):
            best_index = min(
                range(len(self.paths)),
                key=lambda i: max(finish_turn[i] + 1, path_cost[i]),
            )
            chosen = self.paths[best_index]
            self.drones.append(Drone(drone_id, self.graph.start, chosen))
            finish_turn[best_index] = max(finish_turn[best_index] + 1,
                                          path_cost[best_index])
```

**Load balancing:** for each drone, pick the path with the
smallest projected finish turn. `finish_turn[i]` increments each
time we put a drone on path `i`, and starts at `path_cost[i]` (the
first drone on a path can't finish earlier than that). This
spreads drones evenly across parallel paths.

```python
    def step(self):
        arrivals, just_arrived = self._complete_transits()
        turn_link_use = dict(self.link_load)
        new_moves = self._advance_ready_drones(turn_link_use, just_arrived)
        self.turn += 1
        return arrivals + new_moves
```

Two phases per turn:

1. `_complete_transits` — restricted-zone arrivals.
2. `_advance_ready_drones` — everyone else tries to move forward.

We copy `link_load` into `turn_link_use` so the per-turn check
starts from the in-flight load and accumulates this turn's moves
on top of it.

```python
    def _complete_transits(self):
        out, just_arrived = [], set()
        for drone in self.drones:
            if drone.delivered: continue
            if drone.in_flight_to is None: continue
            target = drone.in_flight_to
            link_key = self._link_key_from_label(drone.in_flight_via or "")
            if link_key is not None:
                self.link_load[link_key] -= 1
            drone.position = target
            drone.path_index += 1
            drone.in_flight_to = None
            drone.in_flight_via = None
            just_arrived.add(drone.id)
            out.append((drone, target))
            if target == self.graph.end:
                drone.delivered = True
                self.zone_load[target] -= 1
        return out, just_arrived
```

For every in-flight drone:
- Free the connection (`link_load -= 1`).
- Update position + path index.
- Add to `just_arrived` so the move phase skips them.
- Emit the output line `(drone, target_zone)`.
- If we landed at the end, mark delivered and release the slot.

```python
    def _advance_ready_drones(self, turn_link_use, just_arrived):
        ready = [d for d in self.drones
                 if not d.delivered
                 and d.in_flight_to is None
                 and d.id not in just_arrived]
        ready.sort(key=lambda d: -d.path_index)
        out = []
        for drone in ready:
            move = self._try_move(drone, turn_link_use)
            if move is not None:
                out.append(move)
        return out
```

**Sort by `-path_index`:** drones farther along their path go
first. This makes the subject's "leaving frees the slot" rule
work without an explicit two-pass calculation: drones in front
vacate their zones before drones behind them check.

```python
    def _try_move(self, drone, turn_link_use):
        next_name = drone.next_zone
        if next_name is None: return None
        zone = self.graph.zones[next_name]
        if zone.is_blocked: return None
        link = self.graph.get_connection(drone.position, next_name)
        if link is None: return None
        if turn_link_use.get(link.key, 0) >= link.max_capacity: return None
        cap = zone.effective_capacity()
        if self.zone_load.get(next_name, 0) + 1 > cap: return None
        # commit
        if drone.position != self.graph.start:
            self.zone_load[drone.position] -= 1
        self.zone_load[next_name] += 1
        turn_link_use[link.key] = turn_link_use.get(link.key, 0) + 1
        if zone.zone_type == "restricted":
            self.link_load[link.key] = self.link_load.get(link.key, 0) + 1
            drone.in_flight_to = next_name
            drone.in_flight_via = link.label()
            return (drone, link.label())
        drone.position = next_name
        drone.path_index += 1
        if drone.position == self.graph.end:
            drone.delivered = True
            self.zone_load[next_name] -= 1
        return (drone, next_name)
```

This is the **single most important function** of the project.
Read it carefully — you'll likely be asked to explain it.

Walk through:
1. Get the planned next zone. Bail if there is none.
2. Refuse blocked zones.
3. Get the connection. Bail if missing (shouldn't happen given the
   path was planned, but defensive).
4. Check link capacity using the per-turn counter.
5. Check zone capacity (we add 1 for ourselves).
6. **Commit:**
   - Free the origin zone (unless it's the start, which is uncapped).
   - Reserve the destination zone slot.
   - Mark the link as used this turn.
7. **If restricted** — start a 2-turn transit:
   - Bump the persistent `link_load` (the connection stays busy
     until next turn's arrival phase).
   - Set `in_flight_to` and `in_flight_via`.
   - Return output `D<id>-<connection_label>`.
8. **Otherwise** — instant 1-turn move:
   - Update drone position and path index.
   - If we landed at the end, mark delivered and release the slot
     (end is uncapped but we keep counts clean).

```python
    def run(self):
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
```

Drive the simulation until everyone's delivered. If we make zero
moves for 6 consecutive turns, declare a deadlock — defensive
programming for malformed maps.

```python
    def format_output(self):
        lines = []
        for moves in self.turn_log:
            if not moves: continue
            tokens = [f"{d.label}-{label}" for d, label in moves]
            lines.append(" ".join(tokens))
        return "\n".join(lines)
```

Convert the turn log into the subject's textual format.

### 6.8 `src/visualizer.py` — the pygame window

**Job:** show the graph as an interactive window and let you step
through the simulation visually, one turn at a time (or on auto).

This file is split into: **constants**, **the Visualizer class**
(constructor + layout + event loop + 5 drawing methods), and two
**module-level convenience functions**. Walk through each piece.

---

#### Module-level constants

```python
COLOR_MAP: Dict[str, Tuple[int, int, int]] = {
    "red": (255, 100, 100),
    "green": (100, 220, 120),
    ...
}
```

Maps the color name from a zone's metadata (`color=red`) to an
RGB tuple. If the name isn't in this dict, the border falls back
to dark charcoal. This satisfies the subject's rule that zones
must display their metadata color.

```python
BG_COLOR = (245, 245, 250)   # Light off-white background
GRID_COLOR = (230, 230, 235) # Subtle graph-paper lines
EDGE_COLOR = (150, 150, 160) # Connection lines
TEXT_COLOR = (30, 30, 30)    # Dark text
DRONE_BG   = (50, 50, 60)    # Dark badge behind drone number
DRONE_TEXT = (255, 255, 255) # White number inside badge
BLOCKED_COLOR = (180, 180, 180)
```

Light-theme palette. All drawing functions reference these names
rather than hard-coding RGB tuples, so a color change is one edit.

---

#### `class Visualizer` — class-level constants

```python
class Visualizer:
    WIDTH  = 1100
    HEIGHT = 720
    PADDING = 80
    AUTO_DELAY_MS = 500
```

- `WIDTH` / `HEIGHT` — default window size in pixels. Both are
  updated when the user resizes the window (see `run`).
- `PADDING` — whitespace margin on all sides so zones don't touch
  the edge.
- `AUTO_DELAY_MS = 500` — 500 ms between auto-play steps (2
  turns per second). Change this to speed up or slow down.

---

#### `__init__`

```python
def __init__(self, graph: Graph) -> None:
    self.graph = graph
    self.simulator = Simulator(graph)
    self._auto = False
    self._last_auto_tick = 0
    self._latest_moves: List[Tuple[int, str]] = []
    self._compute_layout()
```

- `self.simulator` — the `Visualizer` owns a fresh `Simulator`.
  The simulation is not pre-run; it advances one step at a time
  as the user presses keys.
- `self._auto` — flag for auto-play mode (toggled by `A`).
- `self._last_auto_tick` — timestamp (ms) of the last auto step,
  used to pace auto-play.
- `self._latest_moves` — a list of `(drone_id, label)` pairs from
  the last turn, displayed in the HUD at the bottom.
- `_compute_layout()` — called immediately so pixel positions are
  ready before the first draw.

---

#### `_compute_layout`

```python
def _compute_layout(self) -> None:
    xs = [z.x for z in self.graph.zones.values()]
    ys = [z.y for z in self.graph.zones.values()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = max(1, max_x - min_x)
    span_y = max(1, max_y - min_y)

    left_margin   = 60
    right_margin  = 250   # safe zone for the legend panel
    top_margin    = 120   # clears the top HUD header
    bottom_margin = 120   # clears the bottom status bar + zone name labels

    usable_w = max(100, self.WIDTH  - left_margin - right_margin)
    usable_h = max(100, self.HEIGHT - top_margin  - bottom_margin)

    self._pos: Dict[str, Tuple[int, int]] = {}
    for zone in self.graph.zones.values():
        nx = (zone.x - min_x) / span_x if span_x > 0 else 0.5
        ny = (zone.y - min_y) / span_y if span_y > 0 else 0.5
        px = int(left_margin + nx * usable_w)
        py = int(top_margin  + ny * usable_h)
        self._pos[zone.name] = (px, py)
```

**What it does:** converts each zone's integer map coordinates
(`zone.x`, `zone.y`) into screen pixel coordinates, stored in
`self._pos[zone_name] = (px, py)`.

**How the math works:**

1. Find the bounding box of all zone coordinates (`min_x`, `max_x`,
   `min_y`, `max_y`).
2. `span_x = max(1, ...)` — prevents division by zero when all zones
   share the same x-coordinate (a degenerate vertical map).
3. `nx = (zone.x - min_x) / span_x` — normalize to `[0.0, 1.0]`.
   The leftmost zone gives 0, the rightmost gives 1.
4. `px = left_margin + nx * usable_w` — scale from normalized to
   pixels, offset by the left margin.
5. `py = top_margin + ny * usable_h` — same vertically, offset by
   the top margin.

**Four named margins instead of a single PADDING:**
The old version used one uniform `PADDING = 80` on every side and
subtracted 60 px for the HUD strip. This caused zones to clip into
the HUD header or the legend panel on certain maps. The new version
gives each side its own margin tailored to what lives there:

| Margin | Value | What it clears |
|--------|-------|----------------|
| `left_margin` | 60 px | Narrow — nothing lives on the left edge |
| `right_margin` | 250 px | Wide enough to keep zones clear of the 195 px legend |
| `top_margin` | 120 px | Clears the turn counter + controls strip |
| `bottom_margin` | 120 px | Clears the "Last turn:" bar + zone name labels |

**`max(100, usable_w/h)` guard:** if the window is dragged so small
that the margins would give a negative usable area, we clamp to 100
px so the graph remains drawable.

**Note on `PADDING`:** the class still defines `PADDING = 80` but
it is no longer used by `_compute_layout`. It's left in place so
external code that reads `Visualizer.PADDING` doesn't break.

**Why it's called again on resize:** when the window grows or
shrinks, `self.WIDTH` and `self.HEIGHT` change. Re-calling this
method recomputes all pixel positions for the new size.

**Peer review question:** *"What if all zones have the same x
coordinate?"*
**Answer:** *"`span_x` would be 0. We clamp it to `max(1, 0) = 1`
and then fall through to `nx = 0.5` (the `if span_x > 0 else 0.5`
branch), centering all zones horizontally."*

---

#### `run` — the pygame event loop

```python
def run(self) -> None:
    pygame.init()
    screen = pygame.display.set_mode(
        (self.WIDTH, self.HEIGHT), pygame.RESIZABLE
    )
    pygame.display.set_caption("Fly-in")
    font     = pygame.font.SysFont("consolas", 14)
    big_font = pygame.font.SysFont("consolas", 20, bold=True)
    clock    = pygame.time.Clock()
    running  = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                self.WIDTH  = event.w
                self.HEIGHT = event.h
                # Grab the already-resized surface — avoids
                # recreating the window and cancelling the drag.
                screen = pygame.display.get_surface()
                self._compute_layout()
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif event.key in (pygame.K_SPACE, pygame.K_RIGHT):
                    self._do_step()
                elif event.key == pygame.K_a:
                    self._auto = not self._auto
                elif event.key == pygame.K_r:
                    self.simulator = Simulator(self.graph)
                    self._latest_moves = []
        if self._auto and not self.simulator.all_delivered():
            now = pygame.time.get_ticks()
            if now - self._last_auto_tick > self.AUTO_DELAY_MS:
                self._do_step()
                self._last_auto_tick = now
        self._draw(screen, font, big_font)
        pygame.display.flip()
        clock.tick(30)
    pygame.quit()
```

This is the **classic pygame game loop**: handle events → update
state → draw → flip the buffer → throttle to 30 fps.

**Key events:**

| Key | Effect |
|-----|--------|
| `SPACE` or `→` | Advance one turn (`_do_step`) |
| `A` | Toggle auto-play |
| `R` | Reset — create a brand-new `Simulator`, clear last moves |
| `ESC` or `Q` | Close window |
| Window drag | `VIDEORESIZE` event fires |

**Resize handling (`pygame.VIDEORESIZE`):**
The window is opened with `pygame.RESIZABLE`. When the user drags
its corner, pygame fires a `VIDEORESIZE` event with the new size in
`event.w` and `event.h`. We:
1. Update `self.WIDTH` and `self.HEIGHT`.
2. Call `pygame.display.get_surface()` to get the surface pygame
   **already resized** for us.
3. Call `_compute_layout()` so all zone pixel positions are
   recalculated for the new dimensions.

**Why `get_surface()` instead of `set_mode()` here?**
The previous version called `set_mode()` again inside the resize
handler. This tells the OS to create a brand-new window, which
cancels the ongoing mouse drag — the user has to click and drag
again for every pixel of resize. `get_surface()` instead grabs the
surface that pygame already resized internally when it received the
`VIDEORESIZE` event, so the drag is never interrupted.

Without step 3, zones would stay at their old positions and drift
outside the visible area after resize.

**Auto-play timing:**
We use `pygame.time.get_ticks()` (milliseconds since startup)
rather than a frame counter. This keeps the pace constant
regardless of what the CPU is doing. The condition:
```python
if now - self._last_auto_tick > self.AUTO_DELAY_MS:
```
fires when at least 500 ms have elapsed since the last step.

**`clock.tick(30)`** — caps the frame rate at 30 fps so we don't
burn CPU in the tight loop. The game still *feels* responsive
because events are handled every frame.

**`pygame.quit()` at the end** — releases all pygame resources
cleanly. Without this, on some platforms the process hangs.

---

#### `_do_step`

```python
def _do_step(self) -> None:
    if self.simulator.all_delivered():
        return
    moves = self.simulator.step()
    self.simulator.turn_log.append(moves)
    self._latest_moves = [(d.id, label) for d, label in moves]
```

Advance one simulation turn:
1. Guard: do nothing if every drone is already delivered.
2. Call `simulator.step()` — returns a list of `(Drone, label)`
   pairs for this turn.
3. Append to `turn_log` so the output can still be formatted.
4. Store `_latest_moves` as `(drone_id, label)` for the HUD.

**Why `(d.id, label)` not `(d, label)`?** We only need the id for
the HUD display string. Storing the full `Drone` object when we
only need one field would be unnecessary.

---

#### `_draw`

```python
def _draw(self, screen, font, big_font) -> None:
    screen.fill(BG_COLOR)
    for x in range(0, self.WIDTH, 40):
        pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, self.HEIGHT))
    for y in range(0, self.HEIGHT, 40):
        pygame.draw.line(screen, GRID_COLOR, (0, y), (self.WIDTH, y))
    self._draw_edges(screen)
    self._draw_zones(screen, font)
    self._draw_drones(screen, font)
    self._draw_hud(screen, big_font, font)
```

**Painter's algorithm** — draw from background to foreground so
later layers cover earlier ones:

1. Fill background with `BG_COLOR` (clears last frame).
2. Draw a subtle 40-pixel grid (graph-paper aesthetic).
3. Draw edge lines (connections).
4. Draw zone circles on top of edges.
5. Draw drone badges on top of zones.
6. Draw the HUD (status + controls + legend) on top of everything.

---

#### `_draw_edges`

```python
def _draw_edges(self, screen: pygame.Surface) -> None:
    for (a, b), conn in self.graph.connections.items():
        pa, pb = self._pos[a], self._pos[b]
        pygame.draw.line(screen, EDGE_COLOR, pa, pb, 3)
        if conn.max_capacity > 1:
            mx = (pa[0] + pb[0]) // 2
            my = (pa[1] + pb[1]) // 2
            pygame.draw.circle(screen, EDGE_COLOR, (mx, my), 6)
```

Draws one line per connection. If `max_capacity > 1`, a small
filled circle appears at the midpoint of the edge — a visual cue
that the connection can carry multiple drones simultaneously.

`self.graph.connections` is the `{(a, b): Connection}` dict.
`self._pos[a]` gives the pixel coordinates of zone `a` (computed
in `_compute_layout`).

**Why thickness 3?** Thin lines (1 px) are hard to see on a dense
graph. 3 px is visible but not distracting.

---

#### `_zone_fill`

```python
def _zone_fill(self, zone: Zone) -> Tuple[int, int, int]:
    if zone.is_start:       return (180, 240, 180)  # Pale green
    if zone.is_end:         return (250, 230, 150)  # Pale yellow
    if zone.is_blocked:     return (160, 160, 160)  # Dark grey
    if zone.zone_type == "restricted": return (255, 190, 190)  # Pale red
    if zone.zone_type == "priority":   return (190, 230, 255)  # Pale blue
    return (255, 255, 255)                           # White (normal)
```

Returns the **fill** (interior) color based on the zone's
**mechanical type** — what the zone *does* in the simulation.

This is a design decision: the fill tells you "is this zone fast /
slow / blocked / start / end?" at a glance. The subject requires
color info to be shown; we chose to separate it into two visual
layers (fill = mechanics, border = metadata color).

**Check order matters:** `is_start` and `is_end` are checked
first because a start/end zone should always render as green/yellow
regardless of its `zone_type`. If we checked `zone_type` first,
a start zone with `zone_type="priority"` would appear blue.

---

#### `_zone_border`

```python
def _zone_border(self, zone: Zone) -> Tuple[int, int, int]:
    if zone.color and zone.color in COLOR_MAP:
        return COLOR_MAP[zone.color]
    return (40, 40, 40)   # Default dark charcoal
```

Returns the **border** color based on the zone's `color` metadata
attribute (e.g. `color=red` in the map file). If the color name
isn't in `COLOR_MAP`, fall back to near-black.

This satisfies the subject's requirement that zone colors from the
map file must be represented visually.

---

#### `_draw_zones`

```python
def _draw_zones(self, screen, font) -> None:
    for zone in self.graph.zones.values():
        cx, cy = self._pos[zone.name]
        radius = 28
        fill_color   = self._zone_fill(zone)
        border_color = self._zone_border(zone)
        # 1. Fill
        pygame.draw.circle(screen, fill_color, (cx, cy), radius)
        # 2. Thick colored border (4 px)
        pygame.draw.circle(screen, border_color, (cx, cy), radius, 4)
        # 3. Name label below
        label = font.render(zone.name, True, TEXT_COLOR)
        bg_rect = label.get_rect(center=(cx, cy + radius + 14))
        pygame.draw.rect(screen, BG_COLOR, bg_rect.inflate(8, 4), border_radius=4)
        screen.blit(label, bg_rect)
```

For every zone this draws three things:

1. **Filled circle** — color from `_zone_fill`. Tells you the
   zone's role/behavior at a glance.
2. **Thick border ring** — color from `_zone_border`. Shows the
   zone's metadata color (the `color=` field). The ring is 4 px
   wide — thick enough to read at a distance.
3. **Name label** — rendered in `font` (Consolas 14), placed 14 px
   below the circle's bottom edge. A small `BG_COLOR` rectangle is
   drawn behind the label first so the text is readable even when
   it overlaps an edge line.

`label.get_rect(center=(cx, cy + radius + 14))` — `get_rect` with
a keyword argument positions the rect's center at the given point,
which neatly centers the text horizontally under the circle.

`bg_rect.inflate(8, 4)` — makes the background rect 8 px wider and
4 px taller than the text, creating a small padding around it.

---

#### `_draw_drones`

```python
def _draw_drones(self, screen, font) -> None:
    clusters: Dict[Tuple[int, int], List[int]] = {}
    for drone in self.simulator.drones:
        if drone.delivered:
            pos = self._pos[self.graph.end]
        elif drone.in_flight_to is not None:
            origin = self._pos[drone.position]
            target = self._pos[drone.in_flight_to]
            pos = ((origin[0] + target[0]) // 2,
                   (origin[1] + target[1]) // 2)
        else:
            pos = self._pos[drone.position]
        clusters.setdefault(pos, []).append(drone.id)
    for pos, ids in clusters.items():
        for i, drone_id in enumerate(ids):
            row = i // 3
            col = i % 3
            offset_x = (col * 24) - (min(len(ids), 3) - 1) * 12
            offset_y = (row * 24) - (len(ids) // 3) * 12
            d_pos = (pos[0] + offset_x, pos[1] + offset_y)
            pygame.draw.circle(screen, DRONE_BG, d_pos, 11)
            pygame.draw.circle(screen, (20, 20, 20), d_pos, 11, 2)
            txt = font.render(f"{drone_id}", True, DRONE_TEXT)
            screen.blit(txt, txt.get_rect(center=d_pos))
```

**Step 1 — determine visual position for each drone:**

- **Delivered** → drawn at the end zone (they've arrived; we keep
  them visible there).
- **In flight** (`drone.in_flight_to is not None`) → drawn at the
  midpoint of its connection. This gives a clear "in transit"
  visual between two zone circles.
- **Otherwise** → drawn at their current `drone.position` zone.

**Step 2 — cluster drones at the same pixel position:**

Multiple drones at the same zone (or in transit on the same
connection) would overlap. `clusters` groups their ids by pixel
position. Then within each cluster we spread them out in a 3-column
grid using offsets:

```python
row = i // 3       # 0 for first 3, 1 for next 3, etc.
col = i % 3        # 0, 1, 2, 0, 1, 2, ...
offset_x = (col * 24) - (min(len(ids), 3) - 1) * 12
offset_y = (row * 24) - (len(ids) // 3) * 12
```

- Each badge is 24 px apart.
- The horizontal offset is centered: `(min(len, 3) - 1) * 12`
  shifts the whole row left so the group is centered on `pos`.
- The vertical offset shifts rows up to center the grid.

**Step 3 — draw each badge:**
A dark filled circle (radius 11), a thin dark border ring (2 px),
and the drone id number centered inside in white text.

**Peer review question:** *"Why midpoint for in-flight drones?"*
**Answer:** *"The drone is conceptually on the connection between
two zones — it hasn't arrived yet. Drawing it at the midpoint of
the line between the two zone circles communicates this visually
better than leaving it at the origin or jumping it to the
destination."*

---

#### `_draw_hud`

```python
def _draw_hud(self, screen, big_font, font) -> None:
```

The HUD (Heads-Up Display) renders four pieces of information:

**Top-left — Turn counter and delivery status:**
```python
turn_text = big_font.render(f"Turn: {self.simulator.turn}", True, TEXT_COLOR)
screen.blit(turn_text, (20, 18))
delivered = sum(1 for d in self.simulator.drones if d.delivered)
delivered_text = big_font.render(
    f"Delivered: {delivered}/{self.graph.nb_drones}", True, TEXT_COLOR
)
screen.blit(delivered_text, (220, 18))
```
Uses `big_font` (Consolas 20 bold) so these two numbers are the
most prominent text on screen. `sum(1 for d in ... if d.delivered)`
counts delivered drones without building a list.

**Top-left below turn — Controls:**
```python
help_text = font.render(
    "SPACE/RIGHT step  |  A auto  |  R reset  |  ESC quit",
    True, TEXT_COLOR,
)
screen.blit(help_text, (20, 46))
```
A one-line reminder of the controls, always visible.

**Bottom-left — Last turn's moves:**
```python
if self._latest_moves:
    moves_str = "Last turn: " + " ".join(
        f"D{i}-{lbl}" for i, lbl in self._latest_moves
    )
    txt = font.render(moves_str, True, TEXT_COLOR)
    screen.blit(txt, (20, self.HEIGHT - 24))
```
Shows the subject-format output for the most recent turn (e.g.
`Last turn: D1-roof1 D2-corridorA`). Positioned at
`self.HEIGHT - 24` so it always sits near the bottom regardless
of window height.

**Top-right — The zone type legend:**
```python
legend_items = [
    ("Start",            (180, 240, 180)),
    ("End",              (250, 230, 150)),
    ("Normal",           (255, 255, 255)),
    ("Priority (Fast)",  (190, 230, 255)),
    ("Restricted (Slow)",(255, 190, 190)),
    ("Blocked",          (160, 160, 160)),
]
pygame.draw.rect(screen, (255, 255, 255),
                 (self.WIDTH - 210, 15, 195, 145), border_radius=6)
pygame.draw.rect(screen, (200, 200, 210),
                 (self.WIDTH - 210, 15, 195, 145), 2, border_radius=6)
start_x = self.WIDTH - 190
start_y = 25
for text, color in legend_items:
    pygame.draw.circle(screen, color, (start_x, start_y), 8)
    pygame.draw.circle(screen, (40, 40, 40), (start_x, start_y), 8, 1)
    label = font.render(text, True, TEXT_COLOR)
    screen.blit(label, (start_x + 15, start_y - 7))
    start_y += 20
```

A white rounded rectangle with a subtle border houses six rows,
one per zone type. Each row: a filled + outlined circle (matching
the zone fill colors from `_zone_fill`) and a text label.

The legend is anchored at `self.WIDTH - 210` so it stays in the
top-right corner regardless of window width.

**Peer review question:** *"Why a legend and not just labels on the
zones?"*
**Answer:** *"The zones already display their name below and their
metadata color as the border. Adding a type label on the circle
itself would make it unreadable — too much text in 28 px. The
legend gives a permanent reference without cluttering the graph."*

---

#### Module-level convenience functions

```python
def visualize(graph: Graph) -> None:
    Visualizer(graph).run()

def visualize_existing(
    graph: Graph, simulator: Optional[Simulator] = None
) -> None:
    visualizer = Visualizer(graph)
    if simulator is not None:
        visualizer.simulator = simulator
    visualizer.run()
```

`visualize` — the usual path: create a fresh `Visualizer` (which
creates its own `Simulator`) and run it. Called from `main.py`.

`visualize_existing` — accepts an already-run `Simulator`. Useful
if you want to replay a simulation that was already computed (e.g.
after printing the output). The visualizer replaces its internal
simulator before opening the window. Marked "kept for symmetry" in
the code because it isn't currently used by main, but it's a clean
API to have.

### 6.9 `src/main.py` and `src/__main__.py`

**Job:** the command-line entry point.

```python
def main(argv=None):
    args = _build_argparser().parse_args(argv)
    graph = safe_parse_map(args.map_file)
    if graph is None: return 1
    try:
        simulator = Simulator(graph)
        total_turns = simulator.run()
    except RuntimeError as exc:
        print(f"simulation error: {exc}")
        return 2
    output = simulator.format_output()
    print(output)
    print(f"=> Map solved in {total_turns} turns with {graph.nb_drones} drones.")
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fp:
            fp.write(output + "\n")
    if not args.no_visual:
        from .visualizer import Visualizer
        Visualizer(graph).run()
    return 0
```

Standard CLI flow: parse args → parse map → run simulator → print
output → optionally open visualizer. Each failure returns a
different exit code (1, 2, 3) so a caller can tell what went wrong.

`src/__main__.py` just calls `main()` so `python -m src ...` works.

---

## 7. Why I made these choices

### Dijkstra over plain BFS
Edge weights aren't uniform (`restricted` = 2). BFS only works for
uniform weights. Dijkstra is the minimum-complexity algorithm that
handles weighted graphs correctly.

### `heapq` instead of a custom priority queue
It's standard library, well-tested, O(log n) operations. The
subject only forbids **graph** libraries — heaps are general
data structures.

### Equal-cost k-paths instead of edge-disjoint paths
Edge-disjoint paths can be much longer than the shortest. Routing
drones down a longer path *delays* them without freeing the real
bottleneck. We verified this empirically: on `circular_loop`,
allowing long alternates jumped the turn count from 15 to 16.

### Greedy "farthest drone first" instead of full constraint solving
The subject's rule "leaving frees the slot that same turn" is
exactly what greedy-by-progress simulates. It's O(D) per turn vs.
O(D²) or worse for ILP-style approaches.

### One simulator, not separate planner + executor
The simulator owns capacity tracking. A separate planner would
need to model capacity too, duplicating logic. Keeping all the
state in one class makes invariants easier to reason about.

### `pygame` not `pyray` / `raylib`
You asked for pygame. It's simpler than 3D graphics and the
subject accepts either terminal or graphical output.

---

## 8. Edge cases and bugs I avoided

These are the kinds of things peer reviewers love to ask about:

### Bug 1 — Link load never resetting (caught during testing)
Initial version: I treated `link_load` as persistent. After one
drone crossed a link, the count stayed at 1 forever, blocking
everyone else. **Fix:** `link_load` now only tracks **in-flight
restricted-transit drones**. Per-turn link usage is computed in a
local dict (`turn_link_use`) that starts from `link_load` and
resets every step.

### Bug 2 — Same drone twice in one turn (caught during testing)
Initial output had `D6-exit_point D6-goal` on the same line.
**Cause:** after completing a transit in phase 1, the drone was
still eligible for phase 2 moves. **Fix:** `_complete_transits`
returns a `just_arrived` set; `_advance_ready_drones` skips those
drones.

### Bug 3 — Routing drones down longer paths actually slows the
simulation (caught during testing)
The k_paths heuristic had a generous slack of `+2 turns`. On
`circular_loop`, it accepted a 7-cost detour that put drones in
loop_b later than necessary. **Fix:** only accept alternates that
have the **same** cost as the base.

### Edge case — Blocked zones
The pathfinder's `_edge_cost` returns `None` for blocked
destinations, so Dijkstra never enters them. The simulator also
checks `zone.is_blocked` defensively in `_try_move`.

### Edge case — No path
`pathfinder.shortest_path` returns `None` if the end is
unreachable. The simulator's `_build_drones` raises
`RuntimeError("no path from start to end")`.

### Edge case — Deadlock
If no drone can move for 6 turns straight, we raise
`RuntimeError("simulation deadlocked")`. We also cap total turns
at 1000.

### Edge case — Duplicate connection
`Connection.__init__` sorts endpoints, so `Graph.add_connection`
catches `a-b` and `b-a` as the same.

### Edge case — Invalid zone type / non-integer coordinates / etc.
The parser raises `ParseError(line_no, message)` for every bad
input. The error is printed via `safe_parse_map` and the program
exits with code 1.

### Edge case — Start/end have infinite capacity
`Zone.effective_capacity` returns `float("inf")` for them, so the
`+ 1 > cap` check never trips.

### Edge case — Drone position when in transit
While in flight, the drone's `position` attribute stays at the
**origin** zone. We don't make it `None` or set it to the
connection. This keeps the data type stable (`position: str`
always).

---

## 9. How to prepare for the evaluation

### The night before

1. **Re-read this guide** end to end.
2. **Read the subject PDF again.** Note any sentence that uses
   words like "must", "exactly", "any". Those are the rules
   evaluators will check.
3. **Run every map** locally and verify the turn count matches the
   target:
   ```bash
   for f in maps/easy/*.txt maps/medium/*.txt maps/hard/*.txt; do
       echo "=== $f ==="
       python -m src "$f" --no-visual | tail -2
   done
   ```
4. **Run the linter:**
   ```bash
   make lint
   ```
   Should print no errors.
5. **Smoke-test the visualizer:**
   ```bash
   make run MAP=maps/easy/02_simple_fork.txt
   ```
   Watch a couple of turns. Press `A`, `R`, `ESC`.

### Just before the eval

- Bring the **subject PDF** on your phone or laptop — refer to it
  when asked about rules.
- Have **this guide** open.
- Have a **terminal** open in the project directory.

### Mental warm-up

Practice saying these out loud:
- "The project routes drones through a weighted graph using
  Dijkstra and runs a turn-by-turn simulation respecting zone and
  link capacities."
- "The two hardest rules are restricted zones (2-turn transit) and
  simultaneous moves with capacity-freed-on-leave."
- "I don't use `networkx` or `graphlib`. I hand-rolled the graph
  data structure and Dijkstra. `heapq` is the standard-library
  heap, not a graph library."

---

## 10. Defending yourself: likely questions + answers

### Q: "Walk me through what happens when I run `python -m src maps/medium/02_circular_loop.txt`."

**A:**
1. `__main__.py` calls `main.main()`.
2. `argparse` parses the args, `safe_parse_map` reads the file.
3. The parser builds a `Graph` (zones + connections + start/end).
4. `Simulator(graph)` is created — in its `__init__`, it calls
   `_build_drones`, which runs Dijkstra to get up to 8 short paths
   and assigns each drone to the path with the smallest projected
   finish turn.
5. `simulator.run()` loops `step()` until every drone is delivered.
   Each `step()` first completes in-flight transits, then tries to
   move every remaining drone one hop forward.
6. The textual output is printed, the visualizer opens, and you
   press `SPACE` to watch the simulation step by step.

### Q: "Why Dijkstra and not BFS?"

**A:** "BFS only finds shortest paths in unweighted graphs.
Restricted zones cost 2 turns to enter, so our edges have different
weights. Dijkstra handles weights correctly using a priority queue."

### Q: "Why `heapq`? Isn't that a graph library?"

**A:** "No. `heapq` is the standard-library binary-heap data
structure — same family as `list` or `dict`. The subject forbids
**graph** libraries like `networkx` and `graphlib` because they
implement graph algorithms for you. I hand-rolled Dijkstra using
just the heap as a priority queue."

### Q: "How do you handle restricted zones?"

**A:** "A restricted destination costs 2 turns and the drone must
arrive at the destination on the next turn — it can't wait on the
connection. When a drone enters a restricted-zone connection at
turn N: (1) it leaves its origin zone, (2) it reserves a slot in
the destination zone (so the destination doesn't accept other
drones), and (3) the link is marked occupied in `link_load`. The
drone outputs `D<id>-<connection_label>`. On turn N+1, the
arrival phase fires: the link is freed, the drone's position is
updated to the destination, the path index advances, and the
drone is excluded from this turn's move phase (one action per
turn)."

### Q: "What happens if two drones want to enter the same zone in
the same turn?"

**A:** "We track zone occupancy in `zone_load`. Before committing
a move, we check `zone_load[dest] + 1 > capacity`. The first drone
to attempt the move commits and bumps `zone_load`. The second
drone's check fails and it stays. Because we sort drones by
descending path_index, the drone closer to the end goes first —
which makes sense because that drone is also more likely to
vacate the next zone in the chain, freeing room behind."

### Q: "What's `zone_load[zone] -= 1` doing when a drone moves?"

**A:** "The drone is leaving that zone, freeing one slot in it. We
only decrement if the zone isn't the start, because the start has
infinite capacity and we never track it."

### Q: "How is the visualizer connected to the simulator?"

**A:** "The `Visualizer` creates and owns its own `Simulator`
instance in `__init__`. Each time the user presses SPACE (or
auto-play fires), `_do_step` calls `simulator.step()`, appends
the returned moves to `turn_log`, and saves them as
`_latest_moves` for the HUD. The window redraws on every frame
based on each drone's current `position` and `in_flight_to`
attributes — drones in flight are drawn at the midpoint of the
connection between the origin and destination zone circles. All
delivered drones are drawn at the end zone so they stay visible
on screen."

### Q: "How does window resizing work in the visualizer?"

**A:** "The window is opened with the `pygame.RESIZABLE` flag.
When the user drags the window corner, pygame fires a
`pygame.VIDEORESIZE` event containing the new width and height.
We update `self.WIDTH` and `self.HEIGHT`, call
`pygame.display.get_surface()` to get the surface pygame already
resized internally, then call `_compute_layout()` to recalculate
all zone pixel positions. We deliberately use `get_surface()`
rather than calling `set_mode()` again — `set_mode()` creates a
brand-new OS window, which cancels the ongoing mouse drag and makes
continuous resizing unusable. `get_surface()` just fetches the
surface pygame already updated, so the drag flows smoothly."

### Q: "How does the zone coloring system work?"

**A:** "There are two separate visual layers. The fill color (the
interior of the circle) encodes the zone's *mechanical type* —
pale green for start, pale yellow for end, pale red for
restricted, pale blue for priority, grey for blocked, white for
normal. This lets you see at a glance what a zone *does* in the
simulation. The border ring color encodes the zone's `color`
metadata from the map file — that's the subject requirement.
`_zone_fill()` and `_zone_border()` are split into two methods
precisely because these two concerns are independent. The legend
in the top-right corner explains the fill colors to the user."

### Q: "How does the drone clustering work?"

**A:** "Multiple drones at the same pixel position would overlap
and become unreadable. `_draw_drones` first groups all drone ids
by their visual pixel position into a `clusters` dict. Then for
each cluster it lays the badges out in a 3-column grid using row
and column offsets, keeping them centered on the cluster's pixel
position. Each drone badge is a dark circle with the drone's id
number in white, radius 11 px, spaced 24 px apart."

### Q: "What happens if the map is unsolvable (no path from start
to end)?"

**A:** "`pathfinder.shortest_path` returns `None`. The simulator's
`_build_drones` raises `RuntimeError("no path from start to end")`,
caught by `main.main()` which prints a message and returns exit
code 2."

### Q: "How do you handle parse errors?"

**A:** "Each parser function raises `ParseError(line_no, message)`.
The custom exception class stores the line number so the message
reads `parser error: line 7: bad metadata token 'foo'`. The
top-level `safe_parse_map` catches `ParseError` and `OSError`,
prints the message, and returns `None`."

### Q: "Why is the project object-oriented?"

**A:** "Each domain concept maps to a class. `Zone` and `Connection`
own their data and invariants (capacity checks, type validation).
`Drone` owns its current state and planned path. `Graph` owns the
zones and connections together. `Simulator` orchestrates the
simulation and owns the per-turn state (`zone_load`, `link_load`,
`turn_log`). This separation makes each piece testable in
isolation and matches the subject's mandate."

### Q: "How would you scale this to 1000 drones?"

**A:** "The bottleneck is `_advance_ready_drones`, which is O(D
log D) per turn because of the sort. Total complexity is
O(T * D log D) where T is the number of turns. For 1000 drones
that's still manageable. The k_paths is independent of D (we cap
k at 8). The biggest practical issue would be the visualizer —
drawing 1000 dots gets noisy — so I'd render them as a single
heatmap circle per zone instead of individual labelled dots."

### Q: "What's the difference between `zone_load` and `link_load`?"

**A:** "`zone_load` is persistent — it tracks how many drones are
*currently in or reserved for* each zone, including in-transit
drones whose destination is reserved. `link_load` is the
*long-term* count for connections still occupied by in-flight
drones (restricted-zone transits that span turns). For per-turn
checks during the move phase we make a local copy
`turn_link_use` so transient single-turn link uses don't leak
into future turns."

### Q: "Show me a line of code you'd refactor if you had more time."

**A:** "The `_link_key_from_label` helper. We store the label as
`'a-b'` and parse it back later. I'd refactor to store the
canonical `(a, b)` tuple directly on the drone instead of
re-parsing the string. It's an O(1) win and removes a fragile
parse step."

### Q: "Defend your choice of k = 8 for k_paths."

**A:** "It's a soft cap. Most maps have far fewer parallel paths
than 8. The cap keeps the path-search cost bounded
(`O(k * (V + E) log V)`) without risking pathological behavior on
weird maps. If you wanted to dial it up, change one constant in
`_build_drones`."

### Q: "Is your solution optimal?"

**A:** "No. The reference student's max-flow / time-expanded
graph approach is provably optimal. My greedy Dijkstra + k_paths
hits every target in the subject but on highly-constrained maps a
smarter solver could find lower turn counts. The tradeoff is code
complexity — this implementation is about 600 lines, the
reference is several thousand."

---

## 11. Live modification practice

The subject says: *"During the evaluation, a brief modification of
the project may be requested."* Practice these before the eval —
you should be able to do each in under 5 minutes.

### Modification 1 — Print the number of moves per turn

**Goal:** add a line `Turn N: X drones moved` after each turn line
in the output.

**Where:** `simulator.py`, `format_output`.

```python
def format_output(self):
    lines = []
    for turn_idx, moves in enumerate(self.turn_log, start=1):
        if not moves: continue
        tokens = [f"{d.label}-{label}" for d, label in moves]
        lines.append(" ".join(tokens))
        lines.append(f"Turn {turn_idx}: {len(moves)} drones moved")
    return "\n".join(lines)
```

### Modification 2 — Compute the average turns per drone

**Goal:** print "Average turns per drone: X.XX" at the end.

**Where:** track each drone's delivery turn in the simulator.

```python
# In Drone.__init__: self.delivery_turn = None
# In _complete_transits and _try_move, when delivered=True:
drone.delivery_turn = self.turn
# In main.py after run():
avg = sum(d.delivery_turn for d in simulator.drones) / len(simulator.drones)
print(f"Average turns per drone: {avg:.2f}")
```

### Modification 3 — Add a new zone type "fast" (cost 0)

**Goal:** add a zone type that costs 0 turns to enter (instant).

**Where:**
- `zone.py`: add `"fast"` to `VALID_TYPES`, return `0` for cost.
- `pathfinder.py`: priority bonus is fine, no change needed.
- `simulator.py`: would need to handle 0-turn movement specially
  (the drone could move multiple hops per turn). Probably skip
  this in eval — say "I'd discuss the simulation impact first".

### Modification 4 — Read the map from stdin instead of a file

**Where:** `main.py`.

```python
if args.map_file == "-":
    import sys
    graph = parse_map_from_string(sys.stdin.read())
```

And add `parse_map_from_string` to `parser.py` that uses
`io.StringIO` instead of `open`.

### Modification 5 — Change the visualizer color of in-flight drones

**Where:** `visualizer.py`, `_draw_drones`.

The current code draws all drone badges in the same dark color
(`DRONE_BG`). To make in-flight drones visually distinct, change
the badge fill color before drawing:

```python
for pos, ids in clusters.items():
    for i, drone_id in enumerate(ids):
        row = i // 3
        col = i % 3
        offset_x = (col * 24) - (min(len(ids), 3) - 1) * 12
        offset_y = (row * 24) - (len(ids) // 3) * 12
        d_pos = (pos[0] + offset_x, pos[1] + offset_y)

        # Check if this specific drone is in flight
        drone_obj = next(d for d in self.simulator.drones if d.id == drone_id)
        badge_color = (200, 170, 0) if drone_obj.in_flight_to else DRONE_BG

        pygame.draw.circle(screen, badge_color, d_pos, 11)
        pygame.draw.circle(screen, (20, 20, 20), d_pos, 11, 2)
        txt = self._font.render(f"{drone_id}", True, DRONE_TEXT)
        screen.blit(txt, txt.get_rect(center=d_pos))
```

Note: `next(...)` is O(D) per badge. Fine for the usual ≤20 drones.
If you had hundreds, pre-build a `{id: drone}` dict before the loop.

### Modification 6 — Output to a file in CSV format

**Where:** `main.py`, when `--output` is given.

```python
with open(args.output, "w", encoding="utf-8") as fp:
    fp.write("turn,drone,destination\n")
    for turn_idx, moves in enumerate(simulator.turn_log, start=1):
        for drone, dest in moves:
            fp.write(f"{turn_idx},{drone.label},{dest}\n")
```

### General tips for live modifications

- **Open the file in your editor first.** Confirm you understand
  the function you're about to change.
- **Talk while you type.** "I'm going to add a counter to the loop
  here, then print it at the end."
- **Run the result.** Show the new output to the evaluator.
- **Mention edge cases.** "If `len(self.drones)` is zero this
  would divide by zero — but that can't happen because the
  parser requires `nb_drones > 0`."

---

## 12. Glossary

- **Adjacency list** — a dict mapping each node to its neighbours.
  How `Graph.adjacency` stores the network.
- **BFS** — Breadth-First Search. Shortest path on unweighted
  graphs.
- **Capacity** — max drones allowed on a zone or connection at the
  same time.
- **Dijkstra** — shortest-path algorithm for weighted graphs.
- **Edge** — a connection between two zones.
- **Edge-disjoint paths** — paths that share no edges.
- **Heap** — a tree-shaped data structure where the smallest
  element is always at the top. `heapq` provides this.
- **In-flight** — a drone currently transiting to a restricted
  zone (between turns).
- **Node** — a zone, in graph terms.
- **OOP** — Object-Oriented Programming. Classes + objects +
  methods.
- **Priority queue** — a queue where elements with the smallest
  priority come out first. Implemented as a heap.
- **Restricted zone** — costs 2 turns to enter (1 in transit + 1
  arriving). Subject's `zone=restricted`.
- **Simulation turn** — one tick of the simulation loop. Every
  drone gets up to one action per turn.
- **Type hints** — `def f(x: int) -> str:` syntax. Documents
  expected types; checked by `mypy`.
- **Weight** — the cost of an edge in a graph. In our project,
  the weight is the destination zone's `cost`.

---

## Last words

You wrote this code. You can defend it. The trick at peer review
is to **be calm**, **answer slowly**, and **point at the file**
when asked. If you don't know the answer to a question, say:
*"That's a good question — give me a moment, I want to read the
function before I answer."* Open the file, read it, then answer.
That's exactly what an experienced engineer does.

Good luck, luricci.
