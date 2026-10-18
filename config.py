"""Global configuration constants for the game.

All tunable values live here so balance / visual tweaks never require editing
game logic. This is the single source of truth for sizes, speeds and colors.
"""

# --- Window ---
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480
FPS = 60
TITLE = "Stealth Heist - AIML Project"

# --- Grid ---
# The world is a grid of tiles. Pixel positions are derived from tile coords.
TILE_SIZE = 32
GRID_COLS = WINDOW_WIDTH // TILE_SIZE  # 20
GRID_ROWS = WINDOW_HEIGHT // TILE_SIZE  # 15

# --- Vision Cone (FOV) ---
import math
FOV_ANGLE = math.radians(70)   # half-angle of the cone (total = 140°)
FOV_RADIUS = 160               # how far the guard can see in pixels
FOV_RAYS = 60                  # number of rays cast across the cone
FOV_STEP = 4                   # ray march step size in pixels (smaller = more accurate, slower)

# --- Colors (R, G, B) ---
COLOR_BG = (15, 15, 20)
COLOR_WALL = (70, 70, 80)
COLOR_FLOOR = (35, 35, 45)
COLOR_EXIT = (40, 200, 90)
COLOR_PLAYER = (80, 180, 255)
COLOR_GUARD = (230, 80, 80)
COLOR_VISION = (255, 220, 80)
COLOR_HUD_TEXT = (235, 235, 235)
