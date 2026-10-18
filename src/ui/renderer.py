"""Renderer: draws the current game state to a Pygame surface.

This is the ONLY file that imports pygame for drawing. It never mutates
game state — it only reads.

Draw order (back to front):
  1. Tiles         (floor, walls, exit)
  2. Vision cones  (semi-transparent, color-coded by FSM state)
  3. Guards        (body + direction arrow, tinted by state)
  4. Player        (always on top)
"""

import pygame
import math

from config import (
    COLOR_EXIT,
    COLOR_FLOOR,
    COLOR_GUARD,
    COLOR_PLAYER,
    COLOR_WALL,
    TILE_SIZE,
)
from src.core.grid import EXIT, FLOOR, WALL

# Vision cone colors per FSM state  (fill RGBA, border RGBA)
_CONE_COLORS = {
    "PATROL":     ((255, 220,  80,  45), (255, 220,  80, 110)),
    "SUSPICIOUS": ((255, 200,  40,  75), (255, 200,  40, 160)),
    "ALERT":      ((255,  60,  60,  90), (255,  60,  60, 190)),
    "SEARCH":     ((255, 130,  30,  65), (255, 130,  30, 145)),
}
_CONE_DEFAULT = ((200, 200, 200, 45), (200, 200, 200, 110))

# Guard body tints per state
_GUARD_TINT = {
    "PATROL":     (230,  80,  80),
    "SUSPICIOUS": (230, 190,  30),
    "ALERT":      (255,  40,  40),
    "SEARCH":     (230, 120,  30),
}


class Renderer:
    """Reads game state and draws it each frame."""

    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self._vision_surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)

    def draw(self, game) -> None:
        self._draw_tiles(game.grid)
        self._draw_exit_marker(game)       # pulsing exit arrow
        self._draw_vision_cones(game.guards)
        for guard in game.guards:
            self._draw_guard(guard)
        self._draw_player(game.player)

    # ------------------------------------------------------------------
    # Tile layer
    # ------------------------------------------------------------------

    def _draw_tiles(self, grid) -> None:
        for row in range(grid.rows):
            for col in range(grid.cols):
                tile = grid.get(col, row)
                rect = pygame.Rect(
                    col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE
                )
                if tile == WALL:
                    color = COLOR_WALL
                elif tile == EXIT:
                    color = COLOR_EXIT
                else:
                    color = COLOR_FLOOR
                pygame.draw.rect(self.screen, color, rect)
                if tile == FLOOR:
                    pygame.draw.rect(self.screen, (25, 25, 35), rect, 1)

    # ------------------------------------------------------------------
    # Exit marker
    # ------------------------------------------------------------------

    def _draw_exit_marker(self, game) -> None:
        """Draw a pulsing 'EXIT' label above the exit tile."""
        import time
        ec, er = game.exit_pos
        cx = ec * TILE_SIZE + TILE_SIZE // 2
        cy = er * TILE_SIZE

        # Pulse brightness using a sine wave
        pulse = (math.sin(time.time() * 4) + 1) / 2        # 0.0 → 1.0
        alpha = int(160 + 80 * pulse)
        green = min(255, int(180 + 75 * pulse))
        color = (30, green, 60)

        if not hasattr(self, "_exit_font"):
            pygame.font.init()
            self._exit_font = pygame.font.SysFont("consolas", 11, bold=True)
        label = self._exit_font.render("EXIT", True, color)
        lx = cx - label.get_width() // 2
        ly = cy - label.get_height() - 2
        self.screen.blit(label, (lx, ly))

    # ------------------------------------------------------------------
    # ------------------------------------------------------------------

    def _draw_vision_cones(self, guards: list) -> None:
        self._vision_surf.fill((0, 0, 0, 0))

        for guard in guards:
            poly = guard.vision.polygon
            if len(poly) < 3:
                continue

            int_poly = [(int(x), int(y)) for x, y in poly]
            fill, border = _CONE_COLORS.get(guard.state_name, _CONE_DEFAULT)

            pygame.draw.polygon(self._vision_surf, fill,   int_poly)
            pygame.draw.polygon(self._vision_surf, border, int_poly, 2)

        self.screen.blit(self._vision_surf, (0, 0))

    # ------------------------------------------------------------------
    # Entity layer
    # ------------------------------------------------------------------

    def _draw_player(self, player) -> None:
        rect = pygame.Rect(int(player.x), int(player.y), player.size, player.size)
        pygame.draw.rect(self.screen, COLOR_PLAYER, rect, border_radius=5)
        pygame.draw.circle(
            self.screen,
            (255, 255, 255),
            (int(player.center_x), int(player.center_y)),
            3,
        )

    def _draw_guard(self, guard) -> None:
        color = _GUARD_TINT.get(guard.state_name, COLOR_GUARD)
        rect  = pygame.Rect(int(guard.x), int(guard.y), guard.size, guard.size)
        pygame.draw.rect(self.screen, color, rect, border_radius=5)

        # Direction arrow — gets longer and brighter in ALERT
        arrow_len = 14 if guard.state_name == "ALERT" else 10
        end_x = guard.center_x + math.cos(guard.facing_angle) * arrow_len
        end_y = guard.center_y + math.sin(guard.facing_angle) * arrow_len
        pygame.draw.line(
            self.screen,
            (255, 255, 255),
            (int(guard.center_x), int(guard.center_y)),
            (int(end_x), int(end_y)),
            2,
        )
