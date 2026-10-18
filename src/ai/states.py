"""Guard FSM states.

Milestone 6: PatrolState upgraded to use A* pathfinding between waypoints.
Milestone 7: SuspiciousState, AlertState, SearchState fully implemented.

State summary
-------------
PATROL     — walk a looping waypoint route via A*
SUSPICIOUS — guard noticed something; moves to investigate point, then returns
ALERT      — guard has clear sight of player; chases via A*
SEARCH     — guard lost the player; moves to last known tile then looks around
"""

import math

from config import TILE_SIZE
from src.ai.fsm import State
from src.ai.pathfinding import find_path

# Pixel distance to waypoint/path-node center before advancing to next node
ARRIVAL_THRESHOLD = 6


# ── Helper shared by multiple states ──────────────────────────────────

def _move_toward_tile(guard, target_col: int, target_row: int, dt: float) -> bool:
    """Move guard one step toward (target_col, target_row).

    Returns True when the guard has arrived (within ARRIVAL_THRESHOLD px).
    Snaps guard to tile center on arrival to avoid drift.
    Updates guard.facing_angle.
    """
    target_x = target_col * TILE_SIZE + TILE_SIZE / 2
    target_y = target_row * TILE_SIZE + TILE_SIZE / 2

    dx = target_x - guard.center_x
    dy = target_y - guard.center_y
    dist = math.hypot(dx, dy)

    if dist < ARRIVAL_THRESHOLD:
        guard.x = target_col * TILE_SIZE + (TILE_SIZE - guard.size) / 2
        guard.y = target_row * TILE_SIZE + (TILE_SIZE - guard.size) / 2
        return True  # arrived

    nx, ny = dx / dist, dy / dist
    guard.x += nx * guard.speed * dt
    guard.y += ny * guard.speed * dt
    guard.facing_angle = math.atan2(dy, dx)
    return False


# ══════════════════════════════════════════════════════════════════════
# PATROL
# ══════════════════════════════════════════════════════════════════════

class PatrolState(State):
    """Walk a looping list of waypoints. A* is used to navigate between them.

    Why A* for patrol?
    ------------------
    Without pathfinding the guard moves in a straight line toward each
    waypoint, which passes through walls if the route isn't perfectly
    designed. A* gives the guard a tile-safe path regardless of level
    layout — and reuses the same algorithm we need for chasing.

    The path to the next waypoint is computed once on entry to each
    waypoint and cached in self._path. The guard walks node-by-node
    along that path until it reaches the waypoint, then plans the next.
    """

    def enter(self) -> None:
        self.owner.waypoint_index = 0
        self._path: list[tuple[int, int]] = []
        self._plan_path()

    def _plan_path(self) -> None:
        """Compute A* path from current tile to the current waypoint."""
        guard = self.owner
        waypoints = guard.patrol_waypoints
        if not waypoints:
            return
        goal = waypoints[guard.waypoint_index]
        self._path = find_path(guard.grid, guard.tile_pos(), goal)

    def update(self, dt: float) -> None:
        guard = self.owner
        if not guard.patrol_waypoints:
            return

        # If path is empty the guard is at the waypoint — advance
        if not self._path:
            guard.waypoint_index = (
                (guard.waypoint_index + 1) % len(guard.patrol_waypoints)
            )
            self._plan_path()
            return

        # Move toward the first tile on the remaining path
        next_col, next_row = self._path[0]
        arrived = _move_toward_tile(guard, next_col, next_row, dt)
        if arrived:
            self._path.pop(0)  # consumed this node

    def exit(self) -> None:
        self._path = []


# ══════════════════════════════════════════════════════════════════════
# SUSPICIOUS  (implemented in Milestone 7)
# ══════════════════════════════════════════════════════════════════════

