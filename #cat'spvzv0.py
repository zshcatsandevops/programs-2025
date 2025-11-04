#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ultra!pvz 0.x — menu + almanac prototype (single file)
#
# Copyright (c) 2025
# Author: You + ChatGPT (original code)
#
# License: GNU GPL v3 or later
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# DISCLAIMER
# ----------
# This is an original prototype inspired by general lane-defense mechanics.
# It contains NO copyrighted Plants vs. Zombies assets or content. All visuals
# are simple shapes; all names are generic. If you distribute this, please keep
# it originally branded and use your own assets. No affiliation with PopCap/EA.

import math
import random
import sys
from dataclasses import dataclass
import pygame

# -----------------------------------------------------------------------------
# Configuration & Constants
# -----------------------------------------------------------------------------

VERSION = "0.x"
TITLE = "ultra!pvz " + VERSION
FPS = 60

GRID_ROWS = 5
GRID_COLS = 9
CELL_SIZE = 86
GRID_MARGIN_X = 36
UI_BAR_H = 120
GRID_MARGIN_Y = UI_BAR_H + 20

SCREEN_W = GRID_MARGIN_X * 2 + GRID_COLS * CELL_SIZE
SCREEN_H = GRID_MARGIN_Y + GRID_ROWS * CELL_SIZE + 24

# Economy
STARTING_SUN = 50
PASSIVE_SUN_PER_SEC = 3        # tiny trickle to keep games moving
SKY_SUN_SPAWN_EVERY = (7.5, 11.0)  # random seconds between sky orbs
SKY_SUN_VALUE = 25
SUN_ORB_LIFETIME = 7.5
SUN_ORB_FALL_SPEED = 70

# Wave / Enemies
LEVEL_TOTAL_ZOMBIES = 18
SPAWN_INTERVAL_START = 5.0
SPAWN_INTERVAL_MIN = 2.1
SPAWN_ACCEL_EVERY = 20.0       # lower interval every X seconds
SPAWN_ACCEL_STEP = 0.4

ZOMBIE_BASE_HP = 220
ZOMBIE_SPEED = 22              # px/s
ZOMBIE_DPS = 10                # damage/s vs plants
ZOMBIE_SIZE = (50, 68)         # w, h

# Plants & projectiles
@dataclass
class PlantStats:
    name: str
    cost: int
    max_hp: int
    cooldown: float
    color: tuple
    # Shooter specifics
    shoots: bool = False
    fire_rate: float = 0.0               # pellets per second
    pellet_damage: int = 0
    pellet_speed: float = 0.0
    # Generator specifics
    generates: bool = False
    gen_interval: float = 0.0
    gen_amount: int = 0
    # Blocker specifics
    is_blocker: bool = False

PLANTS = {
    "shooter": PlantStats(
        name="Shooter",
        cost=100, max_hp=200, cooldown=4.0, color=(90, 200, 90),
        shoots=True, fire_rate=0.7, pellet_damage=25, pellet_speed=320
    ),
    "generator": PlantStats(
        name="Generator",
        cost=50, max_hp=140, cooldown=6.0, color=(250, 210, 70),
        generates=True, gen_interval=7.0, gen_amount=25
    ),
    "blocker": PlantStats(
        name="Blocker",
        cost=50, max_hp=650, cooldown=7.0, color=(140, 120, 85),
        is_blocker=True
    ),
}

PLANT_ORDER = ["shooter", "generator", "blocker"]  # UI card order
PELLET_RADIUS = 6

# Colors
BG = (22, 28, 36)
GRASS_A = (60, 130, 80)
GRASS_B = (56, 122, 76)
GRID_LINE = (35, 90, 60)
UI_BG = (32, 40, 50)
CARD_OUTLINE = (200, 200, 210)
CARD_DIM = (120, 120, 130)
TEXT = (240, 240, 248)
TEXT_DIM = (200, 200, 210)
WARNING = (255, 88, 88)
GOLD = (255, 229, 112)
PROGRESS_BG = (45, 55, 68)
PROGRESS_BAR = (98, 180, 255)
PAUSE_TINT = (0, 0, 0, 120)
BTN_BG = (40, 48, 60)
BTN_BG_HOVER = (64, 78, 98)
BTN_OUTLINE = (210, 210, 220)
TAB_BG = (42, 52, 64)
TAB_ACTIVE = (78, 100, 128)

# Shovel refund
SHOVEL_REFUND_RATIO = 0.35

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def grid_cell_rect(row, col):
    x = GRID_MARGIN_X + col * CELL_SIZE
    y = GRID_MARGIN_Y + row * CELL_SIZE
    return pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

def grid_from_pos(pos):
    x, y = pos
    if y < GRID_MARGIN_Y or x < GRID_MARGIN_X:
        return None
    col = (x - GRID_MARGIN_X) // CELL_SIZE
    row = (y - GRID_MARGIN_Y) // CELL_SIZE
    if 0 <= row < GRID_ROWS and 0 <= col < GRID_COLS:
        return int(row), int(col)
    return None

