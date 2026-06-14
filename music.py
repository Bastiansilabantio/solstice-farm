"""music.py — Procedural background music for Solstice Farm.

Generates a gentle, looping ambient melody using sine waves.
The music dynamically adjusts based on the time of day.
"""

from __future__ import annotations

import array
import math
import random

import pygame

_channel: pygame.mixer.Channel | None = None
_current_track: str = ""

# Musical notes (frequencies in Hz)
_NOTES = {
    "C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23,
    "G4": 392.00, "A4": 440.00, "B4": 493.88,
    "C5": 523.25, "D5": 587.33, "E5": 659.25,
}

# Pentatonic scale for pleasant-sounding melodies
_MORNING = ["C4", "E4", "G4", "A4", "C5", "E5", "C5", "A4",
            "G4", "E4", "G4", "A4", "C5", "G4", "E4", "C4"]
_MIDDAY = ["G4", "A4", "C5", "E5", "D5", "C5", "A4", "G4",
           "A4", "C5", "D5", "E5", "C5", "A4", "G4", "E4"]
_EVENING = ["E4", "G4", "A4", "G4", "E4", "D4", "C4", "D4",
            "E4", "G4", "E4", "D4", "C4", "D4", "E4", "C4"]

_tracks: dict[str, pygame.mixer.Sound] = {}


def _make_note(freq: float, duration: float, rate: int = 22050,
               volume: float = 0.08) -> list[int]:
    """Generate a soft sine note with attack-release envelope."""
    n = int(rate * duration)
    samples = []
    attack = 0.05
    release = 0.15
    for i in range(n):
        t = i / rate
        frac = i / n

        # ADSR envelope
        if frac < attack:
            env = frac / attack
        elif frac > (1.0 - release):
            env = (1.0 - frac) / release
        else:
            env = 1.0

        # Main tone + soft overtone for warmth
        val = (math.sin(2 * math.pi * freq * t) * 0.7 +
               math.sin(2 * math.pi * freq * 2 * t) * 0.15 +
               math.sin(2 * math.pi * freq * 0.5 * t) * 0.15)
        val = val * 32000 * volume * env
        samples.append(int(max(-32767, min(32767, val))))
    return samples


def _make_chord_pad(notes: list[str], duration: float, rate: int = 22050,
                    volume: float = 0.04) -> list[int]:
    """Generate a soft ambient pad from multiple notes."""
    n = int(rate * duration)
    samples = [0] * n
    for note_name in notes:
        freq = _NOTES.get(note_name, 440)
        for i in range(n):
            t = i / rate
            frac = i / n
            env = math.sin(frac * math.pi)  # bell curve
            val = math.sin(2 * math.pi * freq * t) * 32000 * volume * env
            samples[i] = int(max(-32767, min(32767, samples[i] + val)))
    return samples


def _generate_track(melody: list[str], name: str,
                    note_dur: float = 0.6,
                    pad_notes: list[str] | None = None) -> None:
    """Generate a loopable track from a melody sequence."""
    rate = 22050
    all_samples: list[int] = []

    # Generate melody
    for note_name in melody:
        freq = _NOTES.get(note_name, 440)
        note_samples = _make_note(freq, note_dur, rate, volume=0.07)
        all_samples.extend(note_samples)

    # Add ambient pad underneath (blended)
    if pad_notes:
        pad_dur = len(all_samples) / rate
        pad = _make_chord_pad(pad_notes, pad_dur, rate, volume=0.03)
        for i in range(min(len(all_samples), len(pad))):
            all_samples[i] = int(max(-32767, min(32767,
                                                  all_samples[i] + pad[i])))

    arr = array.array("h", all_samples)
    snd = pygame.mixer.Sound(buffer=arr)
    snd.set_volume(0.35)
    _tracks[name] = snd


def _ensure_tracks() -> None:
    """Generate all tracks if not already done."""
    if _tracks:
        return

    if not pygame.mixer.get_init():
        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)

    _generate_track(_MORNING, "morning", 0.55, ["C4", "E4", "G4"])
    _generate_track(_MIDDAY, "midday", 0.5, ["G4", "C5", "E5"])
    _generate_track(_EVENING, "evening", 0.7, ["C4", "E4", "A4"])


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def update_music(time_fraction: float) -> None:
    """Switch music track based on the time of day."""
    global _channel, _current_track

    _ensure_tracks()

    # Choose track
    if time_fraction < 0.30:
        target = "morning"
    elif time_fraction < 0.70:
        target = "midday"
    else:
        target = "evening"

    if target == _current_track and _channel and _channel.get_busy():
        return

    _current_track = target
    track = _tracks.get(target)
    if track:
        if _channel is None:
            _channel = pygame.mixer.find_channel(True)
        if _channel:
            _channel.play(track, loops=-1, fade_ms=2000)


def stop_music() -> None:
    """Stop the background music."""
    global _channel, _current_track
    if _channel:
        _channel.fadeout(1000)
    _current_track = ""


def set_volume(vol: float) -> None:
    """Set music volume (0.0 - 1.0)."""
    for snd in _tracks.values():
        snd.set_volume(vol)
