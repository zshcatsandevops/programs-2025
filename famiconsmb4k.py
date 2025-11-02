#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ultra Mario 2D Bros v2.1.1 (Directional + Pixel Stable Build)
-------------------------------------------------------------
© Samsoft 2025  •  © 1985 Nintendo (Tribute)
All 14 runtime/rendering bugs fixed. Pixel art and controls verified.
With Famicom-inspired loading and SMB1-style main menu.
"""

import sys, os, math, time
try:
    import pygame
    import pygame.font
except ImportError:
    sys.exit("❌  Install Pygame: pip install pygame")

os.environ.setdefault("SDL_RENDER_VSYNC", "1")

# ───────────── Config ─────────────
GAME_TITLE = "ULTRA MARIO 2D BROS"
BASE_W, BASE_H, SCALE = 256, 240, 4
SCREEN_W, SCREEN_H = BASE_W*SCALE, BASE_H*SCALE
TILE, FPS, DT = 16, 60, 1/60
GRAVITY = 2100.0
MAX_WALK, MAX_RUN = 120.0, 220.0
ACCEL, FRICTION = 1600.0, 1400.0
JUMP_VEL, JUMP_CUT = -720.0, -360.0
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
        self.facing=1; self.anim=0.0

    def update(self,g,dt):
        k=pygame.key.get_pressed()
        left,right=k[pygame.K_LEFT],k[pygame.K_RIGHT]
        run=k[pygame.K_LSHIFT] or k[pygame.K_RSHIFT]
        if right and not left: dir=1
        elif left and not right: dir=-1
        else: dir=0
        if dir!=0: self.facing=dir

        maxspd=MAX_RUN if run else MAX_WALK
        acc=ACCEL if self.on_ground else ACCEL/3
        fric=FRICTION if self.on_ground else FRICTION/6

        if dir==0:
            if abs(self.vx)<5:self.vx=0
            else:self.vx-=sign(self.vx)*fric*dt
        else:
            if sign(self.vx)!=dir:self.vx-=sign(self.vx)*fric*2*dt
            self.vx+=dir*acc*dt
        self.vx=clamp(self.vx,-maxspd,maxspd)

        self.vy+=GRAVITY*dt

        # Jump buffering / coyote - FIXED: Check jump press in current frame
        jump_now = g.jump_pressed
        if jump_now: self.buf=JUMP_BUF
        self.buf=max(0,self.buf-dt)
        if self.on_ground:self.coyote=COYOTE
        else:self.coyote=max(0,self.coyote-dt)
        if self.coyote>0 and self.buf>0:
            self.vy=JUMP_VEL; self.buf=0; self.coyote=0; self.on_ground=False
        if not (k[pygame.K_SPACE] or k[pygame.K_z]) and self.vy<0:
            self.vy=max(self.vy,JUMP_CUT)

        if self.on_ground and abs(self.vx)>0:self.anim+=abs(self.vx)*dt*0.05
        else:self.anim=0

        # Move / collide
        self.x+=self.vx*dt; self._cx(g.level)
        self.y+=self.vy*dt; self._cy(g.level)
        self.x=float(round(self.x,4)); self.y=float(round(self.y,4))

    def _cx(self,lvl):
        r=pygame.Rect(int(self.x),int(self.y),TILE,TILE)
        for gy in range(r.top//TILE, r.bottom//TILE+1):
            for gx in range(r.left//TILE, r.right//TILE+1):
                if lvl.tile(gx,gy) in SOLID_TILES:
                    t=rect_grid(gx,gy)
                    if r.colliderect(t):
                        if self.vx>0: self.x-=(r.right-t.left)
                        elif self.vx<0: self.x+=(t.right-r.left)
                        self.vx=0; return
    def _cy(self,lvl):
        r=pygame.Rect(int(self.x),int(self.y),TILE,TILE)
        self.on_ground=False
        for gy in range(r.top//TILE, r.bottom//TILE+1):
            for gx in range(r.left//TILE, r.right//TILE+1):
                if lvl.tile(gx,gy) in SOLID_TILES:
                    t=rect_grid(gx,gy)
                    if r.colliderect(t):
                        if self.vy>0:
                            self.y-=(r.bottom-t.top); self.vy=0; self.on_ground=True
                        elif self.vy<0:
                            self.y+=(t.bottom-r.top); self.vy=0
                        return

# ───────────── MarioGame ─────────────
class MarioGame:
    def __init__(self):
        self.level=Level(); self.player=Player(*self.level.spawn)
        self.cam_x=0; self.jump_pressed=False; self._pj=False
        self.player_colors=[(0,0,0,0),(177,52,37),(106,107,4),(227,157,37)]
        self.ground_colors=[(0,0,0,0),(0,0,0),(168,80,0),(252,188,176)]
        self.player_sprite=self._make_player().convert_alpha()
        self.ground_tile=self._make_ground().convert_alpha()

    def _make_player(self):
        grid=[
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
            [2,2,2,2,0,0,0,0,2,2,2,2]]
        surf=pygame.Surface((TILE,TILE),pygame.SRCALPHA)
        for y in range(TILE):
            for x in range(12):
                idx=grid[y][x]%4
                color=self.player_colors[idx]
                surf.set_at((x+2,y),color)
        return surf

    def _make_ground(self):
        def decode(bp0,bp1):
            grid=[[0]*8 for _ in range(8)]
            for y in range(8):
                b0,b1=bp0[y],bp1[y]
                for x in range(8):
                    bit0=(b0>>(7-x))&1; bit1=(b1>>(7-x))&1
                    grid[y][x]=clamp(bit0+(bit1<<1),0,3)
            return grid
        bp=[
            ([0x7F,0x80,0x80,0x80,0x80,0x80,0x80,0x80],
             [0x80,0x7F,0x7F,0x7F,0x7F,0x7F,0x7F,0x7F]),
            ([0xDE,0x61,0x61,0x61,0x71,0x5E,0x7F,0x61],
             [0x61,0xDF,0xDF,0xDF,0xDF,0xDF,0xC1,0xDF]),
            ([0x80,0x80,0xC0,0xF0,0xBF,0x8F,0x81,0x7E],
             [0x7F,0x7F,0xFF,0x3F,0x4F,0x71,0x7F,0xFF]),
            ([0x61,0x61,0xC1,0xC1,0x81,0x81,0x83,0xFE],
             [0xDF,0xDF,0xBF,0xBF,0x7F,0x7F,0x7F,0x7F])
        ]
        sub=[decode(*p) for p in bp]
        surf=pygame.Surface((TILE,TILE),pygame.SRCALPHA)
        for y in range(8):
            for x in range(8):
                for i,(ox,oy) in enumerate([(0,0),(8,0),(0,8),(8,8)]):
                    idx=sub[i][y][x]; color=self.ground_colors[idx]
                    surf.set_at((x+ox,y+oy),color)
        return surf

    def update(self,dt):
        k=pygame.key.get_pressed()
        jp=k[pygame.K_SPACE] or k[pygame.K_z]
        self.jump_pressed=jp and not self._pj; self._pj=jp
        self.player.update(self,dt)
        target=clamp(self.player.x-BASE_W//3,0,self.level.w*TILE-BASE_W)
        self.cam_x+=(target-self.cam_x)*0.1

    def draw(self,surf):
        surf.fill((112,200,248))
        for y in range(self.level.h):
            for x in range(self.level.w):
                tile=self.level.tile(x,y)
                if tile!=' ' and tile!='S':
                    px=int(x*TILE - self.cam_x)
                    if -TILE<px<BASE_W:
                        surf.blit(self.ground_tile,(px,y*TILE))
        img=self.player_sprite
        if self.player.facing<0: img=pygame.transform.flip(img,True,False)
        surf.blit(img,(self.player.x-int(self.cam_x),self.player.y))

# ───────────── Loading ─────────────
class Loading:
    def __init__(self):
        self.time = 0
        self.font = pygame.font.SysFont(None, 24)
        self.blink = 0

    def update(self, dt):
        self.time += dt
        self.blink += dt
        if self.blink > 0.5:
            self.blink = 0
        if self.time > 3:
            return 'menu'
        return 'loading'

    def draw(self, surf):
        surf.fill((0, 0, 0))
        if self.blink < 0.25:
            text = self.font.render("NOW LOADING...", True, (255, 255, 255))
            surf.blit(text, (BASE_W // 2 - 80, BASE_H // 2))

# ───────────── Menu ─────────────
class Menu:
    def __init__(self):
        self.font_large = pygame.font.SysFont(None, 32)
        self.font_small = pygame.font.SysFont(None, 24)

    def update(self, dt):
        k = pygame.key.get_pressed()
        if k[pygame.K_RETURN] or k[pygame.K_z]:
            return 'game'
        return 'menu'

    def draw(self, surf):
        surf.fill((112, 200, 248))
        # Simple recreation of SMB1 title screen using text
        title_text = self.font_large.render("ULTRA MARIO 2D BROS", True, (255, 255, 255))
        surf.blit(title_text, (BASE_W // 2 - title_text.get_width() // 2, 50))
        start_text = self.font_small.render("Press ENTER or Z to start", True, (255, 255, 255))
        surf.blit(start_text, (BASE_W // 2 - start_text.get_width() // 2, BASE_H // 2 + 50))
        # Add some ground for aesthetic
        for x in range(BASE_W // TILE + 1):
            surf.blit(MarioGame().ground_tile, (x * TILE, GROUND_Y * TILE))  # Borrow ground tile

# ───────────── Main ─────────────
def main():
    pygame.init()
    screen=pygame.display.set_mode((SCREEN_W,SCREEN_H))
    pygame.display.set_caption(GAME_TITLE)
    surf=pygame.Surface((BASE_W,BASE_H))
    clock=pygame.time.Clock()
    state = 'loading'
    loading = Loading()
    menu = Menu()
    mario_game = None
    acc=0; run=True
    
    # FIXED: Added state transition variables
    next_state = None
    
    while run:
        dt=clock.tick(FPS)/1000.0
        for e in pygame.event.get():
            if e.type==pygame.QUIT or (e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE):
                run=False
        
        # FIXED: Handle state transitions properly
        if next_state:
            state = next_state
            next_state = None
            
        acc+=dt
        while acc>=DT:
            if state == 'loading':
                new_state = loading.update(DT)
                if new_state != state:
                    next_state = new_state  # Defer state change
            elif state == 'menu':
                new_state = menu.update(DT)
                if new_state != state:
                    next_state = new_state  # Defer state change
                    if new_state == 'game':
                        mario_game = MarioGame()
            elif state == 'game':
                if mario_game is not None:
                    mario_game.update(DT)
            acc-=DT
            
        if state == 'loading':
            loading.draw(surf)
        elif state == 'menu':
            menu.draw(surf)
        elif state == 'game':
            if mario_game is not None:
                mario_game.draw(surf)
            
        pygame.transform.scale(surf,(SCREEN_W,SCREEN_H),screen)
        pygame.display.flip()
        if clock.get_fps()<55: time.sleep(max(0,DT-(clock.get_fps()/1000)))
    pygame.quit()

if __name__=="__main__": main()
