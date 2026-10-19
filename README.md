# Stealth Heist

A 2D top-down stealth and heist game with AI-driven guards (finite state
machine, field-of-view vision cone, A* pathfinding). Built with Python and
Pygame.

## Requirements

- Python 3.10+ (developed on Python 3.14)
- pygame-ce 2.5.8 (Community Edition of pygame — drop-in `import pygame`)

> Why pygame-ce and not pygame? The classic `pygame` package's last release
> (Sept 2024) predates Python 3.14 and has no cp314 wheel, so installing it on
> Python 3.14 tries to build from source and fails (`distutils.msvccompiler`
> was removed). `pygame-ce` is a drop-in fork maintained by the original pygame
> team and ships cp314 wheels. All code uses plain `import pygame`, so it
> works with either package on supported Python versions.

## Setup (one time)

Run these in a terminal from the project root (`Game theif`):

```powershell
# 1. Create a virtual environment
python -m venv .venv

# 2. Activate it (PowerShell)
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> If PowerShell blocks the activation script, run:
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

## Run

```powershell
# Make sure the venv is activated, then:
python main.py
```

## Controls

- `WASD` / Arrow keys — move player
- `R` — restart
- `ESC` — quit

## Project layout

```
main.py            Entry point
config.py          Tunable constants (sizes, speeds, colors)
requirements.txt   Dependencies
src/core/          Game loop, grid, level
src/entities/      Player, Guard
src/ai/            FSM, states, pathfinding, vision, difficulty
src/ui/            Renderer, HUD
```

## Milestones

- [x] 1. Project setup + window + fixed-timestep loop
- [x] 2. Grid + level + rendering of walls / floor / exit
- [x] 3. Player movement + wall collision
- [x] 4. Guard + FSM scaffold + PATROL state
- [x] 5. Vision cone (FOV)
- [x] 6. A* pathfinding
- [x] 7. Full detection loop (SUSPICIOUS / ALERT / SEARCH)
- [x] 8. Win / lose / restart + HUD messages
- [ ] 9. Difficulty system + polish
