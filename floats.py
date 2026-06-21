"""floats.py — Floating text numbers and crop info tooltips for Solstice Farm."""

from __future__ import annotations

import pygame

from settings import CROPS, PAL, SCREEN_H, SCREEN_W, TILE_SIZE

T = TILE_SIZE


# =========================================================================
# Floating Numbers  (+15g, +35g, etc.)
# =========================================================================

class FloatingText:
    """A single piece of floating text that rises and fades out."""

    __slots__ = ("text", "color", "x", "y", "life", "max_life", "vy", "size")

    def __init__(self, text: str, x: float, y: float,
                 color: tuple[int, int, int] = (255, 220, 50),
                 life: float = 1.2, size: int = 26) -> None:
        self.text = text
        self.color = color
        self.x = x
        self.y = y
        self.life = life
        self.max_life = life
        self.vy = -45.0  # float upward speed
        self.size = size

    def update(self, dt: float) -> bool:
        """Returns False when dead."""
        self.life -= dt
        if self.life <= 0:
            return False
        self.y += self.vy * dt
        # Decelerate
        self.vy *= 0.97
        return True


class FloatingTextSystem:
    """Manages all active floating texts."""

    def __init__(self) -> None:
        self.texts: list[FloatingText] = []
        self._font_cache: dict[int, pygame.font.Font] = {}

    def _get_font(self, size: int) -> pygame.font.Font:
        if size not in self._font_cache:
            self._font_cache[size] = pygame.font.SysFont(None, size)
        return self._font_cache[size]

    def spawn(self, text: str, world_x: float, world_y: float,
              color: tuple[int, int, int] = (255, 220, 50),
              size: int = 26, life: float = 1.2) -> None:
        """Spawn floating text at a world position."""
        self.texts.append(FloatingText(text, world_x, world_y, color, life, size))

    def spawn_gold(self, amount: int, world_x: float, world_y: float) -> None:
        """Spawn a gold gain number."""
        self.spawn(f"+{amount}g", world_x, world_y,
                   color=(255, 220, 50), size=28)

    def spawn_info(self, text: str, world_x: float, world_y: float) -> None:
        """Spawn a small info text."""
        self.spawn(text, world_x, world_y,
                   color=(200, 240, 180), size=20, life=1.0)

    def update(self, dt: float) -> None:
        self.texts = [t for t in self.texts if t.update(dt)]

    def draw(self, surface: pygame.Surface, cam_ox: int, cam_oy: int) -> None:
        for ft in self.texts:
            alpha = max(0.0, min(1.0, ft.life / (ft.max_life * 0.4)))
            a = int(alpha * 255)

            font = self._get_font(ft.size)
            ts = font.render(ft.text, True, ft.color)
            ts.set_alpha(a)

            sx = int(ft.x) + cam_ox - ts.get_width() // 2
            sy = int(ft.y) + cam_oy
            surface.blit(ts, (sx, sy))


# =========================================================================
# Crop Info Tooltip (shown when player faces a crop)
# =========================================================================

