"""sprites.py — Procedural 16-bit pixel-art sprite generator.

Every visual asset in the game is created here via code so no external
image files are required.  Sprites are generated once at startup and
cached as pygame.Surface objects.
"""

from __future__ import annotations

import math
import os
import random
from typing import Dict, List, Tuple

import pygame

from settings import CROPS, PAL, TILE_SIZE

T = TILE_SIZE  # shorthand

# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------
_tile_cache: Dict[str, pygame.Surface] = {}
_player_cache: Dict[str, List[pygame.Surface]] = {}
_crop_cache: Dict[str, List[pygame.Surface]] = {}
_icon_cache: Dict[str, pygame.Surface] = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _px(surf: pygame.Surface, x: int, y: int, color: Tuple[int, ...]) -> None:
    """Set a single pixel (safe bounds check)."""
    if 0 <= x < surf.get_width() and 0 <= y < surf.get_height():
        surf.set_at((x, y), color)


def _rect(surf: pygame.Surface, color: Tuple[int, ...],
           x: int, y: int, w: int, h: int) -> None:
    pygame.draw.rect(surf, color, (x, y, w, h))


def _circ(surf: pygame.Surface, color: Tuple[int, ...],
           cx: int, cy: int, r: int) -> None:
    pygame.draw.circle(surf, color, (cx, cy), r)


def _make(w: int = T, h: int = T, alpha: bool = True) -> pygame.Surface:
    if alpha:
        s = pygame.Surface((w, h), pygame.SRCALPHA)
    else:
        s = pygame.Surface((w, h))
    return s


# ===================================================================
# TILE SPRITES  (32 × 32)
# ===================================================================

def _gen_grass() -> pygame.Surface:
    s = _make()
    base = PAL["grass_a"]
    s.fill(base)
    # Scatter slightly varied green pixels for texture
    rng = random.Random(42)
    colors = [PAL["grass_a"], PAL["grass_b"], PAL["grass_c"]]
    for _ in range(50):
        x, y = rng.randint(0, T - 1), rng.randint(0, T - 1)
        _px(s, x, y, rng.choice(colors))
    # A few dark blades
    for _ in range(8):
        x = rng.randint(2, T - 3)
        y = rng.randint(2, T - 4)
        _px(s, x, y, (60, 130, 45))
        _px(s, x, y - 1, (65, 140, 48))
    return s


def _gen_dirt() -> pygame.Surface:
    s = _make()
    s.fill(PAL["dirt"])
    rng = random.Random(77)
    for _ in range(40):
        x, y = rng.randint(0, T - 1), rng.randint(0, T - 1)
        _px(s, x, y, PAL["dirt_dark"])
    return s


def _gen_tilled() -> pygame.Surface:
    s = _make()
    s.fill(PAL["tilled"])
    # Horizontal furrow lines
    for row in range(4, T, 6):
        pygame.draw.line(s, PAL["tilled_line"], (2, row), (T - 3, row), 1)
    # Edge detail
    pygame.draw.rect(s, PAL["dirt_dark"], (0, 0, T, T), 1)
    return s


def _gen_watered() -> pygame.Surface:
    s = _make()
    s.fill(PAL["watered"])
    for row in range(4, T, 6):
        pygame.draw.line(s, (50, 38, 22), (2, row), (T - 3, row), 1)
    # Slight sheen
    _px(s, 8, 8, (85, 70, 50))
    _px(s, 20, 14, (85, 70, 50))
    pygame.draw.rect(s, (45, 35, 20), (0, 0, T, T), 1)
    return s


def _gen_path() -> pygame.Surface:
    s = _make()
    s.fill(PAL["path"])
    rng = random.Random(99)
    # Cobblestone pattern
    for _ in range(20):
        x, y = rng.randint(0, T - 1), rng.randint(0, T - 1)
        _px(s, x, y, PAL["path_dark"])
    # Border
    pygame.draw.rect(s, PAL["path_dark"], (0, 0, T, T), 1)
    return s


