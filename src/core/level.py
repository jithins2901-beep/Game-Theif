"""Level: builds a Grid from an ASCII map string.

ASCII key
---------
  '#'  → WALL
  ' '  → FLOOR
  'E'  → EXIT  (the goal tile the player must reach)
  'P'  → FLOOR (player start — position is recorded separately)
  'G'  → FLOOR (guard start — position is recorded separately)

Design note: keeping the map as a plain string makes it trivially readable
and editable. Each character is one tile. The first row is row 0.
The map below is 20 columns × 15 rows → 640×480 px at TILE_SIZE=32.
"""

from src.core.grid import EXIT, FLOOR, WALL, Grid

# fmt: off
_MAP = [
    "####################",
    "#P      #          #",
    "#  ###  #  #####   #",
    "#  #       #       #",
    "#  #  ###  #  ###  #",
    "#     # #     #    #",
    "###   # #  ####  ###",
    "#     #       #    #",
    "#  ########   #    #",
    "#       #      #   #",
    "#  ###  #  ##  #   #",
    "#  #       #   #   #",
    "#  #  ###  #   # G #",
    "#         ##       #",
    "####################",
]
# E is placed separately so we can position it precisely
_EXIT_COL = 18
_EXIT_ROW = 1
# fmt: on


def _char_to_tile(ch: str) -> int:
    if ch == "#":
        return WALL
    return FLOOR  # P, G, space all become walkable floor


def build_level() -> dict:
    """Parse the ASCII map and return a dict with everything the Game needs.

    Returns
    -------
    {
        "grid"       : Grid,
        "player_start" : (col, row),
        "guard_starts" : [(col, row), ...],
        "exit"       : (col, row),
    }
    """
    tiles: list[list[int]] = []
    player_start = (1, 1)
    guard_starts: list[tuple[int, int]] = []

    for row_idx, row_str in enumerate(_MAP):
        row_tiles: list[int] = []
        for col_idx, ch in enumerate(row_str):
            if ch == "P":
                player_start = (col_idx, row_idx)
                row_tiles.append(FLOOR)
            elif ch == "G":
                guard_starts.append((col_idx, row_idx))
                row_tiles.append(FLOOR)
            else:
                row_tiles.append(_char_to_tile(ch))
        tiles.append(row_tiles)

    # Stamp the exit tile
    tiles[_EXIT_ROW][_EXIT_COL] = EXIT

    grid = Grid(tiles)
    return {
        "grid": grid,
        "player_start": player_start,
        "guard_starts": guard_starts,
        "exit": (_EXIT_COL, _EXIT_ROW),
    }
