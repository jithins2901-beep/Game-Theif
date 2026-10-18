"""Generic Finite State Machine.

This FSM is completely decoupled from the game — it knows nothing about
guards, players, or pygame. It just manages which state is active and
calls enter/update/exit at the right times.

Why a class-based FSM instead of if/elif chains?
-------------------------------------------------
With if/elif you end up with one giant function that does everything.
Adding a new state means editing that function and risking breaking others.
With this FSM, each state is its own class with three clean methods:
  - enter()  : called once when we switch INTO this state
  - update() : called every frame while this state is active
  - exit()   : called once when we switch OUT of this state

Adding a new state = writing a new class. Existing states don't change.
This is the Open/Closed principle and it's great to show in a viva.
"""


class State:
    """Base class for all FSM states. Override enter/update/exit."""

    def __init__(self, owner) -> None:
        # owner is the Guard that owns this state machine
        self.owner = owner

    def enter(self) -> None:
        """Called once when this state becomes active."""

    def update(self, dt: float) -> None:
        """Called every frame while this state is active."""

    def exit(self) -> None:
        """Called once just before switching to a different state."""

    @property
    def name(self) -> str:
        """Human-readable name shown in the HUD."""
        return self.__class__.__name__.replace("State", "").upper()


class StateMachine:
    """Holds a current state and handles transitions.

    Usage
    -----
        fsm = StateMachine(PatrolState(guard))
        fsm.update(dt)          # every frame
        fsm.change(AlertState(guard))   # when a trigger fires
    """

    def __init__(self, initial_state: State) -> None:
        self.current: State = initial_state
        self.current.enter()

    def change(self, new_state: State) -> None:
        """Transition to a new state cleanly."""
        self.current.exit()
        self.current = new_state
        self.current.enter()

    def update(self, dt: float) -> None:
        self.current.update(dt)

    @property
    def state_name(self) -> str:
        return self.current.name
