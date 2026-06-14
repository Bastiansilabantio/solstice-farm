"""game.py — Central game state and scene management for Solstice Farm."""

from __future__ import annotations

import random

import pygame

from camera import Camera
from floats import CropTooltip, FloatingTextSystem, TileTooltip
from hud import HUD
from inventory import Inventory
from menu import GameOverScreen, TitleScreen
from music import stop_music, update_music
from particles import ParticleSystem
from player import Player
from settings import (
    CROPS, DAY_DURATION,
    EVENT_DURATION, EVENT_INTERVAL_MAX, EVENT_INTERVAL_MIN,
    FARM_COLS, FARM_ROWS, FARM_X, FARM_Y,
    GOLDEN_HOUR_END, GOLDEN_HOUR_MULTIPLIER, GOLDEN_HOUR_START,
    SCREEN_H, SCREEN_W, TILE_SIZE,
    TOOL_HANDS, TOOL_HOE, TOOL_SEEDS, TOOL_WATER,
)
from shop import Shop
from sky import draw_sky, draw_sun_moon, draw_world_tint
from sounds import play as play_sfx, preload_sounds
from sprites import preload
from tutorial import Tutorial
from world import World

T = TILE_SIZE

# Scene names
SCENE_TITLE = "title"
SCENE_PLAY = "play"
SCENE_OVER = "over"

# Solstice event types
EVENT_NONE = "none"
EVENT_SUNBURST = "sunburst"
EVENT_RAIN = "rain"
EVENT_GOLDEN_SEEDS = "golden_seeds"
EVENT_SOLSTICE_WIND = "solstice_wind"