def _gen_tree() -> pygame.Surface:
    s = _make()
    s.fill(PAL["grass_a"])
    cx, cy = T // 2, T // 2
    # Trunk
    _rect(s, PAL["tree_trunk"], cx - 3, cy + 2, 6, T // 2 - 2)
    # Canopy (layered circles)
    _circ(s, PAL["tree_leaves"], cx, cy - 2, 12)
    _circ(s, PAL["tree_leaves_light"], cx - 3, cy - 5, 7)
    _circ(s, PAL["tree_leaves"], cx + 4, cy - 3, 6)
    # Highlight
    _circ(s, (85, 170, 65), cx - 2, cy - 8, 3)
    return s


def _gen_fence() -> pygame.Surface:
    s = _make()
    s.fill(PAL["grass_a"])
    # Vertical posts
    _rect(s, PAL["fence"], 4, 6, 5, 22)
    _rect(s, PAL["fence"], T - 9, 6, 5, 22)
    # Horizontal rails
    _rect(s, PAL["fence"], 2, 10, T - 4, 4)
    _rect(s, PAL["fence"], 2, 20, T - 4, 4)
    # Dark edges
    _rect(s, PAL["fence_dark"], 4, 6, 5, 22, )
    pygame.draw.rect(s, PAL["fence_dark"], (4, 6, 5, 22), 1)
    pygame.draw.rect(s, PAL["fence_dark"], (T - 9, 6, 5, 22), 1)
    return s


def _gen_water_source() -> pygame.Surface:
    s = _make()
    s.fill(PAL["grass_a"])
    # Stone well base
    _rect(s, (140, 135, 125), 4, 6, T - 8, T - 10)
    pygame.draw.rect(s, (100, 95, 85), (4, 6, T - 8, T - 10), 2)
    # Water surface
    _rect(s, PAL["water"], 7, 9, T - 14, T - 16)
    # Ripple
    _circ(s, PAL["water_light"], T // 2, T // 2, 4)
    _circ(s, PAL["water"], T // 2, T // 2, 2)
    return s


def _gen_shop() -> pygame.Surface:
    s = _make()
    s.fill(PAL["path"])
    # Building front
    _rect(s, PAL["shop_wall"], 2, 4, T - 4, T - 6)
    # Roof
    _rect(s, PAL["shop_roof"], 0, 0, T, 8)
    # Door
    _rect(s, (90, 60, 35), 11, 14, 10, 14)
    # Window
    _rect(s, PAL["water_light"], 4, 12, 6, 6)
    pygame.draw.rect(s, (60, 45, 25), (4, 12, 6, 6), 1)
    # Sign
    _rect(s, (220, 200, 140), T - 10, 10, 8, 8)
    pygame.draw.rect(s, (100, 80, 40), (T - 10, 10, 8, 8), 1)
    return s


_TILE_GENERATORS = {
    "grass": _gen_grass,
    "dirt": _gen_dirt,
    "tilled": _gen_tilled,
    "watered": _gen_watered,
    "path": _gen_path,
    "tree": _gen_tree,
    "fence": _gen_fence,
    "water_source": _gen_water_source,
    "shop": _gen_shop,
}


def get_tile(name: str) -> pygame.Surface:
    if name not in _tile_cache:
        gen = _TILE_GENERATORS.get(name)
        if gen is None:
            surf = _make()
            surf.fill((255, 0, 255))  # magenta = missing
            _tile_cache[name] = surf
        else:
            _tile_cache[name] = gen()
    return _tile_cache[name]


# ===================================================================
# PLAYER SPRITES  (24 × 32, drawn on 32 × 32 canvas)
# ===================================================================

# Directions
DIR_DOWN = 0
DIR_UP = 1
DIR_LEFT = 2
DIR_RIGHT = 3
DIR_NAMES = ["down", "up", "left", "right"]


def _gen_player_frame(direction: int, frame: int) -> pygame.Surface:
    """Generate a single player sprite frame.

    frame 0 = idle, 1 = walk-left-foot, 2 = walk-right-foot
    """
    s = _make(T, T)
    cx = T // 2  # 16

    # Leg bob for walk animation
    bob = 0
    leg_shift = 0
    if frame == 1:
        bob = -1
        leg_shift = 2
    elif frame == 2:
        bob = -1
        leg_shift = -2

    # --- Body parts (top-down order) ---
    head_y = 4 + bob
    body_y = 14 + bob
    leg_y = 22 + bob

    # Hat
    hat_c = PAL["hat"]
    hat_band_c = PAL["hat_band"]
    _rect(s, hat_c, cx - 7, head_y - 2, 14, 5)
    _rect(s, hat_band_c, cx - 6, head_y + 2, 12, 2)

    # Head
    skin = PAL["skin"]
    _rect(s, skin, cx - 5, head_y + 4, 10, 8)

    # Eyes
    if direction == DIR_DOWN:
        _px(s, cx - 3, head_y + 7, (40, 30, 20))
        _px(s, cx + 2, head_y + 7, (40, 30, 20))
    elif direction == DIR_UP:
        pass  # back of head — no eyes
    elif direction == DIR_LEFT:
        _px(s, cx - 4, head_y + 7, (40, 30, 20))
    elif direction == DIR_RIGHT:
        _px(s, cx + 3, head_y + 7, (40, 30, 20))

    # Shirt / body
    shirt = PAL["shirt"]
    _rect(s, shirt, cx - 5, body_y, 10, 8)
    # Arms
    if direction in (DIR_DOWN, DIR_UP):
        _rect(s, shirt, cx - 7, body_y + 1, 3, 6)
        _rect(s, shirt, cx + 4, body_y + 1, 3, 6)
        # Hands
        _rect(s, skin, cx - 7, body_y + 6, 3, 2)
        _rect(s, skin, cx + 4, body_y + 6, 3, 2)
    elif direction == DIR_LEFT:
        _rect(s, shirt, cx - 7, body_y + 1, 4, 6)
        _rect(s, skin, cx - 7, body_y + 6, 3, 2)
    elif direction == DIR_RIGHT:
        _rect(s, shirt, cx + 3, body_y + 1, 4, 6)
        _rect(s, skin, cx + 4, body_y + 6, 3, 2)

    # Pants / legs
    pants = PAL["pants"]
    if direction in (DIR_DOWN, DIR_UP):
        _rect(s, pants, cx - 4, leg_y, 4, 7)
        _rect(s, pants, cx, leg_y, 4, 7)
        # Walk animation: shift legs
        if frame == 1:
            _rect(s, pants, cx - 4 + leg_shift, leg_y, 4, 8)
        elif frame == 2:
            _rect(s, pants, cx + leg_shift, leg_y, 4, 8)
    else:
        # Side view — single leg column with bob
        _rect(s, pants, cx - 3, leg_y, 6, 7)
        if frame == 1:
            _rect(s, pants, cx - 2, leg_y, 3, 8)
            _rect(s, pants, cx + 1, leg_y - 1, 3, 6)
        elif frame == 2:
            _rect(s, pants, cx + 1, leg_y, 3, 8)
            _rect(s, pants, cx - 2, leg_y - 1, 3, 6)

    # Shoes
    shoe_c = (60, 40, 25)
    _rect(s, shoe_c, cx - 4, leg_y + 7, 4, 2)
    _rect(s, shoe_c, cx, leg_y + 7, 4, 2)

    return s


_player_sheet: pygame.Surface | None = None
_player_sheet_loaded: bool = False


def get_player_frames(direction: int) -> List[pygame.Surface]:
    """Return [idle, walk1, walk2] frames for the given direction."""
    global _player_sheet, _player_sheet_loaded

    if not _player_sheet_loaded:
        _player_sheet_loaded = True
        base = os.path.dirname(__file__)
        # Try new filename first, fall back to old one
        for fname in ("player_spritesheet.png", "assetkarakter.png"):
            path = os.path.join(base, "assets", "images", fname)
            if os.path.exists(path):
                try:
                    _player_sheet = pygame.image.load(path).convert_alpha()
                    # Automatically remove background color based on top-left pixel
                    bg_color = _player_sheet.get_at((0, 0))
                    _player_sheet.set_colorkey(bg_color)
                except pygame.error:
                    pass
                break

    # Spritesheet row mapping:
    # Row 0 = Down, Row 1 = Left, Row 2 = Right, Row 3 = Up
    # Game directions: DIR_DOWN=0, DIR_UP=1, DIR_LEFT=2, DIR_RIGHT=3
    _DIR_TO_ROW = {0: 0, 1: 3, 2: 1, 3: 2}

    key = DIR_NAMES[direction]
    if key not in _player_cache:
        if _player_sheet:
            sheet_w = _player_sheet.get_width()
            sheet_h = _player_sheet.get_height()
            num_cols = max(1, round(sheet_w / (sheet_h / 4)))
            fw = sheet_w // num_cols
            fh = sheet_h // 4
            row = _DIR_TO_ROW.get(direction, direction)
            
            def get_frame(col: int) -> pygame.Surface:
                rect = pygame.Rect(col * fw, row * fh, fw, fh)
                raw_frame = _player_sheet.subsurface(rect)
                return pygame.transform.smoothscale(raw_frame, (T, T))

            # Return all frames for this direction row
            frames = [get_frame(c) for c in range(num_cols)]
            
            _player_cache[key] = frames
        else:
            _player_cache[key] = [
                _gen_player_frame(direction, 0),
                _gen_player_frame(direction, 1),
                _gen_player_frame(direction, 2),
            ]
    return _player_cache[key]


# ===================================================================
# CROP SPRITES  (drawn on 32 × 32, layered on top of soil tile)
# ===================================================================

def _gen_crop_stages(crop_key: str) -> List[pygame.Surface]:
    """Generate growth stage sprites for a crop type."""
    data = CROPS[crop_key]
    stages = data["stages"]
    stem_c = data["color"]
    fruit_c = data["fruit_color"]
    result: List[pygame.Surface] = []

    for stage in range(stages):
        s = _make(T, T)
        frac = (stage + 1) / stages  # 0.x to 1.0
        cx = T // 2
        ground = T - 4  # base of the plant

        if frac <= 0.25:
            # Tiny sprout: 2 green pixels
            _rect(s, stem_c, cx - 1, ground - 4, 2, 4)
            _px(s, cx - 2, ground - 4, (stem_c[0] + 20, stem_c[1] + 20, stem_c[2]))
            _px(s, cx + 1, ground - 4, (stem_c[0] + 20, stem_c[1] + 20, stem_c[2]))

        elif frac <= 0.5:
            # Small plant with leaves
            stem_h = 10
            _rect(s, stem_c, cx - 1, ground - stem_h, 2, stem_h)
            # Two small leaves
            _rect(s, (stem_c[0] + 15, stem_c[1] + 20, stem_c[2] + 5),
                  cx - 5, ground - stem_h + 2, 4, 3)
            _rect(s, (stem_c[0] + 15, stem_c[1] + 20, stem_c[2] + 5),
                  cx + 1, ground - stem_h + 4, 4, 3)

        elif frac <= 0.75:
            # Medium plant
            stem_h = 16
            _rect(s, stem_c, cx - 1, ground - stem_h, 2, stem_h)
            # Bigger leaves
            leaf = (stem_c[0] + 20, min(255, stem_c[1] + 30), stem_c[2] + 10)
            _rect(s, leaf, cx - 7, ground - stem_h + 3, 6, 4)
            _rect(s, leaf, cx + 1, ground - stem_h + 6, 6, 4)
            _rect(s, leaf, cx - 6, ground - stem_h + 10, 5, 3)
            # Small bud
            _circ(s, (fruit_c[0] // 2 + 60, fruit_c[1] // 2 + 60, fruit_c[2] // 2 + 60),
                  cx, ground - stem_h, 3)

        else:
            # Full grown with fruit/flower — ready to harvest
            stem_h = 20
            _rect(s, stem_c, cx - 1, ground - stem_h, 2, stem_h)
            # Big leaves
            leaf = (stem_c[0] + 25, min(255, stem_c[1] + 35), stem_c[2] + 15)
            _rect(s, leaf, cx - 8, ground - stem_h + 5, 7, 5)
            _rect(s, leaf, cx + 1, ground - stem_h + 8, 7, 5)
            _rect(s, leaf, cx - 7, ground - stem_h + 13, 6, 4)

            # Fruit/flower head
            if crop_key == "sunflower":
                # Sunflower: large circle head
                _circ(s, fruit_c, cx, ground - stem_h - 1, 7)
                _circ(s, (95, 55, 15), cx, ground - stem_h - 1, 3)
                # Petals
                for angle_i in range(8):
                    a = angle_i * math.pi / 4
                    px = int(cx + math.cos(a) * 9)
                    py = int((ground - stem_h - 1) + math.sin(a) * 9)
                    _circ(s, fruit_c, px, py, 2)
            elif crop_key == "corn":
                # Corn: tall yellow cob
                _rect(s, fruit_c, cx - 3, ground - stem_h - 2, 6, 10)
                _rect(s, (200, 180, 50), cx - 2, ground - stem_h - 1, 4, 8)
                # Husk lines
                _px(s, cx, ground - stem_h, (180, 160, 40))
                _px(s, cx, ground - stem_h + 3, (180, 160, 40))
            else:
                # Generic fruit: round fruit
                _circ(s, fruit_c, cx, ground - stem_h - 1, 5)
                # Highlight
                _circ(s, (min(255, fruit_c[0] + 40),
                          min(255, fruit_c[1] + 40),
                          min(255, fruit_c[2] + 40)),
                      cx - 2, ground - stem_h - 3, 2)

        result.append(s)
    return result


def get_crop_stages(crop_key: str) -> List[pygame.Surface]:
    if crop_key not in _crop_cache:
        _crop_cache[crop_key] = _gen_crop_stages(crop_key)
    return _crop_cache[crop_key]


# ===================================================================
# ICON SPRITES  (small icons for HUD / inventory)
# ===================================================================

def _gen_icon_hoe() -> pygame.Surface:
    s = _make(24, 24)
    # Handle
    pygame.draw.line(s, (140, 100, 50), (6, 18), (18, 4), 2)
    # Head
    _rect(s, (160, 160, 165), 14, 2, 8, 4)
    pygame.draw.rect(s, (120, 120, 125), (14, 2, 8, 4), 1)
    return s


def _gen_icon_water_can() -> pygame.Surface:
    s = _make(24, 24)
    # Body
    _rect(s, PAL["water_blue"], 4, 8, 14, 12)
    pygame.draw.rect(s, (50, 100, 180), (4, 8, 14, 12), 1)
    # Spout
    pygame.draw.line(s, (50, 100, 180), (18, 10), (22, 6), 2)
    # Handle
    pygame.draw.arc(s, (50, 100, 180), (8, 2, 10, 10), 0, math.pi, 2)
    return s


def _gen_icon_seeds() -> pygame.Surface:
    s = _make(24, 24)
    # Bag
    _rect(s, (180, 150, 90), 5, 6, 14, 14)
    pygame.draw.rect(s, (130, 100, 50), (5, 6, 14, 14), 1)
    # Seeds inside
    _circ(s, (100, 170, 60), 9, 14, 2)
    _circ(s, (110, 180, 65), 14, 12, 2)
    _circ(s, (90, 160, 55), 11, 17, 2)
    # Tie at top
    pygame.draw.line(s, (130, 100, 50), (8, 6), (12, 3), 2)
    pygame.draw.line(s, (130, 100, 50), (16, 6), (12, 3), 2)
    return s


def _gen_icon_hands() -> pygame.Surface:
    s = _make(24, 24)
    # Open palm
    _rect(s, PAL["skin"], 7, 10, 10, 10)
    # Fingers
    for i in range(4):
        _rect(s, PAL["skin"], 7 + i * 3, 5, 2, 6)
    # Thumb
    _rect(s, PAL["skin"], 4, 11, 4, 3)
    # Outline
    pygame.draw.rect(s, (180, 140, 100), (4, 5, 14, 16), 1)
    return s


def _gen_crop_icon(crop_key: str) -> pygame.Surface:
    s = _make(24, 24)
    data = CROPS[crop_key]
    fc = data["fruit_color"]
    # Simple fruit circle
    _circ(s, fc, 12, 12, 8)
    _circ(s, (min(255, fc[0] + 40), min(255, fc[1] + 40), min(255, fc[2] + 40)),
          10, 9, 3)
    # Stem
    pygame.draw.line(s, data["color"], (12, 4), (12, 2), 2)
    _circ(s, data["color"], 14, 3, 2)
    return s


def _gen_seed_icon(crop_key: str) -> pygame.Surface:
    s = _make(24, 24)
    data = CROPS[crop_key]
    fc = data["fruit_color"]
    # Small bag
    _rect(s, (180, 150, 90), 5, 6, 14, 14)
    pygame.draw.rect(s, (130, 100, 50), (5, 6, 14, 14), 1)
    # Colored dot to show type
    _circ(s, fc, 12, 14, 4)
    # Tie
    pygame.draw.line(s, (130, 100, 50), (8, 6), (12, 3), 2)
    pygame.draw.line(s, (130, 100, 50), (16, 6), (12, 3), 2)
    return s


def get_icon(name: str) -> pygame.Surface:
    if name not in _icon_cache:
        if name == "hoe":
            _icon_cache[name] = _gen_icon_hoe()
        elif name == "water_can":
            _icon_cache[name] = _gen_icon_water_can()
        elif name == "seeds":
            _icon_cache[name] = _gen_icon_seeds()
        elif name == "hands":
            _icon_cache[name] = _gen_icon_hands()
        elif name.startswith("crop_"):
            _icon_cache[name] = _gen_crop_icon(name[5:])
        elif name.startswith("seed_"):
            _icon_cache[name] = _gen_seed_icon(name[5:])
        else:
            s = _make(24, 24)
            s.fill((255, 0, 255))
            _icon_cache[name] = s
    return _icon_cache[name]


# ===================================================================
# Pre-generate everything at import time? No — do it on first access.
# ===================================================================

def preload() -> None:
    """Optional: call once at startup to pre-generate all sprites."""
    for name in _TILE_GENERATORS:
        get_tile(name)
    for d in range(4):
        get_player_frames(d)
    for key in CROPS:
        get_crop_stages(key)
        get_icon(f"crop_{key}")
        get_icon(f"seed_{key}")
    for tool in ("hoe", "water_can", "seeds", "hands"):
        get_icon(tool)