class CropTooltip:
    """Draws a small info panel showing crop status near the cursor."""

    def __init__(self) -> None:
        self.font_name = pygame.font.SysFont(None, 22)
        self.font_info = pygame.font.SysFont(None, 18)

    def draw(self, surface: pygame.Surface, crop, tile_col: int,
             tile_row: int, cam_ox: int, cam_oy: int,
             is_golden_hour: bool = False) -> None:
        """Draw tooltip above the crop tile.

        Args:
            crop: A Crop instance from farming.py
            tile_col, tile_row: Tile position
            cam_ox, cam_oy: Camera offsets
        """
        if crop is None:
            return

        data = crop.data
        name = data["name"]

        # Build info lines
        lines: list[tuple[str, tuple[int, int, int]]] = []

        # Name
        lines.append((name, PAL["text_gold"]))

        # Progress bar text
        if crop.ready:
            lines.append(("✨ Ready to harvest!", (100, 255, 80)))
        else:
            pct = int(crop.progress * 100)
            lines.append((f"Growth: {pct}%", PAL["text_light"]))

        # Water status
        if crop.needs_water and not crop.ready:
            lines.append(("💧 Needs water!", (80, 160, 240)))
        elif not crop.ready:
            remaining = crop.water_needed - crop.times_watered
            if remaining > 0:
                lines.append((f"Waters left: {remaining}", PAL["text_dim"]))

        # Solstice info
        if crop.is_solstice_only:
            from farming import get_sun_multiplier
            # This is a bit of a hack but the tooltip doesn't have tf
            lines.append(("☀ Needs peak sun to grow", (200, 140, 255)))

        # Sell value
        value = data["sell_price"]
        if is_golden_hour:
            lines.append((f"Value: {value * 2}g (2x Golden!)", (255, 220, 50)))
        else:
            lines.append((f"Value: {value}g", PAL["text_dim"]))

        # Calculate panel size
        line_h = 18
        pad = 8
        panel_w = 160
        panel_h = pad * 2 + len(lines) * line_h + 8

        # Position: above the tile
        sx = tile_col * T + cam_ox + T // 2 - panel_w // 2
        sy = tile_row * T + cam_oy - panel_h - 4

        # Clamp to screen
        sx = max(4, min(SCREEN_W - panel_w - 4, sx))
        sy = max(4, sy)

        # Draw panel
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((15, 25, 18, 220))
        surface.blit(panel, (sx, sy))
        pygame.draw.rect(surface, PAL["accent"],
                         (sx, sy, panel_w, panel_h), 1, border_radius=4)

        # Draw progress bar
        if not crop.ready:
            bar_x = sx + pad
            bar_y = sy + pad + line_h + 2
            bar_w = panel_w - pad * 2
            bar_h = 6

            pygame.draw.rect(surface, (40, 40, 40),
                             (bar_x, bar_y, bar_w, bar_h), border_radius=3)
            fill_w = int(bar_w * crop.progress)
            if fill_w > 0:
                bar_color = PAL["accent"] if not crop.is_solstice_only else (180, 120, 255)
                pygame.draw.rect(surface, bar_color,
                                 (bar_x, bar_y, fill_w, bar_h), border_radius=3)

        # Draw text lines
        for i, (text, color) in enumerate(lines):
            font = self.font_name if i == 0 else self.font_info
            ts = font.render(text, True, color)
            ty = sy + pad + i * line_h
            if i > 0 and not crop.ready:
                ty += 8  # shift down after progress bar
            surface.blit(ts, (sx + pad, ty))


# =========================================================================
# Tile Tooltip (for non-crop tiles like shop, well, etc.)
# =========================================================================

class TileTooltip:
    """Shows contextual hints for interactive tiles."""

    def __init__(self) -> None:
        self.font = pygame.font.SysFont(None, 20)

    def get_hint(self, tile_type: int, tool: str) -> str | None:
        """Return a hint string for the given tile and tool, or None."""
        from settings import (
            TILE_DIRT, TILE_TILLED, TILE_WATERED, TILE_WATER,
            TILE_SHOP, TILE_PLANTED,
        )

        if tile_type == TILE_DIRT:
            if tool == "hoe":
                return "Press SPACE to till"
            return "Use Hoe (1) to till"

        if tile_type == TILE_TILLED:
            if tool == "water_can":
                return "Press SPACE to water"
            if tool == "seeds":
                return "Must water soil first!"
            return "Use Water Can (2) to water"

        if tile_type == TILE_WATERED:
            if tool == "seeds":
                return "Press SPACE to plant"
            return "Ready to plant! (3)"

        if tile_type == TILE_WATER:
            if tool == "water_can":
                return "Press SPACE to refill"
            return "Use Water Can (2) to refill"

        if tile_type == TILE_SHOP:
            return "Press TAB to shop"

        return None

    def draw(self, surface: pygame.Surface, text: str,
             tile_col: int, tile_row: int,
             cam_ox: int, cam_oy: int) -> None:
        """Draw a small hint above a tile."""
        ts = self.font.render(text, True, (220, 220, 200))
        tw = ts.get_width()

        sx = tile_col * T + cam_ox + T // 2 - tw // 2
        sy = tile_row * T + cam_oy - 24

        # Clamp
        sx = max(4, min(SCREEN_W - tw - 4, sx))
        sy = max(4, sy)

        # Background
        bg = pygame.Surface((tw + 12, ts.get_height() + 6), pygame.SRCALPHA)
        bg.fill((10, 20, 15, 180))
        surface.blit(bg, (sx - 6, sy - 3))

        surface.blit(ts, (sx, sy))
