#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ultra Mario 2D Bros v2.0.0 (SMB1-STYLE, 32 COURSES, SINGLE-FILE)
-----------------------------------------------------------------
© Samsoft 2025 • Authentic-feel SMB1 physics and palette
NES-style dithering, CRT scanlines, no external assets.
Now with: 8 worlds × 4 stages (procedural set-pieces), flagpole/goal,
block bumps -> coins, pits & lava, lives/respawn, level progression.
"""

import sys, os, math, time, random
try:
    import pygame
    import pygame.font
except ImportError:
    sys.exit("❌ Install Pygame first:  pip install pygame")

os.environ.setdefault("SDL_RENDER_VSYNC", "1")

# ───────────── Config ─────────────
GAME_TITLE = "ULTRA MARIO 2D BROS"
BASE_W, BASE_H, SCALE = 256, 240, 2
SCREEN_W, SCREEN_H = BASE_W * SCALE, BASE_H * SCALE
TILE, FPS, DT = 16, 60, 1 / 60

# ─── SMB1‑Style Physics ───
GRAVITY = 1800.0
MAX_WALK, MAX_RUN = 88.0, 142.0
ACCEL, FRICTION = 1200.0, 900.0
JUMP_VEL, JUMP_CUT = -380.0, -200.0
COYOTE, JUMP_BUF = 0.08, 0.12
GROUND_Y = BASE_H // TILE - 2

# Solid & hazard tiles
SOLID_TILES = set("X?BP#C")  # ground, qblock, pipe, brick, castle
HAZARD_TILES = set("L")      # lava

# ─── NES‑ish Palette ───
PAL = {
    'sky_day':      (107, 140, 255),
    'sky_underground': (24, 24, 56),
    'sky_castle':   (18, 18, 18),

    'ground':   (165, 82, 0),
    'brick':    (181, 49, 33),
    'pipe':     (0, 156, 0),
    'qblock':   (255, 173, 0),

    'mario':    (222, 90, 49),
    'mario_pants': (24, 58, 165),

    'goomba':   (165, 82, 0),
    'goomba_dark': (115, 41, 0),

    'coin':     (255, 205, 0),
    'lava_a':   (255, 77, 0),
    'lava_b':   (200, 24, 0),

    'hud_bg':   (0, 0, 0),
    'hud_txt':  (255, 255, 255),
    'hud_gold': (255, 205, 0),
}

def clamp(v, a, b): return max(a, min(b, v))
def sign(v): return (v > 0) - (v < 0)
def rect_grid(x, y): return pygame.Rect(x * TILE, y * TILE, TILE, TILE)

# ───────────── Level + Builder ─────────────
class Level:
    def __init__(self, world, stage, seed=None):
        self.world, self.stage = world, stage
        self.theme = self._theme_for(stage)
        self.sky = self._sky_for(self.theme)
        self.h = BASE_H // TILE
        # length grows with world; overworld a bit longer, castle tighter
        base = 180 if self.theme == 'castle' else 200
        self.w = base + (world - 1) * 12 + (stage - 1) * 4
        self.goal_x = self.w - 8  # in tiles
        self.spawn = (2 * TILE, (GROUND_Y - 2) * TILE)
        self.grid = [[' '] * self.w for _ in range(self.h)]
        self._rng = random.Random(seed if seed is not None else (world * 100 + stage))
        self._build_basic()
        self._build_course()
        self._place_goal_structures()
        self._cleanup()

    def _theme_for(self, stage):
        # s=2 -> underground; s=4 -> castle; others overworld
        return 'underground' if stage == 2 else ('castle' if stage == 4 else 'overworld')

    def _sky_for(self, theme):
        return PAL['sky_day'] if theme == 'overworld' else (PAL['sky_underground'] if theme == 'underground' else PAL['sky_castle'])

    def tile(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.grid[y][x]
        return ' '

    def set_tile(self, x, y, ch):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.grid[y][x] = ch

    def fill_ground(self, x0, x1):
        for x in range(max(0, x0), min(self.w, x1)):
            for y in range(GROUND_Y, self.h):
                self.grid[y][x] = 'X'

    def carve_gap(self, x0, width):
        for x in range(x0, min(self.w, x0 + width)):
            for y in range(GROUND_Y, self.h):
                self.grid[y][x] = ' '

    def place_pipe(self, x, h):
        # top at GROUND_Y - h + 1
        for dy in range(h):
            self.set_tile(x, GROUND_Y - dy, 'P')

    def place_stairs(self, x, height, width):
        for step in range(width):
            for dy in range(step + 1):
                self.set_tile(x + step, GROUND_Y - dy, '#')

    def place_q_line(self, x, y, count, spacing=2):
        for i in range(count):
            self.set_tile(x + i * spacing, y, '?')

    def place_brick_line(self, x, y, length):
        for i in range(length):
            self.set_tile(x + i, y, 'B')

    def place_goomba(self, x):
        # mark with 'G' (becomes enemy at spawn time)
        self.set_tile(x, GROUND_Y - 1, 'G')

    def place_lava(self, x0, width):
        # castle pits with lava surface
        self.carve_gap(x0, width)
        for x in range(x0, min(self.w, x0 + width)):
            self.set_tile(x, self.h - 1, 'L')

    def _build_basic(self):
        # Base ground across the whole level; underground: lower ceiling feel
        self.fill_ground(0, self.w)
        if self.theme == 'underground':
            # thicken ceiling with bricks
            for x in range(self.w):
                self.set_tile(x, 4, 'B')
                if self._rng.random() < 0.10:
                    self.set_tile(x, 5, 'B')

    def _rng_choice(self, weights):
        # weights: list of (name, probability)
        r = self._rng.random()
        acc = 0.0
        for k, p in weights:
            acc += p
            if r <= acc:
                return k
        return weights[-1][0]

    def _build_course(self):
        x = 12
        difficulty = (self.world - 1) * 0.20 + (self.stage - 1) * 0.10
        pipe_hmin, pipe_hmax = (2, 4) if self.theme != 'underground' else (2, 3)

        while x < self.goal_x - 16:
            choice = self._rng_choice([
                ('qrun', 0.24),
                ('pipes', 0.22),
                ('stairs', 0.20 + difficulty * 0.1),
                ('gap',   0.18 + difficulty * 0.15),
                ('bricks',0.10),
                ('flat',  0.06)
            ])

            if choice == 'qrun':
                y = GROUND_Y - (3 if self.theme == 'overworld' else 4)
                cnt = self._rng.randint(3, 6)
                self.place_q_line(x, y, cnt, spacing=2)
                if self._rng.random() < 0.60:
                    self.place_brick_line(x - 1, y, cnt + 2)
                # goombas under
                for i in range(cnt):
                    if self._rng.random() < 0.6:
                        self.place_goomba(x + i * 2)
                x += cnt * 2 + self._rng.randint(2, 5)

            elif choice == 'pipes':
                n = self._rng.randint(1, 3)
                for i in range(n):
                    h = self._rng.randint(pipe_hmin, pipe_hmax)
                    self.place_pipe(x, h)
                    if self._rng.random() < 0.5:
                        self.place_goomba(x + 2)
                    x += self._rng.randint(5, 8)
                x += self._rng.randint(2, 4)

            elif choice == 'stairs':
                height = self._rng.randint(2, 5 + (1 if difficulty > 0.6 else 0))
                width = self._rng.randint(3, 6)
                self.place_stairs(x, height, width)
                x += width + self._rng.randint(2, 4)

            elif choice == 'gap':
                if self.theme == 'castle' and self._rng.random() < 0.75:
                    width = self._rng.randint(3, 6 + int(difficulty * 4))
                    self.place_lava(x, width)
                else:
                    width = self._rng.randint(2, 5 + int(difficulty * 3))
                    self.carve_gap(x, width)
                x += width + self._rng.randint(3, 6)

            elif choice == 'bricks':
                y = GROUND_Y - self._rng.randint(3, 5)
                length = self._rng.randint(4, 8)
                self.place_brick_line(x, y, length)
                if self._rng.random() < 0.4:
                    self.place_q_line(x + 1, y - 1, self._rng.randint(2, 4), spacing=2)
                x += length + self._rng.randint(3, 6)

            else:  # flat
                x += self._rng.randint(6, 12)

        # Sprinkle some extra goombas on flats
        for k in range(12 + self.world * 2):
            gx = self._rng.randint(6, self.goal_x - 8)
            if self.tile(gx, GROUND_Y - 1) == ' ' and self.tile(gx, GROUND_Y) == 'X':
                if self._rng.random() < 0.40:
                    self.place_goomba(gx)

        # Underground tweak: lower headroom with occasional bricks
        if self.theme == 'underground':
            for k in range(self._rng.randint(8, 14)):
                y = self._rng.randint(6, 8)
                x0 = self._rng.randint(8, self.goal_x - 16)
                ln = self._rng.randint(4, 8)
                for i in range(ln):
                    self.set_tile(x0 + i, y, 'B')

    def _place_goal_structures(self):
        gx = self.goal_x
        # Flagpole (F vertical), simple castle (C) block
        for y in range(5, GROUND_Y + 1):
            self.set_tile(gx, y, 'F')
        # tiny castle block
        for y in range(GROUND_Y - 3, GROUND_Y + 1):
            for x in range(gx + 4, min(self.w, gx + 10)):
                self.set_tile(x, y, 'C')

    def _cleanup(self):
        # Replace transient markers, spawn points etc.
        self.enemy_positions = []
        for y in range(self.h):
            for x in range(self.w):
                if self.grid[y][x] == 'G':
                    self.enemy_positions.append((x * TILE, y * TILE))

# ───────────── Entities ─────────────
class Player:
    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.vx = self.vy = 0.0
        self.on_ground = False
        self.coyote = self.buf = 0.0
        self.facing = 1
        self.lives, self.coins, self.score = 3, 0, 0
        self.anim = 0.0
        self.jump_held = False

    def update(self, game, dt):
        lvl = game.level
        k = pygame.key.get_pressed()
        left, right = k[pygame.K_LEFT], k[pygame.K_RIGHT]
        run = k[pygame.K_LSHIFT] or k[pygame.K_RSHIFT]
        dir = 1 if right and not left else -1 if left and not right else 0
        if dir != 0:
            self.facing = dir

        maxspd = MAX_RUN if run else MAX_WALK
        acc = ACCEL if self.on_ground else ACCEL / 4
        fric = FRICTION if self.on_ground else FRICTION / 8

        if dir == 0:
            if abs(self.vx) < 5: self.vx = 0
            else: self.vx -= sign(self.vx) * fric * dt
        else:
            if sign(self.vx) != dir and self.vx != 0:
                self.vx -= sign(self.vx) * fric * 2.5 * dt
            else:
                self.vx += dir * acc * dt

        self.vx = clamp(self.vx, -maxspd, maxspd)
        self.vy += GRAVITY * dt

        # Jump buffer & coyote
        jp = k[pygame.K_SPACE] or k[pygame.K_z]
        if jp and not self.jump_held: self.buf = JUMP_BUF
        self.jump_held = jp
        self.buf = max(0, self.buf - dt)
        if self.on_ground: self.coyote = COYOTE
        else: self.coyote = max(0, self.coyote - dt)

        if self.coyote > 0 and self.buf > 0:
            self.vy = JUMP_VEL
            self.buf = 0
            self.coyote = 0
            self.on_ground = False

        if not jp and self.vy < 0:
            self.vy = max(self.vy, JUMP_CUT)

        # Integrate & collide
        self.x += self.vx * dt
        self._cx(lvl)
        self.y += self.vy * dt
        self._cy(game)

        # Animate
        if self.on_ground and abs(self.vx) > 10:
            self.anim += abs(self.vx) * 0.05 * dt

    def _cx(self, lvl):
        r = pygame.Rect(int(self.x), int(self.y), TILE, TILE)
        for gy in range(r.top // TILE, r.bottom // TILE + 1):
            for gx in range(r.left // TILE, r.right // TILE + 1):
                if lvl.tile(gx, gy) in SOLID_TILES:
                    t = rect_grid(gx, gy)
                    if r.colliderect(t):
                        if self.vx > 0:
                            self.x -= (r.right - t.left)
                        elif self.vx < 0:
                            self.x += (t.right - r.left)
                        self.vx = 0
                        return

    def _cy(self, game):
        lvl = game.level
        r = pygame.Rect(int(self.x), int(self.y), TILE, TILE)
        self.on_ground = False
        for gy in range(r.top // TILE, r.bottom // TILE + 1):
            for gx in range(r.left // TILE, r.right // TILE + 1):
                tile_ch = lvl.tile(gx, gy)
                if tile_ch in SOLID_TILES or tile_ch in HAZARD_TILES or tile_ch == 'F':
                    t = rect_grid(gx, gy)
                    if r.colliderect(t):
                        if tile_ch in HAZARD_TILES:
                            game.player_die()
                            return
                        if tile_ch == 'F':
                            game.reach_flag()
                            return
                        if self.vy > 0:
                            self.y -= (r.bottom - t.top)
                            self.vy = 0
                            self.on_ground = True
                        elif self.vy < 0:
                            # Bump blocks / q-blocks from below
                            game.bump_block(gx, gy)
                            self.y += (t.bottom - r.top)
                            self.vy = 0
                        return

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), TILE, TILE)

class Goomba:
    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = -40.0, 0.0
        self.alive, self.on_ground = True, False
        self.anim = 0.0

    def update(self, lvl, dt):
        if not self.alive: return
        self.anim += dt * 4
        self.vy += GRAVITY * dt
        self.x += self.vx * dt
        self._cx(lvl)
        self.y += self.vy * dt
        self._cy(lvl)

    def _cx(self, lvl):
        r = pygame.Rect(int(self.x), int(self.y), TILE, TILE)
        for gy in range(r.top // TILE, r.bottom // TILE + 1):
            for gx in range(r.left // TILE, r.right // TILE + 1):
                if lvl.tile(gx, gy) in SOLID_TILES:
                    t = rect_grid(gx, gy)
                    if r.colliderect(t):
                        self.vx *= -1
                        return

    def _cy(self, lvl):
        r = pygame.Rect(int(self.x), int(self.y), TILE, TILE)
        self.on_ground = False
        for gy in range(r.top // TILE, r.bottom // TILE + 1):
            for gx in range(r.left // TILE, r.right // TILE + 1):
                if lvl.tile(gx, gy) in SOLID_TILES:
                    t = rect_grid(gx, gy)
                    if r.colliderect(t):
                        if self.vy > 0:
                            self.y -= (r.bottom - t.top)
                            self.vy = 0
                            self.on_ground = True
                        elif self.vy < 0:
                            self.y += (t.bottom - r.top)
                            self.vy = 0
                        return

    def get_rect(self):
        return pygame.Rect(int(self.x), int(self.y), TILE, TILE)

# ───────────── Little FX ─────────────
class CoinPop:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.vy = -140.0
        self.t = 0.6
    def update(self, dt):
        self.t -= dt
        self.y += self.vy * dt
        self.vy += 500 * dt
        return self.t <= 0

# ───────────── Game ─────────────
class MarioGame:
    def __init__(self, world=1, stage=1):
        self.world, self.stage = world, stage
        self.level = Level(world, stage)
        self.player = Player(*self.level.spawn)
        self.enemies = []
        self.effects = []
        self.spawn_enemies()
        self.cam_x = 0
        self.font = pygame.font.SysFont("Arial", 14, bold=True)
        self.bigfont = pygame.font.SysFont("Arial", 28, bold=True)
        self.time, self.timer = 400, 0
        self.sky = self.level.sky
        self._build_tiles()
        self.dead_freeze = 0.0
        self.finished = False

    # ── Tiles / Surfaces ──
    def _s_ground(self):
        s = pygame.Surface((TILE, TILE)); s.fill(PAL['ground'])
        for y in range(TILE):
            for x in range(TILE):
                if (x + y) % 4 == 0:
                    s.set_at((x, y), (140, 70, 0))
        return s

    def _s_brick(self):
        s = pygame.Surface((TILE, TILE)); s.fill(PAL['brick'])
        for y in range(TILE):
            for x in range(TILE):
                if x % 4 == 0 or y % 4 == 0:
                    s.set_at((x, y), (150, 40, 25))
        return s

    def _s_pipe(self):
        s = pygame.Surface((TILE, TILE)); s.fill(PAL['pipe'])
        for y in range(TILE):
            for x in range(TILE):
                if x < 2 or y < 2: s.set_at((x, y), (0, 130, 0))
                elif x > TILE - 3 or y > TILE - 3: s.set_at((x, y), (0, 180, 0))
        return s

    def _s_qblock(self):
        s = pygame.Surface((TILE, TILE)); s.fill(PAL['qblock'])
        for y in range(TILE):
            for x in range(TILE):
                if (x + y) % 3 == 0: s.set_at((x, y), (230, 160, 0))
        for i in range(4):
            s.set_at((TILE//2, TILE//3 + i), (0, 0, 0))
        return s

    def _s_goomba(self):
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.ellipse(s, PAL['goomba'], (2, 4, TILE-4, TILE-6))
        pygame.draw.ellipse(s, PAL['goomba_dark'], (4, 6, TILE-8, TILE-10))
        pygame.draw.rect(s, PAL['goomba_dark'], (4, TILE-4, 3, 3))
        pygame.draw.rect(s, PAL['goomba_dark'], (TILE-7, TILE-4, 3, 3))
        return s

    def _s_coin(self):
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.circle(s, PAL['coin'], (TILE//2, TILE//2), TILE//3)
        pygame.draw.circle(s, (200, 150, 0), (TILE//2, TILE//2), TILE//3 - 2)
        return s

    def _s_mario(self):
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.rect(s, PAL['mario'], (4, 4, TILE-8, TILE-4))
        pygame.draw.rect(s, PAL['mario_pants'], (4, TILE-6, TILE-8, 4))
        pygame.draw.rect(s, PAL['mario'], (2, 2, TILE-4, 4))
        return s

    def _s_flagpole(self):
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.rect(s, (240, 240, 240), (7, 0, 2, TILE))
        pygame.draw.circle(s, (240, 240, 240), (8, 2), 2)
        return s

    def _s_lava(self):
        s = pygame.Surface((TILE, TILE))
        for y in range(TILE):
            c = PAL['lava_a'] if y % 4 < 2 else PAL['lava_b']
            pygame.draw.line(s, c, (0, y), (TILE, y))
        return s

    def _build_tiles(self):
        self.ground_tile = self._s_ground()
        self.brick_tile  = self._s_brick()
        self.pipe_tile   = self._s_pipe()
        self.q_tile      = self._s_qblock()
        self.goomba_surf = self._s_goomba()
        self.coin_surf   = self._s_coin()
        self.mario_surf  = self._s_mario()
        self.flag_tile   = self._s_flagpole()
        self.lava_tile   = self._s_lava()
        self.scanline_surf = self._scanlines()

    def _scanlines(self):
        s = pygame.Surface((BASE_W, BASE_H), pygame.SRCALPHA)
        for y in range(BASE_H):
            alpha = 40 if y % 2 == 0 else 20
            pygame.draw.line(s, (0, 0, 0, alpha), (0, y), (BASE_W, y))
        return s

    def spawn_enemies(self):
        self.enemies.clear()
        for (px, py) in self.level.enemy_positions:
            self.enemies.append(Goomba(px, py))

    # ── Game mechanics helpers ──
    def bump_block(self, gx, gy):
        ch = self.level.tile(gx, gy)
        if ch == '?':
            self.level.set_tile(gx, gy, ' ')
            self.player.coins = min(99, self.player.coins + 1)
            self.player.score += 200
            # coin pop effect
            self.effects.append(CoinPop(gx * TILE + TILE // 2, gy * TILE))
        elif ch in ('B', '#'):
            # simple bump -> 50 pts
            self.player.score += 50
            # optional: break brick (keeping simple)
            if ch == 'B':
                self.level.set_tile(gx, gy, ' ')

    def reach_flag(self):
        if not self.finished:
            self.finished = True

    def player_die(self):
        if self.dead_freeze > 0: return
        self.player.lives -= 1
        self.dead_freeze = 1.0
        if self.player.lives < 0:
            self.player.lives = 0

    def hard_respawn(self):
        # Called after freeze or time/lava fall
        if self.player.lives <= 0:
            return 'game_over'
        self.level = Level(self.world, self.stage)
        self.sky = self.level.sky
        self.player.x, self.player.y = self.level.spawn
        self.player.vx = self.player.vy = 0
        self.spawn_enemies()
        self.time, self.timer = 400, 0
        self.cam_x = 0
        self.effects.clear()
        self.finished = False
        return 'game'

    def next_stage_or_win(self):
        if self.stage < 4:
            return MarioGame(self.world, self.stage + 1)
        elif self.world < 8:
            return MarioGame(self.world + 1, 1)
        else:
            return None  # victory

    # ── HUD ──
    def draw_hud(self, surf):
        pygame.draw.rect(surf, PAL['hud_bg'], (0, 0, BASE_W, TILE * 2))
        texts = [
            f"SCORE {self.player.score:06d}",
            f"COIN x{self.player.coins:02d}",
            f"WORLD {self.world}-{self.stage}",
            f"TIME {self.time:03d}",
            f"LIVES {self.player.lives}"
        ]
        surf.blit(self.font.render(texts[0], 1, PAL['hud_txt']), (10, 5))
        surf.blit(self.font.render(texts[1], 1, PAL['hud_gold']), (100, 5))
        surf.blit(self.coin_surf, (160, 5))
        surf.blit(self.font.render(texts[2], 1, PAL['hud_txt']), (190, 5))
        surf.blit(self.font.render(texts[3], 1, PAL['hud_txt']), (100, 20))
        surf.blit(self.font.render(texts[4], 1, PAL['hud_txt']), (10, 20))

    # ── Update / Draw ──
    def update(self, dt):
        # Timer
        self.timer += dt
        if self.timer >= 1.0:
            self.time = max(0, self.time - 1)
            self.timer = 0
            if self.time == 0:
                self.player_die()

        # Freeze window on death
        if self.dead_freeze > 0:
            self.dead_freeze -= dt
            if self.dead_freeze <= 0:
                return self.hard_respawn()
            return 'game'

        # Update player
        self.player.update(self, dt)

        # Fall death
        if self.player.y > BASE_H + 32:
            self.player_die()

        # Update enemies and stomp collisions
        p_rect = self.player.rect()
        for e in self.enemies[:]:
            e.update(self.level, dt)
            if e.alive:
                r = e.get_rect()
                if p_rect.colliderect(r):
                    if self.player.vy > 0 and p_rect.bottom - r.top < TILE // 2:
                        e.alive = False
                        self.player.vy = -250
                        self.player.score += 100
                    else:
                        self.player_die()

        # Update effects
        for fx in self.effects[:]:
            if fx.update(dt):
                self.effects.remove(fx)

        # Camera follow
        target = clamp(self.player.x - BASE_W // 2, 0, self.level.w * TILE - BASE_W)
        self.cam_x += (target - self.cam_x) * 0.12

        # Reached flag?
        if self.finished:
            return 'level_clear'

        return 'game'

    def draw(self, surf):
        surf.fill(self.sky)
        self.draw_hud(surf)

        # Visible horizontal tile range
        sx = int(self.cam_x // TILE) - 1
        ex = sx + BASE_W // TILE + 3

        # Level / tiles
        for y in range(self.level.h):
            for x in range(max(0, sx), min(self.level.w, ex)):
                tx, ty = x * TILE - int(self.cam_x), y * TILE + TILE * 2
                t = self.level.tile(x, y)
                if t == 'X': surf.blit(self.ground_tile, (tx, ty))
                elif t == '#': surf.blit(self.brick_tile, (tx, ty))
                elif t == 'B': surf.blit(self.brick_tile, (tx, ty))
                elif t == 'P': surf.blit(self.pipe_tile, (tx, ty))
                elif t == '?': surf.blit(self.q_tile, (tx, ty))
                elif t == 'C': surf.blit(self.brick_tile, (tx, ty))
                elif t == 'F': surf.blit(self.flag_tile, (tx, ty))
                elif t == 'L': surf.blit(self.lava_tile, (tx, ty))

        # Player
        surf.blit(self.mario_surf, (self.player.x - int(self.cam_x), self.player.y + TILE * 2))

        # Enemies
        for e in self.enemies:
            if e.alive:
                offset = 1 if math.sin(e.anim) > 0 else 0
                surf.blit(self.goomba_surf, (e.x - int(self.cam_x), e.y + TILE * 2 + offset))

        # Effects
        for fx in self.effects:
            surf.blit(self.coin_surf, (fx.x - int(self.cam_x) - TILE // 2, fx.y + TILE * 2))

        # CRT scanlines
        surf.blit(self.scanline_surf, (0, 0))

# ───────────── States ─────────────
class Loading:
    def __init__(self):
        self.t = 0; self.f = pygame.font.SysFont("Arial", 20, bold=True); self.b = 0
    def update(self, dt):
        self.t += dt; self.b += dt
        if self.b > 0.5: self.b = 0
        return 'menu' if self.t > 1.5 else 'loading'
    def draw(self, s):
        s.fill((0, 0, 0))
        if self.b < 0.25:
            t = self.f.render("NOW LOADING...", True, (100, 255, 100))
            s.blit(t, (BASE_W//2 - t.get_width()//2, BASE_H//2 - 10))

class Menu:
    def __init__(self):
        self.f1 = pygame.font.SysFont("Arial", 28, bold=True)
        self.f2 = pygame.font.SysFont("Arial", 18, bold=True)
        self.opt, self.t = 0, 0
    def update(self, dt):
        k = pygame.key.get_pressed(); self.t += dt
        if self.t > 0.12:
            if k[pygame.K_UP]: self.opt = (self.opt - 1) % 2; self.t = 0
            elif k[pygame.K_DOWN]: self.opt = (self.opt + 1) % 2; self.t = 0
        if k[pygame.K_RETURN] or k[pygame.K_z]:
            return 'game'
        return 'menu'
    def draw(self, s):
        s.fill(PAL['sky_day'])
        title = self.f1.render("ULTRA MARIO 2D BROS", True, (255, 255, 255))
        s.blit(title, (BASE_W//2 - title.get_width()//2, 60))
        opts = ["1 PLAYER GAME", "32‑COURSE MODE"]
        for i, txt in enumerate(opts):
            color = (255, 255, 100) if i == self.opt else (255, 255, 255)
            r = self.f2.render(txt, True, color)
            s.blit(r, (BASE_W//2 - r.get_width()//2, 120 + i*30))
        arrow = self.f2.render(">", True, (255, 255, 100))
        s.blit(arrow, (BASE_W//2 - 80, 118 + self.opt*30))

class LevelClear:
    def __init__(self, world, stage):
        self.f = pygame.font.SysFont("Arial", 24, bold=True)
        self.sub = pygame.font.SysFont("Arial", 16, bold=True)
        self.t = 0.0
        self.world, self.stage = world, stage
    def update(self, dt):
        self.t += dt
        return 'advance' if self.t > 1.6 else 'level_clear'
    def draw(self, s):
        s.fill((0, 0, 0))
        t = self.f.render("COURSE CLEAR!", True, (255, 255, 255))
        s.blit(t, (BASE_W//2 - t.get_width()//2, BASE_H//2 - 18))
        sub = self.sub.render(f"NEXT: WORLD {self.world}-{self.stage}", True, (200, 200, 200))
        s.blit(sub, (BASE_W//2 - sub.get_width()//2, BASE_H//2 + 10))

class GameOver:
    def __init__(self):
        self.t = 0; self.f = pygame.font.SysFont("Arial", 32, bold=True)
    def update(self, dt):
        self.t += dt
        return 'menu' if self.t > 2.5 else 'game_over'
    def draw(self, s):
        s.fill((0, 0, 0))
        t = self.f.render("GAME OVER", True, (255, 50, 50))
        s.blit(t, (BASE_W//2 - t.get_width()//2, BASE_H//2 - 16))

class Victory:
    def __init__(self):
        self.f = pygame.font.SysFont("Arial", 26, bold=True)
        self.t = 0.0
    def update(self, dt):
        self.t += dt
        return 'menu' if self.t > 3.0 else 'victory'
    def draw(self, s):
        s.fill((0, 0, 0))
        t = self.f.render("YOU SAVED THE KINGDOM!", True, (255, 255, 255))
        s.blit(t, (BASE_W//2 - t.get_width()//2, BASE_H//2 - 16))

# ───────────── Main ─────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption(GAME_TITLE)
    surf = pygame.Surface((BASE_W, BASE_H))
    clock = pygame.time.Clock()

    state = 'loading'
    loading, menu, over, win = Loading(), Menu(), GameOver(), Victory()
    clear = None
    game = None
    acc = 0.0

    # campaign tracking
    cur_world, cur_stage = 1, 1

    running = True
    while running:
        dt_real = clock.tick(FPS) / 1000.0

        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                running = False

        acc += dt_real
        while acc >= DT:
            if state == 'loading':
                ns = loading.update(DT)
                state = ns

            elif state == 'menu':
                ns = menu.update(DT)
                if ns != state:
                    state = ns
                    if state == 'game':
                        cur_world, cur_stage = 1, 1
                        game = MarioGame(cur_world, cur_stage)

            elif state == 'game':
                if game:
                    ns = game.update(DT)
                    if ns == 'level_clear':
                        # prepare clear screen (compute next)
                        if cur_stage < 4:
                            nx_world, nx_stage = cur_world, cur_stage + 1
                        elif cur_world < 8:
                            nx_world, nx_stage = cur_world + 1, 1
                        else:
                            nx_world, nx_stage = None, None
                        clear = LevelClear(nx_world if nx_world else 8, nx_stage if nx_stage else 4)
                        state = 'level_clear'
                    elif ns == 'game_over':
                        state = 'game_over'

            elif state == 'level_clear':
                if clear:
                    ns = clear.update(DT)
                else:
                    ns = 'menu'
                if ns == 'advance':
                    # advance to next course or victory
                    if cur_stage < 4:
                        cur_stage += 1
                        game = MarioGame(cur_world, cur_stage)
                        state = 'game'
                    elif cur_world < 8:
                        cur_world += 1
                        cur_stage = 1
                        game = MarioGame(cur_world, cur_stage)
                        state = 'game'
                    else:
                        state = 'victory'

            elif state == 'game_over':
                ns = over.update(DT)
                if ns != state: state = ns

            elif state == 'victory':
                ns = win.update(DT)
                if ns != state: state = ns

            acc -= DT

        # Render
        if state == 'loading':
            loading.draw(surf)
        elif state == 'menu':
            menu.draw(surf)
        elif state == 'game' and game:
            game.draw(surf)
        elif state == 'level_clear':
            if clear:
                clear.draw(surf)
        elif state == 'game_over':
            over.draw(surf)
        elif state == 'victory':
            win.draw(surf)

        # Scale to screen
        final = pygame.transform.scale(surf, (SCREEN_W, SCREEN_H))
        screen.blit(final, (0, 0))
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
