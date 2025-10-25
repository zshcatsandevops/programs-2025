#!/usr/bin/env python3
"""
Ultra Mario 2D Bros — Files=OFF, PPU/APU-synth, single-file edition
- No external images, sounds, or music.
- NES PPU-inspired rendering: 8x8 tiles + palettes (scaled up).
- Simple APU-like chiptune synth for music/SFX (square + noise).
- Keeps your overall architecture; replaces all media with data synth.

Controls:
  Arrow Keys / A,D   : Move
  Space / W / Up     : Jump
  ESC                : Pause / Back
  R                  : Restart level
  N                  : Next level (test)
  Enter              : Select (menu/level-select)

Tested target: pygame 2.x
"""

import math
import random
import sys
import time
from array import array
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

import pygame

# ---------------------------------------------------------------------------
# Global config (no files, all synth)
# ---------------------------------------------------------------------------

# Screen: keep close to your original while honoring 8x8 tiles scaling nicely.
SCALE = 3            # 8x8 tiles → 24x24 logical pixels
BASE_TILE = 8
TILE_PIX = BASE_TILE * SCALE  # 24px per tile
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Physics
GRAVITY = 0.8
JUMP_STRENGTH = -15
MOVE_SPEED = 5
MAX_FALL_SPEED = 15

# Colors (RGB)
BLACK   = (0, 0, 0)
WHITE   = (255, 255, 255)
RED     = (220, 20, 60)
GREEN   = (0, 200, 70)
BLUE    = (0, 110, 255)
BROWN   = (139, 69, 19)
YELLOW  = (255, 220, 0)
ORANGE  = (255, 140, 0)
SKY_BLUE= (120, 170, 255)
DARKGRAY= (50, 50, 60)
LIGHT   = (240, 240, 240)

# ---------------------------------------------------------------------------
# Safe pygame init (no external media)
# ---------------------------------------------------------------------------

pygame.init()

# Mixer: try to init; if fails, run silent.
AUDIO_ENABLED = True
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
except Exception:
    AUDIO_ENABLED = False

# Display / Clock
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Ultra Mario 2D Bros — Synth/PPU build (no files)")
clock = pygame.time.Clock()

# ---------------------------------------------------------------------------
# Game enums / dataclasses
# ---------------------------------------------------------------------------

class GameState(Enum):
    MENU = 1
    PLAYING = 2
    PAUSED = 3
    GAME_OVER = 4

class PowerUpState(Enum):
    SMALL = 1
    SUPER = 2
    FIRE = 3  # kept for structure; color swap sprite

@dataclass
class LevelData:
    world: int
    level: int
    theme: str   # 'overworld', 'underground', 'castle', 'underwater' (color/music swaps)
    time_limit: int

    def display_name(self) -> str:
        return f"World {self.world}-{self.level}"

# ---------------------------------------------------------------------------
# NES-ish PPU: tile patterns, palettes, sprite builder (all synthesized)
# ---------------------------------------------------------------------------