class Game:
    """Top-level game object that owns all subsystems."""

    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen

        # Pre-generate all sprites & sounds
        preload()
        preload_sounds()

        # Scene
        self.scene: str = SCENE_TITLE
        self.title_screen = TitleScreen()
        self.game_over_screen = GameOverScreen()

        # Will be initialised by _new_game()
        self.world: World = None  # type: ignore
        self.player: Player = None  # type: ignore
        self.camera: Camera = None  # type: ignore
        self.inventory: Inventory = None  # type: ignore
        self.hud: HUD = None  # type: ignore
        self.shop: Shop = None  # type: ignore
        self.particles: ParticleSystem = None  # type: ignore
        self.tutorial: Tutorial = None  # type: ignore
        self.floats: FloatingTextSystem = None  # type: ignore
        self.crop_tooltip: CropTooltip = None  # type: ignore
        self.tile_tooltip: TileTooltip = None  # type: ignore

        self.time_elapsed: float = 0.0
        self.time_fraction: float = 0.0

        # Floating message
        self.message: str = ""
        self.message_timer: float = 0.0

        # Event system
        self.current_event: str = EVENT_NONE
        self.event_timer: float = 0.0
        self.event_cooldown: float = 0.0
        self.golden_hour_notified: bool = False

        # Ambient particle timer
        self._ambient_timer: float = 0.0

        # Footstep sound timer
        self._step_timer: float = 0.0

        # Screen transition
        self._fade_alpha: int = 0
        self._fade_target: int = 0
        self._fade_speed: int = 400  # alpha per second

    # ------------------------------------------------------------------
    # Game reset
    # ------------------------------------------------------------------

    def _new_game(self) -> None:
        """Initialise / reset all game state."""
        self.world = World()
        start_col = FARM_X + FARM_COLS // 2
        start_row = FARM_Y + FARM_ROWS + 2
        self.player = Player(start_col, start_row)
        self.camera = Camera()
        self.inventory = Inventory()
        self.hud = HUD()
        self.shop = Shop()
        self.particles = ParticleSystem()
        self.tutorial = Tutorial()
        self.floats = FloatingTextSystem()
        self.crop_tooltip = CropTooltip()
        self.tile_tooltip = TileTooltip()

        self.time_elapsed = 0.0
        self.time_fraction = 0.0
        self.message = ""
        self.message_timer = 0.0
        self.current_event = EVENT_NONE
        self.event_timer = 0.0
        self.event_cooldown = random.uniform(EVENT_INTERVAL_MIN,
                                              EVENT_INTERVAL_MAX)
        self.golden_hour_notified = False
        self._ambient_timer = 0.0
        self._step_timer = 0.0
        self._fade_alpha = 255  # start faded in from black
        self._fade_target = 0

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.scene == SCENE_TITLE:
            if self.title_screen.check_start(event):
                self._new_game()
                self.scene = SCENE_PLAY
                self._show_message("Welcome to Solstice Farm! ☀️")
                play_sfx("select")
            return

        if self.scene == SCENE_OVER:
            if self.game_over_screen.check_restart(event):
                self._new_game()
                self.scene = SCENE_PLAY
                play_sfx("select")
            return

        # --- SCENE_PLAY ---

        # Tutorial takes priority
        if self.tutorial and self.tutorial.active:
            if self.tutorial.handle_event(event):
                return

        # Shop takes priority if open
        if self.shop.is_open:
            self.shop.sell_multiplier = (
                GOLDEN_HOUR_MULTIPLIER if self._is_golden_hour() else 1.0
            )
            self.shop.handle_event(event, self.inventory)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
            return

        # HUD click
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hud.handle_click(event.pos, self.player):
                play_sfx("select")
                return

        # Player input
        action = self.player.handle_event(event)
        if action == "use_tool":
            self._use_tool()
        elif action == "cycle_seed":
            play_sfx("select")

        # Toggle shop with TAB
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                fc, fr = self.player.facing_tile()
                if self.world.is_shop(fc, fr):
                    self.shop.toggle()
                    play_sfx("select")
                    if self.tutorial and self.tutorial.active:
                        self.tutorial.notify("shop_opened")

    # ------------------------------------------------------------------
    # Tool usage
    # ------------------------------------------------------------------

    def _use_tool(self) -> None:
        fc, fr = self.player.facing_tile()
        tool = self.player.current_tool
        px = fc * T + T // 2
        py = fr * T + T // 2

        if tool == TOOL_HOE:
            if self.world.till(fc, fr):
                self.particles.emit_till(px, py)
                self._show_message("Tilled the soil!")
                play_sfx("till")
                if self.tutorial and self.tutorial.active:
                    self.tutorial.notify("tilled")
            else:
                tile = self.world.get_tile(fc, fr)
                if tile in (2, 3, 9):
                    self._show_message("Already tilled!")
                    play_sfx("deny")

        elif tool == TOOL_WATER:
            if self.world.is_water_source(fc, fr):
                if self.player.refill_water():
                    self.particles.emit_water(px, py)
                    self._show_message("Water can refilled! 💧")
                    play_sfx("refill")
                else:
                    self._show_message("Water can is already full!")
                    play_sfx("deny")
                return

            if self.player.water <= 0:
                self._show_message("No water! Visit the well.")
                play_sfx("deny")
                return

            if self.world.water_soil(fc, fr):
                self.player.water -= 1
                self.particles.emit_water(px, py)
                self._show_message("Watered!")
                play_sfx("water")
                if self.tutorial and self.tutorial.active:
                    self.tutorial.notify("watered")

        elif tool == TOOL_SEEDS:
            seed_type = self.player.current_seed_type
            if not self.inventory.has_seeds(seed_type):
                self._show_message(f"No {seed_type} seeds! Buy at the shop.")
                play_sfx("deny")
                return
            if self.world.can_plant(fc, fr):
                if self.inventory.use_seed(seed_type):
                    self.world.plant(fc, fr, seed_type)
                    self.particles.emit_plant(px, py)
                    name = CROPS[seed_type]["name"]
                    self._show_message(f"Planted {name}!")
                    play_sfx("plant")
                    if seed_type == "solstice_bloom":
                        self.particles.emit_solstice_magic(px, py)
                    if self.tutorial and self.tutorial.active:
                        self.tutorial.notify("planted")
            else:
                tile = self.world.get_tile(fc, fr)
                if tile == 1:
                    self._show_message("Till the soil first! (use Hoe)")
                elif tile == 9:
                    self._show_message("Already planted here!")
                play_sfx("deny")

        elif tool == TOOL_HANDS:
            if self.world.is_shop(fc, fr):
                self.shop.open()
                play_sfx("select")
                if self.tutorial and self.tutorial.active:
                    self.tutorial.notify("shop_opened")
                return

            result = self.world.harvest(fc, fr)
            if result:
                crop_type, value = result
                bonus_text = ""
                if self._is_golden_hour():
                    value = int(value * GOLDEN_HOUR_MULTIPLIER)
                    bonus_text = " (2x Golden!)"
                if self.current_event == EVENT_SOLSTICE_WIND:
                    value = int(value * 1.5)
                    bonus_text += " (+50% Wind!)"
                self.inventory.add_harvest(crop_type)
                self.particles.emit_harvest(px, py)
                if crop_type == "solstice_bloom":
                    self.particles.emit_solstice_magic(px, py)
                name = CROPS[crop_type]["name"]
                self._show_message(
                    f"Harvested {name}! (+{value}g){bonus_text}")
                play_sfx("harvest")
                # Floating gold number
                self.floats.spawn_gold(value, px, py - 16)
                if self.tutorial and self.tutorial.active:
                    self.tutorial.notify("harvested")
            else:
                crop = self.world.crops.get((fc, fr))
                if crop and crop.needs_water:
                    self._show_message("This crop needs water! 💧")
                elif crop and not crop.ready:
                    pct = int(crop.progress * 100)
                    self._show_message(f"Growing... {pct}% 🌱")
                elif crop and crop.is_solstice_only:
                    from farming import get_sun_multiplier
                    if get_sun_multiplier(self.time_fraction) < 1.0:
                        self._show_message(
                            "Solstice Bloom needs peak sun to grow! ☀️")

    # ------------------------------------------------------------------
    # Solstice Events
    # ------------------------------------------------------------------

    def _is_golden_hour(self) -> bool:
        return GOLDEN_HOUR_START <= self.time_fraction <= GOLDEN_HOUR_END

    def _trigger_event(self) -> None:
        events = [EVENT_SUNBURST, EVENT_RAIN, EVENT_GOLDEN_SEEDS,
                  EVENT_SOLSTICE_WIND]
        self.current_event = random.choice(events)
        self.event_timer = EVENT_DURATION
        play_sfx("event")

        if self.current_event == EVENT_SUNBURST:
            self._show_message("☀️ SUNBURST! All crops grow 3× faster!")
            for crop in self.world.crops.values():
                crop.event_boost = 3.0
        elif self.current_event == EVENT_RAIN:
            self._show_message("🌧️ LIGHT RAIN! All crops auto-watered!")
            for (col, row), crop in self.world.crops.items():
                if crop.needs_water:
                    crop.water_crop()
        elif self.current_event == EVENT_GOLDEN_SEEDS:
            gift_type = random.choice(list(CROPS.keys()))
            gift_count = random.randint(2, 5)
            self.inventory.add_seeds(gift_type, gift_count)
            name = CROPS[gift_type]["name"]
            self._show_message(
                f"🎁 SOLSTICE GIFT! +{gift_count} {name} Seeds!")
        elif self.current_event == EVENT_SOLSTICE_WIND:
            self._show_message(
                "🌬️ SOLSTICE WIND! Harvest value +50% for 15s!")

    def _end_event(self) -> None:
        if self.current_event == EVENT_SUNBURST:
            for crop in self.world.crops.values():
                crop.event_boost = 1.0
        self.current_event = EVENT_NONE
        self.event_cooldown = random.uniform(EVENT_INTERVAL_MIN,
                                              EVENT_INTERVAL_MAX)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        # Screen fade
        if self._fade_alpha != self._fade_target:
            if self._fade_alpha < self._fade_target:
                self._fade_alpha = min(self._fade_target,
                                       self._fade_alpha + int(self._fade_speed * dt))
            else:
                self._fade_alpha = max(self._fade_target,
                                       self._fade_alpha - int(self._fade_speed * dt))

        if self.scene == SCENE_TITLE:
            self.title_screen.update(dt)
            return

        if self.scene == SCENE_OVER:
            stop_music()
            return

        # --- SCENE_PLAY ---
        if self.shop.is_open:
            return

        # Day timer
        self.time_elapsed += dt
        self.time_fraction = min(self.time_elapsed / DAY_DURATION, 1.0)

        if self.time_fraction >= 1.0:
            self.inventory.sell_all()
            self._fade_target = 255
            self.scene = SCENE_OVER
            return

        # Music
        update_music(self.time_fraction)

        # Golden hour notification
        if self._is_golden_hour() and not self.golden_hour_notified:
            self.golden_hour_notified = True
            self._show_message(
                "✨ GOLDEN HOUR! Sell prices doubled! ✨")
            play_sfx("event")

        # Event system
        if self.current_event != EVENT_NONE:
            self.event_timer -= dt
            if self.event_timer <= 0:
                self._end_event()
        else:
            self.event_cooldown -= dt
            if self.event_cooldown <= 0 and self.time_fraction < 0.85:
                self._trigger_event()

        # World
        self.world.update(dt, self.time_fraction)

        # Player
        self.player.update(dt, self.world.is_solid)

        # Tutorial
        if self.tutorial and self.tutorial.active:
            self.tutorial.update(dt, self.player.tile_col,
                                 self.player.tile_row)

        # Footstep sound
        if self.player.moving:
            self._step_timer += dt
            if self._step_timer >= 0.35:
                self._step_timer = 0.0
                play_sfx("step")
        else:
            self._step_timer = 0.0

        # Camera
        self.camera.update(self.player.center_x, self.player.center_y, dt)

        # Particles
        self.particles.update(dt)

        # Floating texts
        self.floats.update(dt)

        # Ambient particles
        self._ambient_timer += dt
        if self._ambient_timer >= 0.15:
            self._ambient_timer = 0.0
            self._spawn_ambient_particles()

        # Message fade
        if self.message_timer > 0:
            self.message_timer -= dt

    def _spawn_ambient_particles(self) -> None:
        tf = self.time_fraction
        cx, cy = self.camera.x, self.camera.y

        if 0.30 < tf < 0.60:
            self.particles.emit_sun_sparkles(
                SCREEN_W, SCREEN_H, cx, cy, 1)
        if tf > 0.75:
            self.particles.emit_fireflies(
                SCREEN_W, SCREEN_H, cx, cy, 1)
        if self.current_event == EVENT_RAIN:
            self.particles.emit_rain(SCREEN_W, cx, cy, 4)

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self) -> None:
        if self.scene == SCENE_TITLE:
            self.title_screen.draw(self.screen)
            self._draw_fade()
            return

        # --- Sky background ---
        draw_sky(self.screen, self.time_fraction)
        draw_sun_moon(self.screen, self.time_fraction)

        # --- World ---
        self.world.draw(self.screen, self.camera)

        # --- Player ---
        ox, oy = self.camera.offset
        self.player.draw(self.screen, ox, oy)

        # --- Particles ---
        self.particles.draw(self.screen, ox, oy)

        # --- Floating texts ---
        self.floats.draw(self.screen, ox, oy)

        # --- World tint (dawn/dusk darkness) ---
        draw_world_tint(self.screen, self.time_fraction)

        # --- Crop tooltip ---
        if not self.shop.is_open and (not self.tutorial or
                                       not self.tutorial.active or
                                       self.tutorial.step > 4):
            self._draw_tooltips()

        # --- Event banner ---
        if self.current_event != EVENT_NONE:
            self._draw_event_banner()

        # --- Golden hour glow ---
        if self._is_golden_hour():
            self._draw_golden_hour_glow()

        # --- HUD ---
        self.hud.draw(self.screen, self.player, self.inventory,
                      self.time_fraction)
        self.hud.draw_water(self.screen, self.player.water,
                            self.player.water_max)

        # --- Tutorial overlay ---
        if self.tutorial and self.tutorial.active:
            self.tutorial.draw(self.screen)

        # --- Shop ---
        self.shop.draw(self.screen, self.inventory)

        # --- Floating message ---
        if self.message_timer > 0:
            alpha = min(1.0, self.message_timer / 0.5)
            HUD.draw_message(self.screen, self.message, alpha)

        # --- Game over overlay ---
        if self.scene == SCENE_OVER:
            inv = self.inventory
            self.game_over_screen.draw(
                self.screen, inv.money, inv.total_harvested,
                inv.total_earned, inv.total_planted,
            )

        # --- Screen fade ---
        self._draw_fade()

    def _draw_tooltips(self) -> None:
        """Draw crop info or tile hint for the facing tile."""
        fc, fr = self.player.facing_tile()
        ox, oy = self.camera.offset
        crop = self.world.crops.get((fc, fr))

        if crop:
            self.crop_tooltip.draw(
                self.screen, crop, fc, fr, ox, oy,
                is_golden_hour=self._is_golden_hour(),
            )
        else:
            tile_type = self.world.get_tile(fc, fr)
            hint = self.tile_tooltip.get_hint(tile_type,
                                               self.player.current_tool)
            if hint:
                self.tile_tooltip.draw(self.screen, hint, fc, fr, ox, oy)

    def _draw_event_banner(self) -> None:
        banners = {
            EVENT_SUNBURST: ("☀️ SUNBURST — 3× Growth!", (255, 200, 40)),
            EVENT_RAIN: ("🌧️ LIGHT RAIN — Auto Water!", (80, 160, 240)),
            EVENT_GOLDEN_SEEDS: ("🎁 SEEDS GIFT!", (100, 220, 80)),
            EVENT_SOLSTICE_WIND: ("🌬️ SOLSTICE WIND — +50% Harvest!",
                                  (180, 220, 255)),
        }
        text, color = banners.get(self.current_event,
                                   ("Event", (200, 200, 200)))

        font = pygame.font.SysFont(None, 24)
        ts = font.render(text, True, color)

        remaining = max(0, self.event_timer / EVENT_DURATION)
        bar_w = int(ts.get_width() + 20)
        bar_h = 4

        bx = (SCREEN_W - bar_w) // 2
        by = 46

        bg = pygame.Surface((bar_w, ts.get_height() + 10), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 140))
        self.screen.blit(bg, (bx, by))
        self.screen.blit(ts, (bx + 10, by + 3))

        bar_y = by + ts.get_height() + 4
        pygame.draw.rect(self.screen, (40, 40, 40),
                         (bx, bar_y, bar_w, bar_h))
        fill_w = int(bar_w * remaining)
        if fill_w > 0:
            pygame.draw.rect(self.screen, color,
                             (bx, bar_y, fill_w, bar_h))

    def _draw_golden_hour_glow(self) -> None:
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((255, 180, 50, 18))
        self.screen.blit(overlay, (0, 0))

    def _draw_fade(self) -> None:
        """Draw screen fade overlay for transitions."""
        if self._fade_alpha <= 0:
            return
        fade = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        fade.fill((0, 0, 0, min(255, self._fade_alpha)))
        self.screen.blit(fade, (0, 0))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _show_message(self, text: str) -> None:
        self.message = text
        self.message_timer = 2.5
