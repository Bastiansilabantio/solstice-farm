"""player.py — Player character for Solstice Farm.

Handles movement, animation, direction facing, tool usage, and
collision with the tile map.
"""

from __future__ import annotations

import pygame

from settings import (
    CROP_TYPES, MAP_COLS, MAP_ROWS,
    PLAYER_SPEED, TILE_SIZE,
    TOOL_HANDS, TOOL_HOE, TOOL_SEEDS, TOOL_WATER,
    TOOLS_LIST, WATER_CAN_MAX, WATER_CAN_START,
)
from sprites import DIR_DOWN, DIR_LEFT, DIR_RIGHT, DIR_UP, get_player_frames

T = TILE_SIZE


class Player:
    """Top-down player character."""

    def __init__(self, start_col: int, start_row: int) -> None:
        # Position in world pixels (top-left of 32×32 bounding box)
        self.x: float = start_col * T
        self.y: float = start_row * T

        # Size for collision
        self.w: int = 20   # narrower than a tile for easier navigation
        self.h: int = 12   # short hitbox at feet level
        self.foot_offset_x: int = 6   # offset from sprite left to hitbox left
        self.foot_offset_y: int = 20  # offset from sprite top to hitbox top

        # Direction / animation
        self.direction: int = DIR_DOWN
        self.anim_timer: float = 0.0
        self.anim_frame: int = 0   # 0=idle, 1=walk1, 2=walk2
        self.moving: bool = False

        # Tools
        self.tool_index: int = 0
        self.selected_seed: int = 0  # index into CROP_TYPES

        # Water can
        self.water: int = WATER_CAN_START
        self.water_max: int = WATER_CAN_MAX

        # Action cooldown (prevents rapid-fire actions)
        self.action_cooldown: float = 0.0
        self.ACTION_DELAY: float = 0.25  # seconds

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def current_tool(self) -> str:
        return TOOLS_LIST[self.tool_index]

    @property
    def current_seed_type(self) -> str:
        return CROP_TYPES[self.selected_seed % len(CROP_TYPES)]

    @property
    def center_x(self) -> float:
        return self.x + T / 2

    @property
    def center_y(self) -> float:
        return self.y + T / 2

    @property
    def tile_col(self) -> int:
        return int(self.center_x // T)

    @property
    def tile_row(self) -> int:
        return int(self.center_y // T)

    @property
    def foot_rect(self) -> pygame.Rect:
        """Collision rect at the player's feet."""
        return pygame.Rect(
            int(self.x) + self.foot_offset_x,
            int(self.y) + self.foot_offset_y,
            self.w, self.h,
        )

    def facing_tile(self) -> tuple[int, int]:
        """Return the (col, row) of the tile the player is facing."""
        col, row = self.tile_col, self.tile_row
        if self.direction == DIR_UP:
            row -= 1
        elif self.direction == DIR_DOWN:
            row += 1
        elif self.direction == DIR_LEFT:
            col -= 1
        elif self.direction == DIR_RIGHT:
            col += 1
        return col, row

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Process key events. Returns action string or None.

        Possible return values:
            'use_tool'  — player pressed space to use tool
            'cycle_seed' — player pressed Q/E to change seed type
            None
        """
        if event.type == pygame.KEYDOWN:
            # Tool selection (number keys)
            if event.key == pygame.K_1:
                self.tool_index = 0
            elif event.key == pygame.K_2:
                self.tool_index = 1
            elif event.key == pygame.K_3:
                self.tool_index = 2
            elif event.key == pygame.K_4:
                self.tool_index = 3

            # Use tool
            elif event.key == pygame.K_SPACE:
                if self.action_cooldown <= 0:
                    self.action_cooldown = self.ACTION_DELAY
                    return "use_tool"

            # Cycle seed type
            elif event.key == pygame.K_q:
                self.selected_seed = (self.selected_seed - 1) % len(CROP_TYPES)
                return "cycle_seed"
            elif event.key == pygame.K_e:
                self.selected_seed = (self.selected_seed + 1) % len(CROP_TYPES)
                return "cycle_seed"

        return None

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float, is_solid_fn) -> None:
        """Move the player based on held keys; collide with solid tiles."""
        self.action_cooldown = max(0.0, self.action_cooldown - dt)

        keys = pygame.key.get_pressed()
        dx, dy = 0.0, 0.0
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= 1
            self.direction = DIR_UP
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += 1
            self.direction = DIR_DOWN
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= 1
            self.direction = DIR_LEFT
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += 1
            self.direction = DIR_RIGHT

        self.moving = dx != 0 or dy != 0

        # Normalize diagonal
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071

        speed = PLAYER_SPEED * dt

        # Move X, check collision
        new_x = self.x + dx * speed
        new_rect = pygame.Rect(
            int(new_x) + self.foot_offset_x,
            int(self.y) + self.foot_offset_y,
            self.w, self.h,
        )
        if not self._collides(new_rect, is_solid_fn):
            self.x = new_x
        else:
            # Try sliding along walls
            pass

        # Move Y, check collision
        new_y = self.y + dy * speed
        new_rect = pygame.Rect(
            int(self.x) + self.foot_offset_x,
            int(new_y) + self.foot_offset_y,
            self.w, self.h,
        )
        if not self._collides(new_rect, is_solid_fn):
            self.y = new_y

        # Clamp to world bounds
        self.x = max(0, min(self.x, (MAP_COLS - 1) * T))
        self.y = max(0, min(self.y, (MAP_ROWS - 1) * T))

        # Animation
        if self.moving:
            self.anim_timer += dt
            if self.anim_timer >= 0.12:
                self.anim_timer = 0.0
                # Cycle through walk frames (1 .. N-1), skip frame 0 (idle)
                frames = get_player_frames(self.direction)
                num_frames = len(frames)
                if num_frames <= 3:
                    # Classic 3-frame: alternate between 1 and 2
                    self.anim_frame = 1 if self.anim_frame != 1 else 2
                else:
                    # 4+ frames: cycle 1 → 2 → ... → N-1 → 1
                    self.anim_frame += 1
                    if self.anim_frame >= num_frames:
                        self.anim_frame = 1
        else:
            self.anim_frame = 0
            self.anim_timer = 0.0

    def _collides(self, rect: pygame.Rect, is_solid_fn) -> bool:
        """Check if the rect overlaps any solid tile."""
        # Check corners and midpoints of the rect
        points = [
            (rect.left, rect.top),
            (rect.right - 1, rect.top),
            (rect.left, rect.bottom - 1),
            (rect.right - 1, rect.bottom - 1),
            (rect.centerx, rect.top),
            (rect.centerx, rect.bottom - 1),
        ]
        for px, py in points:
            col = px // T
            row = py // T
            if is_solid_fn(col, row):
                return True
        return False

    def refill_water(self) -> bool:
        """Refill the water can. Returns True if not already full."""
        if self.water < self.water_max:
            self.water = self.water_max
            return True
        return False

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface, cam_ox: int, cam_oy: int) -> None:
        frames = get_player_frames(self.direction)
        frame_idx = min(self.anim_frame, len(frames) - 1)
        sprite = frames[frame_idx]

        screen_x = int(self.x) + cam_ox
        screen_y = int(self.y) + cam_oy
        # Offset upward so character feet align with tile position
        sprite_h = sprite.get_height()
        draw_y = screen_y + T - sprite_h
        surface.blit(sprite, (screen_x, draw_y))

        # Draw facing indicator (subtle)
        fc, fr = self.facing_tile()
        ind_x = fc * T + cam_ox
        ind_y = fr * T + cam_oy
        indicator = pygame.Surface((T, T), pygame.SRCALPHA)
        pygame.draw.rect(indicator, (255, 255, 255, 35), (0, 0, T, T), 2,
                         border_radius=4)
        surface.blit(indicator, (ind_x, ind_y))
