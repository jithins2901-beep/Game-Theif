"""Core game class: owns the window and the main loop.

Stage A: larger facility, 3 guards with unique patrol routes.
Stage B: door interaction, furniture cover.
Stage C: darkness lighting overlay.
"""

import math
import pygame

from config import COLOR_BG, FPS, WINDOW_HEIGHT, WINDOW_WIDTH
from src.core.level import build_level
from src.entities.player import Player
from src.entities.guard import Guard
from src.input_handler import get_movement_intent
from src.ui.renderer import Renderer
from src.ui.hud import HUD

# How close (px, center-to-center) an ALERT guard must be to catch the player
CATCH_RADIUS = 20

# How close the player must be to a door to interact with it (px from tile center)
DOOR_INTERACT_RADIUS = 40


class Game:
    """Top-level controller: update then render, every frame."""

    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Stealth Heist — AIML Project")
        self.clock  = pygame.time.Clock()
        self.running = False

        self.hud = HUD()
        self._load_level()

    # ------------------------------------------------------------------
    # Level init
    # ------------------------------------------------------------------

    def _load_level(self) -> None:
        level = build_level()
        self.grid          = level["grid"]
        self.exit_pos      = level["exit"]
        self.patrol_routes = level["patrol_routes"]

        pc, pr = level["player_start"]
        self.player = Player(pc, pr)

        self.guards: list[Guard] = []
        for col, row, route_id in level["guard_starts"]:
            route = self.patrol_routes.get(route_id, [(col, row)])
            guard = Guard(col, row, route, self.grid, self)
            self.guards.append(guard)

        self.renderer = Renderer(self.screen)

        # "playing" | "won" | "lost"
        self.game_state: str = "playing"

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        self.running = True
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self._handle_events()
            self.update(dt)
            self.render()
        pygame.quit()

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_r:
                    self._load_level()
                elif event.key == pygame.K_SPACE:
                    if self.game_state == "playing":
                        self._interact_door()

    def _interact_door(self) -> None:
        """Toggle any door tile adjacent to the player."""
        from config import TILE_SIZE
        px, py = self.player.center_x, self.player.center_y

        # Check a small area around the player for door tiles
        for dc in (-1, 0, 1):
            for dr in (-1, 0, 1):
                col = self.player.col + dc
                row = self.player.row + dr
                if self.grid.is_door(col, row):
                    # Distance from player center to door tile center
                    door_cx = col * TILE_SIZE + TILE_SIZE / 2
                    door_cy = row * TILE_SIZE + TILE_SIZE / 2
                    dist = math.hypot(px - door_cx, py - door_cy)
                    if dist <= DOOR_INTERACT_RADIUS:
                        self.grid.toggle_door(col, row)
                        return   # toggle only the nearest door per press

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        if self.game_state != "playing":
            return

        intent = get_movement_intent()
        self.player.update(dt, intent, self.grid)

        for guard in self.guards:
            guard.update(dt, self.player)

        if self.player.tile_pos() == self.exit_pos:
            self.game_state = "won"
            return

        if self._player_caught():
            self.game_state = "lost"

    def _player_caught(self) -> bool:
        px, py = self.player.center_x, self.player.center_y
        for guard in self.guards:
            if guard.state_name == "ALERT":
                dist = math.hypot(guard.center_x - px, guard.center_y - py)
                if dist <= CATCH_RADIUS:
                    return True
        return False

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def render(self) -> None:
        self.screen.fill(COLOR_BG)
        self.renderer.draw(self)
        self.hud.draw(self.screen, self)

        if self.game_state == "won":
            self.hud.draw_message(self.screen, "YOU ESCAPED!", (80, 230, 100))
        elif self.game_state == "lost":
            self.hud.draw_message(self.screen, "YOU WERE CAUGHT!", (230, 60, 60))

        pygame.display.flip()
