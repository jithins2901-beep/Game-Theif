"""Core game class: owns the window and the main loop.

Milestone 8: win / lose / restart.

Game states
-----------
  "playing"  — normal gameplay, everything updates
  "won"      — player reached the exit; freeze world, show banner
  "lost"     — guard caught the player; freeze world, show banner

Transitions
-----------
  playing → won    : player tile == exit tile
  playing → lost   : any guard is in ALERT and its center is within
                     CATCH_RADIUS pixels of the player's center
  won / lost → playing : player presses R (calls _load_level())

Catch detection lives here (not in the guard) because it is a game-rule
outcome, not an AI behaviour. The guard doesn't "decide" to catch —
it just gets close enough and the game engine resolves it.
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

# How close (pixels, center-to-center) a guard must be to catch the player
CATCH_RADIUS = 20


class Game:
    """Top-level controller: update then render, every frame."""

    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Stealth Heist - AIML Project")
        self.clock = pygame.time.Clock()
        self.running = False

        self.hud = HUD()
        self._load_level()

    # ------------------------------------------------------------------
    # Level / entity initialisation
    # ------------------------------------------------------------------

    def _load_level(self) -> None:
        """Build level and spawn entities. Called on init and on restart."""
        level = build_level()
        self.grid     = level["grid"]
        self.exit_pos = level["exit"]

        pc, pr = level["player_start"]
        self.player = Player(pc, pr)

        self.guards: list[Guard] = []
        for col, row in level["guard_starts"]:
            waypoints = self._make_patrol_route(col, row)
            guard = Guard(col, row, waypoints, self.grid, self)
            self.guards.append(guard)

        self.renderer = Renderer(self.screen)

        # "playing" | "won" | "lost"
        self.game_state: str = "playing"

    def _make_patrol_route(
        self, start_col: int, start_row: int
    ) -> list[tuple[int, int]]:
        return [
            (17, 12),
            (17, 10),
            (14, 10),
            (14, 12),
        ]

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

                # R restarts from any state
                elif event.key == pygame.K_r:
                    self._load_level()

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        # Freeze the world when the game is over — only events are handled
        if self.game_state != "playing":
            return

        # --- Player movement ---
        intent = get_movement_intent()
        self.player.update(dt, intent, self.grid)

        # --- Guards ---
        for guard in self.guards:
            guard.update(dt, self.player)

        # --- Win check: player reached the exit tile ---
        if self.player.tile_pos() == self.exit_pos:
            self.game_state = "won"
            return

        # --- Lose check: ALERT guard close enough to catch player ---
        if self._player_caught():
            self.game_state = "lost"

    def _player_caught(self) -> bool:
        """True if any ALERT guard is within CATCH_RADIUS of the player."""
        px, py = self.player.center_x, self.player.center_y
        for guard in self.guards:
            if guard.state_name == "ALERT":
                dist = math.hypot(
                    guard.center_x - px,
                    guard.center_y - py,
                )
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

        # Overlay win / lose banner on top of everything
        if self.game_state == "won":
            self.hud.draw_message(
                self.screen,
                "YOU ESCAPED!",
                (80, 230, 100),
            )
        elif self.game_state == "lost":
            self.hud.draw_message(
                self.screen,
                "YOU WERE CAUGHT!",
                (230, 60, 60),
            )

        pygame.display.flip()
