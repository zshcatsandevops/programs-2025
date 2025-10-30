#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PVZ-Lite: A no-asset, pygame-based, PopCap-inspired lane defense engine.
------------------------------------------------------------
License: GPL-3.0-or-later
Author: FlamesCo Labs ✦ (generated via GPT-Next BSD Neural Runtime)
Runtime: pygame
Target: 60 FPS ("vibes = on")

Notes
-----
- This is an original engine inspired by lane-defense mechanics; it uses no copyrighted assets.
- Graphics are simple shapes and text; feel free to replace with your own art later.
- The code is intentionally verbose with comments for learning and modding.
- Single-file build, as requested: program.py
"""

import math
import random
import sys
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict

import pygame

# ---------------------------
# Global Configuration
# ---------------------------
class CFG:
    CAPTION = "PVZ-Lite — No Assets, Just Vibes (60 FPS)"
    WIDTH = 1280
    HEIGHT = 720
    FPS = 60

    # Board layout (5 rows x 9 cols like the classic day level)
    ROWS = 5
    COLS = 9

    # Tile sizing and margins
    TILE_W = 110
    TILE_H = 110
    BOARD_LEFT = 240  # left margin for lawn
    BOARD_TOP = 90    # top margin for lawn

    # UI seed bank sizing
    SEED_BANK_HEIGHT = 80
    SEED_CARD_W = 120
    SEED_CARD_H = 70
    SEED_CARD_MARGIN = 8

    # Economy
    STARTING_SUN = 50
    SUN_VALUE = 25
    SKY_SUN_INTERVAL = (7.0, 13.0)  # seconds (min, max) for random sky drops

    # Colors (RGB)
    COLOR_BG_TOP = (85, 180, 255)
    COLOR_BG_BOTTOM = (180, 235, 255)
    COLOR_LAWN_LIGHT = (116, 196, 118)
    COLOR_LAWN_DARK = (49, 163, 84)
    COLOR_GRID_LINES = (30, 120, 50)
    COLOR_TEXT = (30, 30, 30)
    COLOR_ACCENT = (255, 215, 0)
    COLOR_UI = (240, 240, 240)
    COLOR_UI_DARK = (200, 200, 200)
    COLOR_RED = (200, 60, 60)
    COLOR_BULLET = (40, 120, 40)
    COLOR_MOWER = (220, 220, 220)

    # Gameplay pacing
    FAST_FORWARD = 1.0  # 1.0 = normal; set to 2.0 for 2x dev testing

    # Fonts
    FONT_NAME = None  # pygame will use default if None


# ---------------------------
# Helpers
# ---------------------------
def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def lerp(a, b, t):
    return a + (b - a) * t


def rect_from_cell(r, c):
    x = CFG.BOARD_LEFT + c * CFG.TILE_W
    y = CFG.BOARD_TOP + r * CFG.TILE_H
    return pygame.Rect(x, y, CFG.TILE_W, CFG.TILE_H)


def cell_center(r, c) -> Tuple[int, int]:
    rc = rect_from_cell(r, c)
    return (rc.x + rc.w // 2, rc.y + rc.h // 2)


def pos_to_cell(mx, my) -> Optional[Tuple[int, int]]:
    # Returns (row, col) if inside the lawn grid, else None.
    x0, y0 = CFG.BOARD_LEFT, CFG.BOARD_TOP
    x1 = x0 + CFG.COLS * CFG.TILE_W
    y1 = y0 + CFG.ROWS * CFG.TILE_H
    if not (x0 <= mx < x1 and y0 <= my < y1):
        return None
    c = (mx - x0) // CFG.TILE_W
    r = (my - y0) // CFG.TILE_H
    return (int(r), int(c))


# ---------------------------
# Entity base
# ---------------------------
class Entity:
    def __init__(self):
        self.alive = True

    def update(self, dt: float):
        pass

    def draw(self, surf: pygame.Surface):
        pass


# ---------------------------
# Projectiles & Suns
# ---------------------------
class Pea(Entity):
    def __init__(self, pos: Tuple[int, int], dmg: int = 20, speed: float = 320):
        super().__init__()
        self.x, self.y = float(pos[0]), float(pos[1])
        self.dmg = dmg
        self.speed = speed

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x) - 6, int(self.y) - 6, 12, 12)

    def update(self, dt: float):
        self.x += self.speed * dt * CFG.FAST_FORWARD
        if self.x > CFG.WIDTH + 50:
            self.alive = False

    def draw(self, surf: pygame.Surface):
        pygame.draw.circle(surf, CFG.COLOR_BULLET, (int(self.x), int(self.y)), 6)


class Sun(Entity):
    def __init__(self, pos: Tuple[int, int], fall_to: int, value: int = CFG.SUN_VALUE):
        super().__init__()
        self.x, self.y = float(pos[0]), float(pos[1])
        self.value = value
        self.collect_rect = pygame.Rect(0, 0, 44, 44)
        self.fall_to = fall_to
        self.vy = 0.0
        self.gravity = 600.0
        self.state = "fall"  # fall -> idle -> despawn
        self.idle_time = 9.0

    @property
    def rect(self):
        r = self.collect_rect.copy()
        r.center = (int(self.x), int(self.y))
        return r

    def click(self, pos) -> bool:
        if self.rect.collidepoint(pos):
            self.alive = False
            return True
        return False

    def update(self, dt: float):
        dt *= CFG.FAST_FORWARD
        if self.state == "fall":
            self.vy += self.gravity * dt
            self.y += self.vy * dt
            if self.y >= self.fall_to:
                self.y = float(self.fall_to)
                self.vy = 0.0
                self.state = "idle"
        elif self.state == "idle":
            self.idle_time -= dt
            if self.idle_time <= 0:
                self.alive = False

    def draw(self, surf: pygame.Surface):
        # Shiny circle with a glow
        pygame.draw.circle(surf, CFG.COLOR_ACCENT, (int(self.x), int(self.y)), 20)
        pygame.draw.circle(surf, (255, 255, 255), (int(self.x), int(self.y)), 18, 2)


# ---------------------------
# Plants
# ---------------------------
class Plant(Entity):
    name = "Plant"
    cost = 50
    cooldown = 7.0
    max_hp = 100

    def __init__(self, r: int, c: int):
        super().__init__()
        self.r = r
        self.c = c
        self.hp = self.max_hp
        self.tile_rect = rect_from_cell(r, c)
        self.center = (self.tile_rect.x + self.tile_rect.w // 2, self.tile_rect.y + self.tile_rect.h // 2)

    def hurt(self, dmg: int):
        self.hp -= dmg
        if self.hp <= 0:
            self.alive = False

    def draw_health_bar(self, surf: pygame.Surface):
        w = self.tile_rect.w - 12
        x = self.tile_rect.x + 6
        y = self.tile_rect.bottom - 10
        pct = clamp(self.hp / self.max_hp, 0.0, 1.0)
        pygame.draw.rect(surf, (0, 0, 0), (x, y, w, 6), 1)
        pygame.draw.rect(surf, (60, 180, 60), (x + 1, y + 1, int((w - 2) * pct), 4))


class PeaShooter(Plant):
    name = "PeaShooter"
    cost = 100
    cooldown = 7.0
    max_hp = 100

    def __init__(self, r, c):
        super().__init__(r, c)
        self.fire_rate = 1.4
        self.fire_cd = random.uniform(0.1, 0.8)  # slight offset so rows desync

    def update(self, dt: float, projectiles: List[Pea], zombies: List["Zombie"]):
        dt *= CFG.FAST_FORWARD
        # If any zombie is in this row and ahead, we fire when cd <= 0
        danger = any(z.r == self.r and z.x > self.tile_rect.centerx for z in zombies if z.alive)
        if danger:
            self.fire_cd -= dt
            if self.fire_cd <= 0:
                projectiles.append(Pea((self.tile_rect.centerx + 10, self.tile_rect.centery)))
                self.fire_cd = self.fire_rate

    def draw(self, surf: pygame.Surface):
        # Little green turret shape
        pygame.draw.rect(surf, (80, 170, 90), self.tile_rect.inflate(-28, -28), border_radius=10)
        # barrel
        bx = self.tile_rect.centerx + 12
        by = self.tile_rect.centery
        pygame.draw.rect(surf, (60, 150, 70), (bx, by - 6, 28, 12), border_radius=4)
        self.draw_health_bar(surf)


class SunFlower(Plant):
    name = "Sunflower"
    cost = 50
    cooldown = 7.0
    max_hp = 80

    def __init__(self, r, c):
        super().__init__(r, c)
        self.generate_rate = 9.0
        self.gen_cd = 4.0  # first spawn faster

    def update(self, dt: float, suns: List[Sun]):
        dt *= CFG.FAST_FORWARD
        self.gen_cd -= dt
        if self.gen_cd <= 0:
            cx, cy = self.center
            suns.append(Sun((cx, cy - 10), fall_to=cy - 10))
            self.gen_cd = self.generate_rate

    def draw(self, surf: pygame.Surface):
        # Flower-ish
        cx, cy = self.center
        pygame.draw.circle(surf, (240, 200, 60), (cx, cy), 26)
        for i in range(8):
            a = i * (math.pi * 2 / 8)
            px = int(cx + math.cos(a) * 34)
            py = int(cy + math.sin(a) * 34)
            pygame.draw.circle(surf, (255, 220, 90), (px, py), 10)
        self.draw_health_bar(surf)


class WallNut(Plant):
    name = "Wall-Nut"
    cost = 50
    cooldown = 20.0
    max_hp = 500

    def draw(self, surf: pygame.Surface):
        pygame.draw.rect(surf, (150, 110, 80), self.tile_rect.inflate(-18, -18), border_radius=22)
        self.draw_health_bar(surf)


# ---------------------------
# Zombies
# ---------------------------
class Zombie(Entity):
    name = "Zombie"
    max_hp = 220
    speed = 28.0
    dps = 18.0  # damage per second to plants while chewing

    def __init__(self, r: int):
        super().__init__()
        self.r = r
        # Spawn just off the right side
        row_y = CFG.BOARD_TOP + r * CFG.TILE_H
        self.x = float(CFG.BOARD_LEFT + CFG.COLS * CFG.TILE_W + random.randint(10, 80))
        self.y = float(row_y + CFG.TILE_H // 2)
        self.hp = self.max_hp
        self.chewing = False
        self.target: Optional[Plant] = None

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x) - 28, int(self.y) - 40, 56, 80)

    def hurt(self, dmg: int):
        self.hp -= dmg
        if self.hp <= 0:
            self.alive = False

    def update(self, dt: float, grid: "Grid", plants: List[Plant]):
        dt *= CFG.FAST_FORWARD
        if self.chewing and self.target and self.target.alive:
            # munch munch
            self.target.hurt(self.dps * dt)
            # if plant died, resume walk
            if not self.target.alive:
                self.chewing = False
                self.target = None
        else:
            # scan for plant ahead in same row
            next_plant = grid.plant_in_front(self.r, self.rect)
            if next_plant:
                self.chewing = True
                self.target = next_plant
            else:
                self.x -= self.speed * dt

        # off the left side = loss (handled in Game)
        # keep rect consistent
        # (no-op; rect property is derived)

    def draw(self, surf: pygame.Surface):
        body = self.rect
        pygame.draw.rect(surf, (110, 140, 110), body, border_radius=8)
        # mouth line indicates chewing
        if self.chewing:
            pygame.draw.line(surf, (40, 40, 40), (body.centerx - 10, body.centery + 10), (body.centerx + 10, body.centery + 10), 3)
        # health bar
        w = body.w
        pct = clamp(self.hp / self.max_hp, 0.0, 1.0)
        hb = pygame.Rect(body.left, body.top - 8, w, 6)
        pygame.draw.rect(surf, (0, 0, 0), hb, 1)
        pygame.draw.rect(surf, (200, 70, 70), (hb.left + 1, hb.top + 1, int((w - 2) * pct), 4))


# ---------------------------
# Lawn Mower
# ---------------------------
class LawnMower(Entity):
    def __init__(self, r: int):
        super().__init__()
        self.r = r
        cell = rect_from_cell(r, 0)
        self.x = float(cell.left - 40)
        self.y = float(cell.centery)
        self.active = False
        self.speed = 600.0

    @property
    def rect(self):
        return pygame.Rect(int(self.x) - 18, int(self.y) - 12, 36, 24)

    def trigger(self):
        if not self.active:
            self.active = True

    def update(self, dt: float, zombies: List[Zombie]):
        dt *= CFG.FAST_FORWARD
        if self.active:
            self.x += self.speed * dt
            # destroy zombies in row intersecting mower rect
            for z in zombies:
                if z.alive and z.r == self.r and self.rect.colliderect(z.rect):
                    z.alive = False
            if self.x > CFG.WIDTH + 40:
                self.alive = False

    def draw(self, surf: pygame.Surface):
        pygame.draw.rect(surf, CFG.COLOR_MOWER, self.rect, border_radius=6)
        pygame.draw.circle(surf, (60, 60, 60), (self.rect.left + 8, self.rect.bottom), 6)
        pygame.draw.circle(surf, (60, 60, 60), (self.rect.right - 8, self.rect.bottom), 6)


# ---------------------------
# Grid and Placement
# ---------------------------
class Grid:
    def __init__(self):
        # 2D cell -> plant mapping (or None)
        self.cells: List[List[Optional[Plant]]] = [[None for _ in range(CFG.COLS)] for _ in range(CFG.ROWS)]

    def get(self, r, c) -> Optional[Plant]:
        return self.cells[r][c]

    def set(self, r, c, plant: Optional[Plant]):
        self.cells[r][c] = plant

    def empty(self, r, c) -> bool:
        return self.get(r, c) is None

    def plant_in_front(self, r: int, zrect: pygame.Rect) -> Optional[Plant]:
        """Return plant in same row directly in front of zombie rect (if overlapping)."""
        # Which column is the zombie currently overlapping?
        # We'll check from left to right among cells whose x-range intersects zrect.
        for c in range(CFG.COLS):
            cell_rect = rect_from_cell(r, c)
            if zrect.colliderect(cell_rect.inflate(-10, 0)):
                p = self.get(r, c)
                if p and p.alive:
                    return p
        return None

    def remove_dead(self):
        for r in range(CFG.ROWS):
            for c in range(CFG.COLS):
                p = self.cells[r][c]
                if p and not p.alive:
                    self.cells[r][c] = None

    def draw_lawn(self, surf: pygame.Surface):
        # Checkerboard lawn
        for r in range(CFG.ROWS):
            for c in range(CFG.COLS):
                rect = rect_from_cell(r, c)
                color = CFG.COLOR_LAWN_LIGHT if (r + c) % 2 == 0 else CFG.COLOR_LAWN_DARK
                pygame.draw.rect(surf, color, rect)
        # grid lines
        for r in range(CFG.ROWS + 1):
            y = CFG.BOARD_TOP + r * CFG.TILE_H
            pygame.draw.line(surf, CFG.COLOR_GRID_LINES, (CFG.BOARD_LEFT, y), (CFG.BOARD_LEFT + CFG.COLS * CFG.TILE_W, y), 1)
        for c in range(CFG.COLS + 1):
            x = CFG.BOARD_LEFT + c * CFG.TILE_W
            pygame.draw.line(surf, CFG.COLOR_GRID_LINES, (x, CFG.BOARD_TOP), (x, CFG.BOARD_TOP + CFG.ROWS * CFG.TILE_H), 1)


# ---------------------------
# Seed Bank UI
# ---------------------------
@dataclass
class SeedCard:
    plant_cls: type
    key: str                    # hotkey label (e.g., '1')
    cost: int
    cooldown: float
    ready_in: float = 0.0       # seconds remaining
    selected: bool = False

    def rect(self, index: int) -> pygame.Rect:
        x = CFG.SEED_CARD_MARGIN + index * (CFG.SEED_CARD_W + CFG.SEED_CARD_MARGIN)
        y = (CFG.SEED_BANK_HEIGHT - CFG.SEED_CARD_H) // 2
        return pygame.Rect(x, y, CFG.SEED_CARD_W, CFG.SEED_CARD_H)

    def can_play(self, sun: int) -> bool:
        return self.ready_in <= 0 and sun >= self.cost

    def use(self):
        self.ready_in = self.cooldown

    def update(self, dt: float):
        if self.ready_in > 0:
            self.ready_in -= dt * CFG.FAST_FORWARD

    def draw(self, surf: pygame.Surface, index: int, font: pygame.font.Font):
        r = self.rect(index)
        # base
        pygame.draw.rect(surf, CFG.COLOR_UI, r, border_radius=8)
        pygame.draw.rect(surf, CFG.COLOR_UI_DARK, r, 2, border_radius=8)
        # name
        label = f"{self.key} {self.plant_cls.name}"
        txt = font.render(label, True, CFG.COLOR_TEXT)
        surf.blit(txt, (r.x + 8, r.y + 6))
        # cost
        cost_txt = font.render(f"${self.cost}", True, (100, 60, 10))
        surf.blit(cost_txt, (r.x + 8, r.bottom - 26))
        # cooldown overlay
        if self.ready_in > 0:
            pct = clamp(self.ready_in / self.cooldown, 0.0, 1.0)
            h = int(r.h * pct)
            overlay = pygame.Surface((r.w, h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 110))
            surf.blit(overlay, (r.x, r.y + (r.h - h)))
        # selected
        if self.selected:
            pygame.draw.rect(surf, CFG.COLOR_ACCENT, r.inflate(6, 6), 3, border_radius=10)


class SeedBank:
    def __init__(self, font: pygame.font.Font):
        self.font = font
        self.cards: List[SeedCard] = [
            SeedCard(PeaShooter, "1", PeaShooter.cost, PeaShooter.cooldown),
            SeedCard(SunFlower,  "2", SunFlower.cost,  SunFlower.cooldown),
            SeedCard(WallNut,    "3", WallNut.cost,    WallNut.cooldown),
        ]
        self.selected_index: Optional[int] = 0
        self.cards[0].selected = True

    def select(self, idx: Optional[int]):
        if self.selected_index is not None:
            self.cards[self.selected_index].selected = False
        self.selected_index = idx
        if idx is not None:
            self.cards[idx].selected = True

    def toggle_by_key(self, key: int):
        mapping = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2}
        if key in mapping:
            self.select(mapping[key])

    def update(self, dt: float):
        for c in self.cards:
            c.update(dt)

    def handle_click(self, pos: Tuple[int, int]) -> bool:
        """Returns True if the click was on a card (selection changed)."""
        for i, c in enumerate(self.cards):
            if c.rect(i).collidepoint(pos):
                self.select(i)
                return True
        return False

    def current_card(self) -> Optional[SeedCard]:
        if self.selected_index is None:
            return None
        return self.cards[self.selected_index]

    def draw(self, surf: pygame.Surface, sun: int):
        # seed bank background bar
        bar = pygame.Rect(0, 0, CFG.WIDTH, CFG.SEED_BANK_HEIGHT)
        pygame.draw.rect(surf, (255, 255, 255), bar)
        pygame.draw.line(surf, CFG.COLOR_UI_DARK, (0, CFG.SEED_BANK_HEIGHT), (CFG.WIDTH, CFG.SEED_BANK_HEIGHT), 2)

        for i, c in enumerate(self.cards):
            c.draw(surf, i, self.font)

        # sun counter
        sun_box = pygame.Rect(CFG.WIDTH - 220, 10, 210, CFG.SEED_CARD_H)
        pygame.draw.rect(surf, CFG.COLOR_UI, sun_box, border_radius=8)
        pygame.draw.rect(surf, CFG.COLOR_UI_DARK, sun_box, 2, border_radius=8)
        label = self.font.render("Sun", True, CFG.COLOR_TEXT)
        val = self.font.render(str(sun), True, CFG.COLOR_ACCENT)
        surf.blit(label, (sun_box.x + 8, sun_box.y + 8))
        surf.blit(val,   (sun_box.x + 8, sun_box.y + 34))


# ---------------------------
# Wave / Level Director
# ---------------------------
class LevelDirector:
    """Simple wave spawner that escalates difficulty and drives a progress bar."""
    def __init__(self, total_time: float = 120.0, waves: int = 3):
        self.total_time = total_time
        self.waves = waves
        self.elapsed = 0.0
        # Compute wave times (evenly spaced)
        self.wave_times = [ (i + 1) * (self.total_time / (self.waves + 1)) for i in range(self.waves) ]
        self.wave_index = 0
        self.done = False
        self.next_spawn_t = 2.5  # initial delay
        self.spawn_interval = (3.5, 6.5)

    def update(self, dt: float, zombies: List[Zombie]):
        if self.done:
            return
        dt *= CFG.FAST_FORWARD
        self.elapsed += dt

        # escalate spawn rate slowly
        a = clamp(self.elapsed / self.total_time, 0.0, 1.0)
        lo = lerp(self.spawn_interval[0], 2.2, a)
        hi = lerp(self.spawn_interval[1], 4.0, a)

        self.next_spawn_t -= dt
        if self.next_spawn_t <= 0:
            # normal spawn
            r = random.randrange(CFG.ROWS)
            zombies.append(Zombie(r))
            self.next_spawn_t = random.uniform(lo, hi)

        # wave burst
        if self.wave_index < len(self.wave_times) and self.elapsed >= self.wave_times[self.wave_index]:
            # spawn a burst of zombies in quick succession
            for _ in range(4 + self.wave_index):
                r = random.randrange(CFG.ROWS)
                z = Zombie(r)
                z.speed *= random.uniform(0.9, 1.15)
                z.max_hp = int(z.max_hp * random.uniform(1.0, 1.25))
                z.hp = z.max_hp
                zombies.append(z)
            self.wave_index += 1

        # mark done when elapsed passes total_time
        if self.elapsed >= self.total_time:
            self.done = True

    def progress(self) -> float:
        return clamp(self.elapsed / self.total_time, 0.0, 1.0)

    def draw_progress(self, surf: pygame.Surface, font: pygame.font.Font):
        bar = pygame.Rect(CFG.BOARD_LEFT, CFG.HEIGHT - 40, CFG.COLS * CFG.TILE_W, 18)
        pygame.draw.rect(surf, (240, 240, 240), bar, border_radius=6)
        pygame.draw.rect(surf, (180, 180, 180), bar, 2, border_radius=6)
        p = self.progress()
        fill = pygame.Rect(bar.x + 2, bar.y + 2, int((bar.w - 4) * p), bar.h - 4)
        pygame.draw.rect(surf, (60, 160, 220), fill, border_radius=4)
        txt = font.render("Wave Progress", True, CFG.COLOR_TEXT)
        surf.blit(txt, (bar.x, bar.y - 22))


# ---------------------------
# Game
# ---------------------------
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(CFG.CAPTION)
        self.screen = pygame.display.set_mode((CFG.WIDTH, CFG.HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(CFG.FONT_NAME, 20)
        self.bigfont = pygame.font.SysFont(CFG.FONT_NAME, 36)

        self.running = True
        self.paused = False
        self.game_over = False
        self.win = False

        # Systems
        self.grid = Grid()
        self.seedbank = SeedBank(self.font)
        self.director = LevelDirector(total_time=120.0, waves=3)

        # Entities
        self.plants: List[Plant] = []
        self.zombies: List[Zombie] = []
        self.projectiles: List[Pea] = []
        self.suns: List[Sun] = []
        self.mowers: List[LawnMower] = [LawnMower(r) for r in range(CFG.ROWS)]

        # Economy
        self.sun = CFG.STARTING_SUN
        self.sky_sun_cd = random.uniform(*CFG.SKY_SUN_INTERVAL)

        # Input state
        self.shovel_mode = False  # right-click toggles shovel to remove plants

    # --------------- Event Handling ---------------
    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    self.paused = not self.paused
                elif e.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                    self.seedbank.toggle_by_key(e.key)
                elif e.key == pygame.K_SPACE:
                    # dev: toggle fast-forward quickly during playtests
                    CFG.FAST_FORWARD = 1.0 if CFG.FAST_FORWARD != 1.0 else 2.0
                elif e.key == pygame.K_BACKQUOTE:  # ` toggles shovel
                    self.shovel_mode = not self.shovel_mode
            elif e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 1:
                    self.on_left_click(e.pos)
                elif e.button == 3:
                    self.shovel_mode = not self.shovel_mode

    def on_left_click(self, pos: Tuple[int, int]):
        # click sun?
        for s in self.suns:
            if s.alive and s.click(pos):
                self.sun += s.value
                return

        # click seed card?
        if pos[1] <= CFG.SEED_BANK_HEIGHT:
            if self.seedbank.handle_click(pos):
                return

        # place or shovel on lawn
        cell = pos_to_cell(*pos)
        if cell is None:
            return
        r, c = cell

        if self.shovel_mode:
            p = self.grid.get(r, c)
            if p:
                p.alive = False
                self.grid.set(r, c, None)
            return

        card = self.seedbank.current_card()
        if not card:
            return
        if not card.can_play(self.sun):
            return
        if not self.grid.empty(r, c):
            return

        # place plant
        plant = card.plant_cls(r, c)
        self.plants.append(plant)
        self.grid.set(r, c, plant)
        self.sun -= card.cost
        card.use()

    # --------------- Updates ---------------
    def update(self, dt: float):
        if self.paused or self.game_over:
            return

        # director spawns zombies
        self.director.update(dt, self.zombies)

        # sky suns
        self.sky_sun_cd -= dt * CFG.FAST_FORWARD
        if self.sky_sun_cd <= 0:
            cx = random.randint(CFG.BOARD_LEFT, CFG.BOARD_LEFT + CFG.COLS * CFG.TILE_W - 1)
            fall_to = random.randint(CFG.BOARD_TOP + 40, CFG.BOARD_TOP + CFG.ROWS * CFG.TILE_H - 40)
            self.suns.append(Sun((cx, CFG.BOARD_TOP - 30), fall_to))
            self.sky_sun_cd = random.uniform(*CFG.SKY_SUN_INTERVAL)

        # seedbank
        self.seedbank.update(dt)

        # plants
        for p in self.plants:
            if isinstance(p, PeaShooter):
                p.update(dt, self.projectiles, self.zombies)
            elif isinstance(p, SunFlower):
                p.update(dt, self.suns)
            # WallNut has no active behavior

        # projectiles
        for pea in self.projectiles:
            pea.update(dt)

        # projectile-zombie collisions
        for pea in list(self.projectiles):
            if not pea.alive: 
                continue
            for z in self.zombies:
                if z.alive and z.r is not None and abs((CFG.BOARD_TOP + z.r * CFG.TILE_H + CFG.TILE_H // 2) - pea.y) < CFG.TILE_H // 2:
                    if pea.rect.colliderect(z.rect):
                        z.hurt(pea.dmg)
                        pea.alive = False
                        break

        # zombies
        for z in self.zombies:
            z.update(dt, self.grid, self.plants)
            # check for crossing left boundary -> trigger mower or game over
            if z.alive and z.x < CFG.BOARD_LEFT - 20:
                # find mower for row
                mower = next((m for m in self.mowers if m.alive and m.r == z.r), None)
                if mower and not mower.active:
                    mower.trigger()
                else:
                    self.game_over = True
                    self.win = False

        # mowers
        for m in self.mowers:
            m.update(dt, self.zombies)

        # suns
        for s in self.suns:
            s.update(dt)

        # cleanup
        self.projectiles = [b for b in self.projectiles if b.alive]
        self.zombies = [z for z in self.zombies if z.alive]
        self.suns = [s for s in self.suns if s.alive]
        self.mowers = [m for m in self.mowers if m.alive]
        self.grid.remove_dead()

        # win condition: director done and no zombies remaining
        if self.director.done and len(self.zombies) == 0:
            self.game_over = True
            self.win = True

    # --------------- Rendering ---------------
    def draw_background(self, surf: pygame.Surface):
        # sky gradient
        grad = pygame.Surface((CFG.WIDTH, CFG.HEIGHT))
        for y in range(CFG.HEIGHT):
            t = y / CFG.HEIGHT
            r = int(lerp(CFG.COLOR_BG_TOP[0], CFG.COLOR_BG_BOTTOM[0], t))
            g = int(lerp(CFG.COLOR_BG_TOP[1], CFG.COLOR_BG_BOTTOM[1], t))
            b = int(lerp(CFG.COLOR_BG_TOP[2], CFG.COLOR_BG_BOTTOM[2], t))
            pygame.draw.line(grad, (r, g, b), (0, y), (CFG.WIDTH, y))
        surf.blit(grad, (0, 0))

        # lawn
        self.grid.draw_lawn(surf)

    def draw_entities(self, surf: pygame.Surface):
        # Draw by lanes for simple painter's order: plants -> zombies -> projectiles overlay
        # Plants and zombies are lane-bound; projectiles can be drawn after.
        for r in range(CFG.ROWS):
            # plants in this row
            for p in self.plants:
                if p.r == r and p.alive:
                    p.draw(surf)
            # zombies in this row
            for z in self.zombies:
                if z.r == r and z.alive:
                    z.draw(surf)

        # projectiles
        for pea in self.projectiles:
            if pea.alive:
                pea.draw(surf)

        # suns
        for s in self.suns:
            s.draw(surf)

        # mowers on top
        for m in self.mowers:
            m.draw(surf)

    def draw_ui(self, surf: pygame.Surface):
        self.seedbank.draw(surf, self.sun)
        # wave progress
        self.director.draw_progress(surf, self.font)

        if self.paused:
            self.draw_overlay_message(surf, "PAUSED — press ESC to resume")
        if self.game_over:
            msg = "YOU WIN! 🌻" if self.win else "ZOMBIES ATE YOUR BRAINS! 🧠"
            self.draw_overlay_message(surf, msg)

        # shovel status
        shovel_txt = self.font.render(f"Shovel [{'ON' if self.shovel_mode else 'off'}] (` or Right Click)", True, CFG.COLOR_TEXT)
        surf.blit(shovel_txt, (10, CFG.HEIGHT - 28))

        # controls hint
        hint = self.font.render("Hotkeys: [1]=PeaShooter [2]=Sunflower [3]=Wall-Nut | ESC pause | SPACE x2 speed", True, CFG.COLOR_TEXT)
        surf.blit(hint, (10, CFG.HEIGHT - 54))

    def draw_overlay_message(self, surf: pygame.Surface, text: str):
        overlay = pygame.Surface((CFG.WIDTH, CFG.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surf.blit(overlay, (0, 0))
        box = pygame.Rect(0, 0, CFG.WIDTH // 2 + 80, 140)
        box.center = (CFG.WIDTH // 2, CFG.HEIGHT // 2)
        pygame.draw.rect(surf, (255, 255, 255), box, border_radius=12)
        pygame.draw.rect(surf, (180, 180, 180), box, 2, border_radius=12)
        txt = self.bigfont.render(text, True, CFG.COLOR_TEXT)
        surf.blit(txt, txt.get_rect(center=box.center))

    # --------------- Main Loop ---------------
    def run(self):
        while self.running:
            dt_ms = self.clock.tick(CFG.FPS)  # cap at 60 fps
            dt = min(dt_ms / 1000.0, 0.05)    # clamp dt for stability
            self.handle_events()
            self.update(dt)

            self.draw_background(self.screen)
            self.draw_entities(self.screen)
            self.draw_ui(self.screen)

            pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    try:
        Game().run()
    except KeyboardInterrupt:
        pygame.quit()
        sys.exit(0)
