"""Vision cone: raycasting-based field-of-view for guards.

How it works (explain this in your viva)
-----------------------------------------
1.  We cast FOV_RAYS rays fanning out from the guard's center.
    They spread across a total angle of FOV_ANGLE*2 degrees, centred on
    the guard's current facing direction.

2.  Each ray marches forward step-by-step (FOV_STEP pixels at a time).
    It stops when it either:
      (a) hits a wall tile — the ray is blocked, vision stops here.
      (b) travels FOV_RADIUS pixels — max sight range reached.

3.  The endpoint of every ray is collected into a polygon.
    We draw this polygon as a semi-transparent filled shape so the player
    can *see* exactly what the guard can see.

4.  Player detection: we also do a direct line-of-sight check from the
    guard to the player's center.  If the player's center is:
      - within the cone angle of the guard's facing direction, AND
      - within FOV_RADIUS pixels, AND
      - not blocked by a wall (ray from guard to player hits no wall)
    …then can_see_player() returns True.

This is a "ray marching" approach — simpler than true geometric raycasting
but fast enough for a handful of guards and easy to understand.
"""

import math
from config import FOV_ANGLE, FOV_RADIUS, FOV_RAYS, FOV_STEP, TILE_SIZE


class VisionCone:
    """Computes and stores the vision cone polygon for one guard."""

    def __init__(self, grid) -> None:
        self.grid = grid
        # The polygon points (pixel coords) computed last frame
        self.polygon: list[tuple[float, float]] = []
        # Whether the player was seen last frame
        self.sees_player: bool = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update(self, guard, player) -> None:
        """Recompute the vision cone and check player visibility.

        Call this every frame from Guard.update().
        """
        self.polygon = self._cast_cone(guard)
        self.sees_player = self._check_player(guard, player)

    # ------------------------------------------------------------------
    # Ray casting
    # ------------------------------------------------------------------

    def _cast_cone(
        self, guard
    ) -> list[tuple[float, float]]:
        """Cast FOV_RAYS rays and return the polygon they form.

        The polygon starts and ends at the guard's center so it closes
        properly when drawn as a filled shape.
        """
        cx, cy = guard.center_x, guard.center_y
        angle = guard.facing_angle
        points: list[tuple[float, float]] = [(cx, cy)]

        for i in range(FOV_RAYS + 1):
            # Angle for this ray: spread evenly across the full cone width
            t = i / FOV_RAYS                         # 0.0 → 1.0
            ray_angle = (angle - FOV_ANGLE) + t * (FOV_ANGLE * 2)
            endpoint = self._cast_ray(cx, cy, ray_angle)
            points.append(endpoint)

        return points

    def _cast_ray(
        self, ox: float, oy: float, angle: float
    ) -> tuple[float, float]:
        """March a single ray from (ox, oy) in direction `angle`.

        Returns the first point that hits a wall or the max-range endpoint.
        """
        dx = math.cos(angle)
        dy = math.sin(angle)
        x, y = ox, oy

        steps = int(FOV_RADIUS / FOV_STEP)
        for _ in range(steps):
            x += dx * FOV_STEP
            y += dy * FOV_STEP

            col = int(x // TILE_SIZE)
            row = int(y // TILE_SIZE)

            if self.grid.blocks_sight(col, row):
                # Step back one step so endpoint is just before the wall
                return (x - dx * FOV_STEP, y - dy * FOV_STEP)

        return (x, y)

    # ------------------------------------------------------------------
    # Player detection
    # ------------------------------------------------------------------

    def _check_player(self, guard, player) -> bool:
        """Return True if the guard has an unobstructed view of the player."""
        cx, cy = guard.center_x, guard.center_y
        px, py = player.center_x, player.center_y

        # 1. Distance check
        dist = math.hypot(px - cx, py - cy)
        if dist > FOV_RADIUS:
            return False

        # 2. Cone angle check
        angle_to_player = math.atan2(py - cy, px - cx)
        angle_diff = _angle_diff(angle_to_player, guard.facing_angle)
        if abs(angle_diff) > FOV_ANGLE:
            return False

        # 3. Line-of-sight: march a ray from guard center toward player center.
        #    Start slightly ahead (4 px) to avoid the guard's own tile
        #    registering as a wall due to floating-point edge cases.
        dx = px - cx
        dy = py - cy

        # Unit vector toward player
        ux = dx / dist
        uy = dy / dist

        # Start 4 px ahead of guard center, stop 4 px before player center
        march_dist = dist - 4.0
        steps = max(1, int(march_dist / FOV_STEP))
        step_x = ux * FOV_STEP
        step_y = uy * FOV_STEP

        rx = cx + ux * 4.0
        ry = cy + uy * 4.0

        for _ in range(steps):
            col = int(rx // TILE_SIZE)
            row = int(ry // TILE_SIZE)
            if self.grid.blocks_sight(col, row):
                return False
            rx += step_x
            ry += step_y

        return True


# ------------------------------------------------------------------
# Helper
# ------------------------------------------------------------------

def _angle_diff(a: float, b: float) -> float:
    """Smallest signed difference between two angles (radians).

    Result is in [-π, π].
    """
    diff = (a - b + math.pi) % (2 * math.pi) - math.pi
    return diff