# -----------------------------------------------------------------------------
# Almanac data for zombies (simple shapes; generic names)
# -----------------------------------------------------------------------------
@dataclass
class ZombieInfo:
    key: str
    name: str
    base_hp: int
    speed: float
    dps: float
    color_idle: tuple
    color_gnaw: tuple
    blurb: str

ZOMBIES_INFO = [
    ZombieInfo(
        key="walker",
        name="Walker",
        base_hp=ZOMBIE_BASE_HP,
        speed=ZOMBIE_SPEED,
        dps=ZOMBIE_DPS,
        color_idle=(180, 140, 140),
        color_gnaw=(160, 120, 120),
        blurb="A basic shambling foe. Moves steadily, chews through plants at a modest rate."
    ),
]

# -----------------------------------------------------------------------------
# Entities
# -----------------------------------------------------------------------------

class Pellet:
    __slots__ = ("row", "x", "y", "speed", "damage", "alive")

    def __init__(self, row, x, y, damage, speed):
        self.row = row
        self.x = x
        self.y = y
        self.speed = speed
        self.damage = damage
        self.alive = True

    def update(self, dt):
        self.x += self.speed * dt
        if self.x > SCREEN_W + 40:
            self.alive = False

    def rect(self):
        r = PELLET_RADIUS
        return pygame.Rect(int(self.x - r), int(self.y - r), r * 2, r * 2)


class SunOrb:
    __slots__ = ("x", "y", "target_y", "value", "vy", "life", "alive")

    def __init__(self, x, target_y, value=SKY_SUN_VALUE):
        self.x = x
        self.y = -20
        self.target_y = target_y
        self.value = value
        self.vy = 0
        self.life = SUN_ORB_LIFETIME
        self.alive = True

    def update(self, dt):
        # Fall until target_y, then idle on the turf
        if self.y < self.target_y:
            self.vy = clamp(self.vy + 300 * dt, 0, SUN_ORB_FALL_SPEED)
            self.y += self.vy * dt
            if self.y >= self.target_y:
                self.y = self.target_y
                self.vy = 0
        else:
            self.life -= dt
            if self.life <= 0:
                self.alive = False

    def rect(self):
        return pygame.Rect(int(self.x - 16), int(self.y - 16), 32, 32)

    def draw(self, surf):
        pygame.draw.circle(surf, GOLD, (int(self.x), int(self.y)), 16)
        pygame.draw.circle(surf, (255, 205, 60), (int(self.x), int(self.y)), 16, 3)


class Plant:
    __slots__ = ("row", "col", "stats", "hp", "cool", "fire_cd", "gen_cd")

    def __init__(self, row, col, stats: PlantStats):
        self.row = row
        self.col = col
        self.stats = stats
        self.hp = stats.max_hp
        self.cool = 0.0        # entity-local
        self.fire_cd = 0.0     # for shooters
        self.gen_cd = 0.0      # for generators

    def rect(self):
        return grid_cell_rect(self.row, self.col).inflate(-24, -18)

    def midright(self):
        r = self.rect()
        return (r.right - 2, r.centery)

    def update(self, dt, pellets, sun_orbs, rng):
        if self.stats.shoots:
            self.fire_cd -= dt
            if self.fire_cd <= 0.0:
                self.fire_cd = max(0.01, 1.0 / self.stats.fire_rate)
                x, y = self.midright()
                pellets.append(Pellet(self.row, x, y, self.stats.pellet_damage, self.stats.pellet_speed))
        if self.stats.generates:
            self.gen_cd -= dt
            if self.gen_cd <= 0.0:
                self.gen_cd = self.stats.gen_interval
                r = self.rect()
                sx = rng.uniform(r.left + 16, r.right - 16)
                sy = r.top + rng.uniform(6, 18)
                orb = SunOrb(sx, r.bottom - 12, value=self.stats.gen_amount)
                orb.y = sy
                sun_orbs.append(orb)

    def damage(self, amount):
        self.hp -= amount
        return self.hp <= 0


class Zombie:
    __slots__ = ("row", "x", "y", "w", "h", "hp", "speed", "dps", "gnawing", "alive")

    def __init__(self, row, hp=ZOMBIE_BASE_HP, speed=ZOMBIE_SPEED, dps=ZOMBIE_DPS):
        self.row = row
        self.w, self.h = ZOMBIE_SIZE
        self.x = SCREEN_W + 40
        self.y = GRID_MARGIN_Y + row * CELL_SIZE + (CELL_SIZE - self.h) // 2
        self.hp = hp
        self.speed = speed
        self.dps = dps
        self.gnawing = False
        self.alive = True

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def update(self, dt, plants_row):
        if not self.gnawing:
            self.x -= self.speed * dt
        collided = None
        zr = self.rect()
        for p in plants_row:
            if zr.colliderect(p.rect()):
                collided = p
                break
        if collided:
            self.gnawing = True
            dead = collided.damage(self.dps * dt)
            if dead:
                plants_row.remove(collided)
                self.gnawing = False
        else:
            self.gnawing = False
        if self.x < -self.w - 8:
            self.alive = False

    def hit(self, damage):
        self.hp -= damage
        if self.hp <= 0:
            self.alive = False

