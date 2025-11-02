#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ultra Mario 2D Bros v2.1.0 (Directional Input Fix with Pixelated Graphics)
------------------------------------------------------------------------
© Samsoft 2025  •  © 1985 Nintendo (Tribute)
Eliminates left/right inversion & 'yeet' glitch. Uses hardcoded pixel data for NES-like graphics without files.
Fixed small Mario sprite to correct pixel layout, eliminating squished appearance.
"""

import sys, os, random, math, time
try: import pygame
except ImportError: sys.exit("❌  Install Pygame: pip install pygame")

os.environ.setdefault("SDL_RENDER_VSYNC","1")

# ───────────── Config ─────────────
GAME_TITLE = "ULTRA MARIO 2D BROS"
BASE_W, BASE_H, SCALE = 256, 240, 4
SCREEN_W, SCREEN_H = BASE_W*SCALE, BASE_H*SCALE
TILE, FPS, DT = 16, 60, 1/60
GRAVITY = 2100.0
MAX_WALK, MAX_RUN = 120.0, 220.0
ACCEL, FRICTION = 1600.0, 1400.0
JUMP_VEL, JUMP_CUT = -720.0, -260.0
COYOTE, JUMP_BUF = 0.08, 0.12
GROUND_Y = BASE_H//TILE - 2
SOLID_TILES = set("XBP#FGI")

def clamp(v,a,b): return max(a,min(b,v))
def sign(v): return (v>0)-(v<0)
def rect_grid(x,y): return pygame.Rect(x*TILE,y*TILE,TILE,TILE)

# ───────────── Level ─────────────
class Level:
    def __init__(self):
        W,H = 120, BASE_H//TILE
        g = [[' ']*W for _ in range(H)]
        for x in range(W):
            for y in range(GROUND_Y,H): g[y][x]='X'
        g[GROUND_Y-1][2]='S'
        self.grid=g;self.w=W;self.h=H;self.spawn=(2*TILE,(GROUND_Y-2)*TILE)
    def tile(self,x,y):
        if 0<=x<self.w and 0<=y<self.h:return self.grid[y][x]
        return ' '

# ───────────── Player ─────────────
class Player:
    def __init__(self,x,y):
        self.x=float(x);self.y=float(y)
        self.vx=self.vy=0.0
        self.on_ground=False
        self.coyote=self.buf=0.0
        self.facing=1
        self.anim=0.0
    def update(self,g,dt):
        k=pygame.key.get_pressed()
        left,right=k[pygame.K_LEFT],k[pygame.K_RIGHT]
        run=k[pygame.K_LSHIFT] or k[pygame.K_RSHIFT]

        # 🧭 Input priority filter (Right > Left)
        if right and not left: dir=1
        elif left and not right: dir=-1
        else: dir=0

        if dir != 0: self.facing = dir

        maxspd = MAX_RUN if run else MAX_WALK
        acc = ACCEL if self.on_ground else ACCEL/3
        fric = FRICTION if self.on_ground else FRICTION/6

        # Horizontal movement (safe, stable)
        if dir==0:
            if abs(self.vx)<5: self.vx=0
            else: self.vx -= sign(self.vx)*fric*dt
        else:
            if sign(self.vx)!=dir: self.vx -= sign(self.vx)*fric*2*dt
            self.vx += dir*acc*dt
        self.vx=clamp(self.vx,-maxspd,maxspd)

        # Gravity
        self.vy += GRAVITY*dt

        # Jump buffering
        if g.jump_pressed: self.buf=JUMP_BUF
        self.buf=max(0,self.buf-dt)
        if self.on_ground: self.coyote=COYOTE
        else: self.coyote=max(0,self.coyote-dt)
        if self.coyote>0 and self.buf>0:
            self.vy=JUMP_VEL;self.buf=0;self.coyote=0;self.on_ground=False
        if not (k[pygame.K_SPACE] or k[pygame.K_z]) and self.vy<0:
            self.vy=max(self.vy,JUMP_CUT)

        # Animation (simple, no full walk cycle yet)
        if self.on_ground and abs(self.vx) > 0:
            self.anim += abs(self.vx) * dt * 0.05
        else:
            self.anim = 0

        # Move / collide
        self.x += self.vx*dt; self._cx(g.level)
        self.y += self.vy*dt; self._cy(g.level)

    def _cx(self,lvl):
        r = pygame.Rect(int(self.x),int(self.y),TILE,TILE)
        for gy in range(r.top//TILE, r.bottom//TILE+1):
            for gx in range(r.left//TILE, r.right//TILE+1):
                if lvl.tile(gx,gy) in SOLID_TILES:
                    t=rect_grid(gx,gy)
                    if r.colliderect(t):
                        if self.vx>0: self.x -= (r.right - t.left)
                        elif self.vx<0: self.x += (t.right - r.left)
                        self.vx=0; r.x=int(self.x)
    def _cy(self,lvl):
        r = pygame.Rect(int(self.x),int(self.y),TILE,TILE)
        self.on_ground=False
        for gy in range(r.top//TILE, r.bottom//TILE+1):
            for gx in range(r.left//TILE, r.right//TILE+1):
                if lvl.tile(gx,gy) in SOLID_TILES:
                    t=rect_grid(gx,gy)
                    if r.colliderect(t):
                        if self.vy>0: self.y -= (r.bottom - t.top); self.vy=0; self.on_ground=True
                        elif self.vy<0: self.y += (t.bottom - r.top); self.vy=0
                        r.y=int(self.y)

# ───────────── Game ─────────────
class Game:
    def __init__(self):
        self.level=Level()
        self.player=Player(*self.level.spawn)
        self.cam_x=0;self.jump_pressed=False;self._pj=False
        self.player_colors = [(0,0,0,0), (177,52,37), (106,107,4), (227,157,37)]  # 0=trans,1=red,2=brown,3=skin
        self.ground_colors = [(0,0,0,0), (0,0,0), (168,80,0), (252,188,176)]  # 0=trans,1=black,2=dark brown,3=light brown
        self.player_sprite = self.create_player_sprite()
        self.ground_tile = self.create_ground_tile()

    def create_player_sprite(self):
        grid = [
            [0,0,0,1,1,1,1,1,0,0,0,0],
            [0,0,1,1,1,1,1,1,1,1,1,0],
            [0,0,2,2,2,3,3,2,3,0,0,0],
            [0,2,3,2,3,3,3,2,3,3,3,0],
            [0,2,3,2,2,3,3,3,2,3,3,3],
            [0,2,2,3,3,3,3,2,2,2,2,0],
            [0,0,0,3,3,3,3,3,3,3,0,0],
            [0,0,2,2,1,2,2,2,0,0,0,0],
            [0,2,2,2,1,2,2,1,2,2,2,0],
            [2,2,2,2,1,1,1,1,2,2,2,2],
            [3,3,2,1,3,1,1,3,1,2,3,3],
            [3,3,3,1,1,1,1,1,1,3,3,3],
            [3,3,1,1,1,1,1,1,1,1,3,3],
            [0,0,1,1,1,0,0,1,1,1,0,0],
            [0,2,2,2,0,0,0,0,2,2,2,0],
            [2,2,2,2,0,0,0,0,2,2,2,2]
        ]
        surf = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        for y in range(TILE):
            for x in range(12):
                idx = grid[y][x]
                color = self.player_colors[idx]
                surf.set_at((x+2, y), color)
        return surf

    def create_ground_tile(self):
        # Bitplane data for the four 8x8 sub-tiles (ground metatile)
        # Each: 8 bytes bitplane0, 8 bytes bitplane1
        tile_b4_bp0 = [0x7F, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80]
        tile_b4_bp1 = [0x80, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F]
        tile_b5_bp0 = [0xDE, 0x61, 0x61, 0x61, 0x71, 0x5E, 0x7F, 0x61]
        tile_b5_bp1 = [0x61, 0xDF, 0xDF, 0xDF, 0xDF, 0xDF, 0xC1, 0xDF]
        tile_b6_bp0 = [0x80, 0x80, 0xC0, 0xF0, 0xBF, 0x8F, 0x81, 0x7E]
        tile_b6_bp1 = [0x7F, 0x7F, 0xFF, 0x3F, 0x4F, 0x71, 0x7F, 0xFF]
        tile_b7_bp0 = [0x61, 0x61, 0xC1, 0xC1, 0x81, 0x81, 0x83, 0xFE]
        tile_b7_bp1 = [0xDF, 0xDF, 0xBF, 0xBF, 0x7F, 0x7F, 0x7F, 0x7F]

        # Function to decode 8x8 tile to grid
        def decode_tile(bp0, bp1):
            grid = [[0 for _ in range(8)] for _ in range(8)]
            for y in range(8):
                b0 = bp0[y]
                b1 = bp1[y]
                for x in range(8):
                    bit0 = (b0 >> (7 - x)) & 1
                    bit1 = (b1 >> (7 - x)) & 1
                    grid[y][x] = bit0 + (bit1 << 1)
            return grid

        # Decode sub-tiles
        tl = decode_tile(tile_b4_bp0, tile_b4_bp1)
        tr = decode_tile(tile_b5_bp0, tile_b5_bp1)
        bl = decode_tile(tile_b6_bp0, tile_b6_bp1)
        br = decode_tile(tile_b7_bp0, tile_b7_bp1)

        # Combine to 16x16
        surf = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        for y in range(8):
            for x in range(8):
                idx = tl[y][x]
                color = self.ground_colors[idx]
                surf.set_at((x, y), color)
                idx = tr[y][x]
                color = self.ground_colors[idx]
                surf.set_at((x+8, y), color)
                idx = bl[y][x]
                color = self.ground_colors[idx]
                surf.set_at((x, y+8), color)
                idx = br[y][x]
                color = self.ground_colors[idx]
                surf.set_at((x+8, y+8), color)
        return surf

    def update(self,dt):
        k=pygame.key.get_pressed()
        jp=k[pygame.K_SPACE] or k[pygame.K_z]
        self.jump_pressed=jp and not self._pj; self._pj=jp
        self.player.update(self,dt)
        self.cam_x=clamp(self.player.x-BASE_W//3,0,self.level.w*TILE-BASE_W)
    def draw(self,screen,surf):
        surf.fill((112,200,248))  # Sky blue
        for y in range(self.level.h):
            for x in range(self.level.w):
                tile = self.level.tile(x,y)
                if tile != ' ' and tile != 'S':
                    surf.blit(self.ground_tile, (x*TILE - int(self.cam_x), y*TILE))
        # Player
        player_img = self.player_sprite.copy()
        if self.player.facing < 0:
            player_img = pygame.transform.flip(player_img, True, False)
        # For jump, could replace with jump grid, but simple: if vy <0, adjust if needed
        surf.blit(player_img, (self.player.x - int(self.cam_x), self.player.y))
        pygame.transform.scale(surf,(SCREEN_W,SCREEN_H),screen)

# ───────────── Main ─────────────
def main():
    pygame.init()
    screen=pygame.display.set_mode((SCREEN_W,SCREEN_H))
    surf=pygame.Surface((BASE_W,BASE_H))
    clock=pygame.time.Clock()
    g=Game();acc=0;run=True
    while run:
        dt=clock.tick(FPS)/1000
        for e in pygame.event.get():
            if e.type==pygame.QUIT:run=False
        acc+=dt
        while acc>=DT:
            g.update(DT); acc-=DT
        g.draw(screen,surf); pygame.display.flip()
    pygame.quit()

if __name__=="__main__": main()
