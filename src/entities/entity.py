"""Base Entity: shared position helpers for all game objects.

Entities store their position in PIXEL coordinates (float) for smooth
sub-tile movement. Tile coordinates are derived on demand. This is the
standard approach: keep floating-point precision for movement math, snap
to tile grid only for collision and AI queries.
"""

from config import TILE_SIZE


class Entity:
    """Base class for Player and Guard.

    Attributes
    ----------
    x, y : float
        Pixel position of the entity's top-left corner.
    size : int
        Width and height in pixels. Drawn as a square.
    """

    def __init__(self, col: int, row: int, size: int) -> None:
        # Store as pixels so movement math is straightforward
        self.x: float = col * TILE_SIZE + (TILE_SIZE - size) / 2
        self.y: float = row * TILE_SIZE + (TILE_SIZE - size) / 2
        self.size: int = size

    # ------------------------------------------------------------------
    # Tile-coordinate helpers (used by collision and AI)
    # ------------------------------------------------------------------

    @property
    def col(self) -> int:
        """Tile column the entity's center is in."""
        return int((self.x + self.size / 2) // TILE_SIZE)

    @property
    def row(self) -> int:
        """Tile row the entity's center is in."""
        return int((self.y + self.size / 2) // TILE_SIZE)

    @property
    def center_x(self) -> float:
        return self.x + self.size / 2

    @property
    def center_y(self) -> float:
        return self.y + self.size / 2

    def tile_pos(self) -> tuple[int, int]:
        """Return (col, row) tile position of the entity's center."""
        return (self.col, self.row)
