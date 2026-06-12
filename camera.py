"""camera.py — 2D camera that follows the player with smooth lerp."""

import pygame

from settings import MAP_COLS, MAP_ROWS, SCREEN_H, SCREEN_W, TILE_SIZE


class Camera:
    """Viewport that smoothly tracks a target position."""

    def __init__(self) -> None:
        self.x: float = 0.0
        self.y: float = 0.0
        self.lerp_speed: float = 5.0  # higher = snappier follow

        self.world_w = MAP_COLS * TILE_SIZE
        self.world_h = MAP_ROWS * TILE_SIZE

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update(self, target_x: float, target_y: float, dt: float) -> None:
        """Move toward *target* (player centre) with lerp smoothing."""
        goal_x = target_x - SCREEN_W / 2
        goal_y = target_y - SCREEN_H / 2

        t = min(1.0, self.lerp_speed * dt)
        self.x += (goal_x - self.x) * t
        self.y += (goal_y - self.y) * t

        # Clamp so the camera never shows outside the map.
        self.x = max(0, min(self.x, self.world_w - SCREEN_W))
        self.y = max(0, min(self.y, self.world_h - SCREEN_H))

    def apply(self, rect: pygame.Rect) -> pygame.Rect:
        """Return *rect* shifted by the camera offset (for drawing)."""
        return rect.move(-int(self.x), -int(self.y))

    def apply_pos(self, x: float, y: float) -> tuple[int, int]:
        """Return a world position shifted by the camera offset."""
        return int(x - self.x), int(y - self.y)

    def screen_to_world(self, sx: int, sy: int) -> tuple[float, float]:
        """Convert a screen position to world coordinates."""
        return sx + self.x, sy + self.y

    @property
    def offset(self) -> tuple[int, int]:
        return -int(self.x), -int(self.y)
