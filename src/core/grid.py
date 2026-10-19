"""Grid: the data model for the game world.

Tile types
----------
FLOOR      (0) — walkable, transparent to sight
WALL       (1) — blocks movement AND sight
EXIT       (2) — walkable, transparent to sight (goal tile)
DOOR       (3) — state-dependent: closed=blocks both, open=blocks neither
FURNITURE  (4) — blocks movement, does NOT block sight
               (player crouching near furniture gets reduced detection)

Design note: the two critical queries used throughout the codebase are
  blocks_movement(col, row)  — used by player collision + A*
  blocks_sight(col, row)     — used by vision raycasting

Doors change both flags at once when toggled.
Furniture changes only movement.
"""

# Tile type constants
FLOOR     = 0
WALL      = 1
EXIT      = 2
DOOR      = 3
FURNITURE = 4


class Grid:
    """Holds the tile data and door states; exposes helpers for AI and physics."""

    def __init__(self, tiles: list[list[int]]) -> None:
        self.tiles = tiles
        self.rows  = len(tiles)
        self.cols  = len(tiles[0]) if tiles else 0

        # Door open/closed state: maps (col, row) → bool (True = open)
        # Populated by build_level; toggled by player interaction.
        self.door_open: dict[tuple[int, int], bool] = {}

    # ------------------------------------------------------------------
    # Raw tile access
    # ------------------------------------------------------------------

    def get(self, col: int, row: int) -> int:
        """Return tile type, WALL for out-of-bounds."""
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.tiles[row][col]
        return WALL

    # ------------------------------------------------------------------
    # The two canonical queries used by all subsystems
    # ------------------------------------------------------------------

    def blocks_movement(self, col: int, row: int) -> bool:
        """True if no entity can walk through this tile."""
        t = self.get(col, row)
        if t == WALL:
            return True
        if t == FURNITURE:
            return True
        if t == DOOR:
            return not self.door_open.get((col, row), False)
        return False

    def blocks_sight(self, col: int, row: int) -> bool:
        """True if vision rays cannot pass through this tile."""
        t = self.get(col, row)
        if t == WALL:
            return True
        if t == DOOR:
            return not self.door_open.get((col, row), False)
        # FURNITURE does NOT block sight — player can be seen over a desk
        return False

    # ------------------------------------------------------------------
    # Legacy helpers (keep for backward-compat — redirect to new queries)
    # ------------------------------------------------------------------

    def is_wall(self, col: int, row: int) -> bool:
        """Alias for blocks_movement (used by A* and old collision code)."""
        return self.blocks_movement(col, row)

    def is_walkable(self, col: int, row: int) -> bool:
        return not self.blocks_movement(col, row)

    def is_exit(self, col: int, row: int) -> bool:
        return self.get(col, row) == EXIT

    def is_door(self, col: int, row: int) -> bool:
        return self.get(col, row) == DOOR

    # ------------------------------------------------------------------
    # Door interaction
    # ------------------------------------------------------------------

    def toggle_door(self, col: int, row: int) -> None:
        """Open a closed door or close an open one."""
        if self.get(col, row) == DOOR:
            self.door_open[(col, row)] = not self.door_open.get((col, row), False)

    def door_is_open(self, col: int, row: int) -> bool:
        return self.door_open.get((col, row), False)