class PPU:
    """
    Minimal NES-PPU-inspired renderer:
    - 8x8 tiles (2-bit color indices, here we store directly as 0..3 ints).
    - 4-color palettes. We'll keep a few BG palettes and a few SPR palettes.
    - We scale tiles by SCALE for display.
    - Provides: tile surfaces, sprite assembly, draw tilemap with scroll.
    """
    def __init__(self, scale: int = SCALE):
        self.scale = scale
        self.tile_size = BASE_TILE
        self.tile_pix = self.tile_size * self.scale

        # Palettes: 4 entries per palette (index 0..3)
        # You can extend/swap by theme for variety.
        self.bg_palettes = [
            [ (92,148,252), (0, 168, 0), (222, 165, 115), (56, 56, 56) ],  # sky/grass/ground
            [ (0,0,0), (80,80,80), (160,160,160), (240,240,240) ],         # underground gray
            [ (20,20,20), (120,40,40), (200,80,60), (240,240,200) ],       # castle warm
            [ (16,40,96), (16,96,160), (32,160,192), (64,208,240) ],       # underwater blues
        ]
        self.spr_palettes = [
            [ (255,255,255), (255,0,0), (255,160,0), (100,40,0) ],         # Mario-ish
            [ (255,255,255), (0,200,70), (0,120,40), (20,20,20) ],         # Koopa-ish
            [ (255,255,255), (220,220,0), (160,160,0), (20,20,20) ],       # Star/Mushroom-ish
        ]

        # Tile cache: (tile_id,palette_idx) -> Surface
        self._tile_cache: Dict[Tuple[int,int], pygame.Surface] = {}
        # Sprite cache: arbitrary keys -> Surface
        self._sprite_cache: Dict[str, pygame.Surface] = {}

        # Build a tiny font (only needed letters/numbers) as tiles 200.. (ID space shared)
        self.font_tiles: Dict[str, List[List[int]]] = {}
        self._build_mini_font()

    # ------------ Tile pattern helpers ------------

    @staticmethod
    def _empty_pattern() -> List[List[int]]:
        return [[0]*8 for _ in range(8)]

    @staticmethod
    def _checker(a: int, b: int) -> List[List[int]]:
        # Simple checker pattern for "brick"
        pat = []
        for y in range(8):
            row = []
            for x in range(8):
                row.append(a if ((x//2 + y//2) % 2 == 0) else b)
            pat.append(row)
        return pat

    @staticmethod
    def _stripe_v(a: int, b: int, w: int=2) -> List[List[int]]:
        pat = []
        for y in range(8):
            row = []
            for x in range(8):
                row.append(a if (x % (w*2) < w) else b)
            pat.append(row)
        return pat

    @staticmethod
    def _stripe_h(a: int, b: int, h: int=2) -> List[List[int]]:
        pat = []
        for y in range(8):
            row = [a if (y % (h*2) < h) else b for _ in range(8)]
            pat.append(row)
        return pat

    @staticmethod
    def _question_block() -> List[List[int]]:
        # palette indices: 0 bg, 1 mid, 2 bright, 3 dark
        pat = [[1]*8 for _ in range(8)]
        # draw a "?" simplified
        for x in range(2,6): pat[1][x] = 2
        pat[2][5] = 2; pat[3][5] = 2
        for x in range(2,5): pat[3][x] = 2
        pat[4][2] = 2
        pat[6][3] = 2
        # border
        for x in range(8): pat[0][x] = 3; pat[7][x] = 3
        for y in range(8): pat[y][0] = 3; pat[y][7] = 3
        return pat

    @staticmethod
    def _pipe_top() -> List[List[int]]:
        pat = PPU._stripe_v(1,2, w=3)
        # top rim
        for x in range(8): pat[1][x] = 3
        for x in range(8): pat[0][x] = 3
        return pat

    @staticmethod
    def _pipe_body() -> List[List[int]]:
        return PPU._stripe_v(1,2, w=3)

    def _build_mini_font(self):
        # Minimal 5x7 bitmap inside 8x8 tile (centered) for digits/letters used in HUD
        # Characters: digits 0-9 and letters needed for SCORE, COINS, LIVES, WORLD, TIME, PAUSED, GAME OVER
        FONT = {}
        def glyph(rows: List[str]) -> List[List[int]]:
            # rows: list of strings of ' ' or '#', max 5 columns, 7 rows
            canvas = [[0]*8 for _ in range(8)]
            offx, offy = 1, 1
            for y, r in enumerate(rows):
                for x, ch in enumerate(r):
                    if ch == '#':
                        canvas[offy+y][offx+x] = 3  # brightest
            return canvas

        # Digits
        FONT['0'] = glyph([" ### ",
                           "#   #",
                           "#  ##",
                           "# # #",
                           "##  #",
                           "#   #",
                           " ### "])
        FONT['1'] = glyph(["  #  ",
                           " ##  ",
                           "# #  ",
                           "  #  ",
                           "  #  ",
                           "  #  ",
                           "#####"])
        FONT['2'] = glyph([" ### ",
                           "#   #",
                           "    #",
                           "   # ",
                           "  #  ",
                           " #   ",
                           "#####"])
        FONT['3'] = glyph([" ### ",
                           "    #",
                           "    #",
                           " ### ",
                           "    #",
                           "    #",
                           " ### "])
        FONT['4'] = glyph(["   # ",
                           "  ## ",
                           " # # ",
                           "#  # ",
                           "#####",
                           "   # ",
                           "   # "])
        FONT['5'] = glyph(["#####",
                           "#    ",
                           "#    ",
                           "#### ",
                           "    #",
                           "    #",
                           "#### "])
        FONT['6'] = glyph([" ### ",
                           "#    ",
                           "#    ",
                           "#### ",
                           "#   #",
                           "#   #",
                           " ### "])
        FONT['7'] = glyph(["#####",
                           "    #",
                           "   # ",
                           "  #  ",
                           "  #  ",
                           "  #  ",
                           "  #  "])
        FONT['8'] = glyph([" ### ",
                           "#   #",
                           "#   #",
                           " ### ",
                           "#   #",
                           "#   #",
                           " ### "])
        FONT['9'] = glyph([" ### ",
                           "#   #",
                           "#   #",
                           " ####",
                           "    #",
                           "    #",
                           " ### "])

        # Letters (subset)
        letters = {
            'A': [" ### ",
                  "#   #",
                  "#   #",
                  "#####",
                  "#   #",
                  "#   #",
                  "#   #"],
            'C': [" ### ",
                  "#   #",
                  "#    ",
                  "#    ",
                  "#    ",
                  "#   #",
                  " ### "],
            'D': ["#### ",
                  "#   #",
                  "#   #",
                  "#   #",
                  "#   #",
                  "#   #",
                  "#### "],
            'E': ["#####",
                  "#    ",
                  "#    ",
                  "#### ",
                  "#    ",
                  "#    ",
                  "#####"],
            'G': [" ### ",
                  "#   #",
                  "#    ",
                  "#  ##",
                  "#   #",
                  "#   #",
                  " ####"],
            'I': ["#####",
                  "  #  ",
                  "  #  ",
                  "  #  ",
                  "  #  ",
                  "  #  ",
                  "#####"],
            'L': ["#    ",
                  "#    ",
                  "#    ",
                  "#    ",
                  "#    ",
                  "#    ",
                  "#####"],
            'M': ["#   #",
                  "## ##",
                  "# # #",
                  "# # #",
                  "#   #",
                  "#   #",
                  "#   #"],
            'O': [" ### ",
                  "#   #",
                  "#   #",
                  "#   #",
                  "#   #",
                  "#   #",
                  " ### "],
            'P': ["#### ",
                  "#   #",
                  "#   #",
                  "#### ",
                  "#    ",
                  "#    ",
                  "#    "],
            'R': ["#### ",
                  "#   #",
                  "#   #",
                  "#### ",
                  "# #  ",
                  "#  # ",
                  "#   #"],
            'S': [" ####",
                  "#    ",
                  "#    ",
                  " ### ",
                  "    #",
                  "    #",
                  "#### "],
            'T': ["#####",
                  "  #  ",
                  "  #  ",
                  "  #  ",
                  "  #  ",
                  "  #  ",
                  "  #  "],
            'V': ["#   #",
                  "#   #",
                  "#   #",
                  "#   #",
                  "#   #",
                  " # # ",
                  "  #  "],
            'W': ["#   #",
                  "#   #",
                  "#   #",
                  "# # #",
                  "# # #",
                  "## ##",
                  "#   #"],
        }
        for k, rows in letters.items():
            FONT[k] = glyph(rows)

        self.font_tiles = FONT

    def _pattern_to_surface(self, pattern: List[List[int]], palette: List[Tuple[int,int,int]]) -> pygame.Surface:
        # Convert 8x8 indices (0..3) to scaled Surface
        surf = pygame.Surface((self.tile_pix, self.tile_pix), pygame.SRCALPHA)
        for y in range(8):
            for x in range(8):
                idx = max(0, min(3, pattern[y][x]))
                color = palette[idx]
                pygame.draw.rect(surf, color, (x*self.scale, y*self.scale, self.scale, self.scale))
        return surf

    # Tile IDs (background)
    # 0: empty, 1: ground top, 2: ground body, 3: brick, 4: question, 5: pipe_top_L, 6: pipe_top_R, 7: pipe_body_L, 8: pipe_body_R, 9: flagpole
    def _tile_pattern(self, tile_id: int) -> List[List[int]]:
        if tile_id == 0:
            return self._empty_pattern()
        if tile_id == 1:
            # ground "top" (dirt + grass)
            pat = self._stripe_h(0,1, h=1)
            for x in range(8):
                pat[1][x] = 2
            return pat
        if tile_id == 2:
            # ground body
            return self._checker(1,0)
        if tile_id == 3:
            # brick
            return self._checker(2,3)
        if tile_id == 4:
            return self._question_block()
        if tile_id == 5:
            return self._pipe_top()
        if tile_id == 6:
            return self._pipe_top()
        if tile_id == 7:
            return self._pipe_body()
        if tile_id == 8:
            return self._pipe_body()
        if tile_id == 9:
            # Flagpole segment
            pat = self._empty_pattern()
            for y in range(8):
                pat[y][3] = 3
            return pat
        return self._empty_pattern()

    def tile_surface(self, tile_id: int, palette_index: int) -> pygame.Surface:
        key = (tile_id, palette_index)
        if key in self._tile_cache:
            return self._tile_cache[key]
        palette = self.bg_palettes[palette_index % len(self.bg_palettes)]
        surf = self._pattern_to_surface(self._tile_pattern(tile_id), palette)
        self._tile_cache[key] = surf
        return surf

    # Draw text via tiles (monochrome-ish using palette 0)
    def draw_text(self, target: pygame.Surface, text: str, x: int, y: int, palette_index: int = 0):
        palette = self.bg_palettes[palette_index % len(self.bg_palettes)]
        for i, ch in enumerate(text):
            if ch == ' ':
                continue
            tile = self.font_tiles.get(ch.upper())
            if tile:
                surf = self._pattern_to_surface(tile, palette)
                target.blit(surf, (x + i*self.tile_pix, y))

    # Sprite builder: compose a small multi-tile sprite into a Surface, cache by key.
    def sprite_surface(self, key: str, pattern_tiles: List[List[List[int]]], palette_index: int) -> pygame.Surface:
        cache_key = f"{key}:{palette_index}"
        if cache_key in self._sprite_cache:
            return self._sprite_cache[cache_key]
        palette = self.spr_palettes[palette_index % len(self.spr_palettes)]
        # pattern_tiles: grid of 8x8 index matrices
        rows = len(pattern_tiles)
        cols = len(pattern_tiles[0]) if rows else 0
        surf = pygame.Surface((cols*self.tile_pix, rows*self.tile_pix), pygame.SRCALPHA)
        for r in range(rows):
            for c in range(cols):
                tile_surf = self._pattern_to_surface(pattern_tiles[r][c], palette)
                surf.blit(tile_surf, (c*self.tile_pix, r*self.tile_pix))
        self._sprite_cache[cache_key] = surf
        return surf

    # Mario small: 2x2 tiles; super: 2x3 tiles. Simple silhouette with accent colors.
    @staticmethod
    def _mario_small_tiles() -> List[List[List[int]]]:
        def fill(col: int):
            return [[col]*8 for _ in range(8)]
        head = fill(1)
        hat = fill(2)
        body= fill(3)
        # carve face/hat lines
        for x in range(8): hat[1][x]=2; hat[0][x]=2
        for y in range(2,6): head[y][1]=0; head[y][6]=0
        return [
            [hat, head],
            [body, body],
        ]

    @staticmethod
    def _mario_super_tiles() -> List[List[List[int]]]:
        def fill(col: int): return [[col]*8 for _ in range(8)]
        hat = fill(2); head = fill(1); torso = fill(3); legs = fill(3)
        for x in range(8): hat[0][x]=2; hat[1][x]=2
        for y in range(2,6): head[y][1]=0; head[y][6]=0
        return [
            [hat, head],
            [torso, torso],
            [legs, legs],
        ]

# ---------------------------------------------------------------------------
# Tiny chiptune APU: synth square/noise SFX + short looping tracks
# ---------------------------------------------------------------------------

def note_freq(midi: int) -> float:
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))

class APU:
    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate
        self.enabled = AUDIO_ENABLED
        if self.enabled:
            self.channels = [pygame.mixer.Channel(0), pygame.mixer.Channel(1)]
            self.sfx_channel = pygame.mixer.Channel(2)
        # pre-generate short SFX
        self.sounds = {}
        self._build_sfx()
        # music
        self.current_track = None

    # ---- low-level synth primitives ----

    def _tone(self, freq: float, ms: int, duty: float=0.5, volume: float=0.3) -> bytes:
        """Return stereo 16-bit signed little-endian samples for a square wave tone."""
        n_samples = int(self.sample_rate * ms / 1000.0)
        if n_samples <= 0 or freq <= 0:
            return (array('h', [0]* (n_samples*2))).tobytes()
        period = self.sample_rate / freq
        # Simple ADSR-ish env
        attack = int(0.01 * n_samples)
        release = int(0.05 * n_samples)

        out = array('h')
        amp = int(32767 * volume)
        phase = 0.0
        for i in range(n_samples):
            # Square with duty
            v = amp if (phase/period) % 1.0 < duty else -amp
            # envelope
            if i < attack:
                v = int(v * (i / max(1, attack)))
            elif i > n_samples - release:
                v = int(v * ( (n_samples - i) / max(1, release) ))
            # stereo duplicate
            out.append(v)
            out.append(v)
            phase += 1.0
        return out.tobytes()

    def _noise(self, ms: int, volume: float=0.3) -> bytes:
        n_samples = int(self.sample_rate * ms / 1000.0)
        out = array('h')
        amp = int(32767 * volume)
        for i in range(n_samples):
            v = random.randint(-amp, amp)
            out.extend((v, v))
        return out.tobytes()

    def _concat(self, parts: List[bytes]) -> bytes:
        return b''.join(parts)

    # ---- SFX ----

    def _build_sfx(self):
        # Generate short SFX
        def make(name, data):
            if not self.enabled: return
            self.sounds[name] = pygame.mixer.Sound(buffer=data)

        # Jump: up-chirp
        jump = self._concat([
            self._tone(note_freq(64), 50, duty=0.25, volume=0.25),
            self._tone(note_freq(69), 70, duty=0.25, volume=0.25),
        ])
        coin = self._concat([
            self._tone(note_freq(81), 30, duty=0.5, volume=0.2),
            self._tone(note_freq(93), 30, duty=0.5, volume=0.2),
        ])
        stomp = self._noise(60, 0.25)
        powerup = self._concat([
            self._tone(note_freq(74), 50, duty=0.25, volume=0.25),
            self._tone(note_freq(78), 50, duty=0.25, volume=0.25),
            self._tone(note_freq(81), 70, duty=0.25, volume=0.25),
        ])
        death = self._concat([
            self._tone(note_freq(72), 120, duty=0.5, volume=0.25),
            self._tone(note_freq(65), 180, duty=0.5, volume=0.20),
            self._tone(note_freq(57), 250, duty=0.5, volume=0.15),
        ])

        make('jump', jump)
        make('coin', coin)
        make('stomp', stomp)
        make('powerup', powerup)
        make('death', death)
        # flagpole/worldclear/gameover can be built similarly if needed.

    def play_sfx(self, name: str):
        if not self.enabled: return
        s = self.sounds.get(name)
        if s:
            self.sfx_channel.play(s)

    # ---- Simple music loops (original, non-copyright) ----

    def _build_loop_bytes(self, theme: str) -> bytes:
        """
        Build an ~8s loop by mixing two square channels.
        Patterns are intentionally original (not SMB melodies).
        """
        sr = self.sample_rate
        total_ms = 8000
        steps = []  # (freq1, freq2, ms)
        if theme == 'underground':
            base = [45, 45, 45, 40, 43, 40, 38, 36]  # low minor ostinato
            for m in base:
                steps.append((note_freq(m), 0.0, 250))
        elif theme == 'castle':
            seq1 = [60, 63, 67, 70, 67, 63, 60, 55]  # tense arpeggio
            for m in seq1:
                steps.append((note_freq(m), note_freq(m-12), 250))
        elif theme == 'underwater':
            seq = [64, 67, 71, 74, 71, 67]  # floaty triad
            for m in seq*6:
                steps.append((note_freq(m), 0.0, 200))
        else:
            # overworld default: bouncy I–V–vi–IV outline
            seq1 = [60, 67, 69, 65, 60, 67, 69, 72]
            seq2 = [55, 55, 57, 50, 55, 55, 57, 48]
            for a, b in zip(seq1*4, seq2*4):
                steps.append((note_freq(a), note_freq(b), 125))

        # Mix down
        L = int(sr * total_ms / 1000)
        mix = array('h', [0]*(L*2))
        t = 0
        for f1, f2, ms in steps:
            n = int(sr * ms / 1000)
            for i in range(n):
                idx = t + i
                if idx >= L: break
                # generate instantaneous square for both channels
                v = 0
                if f1 > 0:
                    period1 = sr / f1
                    v += (1 if ((i % period1) / period1) < 0.5 else -1) * 8000
                if f2 > 0:
                    period2 = sr / f2
                    v += (1 if ((i % period2) / period2) < 0.25 else -1) * 6000
                # write stereo with simple limiter
                vx = max(-30000, min(30000, v))
                j = idx*2
                mix[j] = mix[j] + vx if -32768 < mix[j] + vx < 32767 else int(max(-32768, min(32767, mix[j] + vx)))
                mix[j+1] = mix[j]
            t += n
            if t >= L: break

        return mix.tobytes()

    def play_music(self, theme: str):
        if not self.enabled: 
            self.current_track = theme
            return
        data = self._build_loop_bytes(theme)
        snd = pygame.mixer.Sound(buffer=data)
        # loop forever
        self.channels[0].play(snd, loops=-1)
        self.current_track = theme

    def stop_music(self):
        if not self.enabled: return
        for ch in self.channels:
            ch.stop()
        self.current_track = None

# ---------------------------------------------------------------------------
# Tile IDs and Level tilemap helpers
# ---------------------------------------------------------------------------

class T:
    EMPTY = 0
    GROUND_TOP = 1
    GROUND = 2
    BRICK = 3
    QUESTION = 4
    PIPE_TL = 5
    PIPE_TR = 6
    PIPE_BL = 7
    PIPE_BR = 8
    FLAG = 9

SOLID_TILES = {T.GROUND_TOP, T.GROUND, T.BRICK, T.QUESTION, T.PIPE_TL, T.PIPE_TR, T.PIPE_BL, T.PIPE_BR}

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------

class Camera:
    def __init__(self, w: int, h: int):
        self.rect = pygame.Rect(0, 0, w, h)
        self.level_width_px = w

    def update(self, target_rect: pygame.Rect):
        # Follow with a lead
        desired_x = target_rect.centerx - SCREEN_WIDTH // 3
        self.rect.x = max(0, min(self.level_width_px - SCREEN_WIDTH, desired_x))

class Mario:
    def __init__(self, ppu: PPU, x: int, y: int):
        self.ppu = ppu
        self.power = PowerUpState.SMALL
        self.image = self._build_image()
        self.rect = self.image.get_rect(topleft=(x, y))

        self.vel_x = 0.0
        self.vel_y = 0.0
        self.facing_right = True
        self.on_ground = False
        self.alive = True
        self.score = 0
        self.coins = 0
        self.lives = 3
        self.anim = 0

    def _build_image(self) -> pygame.Surface:
        if self.power == PowerUpState.SMALL:
            tiles = self.ppu._mario_small_tiles()
        else:
            tiles = self.ppu._mario_super_tiles()
        # palette 0 for Mario
        return self.ppu.sprite_surface(f"mario_{self.power.name}", tiles, palette_index=0)

    def set_power(self, new_state: PowerUpState):
        self.power = new_state
        x, y = self.rect.topleft
        self.image = self._build_image()
        # adjust rect (height may change)
        self.rect = self.image.get_rect(topleft=(x, y -  (self.rect.height - self.image.get_height())))

    def handle_input(self, keys):
        if not self.alive: return
        self.vel_x = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -MOVE_SPEED
            self.facing_right = False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = MOVE_SPEED
            self.facing_right = True
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.vel_y = JUMP_STRENGTH
            self.on_ground = False

    def _tiles_in_rect(self, rect: pygame.Rect, tilemap: List[List[int]]) -> List[Tuple[int,int,int]]:
        results = []
        rows = len(tilemap)
        cols = len(tilemap[0]) if rows else 0
        ts = TILE_PIX
        x0 = max(0, rect.left // ts)
        y0 = max(0, rect.top // ts)
        x1 = min(cols-1, rect.right // ts)
        y1 = min(rows-1, rect.bottom // ts)
        for ty in range(y0, y1+1):
            for tx in range(x0, x1+1):
                results.append((tx, ty, tilemap[ty][tx]))
        return results

    def _collide_solid(self, rect: pygame.Rect, tilemap: List[List[int]]) -> Optional[pygame.Rect]:
        ts = TILE_PIX
        for tx, ty, tid in self._tiles_in_rect(rect, tilemap):
            if tid in SOLID_TILES:
                return pygame.Rect(tx*ts, ty*ts, ts, ts)
        return None

    def update(self, tilemap: List[List[int]], apu: APU):
        if not self.alive: return

        # Gravity
        self.vel_y = min(self.vel_y + GRAVITY, MAX_FALL_SPEED)

        # Horizontal
        new_rect = self.rect.move(self.vel_x, 0)
        hit = self._collide_solid(new_rect, tilemap)
        if hit:
            if self.vel_x > 0:
                new_rect.right = hit.left
            elif self.vel_x < 0:
                new_rect.left = hit.right
            self.vel_x = 0
        self.rect = new_rect

        # Vertical
        new_rect = self.rect.move(0, self.vel_y)
        hit = self._collide_solid(new_rect, tilemap)
        self.on_ground = False
        if hit:
            if self.vel_y > 0:  # falling
                new_rect.bottom = hit.top
                self.on_ground = True
            elif self.vel_y < 0:  # hitting ceiling
                new_rect.top = hit.bottom
                # bump question/brick?
                # (Simple: if hitting a QUESTION, turn it into BRICK and spawn powerup/coin)
                tx = hit.left // TILE_PIX
                ty = (hit.top // TILE_PIX)
                # tile above is at ty-1 when going up — but here we collided with that tile already.
                # We can inject coin-power behavior where appropriate in Level.update if needed.
            self.vel_y = 0
        self.rect = new_rect

        # death if fallen out
        if self.rect.top > SCREEN_HEIGHT + 200:
            self.die(apu)

        # simple anim counter
        self.anim = (self.anim + 1) % 20

    def die(self, apu: APU):
        if not self.alive: return
        self.alive = False
        self.lives -= 1
        apu.play_sfx('death')

    def draw(self, target: pygame.Surface, cam: Camera):
        img = self.image
        if not self.facing_right:
            img = pygame.transform.flip(img, True, False)
        target.blit(img, (self.rect.x - cam.rect.x, self.rect.y - cam.rect.y))

class Enemy:
    def __init__(self, ppu: PPU, x: int, y: int, kind: str='goomba'):
        self.kind = kind
        self.ppu = ppu
        # Simple 2x2 tile sprite
        tile = [[ [3]*8 for _ in range(8) ]]
        body = [[ [2]*8 for _ in range(8) ]]
        # build composite 2x2
        pattern = [
            [tile[0], tile[0]],
            [body[0], body[0]],
        ]
        pal = 1 if kind == 'koopa' else 0
        self.image = ppu.sprite_surface(f"{kind}_spr", pattern, palette_index=pal)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel_x = -1.0 if kind=='goomba' else -1.2
        self.vel_y = 0.0
        self.alive = True

    def _tiles_in_rect(self, rect: pygame.Rect, tilemap: List[List[int]]) -> List[Tuple[int,int,int]]:
        rows = len(tilemap)
        cols = len(tilemap[0]) if rows else 0
        ts = TILE_PIX
        x0 = max(0, rect.left // ts)
        y0 = max(0, rect.top // ts)
        x1 = min(cols-1, rect.right // ts)
        y1 = min(rows-1, rect.bottom // ts)
        out=[]
        for ty in range(y0, y1+1):
            for tx in range(x0, x1+1):
                out.append((tx, ty, tilemap[ty][tx]))
        return out

    def _collide_solid(self, rect: pygame.Rect, tilemap: List[List[int]]) -> Optional[pygame.Rect]:
        ts = TILE_PIX
        for tx, ty, tid in self._tiles_in_rect(rect, tilemap):
            if tid in SOLID_TILES:
                return pygame.Rect(tx*ts, ty*ts, ts, ts)
        return None

    def update(self, tilemap: List[List[int]]):
        if not self.alive: return
        self.vel_y = min(self.vel_y + GRAVITY, MAX_FALL_SPEED)

        # X
        new_rect = self.rect.move(self.vel_x, 0)
        hit = self._collide_solid(new_rect, tilemap)
        if hit:
            # bounce direction
            if self.vel_x > 0:
                new_rect.right = hit.left
            else:
                new_rect.left = hit.right
            self.vel_x = -self.vel_x
        self.rect = new_rect

        # Y
        new_rect = self.rect.move(0, self.vel_y)
        hit = self._collide_solid(new_rect, tilemap)
        if hit:
            if self.vel_y > 0:
                new_rect.bottom = hit.top
            else:
                new_rect.top = hit.bottom
            self.vel_y = 0
        self.rect = new_rect

    def stomped(self):
        self.alive = False

    def draw(self, target: pygame.Surface, cam: Camera):
        if not self.alive: return
        target.blit(self.image, (self.rect.x - cam.rect.x, self.rect.y - cam.rect.y))

class PowerUp:
    def __init__(self, ppu: PPU, x: int, y: int, kind: str='mushroom'):
        self.kind = kind
        # simple 1x1 tile sprite (bright palette)
        tile = [[ [2]*8 for _ in range(8) ]]
        self.image = ppu.sprite_surface(f"power_{kind}", [tile], palette_index=2)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel_y = 0.0
        self.collected = False

    def update(self, tilemap: List[List[int]]):
        if self.collected: return
        self.vel_y = min(self.vel_y + GRAVITY, MAX_FALL_SPEED)
        new_rect = self.rect.move(0, self.vel_y)
        # collide floor
        ts = TILE_PIX
        y1 = new_rect.bottom // ts
        x0 = new_rect.left // ts
        x1 = new_rect.right // ts
        collided = False
        rows = len(tilemap)
        cols = len(tilemap[0]) if rows else 0
        for tx in range(max(0, x0), min(cols-1, x1)+1):
            if 0 <= y1 < rows and tilemap[y1][tx] in SOLID_TILES:
                collided = True
                break
        if collided:
            new_rect.bottom = y1 * ts
            self.vel_y = 0
        self.rect = new_rect

    def draw(self, target: pygame.Surface, cam: Camera):
        if self.collected: return
        target.blit(self.image, (self.rect.x - cam.rect.x, self.rect.y - cam.rect.y))

# ---------------------------------------------------------------------------
# Level: builds tilemap, manages entities, draws with PPU
# ---------------------------------------------------------------------------

class Level:
    def __init__(self, ppu: PPU, data: LevelData):
        self.ppu = ppu
        self.data = data
        self.tilemap: List[List[int]] = []
        self.bg_palette_index = self._theme_to_palette()
        self.enemies: List[Enemy] = []
        self.powerups: List[PowerUp] = []
        self.flag_x_px = 0
        self._build_level()

    def _theme_to_palette(self) -> int:
        return {
            'overworld': 0,
            'underground': 1,
            'castle': 2,
            'underwater': 3
        }.get(self.data.theme, 0)

    @property
    def width_px(self) -> int:
        cols = len(self.tilemap[0]) if self.tilemap else 0
        return cols * TILE_PIX

    def _build_ground_strip(self, cols: int, rows: int, ground_line: int):
        # Empty sky
        self.tilemap = [[T.EMPTY for _ in range(cols)] for _ in range(rows)]
        # ground
        for x in range(cols):
            if 0 <= ground_line < rows:
                self.tilemap[ground_line][x] = T.GROUND_TOP
            for y in range(ground_line+1, rows):
                self.tilemap[y][x] = T.GROUND

    def _place_pipe(self, x_tile: int, top_tile: int, height: int):
        # left/right columns at x_tile and x_tile+1
        if height < 2: height = 2
        self.tilemap[top_tile][x_tile] = T.PIPE_TL
        self.tilemap[top_tile][x_tile+1] = T.PIPE_TR
        for j in range(1, height):
            self.tilemap[top_tile+j][x_tile] = T.PIPE_BL
            self.tilemap[top_tile+j][x_tile+1] = T.PIPE_BR

    def _place_flag(self, x_tile: int, ground_line: int, h: int = 7):
        for j in range(h):
            if 0 <= ground_line - j < len(self.tilemap):
                self.tilemap[ground_line - j][x_tile] = T.FLAG
        self.flag_x_px = x_tile*TILE_PIX

    def _place_platform(self, x0: int, width: int, y: int, tile: int):
        for x in range(x0, x0+width):
            if 0 <= y < len(self.tilemap[0]):
                self.tilemap[y][x] = tile

    def _build_level(self):
        # Simple template per theme, with variation by world/level
        cols = 500  # long level
        rows = SCREEN_HEIGHT // TILE_PIX
        ground_line = rows - 4  # leave some air
        self._build_ground_strip(cols, rows, ground_line)

        rng = random.Random(self.data.world*10 + self.data.level)
        # scatter bricks and question blocks
        for i in range(80):
            x = rng.randint(10, cols-20)
            y = rng.randint(ground_line-6, ground_line-2)
            self.tilemap[y][x] = T.BRICK if rng.random() < 0.65 else T.QUESTION

        # a few pipes
        for i in range(6):
            x = rng.randint(20, cols-20)
            h = rng.randint(3, 6)
            self._place_pipe(x, ground_line - (h-1), h)

        # flag / end
        self._place_flag(cols-6, ground_line, h=8)

        # enemies
        for i in range(10 + self.data.world):
            ex = rng.randint(15, cols-10) * TILE_PIX
            ey = (ground_line-1) * TILE_PIX
            kind = 'koopa' if rng.random() < 0.35 else 'goomba'
            self.enemies.append(Enemy(self.ppu, ex, ey, kind))

        # powerups
        for i in range(6):
            px = rng.randint(12, cols-8) * TILE_PIX
            py = (ground_line-3) * TILE_PIX
            self.powerups.append(PowerUp(self.ppu, px, py, 'mushroom'))

    def update(self, mario: Mario, apu: APU):
        # Enemies
        for e in self.enemies:
            e.update(self.tilemap)

        # Powerups
        for p in self.powerups:
            p.update(self.tilemap)

        # Interactions
        # Mario vs Enemies
        for e in self.enemies:
            if not e.alive: continue
            if mario.rect.colliderect(e.rect):
                # stomp
                if mario.vel_y > 0 and mario.rect.bottom - e.rect.top < TILE_PIX//2:
                    e.stomped()
                    mario.vel_y = -8
                    mario.score += 100
                    apu.play_sfx('stomp')
                else:
                    # damage
                    if mario.power == PowerUpState.SMALL:
                        mario.die(apu)
                    else:
                        mario.set_power(PowerUpState.SMALL)

        # Mario vs Powerups
        for p in self.powerups:
            if p.collected: continue
            if mario.rect.colliderect(p.rect):
                p.collected = True
                mario.set_power(PowerUpState.SUPER if mario.power == PowerUpState.SMALL else PowerUpState.FIRE)
                mario.score += 1000
                apu.play_sfx('powerup')

    def draw(self, target: pygame.Surface, cam: Camera):
        # Sky based on theme
        bg = {
            0: SKY_BLUE,
            1: (10,10,10),
            2: (30,20,20),
            3: (20,40,80),
        }.get(self.bg_palette_index, SKY_BLUE)
        target.fill(bg)

        # Draw visible tile window
        ts = TILE_PIX
        cols = len(self.tilemap[0])
        rows = len(self.tilemap)
        x0 = cam.rect.left // ts
        x1 = min(cols-1, (cam.rect.right // ts) + 1)
        for ty in range(rows):
            for tx in range(x0, x1+1):
                tid = self.tilemap[ty][tx]
                if tid == T.EMPTY:
                    continue
                # choose palette by theme
                surf = self.ppu.tile_surface(tid, self.bg_palette_index)
                target.blit(surf, (tx*ts - cam.rect.x, ty*ts - cam.rect.y))

        # Enemies & Powerups
        for e in self.enemies: e.draw(target, cam)
        for p in self.powerups: p.draw(target, cam)

# ---------------------------------------------------------------------------
# Music / SFX manager wrapper
# ---------------------------------------------------------------------------

class MusicManager:
    def __init__(self, apu: APU):
        self.apu = apu
        self.current_theme = None

    def play_theme(self, theme: str):
        if theme == self.current_theme:
            return
        self.stop()
        self.apu.play_music(theme)
        self.current_theme = theme

    def stop(self):
        self.apu.stop_music()
        self.current_theme = None

    def sfx(self, name: str):
        self.apu.play_sfx(name)

# ---------------------------------------------------------------------------
# Game
# ---------------------------------------------------------------------------

class Game:
    def __init__(self):
        self.ppu = PPU()
        self.apu = APU()
        self.music = MusicManager(self.apu)

        self.state = GameState.MENU
        self.levels = self._make_levels()
        self.level_index = 0
        self.level = None  # type: Optional[Level]

        self.mario = None  # type: Optional[Mario]
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

        self.menu_selection = 0
        self.menu_options = ["Start Game", "Level Select", "Quit"]
        # Basic runtime text positions
        self.font_palette = 0

    def _make_levels(self) -> List[LevelData]:
        levels: List[LevelData] = []
        themes = ['overworld','underground','overworld','castle']
        # 8 worlds x 4 levels
        for w in range(1,9):
            for i in range(4):
                levels.append(LevelData(w, i+1, themes[i], 400 if i<2 else 300))
        return levels

    def start_level(self, idx: int):
        self.level_index = max(0, min(len(self.levels)-1, idx))
        data = self.levels[self.level_index]
        self.level = Level(self.ppu, data)
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.camera.level_width_px = self.level.width_px
        # Spawn Mario near start
        start_y = (SCREEN_HEIGHT//TILE_PIX - 6) * TILE_PIX
        self.mario = Mario(self.ppu, 4*TILE_PIX, start_y)
        # music per theme
        self.music.play_theme(data.theme)
        self.state = GameState.PLAYING

    def next_level(self):
        self.level_index += 1
        if self.level_index >= len(self.levels):
            self.state = GameState.MENU
            self.music.stop()
        else:
            self.start_level(self.level_index)

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            if e.type == pygame.KEYDOWN:
                if self.state == GameState.MENU:
                    if e.key in (pygame.K_DOWN, pygame.K_s): self.menu_selection = (self.menu_selection + 1) % len(self.menu_options)
                    if e.key in (pygame.K_UP, pygame.K_w): self.menu_selection = (self.menu_selection - 1) % len(self.menu_options)
                    if e.key == pygame.K_RETURN:
                        self._handle_menu_select()
                elif self.state == GameState.PLAYING:
                    if e.key == pygame.K_ESCAPE:
                        self.state = GameState.PAUSED
                    if e.key == pygame.K_r:
                        self.start_level(self.level_index)
                    if e.key == pygame.K_n:
                        self.next_level()
                elif self.state == GameState.PAUSED:
                    if e.key == pygame.K_ESCAPE:
                        self.state = GameState.PLAYING
                elif self.state == GameState.GAME_OVER:
                    if e.key == pygame.K_RETURN:
                        self.state = GameState.MENU
                        self.music.stop()

    def _handle_menu_select(self):
        if self.menu_selection == 0:
            self.start_level(0)
        elif self.menu_selection == 1:
            self._show_level_select()
        else:
            pygame.quit(); sys.exit(0)

    def _show_level_select(self):
        selecting = True
        sel_world = 0
        sel_level = 0
        while selecting:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit(); sys.exit(0)
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        selecting = False
                    elif e.key == pygame.K_LEFT:
                        sel_level = (sel_level - 1) % 4
                    elif e.key == pygame.K_RIGHT:
                        sel_level = (sel_level + 1) % 4
                    elif e.key == pygame.K_UP:
                        sel_world = (sel_world - 1) % 8
                    elif e.key == pygame.K_DOWN:
                        sel_world = (sel_world + 1) % 8
                    elif e.key == pygame.K_RETURN:
                        idx = sel_world*4 + sel_level
                        self.start_level(idx)
                        selecting = False

            # Draw Level Select
            screen.fill(BLACK)
            self.ppu.draw_text(screen, "LEVEL SELECT", 5*TILE_PIX, 2*TILE_PIX, self.font_palette)
            # Grid
            for w in range(8):
                for l in range(4):
                    x = 6*TILE_PIX + l*5*TILE_PIX
                    y = 5*TILE_PIX + w*2*TILE_PIX
                    label = f"W{w+1}-{l+1}"
                    highlight = (w==sel_world and l==sel_level)
                    # draw box
                    pygame.draw.rect(screen, LIGHT if highlight else DARKGRAY, (x-8, y-8, 4*TILE_PIX+16, TILE_PIX+16), 2)
                    self.ppu.draw_text(screen, label, x, y, self.font_palette)

            self.ppu.draw_text(screen, "ENTER=PLAY  ESC=BACK", 5*TILE_PIX, (SCREEN_HEIGHT//TILE_PIX-2)*TILE_PIX, self.font_palette)
            pygame.display.flip()
            clock.tick(FPS)

    def update(self):
        if self.state == GameState.PLAYING and self.level and self.mario:
            keys = pygame.key.get_pressed()
            self.mario.handle_input(keys)
            self.mario.update(self.level.tilemap, self.apu)
            self.level.update(self.mario, self.apu)
            self.camera.update(self.mario.rect)

            # Level end: reach flag
            if self.mario.rect.centerx >= self.level.flag_x_px:
                self.next_level()

            # Game over
            if not self.mario.alive and self.mario.lives <= 0:
                self.state = GameState.GAME_OVER
                self.music.stop()
            elif not self.mario.alive:
                # auto-restart current level with remaining lives
                self.start_level(self.level_index)

    def draw(self):
        if self.state == GameState.MENU:
            self._draw_menu()
        elif self.state in (GameState.PLAYING, GameState.PAUSED):
            self._draw_game()
            if self.state == GameState.PAUSED:
                self._draw_pause()
        elif self.state == GameState.GAME_OVER:
            self._draw_game_over()
        pygame.display.flip()

    # ---- Drawing helpers ----

    def _draw_menu(self):
        screen.fill(BLACK)
        self.ppu.draw_text(screen, "ULTRA", 7*TILE_PIX, 4*TILE_PIX, self.font_palette)
        self.ppu.draw_text(screen, "MARIO 2D BROS", 4*TILE_PIX, 6*TILE_PIX, self.font_palette)
        self.ppu.draw_text(screen, "FILES=OFF  PPU+APU SYNTH", 3*TILE_PIX, 8*TILE_PIX, self.font_palette)
        for i, opt in enumerate(self.menu_options):
            y = 12*TILE_PIX + i*2*TILE_PIX
            if i == self.menu_selection:
                pygame.draw.rect(screen, LIGHT, (7*TILE_PIX-10, y-10, 12*TILE_PIX+20, TILE_PIX+20), 2)
            self.ppu.draw_text(screen, opt.upper(), 7*TILE_PIX, y, self.font_palette)
        self.ppu.draw_text(screen, "ENTER=SELECT", 8*TILE_PIX, 20*TILE_PIX, self.font_palette)

    def _draw_game(self):
        if self.level:
            self.level.draw(screen, self.camera)
        if self.mario:
            self.mario.draw(screen, self.camera)
        self._draw_hud()

    def _draw_hud(self):
        if not self.mario or not self.level: return
        y = 1*TILE_PIX
        self.ppu.draw_text(screen, f"SCORE {self.mario.score:06d}", 1*TILE_PIX, y, self.font_palette)
        self.ppu.draw_text(screen, f"LIVES {self.mario.lives}", 1*TILE_PIX, y + TILE_PIX, self.font_palette)
        name = self.level.data.display_name()
        self.ppu.draw_text(screen, name.upper(), SCREEN_WIDTH - (len(name)+6)*self.ppu.tile_pix, y, self.font_palette)

    def _draw_pause(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        screen.blit(overlay, (0,0))
        self.ppu.draw_text(screen, "PAUSED", 10*TILE_PIX, 10*TILE_PIX, self.font_palette)
        self.ppu.draw_text(screen, "ESC=RESUME", 9*TILE_PIX, 12*TILE_PIX, self.font_palette)

    def _draw_game_over(self):
        screen.fill(BLACK)
        self.ppu.draw_text(screen, "GAME OVER", 9*TILE_PIX, 10*TILE_PIX, self.font_palette)
        if self.mario:
            self.ppu.draw_text(screen, f"FINAL SCORE {self.mario.score}", 6*TILE_PIX, 12*TILE_PIX, self.font_palette)
        self.ppu.draw_text(screen, "ENTER=MENU", 10*TILE_PIX, 14*TILE_PIX, self.font_palette)

    def run(self):
        # Title loop music (overworld vibe)
        self.music.play_theme('overworld')
        while True:
            self.handle_events()
            self.update()
            self.draw()
            clock.tick(FPS)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("="*64)
    print("Ultra Mario 2D Bros — Synth/PPU build (single-file, no assets)")
    print("All art/audio generated on the fly. No external files are loaded.")
    print("Controls: Arrows/WASD move, Space/Up jump, ESC pause/back, R restart, N next level.")
    print("="*64)
    game = Game()
    game.run()

if __name__ == "__main__":
    main()
