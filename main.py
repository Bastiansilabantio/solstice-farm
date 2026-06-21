"""main.py — Entry point for Solstice Farm."""

import sys
import asyncio

import pygame

from game import Game
from settings import FPS, SCREEN_H, SCREEN_W


async def main() -> None:
    pygame.init()
    pygame.display.set_caption("🌾 Solstice Farm — A Summer Solstice Farming Game")
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.WINDOWMAXIMIZED | pygame.RESIZABLE | pygame.SCALED)
    clock = pygame.time.Clock()

    game = Game(screen)

    while True:
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 0.05)  # cap to avoid huge jumps

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            game.handle_event(event)

        game.update(dt)
        game.draw()
        pygame.display.flip()
        await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(main())
