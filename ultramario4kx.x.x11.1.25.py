#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ultra Mario 2D Bros v1.0.2 (SMB1 AUTHENTIC EDITION)
--------------------------------------------------
© Samsoft 2025 • Authentic SMB1 physics and graphics
NES-style dithering, CRT scanlines, authentic palette.
Single-file. No assets. Pure SMB1 vibe.
"""

import sys, os, math, time
try:
    import pygame
    import pygame.font
except ImportError:
    sys.exit("❌ Install Pygame: pip install pygame")

os.environ.setdefault("SDL_RENDER_VSYNC", "1")

# ───────────── Config ─────────────
GAME_TITLE = "ULTRA MARIO 2D BROS"
BASE_W, BASE_H, SCALE = 256, 240, 2
SCREEN_W, SCREEN_H = 512, 480
TILE, FPS, DT = 16, 60, 1 / 60

# ─── SMB1 AUTHENTIC PHYSICS ───
GRAVITY = 1800.0
MAX_WALK, MAX_RUN = 88.0, 142.0  # SMB1 precise values
ACCEL, FRICTION = 1200.0, 900.0  # Authentic acceleration
JUMP_VEL, JUMP_CUT = -380.0, -200.0  # SMB1 jump physics
COYOTE, JUMP_BUF = 0.08, 0.12
GROUND_Y = BASE_H // TILE - 2
SOLID_TILES = set("X?BP#")

# ─── AUTHENTIC NES SMB1 PALETTE (RGB) ───
PAL = {
    'sky':      (107, 140, 255),   # NES blue
    'ground':   (165, 82, 0),      # SMB1 brown
    'brick':    (181, 49, 33),     # SMB1 red brick
    'pipe':     (0, 156, 0),       # SMB1 pipe green
    'qblock':   (255, 173, 0),     # SMB1 question block
    'mario':    (222, 90, 49),     # Mario red
    'mario_pants': (24, 58, 165),  # Mario blue pants
    'goomba':   (165, 82, 0),      # Goomba brown
    'goomba_dark': (115, 41, 0),   # Goomba dark brown
    'coin':     (255, 205, 0),     # Gold coin
    'hud_bg':   (0, 0, 0),
    'hud_txt':  (255, 255, 255),
}

def clamp(v, a, b): return max(a, min(b, v))
def sign(v): return (v > 0) - (v < 0)
def rect_grid(x, y): return pygame.Rect(x * TILE, y * TILE, TILE, TILE)

# ───────────── Level ─────────────
class Level:
    def __init__(self):
        W, H = 200, BASE_H // TILE
        g = [[' ']*W for _ in range(H)]
        
        # Sky and ground
        for x in range(W):
            for y in range(GROUND_Y, H): 
                g[y][x] = 'X'
        
        # SMB1 1-1 inspired layout
        # Question blocks with coins
        g[9][16] = '?'; g[9][20] = '?'; g[9][22] = '?'; g[9][24] = '?'
        g[8][23] = '?'; g[6][28] = '?'; g[6][30] = '?'; g[6][32] = '?'
        
        # Brick blocks
        g[9][21] = 'B'; g[9][23] = 'B'
        g[9][25] = 'B'; g[9][27] = 'B'; g[9][29] = 'B'
        
        # Pipes (SMB1 style)
        for h in range(2): g[GROUND_Y - h][37] = 'P'
        for h in range(3): g[GROUND_Y - h][46] = 'P'
        for h in range(4): g[GROUND_Y - h][57] = 'P'
        for h in range(4): g[GROUND_Y - h][85] = 'P'
        
        # Staircase
        for i in range(5):
            for j in range(i + 1): 
                g[GROUND_Y - i][90 + j] = '#'
        
        # Goombas
        g[GROUND_Y - 1][21] = 'G'; g[GROUND_Y - 1][40] = 'G'; 
        g[GROUND_Y - 1][50] = 'G'; g[GROUND_Y - 1][65] = 'G'
        
        self.grid, self.w, self.h = g, W, H
        self.spawn = (2 * TILE, (GROUND_Y - 2) * TILE)
    
    def tile(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h: 
            return self.grid[y][x]
        return ' '

# ───────────── Player ─────────────
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
    
    def update(self, g, dt):
        k = pygame.key.get_pressed()
        left, right = k[pygame.K_LEFT], k[pygame.K_RIGHT]
        run = k[pygame.K_LSHIFT] or k[pygame.K_RSHIFT]
        
        dir = 1 if right and not left else -1 if left and not right else 0
        
        if dir != 0: 
            self.facing = dir
        
        # SMB1 authentic physics
        maxspd = MAX_RUN if run else MAX_WALK
        acc = ACCEL if self.on_ground else ACCEL / 4  # Less air control
        fric = FRICTION if self.on_ground else FRICTION / 8
        
        if dir == 0:
            # Friction when no input
            if abs(self.vx) < 5: 
                self.vx = 0
            else: 
                self.vx -= sign(self.vx) * fric * dt
        else:
            # Acceleration with directional influence
            if sign(self.vx) != dir and self.vx != 0:
                # Quick turn-around (SMB1 style)
                self.vx -= sign(self.vx) * fric * 2.5 * dt
            else:
                self.vx += dir * acc * dt
        
        self.vx = clamp(self.vx, -maxspd, maxspd)
        
        # Gravity
        self.vy += GRAVITY * dt
        
        # Jump input handling
        jump_pressed = k[pygame.K_SPACE] or k[pygame.K_z]
        
        if jump_pressed and not self.jump_held:
            self.buf = JUMP_BUF
        self.jump_held = jump_pressed
        
        self.buf = max(0, self.buf - dt)
        
        # Coyote time
        if self.on_ground:
            self.coyote = COYOTE
        else:
            self.coyote = max(0, self.coyote - dt)
        
        # Jump execution
        if self.coyote > 0 and self.buf > 0:
            self.vy = JUMP_VEL
            self.buf = 0
            self.coyote = 0
            self.on_ground = False
        
        # Variable jump height (SMB1 style)
        if not jump_pressed and self.vy < 0:
            self.vy = max(self.vy, JUMP_CUT)
        
        # Apply movement
        self.x += self.vx * dt
        self._cx(g.level)
        self.y += self.vy * dt
        self._cy(g.level)
        
        # Animation
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

# ───────────── Goomba ─────────────
class Goomba:
    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = -40.0, 0.0  # Slower SMB1 speed
        self.alive, self.on_ground = True, False
        self.anim = 0.0
    
    def update(self, lvl, dt):
        if not self.alive: 
            return
        
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

# ───────────── MarioGame ─────────────
class MarioGame:
    def __init__(self):
        self.level = Level()
        self.player = Player(*self.level.spawn)
        self.enemies = []
        self.spawn_enemies()
        self.cam_x, self.jump_pressed, self._pj = 0, False, False
        self.font = pygame.font.SysFont("Arial", 14, bold=True)
        self.time, self.timer = 400, 0
        self.sky = PAL['sky']
        
        # Create authentic SMB1 style tiles
        self.ground_tile = self.make_smb1_ground()
        self.brick_tile = self.make_smb1_brick()
        self.pipe_tile = self.make_smb1_pipe()
        self.q_tile = self.make_smb1_question_block()
        self.goomba_surf = self.make_smb1_goomba()
        self.coin = self.create_smb1_coin()
        self.mario_surf = self.make_smb1_mario()
        
        self.scanline_surf = self.make_scanlines()
    
    def make_smb1_ground(self):
        s = pygame.Surface((TILE, TILE))
        s.fill(PAL['ground'])
        # Add SMB1 ground pattern
        for y in range(TILE):
            for x in range(TILE):
                if (x + y) % 4 == 0:
                    s.set_at((x, y), (140, 70, 0))  # Lighter brown
        return s
    
    def make_smb1_brick(self):
        s = pygame.Surface((TILE, TILE))
        s.fill(PAL['brick'])
        # Brick pattern
        for y in range(TILE):
            for x in range(TILE):
                if x % 4 == 0 or y % 4 == 0:
                    s.set_at((x, y), (150, 40, 25))  # Brick lines
        return s
    
    def make_smb1_pipe(self):
        s = pygame.Surface((TILE, TILE))
        s.fill(PAL['pipe'])
        # Pipe shading
        for y in range(TILE):
            for x in range(TILE):
                if x < 2 or y < 2:
                    s.set_at((x, y), (0, 130, 0))  # Darker green
                elif x > TILE - 3 or y > TILE - 3:
                    s.set_at((x, y), (0, 180, 0))  # Lighter green
        return s
    
    def make_smb1_question_block(self):
        s = pygame.Surface((TILE, TILE))
        s.fill(PAL['qblock'])
        # Question block pattern
        for y in range(TILE):
            for x in range(TILE):
                if (x + y) % 3 == 0:
                    s.set_at((x, y), (230, 160, 0))  # Lighter yellow
        # Add question mark (simplified)
        for i in range(4):
            s.set_at((TILE//2, TILE//3 + i), (0, 0, 0))
        return s
    
    def make_smb1_goomba(self):
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        # Goomba body (brown)
        pygame.draw.ellipse(s, PAL['goomba'], (2, 4, TILE-4, TILE-6))
        # Goomba underside (dark brown)
        pygame.draw.ellipse(s, PAL['goomba_dark'], (4, 6, TILE-8, TILE-10))
        # Goomba feet
        pygame.draw.rect(s, PAL['goomba_dark'], (4, TILE-4, 3, 3))
        pygame.draw.rect(s, PAL['goomba_dark'], (TILE-7, TILE-4, 3, 3))
        return s
    
    def create_smb1_coin(self):
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        # Gold coin
        pygame.draw.circle(s, PAL['coin'], (TILE//2, TILE//2), TILE//3)
        pygame.draw.circle(s, (200, 150, 0), (TILE//2, TILE//2), TILE//3 - 2)
        return s
    
    def make_smb1_mario(self):
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        # Mario's red body
        pygame.draw.rect(s, PAL['mario'], (4, 4, TILE-8, TILE-4))
        # Mario's blue pants
        pygame.draw.rect(s, PAL['mario_pants'], (4, TILE-6, TILE-8, 4))
        # Mario's cap
        pygame.draw.rect(s, PAL['mario'], (2, 2, TILE-4, 4))
        return s
    
    def make_scanlines(self):
        s = pygame.Surface((BASE_W, BASE_H), pygame.SRCALPHA)
        for y in range(BASE_H):
            alpha = 40 if y % 2 == 0 else 20
            pygame.draw.line(s, (0, 0, 0, alpha), (0, y), (BASE_W, y))
        return s
    
    def spawn_enemies(self):
        for y in range(self.level.h):
            for x in range(self.level.w):
                if self.level.grid[y][x] == 'G':
                    self.enemies.append(Goomba(x * TILE, y * TILE))
                    self.level.grid[y][x] = ' '
    
    def draw_hud(self, surf):
        pygame.draw.rect(surf, PAL['hud_bg'], (0, 0, BASE_W, TILE * 2))
        texts = [
            f"SCORE {self.player.score:06d}",
            f"COIN x{self.player.coins:02d}",
            "WORLD 1-1",
            f"TIME {self.time:03d}",
            f"LIVES {self.player.lives}"
        ]
        surf.blit(self.font.render(texts[0], 1, PAL['hud_txt']), (10, 5))
        surf.blit(self.font.render(texts[1], 1, PAL['hud_txt']), (100, 5))
        surf.blit(self.coin, (160, 5))
        surf.blit(self.font.render(texts[2], 1, PAL['hud_txt']), (190, 5))
        surf.blit(self.font.render(texts[3], 1, PAL['hud_txt']), (100, 20))
        surf.blit(self.font.render(texts[4], 1, PAL['hud_txt']), (10, 20))
    
    def update(self, dt):
        k = pygame.key.get_pressed()
        jp = k[pygame.K_SPACE] or k[pygame.K_z]
        self.jump_pressed = jp and not self._pj
        self._pj = jp
        
        # Timer
        self.timer += dt
        if self.timer >= 1.0:
            self.time = max(0, self.time - 1)
            self.timer = 0
        
        # Update player
        self.player.update(self, dt)
        
        # Update enemies and check collisions
        for e in self.enemies[:]:
            e.update(self.level, dt)
            p_rect = pygame.Rect(int(self.player.x), int(self.player.y), TILE, TILE)
            if e.alive and p_rect.colliderect(e.get_rect()):
                if self.player.vy > 0 and p_rect.bottom < e.get_rect().centery:
                    # Stomp enemy
                    e.alive = False
                    self.player.vy = -250
                    self.player.score += 100
                else:
                    # Player hit
                    self.player.lives -= 1
                    if self.player.lives <= 0:
                        return 'game_over'
                    self.player.x, self.player.y = self.level.spawn
                    self.player.vx = self.player.vy = 0
        
        # Camera follow (SMB1 style - centered)
        target = clamp(self.player.x - BASE_W // 2, 0, self.level.w * TILE - BASE_W)
        self.cam_x += (target - self.cam_x) * 0.1
        
        return 'game'
    
    def draw(self, surf):
        # Draw sky
        surf.fill(self.sky)
        
        # Draw HUD
        self.draw_hud(surf)
        
        # Draw level
        sx = int(self.cam_x // TILE) - 1
        ex = sx + BASE_W // TILE + 2
        
        for y in range(self.level.h):
            for x in range(max(0, sx), min(self.level.w, ex)):
                tx, ty = x * TILE - int(self.cam_x), y * TILE + TILE * 2
                t = self.level.tile(x, y)
                
                if t == 'X':
                    surf.blit(self.ground_tile, (tx, ty))
                elif t == '#':
                    surf.blit(self.brick_tile, (tx, ty))
                elif t == 'P':
                    surf.blit(self.pipe_tile, (tx, ty))
                elif t == '?':
                    surf.blit(self.q_tile, (tx, ty))
                elif t == 'B':
                    surf.blit(self.brick_tile, (tx, ty))
        
        # Draw player
        surf.blit(self.mario_surf, (self.player.x - int(self.cam_x), self.player.y + TILE * 2))
        
        # Draw enemies
        for e in self.enemies:
            if e.alive:
                # Simple animation
                offset = 1 if math.sin(e.anim) > 0 else 0
                surf.blit(self.goomba_surf, (e.x - int(self.cam_x), e.y + TILE * 2 + offset))
        
        # CRT effects
        surf.blit(self.scanline_surf, (0, 0))

# ───────────── States ─────────────
class Loading:
    def __init__(self): 
        self.t, self.f, self.b = 0, pygame.font.SysFont("Arial", 20, bold=True), 0
    
    def update(self, dt):
        self.t += dt
        self.b += dt
        if self.b > 0.5: 
            self.b = 0
        return 'menu' if self.t > 2 else 'loading'
    
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
        k = pygame.key.get_pressed()
        self.t += dt
        if self.t > 0.12:
            if k[pygame.K_UP]: 
                self.opt = (self.opt - 1) % 2
                self.t = 0
            elif k[pygame.K_DOWN]: 
                self.opt = (self.opt + 1) % 2
                self.t = 0
        if k[pygame.K_RETURN] or k[pygame.K_z]:
            return 'game'
        return 'menu'
    
    def draw(self, s):
        s.fill(PAL['sky'])
        title = self.f1.render("ULTRA MARIO 2D BROS", True, (255, 255, 255))
        s.blit(title, (BASE_W//2 - title.get_width()//2, 60))
        opts = ["1 PLAYER GAME", "2 PLAYER GAME"]
        for i, txt in enumerate(opts):
            color = (255, 255, 100) if i == self.opt else (255, 255, 255)
            r = self.f2.render(txt, True, color)
            s.blit(r, (BASE_W//2 - r.get_width()//2, 120 + i*30))
        arrow = self.f2.render(">", True, (255, 255, 100))
        s.blit(arrow, (BASE_W//2 - 80, 118 + self.opt*30))

class GameOver:
    def __init__(self): 
        self.t, self.f = 0, pygame.font.SysFont("Arial", 32, bold=True)
    
    def update(self, dt):
        self.t += dt
        return 'menu' if self.t > 2.5 else 'game_over'
    
    def draw(self, s):
        s.fill((0, 0, 0))
        t = self.f.render("GAME OVER", True, (255, 50, 50))
        s.blit(t, (BASE_W//2 - t.get_width()//2, BASE_H//2 - 16))

# ───────────── Main ─────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption(GAME_TITLE)
    surf = pygame.Surface((BASE_W, BASE_H))
    clock = pygame.time.Clock()
    
    state, loading, menu, over = 'loading', Loading(), Menu(), GameOver()
    game = None
    acc = 0
    run = True
    
    while run:
        dt = clock.tick(FPS) / 1000.0
        
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                run = False
        
        acc += dt
        while acc >= DT:
            if state == 'loading':
                ns = loading.update(DT)
                state = ns
            elif state == 'menu':
                ns = menu.update(DT)
                if ns != state:
                    state = ns
                    if state == 'game':
                        game = MarioGame()
            elif state == 'game':
                if game:
                    ns = game.update(DT)
                    if ns != state:
                        state = ns
            elif state == 'game_over':
                ns = over.update(DT)
                if ns != state:
                    state = ns
            acc -= DT
        
        if state == 'loading': 
            loading.draw(surf)
        elif state == 'menu': 
            menu.draw(surf)
        elif state == 'game' and game: 
            game.draw(surf)
        elif state == 'game_over': 
            over.draw(surf)
        
        # Scale to screen
        final = pygame.transform.scale(surf, (SCREEN_W, SCREEN_H))
        screen.blit(final, (0, 0))
        pygame.display.flip()
    
    pygame.quit()

if __name__ == "__main__":
    main()
