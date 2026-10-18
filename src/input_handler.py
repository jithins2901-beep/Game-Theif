"""Input handler: translates keyboard state into a movement intent.

Keeping input reading in one place means the Player class never calls
pygame.key.get_pressed() directly. This makes the player logic portable
and unit-testable — you can inject a fake intent dict in tests.

Returns a dict with keys:  dx, dy  (-1, 0, or +1 each).
"""

import pygame


def get_movement_intent() -> dict:
    """Read currently held keys and return a normalised direction.

    WASD and arrow keys are both supported.

    Returns
    -------
    {"dx": int, "dy": int}
        Each value is -1, 0, or +1.
    """
    keys = pygame.key.get_pressed()

    dx = 0
    dy = 0

    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        dx = -1
    elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        dx = 1

    if keys[pygame.K_UP] or keys[pygame.K_w]:
        dy = -1
    elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
        dy = 1

    return {"dx": dx, "dy": dy}
