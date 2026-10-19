"""Renderer — draws the complete game world each frame.

Draw order (back to front)
--------------------------
1.  Floor tiles   (checkerboard texture variation)
2.  Furniture     (brown blocks with top-face shading)
3.  Doors         (warm brown, lighter when open)
4.  Walls         (dark body + lighter top-face for depth illusion)
5.  Exit marker   (pulsing green glow + label)
6.  Vision cones  (per-state colored semi-transparent polygon)
7.  Guards        (body + direction arrow, state-tinted)
8.  Player        (blue rounded square + center dot)
9.  Darkness overlay  (full-screen black with light holes cut out)

The darkness overlay (step 9) is what gives the Takeshi-style "you can
only see what's lit" atmosphere. It works by:
  a. Filling a full-screen SRCALPHA surface with near-opaque black.
  b. Drawing each guard's FOV polygon onto it in ALPHA=0 (transparent).
  c. Drawing a small circle around the player in ALPHA=0.
  d. Blitting the overlay — tiles only shine through the light holes.
"""

import math
import time
import pygame

from config import (
    COLOR_BG,
    COLOR_DOOR_CLOSED,
    COLOR_DOOR_OPEN,
    COLOR_EXIT,
    COLOR_FLOOR,
    COLOR_FLOOR_ALT,
    COLOR_FURNITURE,
    COLOR_GUARD,
    COLOR_PLAYER,
    COLOR_WALL,
    COLOR_WALL_TOP,
    FOV_RADIUS,
    PLAYER_LIGHT_RADIUS,
    TILE_SIZE,
)
from src.core.grid import DOOR, EXIT, FLOOR, FURNITURE, WALL

# Vision cone colors per FSM state (fill RGBA, border RGBA)
_CONE_COLORS = {
    "PATROL":     ((255, 220,  80,  50), (255, 220,  80, 120)),
    "SUSPICIOUS": ((255, 200,  40,  80), (255, 200,  40, 170)),
    "ALERT":      ((255,  55,  55, 100), (255,  55,  55, 200)),
    "SEARCH":     ((255, 130,  30,  70), (255, 130,  30, 155)),
}
_CONE_DEFAULT = ((200, 200, 200, 50), (200, 200, 200, 120))

# Guard body colors per state
_GUARD_COLOR = {
    "PATROL":     (210,  70,  70),
    "SUSPICIOUS": (220, 180,  30),
    "ALERT":      (255,  30,  30),
    "SEARCH":     (220, 110,  25),
}

# How opaque is the darkness overlay (0=invisible, 255=total black)
_DARKNESS_ALPHA = 210


