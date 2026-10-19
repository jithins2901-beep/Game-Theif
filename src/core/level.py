"""Level: builds a Grid from an ASCII map.

Map is 30 columns × 22 rows → 960×704 px at TILE_SIZE=32.

ASCII key
---------
  '#'  WALL
  ' '  FLOOR
  'D'  DOOR  (closed by default)
  'F'  FURNITURE (blocks movement, visible over, hides player)
  'E'  EXIT
  'P'  Player start (becomes FLOOR)
  '1'  Guard 1 start
  '2'  Guard 2 start
  '3'  Guard 3 start

Room layout (annotated):
  ┌──────────────────────────────┐  row 0 (top border)
  │  Entry hall (cols 1-28)      │  rows 1-3
  │  ┌──────────┐  ┌───────────┐ │
  │  │ Server   │  │ Security  │ │  rows 4-9  (left / right)
  │  │  Room    │  │  Office   │ │
  │  └──────────┘  └───────────┘ │
  │  ── corridor ──────────────  │  rows 10-11
  │  ┌──────────┐  ┌───────────┐ │
  │  │ Lounge   │  │ Storage   │ │  rows 12-17 (left / right)
  │  └──────────┘  └───────────┘ │
  │  ── corridor ──────────────  │  rows 18-19
  │  Vault wing          EXIT    │  rows 20-21
  └──────────────────────────────┘
"""

from src.core.grid import DOOR, EXIT, FLOOR, FURNITURE, WALL, Grid

# fmt: off
# 30 chars wide, 22 rows tall
_MAP = [
# 0         1         2
# 0123456789012345678901234567890
  "##############################",  # 0
  "#P           D               #",  # 1  entry hall
  "#   FF   FF      FF   FF     #",  # 2  furniture in hall
  "#            D               #",  # 3
  "####D#####  ####D######  #####",  # 4  room divider
  "#         #  #            #  #",  # 5  server room / security office
  "#  F   F  #  #  1  F  F   #  #",  # 6
  "#         #  #            #  #",  # 7
  "#  F   F  #  #    F  F    #  #",  # 8
  "####D#####  ####D######  #####",  # 9  room divider
  "#                            #",  # 10 mid corridor
  "#   FF        2     FF       #",  # 11 corridor with furniture
  "####D#####  ####D######  #####",  # 12 room divider
  "#         #  #            #  #",  # 13 lounge / storage
  "#  F   F  #  #  F      F  #  #",  # 14
  "#    3    #  #            #  #",  # 15
  "#  F   F  #  #  F      F  #  #",  # 16
  "####D#####  ####D######  #####",  # 17 room divider
  "#                            #",  # 18 lower corridor
  "#   FF        FF    FF       #",  # 19
  "#                          E #",  # 20 vault wing / exit
  "##############################",  # 21
]
# fmt: on

# Map special chars to tile types
_CHAR_MAP: dict[str, int] = {
    "#": WALL,
    " ": FLOOR,
    "D": DOOR,
    "F": FURNITURE,
    "E": EXIT,
    "P": FLOOR,   # player start
    "1": FLOOR,   # guard starts
    "2": FLOOR,
    "3": FLOOR,
}


def build_level() -> dict:
    """Parse the ASCII map and return everything the Game needs.

    Returns
    -------
    {
        "grid"          : Grid,
        "player_start"  : (col, row),
        "guard_starts"  : [(col, row, patrol_id), ...],
        "exit"          : (col, row),
        "patrol_routes" : {patrol_id: [(col,row), ...]},
    }
    """
    tiles: list[list[int]] = []
    player_start = (1, 1)
    guard_starts: list[tuple[int, int, int]] = []   # (col, row, route_id)
    exit_pos = (28, 20)

    for row_idx, row_str in enumerate(_MAP):
        row_tiles: list[int] = []
        for col_idx, ch in enumerate(row_str):
            tile = _CHAR_MAP.get(ch, FLOOR)
            if ch == "P":
                player_start = (col_idx, row_idx)
            elif ch in ("1", "2", "3"):
                guard_starts.append((col_idx, row_idx, int(ch)))
            elif ch == "E":
                exit_pos = (col_idx, row_idx)
            row_tiles.append(tile)
        tiles.append(row_tiles)

    grid = Grid(tiles)

    # ── Patrol routes (tile positions, named by guard id) ─────────────
    # Each route is a loop the guard walks using A*.  Routes are designed
    # to cover different rooms so guards don't all clump together.
    patrol_routes: dict[int, list[tuple[int, int]]] = {
        # Guard 1 — patrols server room (left room rows 5-8, cols 1-9)
        # Cols 1-9 are open floor; col 10 is wall
        1: [(2, 5), (8, 5), (8, 8), (2, 8)],

        # Guard 2 — patrols the two horizontal corridors (rows 10 and 19)
        2: [(2, 10), (27, 10), (27, 19), (2, 19)],

        # Guard 3 — patrols the lounge room (left room rows 13-16, cols 1-9)
        3: [(2, 13), (8, 13), (8, 16), (2, 16)],
    }

    return {
        "grid":          grid,
        "player_start":  player_start,
        "guard_starts":  guard_starts,
        "exit":          exit_pos,
        "patrol_routes": patrol_routes,
    }
