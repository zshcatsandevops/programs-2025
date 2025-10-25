#!/usr/bin/env python3
"""
Ultra Mario 2D Bros — Somari PC Edition
---------------------------------------
• 1990 id Software–style Carmack scrolling (tile-dirty buffer)
• SMW-in-NES PPU shading (procedural 8×8 tiles)
• Somari-style hybrid physics (momentum + Mario jump)
• Synth APU (square + noise)
• No external files — pure Pygame 3.11+
---------------------------------------
Controls:
  ←/→  Move   ↑/SPACE  Jump   ↓  Spin-dash
  R Restart   ESC Quit
"""

import math, random, sys, pygame
from array import array

# =========================================================
# CONFIG
# =========================================================
SCALE, BASE_TILE = 3, 8
TILE_PIX = BASE_TILE * SCALE
SCREEN_WIDTH, SCREEN_HEIGHT = 600, 400
FPS = 60

# physics
GRAVITY = 0.8
MOVE_ACCEL = 0.5
MOVE_FRICTION = 0.8
JUMP_STRENGTH = -14
MAX_SPEED_X = 8
MAX_FALL_SPEED = 15

# colors
SKY_BLUE = (107, 140, 255)
BROWN = (139, 69, 19)
RED = (255, 80, 60)

# =========================================================
# INIT
# =========================================================
pygame.init()
AUDIO_ENABLED = True
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
except Exception:
    AUDIO_ENABLED = False

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Ultra Mario 2D Bros — Somari PC Edition")
clock = pygame.time.Clock()

# =========================================================
# PPU — NES Tile Renderer with SMW Shading
# =========================================================
class PPU:
    def __init__(self, scale=SCALE):
        self.scale = scale
        self.tile_pix = BASE_TILE * scale
        self._cache = {}

    def tile_surface(self, tid, shade=1):
        key = (tid, shade)
        if key in self._cache:
            return self._cache[key]
        base = [(0,0,0),(100,60,20),(160,100,40),(220,180,120)]
        sky  = [(70,130,255),(130,190,255),(180,220,255),(255,255,255)]
        pal = sky if tid==0 else base
        surf = pygame.Surface((self.tile_pix, self.tile_pix))
        rng = random.Random(tid*9973)
        for y in range(8):
            for x in range(8):
                c = pal[min(3,int(rng.randint(0,3)*shade/1.5))]
                pygame.draw.rect(surf,c,(x*self.scale,y*self.scale,self.scale,self.scale))
        self._cache[key] = surf
        return surf

# =========================================================
# APU Synth
# =========================================================
class APU:
    def __init__(self):
        self.enabled = AUDIO_ENABLED
        if not self.enabled: return
        self.ch = pygame.mixer.Channel(0)
        self.jump = self._tone(220,440,0.12)
        self.spin = self._noise(100)

    def _tone(self,f1,f2,dur):
        sr=22050; buf=array('h')
        for i in range(int(sr*dur)):
            f=f1+(f2-f1)*(1-i/(sr*dur))
            s=int(math.sin(2*math.pi*f*i/sr)*16000)
            buf.extend((s,s))
        return pygame.mixer.Sound(buffer=buf.tobytes())

    def _noise(self,ms,vol=0.3):
        n=int(22050*ms/1000); buf=array('h'); amp=int(32767*vol); reg=1
        for _ in range(n):
            bit=(reg^(reg>>1))&1; reg=(reg>>1)|(bit<<14)
            v=amp if reg&1 else -amp; buf.extend((v,v))
        return pygame.mixer.Sound(buffer=buf.tobytes())

    def play_jump(self): 
        if self.enabled: self.ch.play(self.jump)
    def play_spin(self): 
        if self.enabled: self.ch.play(self.spin)