class Renderer:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        w, h = screen.get_size()

        # Vision cone overlay (alpha-blended)
        self._cone_surf    = pygame.Surface((w, h), pygame.SRCALPHA)
        # Darkness overlay — filled black, light holes punched into it
        self._dark_surf    = pygame.Surface((w, h), pygame.SRCALPHA)
        # Exit font (lazy-init)
        self._exit_font: pygame.font.Font | None = None

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def draw(self, game) -> None:
        self._draw_floor(game.grid)
        self._draw_furniture(game.grid)
        self._draw_doors(game.grid)
        self._draw_walls(game.grid)
        self._draw_exit_marker(game)
        self._draw_vision_cones(game.guards)
        for guard in game.guards:
            self._draw_guard(guard)
        self._draw_player(game.player)
        self._draw_darkness(game)

    # ------------------------------------------------------------------
    # Floor
    # ------------------------------------------------------------------

    def _draw_floor(self, grid) -> None:
        for row in range(grid.rows):
            for col in range(grid.cols):
                t = grid.get(col, row)
                if t in (FLOOR, EXIT, DOOR):
                    # Subtle checkerboard: alternate two very similar shades
                    color = COLOR_FLOOR if (col + row) % 2 == 0 else COLOR_FLOOR_ALT
                    rect = pygame.Rect(col * TILE_SIZE, row * TILE_SIZE,
                                       TILE_SIZE, TILE_SIZE)
                    pygame.draw.rect(self.screen, color, rect)

    # ------------------------------------------------------------------
    # Furniture
    # ------------------------------------------------------------------

    def _draw_furniture(self, grid) -> None:
        for row in range(grid.rows):
            for col in range(grid.cols):
                if grid.get(col, row) != FURNITURE:
                    continue
                x = col * TILE_SIZE
                y = row * TILE_SIZE
                # Body
                body = pygame.Rect(x + 3, y + 5, TILE_SIZE - 6, TILE_SIZE - 6)
                pygame.draw.rect(self.screen, COLOR_FURNITURE, body, border_radius=3)
                # Top face (lighter edge — depth)
                top = pygame.Rect(x + 3, y + 5, TILE_SIZE - 6, 5)
                pygame.draw.rect(self.screen, (80, 65, 50), top, border_radius=3)

    # ------------------------------------------------------------------
    # Doors
    # ------------------------------------------------------------------

    def _draw_doors(self, grid) -> None:
        for row in range(grid.rows):
            for col in range(grid.cols):
                if grid.get(col, row) != DOOR:
                    continue
                x = col * TILE_SIZE
                y = row * TILE_SIZE
                is_open = grid.door_is_open(col, row)

                if is_open:
                    # Open door: just a thin frame on the sides
                    color = COLOR_DOOR_OPEN
                    # Left frame
                    pygame.draw.rect(self.screen, color,
                                     pygame.Rect(x, y, 4, TILE_SIZE))
                    # Right frame
                    pygame.draw.rect(self.screen, color,
                                     pygame.Rect(x + TILE_SIZE - 4, y, 4, TILE_SIZE))
                else:
                    # Closed door: full block with a cross handle
                    pygame.draw.rect(self.screen, COLOR_DOOR_CLOSED,
                                     pygame.Rect(x + 2, y + 2, TILE_SIZE - 4, TILE_SIZE - 4),
                                     border_radius=2)
                    # Door handle dot
                    hx = x + TILE_SIZE // 2
                    hy = y + TILE_SIZE // 2
                    pygame.draw.circle(self.screen, (180, 130, 70), (hx, hy), 4)

    # ------------------------------------------------------------------
    # Walls  (drawn last so they cover furniture edges)
    # ------------------------------------------------------------------

    def _draw_walls(self, grid) -> None:
        for row in range(grid.rows):
            for col in range(grid.cols):
                if grid.get(col, row) != WALL:
                    continue
                x = col * TILE_SIZE
                y = row * TILE_SIZE

                # Wall body
                pygame.draw.rect(self.screen, COLOR_WALL,
                                 pygame.Rect(x, y, TILE_SIZE, TILE_SIZE))

                # Top-face highlight (only if the tile above is NOT a wall)
                # This creates a subtle depth illusion — the top edge looks
                # like the lit upper surface of a 3D block.
                if grid.get(col, row - 1) != WALL:
                    pygame.draw.rect(self.screen, COLOR_WALL_TOP,
                                     pygame.Rect(x, y, TILE_SIZE, 5))

    # ------------------------------------------------------------------
    # Exit marker
    # ------------------------------------------------------------------

    def _draw_exit_marker(self, game) -> None:
        ec, er = game.exit_pos
        x = ec * TILE_SIZE
        y = er * TILE_SIZE

        # Pulsing glow behind the tile
        pulse  = (math.sin(time.time() * 3.5) + 1) / 2
        radius = int(TILE_SIZE * 0.8 + TILE_SIZE * 0.25 * pulse)
        cx     = x + TILE_SIZE // 2
        cy     = y + TILE_SIZE // 2

        glow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        alpha     = int(40 + 30 * pulse)
        pygame.draw.circle(glow_surf, (40, 220, 90, alpha),
                           (radius, radius), radius)
        self.screen.blit(glow_surf, (cx - radius, cy - radius))

        # Green tile fill
        pygame.draw.rect(self.screen, COLOR_EXIT,
                         pygame.Rect(x + 2, y + 2, TILE_SIZE - 4, TILE_SIZE - 4),
                         border_radius=3)

        # "EXIT" label
        if self._exit_font is None:
            pygame.font.init()
            self._exit_font = pygame.font.SysFont("consolas", 10, bold=True)
        green  = min(255, int(160 + 95 * pulse))
        label  = self._exit_font.render("EXIT", True, (30, green, 60))
        self.screen.blit(label, (cx - label.get_width() // 2,
                                  cy - label.get_height() // 2))

    # ------------------------------------------------------------------
    # Vision cones (on a transparent overlay)
    # ------------------------------------------------------------------

    def _draw_vision_cones(self, guards: list) -> None:
        self._cone_surf.fill((0, 0, 0, 0))
        for guard in guards:
            poly = guard.vision.polygon
            if len(poly) < 3:
                continue
            ipts = [(int(x), int(y)) for x, y in poly]
            fill, border = _CONE_COLORS.get(guard.state_name, _CONE_DEFAULT)
            pygame.draw.polygon(self._cone_surf, fill,   ipts)
            pygame.draw.polygon(self._cone_surf, border, ipts, 2)
        self.screen.blit(self._cone_surf, (0, 0))

    # ------------------------------------------------------------------
    # Entities
    # ------------------------------------------------------------------

    def _draw_player(self, player) -> None:
        rect = pygame.Rect(int(player.x), int(player.y), player.size, player.size)
        pygame.draw.rect(self.screen, COLOR_PLAYER, rect, border_radius=5)
        pygame.draw.circle(self.screen, (255, 255, 255),
                           (int(player.center_x), int(player.center_y)), 3)

    def _draw_guard(self, guard) -> None:
        color = _GUARD_COLOR.get(guard.state_name, COLOR_GUARD)
        rect  = pygame.Rect(int(guard.x), int(guard.y), guard.size, guard.size)
        pygame.draw.rect(self.screen, color, rect, border_radius=5)

        arrow_len = 14 if guard.state_name == "ALERT" else 10
        ex = guard.center_x + math.cos(guard.facing_angle) * arrow_len
        ey = guard.center_y + math.sin(guard.facing_angle) * arrow_len
        pygame.draw.line(self.screen, (255, 255, 255),
                         (int(guard.center_x), int(guard.center_y)),
                         (int(ex), int(ey)), 2)

    # ------------------------------------------------------------------
    # Darkness overlay with light holes
    # ------------------------------------------------------------------

    def _draw_darkness(self, game) -> None:
        """Fill the screen with near-opaque black, then cut light holes.

        Light holes = guard vision cones (punched through the dark)
                    + a small ambient circle around the player.

        The "punch" is done by drawing the shapes with SRCALPHA=0
        (fully transparent) onto the dark surface using BLEND_RGBA_MIN,
        which sets alpha to min(existing, 0) = 0 wherever we draw.
        """
        # Reset dark surface
        self._dark_surf.fill((0, 0, 0, _DARKNESS_ALPHA))

        # Punch guard vision cones
        for guard in game.guards:
            poly = guard.vision.polygon
            if len(poly) < 3:
                continue
            ipts = [(int(x), int(y)) for x, y in poly]
            # Draw with alpha 0 → makes the cone area transparent in the dark layer
            pygame.draw.polygon(self._dark_surf, (0, 0, 0, 0), ipts)

        # Punch player ambient light (small circle)
        pcx = int(game.player.center_x)
        pcy = int(game.player.center_y)
        r   = PLAYER_LIGHT_RADIUS
        pygame.draw.circle(self._dark_surf, (0, 0, 0, 0), (pcx, pcy), r)
        # Soft falloff ring (a slightly transparent ring around the hole)
        pygame.draw.circle(self._dark_surf, (0, 0, 0, 120), (pcx, pcy), r + 20, 20)

        self.screen.blit(self._dark_surf, (0, 0))
