"""Global configuration constants for the game.

All tunable values live here so balance / visual tweaks never require editing
game logic. This is the single source of truth for sizes, speeds and colors.
"""

import math

# --- Window ---
WINDOW_WIDTH  = 960
WINDOW_HEIGHT = 704
FPS           = 60
TITLE         = "Stealth Heist — AIML Project"

# --- Grid ---
TILE_SIZE  = 32
GRID_COLS  = WINDOW_WIDTH  // TILE_SIZE   # 30
GRID_ROWS  = WINDOW_HEIGHT // TILE_SIZE   # 22

# --- Vision Cone (FOV) ---
FOV_ANGLE  = math.radians(65)   # half-angle → 130° total cone
FOV_RADIUS = 180                # pixels
FOV_RAYS   = 72                 # rays cast per guard (more = smoother polygon)
FOV_STEP   = 3                  # ray march step in pixels

# Ambient light radius around the player (used by lighting overlay)
PLAYER_LIGHT_RADIUS = 80        # pixels — small personal light bubble

# --- Colors (R, G, B) ---
COLOR_BG        = (10, 10, 14)
COLOR_WALL      = (55, 55, 68)
COLOR_WALL_TOP  = (80, 80, 96)   # lighter face on top of wall (depth illusion)
COLOR_FLOOR     = (32, 32, 42)
COLOR_FLOOR_ALT = (28, 28, 38)   # checkerboard variation for visual texture
COLOR_EXIT      = (35, 180, 80)
COLOR_DOOR_CLOSED = (110, 75, 40)
COLOR_DOOR_OPEN   = (70, 48, 25)
COLOR_FURNITURE = (55, 45, 35)
COLOR_PLAYER    = (70, 165, 245)
COLOR_GUARD     = (210, 70,  70)
COLOR_VISION    = (255, 220, 80)
COLOR_HUD_TEXT  = (230, 230, 230)
