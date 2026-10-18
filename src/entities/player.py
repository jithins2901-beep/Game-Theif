"""Player entity: movement + wall collision.

Movement is pixel-based and frame-rate independent (uses dt).
Collision is resolved per-axis (try X move, then try Y move separately).
This "axis-split" approach lets the player slide along walls instead of
getting stuck on corners.

How axis-split collision works
-------------------------------
1. Move the player by dx * speed * dt on the X axis.
2. Check all four corners of the player's bounding box.
3. If any corner is inside a wall, push the player back:
   - Moving right → right edge snaps to the left face of the wall tile.
   - Moving left  → left edge snaps to the right face of the wall tile.
4. Repeat steps 1-3 for the Y axis independently.
"""

from src.entities.entity import Entity
from src.core.grid import Grid
from config import TILE_SIZE


PLAYER_SIZE = 22
PLAYER_SPEED = 120  # pixels per second


class Player(Entity):
    def __init__(self, col: int, row: int) -> None:
        super().__init__(col, row, PLAYER_SIZE)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float, intent: dict, grid: Grid) -> None:
        dx = intent["dx"]
        dy = intent["dy"]

        # Move then resolve — one axis at a time
        if dx != 0:
            self.x += dx * PLAYER_SPEED * dt
            self._resolve_x(dx, grid)

        if dy != 0:
            self.y += dy * PLAYER_SPEED * dt
            self._resolve_y(dy, grid)

    # ------------------------------------------------------------------
    # Collision resolution
    # ------------------------------------------------------------------

    def _resolve_x(self, dx: int, grid: Grid) -> None:
        """Push the player out of walls after an X-axis move."""
        if dx > 0:
            # Moving right: check right edge of bounding box
            right = self.x + self.size
            for row_off in (0, self.size - 1):
                col = int(right // TILE_SIZE)
                row = int((self.y + row_off) // TILE_SIZE)
                if grid.is_wall(col, row):
                    # Snap right edge to the left face of the wall tile
                    self.x = col * TILE_SIZE - self.size
                    break
        else:
            # Moving left: check left edge
            for row_off in (0, self.size - 1):
                col = int(self.x // TILE_SIZE)
                row = int((self.y + row_off) // TILE_SIZE)
                if grid.is_wall(col, row):
                    # Snap left edge to the right face of the wall tile
                    self.x = (col + 1) * TILE_SIZE
                    break

    def _resolve_y(self, dy: int, grid: Grid) -> None:
        """Push the player out of walls after a Y-axis move."""
        if dy > 0:
            # Moving down: check bottom edge
            bottom = self.y + self.size
            for col_off in (0, self.size - 1):
                row = int(bottom // TILE_SIZE)
                col = int((self.x + col_off) // TILE_SIZE)
                if grid.is_wall(col, row):
                    self.y = row * TILE_SIZE - self.size
                    break
        else:
            # Moving up: check top edge
            for col_off in (0, self.size - 1):
                row = int(self.y // TILE_SIZE)
                col = int((self.x + col_off) // TILE_SIZE)
                if grid.is_wall(col, row):
                    self.y = (row + 1) * TILE_SIZE
                    break
