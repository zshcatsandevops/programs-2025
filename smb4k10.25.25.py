#!/usr/bin/env python3
"""
Ultra Mario 2D Bros — Engine Core (Synth/PPU Edition)
-----------------------------------------------------
Part 1 of 2 — Core engine, PPU, APU, physics, camera, basic test level.
60 FPS, 22 kHz synth, pure Pygame.
-----------------------------------------------------
"""

import math, random, sys, time
from array import array
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple
import pygame

# =========================================================
# Global config
# =========================================================
SCALE = 3
BASE_TILE = 8
TILE_PIX = BASE_TILE * SCALE
SCREEN_WIDTH, SCREEN_HEIGHT = 600, 400
FPS = 60

GRAVITY = 0.8
JUMP_STRENGTH = -15
MOVE_SPEED = 5
MAX_FALL_SPEED = 15

# Colors
SKY_BLUE = (107, 140, 255)
RED = (255, 0, 0)
BROWN = (139, 69, 19)

# =========================================================
# Init Pygame + audio
# =========================================================
pygame.init()
AUDIO_ENABLED = True
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
except Exception:
    AUDIO_ENABLED = False
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Ultra Mario 2D Bros — Synth/PPU Core")
clock = pygame.time.Clock()

# =========================================================
# Helpers
# =========================================================
def note_freq(midi: int) -> float:
    return 440.0 * (2 ** ((midi - 69) / 12))

# =========================================================
# Tile constants
# =========================================================
class T:
    EMPTY, BLOCK, GROUND = range(3)

# =========================================================
# PPU Renderer
# =========================================================
class PPU:
    def __init__(self, scale=SCALE):
        self.scale = scale
        self.tile_pix = BASE_TILE * scale
        self._tile_cache = {}
        self.bg_palettes = [
            [(0, 0, 0), (255, 255, 255), (200, 200, 200), (255, 0, 0)],
            [(0, 0, 0), (80, 160, 255), (200, 200, 255), (255, 255, 255)],
        ]

    def _tile_pattern(self, tid: int):
        rng = random.Random(tid * 777)
        return [[rng.randint(0, 1) for _ in range(8)] for _ in range(8)]

    def tile_surface(self, tid: int, pal_idx=0):
        key = (tid, pal_idx)
        if key in self._tile_cache:
            return self._tile_cache[key]
        palette = self.bg_palettes[pal_idx % len(self.bg_palettes)]
        surf = pygame.Surface((self.tile_pix, self.tile_pix))
        pattern = self._tile_pattern(tid)
        for y in range(8):
            for x in range(8):
                c = palette[pattern[y][x]]
                pygame.draw.rect(surf, c, (x * self.scale, y * self.scale, self.scale, self.scale))
        self._tile_cache[key] = surf
        return surf

# =========================================================
# APU Synth
# =========================================================
class APU:
    def __init__(self):
        self.enabled = AUDIO_ENABLED
        if not self.enabled: return
        self.sfx_channel = pygame.mixer.Channel(0)
        self.jump = self._make_jump()
        self.bump = self._make_noise(80)

    def _make_noise(self, ms, vol=0.3):
        n = int(22050 * ms / 1000)
        buf = array('h')
        amp = int(32767 * vol)
        reg = 1
        for _ in range(n):
            bit = (reg ^ (reg >> 1)) & 1
            reg = (reg >> 1) | (bit << 14)
            v = amp if reg & 1 else -amp
            buf.extend((v, v))
        return pygame.mixer.Sound(buffer=buf.tobytes())

    def _make_jump(self):
        sr = 22050
        buf = array('h')
        for i in range(int(sr * 0.1)):
            f = 200 + 400 * (1 - i / (sr * 0.1))
            val = math.sin(2 * math.pi * f * (i / sr))
            s = int(val * 16000)
            buf.extend((s, s))
        return pygame.mixer.Sound(buffer=buf.tobytes())

    def play_jump(self):
        if self.enabled:
            self.sfx_channel.play(self.jump)

    def play_bump(self):
        if self.enabled:
            self.sfx_channel.play(self.bump)

# =========================================================
# Mario + Physics
# =========================================================
class Mario:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TILE_PIX, TILE_PIX * 2)
        self.vel_x = self.vel_y = 0
        self.on_ground = False
        self.facing_right = True

    def handle_input(self, keys, apu):
        self.vel_x = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -MOVE_SPEED
            self.facing_right = False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = MOVE_SPEED
            self.facing_right = True
        if (keys[pygame.K_UP] or keys[pygame.K_SPACE]) and self.on_ground:
            self.vel_y = JUMP_STRENGTH
            self.on_ground = False
            apu.play_jump()

    def update(self, tiles):
        self.vel_y += GRAVITY
        if self.vel_y > MAX_FALL_SPEED:
            self.vel_y = MAX_FALL_SPEED
        self.rect.x += int(self.vel_x)
        self.rect.y += int(self.vel_y)
        # simple ground
        ground_y = SCREEN_HEIGHT - 2 * TILE_PIX
        if self.rect.bottom >= ground_y:
            self.rect.bottom = ground_y
            self.vel_y = 0
            self.on_ground = True

    def draw(self, surf):
        pygame.draw.rect(surf, RED, self.rect)

# =========================================================
# Camera + Level
# =========================================================
class Camera:
    def __init__(self):
        self.x = 0

    def apply(self, rect):
        return rect.move(-self.x, 0)

class Level:
    def __init__(self, ppu):
        self.ppu = ppu
        self.tiles = []
        self._build_test_level()

    def _build_test_level(self):
        cols, rows = 64, 15
        self.tiles = [[T.EMPTY for _ in range(cols)] for _ in range(rows)]
        g = rows - 2
        for x in range(cols):
            self.tiles[g][x] = T.GROUND
            if 10 < x < 15:
                self.tiles[g - 1][x] = T.BLOCK

    def draw(self, surf, cam):
        ts = TILE_PIX
        for y, row in enumerate(self.tiles):
            for x, tid in enumerate(row):
                if tid != T.EMPTY:
                    tile = self.ppu.tile_surface(tid)
                    surf.blit(tile, (x * ts - cam.x, y * ts))

# =========================================================
# Game Loop
# =========================================================
def main():
    ppu = PPU()
    apu = APU()
    level = Level(ppu)
    mario = Mario(4 * TILE_PIX, SCREEN_HEIGHT - 4 * TILE_PIX)
    cam = Camera()
    running = True
    while running:
        dt = clock.tick(FPS) / 1000
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
        keys = pygame.key.get_pressed()
        mario.handle_input(keys, apu)
        mario.update(level.tiles)
        cam.x = mario.rect.centerx - SCREEN_WIDTH // 2
        # Draw
        screen.fill(SKY_BLUE)
        level.draw(screen, cam)
        mario.draw(screen)
        pygame.display.flip()
    pygame.quit()

if __name__ == "__main__":
    main()
