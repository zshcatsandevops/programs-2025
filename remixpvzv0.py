#!/usr/bin/env python3
"""
PyPVZ Full On-The-Fly Decomp-Style Remake (Silent HDR Edition)
--------------------------------------------------------------
A single-file procedural Plants vs Zombies-style engine.
No assets, no sounds, no external data.
Just math, Pygame, and happy chaos 🌻💀

Run:  python pypvz_full_onthefly.py
"""

import pygame, sys, random, math
from pygame.locals import *

pygame.init()
WIDTH, HEIGHT = 640, 400
FPS = 60
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("PyPVZ Full On-The-Fly v0.9")
clock = pygame.time.Clock()

# === COLORS ===========================================================
WHITE=(255,255,255); BLACK=(0,0,0)
GREEN=(80,220,80); DARKGREEN=(60,180,60)
BROWN=(139,69,19); RED=(255,60,60)
YELLOW=(255,230,80); BLUE=(60,200,255)
ORANGE=(255,165,0); GRAY=(120,120,120)
BEARD=(200,200,200)

# === CONSTANTS ========================================================
GRID_COLS, GRID_ROWS = 9, 5
CELL_W, CELL_H = 60, (HEIGHT-60)//GRID_ROWS
LAWN_X, LAWN_Y = 50, 60
SPAWN_X = LAWN_X + GRID_COLS*CELL_W + 10
HOUSE_W = 40

FONT = pygame.font.SysFont(None,20)
BIG = pygame.font.SysFont(None,42)

# === DATA TABLES ======================================================
PLANT_DATA = {
    "sunflower": dict(cost=50,recharge=7000,cooldown=10000,hp=300,action="sun"),
    "peashooter":dict(cost=100,recharge=7000,cooldown=1500,hp=300,action="shoot"),
    "wallnut":dict(cost=50,recharge=10000,cooldown=0,hp=1200,action="block"),
}
ZOMBIE_DATA = {
    "normal":dict(hp=200,speed=30,damage=0.2),
    "cone":dict(hp=400,speed=28,damage=0.25),
    "bucket":dict(hp=800,speed=26,damage=0.25)
}

# === CLASSES ==========================================================

class Pea:
    def __init__(self,x,y,row):
        self.x=x; self.y=y; self.row=row
        self.spd=300; self.dmg=20
    def update(self,dt,zombies):
        self.x += self.spd*dt
        for z in zombies:
            if z.row==self.row and abs(z.x-self.x)<15:
                z.hp -= self.dmg
                return True
        return self.x>WIDTH
    def draw(self):
        pygame.draw.circle(screen,BLUE,(int(self.x),int(self.y)),5)

class Sun:
    def __init__(self,x,y,fall=True):
        self.x=x; self.y=y; self.vy=60 if fall else 0
        self.target_y = y+random.randint(30,80)
    def update(self,dt):
        if self.vy>0 and self.y<self.target_y:
            self.y += self.vy*dt
        return False
    def draw(self):
        pygame.draw.circle(screen,YELLOW,(int(self.x),int(self.y)),10)

class Plant:
    def __init__(self,col,row,ptype):
        data=PLANT_DATA[ptype]
        self.col=col; self.row=row; self.ptype=ptype
        self.x=LAWN_X+col*CELL_W+CELL_W//2
        self.y=LAWN_Y+row*CELL_H+CELL_H//2
        self.hp=data["hp"]; self.timer=0
        self.cool=data["cooldown"]
        self.action=data["action"]
    def update(self,dt,world):
        self.timer += dt*1000
        if self.action=="shoot" and self.timer>self.cool:
            self.timer=0
            world.peas.append(Pea(self.x+20,self.y,self.row))
        elif self.action=="sun" and self.timer>self.cool+4000:
            self.timer=0
            world.suns.append(Sun(self.x,self.y-20,False))
    def draw(self):
        r=pygame.Rect(self.x-20,self.y-20,40,40)
        if self.ptype=="sunflower":
            pygame.draw.circle(screen,YELLOW,(self.x,self.y),18)
        elif self.ptype=="peashooter":
            pygame.draw.circle(screen,GREEN,(self.x,self.y),18)
            pygame.draw.circle(screen,BLUE,(self.x+12,self.y-5),5)
        else:
            pygame.draw.rect(screen,BROWN,r)
        hpbar = self.hp/PLANT_DATA[self.ptype]["hp"]
        pygame.draw.rect(screen,RED,(self.x-20,self.y+22,40,4))
        pygame.draw.rect(screen,GREEN,(self.x-20,self.y+22,int(40*hpbar),4))

class Zombie:
    def __init__(self,ptype,row):
        data=ZOMBIE_DATA[ptype]
        self.ptype=ptype; self.row=row
        self.hp=data["hp"]; self.speed=data["speed"]; self.dmg=data["damage"]
        self.x=SPAWN_X; self.y=LAWN_Y+row*CELL_H+CELL_H//2
        self.eating=None; self.etimer=0
    def update(self,dt,world):
        if self.hp<=0: return True
        if self.eating:
            self.etimer+=dt
            if self.etimer>1:
                self.etimer=0
                self.eating.hp-=self.dmg*100
                if self.eating.hp<=0:
                    world.plants.remove(self.eating)
                    self.eating=None
        else:
            self.x -= self.speed*dt
            for p in world.plants:
                if p.row==self.row and abs(p.x-self.x)<25:
                    self.eating=p; break
            if self.x<LAWN_X+HOUSE_W: world.game_over=True
        return False
    def draw(self):
        col = (200,100,50) if self.ptype=="normal" else (255,120,60) if self.ptype=="cone" else (180,180,180)
        pygame.draw.rect(screen,col,(int(self.x)-15,int(self.y)-25,30,50))
        pygame.draw.circle(screen,BLACK,(int(self.x),int(self.y)-25),5)