class SuspiciousState(State):
    """Guard glimpsed the player. Moves to investigate, then returns to patrol.

    Transitions
    -----------
    → ALERT   if the guard still clearly sees the player after a short
              confirmation delay (avoids frame-0 skip-to-ALERT)
    → PATROL  after SUSPICIOUS_DURATION seconds without a sighting
    """

    SUSPICIOUS_DURATION = 3.0   # seconds before giving up and returning
    # Guard must sustain a sighting for this long before escalating.
    # This adds drama (player can break LoS and stay SUSPICIOUS) and
    # prevents the FSM from skipping SUSPICIOUS in the same frame.
    ALERT_CONFIRM_TIME  = 0.4   # seconds of continuous sighting to trigger ALERT

    def enter(self) -> None:
        guard = self.owner
        self._timer = 0.0
        self._sighting_timer = 0.0   # how long the current sighting has lasted
        target = guard.last_known_player or guard.tile_pos()
        self._path = find_path(guard.grid, guard.tile_pos(), target)

    def update(self, dt: float) -> None:
        from src.ai.states import AlertState, PatrolState
        guard = self.owner

        self._timer += dt

        if guard.vision.sees_player:
            self._sighting_timer += dt
            # Sustained sighting long enough → escalate to ALERT
            if self._sighting_timer >= self.ALERT_CONFIRM_TIME:
                guard.fsm.change(AlertState(guard))
                return
        else:
            # Lost sight — reset the confirmation timer
            self._sighting_timer = 0.0

        # Timed out without sustained sighting → back to patrol
        if self._timer >= self.SUSPICIOUS_DURATION:
            guard.fsm.change(PatrolState(guard))
            return

        # Walk toward the investigation point
        if self._path:
            next_col, next_row = self._path[0]
            arrived = _move_toward_tile(guard, next_col, next_row, dt)
            if arrived:
                self._path.pop(0)

    def exit(self) -> None:
        self._path = []


# ══════════════════════════════════════════════════════════════════════
# ALERT  (implemented in Milestone 7)
# ══════════════════════════════════════════════════════════════════════

class AlertState(State):
    """Guard has a clear sighting — chases the player using A*.

    A* is re-planned every REPLAN_INTERVAL seconds so the guard tracks
    a moving player around corners.

    Transitions
    -----------
    → SEARCH  when the guard loses sight of the player
    """

    REPLAN_INTERVAL = 0.4   # seconds between A* replans

    def enter(self) -> None:
        guard = self.owner
        self._path: list[tuple[int, int]] = []
        self._replan_timer = 0.0
        self._replan(guard)

    def _replan(self, guard) -> None:
        player_tile = guard.game.player.tile_pos()
        self._path = find_path(guard.grid, guard.tile_pos(), player_tile)
        guard.last_known_player = player_tile

    def update(self, dt: float) -> None:
        from src.ai.states import SearchState  # local import avoids circular ref
        guard = self.owner

        # Lost sight → switch to SEARCH
        if not guard.vision.sees_player:
            guard.fsm.change(SearchState(guard))
            return

        # Re-plan periodically so guard turns corners to follow player
        self._replan_timer += dt
        if self._replan_timer >= self.REPLAN_INTERVAL:
            self._replan_timer = 0.0
            self._replan(guard)

        if self._path:
            next_col, next_row = self._path[0]
            arrived = _move_toward_tile(guard, next_col, next_row, dt)
            if arrived:
                self._path.pop(0)

    def exit(self) -> None:
        self._path = []


# ══════════════════════════════════════════════════════════════════════
# SEARCH  (implemented in Milestone 7)
# ══════════════════════════════════════════════════════════════════════

class SearchState(State):
    """Guard lost the player. Moves to last known tile and scans.

    Transitions
    -----------
    → ALERT   if the guard re-acquires the player during the search
    → PATROL  after SEARCH_DURATION seconds without a re-sighting
    """

    SEARCH_DURATION = 5.0   # seconds before giving up

    def enter(self) -> None:
        guard = self.owner
        self._timer = 0.0
        target = guard.last_known_player or guard.tile_pos()
        self._path = find_path(guard.grid, guard.tile_pos(), target)

    def update(self, dt: float) -> None:
        from src.ai.states import AlertState, PatrolState  # local to avoid circular
        guard = self.owner

        # Re-acquired the player → chase again
        if guard.vision.sees_player:
            guard.fsm.change(AlertState(guard))
            return

        self._timer += dt
        if self._timer >= self.SEARCH_DURATION:
            guard.fsm.change(PatrolState(guard))
            return

        if self._path:
            next_col, next_row = self._path[0]
            arrived = _move_toward_tile(guard, next_col, next_row, dt)
            if arrived:
                self._path.pop(0)

    def exit(self) -> None:
        self._path = []
