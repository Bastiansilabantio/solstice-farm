"""sounds.py — Procedural sound effects for Solstice Farm.

Generates all SFX at runtime using pygame.mixer so no external audio
files are needed.
"""

from __future__ import annotations

import array
import math
import random

import pygame

_sounds: dict[str, pygame.mixer.Sound] = {}
_initialized: bool = False


def _ensure_init() -> None:
    global _initialized
    if not _initialized:
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        _initialized = True


# ---------------------------------------------------------------------------
# Wave generators
# ---------------------------------------------------------------------------

def _make_sound(samples: list[int], volume: float = 0.3) -> pygame.mixer.Sound:
    """Create a Sound from a list of signed‑16‑bit samples."""
    arr = array.array("h", samples)
    snd = pygame.mixer.Sound(buffer=arr)
    snd.set_volume(volume)
    return snd


def _sine_wave(freq: float, duration: float, rate: int = 22050,
               volume: float = 0.3, fade_out: float = 0.3) -> list[int]:
    """Generate a sine wave that fades out."""
    n = int(rate * duration)
    samples = []
    for i in range(n):
        t = i / rate
        # Envelope: fade out toward the end
        env = max(0.0, 1.0 - (t / duration) ** fade_out)
        val = math.sin(2 * math.pi * freq * t) * 32000 * volume * env
        samples.append(int(max(-32767, min(32767, val))))
    return samples


def _noise_burst(duration: float, rate: int = 22050,
                 volume: float = 0.15) -> list[int]:
    """Short burst of noise (for dirt/till sounds)."""
    n = int(rate * duration)
    rng = random.Random(12345)
    samples = []
    for i in range(n):
        env = max(0.0, 1.0 - (i / n) ** 0.5)
        val = rng.randint(-32000, 32000) * volume * env
        samples.append(int(val))
    return samples


def _chirp(start_freq: float, end_freq: float, duration: float,
           rate: int = 22050, volume: float = 0.25) -> list[int]:
    """Frequency sweep (chirp) — used for planting and harvesting."""
    n = int(rate * duration)
    samples = []
    for i in range(n):
        t = i / rate
        frac = i / n
        freq = start_freq + (end_freq - start_freq) * frac
        env = max(0.0, 1.0 - frac ** 0.6)
        val = math.sin(2 * math.pi * freq * t) * 32000 * volume * env
        samples.append(int(max(-32767, min(32767, val))))
    return samples


# ---------------------------------------------------------------------------
# Sound generation
# ---------------------------------------------------------------------------

def _generate_all() -> None:
    """Generate all game sounds."""
    _ensure_init()

    # Till sound: short noise burst
    _sounds["till"] = _make_sound(_noise_burst(0.15, volume=0.2), 0.4)

    # Water sound: low bubbling sine
    water = _sine_wave(180, 0.25, volume=0.2, fade_out=0.5)
    water2 = _sine_wave(220, 0.15, volume=0.15, fade_out=0.4)
    combined = [a + b for a, b in zip(water, water2 + [0] * (len(water) - len(water2)))]
    _sounds["water"] = _make_sound(combined, 0.4)

    # Plant sound: soft upward chirp
    _sounds["plant"] = _make_sound(_chirp(300, 600, 0.2, volume=0.2), 0.35)

    # Harvest sound: bright rising chirp + ding
    harvest = _chirp(400, 900, 0.15, volume=0.25)
    ding = _sine_wave(880, 0.3, volume=0.2, fade_out=0.8)
    pad = [0] * len(harvest)
    combined = [a + b for a, b in zip(harvest + [0] * max(0, len(ding) - len(harvest)),
                                       pad[:0] + ding)]
    _sounds["harvest"] = _make_sound(combined, 0.4)

    # Buy/sell sound: coin clink
    _sounds["coin"] = _make_sound(_chirp(1200, 800, 0.1, volume=0.2) +
                                   _sine_wave(800, 0.1, volume=0.15), 0.35)

    # Error/deny sound: low buzz
    _sounds["deny"] = _make_sound(_sine_wave(150, 0.15, volume=0.15, fade_out=0.3), 0.3)

    # Menu select
    _sounds["select"] = _make_sound(_sine_wave(660, 0.08, volume=0.15), 0.3)

    # Event notification: magical ascending notes
    event_snd = (_sine_wave(520, 0.1, volume=0.2) +
                 _sine_wave(660, 0.1, volume=0.2) +
                 _sine_wave(880, 0.15, volume=0.25, fade_out=0.8))
    _sounds["event"] = _make_sound(event_snd, 0.4)

    # Refill water
    refill = _sine_wave(300, 0.1, volume=0.15) + _sine_wave(400, 0.15, volume=0.2)
    _sounds["refill"] = _make_sound(refill, 0.35)

    # Footstep (very subtle)
    _sounds["step"] = _make_sound(_noise_burst(0.06, volume=0.05), 0.15)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def play(name: str) -> None:
    """Play a named sound effect."""
    if not _sounds:
        _generate_all()
    snd = _sounds.get(name)
    if snd:
        snd.play()


def preload_sounds() -> None:
    """Call once at startup to pre-generate all sounds."""
    if not _sounds:
        _generate_all()