# === WORLD ============================================================
class World:
    def __init__(self):
        self.reset()
    def reset(self):
        self.plants=[]; self.zombies=[]; self.peas=[]; self.suns=[]
        self.sun_count=50
        self.spawn_t=0; self.spawn_cd=4
        self.wave=1; self.wave_prog=0
        self.game_over=False; self.won=False
        self.recharges={k:0 for k in PLANT_DATA}
        self.selected=None
    def update(self,dt):
        if self.game_over or self.won: return
        for k in list(self.recharges): self.recharges[k]=max(0,self.recharges[k]-dt*1000)
        # spawn suns randomly
        if random.random()<0.005: self.suns.append(Sun(random.randint(LAWN_X+40,WIDTH-80),60))
        # spawn zombies
        self.spawn_t+=dt
        if self.spawn_t>self.spawn_cd:
            self.spawn_t=0
            if self.wave_prog<self.wave*5:
                typ=random.choice(list(ZOMBIE_DATA))
                row=random.randint(0,GRID_ROWS-1)
                self.zombies.append(Zombie(typ,row))
                self.wave_prog+=1
            elif not self.zombies:
                if self.wave>=5: self.won=True
                else:
                    self.wave+=1; self.wave_prog=0; self.spawn_cd=max(1.5,self.spawn_cd-0.3)
        # update plants
        for p in list(self.plants): p.update(dt,self)
        # update zombies
        for z in list(self.zombies):
            if z.update(dt,self): self.zombies.remove(z)
        # update peas
        for pea in list(self.peas):
            if pea.update(dt,self.zombies): self.peas.remove(pea)
        # update suns
        for s in list(self.suns):
            s.update(dt)
    def draw(self):
        # lawn
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                col = GREEN if (r+c)%2==0 else DARKGREEN
                x=LAWN_X+c*CELL_W; y=LAWN_Y+r*CELL_H
                pygame.draw.rect(screen,col,(x,y,CELL_W,CELL_H))
        pygame.draw.rect(screen,BROWN,(0,LAWN_Y,HOUSE_W,HEIGHT-LAWN_Y))
        # entities
        for s in self.suns: s.draw()
        for p in self.plants: p.draw()
        for z in self.zombies: z.draw()
        for pea in self.peas: pea.draw()
        # UI
        pygame.draw.rect(screen,GRAY,(0,0,WIDTH,LAWN_Y))
        xoff=60
        for name in PLANT_DATA:
            rect=pygame.Rect(xoff,10,50,40)
            clr=GREEN if self.recharges[name]<=0 else (100,100,100)
            pygame.draw.rect(screen,clr,rect)
            txt=FONT.render(name[:4],1,BLACK); screen.blit(txt,(xoff+3,15))
            cost=FONT.render(str(PLANT_DATA[name]["cost"]),1,BLACK); screen.blit(cost,(xoff+3,30))
            xoff+=60
        screen.blit(FONT.render(f"Sun:{int(self.sun_count)}",1,BLACK),(10,10))
        screen.blit(FONT.render(f"Wave:{self.wave}/5",1,BLACK),(10,30))
        if self.game_over:
            t=BIG.render("ZOMBIES ATE YOUR BRAINS!",1,RED)
            screen.blit(t,(WIDTH//2-t.get_width()//2,HEIGHT//2-20))
        if self.won:
            t=BIG.render("LEVEL COMPLETE!",1,GREEN)
            screen.blit(t,(WIDTH//2-t.get_width()//2,HEIGHT//2-20))

# === MAIN LOOP ========================================================
def main():
    world=World()
    while True:
        dt=clock.tick(FPS)/1000.0
        for e in pygame.event.get():
            if e.type==QUIT: pygame.quit(); sys.exit()
            if e.type==MOUSEBUTTONDOWN and not world.game_over and not world.won:
                mx,my=e.pos
                # click sun
                for s in list(world.suns):
                    if (s.x-mx)**2+(s.y-my)**2<100:
                        world.sun_count+=25; world.suns.remove(s)
                # select plant
                xoff=60
                for name in PLANT_DATA:
                    rect=pygame.Rect(xoff,10,50,40)
                    if rect.collidepoint(mx,my) and world.recharges[name]<=0:
                        world.selected=name
                    xoff+=60
                # place
                if world.selected and LAWN_X<mx<SPAWN_X and LAWN_Y<my<HEIGHT:
                    col=(mx-LAWN_X)//CELL_W; row=(my-LAWN_Y)//CELL_H
                    cost=PLANT_DATA[world.selected]["cost"]
                    if world.sun_count>=cost and not any(p.col==col and p.row==row for p in world.plants):
                        world.plants.append(Plant(col,row,world.selected))
                        world.sun_count-=cost
                        world.recharges[world.selected]=PLANT_DATA[world.selected]["recharge"]
                        world.selected=None
        world.update(dt)
        screen.fill(WHITE)
        world.draw()
        pygame.display.flip()

if __name__=="__main__":
    main()
