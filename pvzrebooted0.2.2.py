#!/usr/bin/env python3
"""
PVZ Rebooted v0.1.1 — Single-file lane defense (no assets)
----------------------------------------------------------
PVZ1-like tuning:
- Pea=20 dmg, Basic Zombie ~200 HP, breakable cone/bucket armor
- Snow slow halves walk & chew for ~4s
- Sunflower 25 sun / 24s (first sun ~12s)
- Day sky sun trickle (7–10s)
- Garlic shunts to adjacent lane only
- Cherry Bomb arms 1.2s then explodes
- Potato Mine arms 14s then one-shot (very high dmg)
- Squash lunges within ~1.5 tiles
- Lawnmowers trip on first zombie in lane
- Tooltips; Crazy Dave draw fix
All art runtime-drawn. No external assets.

v0.1.1 Fixes (Nov 2025):
- Fixed schedule shape mismatch causing "ValueError: too many values to unpack".
- Ensured GameScene keeps a reference to app.screen; Crazy Dave cameo draws via the given surface.
- Minor safety/cleanup around overlays and tooltips.
"""

import sys
import math
import random
import time

# Attempt to import pygame with a friendly message if missing.
try:
    import pygame
except Exception as e:
    print("This program requires 'pygame'. Install with: pip install pygame")
    print(f"Import error details: {e}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Global constants (scaled for a compact 600x400 layout)
# ---------------------------------------------------------------------------
TITLE = "PVZ Rebooted v0.1.1 (single file, no assets)"
WIDTH, HEIGHT = 600, 400
FPS = 60

GRID_ROWS = 5
GRID_COLS = 9
TILE = 50                      # compact tiles to fit 5x9 within 600x400
HUD_H = 80
LAWN_X = 80                    # lawn X offset (left)
LAWN_Y = HUD_H + 8             # lawn Y offset (below HUD)
LAWN_W = GRID_COLS * TILE
LAWN_H = GRID_ROWS * TILE

# PVZ-like tuning knobs
PEA_DAMAGE = 20                # pea projectile damage
BASIC_ZOMBIE_HP = 200          # ~10 peas to kill
CONE_ARMOR_HP = 360            # cone durability over a basic zombie
BUCKET_ARMOR_HP = 1100         # bucket durability over a basic zombie
ZOMBIE_SPEED = 20.0            # px/s baseline walk speed
CHEW_INTERVAL = 0.40           # seconds per bite (base)
CHEW_DAMAGE = 20               # damage per bite (base)
SLOW_FACTOR = 0.5              # Snow Pea effect halves walk & chew
SLOW_DURATION = 4.0            # seconds

# Colors
BG = (22, 28, 32)
PANEL = (40, 48, 54)
PANEL_DARK = (30, 36, 42)
GRID_LIGHT = (69, 110, 57)
GRID_DARK  = (62, 98, 51)
WHITE = (240, 240, 240)
BLACK = (20, 20, 20)
YELLOW = (248, 208, 80)
ORANGE = (255, 165, 72)
RED = (224, 70, 70)
GREEN = (84, 190, 108)
CYAN = (92, 208, 236)
GREY = (150, 150, 150)
BROWN = (139, 69, 19)
BLUE = (0, 100, 200)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def clamp(v, a, b): return max(a, min(b, v))

def lerp(a, b, t): return a + (b - a) * t

def ease(t):
    t = clamp(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)

def shadow(surface, rect, radius=8, alpha=110):
    s = pygame.Surface((rect.w + radius*2, rect.h + radius*2), pygame.SRCALPHA)
    pygame.draw.rect(s, (0,0,0,alpha), (radius, radius, rect.w, rect.h), border_radius=radius)
    surface.blit(s, (rect.x - radius, rect.y - radius))

# Pseudo-3D helpers for Crazy Dave
def draw_3d_cube(surf, pos, size, colors, rotation=0):
    angle = math.radians(rotation)
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    # Front face
    front = pygame.Rect(pos[0], pos[1], size, size)
    pygame.draw.rect(surf, colors[0], front)
    # Top face
    top_points = [
        (pos[0], pos[1]),
        (pos[0] + size, pos[1]),
        (pos[0] + size * cos_a - size * sin_a / 2, pos[1] - size * sin_a),
        (pos[0] + cos_a * size - sin_a * size / 2, pos[1] - sin_a * size)
    ]
    pygame.draw.polygon(surf, colors[1], top_points)
    # Side face
    side_points = [
        (pos[0] + size, pos[1]),
        (pos[0] + size, pos[1] + size),
        (pos[0] + size + cos_a * size / 2 + sin_a * size, pos[1] + size - sin_a * size / 2),
        (pos[0] + size + cos_a * size / 2, pos[1] - sin_a * size / 2)
    ]
    pygame.draw.polygon(surf, colors[2], side_points)

# Grid helpers
def cell_rect(row, col):
    x = LAWN_X + col*TILE
    y = LAWN_Y + row*TILE
    return pygame.Rect(x, y, TILE, TILE)

def point_to_cell(px, py):
    if px < LAWN_X or py < LAWN_Y or px >= LAWN_X+LAWN_W or py >= LAWN_Y+LAWN_H:
        return None
    col = (px - LAWN_X) // TILE
    row = (py - LAWN_Y) // TILE
    return int(row), int(col)

# ---------------------------------------------------------------------------
# UI primitives
# ---------------------------------------------------------------------------
class Button:
    def __init__(self, rect, text, action=None, font=None, tip=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.action = action
        self.font = font
        self.tip = tip
        self._hover = False
        self._down = False

    def handle(self, event):
        if event.type == pygame.MOUSEMOTION:
            self._hover = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._hover:
                self._down = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._down and self._hover and self.action:
                self.action()
            self._down = False

    def draw(self, surf, colors=(PANEL, PANEL_DARK), text_color=WHITE):
        base = colors[0]
        if self._down and self._hover:
            base = (int(base[0]*0.8), int(base[1]*0.8), int(base[2]*0.8))
        elif self._hover:
            base = (min(int(base[0]*1.1),255), min(int(base[1]*1.1),255), min(int(base[2]*1.1),255))
        shadow(surf, self.rect, radius=10, alpha=120)
        pygame.draw.rect(surf, base, self.rect, border_radius=10)
        pygame.draw.rect(surf, (0,0,0), self.rect, 2, border_radius=10)
        if self.font:
            txt = self.font.render(self.text, True, text_color)
            surf.blit(txt, txt.get_rect(center=self.rect.center))

# ---------------------------------------------------------------------------
# Seed system
# ---------------------------------------------------------------------------
class SeedType:
    def __init__(self, key, display, cost, cooldown, color, build_fn, desc):
        self.key = key
        self.display = display
        self.cost = cost
        self.cooldown = cooldown
        self.color = color
        self.build_fn = build_fn
        self.desc = desc

class SeedCard:
    W, H = 90, 66  # compact card to fit across 600px HUD
    def __init__(self, seed: SeedType, pos):
        self.seed = seed
        self.rect = pygame.Rect(pos[0], pos[1], SeedCard.W, SeedCard.H)
        self.remaining_cd = 0.0
        self._hover = False

    def can_use(self, sun):
        return self.remaining_cd <= 0 and sun >= self.seed.cost

    def start_cd(self):
        self.remaining_cd = self.seed.cooldown

    def update(self, dt):
        if self.remaining_cd > 0:
            self.remaining_cd -= dt

    def handle_hover(self, pos):
        self._hover = self.rect.collidepoint(pos)

    def draw(self, surf, font_small, font_med, selected=False, sun=0):
        base = self.seed.color
        if selected:
            base = (clamp(base[0]+36,0,255), clamp(base[1]+36,0,255), clamp(base[2]+36,0,255))
        shadow(surf, self.rect, radius=8, alpha=100)
        pygame.draw.rect(surf, base, self.rect, border_radius=8)
        pygame.draw.rect(surf, BLACK, self.rect, 2, border_radius=8)
        # icon (simple bar)
        icon_r = pygame.Rect(self.rect.x+8, self.rect.y+8, self.rect.w-16, 18)
        pygame.draw.rect(surf, (240,240,240), icon_r, border_radius=6)
        # name + cost
        name = font_small.render(self.seed.display, True, BLACK)
        cost = font_small.render(f"{self.seed.cost}", True, YELLOW if sun>=self.seed.cost else GREY)
        surf.blit(name, (self.rect.x+8, self.rect.y+32))
        surf.blit(cost, (self.rect.right-8-cost.get_width(), self.rect.y+32))
        # cooldown overlay
        if self.remaining_cd > 0:
            t = clamp(self.remaining_cd / self.seed.cooldown, 0, 1)
            h = int(self.rect.h * t)
            over = pygame.Surface((self.rect.w, h), pygame.SRCALPHA)
            over.fill((0,0,0,120))
            surf.blit(over, (self.rect.x, self.rect.bottom - h))
        # hover cue
        if self._hover:
            pygame.draw.rect(surf, CYAN, self.rect, 2, border_radius=8)

# ---------------------------------------------------------------------------
# Entities: Plants, Projectiles, Enemies, Suns, Lawnmowers
# ---------------------------------------------------------------------------
class Plant:
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.health = 100
        self.max_health = 100

    def rect(self):
        return cell_rect(self.row, self.col).inflate(-10, -10)

    def update(self, dt, game): pass

    def draw(self, surf):
        r = self.rect()
        pygame.draw.rect(surf, (170, 220, 170), r, border_radius=10)
        if self.health < self.max_health:
            p = clamp(self.health/self.max_health, 0, 1)
            bar_bg = pygame.Rect(r.x, r.bottom+1, r.w, 5)
            bar = pygame.Rect(r.x, r.bottom+1, int(r.w*p), 5)
            pygame.draw.rect(surf, RED, bar_bg)
            pygame.draw.rect(surf, GREEN, bar)

    def hurt(self, dmg):
        self.health -= dmg
        return self.health <= 0

class Shooter(Plant):
    def __init__(self, row, col):
        super().__init__(row, col)
        self.cool = 0.0
        self.rate = 1.35  # seconds (PVZ-ish)
        self.color = (120, 200, 120)
        self.max_health = self.health = 300

    def update(self, dt, game):
        self.cool -= dt
        # fire if enemy in same row ahead
        ahead = any(e.row == self.row and e.x > cell_rect(self.row, self.col).right for e in game.enemies)
        if ahead and self.cool <= 0:
            self.cool = self.rate
            cx, cy = cell_rect(self.row, self.col).center
            game.projectiles.append(Projectile(self.row, cx+8, cy-4, snow=False))

    def draw(self, surf):
        r = self.rect()
        pygame.draw.rect(surf, self.color, r, border_radius=12)
        pygame.draw.circle(surf, (30,120,30), (r.centerx+10, r.centery-6), 7)
        super().draw(surf)

class Solarbud(Plant):
    def __init__(self, row, col):
        super().__init__(row, col)
        # PVZ-like cadence: 25 sun every ~24s, first sun ~12s
        self.timer = 12.0
        self.interval = 24.0
        self.max_health = self.health = 300
        self.color = (255, 220, 120)

    def update(self, dt, game):
        self.timer -= dt
        if self.timer <= 0:
            self.timer += self.interval
            cr = self.rect()
            sx = random.randint(cr.x, cr.right)
            sy = cr.y - 8
            game.suns.append(Sun(sx, sy, value=25))

    def draw(self, surf):
        r = self.rect()
        pygame.draw.circle(surf, self.color, r.center, r.w//3)
        pygame.draw.circle(surf, (240, 200, 80), (r.centerx, r.centery), r.w//3-5, 3)
        super().draw(surf)

class Wallnut(Plant):
    def __init__(self, row, col):
        super().__init__(row, col)
        self.max_health = self.health = 1600  # chunky, lasts a while
        self.color = (150,120,90)

    def update(self, dt, game): pass

    def draw(self, surf):
        r = self.rect()
        pygame.draw.rect(surf, self.color, r, border_radius=14)
        pygame.draw.rect(surf, BROWN, r, 3, border_radius=14)
        super().draw(surf)

class CherryBomb(Plant):
    def __init__(self, row, col):
        super().__init__(row, col)
        self.arm_time = 1.2   # PVZ-ish fuse
        self.color = (220, 140, 140)
        self.max_health = self.health = 100

    def update(self, dt, game):
        self.arm_time -= dt
        if self.arm_time <= 0:
            # explode once then remove self
            center_col = self.col
            for er in range(max(0, self.row - 1), min(GRID_ROWS, self.row + 2)):
                for ec in range(max(0, center_col - 1), min(GRID_COLS, center_col + 2)):
                    cx = LAWN_X + ec*TILE + TILE/2
                    for e in game.enemies:
                        if e.row == er and abs(e.x - cx) < TILE + 6 and e.alive:
                            e.hurt(1200)  # high AoE to reliably delete clustered threats
            game.plants[self.row][self.col] = None

    def draw(self, surf):
        r = self.rect()
        pygame.draw.ellipse(surf, self.color, r)
        t = clamp(self.arm_time / 1.2, 0, 1)
        if t > 0:
            pygame.draw.circle(surf, GREEN, r.center, max(2, int(10 * t)))
        super().draw(surf)

class SnowPea(Plant):
    def __init__(self, row, col):
        super().__init__(row, col)
        self.cool = 0.0
        self.rate = 1.35
        self.color = (100, 160, 200)
        self.max_health = self.health = 300

    def update(self, dt, game):
        self.cool -= dt
        ahead = any(e.row == self.row and e.x > cell_rect(self.row, self.col).right for e in game.enemies)
        if ahead and self.cool <= 0:
            self.cool = self.rate
            cx, cy = cell_rect(self.row, self.col).center
            game.projectiles.append(Projectile(self.row, cx + 8, cy - 4, snow=True))

    def draw(self, surf):
        r = self.rect()
        pygame.draw.rect(surf, self.color, r, border_radius=12)
        pygame.draw.circle(surf, (50, 120, 180), (r.centerx + 10, r.centery - 6), 7)
        super().draw(surf)

class Garlic(Plant):
    def __init__(self, row, col):
        super().__init__(row, col)
        self.max_health = self.health = 300
        self.color = (200, 180, 100)

    def update(self, dt, game): pass

    def draw(self, surf):
        r = self.rect()
        pygame.draw.rect(surf, self.color, r, border_radius=8)
        pygame.draw.line(surf, WHITE, (r.centerx - 8, r.top + 5), (r.centerx + 8, r.top + 5), 2)
        pygame.draw.line(surf, WHITE, (r.centerx, r.top + 5), (r.centerx, r.top + 15), 2)
        super().draw(surf)

class PotatoMine(Plant):
    def __init__(self, row, col):
        super().__init__(row, col)
        self.arm_time = 14.0  # PVZ-like (long)
        self.armed = False
        self.color = (139, 69, 19)
        self.max_health = self.health = 80

    def update(self, dt, game):
        if not self.armed:
            self.arm_time -= dt
            if self.arm_time <= 0:
                self.armed = True
        if self.armed:
            col = self.col
            cx = cell_rect(self.row, col).centerx
            for e in game.enemies:
                if e.row == self.row and e.alive and abs(e.x - cx) < TILE * 0.65:
                    e.hurt(5000)  # one-shot most non-boss enemies
                    game.plants[self.row][self.col] = None
                    break

    def draw(self, surf):
        r = self.rect()
        pygame.draw.circle(surf, self.color, r.center, r.w // 3)
        if self.armed:
            pygame.draw.circle(surf, BROWN, r.center, r.w // 3 - 5, 2)
        else:
            t = clamp(self.arm_time / 14.0, 0, 1)
            pygame.draw.circle(surf, GREEN, r.center, max(2, int(8 * t)))
        super().draw(surf)

class Squash(Plant):
    def __init__(self, row, col):
        super().__init__(row, col)
        self.color = (0, 150, 0)
        self.max_health = self.health = 100
        self.ready = True

    def update(self, dt, game):
        if not self.ready: return
        cx = cell_rect(self.row, self.col).centerx
        # find nearest enemy within ~1.5 tiles
        in_range = [e for e in game.enemies if e.row == self.row and e.alive and abs(e.x - cx) < TILE * 1.5]
        if in_range:
            target = min(in_range, key=lambda e: abs(e.x - cx))
            target.hurt(5000)
            self.ready = False
            game.plants[self.row][self.col] = None

    def draw(self, surf):
        r = self.rect()
        pygame.draw.rect(surf, self.color, r, border_radius=6)
        super().draw(surf)

class Projectile:
    def __init__(self, row, x, y, snow=False):
        self.row = row
        self.x = x
        self.y = y
        self.v = 280.0
        self.dmg = PEA_DAMAGE
        self.snow = snow
        self.alive = True

    def update(self, dt, game):
        self.x += self.v * dt
        if self.x > LAWN_X + LAWN_W + 24:
            self.alive = False
            return
        # hit enemy in same row
        for e in game.enemies:
            if e.row == self.row and e.alive and e.rect().collidepoint(self.x, self.y):
                e.hurt(self.dmg, slow=self.snow)
                self.alive = False
                break

    def draw(self, surf):
        col = (80, 200, 60) if not self.snow else (100, 180, 220)
        pygame.draw.circle(surf, col, (int(self.x), int(self.y)), 4)

class Enemy:
    def __init__(self, row, kind="walker", hp=BASIC_ZOMBIE_HP, speed=ZOMBIE_SPEED, dmg=CHEW_DAMAGE, armor=None):
        self.row = row
        self.y = LAWN_Y + row * TILE + 6
        self.kind = kind
        self.health = hp
        self.max_health = hp
        self.speed = speed
        self.dmg = dmg
        self.x = LAWN_X + LAWN_W + 18
        self.alive = True
        self.eating = False
        self._eat_timer = 0.0
        self.slow_timer = 0.0
        # Armor modeling (cone/bucket break off)
        self.armor_type = armor  # None, "cone", "bucket"
        if armor == "cone":
            self.armor_hp = CONE_ARMOR_HP
        elif armor == "bucket":
            self.armor_hp = BUCKET_ARMOR_HP
        else:
            self.armor_hp = 0

    def rect(self):
        return pygame.Rect(int(self.x) - 22, self.y, 44, TILE - 12)

    def update(self, dt, game):
        if not self.alive: return
        slowed = (self.slow_timer > 0)
        if slowed:
            self.slow_timer -= dt
        move_speed = self.speed * (SLOW_FACTOR if slowed else 1.0)

        col = int((self.x - LAWN_X) // TILE)
        col = clamp(col, 0, GRID_COLS - 1)
        plant = game.plants[self.row][col]

        if plant:
            # Garlic: adjacent-lane shunt only
            if isinstance(plant, Garlic):
                options = []
                if self.row > 0: options.append(self.row - 1)
                if self.row < GRID_ROWS - 1: options.append(self.row + 1)
                if options:
                    new_row = random.choice(options)
                    self.row = new_row
                    self.y = LAWN_Y + new_row * TILE + 6
                    # slight stumble back
                    self.x -= move_speed * dt * 0.5
                self.eating = False
            else:
                self.eating = True
                chew_interval = CHEW_INTERVAL * (SLOW_FACTOR if slowed else 1.0)
                self._eat_timer -= dt
                if self._eat_timer <= 0:
                    self._eat_timer = chew_interval
                    died = plant.hurt(self.dmg)
                    if died:
                        game.plants[self.row][col] = None
        else:
            self.eating = False
            self.x -= move_speed * dt

        # off left edge => trigger lawnmower or lose
        if self.x < LAWN_X - 36:
            mower = game.lawnmowers[self.row]
            if mower and mower.alive:
                if not mower.moving:
                    mower.start_moving()
                mower.kill_zombie(self)
                self.alive = False
            else:
                game.lose_flag = True

    def hurt(self, dmg, slow=False):
        # peel armor first
        if self.armor_hp > 0:
            self.armor_hp -= dmg
            if self.armor_hp <= 0:
                # armor breaks; revert to walker visuals/stats
                self.armor_hp = 0
                self.armor_type = None
                self.kind = "walker"
            # apply slow even if armor took it
            if slow:
                self.slow_timer = max(self.slow_timer, SLOW_DURATION)
            return
        # hit body
        self.health -= dmg
        if slow:
            self.slow_timer = max(self.slow_timer, SLOW_DURATION)
        if self.health <= 0:
            self.alive = False

    def draw(self, surf):
        r = self.rect()
        colors = {"walker": (140, 80, 80), "brute": (120, 70, 160)}
        color = colors.get(self.kind, (140, 80, 80))
        pygame.draw.rect(surf, color, r, border_radius=10)
        # health bar (body only)
        p = clamp(self.health / self.max_health, 0, 1)
        hb_bg = pygame.Rect(r.x, r.y - 6, r.w, 5)
        hb = pygame.Rect(r.x, r.y - 6, int(r.w * p), 5)
        pygame.draw.rect(surf, RED, hb_bg)
        pygame.draw.rect(surf, GREEN, hb)

        # armor visuals
        if self.armor_type == "cone":
            cone_y = r.top - 10
            points = [(r.left + 10, cone_y), (r.right - 10, cone_y), (r.centerx, cone_y + 15)]
            pygame.draw.polygon(surf, (200, 150, 50), points)
        elif self.armor_type == "bucket":
            bucket_y = r.top - 15
            pygame.draw.rect(surf, GREY, (r.centerx - 12, bucket_y, 24, 12))
            pygame.draw.rect(surf, BLACK, (r.centerx - 12, bucket_y, 24, 12), 1)

        if self.eating:
            pygame.draw.rect(surf, (255, 200, 120), (r.right - 6, r.centery - 5, 4, 10))

class Lawnmower:
    def __init__(self, row):
        self.row = row
        self.x = LAWN_X - 40  # Stationary position on left
        self.y = LAWN_Y + row * TILE + 12
        self.alive = True
        self.moving = False
        self.speed = 100.0

    def start_moving(self):
        self.moving = True

    def update(self, dt, game):
        if self.moving and self.alive:
            self.x += self.speed * dt
            # Kill zombies in path
            for e in game.enemies[:]:
                if e.row == self.row and e.alive and self.x < e.x < self.x + 60:
                    self.kill_zombie(e)
            if self.x > LAWN_X + LAWN_W + 50:
                self.alive = False

    def kill_zombie(self, zombie):
        zombie.alive = False
        # visual effect: mower speeds up after kill
        self.speed += 30.0

    def draw(self, surf):
        if self.alive:
            body = pygame.Rect(self.x, self.y, 40, 16)
            pygame.draw.rect(surf, GREY, body)
            pygame.draw.rect(surf, BLACK, body, 1)
            pygame.draw.circle(surf, BLACK, (int(self.x + 8), int(self.y + 16)), 4)
            pygame.draw.circle(surf, BLACK, (int(self.x + 32), int(self.y + 16)), 4)

class Sun:
    def __init__(self, x, y, value=25):
        self.x = x
        self.y = y
        self.vy = 38.0
        self.value = value
        self.t = 0.0
        self.rect = pygame.Rect(x - 14, y - 14, 28, 28)
        self.alive = True

    def update(self, dt):
        self.t += dt
        if self.t < 1.8:
            self.y += self.vy * dt
            self.rect.topleft = (self.x - 14, self.y - 14)
        if self.t > 8.0:
            self.alive = False

    def draw(self, surf):
        pygame.draw.circle(surf, YELLOW, self.rect.center, 14)
        pygame.draw.circle(surf, ORANGE, self.rect.center, 14, 2)

# ---------------------------------------------------------------------------
# Game Scene
# ---------------------------------------------------------------------------
class GameScene:
    def __init__(self, app, mode="level", level_index=0, tutorial=False, endless=False):
        self.app = app
        self.screen = app.screen  # for occasional special draws
        self.mode = mode
        self.level_index = level_index
        self.tutorial = tutorial
        self.endless = endless

        self.sun = 100
        self.selected_card = None
        self.shovel_mode = False
        self.lawnmowers = [Lawnmower(r) for r in range(GRID_ROWS)]

        # plants grid
        self.plants = [[None for _ in range(GRID_COLS)] for __ in range(GRID_ROWS)]
        self.enemies = []
        self.projectiles = []
        self.suns = []

        # seed bank: only unlocked seeds
        unlocked = [st for st in app.seed_types if st.key in app.unlocked_seeds]
        self.cards = []
        x = 10
        y = 8
        spacing = 8
        for st in unlocked:
            self.cards.append(SeedCard(st, (x, y)))
            x += SeedCard.W + spacing

        # waves/schedule
        self.spawn_timer = 0.0
        self.total_time = 0.0
        self.win_flag = False
        self.lose_flag = False
        self.progress = 0.0

        if self.endless:
            self.schedule = None
        elif self.tutorial:
            self.schedule = self.make_schedule_easy()
        else:
            self.schedule = self.make_schedule_for_level(level_index)
        self._next_spawn_index = 0

        # tutorial scripting
        self.tut = TutorialScript(self) if tutorial else None

        # pause
        self.paused = False

        # Crazy Dave timer
        self.dave_timer = random.uniform(10, 30)
        self._dave_show = 0.0

        # Day sky-sun
        self.sky_sun_timer = random.uniform(7.0, 10.0)

    # schedules
    def make_schedule_easy(self):
        # Standardized shape: (time, row, (kind, armor))
        sched = []
        t = 6.0
        for _ in range(5):
            sched.append((t, random.randint(0, GRID_ROWS-1), ("walker", None)))
            t += random.uniform(4.0, 6.5)
        for i in range(3):
            sched.append((t+4+i*1.0, random.randint(0, GRID_ROWS-1), ("walker", None)))
        sched.sort(key=lambda x: x[0])
        return sched

    def make_schedule_for_level(self, idx):
        rnd = random.Random(1234 + idx * 77)
        world = idx // 10
        base = 5 + world * 4 + (idx % 10) * 2
        sched = []
        t = 7.0
        brute_prob = 0.08 + world * 0.10
        cone_prob = 0.12 if idx >= 5 else 0.0
        bucket_prob = 0.05 if idx >= 15 else 0.0
        for _ in range(base):
            row = rnd.randrange(GRID_ROWS)
            # choose kind & armor
            kind = "walker"
            armor = None
            if rnd.random() < bucket_prob:
                armor = "bucket"
            elif rnd.random() < cone_prob:
                armor = "cone"
            elif rnd.random() < brute_prob:
                kind = "brute"
            sched.append((t, row, (kind, armor)))
            t += rnd.uniform(3.0, 5.5)
        # final wave (basic walkers)
        final_count = 4 + world * 2
        for i in range(final_count):
            sched.append((t + 5 + i * 0.6, rnd.randrange(GRID_ROWS), ("walker", None)))
        sched.sort(key=lambda x: x[0])
        return sched

    # input
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.paused = not self.paused
            elif event.key == pygame.K_SPACE:
                self.sun += 25  # debug

        if self.paused or self.win_flag or self.lose_flag:
            return

        if event.type == pygame.MOUSEMOTION:
            for c in self.cards:
                c.handle_hover(event.pos)

        if event.type == pygame.MOUSEBUTTONDOWN:
            # Right-click => shovel toggle OR cancel selection
            if event.button == 3:
                if self.selected_card:
                    self.selected_card = None
                else:
                    self.shovel_mode = not self.shovel_mode
                return

            if event.button == 1:
                mx, my = event.pos
                # seed cards
                for c in self.cards:
                    if c.rect.collidepoint((mx, my)):
                        if c.can_use(self.sun):
                            self.selected_card = c
                            self.shovel_mode = False
                        else:
                            self.selected_card = None
                        return
                # suns
                for s in self.suns:
                    if s.rect.collidepoint((mx,my)):
                        self.sun += s.value
                        s.alive = False
                        return
                # grid
                cell = point_to_cell(mx, my)
                if cell:
                    r, c = cell
                    if self.shovel_mode:
                        if self.plants[r][c]:
                            self.plants[r][c] = None
                        return
                    if self.selected_card and self.plants[r][c] is None:
                        seed = self.selected_card.seed
                        if self.sun >= seed.cost and self.selected_card.remaining_cd <= 0:
                            self.sun -= seed.cost
                            self.plants[r][c] = seed.build_fn(r, c)
                            self.selected_card.start_cd()
                            if self.tut: self.tut.on_place(seed.key, r, c)
                        self.selected_card = None
                        return
                    self.selected_card = None

    # tick
    def update(self, dt):
        if self.paused:
            return

        self.total_time += dt

        # cooldowns
        for c in self.cards:
            c.update(dt)

        # suns
        for s in self.suns:
            s.update(dt)
        self.suns = [s for s in self.suns if s.alive]

        # Day/Tutorial sky suns
        if not self.endless and (self.level_index // 10 == 0 or self.tutorial):
            self.sky_sun_timer -= dt
            if self.sky_sun_timer <= 0:
                self.sky_sun_timer = random.uniform(7.0, 10.0)
                x = random.randint(LAWN_X, LAWN_X+LAWN_W-28)
                self.suns.append(Sun(x, LAWN_Y, value=25))

        # endless sky suns: gentle trickle
        if self.endless and random.random() < dt*0.55:
            x = random.randint(LAWN_X, LAWN_X+LAWN_W-28)
            self.suns.append(Sun(x, LAWN_Y, value=25))

        # spawn enemies
        if self.endless:
            rate = clamp(0.85 + (60.0 / max(20.0, self.total_time)), 0.85, 3.0)
            self.spawn_timer -= dt
            if self.spawn_timer <= 0:
                self.spawn_timer = rate
                row = random.randrange(GRID_ROWS)
                kind, armor = random.choice(
                    [("walker", None)] * 6 +
                    [("walker", "cone")] * 2 +
                    [("walker", "bucket")] +
                    [("brute", None)]
                )
                hp = BASIC_ZOMBIE_HP if kind == "walker" else 300
                sp = ZOMBIE_SPEED if kind == "walker" else 18.0
                dmg = CHEW_DAMAGE if kind == "walker" else int(CHEW_DAMAGE * 1.1)
                self.enemies.append(Enemy(row, kind=kind, hp=hp, speed=sp, dmg=dmg, armor=armor))
        else:
            sched = self.schedule or []
            while self._next_spawn_index < len(sched) and self.total_time >= sched[self._next_spawn_index][0]:
                _, row, kind_armor = sched[self._next_spawn_index]
                # Back-compat: accept either "walker" or (kind, armor)
                if isinstance(kind_armor, tuple):
                    kind, armor = kind_armor
                else:
                    kind, armor = str(kind_armor), None
                hp = BASIC_ZOMBIE_HP if kind == "walker" else 300
                sp = ZOMBIE_SPEED if kind == "walker" else 18.0
                dmg = CHEW_DAMAGE if kind == "walker" else int(CHEW_DAMAGE * 1.1)
                self.enemies.append(Enemy(row, kind=kind, hp=hp, speed=sp, dmg=dmg, armor=armor))
                self._next_spawn_index += 1
            self.progress = 0.0 if not sched else clamp(self._next_spawn_index / len(sched), 0, 1)

        # plants
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                p = self.plants[r][c]
                if p:
                    p.update(dt, self)

        # projectiles
        for pr in self.projectiles:
            pr.update(dt, self)
        self.projectiles = [p for p in self.projectiles if p.alive]

        # enemies
        for e in self.enemies:
            e.update(dt, self)
        self.enemies = [e for e in self.enemies if e.alive]

        # lawnmowers
        for mower in self.lawnmowers:
            mower.update(dt, self)

        # Crazy Dave occasional appearance (draw handled in draw())
        self.dave_timer -= dt
        if self.dave_timer <= 0 and self._dave_show <= 0:
            self._dave_show = 2.5  # show Dave for a short moment
            self.dave_timer = random.uniform(20, 40)
        if self._dave_show > 0:
            self._dave_show -= dt

        # win/lose state
        if not self.endless:
            if self._next_spawn_index >= len(self.schedule or []) and len([e for e in self.enemies if e.alive]) == 0:
                self.win_flag = True

        if self.tut:
            self.tut.update(dt)

    def draw(self, surf):
        # background + HUD panel
        surf.fill(BG)
        top = pygame.Rect(0, 0, WIDTH, HUD_H)
        pygame.draw.rect(surf, PANEL, top)
        pygame.draw.line(surf, BLACK, (0, HUD_H), (WIDTH, HUD_H), 2)

        # seed bank row
        for c in self.cards:
            c.draw(surf, self.app.font_small, self.app.font_small, selected=(self.selected_card==c), sun=self.sun)

        # Sun counter (top-right)
        sbox = pygame.Rect(WIDTH-128, 10, 118, 60)
        shadow(surf, sbox, radius=8, alpha=100)
        pygame.draw.rect(surf, (60,80,60), sbox, border_radius=8)
        pygame.draw.rect(surf, BLACK, sbox, 2, border_radius=8)
        sun_txt = self.app.font_large.render(str(self.sun), True, YELLOW)
        surf.blit(sun_txt, sun_txt.get_rect(center=sbox.center))

        # Shovel indicator
        tag = self.app.font_small.render(f"Shovel: {'ON' if self.shovel_mode else 'OFF'}", True,
                                         RED if self.shovel_mode else GREY)
        surf.blit(tag, (sbox.x+8, sbox.bottom-18))

        # progress
        if not self.endless:
            bar = pygame.Rect(10, HUD_H-18, WIDTH-20, 10)
            pygame.draw.rect(surf, (70,70,90), bar, border_radius=6)
            inner = pygame.Rect(bar.x+2, bar.y+2, int((bar.w-4) * self.progress), bar.h-4)
            pygame.draw.rect(surf, CYAN, inner, border_radius=6)
            world_names = ['Day', 'Night', 'Pool', 'Fog', 'Roof']
            w = self.level_index // 10
            l = self.level_index % 10 + 1
            lab = self.app.font_small.render(f"{world_names[w]} {l}", True, WHITE)
            surf.blit(lab, (WIDTH//2 - lab.get_width()//2, HUD_H - 22))
        else:
            lab = self.app.font_small.render("Endless", True, WHITE)
            surf.blit(lab, (10, HUD_H-22))

        # grid
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                rect = cell_rect(r, c)
                color = GRID_LIGHT if (r+c)%2==0 else GRID_DARK
                pygame.draw.rect(surf, color, rect)
                pygame.draw.rect(surf, (0,0,0), rect, 1)

        # lawnmowers
        for mower in self.lawnmowers:
            if mower.alive:
                mower.draw(surf)

        # plants & entities
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                p = self.plants[r][c]
                if p: p.draw(surf)

        for pr in self.projectiles: pr.draw(surf)
        for e in self.enemies: e.draw(surf)
        for s in self.suns: s.draw(surf)

        # selection preview
        if self.selected_card:
            mx, my = pygame.mouse.get_pos()
            cell = point_to_cell(mx, my)
            if cell:
                r, c = cell
                pr = cell_rect(r, c).inflate(-10, -10)
                pygame.draw.rect(surf, (255,255,255), pr, 2, border_radius=10)

        # Crazy Dave cameo (draw using the given surface)
        if self._dave_show > 0:
            dave_pos = (10, HEIGHT - 100)
            draw_3d_cube(surf, dave_pos, 30, [(200,150,100), (180,130,80), (160,110,60)],
                         math.sin(self.total_time * 2) * 10)
            hat = pygame.Rect(dave_pos[0] - 5, dave_pos[1] - 15, 40, 10)
            pygame.draw.rect(surf, RED, hat)

        # overlays
        if self.paused:
            self.draw_overlay(surf, "Paused", buttons=[("Resume", self.toggle_pause),
                                                       ("Main Menu", self.to_menu)])
        if self.win_flag:
            if self.tutorial or self.endless:
                buttons = [("Replay", self.replay), ("Main Menu", self.to_menu)]
            elif self.level_index + 1 < self.app.max_level:
                buttons = [("Next Level", self.next_level), ("Replay", self.replay), ("Main Menu", self.to_menu)]
            else:
                buttons = [("You've Won!", self.to_menu), ("Replay", self.replay)]
            self.draw_overlay(surf, "Level Complete!", buttons=buttons)
        if self.lose_flag:
            self.draw_overlay(surf, "You've Lost!", buttons=[("Retry", self.replay),
                                                             ("Main Menu", self.to_menu)])

        # seed hover tooltip
        hovered = next((c for c in self.cards if c._hover), None)
        if hovered:
            tip = hovered.seed.desc
            tw = max(160, self.app.font_small.size(tip)[0] + 14)
            th = 24
            box = pygame.Rect(0,0, tw, th)
            box.topleft = (hovered.rect.x, hovered.rect.bottom + 4)
            shadow(surf, box, radius=8, alpha=120)
            pygame.draw.rect(surf, (50,60,70), box, border_radius=6)
            pygame.draw.rect(surf, BLACK, box, 1, border_radius=6)
            surf.blit(self.app.font_small.render(tip, True, WHITE), (box.x+7, box.y+4))

        if self.tut:
            self.tut.draw(surf)

    # overlay helpers
    def toggle_pause(self):
        self.paused = not self.paused

    def to_menu(self):
        self.app.change_scene(MainMenu(self.app))

    def next_level(self):
        nxt = self.level_index + 1
        self.app.unlocked_level = max(self.app.unlocked_level, nxt + 1)
        if nxt % 10 == 0 and nxt > 0:
            # unlock new seeds at end of world
            if nxt == 10:
                self.app.unlocked_seeds.add("cherry")
            elif nxt == 20:
                self.app.unlocked_seeds.add("snow")
            elif nxt == 30:
                self.app.unlocked_seeds.add("garlic")
            elif nxt == 40:
                self.app.unlocked_seeds.add("potato")
                self.app.unlocked_seeds.add("squash")
        if nxt < self.app.max_level:
            self.app.change_scene(GameScene(self.app, mode="level", level_index=nxt))
        else:
            self.to_menu()

    def replay(self):
        self.app.change_scene(GameScene(self.app, mode=self.mode,
                                        level_index=self.level_index,
                                        tutorial=self.tutorial,
                                        endless=self.endless))

    def draw_overlay(self, surf, title, buttons):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0,0,0,160))
        surf.blit(overlay, (0,0))
        box = pygame.Rect(0,0, 380, 220)
        box.center = (WIDTH//2, HEIGHT//2)
        shadow(surf, box, radius=14, alpha=160)
        pygame.draw.rect(surf, PANEL, box, border_radius=14)
        pygame.draw.rect(surf, BLACK, box, 2, border_radius=14)
        tit = self.app.font_large.render(title, True, WHITE)
        surf.blit(tit, tit.get_rect(center=(box.centerx, box.y+48)))
        bx = box.x + 22
        by = box.y + 110
        self._overlay_btns = []
        for (txt, fn) in buttons:
            b = Button(pygame.Rect(bx, by, 160, 40), txt, action=fn, font=self.app.font_med)
            b.draw(surf)
            self._overlay_btns.append(b)
            bx += 170 if len(buttons) > 2 else 190

    def handle_overlay_event(self, event):
        if hasattr(self, "_overlay_btns"):
            for b in self._overlay_btns:
                b.handle(event)

# ---------------------------------------------------------------------------
# Tutorial Script
# ---------------------------------------------------------------------------
class TutorialScript:
    def __init__(self, game: GameScene):
        self.game = game
        self.phase = 0
        self.bubbles = []  # list of [text, ttl]
        self.say("Welcome! I'm your wacky neighbor.", 5)
        self.say("Collect sun and place a Sunflower.", 6)

    def say(self, text, ttl=5.0):
        self.bubbles.append([text, ttl])

    def on_place(self, seed_key, r, c):
        if self.phase == 0 and seed_key == "solar":
            self.say("Nice! Sunflowers make sun over time.", 5)
            self.say("Now place a Peashooter to defend.", 6)
            self.phase = 1
        elif self.phase == 1 and seed_key == "shoot":
            self.say("Great! Ready for a small wave.", 4)
            self.phase = 2
            for _ in range(3):
                self.game.enemies.append(Enemy(random.randrange(GRID_ROWS)))

    def update(self, dt):
        for b in self.bubbles:
            b[1] -= dt
        self.bubbles = [b for b in self.bubbles if b[1] > 0]
        # gentle sun trickle for tutorial (already have day sky sun; keep a light extra)
        if random.random() < dt*0.25:
            x = random.randint(LAWN_X, LAWN_X+LAWN_W-28)
            self.game.suns.append(Sun(x, LAWN_Y, 25))

    def draw(self, surf):
        base = pygame.Rect(10, HEIGHT-130, 360, 120)
        shadow(surf, base, radius=12, alpha=120)
        pygame.draw.rect(surf, PANEL, base, border_radius=12)
        pygame.draw.rect(surf, BLACK, base, 2, border_radius=12)
        title = self.game.app.font_med.render("Neighbor", True, WHITE)
        surf.blit(title, (base.x+12, base.y+10))
        y = base.y + 38
        for (text, ttl) in self.bubbles[-3:]:
            label = self.game.app.font_small.render(text, True, WHITE)
            surf.blit(label, (base.x+12, y))
            y += 20

# ---------------------------------------------------------------------------
# Menu / Level Select
# ---------------------------------------------------------------------------
class MainMenu:
    def __init__(self, app):
        self.app = app
        self.buttons = []
        cx = WIDTH//2 - 120
        cy = 170
        self.buttons.append(Button(pygame.Rect(cx, cy, 240, 52), "Adventure",
                                   action=self.adventure, font=app.font_med))
        cy += 60
        self.buttons.append(Button(pygame.Rect(cx, cy, 240, 52), "Tutorial",
                                   action=self.tutorial, font=app.font_med))
        cy += 60
        self.buttons.append(Button(pygame.Rect(cx, cy, 240, 52), "Endless",
                                   action=self.endless, font=app.font_med))
        cy += 60
        self.buttons.append(Button(pygame.Rect(cx, cy, 240, 52), "Quit",
                                   action=self.quit, font=app.font_med))

    def adventure(self): self.app.change_scene(LevelSelect(self.app))
    def tutorial(self): self.app.change_scene(GameScene(self.app, tutorial=True))
    def endless(self): self.app.change_scene(GameScene(self.app, endless=True, mode="endless"))
    def quit(self): pygame.event.post(pygame.event.Event(pygame.QUIT))

    def handle_event(self, event):
        for b in self.buttons: b.handle(event)

    def update(self, dt): pass

    def draw(self, surf):
        surf.fill(BG)
        t = self.app.font_title.render("PVZ Rebooted", True, WHITE)
        surf.blit(t, t.get_rect(center=(WIDTH//2, 100)))
        s = self.app.font_small.render("v0.1.1 — No assets. Single file. PVZ1-like physics.", True, GREY)
        surf.blit(s, s.get_rect(center=(WIDTH//2, 132)))
        for b in self.buttons: b.draw(surf)

class LevelSelect:
    def __init__(self, app):
        self.app = app
        self.buttons = []
        self.world_names = ['Day', 'Night', 'Pool', 'Fog', 'Roof']
        cols = 4
        spacing_x = 140
        spacing_y = 65
        x0 = 20
        y0 = 140
        for i in range(self.app.unlocked_level):
            c = i % cols
            r = i // cols
            w_idx = i // 10
            l = i % 10 + 1
            label = f"{self.world_names[w_idx]} {l}"
            rect = pygame.Rect(x0 + c * spacing_x, y0 + r * spacing_y, 120, 50)
            self.buttons.append(Button(rect, label, action=lambda idx=i: self.play(idx), font=self.app.font_small))
        self.back_btn = Button(pygame.Rect(14, HEIGHT-60, 160, 44), "Back", action=self.back, font=self.app.font_med)

    def play(self, idx):
        self.app.change_scene(GameScene(self.app, mode="level", level_index=idx))

    def back(self):
        self.app.change_scene(MainMenu(self.app))

    def handle_event(self, event):
        for b in self.buttons: b.handle(event)
        self.back_btn.handle(event)

    def update(self, dt): pass

    def draw(self, surf):
        surf.fill(BG)
        t = self.app.font_title.render("Adventure - Worlds", True, WHITE)
        surf.blit(t, t.get_rect(center=(WIDTH//2, 80)))
        for b in self.buttons: b.draw(surf)
        self.back_btn.draw(surf)

# ---------------------------------------------------------------------------
# App (scene manager) and seed definitions
# ---------------------------------------------------------------------------
class App:
    def __init__(self):
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        # Fonts
        self.font_small = pygame.font.Font(None, 22)
        self.font_med = pygame.font.Font(None, 30)
        self.font_large = pygame.font.Font(None, 38)
        self.font_title = pygame.font.Font(None, 60)
        # Seed types (PVZ1-ish costs & cooldowns)
        self.seed_types = [
            SeedType("shoot", "Peashooter", 100, 7.5, (96, 170, 96), lambda r,c: Shooter(r,c),
                     "Shoots peas at enemies in its lane."),
            SeedType("solar", "Sunflower", 50, 7.5, (210, 180, 80), lambda r,c: Solarbud(r,c),
                     "Generates sun over time."),
            SeedType("wall", "Wall-nut", 50, 30.0, (140, 110, 80), lambda r,c: Wallnut(r,c),
                     "High-health barrier."),
            SeedType("cherry", "Cherry Bomb", 150, 50.0, (220, 140, 140), lambda r,c: CherryBomb(r,c),
                     "Explodes after ~1.2s (3x3 area)."),
            SeedType("snow", "Snow Pea", 175, 7.5, (120, 180, 200), lambda r,c: SnowPea(r,c),
                     "Shoots peas that slow zombies."),
            SeedType("garlic", "Garlic", 50, 7.5, (200, 180, 100), lambda r,c: Garlic(r,c),
                     "Diverts zombies to adjacent lane."),
            SeedType("potato", "Potato Mine", 25, 30.0, (139, 69, 19), lambda r,c: PotatoMine(r,c),
                     "Arms in ~14s, then one-shots on contact."),
            SeedType("squash", "Squash", 50, 30.0, (0, 150, 0), lambda r,c: Squash(r,c),
                     "Squashes nearby zombie on sight."),
        ]
        self.unlocked_seeds = set(["shoot", "solar", "wall"])
        self.max_level = 50
        self.unlocked_level = 1
        self.scene = MainMenu(self)

    def change_scene(self, scene):
        self.scene = scene

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    if isinstance(self.scene, GameScene) and (self.scene.paused or self.scene.win_flag or self.scene.lose_flag):
                        self.scene.handle_overlay_event(event)
                    else:
                        self.scene.handle_event(event)
            # update/draw
            self.scene.update(dt)
            self.scene.draw(self.screen)
            # cursor hint when shovel is active
            if isinstance(self.scene, GameScene) and self.scene.shovel_mode:
                mx, my = pygame.mouse.get_pos()
                pygame.draw.circle(self.screen, RED, (mx, my), 9, 2)
                pygame.draw.line(self.screen, RED, (mx-10, my-10), (mx+10, my+10), 2)
                pygame.draw.line(self.screen, RED, (mx-10, my+10), (mx+10, my-10), 2)
            pygame.display.flip()
        pygame.quit()

def main():
    pygame.init()
    App().run()

if __name__ == "__main__":
    main()
