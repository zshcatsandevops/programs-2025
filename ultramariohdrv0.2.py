"""
Super Mario Forever (Community Tribute)
Fan-made recreation built in Pygame — no copyrighted assets.
All sprites are generated procedurally using basic shapes and colors.

Author: Samsoft Universal API
License: BSD-Style (for demo purposes)
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import List, Sequence, Tuple
import pygame

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 540
FPS = 60
TILE_SIZE = 36
GRAVITY = 0.5
MAX_FALL_SPEED = 12
PLAYER_SPEED = 4
PLAYER_JUMP = 12

Color = Tuple[int, int, int]
FONT_PATH = None  # default font

# ─────────────────────────────────────────────
# Colors
# ─────────────────────────────────────────────
BACKGROUND_SKY: Color = (124, 194, 255)
BACKGROUND_GROUND: Color = (90, 180, 82)
PLAYER_BODY: Color = (240, 65, 53)
PLAYER_CAP: Color = (220, 0, 0)
BLOCK_COLOR: Color = (201, 154, 63)
BLOCK_EDGE: Color = (110, 78, 40)
GOAL_FLAG: Color = (255, 247, 135)
ENEMY_COLOR: Color = (156, 84, 32)
COIN_COLOR: Color = (255, 198, 0)

# ─────────────────────────────────────────────
# Entity Classes
# ─────────────────────────────────────────────
@dataclass
class Player:
    rect: pygame.Rect
    vel_x: float = 0.0
    vel_y: float = 0.0
    grounded: bool = False

    def update(self, tiles: Sequence[pygame.Rect], keys: Sequence[bool]) -> None:
        self.vel_x = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x -= PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x += PLAYER_SPEED

        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.grounded:
            self.vel_y = -PLAYER_JUMP
            self.grounded = False

        self.vel_y = min(self.vel_y + GRAVITY, MAX_FALL_SPEED)
        self._move_axis(tiles, self.vel_x, 0)
        self._move_axis(tiles, 0, self.vel_y)

    def _move_axis(self, tiles: Sequence[pygame.Rect], dx: float, dy: float) -> None:
        self.rect.x += int(dx)
        self.rect.y += int(dy)
        for tile in tiles:
            if self.rect.colliderect(tile):
                if dx > 0:
                    self.rect.right = tile.left
                if dx < 0:
                    self.rect.left = tile.right
                if dy > 0:
                    self.rect.bottom = tile.top
                    self.vel_y = 0
                    self.grounded = True
                if dy < 0:
                    self.rect.top = tile.bottom
                    self.vel_y = 0

    def draw(self, surface: pygame.Surface) -> None:
        body_rect = self.rect.copy()
        cap_rect = pygame.Rect(body_rect.x, body_rect.y - 6, body_rect.width, 10)
        pygame.draw.rect(surface, PLAYER_BODY, body_rect)
        pygame.draw.rect(surface, PLAYER_CAP, cap_rect)


@dataclass
class Enemy:
    rect: pygame.Rect
    speed: float
    direction: int = 1

    def update(self, tiles: Sequence[pygame.Rect]) -> None:
        self.rect.x += int(self.speed * self.direction)
        for tile in tiles:
            if self.rect.colliderect(tile):
                if self.direction > 0:
                    self.rect.right = tile.left
                else:
                    self.rect.left = tile.right
                self.direction *= -1
                break

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, ENEMY_COLOR, self.rect)


@dataclass
class Coin:
    rect: pygame.Rect
    pulse: float = 0.0

    def update(self) -> None:
        self.pulse = (self.pulse + 0.07) % (2 * math.pi)

    def draw(self, surface: pygame.Surface) -> None:
        radius = int(self.rect.width // 2 + math.sin(self.pulse) * 2)
        pygame.draw.circle(surface, COIN_COLOR, self.rect.center, radius)


# ─────────────────────────────────────────────
# Level Definition
# ─────────────────────────────────────────────
@dataclass
class Level:
    layout: List[str]
    background: Color

    def __post_init__(self) -> None:
        self.tiles: List[pygame.Rect] = []
        self.enemies: List[Enemy] = []
        self.coins: List[Coin] = []
        self.goal_rect: pygame.Rect | None = None
        self.spawn_point = pygame.Vector2(80, 80)
        self._parse_layout()

    def _parse_layout(self) -> None:
        for row_idx, row in enumerate(self.layout):
            for col_idx, cell in enumerate(row):
                x, y = col_idx * TILE_SIZE, row_idx * TILE_SIZE
                if cell == "#":
                    self.tiles.append(pygame.Rect(x, y, TILE_SIZE, TILE_SIZE))
                elif cell == "E":
                    self.enemies.append(Enemy(pygame.Rect(x, y, TILE_SIZE, TILE_SIZE), speed=2))
                elif cell == "C":
                    self.coins.append(Coin(pygame.Rect(x + 8, y + 8, TILE_SIZE - 16, TILE_SIZE - 16)))
                elif cell == "S":
                    self.spawn_point = pygame.Vector2(x, y - TILE_SIZE)
                elif cell == "G":
                    self.goal_rect = pygame.Rect(x + 8, y + 8, TILE_SIZE - 16, TILE_SIZE - 16)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(self.background)
        ground = pygame.Rect(0, SCREEN_HEIGHT - TILE_SIZE, SCREEN_WIDTH, TILE_SIZE)
        pygame.draw.rect(surface, BACKGROUND_GROUND, ground)

        for tile in self.tiles:
            pygame.draw.rect(surface, BLOCK_COLOR, tile)
            pygame.draw.rect(surface, BLOCK_EDGE, tile, 2)

        for coin in self.coins:
            coin.draw(surface)
        for enemy in self.enemies:
            enemy.draw(surface)
        if self.goal_rect:
            pygame.draw.rect(surface, GOAL_FLAG, self.goal_rect)


# ─────────────────────────────────────────────
# Levels
# ─────────────────────────────────────────────
LEVELS: Tuple[Level, ...] = (
    Level(
        [
            "#                                #",
            "#         C                      #",
            "#                                #",
            "#     #######       E            #",
            "#                                #",
            "#S                               #",
            "##################################",
        ],
        (135, 206, 250),
    ),
    Level(
        [
            "#                                #",
            "#   C      ###                   #",
            "#          ###        E          #",
            "#                                #",
            "#      #####                     #",
            "#                 #######        #",
            "#S                               #",
            "##################################",
        ],
        (120, 210, 248),
    ),
    Level(
        [
            "#                                #",
            "#   C         ###                #",
            "#              ###           E   #",
            "#                                #",
            "#      #####                     #",
            "#                 #######        #",
            "#S                C      G       #",
            "##################################",
        ],
        (110, 200, 240),
    ),
)

# ─────────────────────────────────────────────
# Game Controller
# ─────────────────────────────────────────────
class GameState:
    def __init__(self) -> None:
        self.level_index = 0
        self.player = Player(pygame.Rect(0, 0, TILE_SIZE - 8, TILE_SIZE - 8))
        self.score = 0
        self.collected = set()
        self.state = "menu"
        self.font = pygame.font.Font(FONT_PATH, 32)
        self.big_font = pygame.font.Font(FONT_PATH, 64)
        self.reset_level()

    @property
    def level(self) -> Level:
        return LEVELS[self.level_index]

    def reset_level(self) -> None:
        lvl = self.level
        self.player.rect.topleft = (int(lvl.spawn_point.x), int(lvl.spawn_point.y))
        self.player.vel_x = self.player.vel_y = 0
        self.player.grounded = False
        self.collected.clear()

    def update(self, keys: Sequence[bool]) -> None:
        if self.state == "playing":
            self._update_playing(keys)
        elif self.state in ("menu", "victory", "final"):
            if keys[pygame.K_RETURN]:
                if self.state == "menu":
                    self.state = "playing"
                elif self.state == "victory":
                    if self.level_index < len(LEVELS) - 1:
                        self.level_index += 1
                        self.reset_level()
                        self.state = "playing"
                    else:
                        self.state = "final"
                elif self.state == "final":
                    self.level_index = 0
                    self.score = 0
                    self.reset_level()
                    self.state = "menu"

    def _update_playing(self, keys: Sequence[bool]) -> None:
        lvl = self.level
        self.player.update(lvl.tiles, keys)

        for enemy in lvl.enemies:
            enemy.update(lvl.tiles)
            if self.player.rect.colliderect(enemy.rect):
                if self.player.vel_y > 0 and self.player.rect.bottom <= enemy.rect.top + 10:
                    enemy.rect.y = SCREEN_HEIGHT + 100
                    self.player.vel_y = -PLAYER_JUMP / 1.5
                else:
                    self.reset_level()
                    break

        for i, coin in enumerate(lvl.coins):
            coin.update()
            if i not in self.collected and self.player.rect.colliderect(coin.rect):
                self.collected.add(i)
                self.score += 100

        if lvl.goal_rect and self.player.rect.colliderect(lvl.goal_rect):
            self.state = "victory"

    def draw(self, surface: pygame.Surface) -> None:
        lvl = self.level
        lvl.draw(surface)
        self.player.draw(surface)

        score_surf = self.font.render(f"Score: {self.score}", True, (0, 0, 0))
        surface.blit(score_surf, (16, 16))

        if self.state == "menu":
            self._center(surface, "Super Mario Forever", self.big_font, (255, 255, 255), 150)
            self._center(surface, "Community Tribute", self.font, (255, 255, 0), 220)
            self._center(surface, "Press Enter to Start", self.font, (0, 0, 0), 340)
        elif self.state == "victory":
            self._center(surface, "Course Clear!", self.big_font, (255, 255, 255), 180)
            self._center(surface, "Press Enter for Next Level", self.font, (0, 0, 0), 260)
        elif self.state == "final":
            self._center(surface, "Thanks for Playing!", self.big_font, (255, 255, 255), 180)
            self._center(surface, "Press Enter to return to Menu", self.font, (0, 0, 0), 260)

    def _center(self, surface, text, font, color, y):
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=(SCREEN_WIDTH // 2, y))
        surface.blit(surf, rect)


# ─────────────────────────────────────────────
# Main Entry
# ─────────────────────────────────────────────
def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Super Mario Forever Community Tribute")
    clock = pygame.time.Clock()

    game = GameState()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            running = False

        game.update(keys)
        game.draw(screen)  # ✅ fixed typo here
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
