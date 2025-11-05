#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ultra PVZ 0.3 — single-file prototype engine in pygame
------------------------------------------------------
Features
- Main Menu (Play, Almanac, Settings, Quit)
- Lawn (grid board, seed bank UI, sun economy, three plant types, zombies, basic win/lose)
- Almanac (browse plants & zombies with stats)
- Settings (FPS cap, difficulty, mute toggle, debug grid/overlay)
- No external assets; all visuals are rectangles, circles, and text.
- Single file; no save files written (PR files = off).

How to run
    pip install pygame
    python program.py

Keybinds (in Lawn)
    [1][2][3] quick-select plant cards
    [ESC] open pause menu (resume, settings, main menu)
    [D] toggle debug overlay
    [R] restart wave
    [M] open Almanac
    Left click = place
    Right click = shovel (remove plant)

This is a teaching / prototype engine intended to be extended.
PopCap / PVZ are trademarks of their owners; this file uses original placeholder code and shapes only.
"""
import sys
import math
import random
from dataclasses import dataclass, field

import pygame

VERSION = "Ultra PVZ 0.3"
PR_FILES_OFF = True  # honor the user's 'pr files = off' request: no disk writes


# ---------------------------- Utility & Config ----------------------------

@dataclass
class GameConfig:
    rows: int = 5
    cols: int = 9
    tile: int = 84
    margin_left: int = 220  # space for seed bank
    margin_top: int = 60    # top UI strip
    fps: int = 60
    width: int = field(init=False)
    height: int = field(init=False)
    starting_sun: int = 150
    debug: bool = False
    difficulty: float = 1.0  # 0.5 (easy) ... 2.0 (hard)
    music_volume: float = 0.0  # placeholder

    def __post_init__(self):
        self.width = self.margin_left + self.cols * self.tile + 40
        self.height = self.margin_top + self.rows * self.tile + 60


CFG = GameConfig()


# Colors (no explicit style library; just a small palette)
COL_BG = (23, 26, 33)
COL_PANEL = (33, 38, 48)
COL_ACCENT = (142, 197, 70)
COL_ACCENT_2 = (233, 196, 106)
COL_TEXT = (230, 232, 239)
COL_TEXT_DIM = (160, 170, 185)
COL_RED = (230, 80, 80)
COL_GREEN = (90, 190, 95)
COL_YELLOW = (240, 220, 120)
COL_BLUE = (120, 160, 240)
COL_BTN = (50, 56, 68)
COL_BTN_HOVER = (70, 76, 88)
COL_GRID = (44, 50, 62)


# ---------------------------- Engine Core ----------------------------

class Scene:
    def __init__(self, engine):
        self.engine = engine

    def enter(self):  # called when scene becomes active
        pass

    def handle_event(self, e):
        pass

    def update(self, dt):
        pass

    def draw(self, surf):
        pass


class Engine:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(VERSION)
        self.screen = pygame.display.set_mode((CFG.width, CFG.height))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 24)
        self.font_big = pygame.font.SysFont(None, 42)
        self.scene = None
        self.running = True

        # shared state (for settings)
        self.settings = {
            "fps_cap": CFG.fps,
            "difficulty": CFG.difficulty,
            "mute": False,
            "debug": CFG.debug,
        }

        # Almanac data (discoveries as you play; but no disk writes)
        self.almanac_known = {
            "plants": set(["Shooter", "Sun Plant", "Blocker"]),
            "zombies": set(["Walker"]),
        }

        self.goto(MainMenu(self))

    def goto(self, scene: Scene):
        self.scene = scene
        self.scene.enter()

    def main_loop(self):
        while self.running:
            dt = self.clock.tick(self.settings["fps_cap"]) / 1000.0
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                else:
                    self.scene.handle_event(e)
            self.scene.update(dt)
            self.scene.draw(self.screen)
            pygame.display.flip()
        pygame.quit()


# ---------------------------- UI Widgets ----------------------------

class Button:
    def __init__(self, rect, text, on_click, font, tooltip=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.on_click = on_click
        self.font = font
        self.tooltip = tooltip
        self.hover = False
        self.disabled = False

    def handle(self, e):
        if self.disabled:
            return
        if e.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(e.pos)
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.rect.collidepoint(e.pos):
                self.on_click()

    def draw(self, surf):
        col = COL_BTN_HOVER if self.hover and not self.disabled else COL_BTN
        pygame.draw.rect(surf, col, self.rect, border_radius=8)
        pygame.draw.rect(surf, (0,0,0), self.rect, 2, border_radius=8)
        txt = self.font.render(self.text, True, COL_TEXT)
        surf.blit(txt, txt.get_rect(center=self.rect.center))


class Slider:
    def __init__(self, x, y, w, min_v, max_v, value, label, font, step=None):
        self.rect = pygame.Rect(x, y, w, 28)
        self.min = min_v
        self.max = max_v
        self.value = value
        self.label = label
        self.dragging = False
        self.font = font
        self.step = step

    def _pos_to_val(self, x):
        t = (x - self.rect.x) / max(1, self.rect.w)
        v = self.min + t * (self.max - self.min)
        if self.step:
            v = round(v / self.step) * self.step
        return max(self.min, min(self.max, v))

    def handle(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.rect.collidepoint(e.pos):
            self.dragging = True
            self.value = self._pos_to_val(e.pos[0])
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            self.dragging = False
        elif e.type == pygame.MOUSEMOTION and self.dragging:
            self.value = self._pos_to_val(e.pos[0])

    def draw(self, surf):
        # track
        pygame.draw.rect(surf, COL_GRID, self.rect, border_radius=6)
        # knob pos
        t = (self.value - self.min) / (self.max - self.min)
        x = int(self.rect.x + t * self.rect.w)
        pygame.draw.circle(surf, COL_ACCENT, (x, self.rect.centery), 8)
        # label
        txt = f"{self.label}: {self.value:.2f}" if isinstance(self.value, float) else f"{self.label}: {int(self.value)}"
        img = self.font.render(txt, True, COL_TEXT)
        surf.blit(img, (self.rect.x, self.rect.y - 24))


class Toggle:
    def __init__(self, x, y, label, value, font):
        self.rect = pygame.Rect(x, y, 40, 24)
        self.label = label
        self.value = value
        self.font = font

    def handle(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and (self.rect.collidepoint(e.pos) or self.label_rect.collidepoint(e.pos)):
            self.value = not self.value

    def draw(self, surf):
        # label text first to compute clickable area
        label_img = self.font.render(self.label, True, COL_TEXT)
        self.label_rect = label_img.get_rect(midleft=(self.rect.right + 10, self.rect.centery))
        # track
        pygame.draw.rect(surf, COL_GRID, self.rect, border_radius=12)
        knob_x = self.rect.x + (22 if self.value else 6)
        pygame.draw.circle(surf, COL_ACCENT if self.value else COL_TEXT_DIM, (knob_x, self.rect.centery), 8)
        surf.blit(label_img, self.label_rect)


# ---------------------------- Lawn / Game Logic ----------------------------

@dataclass
class PlantType:
    name: str
    cost: int
    max_hp: int
    cooldown: float
    desc: str
    # behavior params
    fire_rate: float = 0.0      # shots per second (if shooter)
    damage: int = 0
    sun_rate: float = 0.0       # sun per second (if generator)
    armor: float = 1.0          # damage multiplier (1.0 default)


PLANTS = [
    PlantType("Shooter", cost=100, max_hp=300, cooldown=5.0,
              desc="Fires peas at enemies in its row.",
              fire_rate=0.8, damage=20),
    PlantType("Sun Plant", cost=50, max_hp=250, cooldown=5.0,
              desc="Generates sun over time.",
              sun_rate=0.8),
    PlantType("Blocker", cost=50, max_hp=800, cooldown=5.0,
              desc="Soaks damage, slowing foes."),
]

PLANT_INDEX = {p.name: i for i, p in enumerate(PLANTS)}


@dataclass
class ZombieType:
    name: str
    hp: int
    speed: float
    desc: str


ZOMBIE_WALKER = ZombieType("Walker", hp=220, speed=22.0, desc="Lumbers left. Chews on plants.")

# runtime objects
class Plant:
    def __init__(self, ptype: PlantType, row: int, col: int):
        self.ptype = ptype
        self.row = row
        self.col = col
        self.hp = ptype.max_hp
        self.fire_cd = 0.0
        self.sun_cd = 0.0

    def rect(self, board):
        x, y = board.cell_to_px(self.row, self.col)
        return pygame.Rect(x+8, y+8, board.tile-16, board.tile-16)

    def update(self, dt, board, world):
        self.hp = min(self.hp, self.ptype.max_hp)
        # Shooter: fire if zombie ahead in row
        if self.ptype.fire_rate > 0:
            self.fire_cd -= dt
            if self.fire_cd <= 0 and board.row_has_zombie_ahead(self.row, self.col):
                self.fire_cd = 1.0 / self.ptype.fire_rate
                px, py = self.rect(board).midright
                world.projectiles.append(Projectile(px, py, speed=240, dmg=self.ptype.damage))
        # Sun generator
        if self.ptype.sun_rate > 0:
            self.sun_cd -= dt
            if self.sun_cd <= 0:
                self.sun_cd = 1.0 / self.ptype.sun_rate
                world.sun += 5  # gentle drip feed

    def draw(self, surf, board):
        r = self.rect(board)
        # body
        pygame.draw.rect(surf, COL_GREEN, r, border_radius=10)
        # hp bar
        hp_t = max(0, self.hp) / self.ptype.max_hp
        if hp_t < 1.0:
            bar = pygame.Rect(r.x, r.y - 6, int(r.w * hp_t), 4)
            pygame.draw.rect(surf, COL_YELLOW if hp_t > 0.5 else COL_RED, bar, border_radius=2)
        # small icon hint
        label = board.engine.font.render(self.ptype.name.split()[0], True, COL_TEXT)
        surf.blit(label, (r.x+6, r.y+6))


class Zombie:
    def __init__(self, ztype: ZombieType, row: int, x: int):
        self.ztype = ztype
        self.row = row
        self.x = x
        self.hp = int(ztype.hp * (0.75 + 0.5 * CFG.difficulty))  # scale a bit
        self.stunned = 0.0
        self.chew_cd = 0.0

    def rect(self, board):
        y = board.margin_top + self.row * board.tile
        return pygame.Rect(int(self.x), y+10, board.tile-20, board.tile-20)

    def update(self, dt, board, world):
        if self.stunned > 0:
            self.stunned -= dt
        # collide with plant in current cell
        col = board.px_to_col(self.x + 10)
        plant = board.get_plant(self.row, col)
        if plant:
            # chew
            self.chew_cd -= dt
            if self.chew_cd <= 0:
                self.chew_cd = 0.6
                plant.hp -= int(25 * CFG.difficulty)
        else:
            # move
            v = self.ztype.speed * (0.8 + 0.4 * CFG.difficulty)
            self.x -= v * dt

    def draw(self, surf, board):
        r = self.rect(board)
        pygame.draw.rect(surf, (140, 110, 110), r, border_radius=6)
        hp_t = max(0, self.hp) / (self.ztype.hp * (0.75 + 0.5 * CFG.difficulty))
        bar = pygame.Rect(r.x, r.y - 6, int(r.w * hp_t), 4)
        pygame.draw.rect(surf, COL_RED, bar, border_radius=2)
        label = board.engine.font.render("Z", True, COL_TEXT)
        surf.blit(label, (r.x+6, r.y+6))


class Projectile:
    def __init__(self, x, y, speed, dmg):
        self.x = x
        self.y = y
        self.speed = speed
        self.dmg = dmg
        self.alive = True

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y)-3, 10, 6)

    def update(self, dt, world):
        self.x += self.speed * dt
        # collision test
        for z in world.zombies:
            if z.rect(world.board).colliderect(self.rect()) and z.row == world.board.px_to_row(self.y):
                z.hp -= self.dmg
                self.alive = False
                break
        # off screen
        if self.x > CFG.width + 50:
            self.alive = False

    def draw(self, surf):
        pygame.draw.rect(surf, COL_ACCENT_2, self.rect(), border_radius=3)


class Board:
    def __init__(self, engine):
        self.engine = engine
        self.rows = CFG.rows
        self.cols = CFG.cols
        self.tile = CFG.tile
        self.margin_left = CFG.margin_left
        self.margin_top = CFG.margin_top
        self.grid = [[None for _ in range(self.cols)] for _ in range(self.rows)]

    def cell_to_px(self, row, col):
        x = self.margin_left + col * self.tile
        y = self.margin_top + row * self.tile
        return x, y

    def px_to_cell(self, px, py):
        col = (px - self.margin_left) // self.tile
        row = (py - self.margin_top) // self.tile
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return int(row), int(col)
        return None, None

    def px_to_col(self, px):
        return int((px - self.margin_left) // self.tile)

    def px_to_row(self, py):
        return int((py - self.margin_top) // self.tile)

    def get_plant(self, row, col):
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.grid[row][col]
        return None

    def place_plant(self, plant: Plant):
        if self.grid[plant.row][plant.col] is None:
            self.grid[plant.row][plant.col] = plant
            return True
        return False

    def remove_plant(self, row, col):
        if 0 <= row < self.rows and 0 <= col < self.cols and self.grid[row][col] is not None:
            self.grid[row][col] = None
            return True
        return False

    def row_has_zombie_ahead(self, row, col):
        # any zombie in this row with x > plant x
        px, _ = self.cell_to_px(row, col)
        for z in self.engine.scene.world.zombies:
            if z.row == row and z.x > px:
                return True
        return False

    def draw(self, surf):
        # base lawn
        pygame.draw.rect(surf, (40, 90, 40),
                         pygame.Rect(self.margin_left-6, self.margin_top-6,
                                     self.cols*self.tile+12, self.rows*self.tile+12), border_radius=10)
        for r in range(self.rows):
            for c in range(self.cols):
                x, y = self.cell_to_px(r, c)
                color = (45, 110, 50) if (r + c) % 2 == 0 else (50, 120, 60)
                tile_rect = pygame.Rect(x+2, y+2, self.tile-4, self.tile-4)
                pygame.draw.rect(surf, color, tile_rect, border_radius=6)
                if self.engine.settings["debug"]:
                    pygame.draw.rect(surf, COL_GRID, tile_rect, 1, border_radius=6)


class SeedCard:
    def __init__(self, plant_type: PlantType, idx: int, bank):
        self.plant_type = plant_type
        self.idx = idx
        self.bank = bank
        self.cooldown = 0.0
        w, h = 180, 54
        x = 20
        y = 80 + idx * (h + 10)
        self.rect = pygame.Rect(x, y, w, h)

    def update(self, dt):
        if self.cooldown > 0.0:
            self.cooldown = max(0.0, self.cooldown - dt)

    def can_take(self, sun):
        return self.cooldown <= 0.0 and sun >= self.plant_type.cost

    def draw(self, surf, font, selected: bool, sun: int):
        # card bg
        col = COL_BTN_HOVER if selected else COL_BTN
        pygame.draw.rect(surf, col, self.rect, border_radius=8)
        pygame.draw.rect(surf, (0,0,0), self.rect, 2, border_radius=8)

        # title & cost
        title = font.render(f"[{self.idx+1}] {self.plant_type.name}", True, COL_TEXT)
        cost = font.render(f"{self.plant_type.cost} ☼", True, COL_YELLOW if sun >= self.plant_type.cost else COL_TEXT_DIM)
        surf.blit(title, (self.rect.x + 10, self.rect.y + 6))
        surf.blit(cost, (self.rect.right - cost.get_width() - 8, self.rect.y + 6))

        # desc
        desc = font.render(self.plant_type.desc, True, COL_TEXT_DIM)
        surf.blit(desc, (self.rect.x + 10, self.rect.y + 28))

        # cooldown overlay
        if self.cooldown > 0.0:
            t = min(1.0, self.cooldown / self.plant_type.cooldown)
            h = int(self.rect.h * t)
            overlay = pygame.Rect(self.rect.x, self.rect.bottom - h, self.rect.w, h)
            s = pygame.Surface((overlay.w, overlay.h), pygame.SRCALPHA)
            s.fill((0, 0, 0, 110))
            surf.blit(s, overlay.topleft)


class SeedBank:
    def __init__(self, engine):
        self.engine = engine
        self.cards = [SeedCard(PLANTS[i], i, self) for i in range(len(PLANTS))]
        self.selected_idx = 0

    def update(self, dt, sun):
        for c in self.cards:
            c.update(dt)

    def draw(self, surf, sun):
        # panel
        pygame.draw.rect(surf, COL_PANEL, pygame.Rect(10, 10, CFG.margin_left-20, CFG.height-20), border_radius=12)
        title = self.engine.font_big.render("Seed Bank", True, COL_TEXT)
        surf.blit(title, (20, 20))
        sun_img = self.engine.font_big.render(f"☼ {sun}", True, COL_YELLOW)
        surf.blit(sun_img, (CFG.margin_left - sun_img.get_width() - 20, 20))

        for i, c in enumerate(self.cards):
            selected = (i == self.selected_idx)
            c.draw(surf, self.engine.font, selected, self.engine.scene.world.sun)

    def handle(self, e, sun):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, c in enumerate(self.cards):
                if c.rect.collidepoint(e.pos):
                    self.selected_idx = i
                    break
        elif e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_1, pygame.K_KP1): self.selected_idx = 0
            elif e.key in (pygame.K_2, pygame.K_KP2) and len(self.cards) > 1: self.selected_idx = 1
            elif e.key in (pygame.K_3, pygame.K_KP3) and len(self.cards) > 2: self.selected_idx = 2

    def current(self):
        return self.cards[self.selected_idx]


class World:
    def __init__(self, engine):
        self.engine = engine
        self.board = Board(engine)
        self.zombies = []
        self.projectiles = []
        self.sun = CFG.starting_sun
        self.spawn_cd = 2.0
        self.time = 0.0
        self.game_over = False
        self.victory = False
        self.wave_duration = 120.0  # seconds until spawns stop
        self.wave_time = 0.0

    def restart(self):
        self.__init__(self.engine)

    def spawn_zombie(self):
        row = random.randrange(self.board.rows)
        x = CFG.width + random.randint(0, 80)
        z = Zombie(ZOMBIE_WALKER, row=row, x=x)
        self.zombies.append(z)

    def update(self, dt):
        if self.game_over or self.victory:
            return
        self.time += dt
        self.wave_time += dt

        # spawn logic
        self.spawn_cd -= dt
        if self.wave_time < self.wave_duration and self.spawn_cd <= 0:
            self.spawn_cd = max(0.8, 2.8 - self.engine.settings["difficulty"] * 1.5)  # harder -> faster spawns
            self.spawn_zombie()

        # update plants
        for r in range(self.board.rows):
            for c in range(self.board.cols):
                p = self.board.grid[r][c]
                if p:
                    p.update(dt, self.board, self)

        # update zombies
        for z in list(self.zombies):
            z.update(dt, self.board, self)
            if z.hp <= 0:
                self.zombies.remove(z)

        # update projectiles
        for pr in list(self.projectiles):
            pr.update(dt, self)
            if not pr.alive:
                self.projectiles.remove(pr)

        # clean up dead plants
        for r in range(self.board.rows):
            for c in range(self.board.cols):
                p = self.board.grid[r][c]
                if p and p.hp <= 0:
                    self.board.grid[r][c] = None

        # lose condition: any zombie crosses the left edge
        for z in self.zombies:
            if z.x < 20:
                self.game_over = True
                break

        # win condition: spawns stop and no zombies remain shortly after
        if self.wave_time >= self.wave_duration and not self.zombies:
            self.victory = True

    def draw(self, surf):
        self.board.draw(surf)
        # plants
        for r in range(self.board.rows):
            for c in range(self.board.cols):
                p = self.board.grid[r][c]
                if p:
                    p.draw(surf, self.board)
        # projectiles
        for pr in self.projectiles:
            pr.draw(surf)
        # zombies
        for z in self.zombies:
            z.draw(surf, self.board)

        if self.game_over:
            self._overlay_message(surf, "Zombies ate your brains!")
        if self.victory:
            self._overlay_message(surf, "You defended the lawn!")

    def _overlay_message(self, surf, text):
        s = pygame.Surface((CFG.width, CFG.height), pygame.SRCALPHA)
        s.fill((0,0,0, 150))
        surf.blit(s, (0,0))
        title = self.engine.font_big.render(text, True, COL_TEXT)
        surf.blit(title, title.get_rect(center=(CFG.width//2, CFG.height//2 - 20)))
        tip = self.engine.font.render("Press R to restart or ESC for menu", True, COL_TEXT_DIM)
        surf.blit(tip, tip.get_rect(center=(CFG.width//2, CFG.height//2 + 20)))


# ---------------------------- Scenes ----------------------------

class MainMenu(Scene):
    def enter(self):
        self.buttons = []
        f = self.engine.font_big
        w = 300
        x = CFG.width//2 - w//2
        y = 180
        gap = 68
        self.buttons.append(Button((x, y, w, 56), "Play", lambda: self.engine.goto(LawnScene(self.engine)), f))
        self.buttons.append(Button((x, y+gap, w, 56), "Almanac", lambda: self.engine.goto(AlmanacScene(self.engine)), f))
        self.buttons.append(Button((x, y+2*gap, w, 56), "Settings", lambda: self.engine.goto(SettingsScene(self.engine, back_to="menu")), f))
        self.buttons.append(Button((x, y+3*gap, w, 56), "Quit", self.quit, f))

    def quit(self):
        self.engine.running = False

    def handle_event(self, e):
        for b in self.buttons:
            b.handle(e)

    def update(self, dt):
        pass

    def draw(self, surf):
        surf.fill(COL_BG)
        title = self.engine.font_big.render(VERSION, True, COL_TEXT)
        surf.blit(title, title.get_rect(center=(CFG.width//2, 90)))
        subtitle = self.engine.font.render("A tiny single-file PVZ-like engine (no assets, PR files off)", True, COL_TEXT_DIM)
        surf.blit(subtitle, subtitle.get_rect(center=(CFG.width//2, 120)))
        for b in self.buttons:
            b.draw(surf)


class PauseOverlay:
    def __init__(self, engine, resume_cb, to_menu_cb):
        self.engine = engine
        self.resume_cb = resume_cb
        self.to_menu_cb = to_menu_cb
        self.buttons = []
        f = self.engine.font_big
        w = 320
        x = CFG.width//2 - w//2
        y = CFG.height//2 - 120
        self.buttons.append(Button((x, y, w, 56), "Resume", self.resume_cb, f))
        self.buttons.append(Button((x, y+70, w, 56), "Settings", lambda: self.engine.goto(SettingsScene(self.engine, back_to="lawn")), f))
        self.buttons.append(Button((x, y+140, w, 56), "Main Menu", self.to_menu_cb, f))

    def handle(self, e):
        for b in self.buttons:
            b.handle(e)

    def draw(self, surf):
        s = pygame.Surface((CFG.width, CFG.height), pygame.SRCALPHA)
        s.fill((0,0,0,180))
        surf.blit(s, (0,0))
        for b in self.buttons:
            b.draw(surf)


class LawnScene(Scene):
    def enter(self):
        self.world = World(self.engine)
        self.board = self.world.board
        self.seed_bank = SeedBank(self.engine)
        self.paused = False
        self.pause_overlay = PauseOverlay(self.engine, self.toggle_pause, lambda: self.engine.goto(MainMenu(self.engine)))
        self.status_tip = "Left-click to place, Right-click to shovel. 1/2/3 select seeds. ESC menu."

    def toggle_pause(self):
        self.paused = not self.paused

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.toggle_pause()
            return

        if self.paused:
            self.pause_overlay.handle(e)
            return

        self.seed_bank.handle(e, self.world.sun)

        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_m:
                self.engine.goto(AlmanacScene(self.engine, back_to="lawn"))
            elif e.key == pygame.K_r:
                self.world.restart()
            elif e.key == pygame.K_d:
                self.engine.settings["debug"] = not self.engine.settings["debug"]

        if e.type == pygame.MOUSEBUTTONDOWN:
            if e.button == 1:
                # place
                row, col = self.board.px_to_cell(*e.pos)
                if row is not None:
                    card = self.seed_bank.current()
                    if card.can_take(self.world.sun) and self.board.get_plant(row, col) is None:
                        p = Plant(card.plant_type, row, col)
                        if self.board.place_plant(p):
                            self.world.sun -= card.plant_type.cost
                            card.cooldown = card.plant_type.cooldown
            elif e.button == 3:
                # shovel
                row, col = self.board.px_to_cell(*e.pos)
                if row is not None:
                    self.board.remove_plant(row, col)

    def update(self, dt):
        if not self.paused:
            self.seed_bank.update(dt, self.world.sun)
            self.world.update(dt)

    def draw(self, surf):
        surf.fill(COL_BG)
        # left panel (seed bank)
        self.seed_bank.draw(surf, self.world.sun)

        # lawn
        self.world.draw(surf)

        # top strip
        strip = pygame.Rect(CFG.margin_left, 10, CFG.width - CFG.margin_left - 10, 40)
        pygame.draw.rect(surf, COL_PANEL, strip, border_radius=10)
        tip = self.engine.font.render(self.status_tip, True, COL_TEXT_DIM)
        surf.blit(tip, (strip.x + 12, strip.y + 10))

        # pause overlay
        if self.paused:
            self.pause_overlay.draw(surf)


class AlmanacScene(Scene):
    def __init__(self, engine, back_to="menu"):
        super().__init__(engine)
        self.back_to = back_to

    def enter(self):
        self.scroll = 0
        self.buttons = [Button((20, CFG.height - 60, 160, 40), "Back", self.go_back, self.engine.font_big)]
        # compile entries (plants then zombies)
        self.plant_entries = PLANTS
        self.zombie_entries = [ZOMBIE_WALKER]

    def go_back(self):
        if self.back_to == "menu":
            self.engine.goto(MainMenu(self.engine))
        else:
            self.engine.goto(LawnScene(self.engine))

    def handle_event(self, e):
        for b in self.buttons:
            b.handle(e)
        if e.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, self.scroll - e.y * 40)

    def update(self, dt):
        pass

    def _draw_entry(self, surf, x, y, title, body_lines, color):
        box = pygame.Rect(x, y, CFG.width - x - 20, 100)
        pygame.draw.rect(surf, COL_PANEL, box, border_radius=8)
        pygame.draw.rect(surf, (0,0,0), box, 2, border_radius=8)
        name = self.engine.font_big.render(title, True, color)
        surf.blit(name, (box.x + 12, box.y + 8))
        for i, ln in enumerate(body_lines):
            timg = self.engine.font.render(ln, True, COL_TEXT_DIM)
            surf.blit(timg, (box.x + 12, box.y + 50 + i*20))

    def draw(self, surf):
        surf.fill(COL_BG)
        title = self.engine.font_big.render("Almanac", True, COL_TEXT)
        surf.blit(title, (20, 16))
        y = 60 - self.scroll

        # Plants
        header = self.engine.font.render("Plants", True, COL_ACCENT)
        surf.blit(header, (20, y)); y += 24
        for p in self.plant_entries:
            lines = [
                p.desc,
                f"Cost: {p.cost} ☼   HP: {p.max_hp}   Cooldown: {p.cooldown:.1f}s",
                f"Fire Rate: {p.fire_rate}/s   Damage: {p.damage}   Sun Rate: {p.sun_rate}/s",
            ]
            self._draw_entry(surf, 20, y, p.name, lines, COL_ACCENT); y += 110 + 10

        # Zombies
        header = self.engine.font.render("Zombies", True, COL_ACCENT_2)
        surf.blit(header, (20, y)); y += 24
        for z in [ZOMBIE_WALKER]:
            lines = [
                z.desc,
                f"HP: {z.hp}   Speed: {z.speed:.1f} px/s",
            ]
            self._draw_entry(surf, 20, y, z.name, lines, COL_ACCENT_2); y += 110 + 10

        # Back button
        for b in self.buttons:
            b.draw(surf)


class SettingsScene(Scene):
    def __init__(self, engine, back_to="menu"):
        super().__init__(engine)
        self.back_to = back_to

    def enter(self):
        self.buttons = [Button((20, CFG.height - 60, 160, 40), "Back", self.go_back, self.engine.font_big)]
        self.sl_fps = Slider(260, 120, 360, 30, 240, self.engine.settings["fps_cap"], "FPS Cap", self.engine.font, step=10)
        self.sl_diff = Slider(260, 200, 360, 0.5, 2.0, self.engine.settings["difficulty"], "Difficulty", self.engine.font, step=0.1)
        self.tg_mute = Toggle(260, 280, "Mute (placeholder, no audio)", self.engine.settings["mute"], self.engine.font)
        self.tg_debug = Toggle(260, 330, "Debug Grid/Overlay", self.engine.settings["debug"], self.engine.font)

    def go_back(self):
        # apply
        self.engine.settings["fps_cap"] = int(self.sl_fps.value)
        self.engine.settings["difficulty"] = round(self.sl_diff.value, 2)
        self.engine.settings["mute"] = self.tg_mute.value
        self.engine.settings["debug"] = self.tg_debug.value

        if self.back_to == "menu":
            self.engine.goto(MainMenu(self.engine))
        elif self.back_to == "lawn":
            self.engine.goto(LawnScene(self.engine))

    def handle_event(self, e):
        for b in self.buttons:
            b.handle(e)
        self.sl_fps.handle(e)
        self.sl_diff.handle(e)
        self.tg_mute.handle(e)
        self.tg_debug.handle(e)

    def update(self, dt):
        pass

    def draw(self, surf):
        surf.fill(COL_BG)
        title = self.engine.font_big.render("Settings", True, COL_TEXT)
        surf.blit(title, (20, 16))
        panel = pygame.Rect(240, 80, 520, 320)
        pygame.draw.rect(surf, COL_PANEL, panel, border_radius=12)
        pygame.draw.rect(surf, (0,0,0), panel, 2, border_radius=12)

        self.sl_fps.draw(surf)
        self.sl_diff.draw(surf)
        self.tg_mute.draw(surf)
        self.tg_debug.draw(surf)

        info = [
            "Tip: Difficulty influences spawn rate and zombie stats.",
            "PR files = off — this build does not write any saves to disk.",
        ]
        for i, ln in enumerate(info):
            img = self.engine.font.render(ln, True, COL_TEXT_DIM)
            surf.blit(img, (panel.x + 16, panel.bottom + 16 + i*20))

        for b in self.buttons:
            b.draw(surf)


# ---------------------------- Entry ----------------------------

def main():
    eng = Engine()
    eng.main_loop()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # fail-safe message in console; we still avoid any file writes
        print("Fatal error:", exc)
