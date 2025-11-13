# Retro Platformer 32 — single-file pygame game
# -----------------------------------------------------------------------------
# This is an original, from-scratch platformer inspired by classic side-scrollers.
# It is NOT a reproduction of any specific commercial game, levels, art, music,
# or characters. All gameplay code and level generation herein are original.
#
# Requirements:
#   pip install pygame
#
# Run:
#   python program.py
#
# Features:
#   - Main menu + level select (1–32)
#   - 32 deterministically generated levels (increasing difficulty)
#   - Side-scrolling camera, coins, simple enemies, hazards, lives & score
#   - Single-file, no external assets (shapes + text only)
#
# Controls:
#   Arrow keys / A-D to move, Space / W / Up to jump
#   Enter = confirm (menu), Escape = quit, R = restart level
#   From main menu: L = Level Select
#
# -----------------------------------------------------------------------------

import math
import random
import sys
from dataclasses import dataclass

import pygame

# ------------------------------ Constants ------------------------------------

SCREEN_W, SCREEN_H = 960, 540
TILE = 30
FPS = 60
LEVEL_COUNT = 32
BASE_SEED = 1337

# Colors (RGB)
SKY = (138, 196, 255)
GROUND = (100, 82, 66)
BLOCK = (96, 108, 128)
COIN = (255, 207, 64)
FLAG = (60, 180, 75)
HAZARD = (220, 50, 50)
ENEMY = (230, 80, 50)
PLAYER = (60, 120, 230)
UI_FG = (20, 20, 20)
UI_BG = (250, 250, 250)

# ------------------------------ Utilities ------------------------------------

def clamp(v, a, b):
    return a if v < a else b if v > b else v

def sign(x):
    return (x > 0) - (x < 0)

# ------------------------------ Level Gen ------------------------------------

