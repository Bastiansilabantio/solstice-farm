"""shop.py — Shop overlay UI for Solstice Farm."""

from __future__ import annotations

import pygame

from inventory import Inventory
from settings import (
    CROPS, CROP_TYPES, GOLDEN_HOUR_END, GOLDEN_HOUR_START,
    PAL, SCREEN_H, SCREEN_W,
)
from sounds import play as play_sfx
from sprites import get_icon


class Shop:
    """Simple buy/sell shop overlay."""

    PANEL_W = 520
    PANEL_H = 480
    ROW_H = 40
    BTN_W = 70
    BTN_H = 28

    def __init__(self) -> None:
        self.is_open: bool = False
        self.tab: str = "buy"  # "buy" or "sell"
        self.sell_multiplier: float = 1.0  # set by game for golden hour

        self.px = (SCREEN_W - self.PANEL_W) // 2
        self.py = (SCREEN_H - self.PANEL_H) // 2

        self.font_title = pygame.font.SysFont(None, 36)
        self.font_item = pygame.font.SysFont(None, 26)
        self.font_btn = pygame.font.SysFont(None, 22)
        self.font_tab = pygame.font.SysFont(None, 28)

        # Tab rects
        tw = self.PANEL_W // 2
        self.tab_buy_rect = pygame.Rect(self.px, self.py - 34, tw, 34)
        self.tab_sell_rect = pygame.Rect(self.px + tw, self.py - 34, tw, 34)

        # Close button
        self.close_rect = pygame.Rect(
            self.px + self.PANEL_W - 32, self.py + 4, 28, 28
        )

    def open(self) -> None:
        self.is_open = True

    def close(self) -> None:
        self.is_open = False

    def toggle(self) -> None:
        self.is_open = not self.is_open

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event,
                     inventory: Inventory) -> bool:
        """Handle click events. Returns True if event was consumed."""
        if not self.is_open:
            return False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
            return True
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return False

        pos = event.pos

        # Close button
        if self.close_rect.collidepoint(pos):
            self.close()
            return True

        # Tab switch
        if self.tab_buy_rect.collidepoint(pos):
            self.tab = "buy"
            return True
        if self.tab_sell_rect.collidepoint(pos):
            self.tab = "sell"
            return True

        # Item buttons
        if self.tab == "buy":
            for i, crop_key in enumerate(CROP_TYPES):
                btn_rect = self._buy_btn_rect(i)
                if btn_rect.collidepoint(pos):
                    if inventory.buy_seeds(crop_key, 1):
                        play_sfx("coin")
                    return True
                # Buy 5 button
                btn5_rect = self._buy5_btn_rect(i)
                if btn5_rect.collidepoint(pos):
                    if inventory.buy_seeds(crop_key, 5):
                        play_sfx("coin")
                    return True
        else:
            for i, crop_key in enumerate(CROP_TYPES):
                btn_rect = self._sell_btn_rect(i)
                if btn_rect.collidepoint(pos):
                    if inventory.sell_crop(crop_key, 1, self.sell_multiplier):
                        play_sfx("coin")
                    return True
                # Sell all button
                btn_all_rect = self._sell_all_btn_rect(i)
                if btn_all_rect.collidepoint(pos):
                    count = inventory.get_harvest_count(crop_key)
                    if count > 0:
                        inventory.sell_crop(crop_key, count, self.sell_multiplier)
                        play_sfx("coin")
                    return True

        return True  # consume click even if nothing hit

    # ------------------------------------------------------------------
    # Layout helpers
    # ------------------------------------------------------------------

    def _row_y(self, i: int) -> int:
        return self.py + 60 + i * self.ROW_H

    def _buy_btn_rect(self, i: int) -> pygame.Rect:
        return pygame.Rect(
            self.px + self.PANEL_W - self.BTN_W - 90,
            self._row_y(i) + 6,
            self.BTN_W, self.BTN_H,
        )

    def _buy5_btn_rect(self, i: int) -> pygame.Rect:
        return pygame.Rect(
            self.px + self.PANEL_W - self.BTN_W - 12,
            self._row_y(i) + 6,
            self.BTN_W, self.BTN_H,
        )

    def _sell_btn_rect(self, i: int) -> pygame.Rect:
        return pygame.Rect(
            self.px + self.PANEL_W - self.BTN_W - 90,
            self._row_y(i) + 6,
            self.BTN_W, self.BTN_H,
        )

    def _sell_all_btn_rect(self, i: int) -> pygame.Rect:
        return pygame.Rect(
            self.px + self.PANEL_W - self.BTN_W - 12,
            self._row_y(i) + 6,
            self.BTN_W, self.BTN_H,
        )

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface, inventory: Inventory) -> None:
        if not self.is_open:
            return

        # Dim overlay
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        surface.blit(overlay, (0, 0))

        # Panel background
        panel = pygame.Surface((self.PANEL_W, self.PANEL_H), pygame.SRCALPHA)
        panel.fill((25, 35, 30, 240))
        surface.blit(panel, (self.px, self.py))
        pygame.draw.rect(surface, PAL["accent"],
                         (self.px, self.py, self.PANEL_W, self.PANEL_H), 2,
                         border_radius=6)

        # Tabs
        for tab_name, rect in [("buy", self.tab_buy_rect),
                                ("sell", self.tab_sell_rect)]:
            active = self.tab == tab_name
            color = PAL["accent"] if active else (50, 60, 50)
            pygame.draw.rect(surface, color, rect, border_radius=4)
            pygame.draw.rect(surface, PAL["accent"], rect, 1, border_radius=4)
            label = "BUY SEEDS" if tab_name == "buy" else "SELL CROPS"
            text_c = PAL["text_light"] if active else PAL["text_dim"]
            ts = self.font_tab.render(label, True, text_c)
            surface.blit(ts, (rect.centerx - ts.get_width() // 2,
                              rect.centery - ts.get_height() // 2))

        # Title & money
        title = "SHOP"
        ts = self.font_title.render(title, True, PAL["text_gold"])
        surface.blit(ts, (self.px + 16, self.py + 12))

        money_s = self.font_item.render(f"Gold: {inventory.money}g", True,
                                        PAL["text_gold"])
        surface.blit(money_s, (self.px + self.PANEL_W - money_s.get_width() - 48,
                               self.py + 18))

        # Close button
        pygame.draw.rect(surface, (180, 50, 40), self.close_rect, border_radius=4)
        xs = self.font_btn.render("X", True, PAL["text_light"])
        surface.blit(xs, (self.close_rect.centerx - xs.get_width() // 2,
                          self.close_rect.centery - xs.get_height() // 2))

        # Divider
        pygame.draw.line(surface, (60, 80, 60),
                         (self.px + 10, self.py + 50),
                         (self.px + self.PANEL_W - 10, self.py + 50), 1)

        # Items
        if self.tab == "buy":
            self._draw_buy_tab(surface, inventory)
        else:
            self._draw_sell_tab(surface, inventory)

    def _draw_buy_tab(self, surface: pygame.Surface,
                      inventory: Inventory) -> None:
        for i, crop_key in enumerate(CROP_TYPES):
            data = CROPS[crop_key]
            ry = self._row_y(i)

            # Icon
            icon = get_icon(f"seed_{crop_key}")
            surface.blit(icon, (self.px + 14, ry + 8))

            # Name
            name_s = self.font_item.render(data["name"], True, PAL["text_light"])
            surface.blit(name_s, (self.px + 44, ry + 6))

            # Cost
            cost_s = self.font_btn.render(f"{data['seed_cost']}g", True,
                                          PAL["text_gold"])
            surface.blit(cost_s, (self.px + 44, ry + 24))

            # Owned count
            owned = inventory.seeds.get(crop_key, 0)
            own_s = self.font_btn.render(f"Owned: {owned}", True, PAL["text_dim"])
            surface.blit(own_s, (self.px + 140, ry + 24))

            # Buy 1 button
            btn = self._buy_btn_rect(i)
            can = inventory.can_afford(data["seed_cost"])
            self._draw_button(surface, btn, "Buy 1", can)

            # Buy 5 button
            btn5 = self._buy5_btn_rect(i)
            can5 = inventory.can_afford(data["seed_cost"] * 5)
            self._draw_button(surface, btn5, "Buy 5", can5)

    def _draw_sell_tab(self, surface: pygame.Surface,
                       inventory: Inventory) -> None:
        for i, crop_key in enumerate(CROP_TYPES):
            data = CROPS[crop_key]
            ry = self._row_y(i)

            # Icon
            icon = get_icon(f"crop_{crop_key}")
            surface.blit(icon, (self.px + 14, ry + 8))

            # Name
            name_s = self.font_item.render(data["name"], True, PAL["text_light"])
            surface.blit(name_s, (self.px + 44, ry + 6))

            # Sell price (show multiplier if golden hour)
            base_price = data['sell_price']
            if self.sell_multiplier > 1.0:
                price_text = f"+{int(base_price * self.sell_multiplier)}g (2x!)"
                price_color = PAL["text_gold"]
            else:
                price_text = f"+{base_price}g"
                price_color = PAL["accent"]
            price_s = self.font_btn.render(price_text, True, price_color)
            surface.blit(price_s, (self.px + 44, ry + 24))

            # Owned count
            count = inventory.get_harvest_count(crop_key)
            own_s = self.font_btn.render(f"Have: {count}", True, PAL["text_dim"])
            surface.blit(own_s, (self.px + 140, ry + 24))

            # Sell 1 button
            btn = self._sell_btn_rect(i)
            self._draw_button(surface, btn, "Sell 1", count > 0)

            # Sell all button
            btn_all = self._sell_all_btn_rect(i)
            self._draw_button(surface, btn_all, "Sell All", count > 0)

    def _draw_button(self, surface: pygame.Surface, rect: pygame.Rect,
                     text: str, enabled: bool) -> None:
        hovering = rect.collidepoint(pygame.mouse.get_pos()) and enabled
        if not enabled:
            bg = (40, 40, 40)
            fg = (80, 80, 80)
            border = (60, 60, 60)
        elif hovering:
            bg = PAL["accent"]
            fg = PAL["text_light"]
            border = PAL["accent_bright"]
        else:
            bg = (50, 80, 50)
            fg = PAL["text_light"]
            border = PAL["accent"]

        pygame.draw.rect(surface, bg, rect, border_radius=4)
        pygame.draw.rect(surface, border, rect, 1, border_radius=4)
        ts = self.font_btn.render(text, True, fg)
        surface.blit(ts, (rect.centerx - ts.get_width() // 2,
                          rect.centery - ts.get_height() // 2))
