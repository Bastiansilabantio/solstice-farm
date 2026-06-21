"""hud.py — Heads-up display overlay for Solstice Farm."""

from __future__ import annotations

import math

import pygame

from inventory import Inventory
from player import Player
from settings import (
    CROPS, CROP_TYPES, DAY_DURATION, PAL, SCREEN_H, SCREEN_W,
    TOOL_HANDS, TOOL_HOE, TOOL_SEEDS, TOOL_WATER,
    TOOL_NAMES, TOOLS_LIST,
)
from sprites import get_icon

# Bar dimensions
TOP_H = 56
BOT_H = 52
BAR_W = 280
BAR_H = 14


class HUD:
    """Draws toolbar, sun timer, money, and contextual info."""

    def __init__(self) -> None:
        self.font_label = pygame.font.SysFont(None, 20)
        self.font_value = pygame.font.SysFont(None, 28)
        self.font_tool = pygame.font.SysFont(None, 22)
        self.font_hint = pygame.font.SysFont(None, 20)

        # Toolbar icon rects (bottom bar)
        self.tool_rects: list[pygame.Rect] = []
        tool_y = SCREEN_H - BOT_H + 8
        start_x = 16
        for i in range(len(TOOLS_LIST)):
            self.tool_rects.append(
                pygame.Rect(start_x + i * 46, tool_y, 38, 38)
            )

    # ------------------------------------------------------------------
    # Click handling
    # ------------------------------------------------------------------

    def handle_click(self, pos: tuple[int, int], player: Player) -> bool:
        """Check if user clicked a toolbar icon. Returns True if consumed."""
        for i, rect in enumerate(self.tool_rects):
            if rect.collidepoint(pos):
                player.tool_index = i
                return True
        return False

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface, player: Player,
             inventory: Inventory, time_fraction: float) -> None:
        self._draw_top_bar(surface, inventory, time_fraction)
        self._draw_bottom_bar(surface, player, inventory)

    # ---- Top bar -------------------------------------------------------

    def _draw_top_bar(self, surface: pygame.Surface,
                      inventory: Inventory, tf: float) -> None:
        # Semi-transparent strip
        strip = pygame.Surface((SCREEN_W, TOP_H), pygame.SRCALPHA)
        strip.fill((10, 15, 10, 200))
        surface.blit(strip, (0, 0))

        # --- Sun timer bar (centre) ---
        bar_x = (SCREEN_W - BAR_W) // 2
        bar_y = 18

        label = self.font_label.render("☀ Solstice Sunlight", True,
                                       (200, 185, 100))
        surface.blit(label, (bar_x, 2))

        # Background track
        pygame.draw.rect(surface, (38, 38, 38),
                         (bar_x, bar_y, BAR_W, BAR_H), border_radius=5)

        # Fill (decreases as time passes)
        fill = max(0.0, min(1.0, 1.0 - tf))
        fill_w = int(BAR_W * fill)

        if fill > 0.5:
            color = (240, 200, 40)
        elif fill > 0.25:
            color = (230, 130, 30)
        else:
            color = (210, 50, 35)

        if fill_w > 0:
            pygame.draw.rect(surface, color,
                             (bar_x, bar_y, fill_w, BAR_H), border_radius=5)

        # Track outline
        pygame.draw.rect(surface, (80, 80, 80),
                         (bar_x, bar_y, BAR_W, BAR_H), 1, border_radius=5)

        # Sun icon riding the edge
        sun_cx = max(bar_x + 6, min(bar_x + BAR_W - 6, bar_x + fill_w))
        sun_cy = bar_y + BAR_H // 2
        pygame.draw.circle(surface, (255, 235, 80), (sun_cx, sun_cy), 7)
        pygame.draw.circle(surface, (255, 200, 0), (sun_cx, sun_cy), 7, 2)

        # Time remaining text
        remaining = max(0, DAY_DURATION * (1.0 - tf))
        mins = int(remaining) // 60
        secs = int(remaining) % 60
        time_s = self.font_label.render(f"{mins}:{secs:02d}", True,
                                        PAL["text_dim"])
        surface.blit(time_s, (bar_x + BAR_W + 8, bar_y))

        # --- Money (left) ---
        money_s = self.font_value.render(f"Gold: {inventory.money}g", True,
                                         PAL["text_gold"])
        surface.blit(money_s, (16, 10))

        # --- Water (right) ---
        water_s = self.font_value.render(
            f"💧 {inventory._player_water}/{inventory._player_water_max}"
            if hasattr(inventory, '_player_water') else "",
            True, PAL["water_blue"]
        )
        # We'll show water from draw call instead
        pass

    def draw_stats(self, surface: pygame.Surface, player: Player) -> None:
        """Draw water and energy count on top bar (called separately with player data)."""
        # Water
        water_s = self.font_value.render(f"Water: {player.water}/{player.water_max}", True,
                                         PAL["water_blue"])
        surface.blit(water_s, (SCREEN_W - water_s.get_width() - 16, 10))

        # Energy Bar
        energy_pct = max(0.0, player.energy / player.energy_max)
        bar_w = 120
        bar_h = 12
        bx = SCREEN_W - bar_w - 16
        by = 38

        pygame.draw.rect(surface, (50, 50, 50), (bx, by, bar_w, bar_h), border_radius=4)
        if energy_pct > 0:
            color = (255, 220, 50) if energy_pct > 0.25 else (220, 50, 50)
            pygame.draw.rect(surface, color, (bx, by, int(bar_w * energy_pct), bar_h), border_radius=4)
        pygame.draw.rect(surface, (100, 100, 100), (bx, by, bar_w, bar_h), 1, border_radius=4)

        eng_label = self.font_label.render("Energy:", True, (255, 220, 50))
        surface.blit(eng_label, (bx - eng_label.get_width() - 6, by - 2))

    # ---- Bottom bar ----------------------------------------------------

    def _draw_bottom_bar(self, surface: pygame.Surface, player: Player,
                         inventory: Inventory) -> None:
        # Semi-transparent strip
        strip = pygame.Surface((SCREEN_W, BOT_H), pygame.SRCALPHA)
        strip.fill((10, 15, 10, 210))
        surface.blit(strip, (0, SCREEN_H - BOT_H))

        # Tool icons
        tool_icons = ["hoe", "water_can", "seeds", "hands"]
        for i, rect in enumerate(self.tool_rects):
            selected = i == player.tool_index
            # Background
            bg = PAL["accent"] if selected else (40, 55, 40)
            pygame.draw.rect(surface, bg, rect, border_radius=6)
            border_c = PAL["accent_bright"] if selected else (70, 85, 70)
            pygame.draw.rect(surface, border_c, rect, 2, border_radius=6)

            # Icon
            icon = get_icon(tool_icons[i])
            ix = rect.x + (rect.width - icon.get_width()) // 2
            iy = rect.y + (rect.height - icon.get_height()) // 2
            surface.blit(icon, (ix, iy))

            # Hotkey number
            num = self.font_label.render(str(i + 1), True, PAL["text_dim"])
            surface.blit(num, (rect.x + 2, rect.y + 1))

        # Selected tool label
        tool_name = TOOL_NAMES[player.current_tool]
        extra = ""
        if player.current_tool == TOOL_SEEDS:
            seed_name = CROPS[player.current_seed_type]["name"]
            count = inventory.seeds.get(player.current_seed_type, 0)
            extra = f" ({seed_name} ×{count})  [Q/E switch]"
        elif player.current_tool == TOOL_WATER:
            extra = f" ({player.water}/{player.water_max})"

        label = self.font_tool.render(f"Tool: {tool_name}{extra}", True,
                                      PAL["text_light"])
        surface.blit(label, (210, SCREEN_H - BOT_H + 16))

        # Controls hint (right side)
        hint = self.font_hint.render("WASD:Move  Space:Use  TAB:Shop  1-4:Tool",
                                     True, PAL["text_dim"])
        surface.blit(hint, (SCREEN_W - hint.get_width() - 12,
                            SCREEN_H - BOT_H + 32))

    # ------------------------------------------------------------------
    # Floating messages
    # ------------------------------------------------------------------

    @staticmethod
    def draw_message(surface: pygame.Surface, text: str,
                     alpha: float) -> None:
        """Draw a centred floating message with fade."""
        font = pygame.font.SysFont(None, 32)
        a = max(0, min(255, int(alpha * 255)))
        ts = font.render(text, True, PAL["text_gold"])
        ts.set_alpha(a)
        x = (SCREEN_W - ts.get_width()) // 2
        y = SCREEN_H // 2 - 60
        surface.blit(ts, (x, y))
