# program.py
# Ultra Mario 2D Bros HDR v0 — fixed build
# [C] 2025 Samsoft / Catsan
# Pure procedural art, no external assets.

from __future__ import annotations
import math, random, sys
from dataclasses import dataclass, field
from typing import List, Tuple
import pygame

# ────────────── CONFIG ──────────────
SCREEN = (960, 540)
GRAVITY = 0.5
PLAYER_SPEED = 5
JUMP = -12
FRAMERATE = 60

Color = Tuple[int, int, int]

# ────────────── ENTITIES ──────────────
@dataclass
class Platform:
    rect: pygame.Rect

@dataclass
class Coin:
    rect: pygame.Rect
    rotation: float = 0.0
    def update(self, dt: float): self.rotation = (self.rotation + 180 * dt) % 360
    def draw(self, surf: pygame.Surface):
        cx, cy = self.rect.center; s = self.rect.w // 2
        a = math.radians(self.rotation)
        c, s_ = math.cos(a), math.sin(a)
        pts = [(cx+c*s,cy+s_*s),(cx-s_*s,cy+c*s),(cx-c*s,cy-s_*s),(cx+s_*s,cy-c*s)]
        pygame.draw.polygon(surf,(255,215,64),pts)
        pygame.draw.polygon(surf,(255,243,173),pts,2)

