#!/usr/bin/env python3
"""
PVZ Rebooted v0.0.4 — Single-file lane defense (no assets)
----------------------------------------------------------
Merged:
- HD 600x400/60 FPS, compact grid + smooth runtime visuals
- Seed bank with costs/cooldowns (Shooter, Solarbud, Rocknut)
- Tutorial, Level Select, Endless
- Wave scheduler, progress bar, shovel removal, win/lose overlays

All art is runtime-drawn. No external assets.
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
TITLE = "PVZ Rebooted v0.0.4 (single file, no assets)"
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

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def clamp(v, a, b): return max(a, min(b, v))

def lerp(a, b, t): return a + (b - a) * t

def ease(t):
    # smoothstep
    t = clamp(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)

def shadow(surface, rect, radius=8, alpha=110):
    # Simple drop shadow behind rect
    s = pygame.Surface((rect.w + radius*2, rect.h + radius*2), pygame.SRCALPHA)
    pygame.draw.rect(s, (0,0,0,alpha), (radius, radius, rect.w, rect.h), border_radius=radius)
    surface.blit(s, (rect.x - radius, rect.y - radius))

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
# Entities: Plants, Projectiles, Enemies, Suns
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
        self.rate = 1.35  # seconds
        self.color = (120, 200, 120)
        self.max_health = self.health = 120

    def update(self, dt, game):
        self.cool -= dt
        # fire if enemy in same row ahead
        ahead = any(e.row == self.row and e.x > cell_rect(self.row, self.col).right for e in game.enemies)
        if ahead and self.cool <= 0:
            self.cool = self.rate
            cx, cy = cell_rect(self.row, self.col).center
            game.projectiles.append(Projectile(self.row, cx+8, cy-4))

    def draw(self, surf):
        r = self.rect()
        pygame.draw.rect(surf, self.color, r, border_radius=12)
        pygame.draw.circle(surf, (30,120,30), (r.centerx+10, r.centery-6), 7)
        super().draw(surf)

class Solarbud(Plant):
    def __init__(self, row, col):
        super().__init__(row, col)
        self.timer = 2.5
        self.interval = 7.0
        self.max_health = self.health = 100
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

class Rocknut(Plant):
    def __init__(self, row, col):
        super().__init__(row, col)
        self.max_health = self.health = 380
        self.color = (150,120,90)

    def update(self, dt, game): pass

    def draw(self, surf):
        r = self.rect()
        pygame.draw.rect(surf, self.color, r, border_radius=14)
        pygame.draw.rect(surf, (100,80,60), r, 3, border_radius=14)
        super().draw(surf)

class Projectile:
    def __init__(self, row, x, y):
        self.row = row
        self.x = x
        self.y = y
        self.v = 280.0
        self.dmg = 25
        self.alive = True

    def update(self, dt, game):
        self.x += self.v * dt
        if self.x > LAWN_X + LAWN_W + 24:
            self.alive = False
            return
        # hit enemy in same row
        for e in game.enemies:
            if e.row == self.row and e.alive:
                if e.rect().collidepoint(self.x, self.y):
                    e.hurt(self.dmg)
                    self.alive = False
                    break

    def draw(self, surf):
        pygame.draw.circle(surf, (80, 200, 60), (int(self.x), int(self.y)), 4)

class Enemy:
    def __init__(self, row, kind="walker", hp=120, speed=22.0, dmg=12):
        self.row = row
        self.kind = kind
        self.health = hp
        self.max_health = hp
        self.speed = speed
        self.dmg = dmg
        self.x = LAWN_X + LAWN_W + 18
        self.alive = True
        self.eating = False
        self._eat_timer = 0.0

    def rect(self):
        y = LAWN_Y + self.row*TILE + 6
        return pygame.Rect(int(self.x)-22, y, 44, TILE-12)

    def update(self, dt, game):
        if not self.alive: return
        # collide with plant in current column
        col = int((self.x - LAWN_X) // TILE)
        col = clamp(col, 0, GRID_COLS-1)
        plant = game.plants[self.row][col]
        if plant:
            self.eating = True
            self._eat_timer -= dt
            if self._eat_timer <= 0:
                self._eat_timer = 0.55
                died = plant.hurt(self.dmg)
                if died:
                    game.plants[self.row][col] = None
        else:
            self.eating = False
            self.x -= self.speed * dt

        # off left edge => lose
        if self.x < LAWN_X - 36:
            game.lose_flag = True

    def hurt(self, dmg):
        self.health -= dmg
        if self.health <= 0:
            self.alive = False

    def draw(self, surf):
        r = self.rect()
        color = (140, 80, 80) if self.kind == "walker" else (120, 70, 160)
        pygame.draw.rect(surf, color, r, border_radius=10)
        # health
        p = clamp(self.health/self.max_health, 0, 1)
        hb = pygame.Rect(r.x, r.y-6, int(r.w*p), 5)
        pygame.draw.rect(surf, RED, (r.x, r.y-6, r.w, 5))
        pygame.draw.rect(surf, GREEN, hb)
        if self.eating:
            pygame.draw.rect(surf, (255,200,120), (r.right-6, r.centery-5, 4, 10))

class Sun:
    def __init__(self, x, y, value=25):
        self.x = x
        self.y = y
        self.vy = 38.0
        self.value = value
        self.t = 0.0
        self.rect = pygame.Rect(x-14, y-14, 28, 28)
        self.alive = True

    def update(self, dt):
        self.t += dt
        if self.t < 1.8:
            self.y += self.vy * dt
            self.rect.topleft = (self.x-14, self.y-14)
        # lifespan
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
        self.mode = mode
        self.level_index = level_index
        self.tutorial = tutorial
        self.endless = endless

        self.sun = 100
        self.selected_card = None
        self.shovel_mode = False

        # plants grid
        self.plants = [[None for _ in range(GRID_COLS)] for __ in range(GRID_ROWS)]
        self.enemies = []
        self.projectiles = []
        self.suns = []

        # seed bank laid out horizontally across HUD
        self.cards = []
        x = 10
        y = 8
        spacing = 8
        for st in app.seed_types:
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

    # schedules
    def make_schedule_easy(self):
        sched = []
        t = 6.0
        for _ in range(5):
            sched.append((t, random.randint(0, GRID_ROWS-1), "walker"))
            t += random.uniform(4.0, 6.5)
        for i in range(3):
            sched.append((t+4+i*1.0, random.randint(0, GRID_ROWS-1), "walker"))
        sched.sort(key=lambda x: x[0])
        return sched

    def make_schedule_for_level(self, idx):
        rnd = random.Random(1234 + idx*77)
        base = 9 + idx*6
        sched = []
        t = 7.0
        for _ in range(base):
            row = rnd.randrange(GRID_ROWS)
            kind = "walker" if rnd.random() < 0.8 else "brute"
            sched.append((t, row, kind))
            t += rnd.uniform(3.3, 6.0)
        for i in range(3+idx):
            sched.append((t+2+i*0.85, rnd.randrange(GRID_ROWS), "walker"))
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
                kind = "walker" if random.random() < 0.7 else "brute"
                self.enemies.append(
                    Enemy(row, kind=kind, hp=160 if kind=="brute" else 120, speed=24 if kind=="brute" else 20, dmg=14)
                )
        else:
            sched = self.schedule
            while self._next_spawn_index < len(sched) and self.total_time >= sched[self._next_spawn_index][0]:
                _, row, kind = sched[self._next_spawn_index]
                hp = 160 if kind=="brute" else 120
                sp = 22 if kind=="brute" else 20
                dmg = 14 if kind=="brute" else 12
                self.enemies.append(Enemy(row, kind=kind, hp=hp, speed=sp, dmg=dmg))
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

        # win/lose state
        if not self.endless:
            if self._next_spawn_index >= len(self.schedule) and len([e for e in self.enemies if e.alive]) == 0:
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

        # Shovel indicator (small tag below sun)
        tag = self.app.font_small.render(f"Shovel: {'ON' if self.shovel_mode else 'OFF'}", True,
                                         RED if self.shovel_mode else GREY)
        surf.blit(tag, (sbox.x+8, sbox.bottom-18))

        # progress (under HUD, across width)
        if not self.endless:
            bar = pygame.Rect(10, HUD_H-18, WIDTH-20, 10)
            pygame.draw.rect(surf, (70,70,90), bar, border_radius=6)
            inner = pygame.Rect(bar.x+2, bar.y+2, int((bar.w-4) * self.progress), bar.h-4)
            pygame.draw.rect(surf, CYAN, inner, border_radius=6)
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

        # plants
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                p = self.plants[r][c]
                if p: p.draw(surf)

        # projectiles, enemies, suns
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

        # overlays
        if self.paused:
            self.draw_overlay(surf, "Paused", buttons=[("Resume", self.toggle_pause),
                                                       ("Main Menu", self.to_menu)])
        if self.win_flag:
            self.draw_overlay(surf, "Level Complete!", buttons=[("Next Level", self.next_level),
                                                                ("Replay", self.replay),
                                                                ("Main Menu", self.to_menu)])
        if self.lose_flag:
            self.draw_overlay(surf, "You Lost!", buttons=[("Retry", self.replay),
                                                           ("Main Menu", self.to_menu)])

        if self.tut:
            self.tut.draw(surf)

    # overlay helpers
    def toggle_pause(self):
        self.paused = not self.paused

    def to_menu(self):
        self.app.change_scene(MainMenu(self.app))

    def next_level(self):
        if self.endless or self.tutorial:
            self.app.change_scene(MainMenu(self.app))
        else:
            nxt = min(self.level_index+1, 2)
            self.app.change_scene(GameScene(self.app, mode="level", level_index=nxt))

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
        # buttons
        bx = box.x + 22
        by = box.y + 110
        self._overlay_btns = []
        for (txt, fn) in buttons:
            b = Button(pygame.Rect(bx, by, 160, 40), txt, action=fn, font=self.app.font_med)
            b.draw(surf)
            self._overlay_btns.append(b)
            bx += 170

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
        self.say("Collect sun and place a Solarbud.", 6)

    def say(self, text, ttl=5.0):
        self.bubbles.append([text, ttl])

    def on_place(self, seed_key, r, c):
        if self.phase == 0 and seed_key == "solar":
            self.say("Nice! Solarbuds make sun over time.", 5)
            self.say("Now place a Shooter to defend.", 6)
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
        # gentle sun trickle for tutorial
        if random.random() < dt*0.32:
            x = random.randint(LAWN_X, LAWN_X+LAWN_W-28)
            self.game.suns.append(Sun(x, LAWN_Y, 25))

    def draw(self, surf):
        # neighbor chat at bottom-left
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
        self.buttons.append(Button(pygame.Rect(cx, cy, 240, 52), "Play (Level 1)",
                                   action=self.play1, font=app.font_med))
        cy += 60
        self.buttons.append(Button(pygame.Rect(cx, cy, 240, 52), "Level Select",
                                   action=self.level_select, font=app.font_med))
        cy += 60
        self.buttons.append(Button(pygame.Rect(cx, cy, 240, 52), "Tutorial",
                                   action=self.tutorial, font=app.font_med))
        cy += 60
        self.buttons.append(Button(pygame.Rect(cx, cy, 240, 52), "Endless",
                                   action=self.endless, font=app.font_med))
        cy += 60
        self.buttons.append(Button(pygame.Rect(cx, cy, 240, 52), "Quit",
                                   action=self.quit, font=app.font_med))

    def play1(self): self.app.change_scene(GameScene(self.app, mode="level", level_index=0))
    def tutorial(self): self.app.change_scene(GameScene(self.app, tutorial=True))
    def endless(self): self.app.change_scene(GameScene(self.app, endless=True, mode="endless"))
    def level_select(self): self.app.change_scene(LevelSelect(self.app))
    def quit(self): pygame.event.post(pygame.event.Event(pygame.QUIT))

    def handle_event(self, event):
        for b in self.buttons: b.handle(event)

    def update(self, dt): pass

    def draw(self, surf):
        surf.fill(BG)
        t = self.app.font_title.render("PVZ Rebooted", True, WHITE)
        surf.blit(t, t.get_rect(center=(WIDTH//2, 100)))
        s = self.app.font_small.render("v0.0.4 — No assets. Single file. 60 FPS.", True, GREY)
        surf.blit(s, s.get_rect(center=(WIDTH//2, 132)))
        for b in self.buttons: b.draw(surf)

class LevelSelect:
    def __init__(self, app):
        self.app = app
        self.levels = 3
        self.buttons = []
        x0, y0 = 120, 160
        idx = 0
        for c in range(self.levels):
            rect = pygame.Rect(x0 + c*120, y0, 100, 60)
            i = idx
            self.buttons.append(Button(rect, f"Level {i+1}", action=lambda i=i: self.play(i), font=app.font_med))
            idx += 1
        self.back_btn = Button(pygame.Rect(14, HEIGHT-60, 160, 44), "Back", action=self.back, font=app.font_med)

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
        t = self.app.font_title.render("Level Select", True, WHITE)
        surf.blit(t, t.get_rect(center=(WIDTH//2, 100)))
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
        # Seed types
        self.seed_types = [
            SeedType("shoot", "Shooter", 100, 6.0, (96, 170, 96), lambda r,c: Shooter(r,c),
                     "Shoots peas at enemies in its lane."),
            SeedType("solar", "Solarbud", 50, 7.0, (210, 180, 80), lambda r,c: Solarbud(r,c),
                     "Generates sun over time."),
            SeedType("rock", "Rocknut", 50, 12.0, (140, 110, 80), lambda r,c: Rocknut(r,c),
                     "High-health barrier."),
        ]
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
                    # overlay buttons get first dibs if present
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
