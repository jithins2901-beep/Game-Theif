"""Guard entity.

The guard owns:
  - A StateMachine (FSM) that decides behaviour each frame
  - A VisionCone that computes FOV and detection each frame
  - A list of patrol waypoints (tile positions)
  - A facing angle (radians) — updated by movement
  - A reference to the grid (for pathfinding)
  - A speed value (scaled by difficulty in Milestone 9)

Detection trigger (the heart of Milestone 7)
--------------------------------------------
The guard's update() is the ONLY place that fires FSM transitions based
on vision. States themselves (Alert, Search, Suspicious) can also trigger
transitions when timers expire or vision changes mid-state — but the
PATROL → SUSPICIOUS trigger lives here so it is easy to find and tune.

State machine diagram:

        sees player
  PATROL ──────────► SUSPICIOUS ──────────► ALERT
    ▲                    │  sees player        │
    │     timer runs out │                     │ loses sight
    └────────────────────┘      ┌──────────────┘
                                ▼
                              SEARCH
                                │ timer runs out OR re-sees player
                                ├──────────────────────────────► ALERT
                                └──────────────────────────────► PATROL
"""

from config import TILE_SIZE
from src.ai.fsm import StateMachine
from src.ai.states import PatrolState, SuspiciousState
from src.ai.vision import VisionCone
from src.entities.entity import Entity

GUARD_SIZE = 22
GUARD_DEFAULT_SPEED = 70   # pixels/second (player is 120)


class Guard(Entity):
    def __init__(
        self,
        col: int,
        row: int,
        patrol_waypoints: list[tuple[int, int]],
        grid,
        game,
    ) -> None:
        super().__init__(col, row, GUARD_SIZE)

        self.patrol_waypoints = patrol_waypoints
        self.grid = grid
        self.game = game
        self.speed = GUARD_DEFAULT_SPEED
        self.waypoint_index = 0
        self.facing_angle: float = 0.0

        self.last_known_player: tuple[int, int] | None = None

        self.vision = VisionCone(grid)
        self.fsm = StateMachine(PatrolState(self))

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float, player=None) -> None:
        """Update vision, fire detection transitions, then step the FSM."""

        # ── 1. Recompute vision cone ───────────────────────────────────
        if player is not None:
            self.vision.update(self, player)
            if self.vision.sees_player:
                self.last_known_player = player.tile_pos()

        # ── 2. Detection trigger: PATROL → SUSPICIOUS ─────────────────
        # Only fire this transition here; all other transitions are owned
        # by the states themselves (SuspiciousState, AlertState, etc.).
        if (
            self.state_name == "PATROL"
            and player is not None
            and self.vision.sees_player
        ):
            self.fsm.change(SuspiciousState(self))

        # ── 3. Step the active state ───────────────────────────────────
        self.fsm.update(dt)

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    @property
    def state_name(self) -> str:
        return self.fsm.state_name

    @property
    def can_see_player(self) -> bool:
        return self.vision.sees_player