@dataclass
class Enemy:
    rect: pygame.Rect; speed: float; min_x: float; max_x: float; direction: int = 1
    def update(self):
        self.rect.x += self.speed*self.direction
        if self.rect.left<=self.min_x: self.rect.left,self.direction=self.min_x,1
        elif self.rect.right>=self.max_x: self.rect.right,self.direction=self.max_x,-1
    def draw(self,surf):
        pygame.draw.rect(surf,(214,49,111),self.rect)
        e=self.rect.w//6;o=self.rect.w//4
        for side in (-1,1):
            x=self.rect.centerx+side*o; y=self.rect.centery-e
            pygame.draw.circle(surf,(255,255,255),(x,y),e)
            pygame.draw.circle(surf,(0,0,0),(x,y),e//2)
        pygame.draw.rect(surf,(249,148,0),(self.rect.x,self.rect.bottom-6,self.rect.w,6))

@dataclass
class Level:
    name:str; bg:Color
    plats:List[Platform]=field(default_factory=list)
    coins:List[Coin]=field(default_factory=list)
    enemies:List[Enemy]=field(default_factory=list)
    goal:pygame.Rect|None=None

class LevelReset(Exception): pass

# ────────────── PLAYER ──────────────
class Player:
    def __init__(self):
        self.rect=pygame.Rect(80,SCREEN[1]-180,32,48)
        self.vx=self.vy=0.0; self.on_ground=False; self.score=0
    def spawn(self,pos): self.rect.topleft=pos; self.vx=self.vy=0; self.on_ground=False
    def handle(self,keys):
        self.vx=(keys[pygame.K_RIGHT]or keys[pygame.K_d])*PLAYER_SPEED-(keys[pygame.K_LEFT]or keys[pygame.K_a])*PLAYER_SPEED
        if (keys[pygame.K_UP]or keys[pygame.K_w]or keys[pygame.K_SPACE]) and self.on_ground:
            self.vy=JUMP; self.on_ground=False
    def update(self,plats):
        self.vy=min(self.vy+GRAVITY,14)
        self.rect.x+=int(self.vx); self.collide(plats,True)
        self.rect.y+=int(self.vy); self.collide(plats,False)
        if self.rect.top>SCREEN[1]: raise LevelReset
    def collide(self,plats,hor):
        for p in plats:
            if self.rect.colliderect(p.rect):
                if hor:
                    if self.vx>0:self.rect.right=p.rect.left
                    elif self.vx<0:self.rect.left=p.rect.right
                    self.vx=0
                else:
                    if self.vy>0:self.rect.bottom=p.rect.top; self.on_ground=True
                    elif self.vy<0:self.rect.top=p.rect.bottom
                    self.vy=0
    def draw(self,s):
        pygame.draw.rect(s,(73,158,255),self.rect)
        pygame.draw.rect(s,(255,255,255),self.rect.inflate(-16,-16),2)
        pygame.draw.rect(s,(244,72,66),(self.rect.x+4,self.rect.y-8,self.rect.w-8,10))

# ────────────── GAME CORE ──────────────
class UltraMario:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Ultra Mario 2D Bros HDR v0")
        self.screen=pygame.display.set_mode(SCREEN)
        self.clock=pygame.time.Clock()
        f=lambda s,b=False:pygame.font.SysFont("arial",s,b)
        self.fL,self.fM,self.fS=f(48,1),f(32),f(24)
        self.levels=self.make_lvls()
        self.player=Player()
        self.state="menu"; self.idx=0; self.timer=0; self.msg=""
    # ─── LEVEL GEN ───
    def make_lvls(self)->List[Level]:
        pal=[(86,156,214),(78,182,172),(249,168,37),(244,114,208),(128,90,213),(72,202,228)]
        lvls=[]
        for i in range(32):
            bg=pal[i%len(pal)]
            plats=[Platform(pygame.Rect(0,SCREEN[1]-40,*SCREEN))]
            random.seed(i); seg=SCREEN[0]//8; base=SCREEN[1]-160
            for s in range(1,8):
                w=random.randint(100,180); x=s*seg+random.randint(-30,30); y=base-random.randint(0,160)
                plats.append(Platform(pygame.Rect(x,y,w,20)))
            coins=[]; enemies=[]
            for p in plats[1:]:
                for k in range(random.randint(1,3)):
                    c=pygame.Rect(p.rect.x+20+32*k,p.rect.y-32,20,20)
                    coins.append(Coin(c))
                if random.random()<0.5:
                    r=pygame.Rect(p.rect.x+10,p.rect.y-28,36,28)
                    mn,mx=p.rect.x+10,p.rect.right-10
                    sp=random.choice([1.5,2.5,3.0])+i*0.05
                    enemies.append(Enemy(r,sp,mn,mx))
            goal=pygame.Rect(SCREEN[0]-80,SCREEN[1]-120,48,80)
            lvls.append(Level(f"World {i//4+1}-{i%4+1}",bg,plats,coins,enemies,goal))
        return lvls
    # ─── LOOP ───
    def run(self):
        while True:
            dt=self.clock.tick(FRAMERATE)/1000
            for e in pygame.event.get():
                if e.type==pygame.QUIT: pygame.quit(); sys.exit()
                if e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE:
                    if self.state=="menu": pygame.quit(); sys.exit()
                    self.state="menu"
                if self.state=="menu" and e.type==pygame.KEYDOWN and e.key in (pygame.K_RETURN,pygame.K_SPACE): self.start()
                if self.state=="playing" and e.type==pygame.KEYDOWN and e.key==pygame.K_r: self.reset("Manual reset")
            # states
            if self.state=="menu": self.menu()
            elif self.state=="playing": self.update(dt); self.draw()
            elif self.state=="trans": self.timer-=dt; (self.next() if self.timer<=0 else self.trans())
            elif self.state=="done": self.done()
            pygame.display.flip()
    # ─── DRAWERS ───
    def menu(self):
        s=self.screen; s.fill((24,24,48))
        s.blit(self.fL.render("Ultra Mario 2D Bros HDR",1,(255,255,255)),(180,180))
        s.blit(self.fM.render("Press Enter to Begin",1,(255,203,107)),(300,260))
        s.blit(self.fS.render("All visuals procedural – no assets",1,(180,180,220)),(260,320))
    def trans(self):
        lvl=self.levels[self.idx]; self.screen.fill(lvl.bg)
        t=self.fM.render(self.msg,1,(0,0,0))
        self.screen.blit(t,t.get_rect(center=(SCREEN[0]//2,SCREEN[1]//2)))
    def done(self):
        s=self.screen; s.fill((20,18,68))
        s.blit(self.fL.render("Congratulations!",1,(255,255,255)),(260,180))
        s.blit(self.fM.render(f"Final Score: {self.player.score}",1,(255,203,107)),(330,260))
        s.blit(self.fS.render("Press Enter to replay",1,(200,200,200)),(340,320))
        if any(pygame.key.get_pressed()[k] for k in (pygame.K_RETURN,pygame.K_SPACE)): self.start()
    def draw(self):
        lvl=self.levels[self.idx]; s=self.screen; s.fill(lvl.bg)
        for p in lvl.plats: pygame.draw.rect(s,(74,74,74),p.rect); pygame.draw.rect(s,(169,169,169),p.rect,2)
        for c in lvl.coins:c.draw(s)
        for e in lvl.enemies:e.draw(s)
        if lvl.goal:self.goal(lvl.goal)
        self.player.draw(s)
        self.hud()
    def hud(self):
        s=self.fS.render(lvl:=self.levels[self.idx].name,1,(0,0,0))
        sc=self.fS.render(f"Score:{self.player.score}",1,(0,0,0))
        self.screen.blit(s,(16,12)); self.screen.blit(sc,(16,40))
    def goal(self,r):
        p=pygame.Surface((r.w,r.h),pygame.SRCALPHA)
        for i in range(r.w//2):
            c=(60+i*4,0,120+i*4,150)
            pygame.draw.ellipse(p,c,pygame.Rect(i,0,r.w-i*2,r.h),2)
        self.screen.blit(p,r)
    # ─── GAMEPLAY ───
    def update(self,dt):
        keys=pygame.key.get_pressed(); self.player.handle(keys)
        lvl=self.levels[self.idx]
        try: self.player.update(lvl.plats)
        except LevelReset: self.reset("Watch your step!"); return
        for e in lvl.enemies:
            e.update()
            if self.player.rect.colliderect(e.rect): self.reset("Bounced by baddie"); return
        for c in list(lvl.coins):
            c.update(dt)
            if self.player.rect.colliderect(c.rect): self.player.score+=50; lvl.coins.remove(c)
        if lvl.goal and self.player.rect.colliderect(lvl.goal):
            self.player.score+=500; self.msg=f"Level cleared! Score:{self.player.score}"
            self.state="trans"; self.timer=2
    # ─── STATE OPS ───
    def start(self): self.state="playing"; self.player=Player(); self.idx=0; self.load(self.levels[0])
    def next(self):
        self.idx+=1
        if self.idx>=len(self.levels): self.state="done"
        else: self.state="playing"; self.load(self.levels[self.idx])
    def reset(self,msg):
        self.msg=msg; self.timer=1.5; self.state="trans"; self.load(self.levels[self.idx])
    def load(self,lvl):
        y=min(lvl.plats[0].rect.top-48,SCREEN[1]-120) if lvl.plats else SCREEN[1]-120
        self.player.spawn((80,y))
        for e in lvl.enemies:e.direction=1

def main(): UltraMario().run()
if __name__=="__main__": main()
