"""menu.py — Title screen and game-over screen for Solstice Farm."""

from __future__ import annotations

import math

import pygame

from settings import PAL, SCREEN_H, SCREEN_W


class TitleScreen:
    """Animated title screen with sun and press-enter prompt."""

    def __init__(self) -> None:
        self.font_title = pygame.font.SysFont(None, 72)
        self.font_sub = pygame.font.SysFont(None, 28)
        self.font_prompt = pygame.font.SysFont(None, 30)
        self.font_credit = pygame.font.SysFont(None, 20)
        self.timer: float = 0.0

    def update(self, dt: float) -> None:
        self.timer += dt

    def draw(self, surface: pygame.Surface) -> None:
        # Sky gradient background
        for y in range(SCREEN_H):
            t = y / SCREEN_H
            r = int(25 + t * 30)
            g = int(18 + t * 45)
            b = int(55 + t * 30)
            pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_W, y))

        # Animated sun
        sun_y = SCREEN_H // 3 + int(math.sin(self.timer * 0.8) * 10)
        sun_x = SCREEN_W // 2

        # Sun glow
        glow = pygame.Surface((120, 120), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 200, 50, 40), (60, 60), 60)
        surface.blit(glow, (sun_x - 60, sun_y - 60))

        # Sun disc
        pygame.draw.circle(surface, (255, 220, 70), (sun_x, sun_y), 35)
        pygame.draw.circle(surface, (255, 240, 120), (sun_x - 8, sun_y - 8), 12)

        # Sun rays
        for i in range(12):
            angle = i * math.pi / 6 + self.timer * 0.3
            length = 50 + math.sin(self.timer * 2 + i) * 8
            ex = int(sun_x + math.cos(angle) * length)
            ey = int(sun_y + math.sin(angle) * length)
            pygame.draw.line(surface, (255, 220, 70, 180),
                             (sun_x, sun_y), (ex, ey), 2)

        # Ground
        pygame.draw.rect(surface, (60, 100, 45),
                         (0, SCREEN_H * 2 // 3, SCREEN_W, SCREEN_H // 3))
        pygame.draw.rect(surface, (70, 120, 50),
                         (0, SCREEN_H * 2 // 3, SCREEN_W, 4))

        # Title text with shadow
        title = "SOLSTICE FARM"
        shadow = self.font_title.render(title, True, (20, 15, 10))
        main = self.font_title.render(title, True, PAL["text_gold"])
        tx = (SCREEN_W - main.get_width()) // 2
        ty = 60
        surface.blit(shadow, (tx + 3, ty + 3))
        surface.blit(main, (tx, ty))

        # Subtitle
        sub = "A Summer Solstice Farming Game"
        sub_s = self.font_sub.render(sub, True, (180, 200, 160))
        surface.blit(sub_s, ((SCREEN_W - sub_s.get_width()) // 2, ty + 70))

        # Prompt (blinking)
        if int(self.timer * 2) % 2 == 0:
            prompt = "Press ENTER to start"
            ps = self.font_prompt.render(prompt, True, PAL["text_light"])
            surface.blit(ps, ((SCREEN_W - ps.get_width()) // 2,
                              SCREEN_H - 140))

        # Controls hint
        hints = [
            "WASD / Arrows: Move",
            "Space: Use Tool",
            "1-4: Select Tool",
            "Q/E: Change Seed",
        ]
        for i, hint in enumerate(hints):
            hs = self.font_credit.render(hint, True, PAL["text_dim"])
            surface.blit(hs, ((SCREEN_W - hs.get_width()) // 2,
                              SCREEN_H - 100 + i * 18))

        # Credit
        credit = self.font_credit.render(
            "Made for DEV June Solstice Game Jam 2026", True,
            (100, 100, 80))
        surface.blit(credit, ((SCREEN_W - credit.get_width()) // 2,
                              SCREEN_H - 25))

    def check_start(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return True
        return False


# ===================================================================


class GameOverScreen:
    """End-of-day results screen."""

    PANEL_W = 520
    PANEL_H = 440

    def __init__(self) -> None:
        self.font_title = pygame.font.SysFont(None, 56)
        self.font_sub = pygame.font.SysFont(None, 26)
        self.font_stat = pygame.font.SysFont(None, 28)
        self.font_rating = pygame.font.SysFont(None, 38)
        self.font_btn = pygame.font.SysFont(None, 30)

        self.px = (SCREEN_W - self.PANEL_W) // 2
        self.py = (SCREEN_H - self.PANEL_H) // 2

        btn_w, btn_h = 180, 44
        self.btn_rect = pygame.Rect(
            self.px + (self.PANEL_W - btn_w) // 2,
            self.py + self.PANEL_H - btn_h - 24,
            btn_w, btn_h,
        )

    def draw(self, surface: pygame.Surface, money: int,
             total_harvested: int, total_earned: int,
             total_planted: int) -> None:
        # Dim overlay
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        surface.blit(overlay, (0, 0))

        # Panel
        panel = pygame.Surface((self.PANEL_W, self.PANEL_H), pygame.SRCALPHA)
        panel.fill((20, 30, 25, 240))
        surface.blit(panel, (self.px, self.py))
        pygame.draw.rect(surface, PAL["accent"],
                         (self.px, self.py, self.PANEL_W, self.PANEL_H),
                         2, border_radius=10)

        cx = self.px + self.PANEL_W // 2

        # Title
        ts = self.font_title.render("Day's End", True, PAL["text_gold"])
        surface.blit(ts, (cx - ts.get_width() // 2, self.py + 24))

        # Subtitle
        ss = self.font_sub.render(
            "The solstice sun has set on your farm.", True,
            (175, 200, 155))
        surface.blit(ss, (cx - ss.get_width() // 2, self.py + 85))

        # Divider
        pygame.draw.line(surface, (60, 90, 50),
                         (self.px + 30, self.py + 120),
                         (self.px + self.PANEL_W - 30, self.py + 120), 1)

        # Stats
        stats = [
            (f"Final Gold: {money}g", PAL["text_gold"]),
            (f"Crops Planted: {total_planted}", PAL["accent"]),
            (f"Crops Harvested: {total_harvested}", PAL["accent"]),
            (f"Gold Earned: {total_earned}g", PAL["text_gold"]),
        ]
        for i, (text, color) in enumerate(stats):
            ts = self.font_stat.render(text, True, color)
            surface.blit(ts, (cx - ts.get_width() // 2, self.py + 140 + i * 34))

        # Rating
        rating, rating_color = self._rating(total_earned)
        rs = self.font_rating.render(rating, True, rating_color)
        surface.blit(rs, (cx - rs.get_width() // 2, self.py + 300))

        # Play again button
        hovering = self.btn_rect.collidepoint(pygame.mouse.get_pos())
        bg = (90, 160, 70) if hovering else (55, 110, 45)
        border = (160, 230, 100) if hovering else (80, 150, 60)
        pygame.draw.rect(surface, bg, self.btn_rect, border_radius=10)
        pygame.draw.rect(surface, border, self.btn_rect, 2, border_radius=10)

        bs = self.font_btn.render("Play Again", True, (220, 255, 200))
        surface.blit(bs, (self.btn_rect.centerx - bs.get_width() // 2,
                          self.btn_rect.centery - bs.get_height() // 2))

    def _rating(self, earned: int) -> tuple[str, tuple[int, int, int]]:
        if earned >= 500:
            return "🌟 Legendary Farmer!", (255, 220, 50)
        elif earned >= 300:
            return "🏆 Master Gardener!", (240, 200, 40)
        elif earned >= 150:
            return "🌾 Great Harvest!", (100, 210, 80)
        elif earned >= 50:
            return "🌱 Good Work!", (140, 220, 120)
        else:
            return "🌰 Keep Trying...", (160, 160, 160)

    def check_restart(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_rect.collidepoint(event.pos):
                return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            return True
        return False
