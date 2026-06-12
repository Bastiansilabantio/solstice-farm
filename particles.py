"""particles.py — Simple particle effects for Solstice Farm."""

from __future__ import annotations

import random

import pygame


class Particle:
    """A single particle with position, velocity, lifetime, and color."""

    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size",
                 "gravity")

    def __init__(self, x: float, y: float, vx: float, vy: float,
                 life: float, color: tuple[int, int, int],
                 size: int = 3, gravity: float = 0.0) -> None:
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size
        self.gravity = gravity

    def update(self, dt: float) -> bool:
        """Advance the particle. Returns False when dead."""
        self.life -= dt
        if self.life <= 0:
            return False
        self.vy += self.gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        return True


class ParticleSystem:
    """Manages all active particles."""

    def __init__(self) -> None:
        self.particles: list[Particle] = []

    def update(self, dt: float) -> None:
        self.particles = [p for p in self.particles if p.update(dt)]

    def draw(self, surface: pygame.Surface, cam_ox: int, cam_oy: int) -> None:
        for p in self.particles:
            alpha = max(0.0, min(1.0, p.life / p.max_life))
            sx = int(p.x) + cam_ox
            sy = int(p.y) + cam_oy
            size = max(1, int(p.size * alpha))

            # Draw with alpha via a tiny surface
            dot = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            a = int(alpha * 220)
            pygame.draw.circle(dot, (*p.color, a), (size, size), size)
            surface.blit(dot, (sx - size, sy - size))

    # ------------------------------------------------------------------
    # Effect spawners
    # ------------------------------------------------------------------

    def emit_water(self, wx: float, wy: float) -> None:
        """Blue water splash."""
        for _ in range(8):
            vx = random.uniform(-40, 40)
            vy = random.uniform(-80, -20)
            life = random.uniform(0.3, 0.6)
            color = random.choice([
                (80, 160, 240), (100, 180, 255), (60, 140, 220)
            ])
            self.particles.append(
                Particle(wx, wy, vx, vy, life, color, 3, 150)
            )

    def emit_harvest(self, wx: float, wy: float) -> None:
        """Gold sparkle burst."""
        for _ in range(12):
            vx = random.uniform(-60, 60)
            vy = random.uniform(-90, -10)
            life = random.uniform(0.4, 0.8)
            color = random.choice([
                (255, 220, 50), (255, 200, 30), (255, 240, 100),
                (255, 255, 180),
            ])
            self.particles.append(
                Particle(wx, wy, vx, vy, life, color, 4, 80)
            )

    def emit_till(self, wx: float, wy: float) -> None:
        """Brown dirt puff."""
        for _ in range(6):
            vx = random.uniform(-30, 30)
            vy = random.uniform(-50, -10)
            life = random.uniform(0.2, 0.5)
            color = random.choice([
                (140, 100, 55), (120, 85, 45), (160, 115, 65)
            ])
            self.particles.append(
                Particle(wx, wy, vx, vy, life, color, 3, 100)
            )

    def emit_plant(self, wx: float, wy: float) -> None:
        """Small green leaves."""
        for _ in range(5):
            vx = random.uniform(-25, 25)
            vy = random.uniform(-40, -5)
            life = random.uniform(0.3, 0.6)
            color = random.choice([
                (80, 180, 60), (100, 200, 70), (60, 160, 50)
            ])
            self.particles.append(
                Particle(wx, wy, vx, vy, life, color, 3, 60)
            )

    def emit_coins(self, wx: float, wy: float) -> None:
        """Gold coins flying up (for selling)."""
        for _ in range(8):
            vx = random.uniform(-30, 30)
            vy = random.uniform(-100, -40)
            life = random.uniform(0.5, 0.9)
            color = (255, 210, 40)
            self.particles.append(
                Particle(wx, wy, vx, vy, life, color, 4, 120)
            )

    # ------------------------------------------------------------------
    # Ambient / event effects
    # ------------------------------------------------------------------

    def emit_fireflies(self, screen_w: int, screen_h: int,
                       cam_x: float, cam_y: float, count: int = 2) -> None:
        """Spawn gentle fireflies (called each frame at dusk)."""
        for _ in range(count):
            wx = cam_x + random.uniform(0, screen_w)
            wy = cam_y + random.uniform(50, screen_h - 80)
            vx = random.uniform(-15, 15)
            vy = random.uniform(-20, 10)
            life = random.uniform(1.0, 2.5)
            color = random.choice([
                (200, 230, 80), (220, 255, 100), (180, 210, 60)
            ])
            self.particles.append(
                Particle(wx, wy, vx, vy, life, color, 2, -5)
            )

    def emit_sun_sparkles(self, screen_w: int, screen_h: int,
                          cam_x: float, cam_y: float,
                          count: int = 1) -> None:
        """Sparkling sunlight motes during peak sun."""
        for _ in range(count):
            wx = cam_x + random.uniform(0, screen_w)
            wy = cam_y + random.uniform(0, screen_h * 0.6)
            vx = random.uniform(-5, 5)
            vy = random.uniform(10, 30)
            life = random.uniform(0.5, 1.2)
            color = random.choice([
                (255, 250, 200), (255, 240, 150), (255, 255, 220)
            ])
            self.particles.append(
                Particle(wx, wy, vx, vy, life, color, 2, 5)
            )

    def emit_rain(self, screen_w: int, cam_x: float,
                  cam_y: float, count: int = 5) -> None:
        """Rain drops falling from top of screen."""
        for _ in range(count):
            wx = cam_x + random.uniform(0, screen_w)
            wy = cam_y - 10
            vx = random.uniform(-10, 10)
            vy = random.uniform(200, 350)
            life = random.uniform(0.4, 0.8)
            color = random.choice([
                (100, 160, 220), (80, 140, 200), (120, 180, 240)
            ])
            self.particles.append(
                Particle(wx, wy, vx, vy, life, color, 2, 50)
            )

    def emit_solstice_magic(self, wx: float, wy: float) -> None:
        """Purple/violet sparkles for Solstice Bloom."""
        for _ in range(6):
            vx = random.uniform(-35, 35)
            vy = random.uniform(-60, -10)
            life = random.uniform(0.4, 0.8)
            color = random.choice([
                (200, 140, 255), (180, 120, 240), (220, 170, 255),
                (255, 200, 255),
            ])
            self.particles.append(
                Particle(wx, wy, vx, vy, life, color, 3, 40)
            )

