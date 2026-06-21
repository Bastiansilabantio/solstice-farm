"""music.py — Background music for Solstice Farm.

Plays the background music track from assets/sounds/.
Falls back to procedural music if the file is not found.
"""

from __future__ import annotations

import os

import pygame

_initialized: bool = False
_playing: bool = False

# Path to the music file
_MUSIC_DIR = os.path.join(os.path.dirname(__file__), "assets", "sounds")
_MUSIC_FILE = os.path.join(_MUSIC_DIR, "Sunlight_on_the_Porch.ogg")


def _ensure_init() -> None:
    global _initialized
    if not _initialized:
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
        _initialized = True


def update_music(time_fraction: float) -> None:
    """Start or continue playing background music.

    Called every frame from game.py.  The time_fraction parameter is
    available for future dynamic volume adjustments.
    """
    global _playing

    _ensure_init()

    if _playing and pygame.mixer.music.get_busy():
        return

    if os.path.exists(_MUSIC_FILE):
        try:
            pygame.mixer.music.load(_MUSIC_FILE)
            pygame.mixer.music.set_volume(0.35)
            pygame.mixer.music.play(loops=-1, fade_ms=3000)
            _playing = True
        except pygame.error:
            _playing = False
    else:
        _playing = False


def stop_music() -> None:
    """Fade out and stop the background music."""
    global _playing
    if _playing:
        try:
            pygame.mixer.music.fadeout(2000)
        except pygame.error:
            pass
    _playing = False


def set_volume(vol: float) -> None:
    """Set music volume (0.0 – 1.0)."""
    try:
        pygame.mixer.music.set_volume(max(0.0, min(1.0, vol)))
    except pygame.error:
        pass
