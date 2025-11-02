#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ultra Mario 2D Bros v2.1.0 (Directional Input Fix)
--------------------------------------------------
© Samsoft 2025  •  © 1985 Nintendo (Tribute)
Eliminates left/right inversion & 'yeet' glitch by normalizing key input priority.
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
    def update(self,g,dt):
        k=pygame.key.get_pressed()
        left,right=k[pygame.K_LEFT],k[pygame.K_RIGHT]
        run=k[pygame.K_LSHIFT] or k[pygame.K_RSHIFT]

        # 🧭 Input priority filter (Right > Left)
        if right and not left: dir=1
        elif left and not right: dir=-1
        else: dir=0

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
    def update(self,dt):
        k=pygame.key.get_pressed()
        jp=k[pygame.K_SPACE] or k[pygame.K_z]
        self.jump_pressed=jp and not self._pj; self._pj=jp
        self.player.update(self,dt)
        self.cam_x=clamp(self.player.x-BASE_W//3,0,self.level.w*TILE-BASE_W)
    def draw(self,screen,surf):
        surf.fill((112,200,248))
        for y in range(self.level.h):
            for x in range(self.level.w):
                if self.level.tile(x,y)!=' ':
                    pygame.draw.rect(surf,(168,80,0),(x*TILE-int(self.cam_x),y*TILE,TILE,TILE))
        pygame.draw.rect(surf,(230,37,37),(self.player.x-int(self.cam_x),self.player.y,TILE,TILE))
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
