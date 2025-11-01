#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Super Mario Bros (NES-Style Emulation) v1.1.2  —  Fixed-Step 60 FPS + Item Blocks
---------------------------------------------------------------------------------
Single-file, no external assets. Pygame-only.
This build keeps your codebase and adds a true fixed-step 60 FPS loop
plus '?' blocks, brick bumps, coin pop animation, fire flower power-up,
lightweight brick debris, and a couple of QoL toggles (fullscreen, scale).

Controls (same as yours + extras):
- ←/→ : Move    Z/SPACE : Jump    X : Fire (when powered)
- P : Pause      R : Restart stage   ESC : Quit
- F11 : Fullscreen toggle            F5 : Cycle integer scale (2x–6x)

Notes:
- Still zero external art; all pixels are generated.
- If VSYNC is available, the window enables it; otherwise we fall back to
  a busy-loop limiter. Physics is fixed at exactly 60 Hz either way.
"""

import os, sys, math, random, time
try:
    import pygame  # type: ignore
except ImportError:
    sys.exit("❌  Pygame not found. Install with: pip install pygame")

# Try to encourage vsync where supported
os.environ.setdefault("SDL_RENDER_VSYNC", "1")

# ───────────── Config ─────────────
GAME_TITLE = "SUPER MARIO BROS"
BASE_W, BASE_H = 256, 240
SCALE = 3  # can be changed at runtime with F5
SCREEN_W, SCREEN_H = BASE_W * SCALE, BASE_H * SCALE
TILE, FPS_TARGET = 16, 60
PHYS_DT = 1.0 / 60.0  # true fixed-step for gameplay logic

GRAVITY = 2100.0
MAX_WALK, MAX_RUN = 120.0, 220.0
ACCEL, FRICTION = 1600.0, 1400.0
JUMP_VEL, JUMP_CUT = -720.0, -260.0
COYOTE, JUMP_BUF = 0.08, 0.12
START_LIVES, START_TIME = 3, 300
GROUND_Y = BASE_H // TILE - 2
SOLID_TILES, HARM_TILES = set("XBP#FG"), set("H")

# ───────────── Helpers ─────────────
def clamp(v, lo, hi):
    if hi < lo:
        lo, hi = hi, lo
    return max(lo, min(hi, v))

def rect_from_grid(gx, gy):
    return pygame.Rect(gx*TILE, gy*TILE, TILE, TILE)

# ───────────── Tileset ─────────────
class Tileset:
    def __init__(self):
        self.cache = {}
        self.sprite_cache = {}
        pygame.font.init()
        self.font_small = pygame.font.SysFont("Courier", 8, bold=True)
        self.font_hud   = pygame.font.SysFont("Arial",   8, bold=True)
        self.font_big   = pygame.font.SysFont("Arial",  16, bold=True)
        self._make_colors(); self._sky = self._make_sky()

    def _make_colors(self):
        self.c = {
            'brown':(168,80,0),'dark_brown':(120,64,0),'yellow':(248,184,0),
            'gray':(168,168,168),'dark_gray':(88,88,88),
            'green':(0,168,0),'dark_green':(0,104,0),
            'red':(228,0,88),'sky1':(112,200,248),'sky2':(184,232,248),
            'white':(248,248,248),'black':(0,0,0),
            'orange':(255,132,0),'leaf':(0,200,88)
        }

    def _make_sky(self):
        surf = pygame.Surface((BASE_W, BASE_H))
        for y in range(BASE_H):
            t = y / BASE_H
            col = tuple(int(self.c['sky1'][i]*(1-t)+self.c['sky2'][i]*t) for i in range(3))
            pygame.draw.line(surf, col, (0, y), (BASE_W, y))
        # clouds
        for _ in range(6):
            x = random.randint(0, BASE_W-40); y = random.randint(8, 80)
            for b in range(3):
                pygame.draw.circle(surf, self.c['white'], (x + 10*b, y + (b%2)*2), 8)
        return surf

    def sky(self): return self._sky

    def tile(self, ch):
        if ch in self.cache: return self.cache[ch]
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        c = self.c
        if ch == 'X':
            s.fill(c['brown'])
            for y in range(0, TILE, 2):
                for x in range((y//2)%2, TILE, 2): s.set_at((x,y), c['dark_brown'])
        elif ch == '#':
            s.fill(c['gray']); pygame.draw.rect(s,c['dark_gray'],(0,0,TILE,TILE),2)
        elif ch == 'B':
            s.fill((216,128,88)); pygame.draw.line(s,(168,80,0),(0,8),(TILE,8))
        elif ch == '?':
            s.fill(c['yellow'])
            t=self.font_small.render("?",1,c['brown']); s.blit(t,(8-t.get_width()//2,4))
        elif ch == 'P':
            s.fill(c['green']); pygame.draw.rect(s,c['dark_green'],(0,0,TILE,TILE),2)
        elif ch == 'F':
            pygame.draw.rect(s,c['gray'],(TILE//2-1,0,2,TILE))
        elif ch == 'G':
            s.fill(c['dark_gray'])  # used block
        elif ch == 'C':
            pygame.draw.circle(s,c['yellow'],(8,8),5)
            pygame.draw.circle(s,(200,150,0),(8,8),5,1)
        elif ch == 'H':
            s.fill(c['red'])
            for x in range(0,TILE,4):
                pygame.draw.polygon(s,c['yellow'],[(x,TILE),(x+2,TILE-6),(x+4,TILE)])
        else:
            s.fill((0,0,0,0))
        self.cache[ch]=s; return s

    def sprite(self, name):
        if name in self.sprite_cache: return self.sprite_cache[name]
        c=self.c
        if name == 'mario_small_stand':
            s = pygame.Surface((12, 16), pygame.SRCALPHA)
            grid = [
                [None, None, None, 'red', 'red', 'red', 'red', 'red', None, None, None, None],
                [None, None, 'red', 'red', 'red', 'red', 'red', 'red', 'red', 'red', 'red', None],
                [None, None, 'brown','brown','brown','yellow','yellow','brown','yellow',None,None,None],
                [None,'brown','yellow','brown','yellow','yellow','yellow','brown','yellow','yellow','yellow',None],
                [None,'brown','yellow','brown','brown','yellow','yellow','yellow','brown','yellow','yellow','yellow'],
                [None,'brown','brown','yellow','yellow','yellow','yellow','brown','brown','brown','brown',None],
                [None,None,None,'yellow','yellow','yellow','yellow','yellow','yellow','yellow',None,None],
                [None,None,'brown','brown','red','brown','brown','brown',None,None,None,None],
                [None,'brown','brown','brown','red','brown','brown','red','brown','brown','brown',None],
                ['brown','brown','brown','brown','red','red','red','red','brown','brown','brown','brown'],
                ['yellow','yellow','brown','red','yellow','red','red','yellow','red','brown','yellow','yellow'],
                ['yellow','yellow','yellow','red','red','red','red','red','red','yellow','yellow','yellow'],
                ['yellow','yellow','red','red','red','red','red','red','red','red','yellow','yellow'],
                [None,None,'red','red','red',None,None,'red','red','red',None,None],
                [None,'brown','brown','brown',None,None,None,None,'brown','brown','brown',None],
                ['brown','brown','brown','brown',None,None,None,None,'brown','brown','brown','brown'],
            ]
            for y in range(16):
                for x in range(12):
                    key = grid[y][x]
                    if key:
                        s.set_at((x,y), c[key])
            self.sprite_cache[name]=s; return s
        if name == 'flower':
            s=pygame.Surface((12,12),pygame.SRCALPHA)
            pygame.draw.circle(s,c['orange'],(6,6),5)
            pygame.draw.circle(s,c['yellow'],(6,6),3)
            pygame.draw.rect(s,c['leaf'],(5,10,2,2))
            return s
        if name == 'debris':
            s=pygame.Surface((6,6),pygame.SRCALPHA)
            s.fill((216,128,88))
            pygame.draw.rect(s,(168,80,0),(0,0,6,6),1)
            return s
        self.sprite_cache[name]=pygame.Surface((1,1), pygame.SRCALPHA)
        return self.sprite_cache[name]

# ───────────── Level ─────────────
class Level:
    def __init__(self, grid):
        self.grid = grid; self.h=len(grid); self.w=len(grid[0])
        self.spawn_x,self.spawn_y=2*TILE,(GROUND_Y-1)*TILE
        self.enemy_spawns=[]; self.goal_rects=[]
        for y,row in enumerate(grid):
            for x,ch in enumerate(row):
                if ch=='S': self.spawn_x=x*TILE; self.spawn_y=(y-1)*TILE; self._set(x,y,' ')
                elif ch=='E': self.enemy_spawns.append((x*TILE,(y-1)*TILE)); self._set(x,y,' ')
                elif ch in ('F','G'): self.goal_rects.append(rect_from_grid(x,y))
    def _set(self,x,y,ch):
        r=list(self.grid[y]); r[x]=ch; self.grid[y]=''.join(r)
    def tile(self,x,y):
        if x<0 or y<0 or y>=self.h or x>=self.w: return ' '
        return self.grid[y][x]
    def solid_cells(self,r):
        cells=[]; gx0=max(r.left//TILE,0); gy0=max(r.top//TILE,0)
        gx1=min((r.right-1)//TILE,self.w-1); gy1=min((r.bottom-1)//TILE,self.h-1)
        for gy in range(gy0,gy1+1):
            for gx in range(gx0,gx1+1):
                if self.tile(gx,gy) in SOLID_TILES: cells.append((gx,gy))
        return cells
    def harm(self,r):
        gx0=max(r.left//TILE,0); gy0=max(r.top//TILE,0)
        gx1=min((r.right-1)//TILE,self.w-1); gy1=min((r.bottom-1)//TILE,self.h-1)
        for gy in range(gy0,gy1+1):
            for gx in range(gx0,gx1+1):
                if self.tile(gx,gy) in HARM_TILES: return True
        return False
    def collect_coins_in_rect(self, r):
        collected = 0
        gx0=max(r.left//TILE,0); gy0=max(r.top//TILE,0)
        gx1=min((r.right-1)//TILE,self.w-1); gy1=min((r.bottom-1)//TILE,self.h-1)
        for gy in range(gy0,gy1+1):
            for gx in range(gx0,gx1+1):
                if self.tile(gx,gy) == 'C':
                    self._set(gx,gy,' ')
                    collected += 1
        return collected

# ───────────── Entities ─────────────
class Entity:
    def __init__(self,x,y,w,h): self.rect=pygame.Rect(x,y,w,h); self.vx=self.vy=0; self.remove=False
    def update(self,g,dt): pass
    def draw(self,g,s,cx): pass

class Player(Entity):
    def __init__(self,x,y):
        super().__init__(x,y,12,16)
        self.lives,self.coins,self.score=START_LIVES,0,0
        self.facing=True; self.on_ground=False; self.dead=False
        self.coyote=self.buf=0; self.inv=0; self.game=None  # type: ignore
        self.fire=False
    def _collide(self,g,dt):
        level=g.level
        # horizontal
        self.rect.x+=int(self.vx*dt)
        for gx,gy in level.solid_cells(self.rect):
            c=rect_from_grid(gx,gy)
            if self.vx>0 and self.rect.right>c.left:
                self.rect.right=c.left; self.vx=0
            elif self.vx<0 and self.rect.left<c.right:
                self.rect.left=c.right; self.vx=0
        # vertical
        self.rect.y+=int(self.vy*dt); self.on_ground=False
        for gx,gy in level.solid_cells(self.rect):
            c=rect_from_grid(gx,gy)
            if self.vy>0 and self.rect.bottom>c.top:
                self.rect.bottom=c.top; self.vy=0; self.on_ground=True; self.coyote=COYOTE
            elif self.vy<0 and self.rect.top<c.bottom:
                self.rect.top=c.bottom; self.vy=0
                g.bump_block(gx,gy)  # NEW: bump '?' / bricks
    def update(self,g,dt):
        if self.dead:
            self.vy+=GRAVITY*dt; self._collide(g,dt); return
        k=pygame.key.get_pressed()
        ax=0
        if k[pygame.K_LEFT]^k[pygame.K_RIGHT]:
            ax=-ACCEL if k[pygame.K_LEFT] else ACCEL
            self.facing=not k[pygame.K_LEFT]
        else:
            if abs(self.vx)<20: self.vx=0
            ax=-FRICTION if self.vx>0 else FRICTION if self.vx<0 else 0
        maxv=MAX_RUN if k[pygame.K_x] else MAX_WALK
        self.vx=clamp(self.vx+ax*dt,-maxv,maxv)
        self.coyote=max(0,self.coyote-dt); self.buf=max(0,self.buf-dt)
        if g.jump_pressed: self.buf=JUMP_BUF
        if self.buf>0 and self.coyote>0:
            self.vy=JUMP_VEL; self.buf=self.coyote=0
        if not (k[pygame.K_z] or k[pygame.K_SPACE]) and self.vy<JUMP_CUT:
            self.vy=JUMP_CUT
        if self.fire and g.shoot_pressed: spawn_fireball(self)
        self.vy+=GRAVITY*dt; self._collide(g,dt)
        # pickups & hazards
        coins = g.level.collect_coins_in_rect(self.rect)
        if coins:
            self.coins += coins
            self.score += coins*100
            if self.coins >= 100:
                self.coins -= 100
                self.lives += 1
        if g.level.harm(self.rect): self.hurt(g)
        if self.rect.top>g.level.h*TILE: self.die(g)
        for goal in g.level.goal_rects:
            if self.rect.colliderect(goal): g.win()
        self.inv=max(0,self.inv-dt)
    def hurt(self,g):
        if self.inv>0:return
        if self.fire: self.fire=False
        else: self.die(g)
        self.inv=1.2
    def die(self,g):
        if self.dead:return
        self.dead=True; self.vx=0; self.vy=-320; g.player_died()
    def draw(self,g,s,cx):
        r=self.rect.move(-cx,0)
        if self.inv>0 and int(time.time()*10)%2==0:
            return  # blink when invincible
        surf = g.tiles.sprite('mario_small_stand')
        if not self.facing:
            surf = pygame.transform.flip(surf, True, False)
        s.blit(surf, r.topleft)

class Walker(Entity):
    def __init__(self,x,y): super().__init__(x,y,16,16); self.vx=-40
    def update(self,g,dt):
        self.vy+=GRAVITY*dt*0.9; self.rect.x+=int(self.vx*dt)
        # turn on bump
        for gx,gy in g.level.solid_cells(self.rect):
            c=rect_from_grid(gx,gy)
            if self.vx>0 and self.rect.right>c.left: self.rect.right=c.left; self.vx=-40
            elif self.vx<0 and self.rect.left<c.right: self.rect.left=c.right; self.vx=40
        self.rect.y+=int(self.vy*dt)
        for gx,gy in g.level.solid_cells(self.rect):
            c=rect_from_grid(gx,gy)
            if self.vy>0 and self.rect.bottom>c.top:
                self.rect.bottom=c.top; self.vy=0
        # simple edge turn-around when about to fall
        ahead = self.rect.midbottom[0] + (8 if self.vx>0 else -8)
        gx = int(ahead//TILE); gy = int(self.rect.bottom//TILE)
        if gy < g.level.h and (gx<0 or gx>=g.level.w or g.level.tile(gx,gy) not in SOLID_TILES):
            self.vx *= -1
        if self.rect.colliderect(g.player.rect) and not g.player.inv:
            if g.player.vy>80 and g.player.rect.bottom<=self.rect.top+14:
                self.remove=True; g.player.vy=-250; g.player.score+=200
            else: g.player.hurt(g)
    def draw(self,g,s,cx):
        pygame.draw.rect(s,(168,80,0),self.rect.move(-cx,0))

class Fireball(Entity):
    def __init__(self,x,y,r=True): super().__init__(x,y,6,6); self.vx=260 if r else -260; self.vy=-60; self.life=2.0
    def update(self,g,dt):
        self.vy+=GRAVITY*dt*0.6; self.rect.x+=int(self.vx*dt); self.rect.y+=int(self.vy*dt)
        self.life-=dt
        if self.life<=0: self.remove=True
        for e in list(g.entities):
            if isinstance(e,Walker) and self.rect.colliderect(e.rect):
                e.remove=True; self.remove=True; g.player.score+=200
        for gx,gy in g.level.solid_cells(self.rect):
            c=rect_from_grid(gx,gy)
            if self.vy>0 and self.rect.bottom>c.top:
                self.rect.bottom=c.top; self.vy=-abs(self.vy)*0.6
    def draw(self,g,s,cx):
        pygame.draw.circle(s,(248,184,0),self.rect.move(-cx,0).center,3)

def spawn_fireball(p):
    now=time.time()
    if hasattr(p,"_last_fire") and now-p._last_fire<0.25:return
    p._last_fire=now
    p.game.entities.append(Fireball(p.rect.centerx+(10 if p.facing else -10),p.rect.centery,p.facing))

# NEW: Coin pop (little animation), FireFlower powerup, Mushroom-like walker, and brick debris
class CoinPop(Entity):
    def __init__(self,x,y): super().__init__(x,y,8,8); self.vy=-140; self.life=0.45
    def update(self,g,dt):
        self.life-=dt; self.rect.y+=int(self.vy*dt); self.vy+=420*dt
        if self.life<=0: self.remove=True
    def draw(self,g,s,cx):
        s.blit(g.tiles.tile('C'), self.rect.move(-cx,0))

class FireFlower(Entity):
    def __init__(self,x,y): super().__init__(x,y,12,12)
    def update(self,g,dt):
        if self.rect.colliderect(g.player.rect):
            g.player.fire=True; g.player.score+=1000; self.remove=True
    def draw(self,g,s,cx): s.blit(g.tiles.sprite('flower'), self.rect.move(-cx,0))

class Shroom(Entity):
    def __init__(self,x,y): super().__init__(x,y,12,12); self.vx=60
    def update(self,g,dt):
        self.vy+=GRAVITY*dt*0.9; self.rect.x+=int(self.vx*dt)
        for gx,gy in g.level.solid_cells(self.rect):
            c=rect_from_grid(gx,gy)
            if self.vx>0 and self.rect.right>c.left: self.rect.right=c.left; self.vx=-abs(self.vx)
            elif self.vx<0 and self.rect.left<c.right: self.rect.left=c.right; self.vx=abs(self.vx)
        self.rect.y+=int(self.vy*dt)
        for gx,gy in g.level.solid_cells(self.rect):
            c=rect_from_grid(gx,gy)
            if self.vy>0 and self.rect.bottom>c.top:
                self.rect.bottom=c.top; self.vy=0
        if self.rect.colliderect(g.player.rect):
            g.player.fire=True; g.player.score+=1000; self.remove=True
    def draw(self,g,s,cx):
        # draw like a red mushroom cap
        r=self.rect.move(-cx,0)
        pygame.draw.rect(s,(200,0,0),(r.x,r.y,12,6))
        pygame.draw.rect(s,(250,250,250),(r.x+3,r.y+2,2,2))
        pygame.draw.rect(s,(250,250,250),(r.x+7,r.y+1,2,2))
        pygame.draw.rect(s,(216,128,88),(r.x+4,r.y+6,4,6))

class Debris(Entity):
    def __init__(self,x,y,vx,vy): super().__init__(x,y,6,6); self.vx=vx; self.vy=vy
    def update(self,g,dt):
        self.vy+=GRAVITY*dt; self.rect.x+=int(self.vx*dt); self.rect.y+=int(self.vy*dt)
        if self.rect.top>BASE_H: self.remove=True
    def draw(self,g,s,cx): s.blit(g.tiles.sprite('debris'), self.rect.move(-cx,0))

# ───────────── Level Generation ─────────────
def make_level(world,stage):
    rng=random.Random(world*100+stage*11)
    w,h=120,BASE_H//TILE
    g=[" " * w for _ in range(h)]; g=list(g)
    # ground
    for x in range(w):
        for y in range(GROUND_Y,h): g[y]=g[y][:x]+'X'+g[y][x+1:]
    # start
    g[GROUND_Y-1]=g[GROUND_Y-1][:2]+'S'+g[GROUND_Y-1][3:]
    # finish pole + base
    fx=w-10
    for y in range(2,GROUND_Y-1): g[y]=g[y][:fx]+'F'+g[y][fx+1:]
    g[GROUND_Y-1]=g[GROUND_Y-1][:fx+3]+'G'+g[GROUND_Y-1][fx+4:]
    # platforms / hazards / coins / enemies / blocks
    for _ in range(12):
        px=rng.randint(6,fx-12); py=rng.randint(5,GROUND_Y-4)
        for dx in range(rng.randint(3,7)):
            if px+dx<fx-6:
                g[py]=g[py][:px+dx]+'#'+g[py][px+dx+1:]
    for _ in range(10):
        hx=rng.randint(8,fx-12)
        g[GROUND_Y-1]=g[GROUND_Y-1][:hx]+'H'+g[GROUND_Y-1][hx+1:]
    # sprinkle coins, enemies, and blocks
    for _ in range(18):
        gx=rng.randint(5,fx-10)
        r=rng.random()
        if r<0.25:
            # surprise block
            gy=rng.randint(5,GROUND_Y-4)
            g[gy]=g[gy][:gx]+'?'+g[gy][gx+1:]
        elif r<0.40:
            gy=rng.randint(5,GROUND_Y-4)
            g[gy]=g[gy][:gx]+'B'+g[gy][gx+1:]
        elif r<0.70:
            g[GROUND_Y-3]=g[GROUND_Y-3][:gx]+'C'+g[GROUND_Y-3][gx+1:]
        else:
            g[GROUND_Y-2]=g[GROUND_Y-2][:gx]+'E'+g[GROUND_Y-2][gx+1:]
    lvl=Level(g)
    return lvl

# ───────────── Game Controller ─────────────
class Game:
    def __init__(self):
        self.state="title"; self.world=self.stage=1
        self.level=None; self.player=None; self.entities=[]
        self.cam_x=0; self.time_left=START_TIME
        self.jump_pressed=self.shoot_pressed=False
        self._pj=self._ps=False
        self.tiles = Tileset()
        self.selected = 0
        self.high_score = 0
        self.scale = SCALE

    def start(self): self.load(1,1)

    def load(self,w,s):
        self.level=make_level(w,s)
        self.player=Player(self.level.spawn_x,self.level.spawn_y)
        self.player.game=self  # type: ignore
        self.entities=[Walker(x,y) for x,y in self.level.enemy_spawns]
        self.state="play"; self.time_left=START_TIME; self.cam_x=0

    def player_died(self):
        assert self.player is not None
        if self.player.lives>0:
            self.player.lives-=1; self.load(self.world,self.stage)
        else:
            self.high_score = max(self.high_score, self.player.score)
            self.state="gameover"

    def win(self):
        nxt=self.stage+1
        if nxt>4:
            self.stage=1; self.world+=1
        else: self.stage=nxt
        self.load(self.world,self.stage)

    # NEW: block bump behavior
    def bump_block(self,gx,gy):
        assert self.level and self.player
        ch=self.level.tile(gx,gy)
        above_y=gy-1
        if ch=='?':
            # convert to used block
            self.level._set(gx,gy,'G')
            # coin pop animation + immediate coin
            self.entities.append(CoinPop(gx*TILE+4, gy*TILE-6))
            self.player.coins += 1
            self.player.score += 200
            if self.player.coins>=100: self.player.coins-=100; self.player.lives+=1
            # 40% chance spawn a powerup (mushroom/flower). We'll just use shroom that grants fire.
            if random.random()<0.40:
                self.entities.append(Shroom(gx*TILE+2, (gy-1)*TILE-8))
        elif ch=='B':
            # break brick into debris if hit from below
            self.level._set(gx,gy,' ')
            for (dx,dy) in [(-60,-280),(60,-280),(-40,-200),(40,-200)]:
                self.entities.append(Debris(gx*TILE+5, gy*TILE+5, dx, dy))
            self.player.score+=50
        # other tiles ignored

    def update(self,dt):
        k=pygame.key.get_pressed()
        pressed_jump = (k[pygame.K_z] or k[pygame.K_SPACE])
        pressed_shoot = k[pygame.K_x]
        self.jump_pressed = pressed_jump and not self._pj
        self.shoot_pressed = pressed_shoot and not self._ps
        self._pj = pressed_jump; self._ps = pressed_shoot

        if self.state=="title":
            if k[pygame.K_UP]:   self.selected = 0
            if k[pygame.K_DOWN]: self.selected = 1
            if self.jump_pressed or k[pygame.K_RETURN]: self.start()
            return
        if self.state=="gameover":
            if self.jump_pressed or k[pygame.K_RETURN]: self.state="title"
            return
        if self.state=="pause":
            if self.jump_pressed or k[pygame.K_p]: self.state="play"
            return
        if self.state=="play":
            assert self.player is not None and self.level is not None
            if k[pygame.K_p]: self.state="pause"; return
            self.time_left=max(0,self.time_left-dt)
            if self.time_left<=0:
                self.player.die(self)
            self.player.update(self,dt)
            for e in list(self.entities): e.update(self,dt)
            self.entities=[e for e in self.entities if not e.remove]
            # camera (clamped)
            max_cam = max(0, self.level.w*TILE - BASE_W)
            target = int(self.player.rect.centerx - BASE_W//3)
            self.cam_x = int(clamp(target, 0, max_cam))

    def draw(self, screen, surf, fps_readout=None):
        s = surf
        s.blit(self.tiles.sky(), (0,0))
        if self.state=="title":
            self.draw_menu(s)
        elif self.state in ("play","pause","gameover"):
            self.draw_world(s)
            self.draw_hud(s, fps_readout)
            if self.state=="pause": self.draw_pause(s)
            if self.state=="gameover": self.draw_game_over(s)
        # scale up
        pygame.transform.scale(s, (BASE_W*self.scale, BASE_H*self.scale), screen)

    def draw_menu(self, s):
        s.fill(self.tiles.c['black'])
        t1 = self.tiles.font_big.render("1 PLAYER GAME", True, self.tiles.c['white'])
        t1_pos = (BASE_W//2 - t1.get_width()//2, 80)
        s.blit(t1, t1_pos)
        t2 = self.tiles.font_big.render("2 PLAYER GAME", True, self.tiles.c['white'])
        t2_pos = (BASE_W//2 - t2.get_width()//2, 110)
        s.blit(t2, t2_pos)
        t3 = self.tiles.font_hud.render(f"TOP- {self.high_score:06d}", True, self.tiles.c['white'])
        s.blit(t3, (BASE_W - t3.get_width() - 8, 8))
        # selector (mario sprite)
        sel_y = 80 if self.selected == 0 else 110
        sel_x = BASE_W//2 - t1.get_width()//2 - 20
        surf = self.tiles.sprite('mario_small_stand')
        s.blit(surf, (sel_x, sel_y))

    def draw_world(self, s):
        assert self.level is not None and self.player is not None
        cx = self.cam_x
        # tiles (cull to view)
        gx0 = max(0, cx//TILE)
        gx1 = min(self.level.w-1, (cx+BASE_W)//TILE + 1)
        for y in range(self.level.h):
            for x in range(gx0,gx1+1):
                ch = self.level.tile(x,y)
                if ch != ' ':
                    s.blit(self.tiles.tile(ch),(x*TILE - cx, y*TILE))
        # entities
        for e in self.entities:
            e.draw(self,s,cx)
        # player last (on top)
        self.player.draw(self,s,cx)

    def draw_hud(self, s, fps_readout=None):
        assert self.player is not None
        f = self.tiles.font_hud
        col = self.tiles.c['white']
        def text(tx, x, y): s.blit(f.render(tx, True, col),(x,y))
        text(f"WORLD {self.world}-{self.stage}", 8, 8)
        text(f"LIVES {self.player.lives}", 8, 18)
        text(f"COIN {self.player.coins:02d}", 100, 8)
        text(f"SCORE {self.player.score:06d}", 160, 8)
        text(f"TIME {int(self.time_left):03d}", 220, 18)
        if fps_readout is not None:
            text(f"FPS {int(fps_readout)}", 8, 28)

    def draw_pause(self, s):
        t = self.tiles.font_big.render("PAUSED", True, self.tiles.c['white'])
        s.blit(t,(BASE_W//2 - t.get_width()//2, BASE_H//2 - 8))

    def draw_game_over(self, s):
        t = self.tiles.font_big.render("GAME OVER", True, self.tiles.c['white'])
        s.blit(t,(BASE_W//2 - t.get_width()//2, BASE_H//2 - 8))
        t2 = self.tiles.font_hud.render("Press ENTER/Z to return", True, self.tiles.c['white'])
        s.blit(t2,(BASE_W//2 - t2.get_width()//2, BASE_H//2 + 12))

# ───────────── Display helpers ─────────────

def make_window(scale, vsync=True, fullscreen=False):
    flags = 0
    if fullscreen:
        flags |= pygame.FULLSCREEN
    try:
        screen = pygame.display.set_mode((BASE_W*scale, BASE_H*scale), flags, vsync=1 if vsync else 0)
    except TypeError:
        # older pygame; no vsync kw
        screen = pygame.display.set_mode((BASE_W*scale, BASE_H*scale), flags)
    pygame.display.set_caption(GAME_TITLE)
    return screen

# ───────────── Main ─────────────

def main():
    pygame.init()
    screen = make_window(SCALE, vsync=True, fullscreen=False)
    surf = pygame.Surface((BASE_W, BASE_H)).convert_alpha()
    clock = pygame.time.Clock()

    game = Game()

    # Fixed-step accumulator
    accumulator = 0.0
    last = time.perf_counter()

    running = True
    while running:
        # precise frame pacing
        now = time.perf_counter()
        frame_dt = now - last
        last = now
        # clamp to avoid spiral of death on tab-out
        if frame_dt > 0.25:
            frame_dt = 0.25
        accumulator += frame_dt

        # input/events
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running=False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running=False
                elif ev.key == pygame.K_r and game.state=="play":
                    game.load(game.world, game.stage)
                elif ev.key == pygame.K_F11:
                    # toggle fullscreen
                    fs = (screen.get_flags() & pygame.FULLSCREEN) == 0
                    screen = make_window(game.scale, vsync=True, fullscreen=fs)
                elif ev.key == pygame.K_F5:
                    # cycle scale 2..6
                    game.scale = 2 if game.scale >= 6 else game.scale + 1
                    screen = make_window(game.scale, vsync=True, fullscreen=False)

        # FIXED-STEP UPDATE @ 60 Hz
        steps = 0
        while accumulator >= PHYS_DT:
            game.update(PHYS_DT)
            accumulator -= PHYS_DT
            steps += 1
            if steps > 5:  # safety to keep up after long stall
                accumulator = 0.0
                break

        # RENDER
        fps_est = clock.get_fps()
        game.draw(screen, surf, fps_readout=fps_est)
        pygame.display.flip()

        # Busy-loop limiter toward target FPS if vsync is off
        clock.tick_busy_loop(FPS_TARGET)

    pygame.quit()

if __name__ == '__main__':
    main()
