"""sky.py — Solstice Farm day/night sky cycle.

Renders a smooth vertical gradient that transitions through keyframes
representing a full solstice day from dawn to dusk.  Also provides a
world tint color used to overlay the entire game scene.
"""

from __future__ import annotations

import pygame

from settings import SCREEN_H, SCREEN_W

# ---------------------------------------------------------------------------
# Keyframe data: (time_fraction, top_color, bottom_color, tint_alpha)
# ---------------------------------------------------------------------------
_KEYFRAMES: list[tuple[float, tuple[int, int, int], tuple[int, int, int], int]] = [
    (0.00, (25, 18, 55),  (110, 65, 85),   60),   # pre-dawn
    (0.06, (220, 100, 55), (250, 170, 95),  30),   # sunrise
    (0.15, (85, 155, 240), (175, 215, 255), 0),    # morning
    (0.35, (55, 140, 245), (150, 205, 255), 0),    # late morning
    (0.50, (40, 120, 235), (135, 190, 255), 0),    # midday (solstice peak!)
    (0.65, (60, 140, 240), (155, 200, 255), 0),    # afternoon
    (0.78, (245, 150, 55), (255, 200, 110), 15),   # golden hour
    (0.88, (210, 75, 55),  (140, 55, 90),   40),   # sunset
    (1.00, (18, 12, 48),   (65, 30, 60),    70),   # dusk
]

# Cache
_cache: dict[str, object] = {"tf": -1.0, "strip": None}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _lerp_color(c0: tuple[int, int, int], c1: tuple[int, int, int],
                t: float) -> tuple[int, int, int]:
    return (
        int(max(0, min(255, _lerp(c0[0], c1[0], t)))),
        int(max(0, min(255, _lerp(c0[1], c1[1], t)))),
        int(max(0, min(255, _lerp(c0[2], c1[2], t)))),
    )


def _find_segment(tf: float):
    tf = max(0.0, min(1.0, tf))
    for i in range(len(_KEYFRAMES) - 1):
        t0, top0, bot0, a0 = _KEYFRAMES[i]
        t1, top1, bot1, a1 = _KEYFRAMES[i + 1]
        if tf <= t1:
            span = t1 - t0
            lt = (tf - t0) / span if span > 0 else 0.0
            return top0, bot0, a0, top1, bot1, a1, lt
    _, top, bot, a = _KEYFRAMES[-1]
    return top, bot, a, top, bot, a, 0.0


def _build_strip(height: int, top: tuple[int, int, int],
                 bot: tuple[int, int, int]) -> pygame.Surface:
    strip = pygame.Surface((1, height))
    for y in range(height):
        t = y / max(height - 1, 1)
        strip.set_at((0, y), _lerp_color(top, bot, t))
    return strip


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_sky_colors(tf: float) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    top0, bot0, _, top1, bot1, _, lt = _find_segment(tf)
    return _lerp_color(top0, top1, lt), _lerp_color(bot0, bot1, lt)


def get_tint_alpha(tf: float) -> int:
    """Return the darkness overlay alpha for the current time."""
    top0, _, a0, _, _, a1, lt = _find_segment(tf)
    return int(_lerp(a0, a1, lt))


def draw_sky(surface: pygame.Surface, tf: float) -> None:
    """Draw a smooth vertical sky gradient onto *surface*."""
    top, bot = get_sky_colors(tf)
    width, height = surface.get_size()

    if _cache["tf"] != tf or _cache["strip"] is None:
        _cache["strip"] = _build_strip(height, top, bot)
        _cache["tf"] = tf

    scaled = pygame.transform.scale(_cache["strip"], (width, height))  # type: ignore
    surface.blit(scaled, (0, 0))


def draw_world_tint(surface: pygame.Surface, tf: float) -> None:
    """Draw a semi-transparent dark overlay for dawn/dusk lighting."""
    alpha = get_tint_alpha(tf)
    if alpha <= 0:
        return
    overlay = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
    overlay.fill((10, 5, 25, alpha))
    surface.blit(overlay, (0, 0))


def draw_sun_moon(surface: pygame.Surface, tf: float) -> None:
    """Draw a small sun that arcs across the top of the screen."""
    import math
    # Sun position: arcs from left to right
    sun_x = int(80 + tf * (SCREEN_W - 160))
    sun_y = int(50 - math.sin(tf * math.pi) * 35)

    if tf > 0.92:
        return  # sun has set

    # Determine color based on time
    if tf < 0.1 or tf > 0.85:
        color = (255, 100, 35)
        radius = 10
    elif 0.35 < tf < 0.65:
        color = (255, 245, 130)
        radius = 14
    else:
        color = (255, 195, 65)
        radius = 12

    # Glow
    glow_r = radius + 8
    glow = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
    pygame.draw.circle(glow, (*color, 40), (glow_r, glow_r), glow_r)
    surface.blit(glow, (sun_x - glow_r, sun_y - glow_r))
    # Solid disc
    pygame.draw.circle(surface, color, (sun_x, sun_y), radius)
