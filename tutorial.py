"""tutorial.py — Interactive step-by-step tutorial for Solstice Farm."""

from __future__ import annotations

import math

import pygame

from settings import (
    CROPS, PAL, SCREEN_H, SCREEN_W,
    TILE_SIZE, TOOL_HOE, TOOL_WATER, TOOL_SEEDS, TOOL_HANDS,
)

T = TILE_SIZE

# Tutorial steps — each is (trigger_condition_key, instruction_text, hint_text)
STEPS = [
    ("start",
     "Welcome, farmer! ☀️",
     "This is the longest day of the year — the Summer Solstice!\n"
     "You have 10 minutes to grow crops and earn as much gold as you can.\n\n"
     "Press SPACE to continue..."),
    ("move",
     "🚶 Moving Around",
     "Use WASD or Arrow Keys to walk around your farm.\n"
     "Try walking to the brown dirt tiles inside the fence!\n\n"
     "Walk to the farm area to continue..."),
    ("till",
     "🪓 Step 1: Till the Soil",
     "Press 1 to select the HOE tool.\n"
     "Face a brown dirt tile and press SPACE to till it.\n\n"
     "The soil will turn dark — ready for planting!"),
    ("water_soil",
     "💧 Step 2: Water the Soil",
     "Press 2 to select the WATER CAN.\n"
     "Face the tilled soil and press SPACE to water it.\n\n"
     "Watered soil is darker and moist."),
    ("plant",
     "🌱 Step 3: Plant Seeds",
     "Press 3 to select SEEDS.\n"
     "Use Q/E to choose seed type.\n"
     "Face watered soil and press SPACE to plant!\n\n"
     "Watch your crop grow in real-time!"),
    ("wait_grow",
     "⏳ Growing...",
     "Your crop is growing! Crops grow faster during peak sunlight.\n"
     "Some crops need multiple waterings — watch for the 💧 icon.\n\n"
     "While waiting, try planting more crops!\n"
     "Press SPACE to skip ahead..."),
    ("harvest",
     "🌾 Step 4: Harvest!",
     "When a crop shows a ✨ golden sparkle, it's ready!\n"
     "Press 4 to select HANDS, face the crop, press SPACE.\n\n"
     "Harvested crops go to your inventory."),
    ("shop",
     "🏪 Step 5: Visit the Shop",
     "Walk to the house on the right side of the map.\n"
     "Face it and press SPACE or TAB to open the Shop.\n\n"
     "You can SELL crops for gold and BUY more seeds!"),
    ("done",
     "✅ Tutorial Complete!",
     "You now know the basics of Solstice Farm!\n\n"
     "🌟 Tips:\n"
     "• Crops grow fastest at midday (solstice peak!)\n"
     "• During Golden Hour, sell prices are DOUBLED!\n"
     "• Watch for Solstice Events — they help a lot!\n"
     "• The Solstice Bloom only grows during peak sun.\n\n"
     "Press SPACE to start farming! Good luck! 🌻"),
]


class Tutorial:
    """Manages the interactive tutorial overlay."""

    def __init__(self) -> None:
        self.active: bool = True
        self.step: int = 0
        self.timer: float = 0.0
        self.dismissed: bool = False  # set True when fully done

        self.font_title = pygame.font.SysFont(None, 36)
        self.font_body = pygame.font.SysFont(None, 24)
        self.font_step = pygame.font.SysFont(None, 20)
        self.font_skip = pygame.font.SysFont(None, 18)

        # Auto-advance tracking
        self._player_moved: bool = False
        self._tilled: bool = False
        self._watered: bool = False
        self._planted: bool = False
        self._harvested: bool = False
        self._shop_visited: bool = False

    @property
    def current_step_key(self) -> str:
        if self.step < len(STEPS):
            return STEPS[self.step][0]
        return "done"

    def notify(self, action: str) -> None:
        """Called by game when player performs an action."""
        if not self.active:
            return
        key = self.current_step_key

        if key == "move" and action == "player_moved":
            self._player_moved = True
        elif key == "till" and action == "tilled":
            self._tilled = True
            self._advance()
        elif key == "water_soil" and action == "watered":
            self._watered = True
            self._advance()
        elif key == "plant" and action == "planted":
            self._planted = True
            self._advance()
        elif key == "harvest" and action == "harvested":
            self._harvested = True
            self._advance()
        elif key == "shop" and action == "shop_opened":
            self._shop_visited = True
            self._advance()

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle input. Returns True if event was consumed."""
        if not self.active:
            return False

        if event.type == pygame.KEYDOWN:
            # ESC to skip tutorial entirely
            if event.key == pygame.K_ESCAPE:
                self.active = False
                self.dismissed = True
                return True

            # SPACE to advance on text-only steps or if player gets stuck
            key = self.current_step_key
            if event.key == pygame.K_SPACE:
                if key in ("start", "move", "wait_grow", "done"):
                    self._advance()
                    return True

        return False

    def update(self, dt: float, player_col: int, player_row: int) -> None:
        """Update tutorial state."""
        if not self.active:
            return
        self.timer += dt

        key = self.current_step_key

        # Auto-advance: player reached farm area
        if key == "move":
            from settings import FARM_X, FARM_Y, FARM_COLS, FARM_ROWS
            if (FARM_X <= player_col < FARM_X + FARM_COLS and
                    FARM_Y <= player_row < FARM_Y + FARM_ROWS):
                self._advance()

    def _advance(self) -> None:
        """Move to the next tutorial step."""
        self.step += 1
        self.timer = 0.0
        if self.step >= len(STEPS):
            self.active = False
            self.dismissed = True

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        if not self.active or self.step >= len(STEPS):
            return

        _, title, body = STEPS[self.step]

        # Panel dimensions — wide enough so text doesn't spill out
        panel_w = 680
        lines = body.split("\n")
        line_h = 26
        panel_h = 80 + len(lines) * line_h + 30
        px = (SCREEN_W - panel_w) // 2
        py = SCREEN_H - panel_h - 70  # above the bottom bar

        # Animate entrance
        if self.timer < 0.3:
            frac = self.timer / 0.3
            py += int((1.0 - frac) * 40)

        # Panel background
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((15, 25, 20, 240))
        surface.blit(panel, (px, py))

        # Border with glow
        pulse = 0.7 + 0.3 * abs(math.sin(self.timer * 2))
        border_color = (
            int(100 * pulse), int(220 * pulse), int(80 * pulse)
        )
        pygame.draw.rect(surface, border_color,
                         (px, py, panel_w, panel_h), 2, border_radius=10)

        # Step counter
        step_text = f"Step {self.step + 1}/{len(STEPS)}"
        ss = self.font_step.render(step_text, True, PAL["text_dim"])
        surface.blit(ss, (px + panel_w - ss.get_width() - 16, py + 14))

        # Title
        ts = self.font_title.render(title, True, PAL["text_gold"])
        surface.blit(ts, (px + 24, py + 16))

        # Body text (multi-line)
        body_start_y = py + 65
        for i, line in enumerate(lines):
            if not line.strip():
                continue
            color = PAL["text_light"] if not line.startswith("•") else PAL["accent"]
            ls = self.font_body.render(line, True, color)
            surface.blit(ls, (px + 24, body_start_y + i * line_h))

        # Skip hint
        skip = self.font_skip.render("ESC to skip tutorial", True,
                                     (120, 120, 100))
        surface.blit(skip, (px + 24, py + panel_h - 24))