# =========================================================
# SOMARI PLAYER
# =========================================================
class Somari:
    def __init__(self,x,y):
        self.rect = pygame.Rect(x,y,TILE_PIX,TILE_PIX*2)
        self.vel_x=self.vel_y=0
        self.on_ground=False
        self.spin_mode=False
        self.facing_right=True

    def handle_input(self,keys,apu):
        ax=0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            ax=-MOVE_ACCEL; self.facing_right=False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            ax= MOVE_ACCEL; self.facing_right=True
        if keys[pygame.K_DOWN]:
            self.spin_mode=True; apu.play_spin()
        else:
            self.spin_mode=False
        if (keys[pygame.K_UP] or keys[pygame.K_SPACE]) and self.on_ground:
            self.vel_y=JUMP_STRENGTH; self.on_ground=False; apu.play_jump()

        self.vel_x += ax
        self.vel_x *= MOVE_FRICTION if self.on_ground else 0.98
        self.vel_x = max(-MAX_SPEED_X, min(MAX_SPEED_X, self.vel_x))

    def update(self,level):
        self.vel_y += GRAVITY
        if self.vel_y>MAX_FALL_SPEED: self.vel_y=MAX_FALL_SPEED
        self.rect.x += int(self.vel_x)
        self.collide(level,dx=True)
        self.rect.y += int(self.vel_y)
        self.on_ground=False
        self.collide(level,dx=False)

    def collide(self,level,dx):
        for y,row in enumerate(level.tiles):
            for x,t in enumerate(row):
                if t==1:
                    r=pygame.Rect(x*TILE_PIX,y*TILE_PIX,TILE_PIX,TILE_PIX)
                    if self.rect.colliderect(r):
                        if dx:
                            if self.vel_x>0:self.rect.right=r.left
                            elif self.vel_x<0:self.rect.left=r.right
                            self.vel_x=0
                        else:
                            if self.vel_y>0:self.rect.bottom=r.top; self.on_ground=True
                            elif self.vel_y<0:self.rect.top=r.bottom
                            self.vel_y=0

    def draw(self,surf):
        col=(255,120,60) if not self.spin_mode else (255,255,0)
        pygame.draw.rect(surf,col,self.rect)
        eye=(self.rect.centerx+(3 if self.facing_right else -3),self.rect.top+8)
        pygame.draw.circle(surf,(255,255,255),eye,2)

# =========================================================
# CARMACK SCROLLER
# =========================================================
class CarmackScroller:
    def __init__(self,ppu,level):
        self.ppu=ppu; self.level=level
        self.buffer=pygame.Surface((SCREEN_WIDTH+TILE_PIX,SCREEN_HEIGHT))
        self.prev_x=0

    def render(self,surf,cam_x):
        dx=int(cam_x-self.prev_x)
        if dx==0:
            surf.blit(self.buffer,(0,0)); return
        self.buffer.scroll(-dx,0)
        # right scroll draw new columns
        if dx>0:
            cols=(dx+TILE_PIX-1)//TILE_PIX
            start=int((cam_x+SCREEN_WIDTH)//TILE_PIX)
            for i in range(cols):
                x=start+i
                for y,row in enumerate(self.level.tiles):
                    if 0<=x<len(row) and row[x]==1:
                        t=self.ppu.tile_surface(1)
                        self.buffer.blit(t,(x*TILE_PIX-cam_x+self.buffer.get_width()-TILE_PIX, y*TILE_PIX))
        self.prev_x=cam_x
        surf.blit(self.buffer,(0,0))

# =========================================================
# LEVEL
# =========================================================
class Level:
    def __init__(self,ppu):
        self.ppu=ppu; self.tiles=[]
        self._build()

    def _build(self):
        cols,rows=200,15
        self.tiles=[[0 for _ in range(cols)] for _ in range(rows)]
        g=rows-2
        for x in range(cols):
            self.tiles[g][x]=1
            if 10<x<15: self.tiles[g-1][x]=1
            if x%25==0 and x>0: self.tiles[g-3][x]=1

    def draw_parallax(self,surf,cam_x):
        for y in range(SCREEN_HEIGHT):
            col=(int(80+y/4),int(140+y/8),255)
            pygame.draw.line(surf,col,(0,y),(SCREEN_WIDTH,y))
        for i in range(-2,6):
            cx=i*120-(cam_x*0.5%120)
            pygame.draw.circle(surf,(0,200,80),(int(cx),SCREEN_HEIGHT-60),80)

# =========================================================
# GAME LOOP
# =========================================================
def main():
    ppu=PPU(); apu=APU(); lvl=Level(ppu)
    hero=Somari(4*TILE_PIX,SCREEN_HEIGHT-4*TILE_PIX)
    cam_x=0; scroller=CarmackScroller(ppu,lvl)
    running=True
    while running:
        dt=clock.tick(FPS)/1000
        for e in pygame.event.get():
            if e.type==pygame.QUIT or (e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE): running=False
            if e.type==pygame.KEYDOWN and e.key==pygame.K_r: hero.rect.x,hero.rect.y=(4*TILE_PIX,SCREEN_HEIGHT-4*TILE_PIX)
        keys=pygame.key.get_pressed()
        hero.handle_input(keys,apu)
        hero.update(lvl)
        cam_x=hero.rect.centerx-SCREEN_WIDTH//2
        lvl.draw_parallax(screen,cam_x)
        scroller.render(screen,cam_x)
        hero.draw(screen)
        pygame.display.flip()
    pygame.quit()

if __name__=="__main__":
    main()
