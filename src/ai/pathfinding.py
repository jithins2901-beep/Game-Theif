"""A* pathfinding on the tile grid.

What is A*?
-----------
A* is a best-first search algorithm. It finds the shortest path between
two tiles by exploring tiles in order of  f = g + h  where:

  g = actual cost from the start tile to this tile (steps taken so far)
  h = heuristic estimate of cost from this tile to the goal
      (we use Manhattan distance — always admissible on a 4-dir grid)
  f = total estimated cost of the cheapest path through this tile

Because h never over-estimates, A* is guaranteed to find the shortest
path. It is faster than plain BFS/Dijkstra because h steers the search
toward the goal instead of expanding in all directions equally.

Implementation details
----------------------
- 4-directional movement (up/down/left/right). No diagonals — cleaner
  for a grid game and easier to explain.
- Uses a min-heap (heapq) as the open set for O(log n) pop.
- Returns a list of (col, row) tile positions from start to goal,
  NOT including the start tile itself.
- Returns an empty list if no path exists (goal is unreachable).
"""

import heapq
from src.core.grid import Grid


def find_path(
    grid: Grid,
    start: tuple[int, int],
    goal: tuple[int, int],
) -> list[tuple[int, int]]:
    """Find the shortest walkable path from start to goal using A*.

    Parameters
    ----------
    grid  : the level grid (used for wall checks)
    start : (col, row) starting tile
    goal  : (col, row) destination tile

    Returns
    -------
    List of (col, row) tiles from start (exclusive) to goal (inclusive).
    Empty list if start == goal or no path exists.
    """
    if start == goal:
        return []

    # If either endpoint is a wall, bail out immediately
    if grid.is_wall(*start) or grid.is_wall(*goal):
        return []

    # --- Open set: min-heap of (f, g, (col, row)) ---
    open_heap: list[tuple[int, int, tuple[int, int]]] = []
    heapq.heappush(open_heap, (0, 0, start))

    # came_from: maps each visited tile to its predecessor
    came_from: dict[tuple[int, int], tuple[int, int] | None] = {start: None}

    # g_cost: cheapest known cost to reach each tile
    g_cost: dict[tuple[int, int], int] = {start: 0}

    # 4-directional neighbours
    _DIRS = [(0, -1), (0, 1), (-1, 0), (1, 0)]

    while open_heap:
        _f, g, current = heapq.heappop(open_heap)

        if current == goal:
            return _reconstruct(came_from, goal)

        for dc, dr in _DIRS:
            neighbour = (current[0] + dc, current[1] + dr)

            if grid.is_wall(*neighbour):
                continue

            tentative_g = g + 1  # every step costs 1

            if tentative_g < g_cost.get(neighbour, float("inf")):
                g_cost[neighbour] = tentative_g
                came_from[neighbour] = current
                h = _manhattan(neighbour, goal)
                f = tentative_g + h
                heapq.heappush(open_heap, (f, tentative_g, neighbour))

    return []  # no path found


def _manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
    """Manhattan distance heuristic — admissible for 4-dir grid movement."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _reconstruct(
    came_from: dict[tuple[int, int], tuple[int, int] | None],
    goal: tuple[int, int],
) -> list[tuple[int, int]]:
    """Walk the came_from chain backwards to build the path."""
    path: list[tuple[int, int]] = []
    node: tuple[int, int] | None = goal
    while node is not None:
        path.append(node)
        node = came_from[node]
    path.reverse()
    # Drop the start tile (index 0) — the guard is already there
    return path[1:]
