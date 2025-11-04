"""
pvz rebooted 0.1  —  a single-file lane-defense prototype built with pygame

Copyright (c) 2025
Author: You + ChatGPT (original code)

License: MIT License (feel free to tinker/ship your own art+name later)

DISCLAIMER
----------
This is an original prototype inspired by general lane-defense mechanics.
It contains NO copyrighted Plants vs. Zombies assets or content. All visuals are
simple shapes; all names are generic. If you distribute this, please keep it
originally branded and use your own assets.

HOW TO PLAY
-----------
- Click a card on the top bar to select a plant type, then click a lawn tile to
  place it (if you can afford the sun cost & the card is off cooldown).
- Click falling SUN ORBS to collect +25 sun each.
- Right-click a placed plant to shovel it (partial refund).
- Survive the wave: if any enemy reaches the far left, you lose. Clear the
  remaining enemies after the wave finishes to win.

KEYS
----
P = Pause / Unpause
R = Restart
ESC = Quit

Tested with: Python 3.11 + pygame 2.5.
"""

import math
import random
import sys
import pygame
from dataclasses import dataclass

# -----------------------------------------------------------------------------
# Configuration & Constants
# -----------------------------------------------------------------------------

TITLE = "pvz rebooted 0.1"
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
        self.cool = 0.0        # placement card cooldown tracked elsewhere; this is entity-local
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
                # fire if there's likely an enemy on this row (optional heuristic)
                # (We fire constantly at fire_rate; smarter checks could be added.)
                self.fire_cd = max(0.01, 1.0 / self.stats.fire_rate)
                x, y = self.midright()
                pellets.append(Pellet(self.row, x, y, self.stats.pellet_damage, self.stats.pellet_speed))
        if self.stats.generates:
            self.gen_cd -= dt
            if self.gen_cd <= 0.0:
                self.gen_cd = self.stats.gen_interval
                # spawn a sun orb gently above the plant
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
        # If gnawing and there is a target, do not move; otherwise, walk left
        if not self.gnawing:
            self.x -= self.speed * dt
        # collide with nearest plant in front
        collided = None
        zr = self.rect()
        for p in plants_row:
            if zr.colliderect(p.rect()):
                collided = p
                break
        if collided:
            self.gnawing = True
            # deal damage over time
            dead = collided.damage(self.dps * dt)
            if dead:
                plants_row.remove(collided)
                self.gnawing = False
        else:
            self.gnawing = False

        # Check left boundary (loss condition handled in game loop)
        if self.x < -self.w - 8:
            self.alive = False

    def hit(self, damage):
        self.hp -= damage
        if self.hp <= 0:
            self.alive = False


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
        self.rng = random.Random()

        self.reset()

    def reset(self):
        self.sun = STARTING_SUN
        self.time = 0.0
        self.running = True
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
    # Core loop
    # -----------------------------------
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            if not self.paused:
                self.update(dt)
            self.draw()
        pygame.quit()

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    self.running = False
                elif e.key == pygame.K_r:
                    self.reset()
                elif e.key == pygame.K_p:
                    if self.state == "playing":
                        self.paused = not self.paused
            elif e.type == pygame.MOUSEBUTTONDOWN:
                if self.state != "playing":
                    # Any click during end screen: restart
                    self.reset()
                    return
                if e.button == 1:
                    self.on_left_click(e.pos)
                elif e.button == 3:
                    self.on_right_click(e.pos)

    # -----------------------------------
    # Interactions
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
    # Update
    # -----------------------------------
    def update(self, dt):
        if self.state != "playing":
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
        # collide pellets with zombies in same row
        for pel in self.pellets:
            if not pel.alive:
                continue
            row_z = self.zombies[pel.row]
            hit_any = False
            for z in row_z:
                if not z.alive:
                    continue
                if pel.rect().colliderect(z.rect()):
                    z.hit(pel.damage)
                    pel.alive = False
                    hit_any = True
                    break
            # remove dead zombies immediately
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
            # accelerate spawns a bit as time passes
            if self.spawn_elapsed >= SPAWN_ACCEL_EVERY:
                self.spawn_elapsed = 0.0
                self.spawn_interval = max(SPAWN_INTERVAL_MIN, self.spawn_interval - SPAWN_ACCEL_STEP)

        # Zombies update
        lost = False
        for r in range(GRID_ROWS):
            row_z = self.zombies[r]
            if row_z:
                # Update
                for z in row_z:
                    z.update(dt, self.plants[r])
                    if z.x <= GRID_MARGIN_X - 18:  # house line
                        lost = True
                # purge dead
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
    # Draw
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
                # draw cooldown slice
                if card["cd"] > 0:
                    frac = clamp(card["cd"] / stats.cooldown, 0, 1)
                    cd_h = int(rect.h * frac)
                    pygame.draw.rect(overlay, (0, 0, 0, 110), (0, rect.h - cd_h, rect.w, cd_h))
                surf.blit(overlay, rect.topleft)

            # Selection highlight
            if self.selected_card is card:
                pygame.draw.rect(surf, (255, 255, 255), rect, 3, border_radius=10)

        # Tips line
        tips = "Left-click card→tile to place | Click sun orbs | Right-click plant to shovel (partial refund) | P pause, R restart"
        tips_s = self.font_small.render(tips, True, TEXT_DIM)
        surf.blit(tips_s, (20, UI_BAR_H - 20))

    def draw_entities(self, surf):
        # Plants
        for r in range(GRID_ROWS):
            for p in self.plants[r]:
                rect = p.rect()
                # body
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
        # tint
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 130))
        surf.blit(overlay, (0, 0))

        t = self.font_big.render(msg, True, color)
        surf.blit(t, (SCREEN_W // 2 - t.get_width() // 2, SCREEN_H // 2 - 30))

    def draw_pause(self, surf):
        if not self.paused or self.state != "playing":
            return
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill(PAUSE_TINT)
        surf.blit(overlay, (0, 0))
        t = self.font_big.render("PAUSED", True, (230, 230, 240))
        surf.blit(t, (SCREEN_W // 2 - t.get_width() // 2, SCREEN_H // 2 - 26))

    def draw(self):
        self.screen.fill(BG)
        self.draw_grid(self.screen)
        self.draw_entities(self.screen)
        self.draw_ui(self.screen)
        self.draw_state_overlay(self.screen)
        self.draw_pause(self.screen)
        pygame.display.flip()


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