class Level:
    """
    Level made from a tile grid with the following codes:
      'X' = solid block
      '^' = floor spike (hazard)
      'C' = coin
      'E' = enemy spawn
      'F' = flag/goal
      ' ' = air
    """
    def __init__(self, level_index: int):
        self.index = level_index
        self.grid, self.wt, self.ht = self._generate(level_index)
        self.pixel_w = self.wt * TILE
        self.pixel_h = self.ht * TILE

        self.solids = []
        self.hazards = []
        self.coins = []  # list[pygame.Rect]
        self.enemies = []  # list[Enemy]
        self.flag_rect = None
        self.spawn = None

        self._bake()

    # -------------------------- generation -----------------------------------
    def _generate(self, n: int):
        # Deterministic seed per-level
        rnd = random.Random(BASE_SEED + n * 8191)

        ht = 18
        wt = 128 + (n // 4) * 6  # width grows with level
        wt = min(wt, 192)

        # empty grid
        grid = [[' ' for _ in range(wt)] for _ in range(ht)]
        gy = ht - 2  # base ground height

        # carve rolling ground with gaps
        x = 0
        while x < wt:
            # segment length 6..18, raise/lower ground sometimes
            seg_len = rnd.randint(8, 16)
            gy += rnd.choice([0, 0, 0, -1, 1])
            gy = clamp(gy, 6, ht - 3)
            # draw ground two tiles thick
            for gx in range(x, min(wt, x + seg_len)):
                # chance to leave a gap (bigger later levels)
                gap = rnd.random() < (0.05 + 0.01 * (n / LEVEL_COUNT))
                if not gap:
                    for gy2 in range(gy, ht):
                        grid[gy2][gx] = 'X'
                else:
                    # put occasional spikes in gaps
                    if rnd.random() < 0.25:
                        grid[ht - 1][gx] = '^'
            x += seg_len

        # add platforms
        platform_chance = 0.3 + 0.2 * (n / LEVEL_COUNT)
        for _ in range(int(wt * platform_chance)):
            px = rnd.randint(8, wt - 8)
            plen = rnd.randint(3, 7)
            py = rnd.randint(5, gy - 1) if gy > 6 else rnd.randint(6, 9)
            for i in range(plen):
                if 0 <= px + i < wt and 3 <= py < ht - 2:
                    grid[py][px + i] = 'X'
                    # coins above
                    if rnd.random() < 0.6:
                        if py - 1 >= 3:
                            grid[py - 1][px + i] = 'C'

        # coins on ground ridges
        for cx in range(3, wt - 3):
            if grid[gy - 1][cx] == ' ' and grid[gy][cx] == 'X' and rnd.random() < 0.15:
                grid[gy - 1][cx] = 'C'

        # enemies on flats
        last_floor_y = [None] * wt
        for cx in range(wt):
            for cy in range(ht - 1):
                if grid[cy][cx] == ' ' and grid[cy + 1][cx] == 'X':
                    last_floor_y[cx] = cy
                    break
        step = max(7, 12 - n // 3)
        for cx in range(12, wt - 12, step):
            fy = last_floor_y[cx]
            if fy is not None and rnd.random() < 0.8:
                grid[fy][cx] = 'E'

        # occasional spike rows on ground
        for cx in range(10, wt - 10):
            if grid[ht - 2][cx] == 'X' and grid[ht - 3][cx] == ' ' and rnd.random() < 0.05 + 0.02 * (n / LEVEL_COUNT):
                grid[ht - 2][cx] = '^'

        # flag near end
        fx = wt - 5
        fy = 0
        for cy in range(ht - 3):
            if grid[cy + 1][fx] == 'X' or cy + 2 == ht - 1:
                fy = cy
                break
        grid[fy][fx] = 'F'

        # ensure safe spawn
        sx = 2
        sy = 0
        for cy in range(ht):
            if grid[cy][sx] == ' ' and grid[cy + 1][sx] == 'X':
                sy = cy
                break

        return grid, wt, ht

    def _bake(self):
        # Convert codes to world objects
        for y in range(self.ht):
            for x in range(self.wt):
                c = self.grid[y][x]
                rx = x * TILE
                ry = y * TILE
                rr = pygame.Rect(rx, ry, TILE, TILE)
                if c == 'X':
                    self.solids.append(rr)
                elif c == '^':
                    self.hazards.append(rr)
                elif c == 'C':
                    self.coins.append(rr)
                elif c == 'E':
                    self.enemies.append(Enemy(rx + TILE * 0.2, ry + 2, direction=random.choice([-1, 1])))
                elif c == 'F':
                    self.flag_rect = pygame.Rect(rx, ry - TILE * 2, TILE, TILE * 3)

        # spawn near start
        sx = 2 * TILE
        # find first air above ground near x=2
        sy = 0
        for rr in sorted(self.solids, key=lambda r: r.y):
            if rr.x <= sx <= rr.right and rr.y > sy:
                sy = rr.y - TILE * 2
        self.spawn = pygame.Vector2(sx, max(0, sy))

    # ------------------------------ queries -----------------------------------

    def rects_near(self, rect, margin=90):
        # return solids near rect for cheaper checks
        mrect = rect.inflate(margin, margin)
        return [r for r in self.solids if r.colliderect(mrect)]

    def is_solid_at_pixel(self, px, py):
        if px < 0 or py < 0 or px >= self.pixel_w or py >= self.pixel_h:
            return False
        tx = int(px // TILE)
        ty = int(py // TILE)
        if 0 <= tx < self.wt and 0 <= ty < self.ht:
            return self.grid[ty][tx] == 'X'
        return False


# ------------------------------ Entities -------------------------------------

@dataclass
class Enemy:
    x: float
    y: float
    direction: int = -1
    speed: float = 1.0
    alive: bool = True

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), int(TILE * 0.9), int(TILE * 0.9))

    def update(self, level: Level):
        if not self.alive:
            return
        # patrol
        self.x += self.direction * self.speed
        r = self.rect()

        # flip on collision with wall
        for s in level.rects_near(r):
            if r.colliderect(s):
                if self.direction > 0:
                    r.right = s.left
                else:
                    r.left = s.right
                self.x, self.y = r.x, r.y
                self.direction *= -1
                break

        # flip at platform edge
        front_x = r.centerx + (self.direction * TILE // 2)
        feet_y = r.bottom + 2
        if not level.is_solid_at_pixel(front_x, feet_y):
            self.direction *= -1

@dataclass
class Player:
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    on_ground: bool = False
    facing: int = 1
    invuln_time: float = 0.0

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), int(TILE * 0.75), int(TILE * 0.9))

    def center(self):
        r = self.rect()
        return pygame.Vector2(r.centerx, r.centery)

# ------------------------------ Game -----------------------------------------

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Retro Platformer 32")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 28)
        self.bigfont = pygame.font.SysFont(None, 64)

        self.state = 'menu'  # 'menu', 'select', 'play', 'level_complete', 'game_over', 'win'
        self.level_idx = 1
        self.level: Level | None = None
        self.player: Player | None = None

        self.lives = 3
        self.score = 0
        self.camera_x = 0
        self.level_time = 0.0

        self.flash_time = 0.0  # for effects

    # ------------------------- state helpers ---------------------------------

    def start_level(self, idx: int):
        self.level_idx = int(clamp(idx, 1, LEVEL_COUNT))
        self.level = Level(self.level_idx)
        self.player = Player(self.level.spawn.x, self.level.spawn.y)
        self.camera_x = 0
        self.level_time = 0.0
        self.state = 'play'

    def restart_level(self):
        self.start_level(self.level_idx)

    def next_level(self):
        if self.level_idx >= LEVEL_COUNT:
            self.state = 'win'
        else:
            self.start_level(self.level_idx + 1)

    # ------------------------------- loop ------------------------------------

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            self.flash_time = max(0.0, self.flash_time - dt)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if self.state == 'play':
                        # quick pause->menu
                        self.state = 'menu'
                    else:
                        pygame.quit()
                        sys.exit()

                # menu interactions
                if self.state == 'menu':
                    if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self.start_level(1)
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_l:
                        self.state = 'select'

                elif self.state == 'select':
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            self.start_level(self.level_idx)
                        elif event.key == pygame.K_LEFT:
                            self.level_idx = LEVEL_COUNT if self.level_idx == 1 else self.level_idx - 1
                        elif event.key == pygame.K_RIGHT:
                            self.level_idx = 1 if self.level_idx == LEVEL_COUNT else self.level_idx + 1
                        elif event.key == pygame.K_UP:
                            self.level_idx = int(clamp(self.level_idx + 10, 1, LEVEL_COUNT))
                        elif event.key == pygame.K_DOWN:
                            self.level_idx = int(clamp(self.level_idx - 10, 1, LEVEL_COUNT))

                elif self.state == 'level_complete':
                    if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self.next_level()

                elif self.state == 'game_over':
                    if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        # reset run
                        self.lives = 3
                        self.score = 0
                        self.start_level(1)

                elif self.state == 'win':
                    if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self.state = 'menu'

            # per-state updates & draws
            if self.state == 'menu':
                self.draw_menu()
            elif self.state == 'select':
                self.draw_select()
            elif self.state == 'play':
                self.update_play(dt)
                self.draw_play()
            elif self.state == 'level_complete':
                self.draw_level_complete()
            elif self.state == 'game_over':
                self.draw_game_over()
            elif self.state == 'win':
                self.draw_win()

            pygame.display.flip()

    # ------------------------------ rendering --------------------------------

    def draw_menu(self):
        self.screen.fill(SKY)
        title = self.bigfont.render("Retro Platformer 32", True, UI_FG)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 110))

        msg1 = self.font.render("Press Enter to Start", True, UI_FG)
        msg2 = self.font.render("Press L for Level Select (1–32)", True, UI_FG)
        msg3 = self.font.render("Esc to Quit", True, UI_FG)

        self.screen.blit(msg1, (SCREEN_W // 2 - msg1.get_width() // 2, 240))
        self.screen.blit(msg2, (SCREEN_W // 2 - msg2.get_width() // 2, 270))
        self.screen.blit(msg3, (SCREEN_W // 2 - msg3.get_width() // 2, 300))

        self.draw_footer()

    def draw_select(self):
        self.screen.fill(SKY)
        title = self.bigfont.render("Select Level", True, UI_FG)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 80))

        hint = self.font.render("← → = change, ↑ ↓ = ±10, Enter = Play, Esc = Quit", True, UI_FG)
        self.screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, 140))

        box = pygame.Rect(SCREEN_W // 2 - 180, 200, 360, 120)
        pygame.draw.rect(self.screen, UI_BG, box, border_radius=12)
        pygame.draw.rect(self.screen, UI_FG, box, 2, border_radius=12)

        lv = self.bigfont.render(f"{self.level_idx:02d} / {LEVEL_COUNT:02d}", True, UI_FG)
        self.screen.blit(lv, (SCREEN_W // 2 - lv.get_width() // 2, box.centery - lv.get_height() // 2))

        self.draw_footer()

    def draw_footer(self):
        txt = self.font.render("Original single-file game (no external assets).", True, UI_FG)
        self.screen.blit(txt, (SCREEN_W // 2 - txt.get_width() // 2, SCREEN_H - 32))

    def draw_hud(self):
        hud = self.font.render(f"Level {self.level_idx}/{LEVEL_COUNT}   Lives {self.lives}   Score {self.score}   Time {int(self.level_time)}s", True, UI_FG)
        box = pygame.Rect(10, 6, hud.get_width() + 16, 28)
        pygame.draw.rect(self.screen, UI_BG, box, border_radius=6)
        pygame.draw.rect(self.screen, UI_FG, box, 2, border_radius=6)
        self.screen.blit(hud, (box.x + 8, box.y + 4))

    def draw_play(self):
        # background
        self.screen.fill(SKY)
        self.draw_parallax()

        # world draw: only visible area for speed
        cam = pygame.Rect(int(self.camera_x), 0, SCREEN_W, SCREEN_H)
        # solids
        for r in self.level.solids:
            if r.colliderect(cam):
                rr = r.move(-self.camera_x, 0)
                pygame.draw.rect(self.screen, BLOCK, rr)
        # hazards
        for r in self.level.hazards:
            if r.colliderect(cam):
                rr = r.move(-self.camera_x, 0)
                pygame.draw.rect(self.screen, HAZARD, rr)
                # draw little triangles to suggest spikes
                pts = [(rr.x, rr.bottom), (rr.centerx, rr.top + 6), (rr.right, rr.bottom)]
                pygame.draw.polygon(self.screen, (255, 120, 120), pts)

        # coins
        for cr in self.level.coins:
            if cr.width == 0:  # collected
                continue
            if cr.colliderect(cam):
                rr = cr.move(-self.camera_x, 0)
                pygame.draw.circle(self.screen, COIN, rr.center, rr.width // 2 - 4)
                pygame.draw.circle(self.screen, (255, 240, 160), rr.center, rr.width // 2 - 8)

        # flag
        if self.level.flag_rect and self.level.flag_rect.colliderect(cam):
            fr = self.level.flag_rect.move(-self.camera_x, 0)
            pygame.draw.rect(self.screen, FLAG, (fr.x + fr.w - 6, fr.y, 6, fr.h))  # pole
            pygame.draw.polygon(self.screen, FLAG, [(fr.x + fr.w - 6, fr.y + 10), (fr.x - 16, fr.y + 20), (fr.x + fr.w - 6, fr.y + 30)])

        # enemies
        for e in self.level.enemies:
            if not e.alive:
                continue
            er = e.rect()
            if er.colliderect(cam):
                rr = er.move(-self.camera_x, 0)
                pygame.draw.rect(self.screen, ENEMY, rr, border_radius=4)
                # tiny eyes
                pygame.draw.circle(self.screen, UI_BG, (rr.x + rr.w // 3, rr.y + rr.h // 3), 3)
                pygame.draw.circle(self.screen, UI_BG, (rr.x + 2 * rr.w // 3, rr.y + rr.h // 3), 3)

        # player
        pr = self.player.rect().move(-self.camera_x, 0)
        color = PLAYER if self.player.invuln_time <= 0 or (int(self.player.invuln_time * 20) % 2 == 0) else (200, 200, 255)
        pygame.draw.rect(self.screen, color, pr, border_radius=6)

        self.draw_hud()

        # flash on hurt
        if self.flash_time > 0.0:
            alpha = int(180 * self.flash_time)
            s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            s.fill((255, 255, 255, alpha))
            self.screen.blit(s, (0, 0))

        # tip
        tip = self.font.render("R = restart", True, UI_FG)
        self.screen.blit(tip, (SCREEN_W - tip.get_width() - 10, SCREEN_H - 26))

    def draw_parallax(self):
        # very light parallax: hills & clouds
        t = pygame.time.get_ticks() / 1000.0
        # hills
        for i, hcol in enumerate([(180, 220, 170), (150, 200, 150)]):
            y = SCREEN_H - 60 - i * 20
            for x in range(-200, SCREEN_W + 200, 160):
                ox = int((-self.camera_x * (0.2 + 0.1 * i)) % 160)
                pygame.draw.ellipse(self.screen, hcol, (x + ox, y, 220, 120))

        # clouds
        for i in range(6):
            base_x = (i * 220) - int(self.camera_x * 0.1) + int((math.sin(t * 0.2 + i) * 20))
            base_y = 60 + (i % 3) * 40
            pygame.draw.ellipse(self.screen, (255, 255, 255), (base_x, base_y, 90, 40))
            pygame.draw.ellipse(self.screen, (255, 255, 255), (base_x + 30, base_y - 10, 70, 35))
            pygame.draw.ellipse(self.screen, (255, 255, 255), (base_x + 60, base_y + 5, 60, 30))

    def draw_level_complete(self):
        self.screen.fill(SKY)
        txt = self.bigfont.render("Level Complete!", True, UI_FG)
        self.screen.blit(txt, (SCREEN_W // 2 - txt.get_width() // 2, 160))

        p = self.font.render(f"Score +500   Total: {self.score}", True, UI_FG)
        self.screen.blit(p, (SCREEN_W // 2 - p.get_width() // 2, 230))

        h = self.font.render("Press Enter for next level", True, UI_FG)
        self.screen.blit(h, (SCREEN_W // 2 - h.get_width() // 2, 270))

    def draw_game_over(self):
        self.screen.fill(SKY)
        txt = self.bigfont.render("Game Over", True, UI_FG)
        self.screen.blit(txt, (SCREEN_W // 2 - txt.get_width() // 2, 180))
        h = self.font.render("Press Enter to return to Level 1", True, UI_FG)
        self.screen.blit(h, (SCREEN_W // 2 - h.get_width() // 2, 260))

    def draw_win(self):
        self.screen.fill(SKY)
        txt = self.bigfont.render("You cleared all 32 levels!", True, UI_FG)
        self.screen.blit(txt, (SCREEN_W // 2 - txt.get_width() // 2, 160))
        h = self.font.render("Press Enter to return to the Main Menu", True, UI_FG)
        self.screen.blit(h, (SCREEN_W // 2 - h.get_width() // 2, 240))

    # ------------------------------ gameplay ----------------------------------

    def update_play(self, dt: float):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_r]:
            self.restart_level()
            return

        p = self.player
        lvl = self.level
        self.level_time += dt
        p.invuln_time = max(0.0, p.invuln_time - dt)

        # input
        move = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move += 1
        p.facing = move if move != 0 else p.facing

        # horizontal velocity
        accel = 0.08 * TILE
        max_speed = 4.0
        p.vx += accel * move
        if move == 0:
            p.vx *= 0.85  # friction
        p.vx = clamp(p.vx, -max_speed, max_speed)

        # gravity
        p.vy += 0.35
        p.vy = clamp(p.vy, -20, 20)

        # jump
        jump_pressed = keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]
        if jump_pressed and p.on_ground:
            p.vy = -7.8
            p.on_ground = False

        # move X then Y with collision
        r = p.rect()

        # X
        r.x += int(p.vx)
        collided = False
        for s in lvl.rects_near(r):
            if r.colliderect(s):
                collided = True
                if p.vx > 0:
                    r.right = s.left
                elif p.vx < 0:
                    r.left = s.right
                p.vx = 0
        p.x, p.y = r.x, r.y

        # Y
        r.y += int(p.vy)
        p.on_ground = False
        for s in lvl.rects_near(r):
            if r.colliderect(s):
                if p.vy > 0:
                    r.bottom = s.top
                    p.on_ground = True
                elif p.vy < 0:
                    r.top = s.bottom
                p.vy = 0
        p.x, p.y = r.x, r.y

        # camera follow
        self.camera_x = clamp(p.x + r.w / 2 - SCREEN_W / 2, 0, lvl.pixel_w - SCREEN_W)

        # hazards
        pr = p.rect()
        for hz in lvl.hazards:
            if pr.colliderect(hz):
                self._hurt_or_die()
                return

        # fall out of world
        if p.y > lvl.pixel_h + 200:
            self._hurt_or_die()
            return

        # coins
        for i, cr in enumerate(lvl.coins):
            if cr.width == 0:
                continue
            if pr.colliderect(cr):
                self.score += 10
                lvl.coins[i] = pygame.Rect(0, 0, 0, 0)  # mark collected

        # enemies
        stomped = False
        for e in lvl.enemies:
            if not e.alive:
                continue
            e.update(lvl)
            er = e.rect()
            if pr.colliderect(er):
                # stomp?
                if p.vy > 1.0 and pr.bottom - er.top < TILE * 0.5:
                    e.alive = False
                    p.vy = -6.5
                    self.score += 100
                    stomped = True
                elif p.invuln_time <= 0.0:
                    self._hurt_or_die()
                    return
        if stomped:
            self.flash_time = 0.15

        # flag (level end)
        if lvl.flag_rect and pr.colliderect(lvl.flag_rect):
            self.score += 500
            self.state = 'level_complete'

    def _hurt_or_die(self):
        if self.lives > 1:
            self.lives -= 1
            self.player.invuln_time = 1.2
            # reset to spawn and camera
            self.player.x, self.player.y = self.level.spawn.x, self.level.spawn.y
            self.player.vx = self.player.vy = 0
            self.camera_x = clamp(self.player.x - SCREEN_W / 2, 0, self.level.pixel_w - SCREEN_W)
            self.flash_time = 0.4
        else:
            self.state = 'game_over'


def main():
    Game().run()


if __name__ == "__main__":
    main()
