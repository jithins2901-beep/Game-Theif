"""Grid: the data model for the game world.

The world is a 2D list of integer tile types. All game logic (collision,
pathfinding, FOV) works in tile coordinates. Pixel positions are always
derived: pixel_x = tile_col * TILE_SIZE.

Tile types
----------
FLOOR  (0) — walkable
WALL   (1) — blocks movement and line-of-sight
EXIT   (2) — walkable; reaching it wins the game
"""

# Tile type constants — use these everywhere instead of bare ints
FLOOR = 0
WALL = 1
EXIT = 2


class Grid:
    """Holds the tile data and exposes helpers used by rendering and AI."""

    def __init__(self, tiles: list[list[int]]) -> None:
        """
        Parameters
        ----------
        tiles : 2-D list  tiles[row][col]
        """
        self.tiles = tiles
        self.rows = len(tiles)
        self.cols = len(tiles[0]) if tiles else 0

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get(self, col: int, row: int) -> int:
        """Return the tile type at (col, row), or WALL if out of bounds."""
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.tiles[row][col]
        return WALL  # treat out-of-bounds as solid

    def is_walkable(self, col: int, row: int) -> bool:
        """True for tiles an entity can stand on (floor or exit)."""
        return self.get(col, row) != WALL

    def is_wall(self, col: int, row: int) -> bool:
        return self.get(col, row) == WALL

    def is_exit(self, col: int, row: int) -> bool:
        return self.get(col, row) == EXIT
