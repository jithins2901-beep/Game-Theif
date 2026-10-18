"""HUD: on-screen UI overlay.

Milestone 7 additions:
  - Guard state label is now color-coded by state
  - An alert bar grows while the guard is in SUSPICIOUS / ALERT / SEARCH
  - Win and lose banners (used from Milestone 8)

Color coding
------------
  PATROL     → grey / neutral
  SUSPICIOUS → yellow (something's wrong)
  ALERT      → red   (chasing!)
  SEARCH     → orange (lost you, but looking)
"""

import pygame

from config import COLOR_HUD_TEXT

# State → text color
_STATE_COLOR = {
    "PATROL":     (160, 160, 175),
    "SUSPICIOUS": (255, 220,  60),
    "ALERT":      (255,  70,  70),
    "SEARCH":     (255, 140,  30),
}
_DEFAULT_STATE_COLOR = (200, 200, 200)

# Alert bar colors
_BAR_BG    = (50, 50, 60)
_BAR_FILL  = {
    "PATROL":     (60,  60,  80),
    "SUSPICIOUS": (200, 180,  20),
    "ALERT":      (220,  40,  40),
    "SEARCH":     (210, 110,  20),
}


class HUD:
    """Draws all UI elements on top of the game world."""

    def __init__(self) -> None:
        pygame.font.init()
        self.font_sm = pygame.font.SysFont("consolas", 15)
        self.font_lg = pygame.font.SysFont("consolas", 42, bold=True)
        # Per-guard alert fill level (0.0 – 1.0) for smooth bar animation
        self._alert_levels: dict[int, float] = {}

    def draw(self, surface: pygame.Surface, game) -> None:
        # Only show guard status panel during active gameplay
        if game.game_state == "playing":
            self._draw_guard_states(surface, game.guards)
            self._draw_controls_hint(surface)

    def draw_message(self, surface: pygame.Surface, text: str, color: tuple) -> None:
        """Draw a large centered banner with a sub-hint below it."""
        msg = self.font_lg.render(text, True, color)
        x = (surface.get_width()  - msg.get_width())  // 2
        y = (surface.get_height() - msg.get_height()) // 2 - 20

        # Dark background panel
        pad = 16
        panel_w = msg.get_width()  + pad * 2
        panel_h = msg.get_height() + pad * 2 + 36   # extra room for hint
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 200))
        surface.blit(panel, (x - pad, y - pad))
        surface.blit(msg, (x, y))

        # Sub-hints
        hint1 = self.font_sm.render("Press  R  to play again", True, (200, 200, 200))
        hint2 = self.font_sm.render("Press  ESC  to quit",     True, (140, 140, 140))
        hx1 = (surface.get_width() - hint1.get_width()) // 2
        hx2 = (surface.get_width() - hint2.get_width()) // 2
        hy  = y + msg.get_height() + 10
        surface.blit(hint1, (hx1, hy))
        surface.blit(hint2, (hx2, hy + 18))

    # ------------------------------------------------------------------
    # Controls hint (bottom of screen during play)
    # ------------------------------------------------------------------

    def _draw_controls_hint(self, surface: pygame.Surface) -> None:
        """Small hint at the bottom-center so new players know the controls."""
        hint = self.font_sm.render(
            "WASD / Arrow keys — move     ESC — quit     Reach the GREEN tile!",
            True,
            (100, 100, 120),
        )
        x = (surface.get_width() - hint.get_width()) // 2
        y = surface.get_height() - hint.get_height() - 6
        surface.blit(hint, (x, y))

    # ------------------------------------------------------------------
    # Guard state panel
    # ------------------------------------------------------------------

    def _draw_guard_states(self, surface: pygame.Surface, guards: list) -> None:
        x, y = 8, 8
        for i, guard in enumerate(guards):
            state = guard.state_name
            text_color = _STATE_COLOR.get(state, _DEFAULT_STATE_COLOR)

            # ── State label ───────────────────────────────────────────
            label = f"GUARD {i + 1}:  {state}"
            text_surf = self.font_sm.render(label, True, text_color)

            pad = 4
            panel_w = max(text_surf.get_width() + pad * 2, 140)
            panel_h = text_surf.get_height() + pad * 2

            bg = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 160))
            surface.blit(bg, (x - pad, y - pad))
            surface.blit(text_surf, (x, y))
            y += panel_h + 2

            # ── Alert bar ─────────────────────────────────────────────
            # Smoothly animate a fill level toward the target
            target = _bar_target(state)
            prev   = self._alert_levels.get(i, 0.0)
            # Lerp toward target at different speeds (rise fast, fall slow)
            speed  = 3.0 if target > prev else 0.6
            level  = prev + (target - prev) * speed * (1 / 60)
            level  = max(0.0, min(1.0, level))
            self._alert_levels[i] = level

            bar_w  = 140
            bar_h  = 6
            bar_x  = x - pad
            bar_y  = y
            pygame.draw.rect(surface, _BAR_BG, (bar_x, bar_y, bar_w, bar_h), border_radius=3)
            fill_w = int(bar_w * level)
            if fill_w > 0:
                fill_color = _BAR_FILL.get(state, (80, 80, 80))
                pygame.draw.rect(
                    surface, fill_color, (bar_x, bar_y, fill_w, bar_h), border_radius=3
                )

            y += bar_h + 6


def _bar_target(state: str) -> float:
    """How full should the alert bar be for each state?"""
    return {
        "PATROL":     0.0,
        "SUSPICIOUS": 0.45,
        "ALERT":      1.0,
        "SEARCH":     0.65,
    }.get(state, 0.0)