# -----------------------------------------------------------------------------
# Simple UI helpers (buttons)
# -----------------------------------------------------------------------------
class UIButton:
    __slots__ = ("rect", "label", "hotkey", "action")

    def __init__(self, rect, label, action, hotkey=None):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.action = action
        self.hotkey = hotkey

    def draw(self, surf, font, hover=False):
        pygame.draw.rect(surf, BTN_BG_HOVER if hover else BTN_BG, self.rect, border_radius=12)
        pygame.draw.rect(surf, BTN_OUTLINE, self.rect, 2, border_radius=12)
        txt = font.render(self.label, True, TEXT)
        surf.blit(txt, (self.rect.centerx - txt.get_width() // 2,
                        self.rect.centery - txt.get_height() // 2))

    def contains(self, pos):
        return self.rect.collidepoint(pos)

# -----------------------------------------------------------------------------
# Game
# -----------------------------------------------------------------------------

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 26)
        self.font_small = pygame.font.SysFont(None, 20)
        self.font_big = pygame.font.SysFont(None, 48)
        self.font_huge = pygame.font.SysFont(None, 64)
        self.rng = random.Random()

        # Scene: "menu" | "almanac" | "playing"
        self.mode = "menu"

        # Game state (only meaningful when mode == "playing"):
        self.paused = False
        self.state = "playing"   # "playing" | "victory" | "defeat"

        # Almanac UI state
        self.almanac_tab = "plants"  # or "zombies"
        self.almanac_idx = 0
        self.almanac_item_rects = []  # rebuilt each draw

        # Menu buttons
        btn_w, btn_h = 240, 64
        btn_x = SCREEN_W // 2 - btn_w // 2
        btn_y = SCREEN_H // 2 - 40
        self.menu_buttons = [
            UIButton((btn_x, btn_y - 80, btn_w, btn_h), "Play", action="play"),
            UIButton((btn_x, btn_y + 0,  btn_w, btn_h), "Almanac", action="almanac"),
            UIButton((btn_x, btn_y + 80, btn_w, btn_h), "Quit", action="quit"),
        ]

        self.reset_game()   # prepare a run (will be used when starting Play)
        self.mode = "menu"  # land in main menu

    # -----------------------------------
    # Core loop
    # -----------------------------------
    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            if not self.handle_events():
                break
            self.update(dt)
            self.draw()
        pygame.quit()

    # -----------------------------------
    # Scene transitions
    # -----------------------------------
    def start_play(self):
        self.reset_game()
        self.mode = "playing"
        self.state = "playing"
        self.paused = False

    def open_almanac(self):
        self.mode = "almanac"
        self.almanac_tab = "plants"
        self.almanac_idx = 0

    def back_to_menu(self):
        self.mode = "menu"

    # -----------------------------------
    # Event handling
    # -----------------------------------
    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return False  # Quit everywhere (as original)
                if self.mode == "playing":
                    if e.key == pygame.K_r:
                        self.reset_game()
                    elif e.key == pygame.K_p and self.state == "playing":
                        self.paused = not self.paused
                elif self.mode == "menu":
                    if e.key == pygame.K_RETURN:
                        self.start_play()
                elif self.mode == "almanac":
                    if e.key == pygame.K_TAB:
                        self.almanac_tab = "zombies" if self.almanac_tab == "plants" else "plants"
                        self.almanac_idx = 0
            elif e.type == pygame.MOUSEBUTTONDOWN:
                if self.mode == "menu":
                    self.on_menu_click(e)
                elif self.mode == "almanac":
                    self.on_almanac_click(e)
                elif self.mode == "playing":
                    if self.state != "playing":
                        # Any click during end screen: restart current run
                        self.reset_game()
                        continue
                    if e.button == 1:
                        self.on_left_click(e.pos)
                    elif e.button == 3:
                        self.on_right_click(e.pos)
        return True

    # -----------------------------------
    # Menu interactions
    # -----------------------------------
    def on_menu_click(self, e):
        if e.button != 1:
            return
        for b in self.menu_buttons:
            if b.contains(e.pos):
                if b.action == "play":
                    self.start_play()
                elif b.action == "almanac":
                    self.open_almanac()
                elif b.action == "quit":
                    pygame.event.post(pygame.event.Event(pygame.QUIT))

    # -----------------------------------
    # Almanac interactions
    # -----------------------------------
    def current_almanac_entries(self):
        if self.almanac_tab == "plants":
            # Build from PLANTS dict in the same order as cards
            entries = []
            for k in PLANT_ORDER:
                s = PLANTS[k]
                entries.append({
                    "key": k,
                    "title": s.name,
                    "subtitle": f"Cost {s.cost} | HP {s.max_hp}",
                    "stats": s,
                    "type": "plant",
                })
            return entries
        else:
            entries = []
            for z in ZOMBIES_INFO:
                entries.append({
                    "key": z.key,
                    "title": z.name,
                    "subtitle": f"HP {z.base_hp} | Speed {int(z.speed)} | DPS {int(z.dps)}",
                    "stats": z,
                    "type": "zombie",
                })
            return entries

    def on_almanac_click(self, e):
        if e.button != 1:
            return
        # Back button
        back_rect = pygame.Rect(20, 16, 120, 42)
        if back_rect.collidepoint(e.pos):
            self.back_to_menu()
            return
        # Tabs
        tab_plants = pygame.Rect(160, 16, 140, 42)
        tab_zombies = pygame.Rect(160 + 146, 16, 160, 42)
        if tab_plants.collidepoint(e.pos):
            self.almanac_tab = "plants"; self.almanac_idx = 0; return
        if tab_zombies.collidepoint(e.pos):
            self.almanac_tab = "zombies"; self.almanac_idx = 0; return
        # List items
        for idx, r in enumerate(self.almanac_item_rects):
            if r.collidepoint(e.pos):
                self.almanac_idx = idx
                return

    # -----------------------------------
    # Interactions (gameplay)
    # -----------------------------------
    def on_left_click(self, pos):
        # Click sun orbs first
        for orb in reversed(self.suns):
            if orb.rect().collidepoint(pos):
                self.sun += orb.value
                orb.alive = False
                return

        # Click a card?
        for card in self.cards:
            if card["rect"].collidepoint(pos):
                stats = card["stats"]
                if card["cd"] <= 0 and self.sun >= stats.cost:
                    self.selected_card = card
                else:
                    self.selected_card = None
                return

        # Place a plant?
        cell = grid_from_pos(pos)
        if self.selected_card and cell:
            r, c = cell
            if self.grid[r][c] is None:
                stats = self.selected_card["stats"]
                if self.sun >= stats.cost and self.selected_card["cd"] <= 0:
                    plant = Plant(r, c, stats)
                    self.grid[r][c] = plant
                    self.plants[r].append(plant)
                    self.sun -= stats.cost
                    self.selected_card["cd"] = stats.cooldown
                    self.selected_card = None

    def on_right_click(self, pos):
        # shovel: remove plant (partial refund)
        cell = grid_from_pos(pos)
        if not cell:
            return
        r, c = cell
        plant = self.grid[r][c]
        if plant:
            self.grid[r][c] = None
            self.plants[r].remove(plant)
            refund = int(PLANTS[self.kind_of(plant)].cost * SHOVEL_REFUND_RATIO)
            self.sun += refund

    def kind_of(self, plant):
        # find the key by identity of stats
        for k, v in PLANTS.items():
            if v is plant.stats:
                return k
        return "unknown"

    # -----------------------------------
    # State resets (gameplay)
    # -----------------------------------
    def reset_game(self):
        # Core run variables
        self.sun = STARTING_SUN
        self.time = 0.0
        self.paused = False
        self.state = "playing"   # "playing" | "victory" | "defeat"

        # Board
        self.grid = [[None for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        self.plants = [[] for _ in range(GRID_ROWS)]
        self.zombies = [[] for _ in range(GRID_ROWS)]
        self.pellets = []
        self.suns = []

        # Cards UI
        self.cards = self.make_cards()
        self.selected_card = None

        # Spawn control
        self.spawn_timer = SPAWN_INTERVAL_START
        self.spawn_interval = SPAWN_INTERVAL_START
        self.spawn_elapsed = 0.0
        self.spawned = 0

        # Sky sun control
        self.sky_timer = self.rng.uniform(*SKY_SUN_SPAWN_EVERY)

        # Progress
        self.progress = 0.0  # 0..1

    def make_cards(self):
        cards = []
        x = 20
        y = 12
        w = 160
        h = 96
        gap = 14
        for kind in PLANT_ORDER:
            stats = PLANTS[kind]
            rect = pygame.Rect(x, y + 8, w, h)
            cards.append({
                "kind": kind,
                "stats": stats,
                "rect": rect,
                "cd": 0.0,  # cooldown timer
            })
            x += w + gap
        return cards

    # -----------------------------------
    # Update
    # -----------------------------------
    def update(self, dt):
        # Only gameplay requires heavy updates
        if self.mode != "playing":
            return
        if self.state != "playing" or self.paused:
            return

        self.time += dt

        # Passive sun
        self.sun += PASSIVE_SUN_PER_SEC * dt

        # Update card cooldowns
        for card in self.cards:
            if card["cd"] > 0:
                card["cd"] -= dt

        # Sky sun spawning
        self.sky_timer -= dt
        if self.sky_timer <= 0:
            self.sky_timer = self.rng.uniform(*SKY_SUN_SPAWN_EVERY)
            x = self.rng.uniform(GRID_MARGIN_X + 18, SCREEN_W - GRID_MARGIN_X - 18)
            row = self.rng.randrange(GRID_ROWS)
            target_y = GRID_MARGIN_Y + row * CELL_SIZE + self.rng.uniform(10, CELL_SIZE - 10)
            self.suns.append(SunOrb(x, target_y, SKY_SUN_VALUE))

        # Plants update
        for row_plants in self.plants:
            for p in row_plants:
                p.update(dt, self.pellets, self.suns, self.rng)

        # Pellets update & collisions
        for pel in self.pellets:
            pel.update(dt)
        for pel in self.pellets:
            if not pel.alive:
                continue
            row_z = self.zombies[pel.row]
            for z in row_z:
                if not z.alive:
                    continue
                if pel.rect().colliderect(z.rect()):
                    z.hit(pel.damage)
                    pel.alive = False
                    break
            self.zombies[pel.row] = [z for z in row_z if z.alive]
        self.pellets = [p for p in self.pellets if p.alive]

        # Sun orbs update
        for s in self.suns:
            s.update(dt)
        self.suns = [s for s in self.suns if s.alive]

        # Spawn zombies over time
        if self.spawned < LEVEL_TOTAL_ZOMBIES:
            self.spawn_timer -= dt
            self.spawn_elapsed += dt
            if self.spawn_timer <= 0:
                self.spawn_timer = self.spawn_interval
                row = self.rng.randrange(GRID_ROWS)
                self.zombies[row].append(Zombie(row))
                self.spawned += 1
            if self.spawn_elapsed >= SPAWN_ACCEL_EVERY:
                self.spawn_elapsed = 0.0
                self.spawn_interval = max(SPAWN_INTERVAL_MIN, self.spawn_interval - SPAWN_ACCEL_STEP)

        # Zombies update
        lost = False
        for r in range(GRID_ROWS):
            row_z = self.zombies[r]
            if row_z:
                for z in row_z:
                    z.update(dt, self.plants[r])
                    if z.x <= GRID_MARGIN_X - 18:  # house line
                        lost = True
                self.zombies[r] = [z for z in row_z if z.alive]
            # purge dead plants
            self.plants[r] = [p for p in self.plants[r] if p.hp > 0]
            for c in range(GRID_COLS):
                if self.grid[r][c] and self.grid[r][c].hp <= 0:
                    self.grid[r][c] = None

        if lost:
            self.state = "defeat"

        # Victory condition: all zombies spawned and none left on board
        total_on_board = sum(len(zr) for zr in self.zombies)
        if self.spawned >= LEVEL_TOTAL_ZOMBIES and total_on_board == 0:
            self.state = "victory"

        # Progress bar
        self.progress = clamp(self.spawned / LEVEL_TOTAL_ZOMBIES, 0.0, 1.0)

    # -----------------------------------
    # Draw routines
    # -----------------------------------
    def draw(self):
        if self.mode == "menu":
            self.draw_menu()
        elif self.mode == "almanac":
            self.draw_almanac()
        else:
            self.draw_game()
        pygame.display.flip()

    def draw_menu(self):
        self.screen.fill(BG)
        # Decorative gradient stripes
        for i in range(8):
            y = 120 + i * 18
            pygame.draw.rect(self.screen, (30 + i*2, 40 + i*3, 54 + i*4), (0, y, SCREEN_W, 12))
        # Title
        title = self.font_huge.render(TITLE, True, TEXT)
        self.screen.blit(title, (SCREEN_W//2 - title.get_width()//2, 54))
        # Subtitle
        sub = self.font_small.render("Original shapes • Generic names • GPL-3.0-or-later", True, TEXT_DIM)
        self.screen.blit(sub, (SCREEN_W//2 - sub.get_width()//2, 54 + title.get_height() + 8))
        # Buttons
        mx, my = pygame.mouse.get_pos()
        for b in self.menu_buttons:
            b.draw(self.screen, self.font_big, hover=b.contains((mx, my)))
        # Footer tips
        tips = "Play: Start a run  •  Almanac: Browse units  •  ESC: Quit"
        tips_s = self.font_small.render(tips, True, TEXT_DIM)
        self.screen.blit(tips_s, (SCREEN_W//2 - tips_s.get_width()//2, SCREEN_H - 36))

    def draw_almanac(self):
        self.screen.fill(BG)
        # Header bar
        pygame.draw.rect(self.screen, UI_BG, (0, 0, SCREEN_W, 78))
        # Back button
        back = pygame.Rect(20, 16, 120, 42)
        self.draw_button(back, "Back", small=True)
        # Tabs
        tab_plants = pygame.Rect(160, 16, 140, 42)
        tab_zombies = pygame.Rect(160 + 146, 16, 160, 42)
        self.draw_tab(tab_plants, "Plants", self.almanac_tab == "plants")
        self.draw_tab(tab_zombies, "Zombies", self.almanac_tab == "zombies")

        # Body split
        list_w = 320
        list_rect = pygame.Rect(20, 92, list_w, SCREEN_H - 112)
        detail_rect = pygame.Rect(20 + list_w + 16, 92, SCREEN_W - (20 + list_w + 16) - 20, SCREEN_H - 112)

        # List panel
        pygame.draw.rect(self.screen, (28, 36, 46), list_rect, border_radius=10)
        pygame.draw.rect(self.screen, (58, 76, 90), list_rect, 2, border_radius=10)

        entries = self.current_almanac_entries()
        self.almanac_item_rects = []
        iy = list_rect.y + 14
        for i, ent in enumerate(entries):
            r = pygame.Rect(list_rect.x + 12, iy, list_rect.w - 24, 58)
            self.almanac_item_rects.append(r)
            hovered = r.collidepoint(pygame.mouse.get_pos())
            selected = (i == self.almanac_idx)
            self.draw_list_item(r, ent["title"], ent["subtitle"], hovered or selected, selected)
            iy += 62

        # Detail panel
        pygame.draw.rect(self.screen, (28, 36, 46), detail_rect, border_radius=10)
        pygame.draw.rect(self.screen, (58, 76, 90), detail_rect, 2, border_radius=10)

        if entries:
            ent = entries[self.almanac_idx]
            self.draw_detail_panel(detail_rect, ent)

    def draw_list_item(self, rect, title, subtitle, hover, selected):
        base = (44, 56, 72)
        hl = (64, 84, 108)
        pygame.draw.rect(self.screen, hl if (hover or selected) else base, rect, border_radius=8)
        pygame.draw.rect(self.screen, (80, 100, 124), rect, 1, border_radius=8)
        t = self.font.render(title, True, TEXT)
        s = self.font_small.render(subtitle, True, TEXT_DIM)
        self.screen.blit(t, (rect.x + 12, rect.y + 8))
        self.screen.blit(s, (rect.x + 12, rect.y + 30))

    def draw_button(self, rect, label, small=False):
        pygame.draw.rect(self.screen, BTN_BG, rect, border_radius=10)
        pygame.draw.rect(self.screen, BTN_OUTLINE, rect, 2, border_radius=10)
        ft = self.font_small if small else self.font
        txt = ft.render(label, True, TEXT)
        self.screen.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))

    def draw_tab(self, rect, label, active):
        pygame.draw.rect(self.screen, TAB_ACTIVE if active else TAB_BG, rect, border_radius=10)
        pygame.draw.rect(self.screen, BTN_OUTLINE, rect, 2, border_radius=10)
        txt = self.font.render(label, True, TEXT if active else TEXT_DIM)
        self.screen.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))

    def draw_detail_panel(self, rect, ent):
        pad = 16
        title = self.font_big.render(ent["title"], True, TEXT)
        self.screen.blit(title, (rect.x + pad, rect.y + pad))

        # Divider
        y = rect.y + pad + title.get_height() + 8
        pygame.draw.line(self.screen, (70, 86, 104), (rect.x + pad, y), (rect.right - pad, y), 2)
        y += 12

        if ent["type"] == "plant":
            s: PlantStats = ent["stats"]
            lines = [
                f"Type: {'Shooter' if s.shoots else 'Generator' if s.generates else 'Blocker'}",
                f"Cost: {s.cost}",
                f"Max HP: {s.max_hp}",
            ]
            if s.shoots:
                lines += [f"Fire Rate: {s.fire_rate:.2f}/s", f"Projectile: {s.pellet_damage} dmg, {int(s.pellet_speed)} px/s"]
            if s.generates:
                lines += [f"Generates: +{s.gen_amount} sun every {s.gen_interval:.1f}s"]
            if s.is_blocker:
                lines += ["Role: High-HP blocker"]

            # Icon
            icon = pygame.Rect(rect.right - 200, rect.y + pad + 8, 160, 120)
            pygame.draw.rect(self.screen, (40, 46, 58), icon, border_radius=10)
            self.draw_plant_icon(icon, s)

            # Text
            for line in lines:
                txt = self.font.render(line, True, TEXT)
                self.screen.blit(txt, (rect.x + pad, y))
                y += txt.get_height() + 6

            blurb = "A reliable, generic plant. Original art; shape-based only."
            bl = self.wrap_text(blurb, rect.w - 220 - pad*2, self.font_small)
            y += 6
            for seg in bl:
                tip = self.font_small.render(seg, True, TEXT_DIM)
                self.screen.blit(tip, (rect.x + pad, y))
                y += tip.get_height() + 2

        else:
            z: ZombieInfo = ent["stats"]
            lines = [
                f"HP: {z.base_hp}",
                f"Speed: {int(z.speed)} px/s",
                f"DPS vs plants: {int(z.dps)}",
            ]
            # Icon
            icon = pygame.Rect(rect.right - 200, rect.y + pad + 8, 160, 120)
            pygame.draw.rect(self.screen, (40, 46, 58), icon, border_radius=10)
            self.draw_zombie_icon(icon, z)

            # Text
            for line in lines:
                txt = self.font.render(line, True, TEXT)
                self.screen.blit(txt, (rect.x + pad, y))
                y += txt.get_height() + 6

            bl = self.wrap_text(z.blurb, rect.w - 220 - pad*2, self.font_small)
            y += 6
            for seg in bl:
                tip = self.font_small.render(seg, True, TEXT_DIM)
                self.screen.blit(tip, (rect.x + pad, y))
                y += tip.get_height() + 2

        # Bottom disclaimer
        disc = "No copyrighted assets. Use original branding when distributing."
        disct = self.font_small.render(disc, True, TEXT_DIM)
        self.screen.blit(disct, (rect.right - disct.get_width() - pad, rect.bottom - disct.get_height() - pad))

    def draw_plant_icon(self, rect, s: PlantStats):
        # abstract icon
        core = rect.inflate(-rect.w*0.5, -rect.h*0.48); core.y += 4
        pygame.draw.rect(self.screen, s.color, core, border_radius=8)
        if s.shoots:
            mx, my = core.right - 6, core.centery
            pygame.draw.circle(self.screen, (22, 60, 22), (int(mx), int(my)), 8)
        elif s.generates:
            pygame.draw.polygon(self.screen, (220, 180, 40), [
                (core.centerx, core.top),
                (core.left, core.bottom),
                (core.right, core.bottom),
            ])
        else:
            pygame.draw.rect(self.screen, (80, 65, 50), core)

    def draw_zombie_icon(self, rect, z: ZombieInfo):
        body = rect.inflate(-rect.w*0.45, -rect.h*0.35)
        pygame.draw.rect(self.screen, z.color_idle, body, border_radius=10)
        # eyes
        pygame.draw.circle(self.screen, (240, 240, 240), (body.x + 16, body.y + 22), 6)
        pygame.draw.circle(self.screen, (240, 240, 240), (body.x + 32, body.y + 22), 6)

    def wrap_text(self, text, width, font):
        # Simple word-wrap returning list of lines
        words = text.split()
        lines, cur = [], ""
        for w in words:
            test = (cur + " " + w).strip()
            if font.size(test)[0] <= width:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    # -----------------------------------
    # Game draw
    # -----------------------------------
    def draw_grid(self, surf):
        # Lawn tiles
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                rect = grid_cell_rect(r, c)
                color = GRASS_A if (r + c) % 2 == 0 else GRASS_B
                pygame.draw.rect(surf, color, rect)
                pygame.draw.rect(surf, GRID_LINE, rect, 1)

    def draw_ui(self, surf):
        # Top bar
        pygame.draw.rect(surf, UI_BG, (0, 0, SCREEN_W, UI_BAR_H))

        # Title
        title_surf = self.font.render(TITLE, True, TEXT)
        surf.blit(title_surf, (20, 10))

        # Sun counter
        sun_label = self.font.render(f"Sun: {int(self.sun)}", True, GOLD)
        surf.blit(sun_label, (SCREEN_W - 160, 10))

        # Wave progress
        bar_w = 260
        bar_h = 14
        bx = SCREEN_W - bar_w - 20
        by = 40
        pygame.draw.rect(surf, PROGRESS_BG, (bx, by, bar_w, bar_h), border_radius=7)
        pygame.draw.rect(surf, PROGRESS_BAR, (bx, by, int(bar_w * self.progress), bar_h), border_radius=7)
        prog_text = self.font_small.render(f"Wave {self.spawned}/{LEVEL_TOTAL_ZOMBIES}", True, TEXT_DIM)
        surf.blit(prog_text, (bx, by - 18))

        # Cards
        for card in self.cards:
            rect = card["rect"]
            stats = card["stats"]
            available = (card["cd"] <= 0 and self.sun >= stats.cost)
            base_color = stats.color
            # card background
            pygame.draw.rect(surf, base_color, rect, border_radius=10)
            pygame.draw.rect(surf, CARD_OUTLINE, rect, 2, border_radius=10)

            # Plant icon (abstract shape)
            icon = rect.inflate(-rect.w * 0.6, -rect.h * 0.5)
            icon.y += 6
            if stats.shoots:
                pygame.draw.circle(surf, (40, 85, 40), icon.center, max(8, icon.w // 3))
                pygame.draw.circle(surf, (20, 40, 20), icon.center, max(6, icon.w // 4), 3)
            elif stats.generates:
                pygame.draw.polygon(surf, (220, 180, 40), [
                    (icon.centerx, icon.top),
                    (icon.left, icon.bottom),
                    (icon.right, icon.bottom),
                ])
            else:
                pygame.draw.rect(surf, (80, 65, 50), icon)

            # Texts
            name_s = self.font.render(stats.name, True, TEXT)
            cost_s = self.font_small.render(f"Cost {stats.cost}", True, TEXT)
            surf.blit(name_s, (rect.x + 10, rect.y + rect.h - 42))
            surf.blit(cost_s, (rect.x + 10, rect.y + rect.h - 22))

            # Cooldown overlay or dim
            if card["cd"] > 0 or self.sun < stats.cost:
                overlay = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 90) if self.sun < stats.cost else (0, 0, 0, 65))
                if card["cd"] > 0:
                    frac = clamp(card["cd"] / stats.cooldown, 0, 1)
                    cd_h = int(rect.h * frac)
                    pygame.draw.rect(overlay, (0, 0, 0, 110), (0, rect.h - cd_h, rect.w, cd_h))
                surf.blit(overlay, rect.topleft)

            # Selection highlight
            if self.selected_card is card:
                pygame.draw.rect(surf, (255, 255, 255), rect, 3, border_radius=10)

        # Tips line
        tips = "Left-click card→tile to place | Click sun orbs | Right-click plant to shovel | P pause, R restart, ESC quit"
        tips_s = self.font_small.render(tips, True, TEXT_DIM)
        surf.blit(tips_s, (20, UI_BAR_H - 20))

    def draw_entities(self, surf):
        # Plants
        for r in range(GRID_ROWS):
            for p in self.plants[r]:
                rect = p.rect()
                pygame.draw.rect(surf, p.stats.color, rect, border_radius=8)
                # HP bar
                hp_frac = clamp(p.hp / p.stats.max_hp, 0.0, 1.0)
                bar = pygame.Rect(rect.x, rect.bottom + 2, rect.w, 6)
                pygame.draw.rect(surf, (40, 40, 46), bar, border_radius=3)
                pygame.draw.rect(surf, (90, 230, 120), (bar.x, bar.y, int(bar.w * hp_frac), bar.h), border_radius=3)
                # shooter muzzle hint
                if p.stats.shoots:
                    mx, my = p.midright()
                    pygame.draw.circle(surf, (22, 60, 22), (int(mx), int(my)), 6)

        # Pellets
        for pel in self.pellets:
            pygame.draw.circle(surf, (240, 255, 255), (int(pel.x), int(pel.y)), PELLET_RADIUS)

        # Zombies
        for r in range(GRID_ROWS):
            for z in self.zombies[r]:
                zr = z.rect()
                color = (160, 120, 120) if z.gnawing else (180, 140, 140)
                pygame.draw.rect(surf, color, zr, border_radius=6)
                # Eyes
                pygame.draw.circle(surf, (240, 240, 240), (zr.x + 12, zr.y + 16), 5)
                pygame.draw.circle(surf, (240, 240, 240), (zr.x + 26, zr.y + 16), 5)
                # HP bar
                hp_frac = clamp(z.hp / ZOMBIE_BASE_HP, 0.0, 1.0)
                bar = pygame.Rect(zr.x, zr.y - 8, zr.w, 5)
                pygame.draw.rect(surf, (40, 40, 46), bar, border_radius=3)
                pygame.draw.rect(
                    surf, (255, 120, 120),
                    (bar.x, bar.y, int(bar.w * hp_frac), bar.h), border_radius=3
                )

        # Sun orbs
        for orb in self.suns:
            orb.draw(surf)

    def draw_state_overlay(self, surf):
        if self.state == "victory":
            msg = "YOU WIN!  Click or press R to play again."
            color = (120, 235, 160)
        elif self.state == "defeat":
            msg = "ZOMBIES ATE YOUR… house line! Click or press R to retry."
            color = WARNING
        else:
            return
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 130))
        surf.blit(overlay, (0, 0))
        t = self.font_big.render(msg, True, color)
        surf.blit(t, (SCREEN_W // 2 - t.get_width() // 2, SCREEN_H // 2 - 30))

    def draw_pause(self, surf):
        if not (self.mode == "playing" and self.paused and self.state == "playing"):
            return
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill(PAUSE_TINT)
        surf.blit(overlay, (0, 0))
        t = self.font_big.render("PAUSED", True, (230, 230, 240))
        surf.blit(t, (SCREEN_W // 2 - t.get_width() // 2, SCREEN_H // 2 - 26))

    def draw_game(self):
        self.screen.fill(BG)
        self.draw_grid(self.screen)
        self.draw_entities(self.screen)
        self.draw_ui(self.screen)
        self.draw_state_overlay(self.screen)
        self.draw_pause(self.screen)

# -----------------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        Game().run()
    except Exception as e:
        print("Fatal error:", e)
        pygame.quit()
        sys.exit(1)
