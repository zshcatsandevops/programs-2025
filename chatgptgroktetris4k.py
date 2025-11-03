 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ultra!Tetriis — Samsoft Edition (2025)
--------------------------------------
Full-featured Tetris with OST, white Samsoft intro, NES-style fade,
and Game Boy-style menu.

© 2025 Samsoft Co.
© 1990 The Tetris Company
"""

import sys, random, time, math, collections
import numpy as np
import pygame

# ---------- Optional audio backend ----------
AUDIO_ENABLED = True
try:
    import sounddevice as sd
except Exception:
    sd = None
    AUDIO_ENABLED = False

# ---------- Synth Basics ----------
SR = 44100
def note_freq(n):
    k = {'C':-9,'C#':-8,'D':-7,'D#':-6,'E':-5,'F':-4,'F#':-3,'G':-2,'G#':-1,'A':0,'A#':1,'B':2}
    if len(n) > 1 and n[1] in '#b': name,octv = n[:2],int(n[2:])
    else: name,octv = n[:1],int(n[1:])
    return 440*(2**((k[name]+12*(octv-4))/12))

def sq(freq,dur,vol=0.4):
    n=int(SR*dur)
    t=np.linspace(0,dur,n,False)
    y=np.sign(np.sin(2*np.pi*freq*t)).astype(np.float32)
    env=np.linspace(0,1,int(SR*0.01))
    y[:len(env)]*=env
    y[-len(env):]*=env[::-1]
    return (vol*y).astype(np.float32)

def play_blip():
    if not AUDIO_ENABLED: return
    try:
        snd=np.concatenate([sq(note_freq('C5'),0.1),sq(note_freq('E5'),0.1),sq(note_freq('G5'),0.2)])
        sd.play(snd,SR,blocking=False)
    except:
        pass  # Suppress Mac AUHAL errors

def play_theme():
    if not AUDIO_ENABLED: return
    try:
        notes = [
            ('E5',0.15), ('B4',0.15), ('C5',0.15), ('D5',0.15), ('C5',0.15), ('B4',0.15), ('A4',0.15),
            ('A4',0.15), ('C5',0.15), ('E5',0.15), ('D5',0.15), ('C5',0.15), ('B4',0.15),
            ('C5',0.15), ('D5',0.15), ('E5',0.15), ('C5',0.15), ('A4',0.15), ('A4',0.15),
            ('D5',0.15), ('F5',0.15), ('A5',0.15), ('G5',0.15), ('F5',0.15), ('E5',0.15),
            ('C5',0.15), ('E5',0.15), ('D5',0.15), ('C5',0.15), ('B4',0.15),
            ('B4',0.15), ('C5',0.15), ('D5',0.15), ('E5',0.15), ('C5',0.15), ('A4',0.15), ('A4',0.15)
        ]
        snds = [sq(note_freq(n), d) for n,d in notes]
        full = np.concatenate(snds)
        sd.play(full, SR, blocking=False)
    except:
        pass  # Suppress Mac AUHAL errors

# ------------------------------
# TETRIS CORE
# ------------------------------
COLS,ROWS=10,20
BLK=30
MARG=2
W,H=COLS*BLK+200,ROWS*BLK
BG=(16,18,22)
GRID=(40,40,50)
TEXT=(240,240,245)

PIECES={
'I':["....","1111","....","...."],
'J':["1...","111.","....","...."],
'L':["..1.","111.","....","...."],
'O':[".11.",".11.","....","...."],
'S':[".11.","11..","....","...."],
'T':[".1..","111.","....","...."],
'Z':["11..",".11.","....","...."]
}
COL={'I':(0,240,240),'J':(0,80,240),'L':(240,160,0),'O':(240,240,0),
     'S':(0,240,0),'T':(160,0,240),'Z':(240,0,0)}

def cells(sh,x,y):
    for r in range(4):
        for c in range(4):
            if sh[r][c]=="1":
                yield x+c,y+r

def can(grid,sh,x,y):
    for cx,cy in cells(sh,x,y):
        if cx<0 or cx>=COLS or cy>=ROWS: return False
        if cy>=0 and grid[cy][cx] is not None: return False
    return True

def rot(sh): return [''.join(r) for r in zip(*[list(x) for x in sh[::-1]])]
def newbag(): b=list(PIECES.keys()); random.shuffle(b); return collections.deque(b)

class Piece:
    def __init__(self,n):
        self.n=n
        self.sh=PIECES[n][:]
        self.x=COLS//2-2
        self.y=-2
        self.c=COL[n]
    def mv(self,g,dx,dy):
        if can(g,self.sh,self.x+dx,self.y+dy):
            self.x+=dx;self.y+=dy
            return True
        return False
    def rot(self,g):
        r=rot(self.sh)
        for ox,oy in[(0,0),(1,0),(-1,0),(0,-1)]:
            if can(g,r,self.x+ox,self.y+oy):
                self.sh=r;self.x+=ox;self.y+=oy
                return True
        return False
    def drop(self,g):
        d=0
        while can(g,self.sh,self.x,self.y+d+1): d+=1
        return d

def clr(g):
    new=[r for r in g if any(c is None for c in r)]
    cl=ROWS-len(new)
    for _ in range(cl): new.insert(0,[None]*COLS)
    return new,cl

# ------------------------------
# DRAW HELPERS
# ------------------------------
def drawcell(s,x,y,c):
    r=pygame.Rect(x*BLK+MARG,y*BLK+MARG,BLK-2*MARG,BLK-2*MARG)
    pygame.draw.rect(s,c,r,border_radius=4)

def drawboard(s,g):
    s.fill(BG)
    for x in range(COLS+1): pygame.draw.line(s,GRID,(x*BLK,0),(x*BLK,ROWS*BLK))
    for y in range(ROWS+1): pygame.draw.line(s,GRID,(0,y*BLK),(COLS*BLK,y*BLK))
    for r in range(ROWS):
        for c in range(COLS):
            if g[r][c]: drawcell(s,c,r,g[r][c])

def text(s,tx,sz,x,y,clr=TEXT,align="center"):
    f=pygame.font.SysFont("arial",sz,bold=True)
    r=f.render(tx,True,clr)
    rect=r.get_rect(center=(x,y))
    s.blit(r,rect)

# ------------------------------
# INTRO: SAMSOFT PRESENTS
# ------------------------------
def intro(screen,clock):
    play_blip()
    t0=pygame.time.get_ticks()
    while True:
        t=(pygame.time.get_ticks()-t0)/1000.0
        if t<2:
            alpha=int(255*math.sin(t*math.pi/2))
        elif t<3:
            alpha=int(255*(1-(t-2)))
        else: break
        screen.fill((0,0,0))
        f=pygame.font.SysFont("arial",48,bold=True)
        txt=f.render("Samsoft Presents",True,(255,255,255))
        txt.set_alpha(max(0,min(255,alpha)))
        screen.blit(txt,txt.get_rect(center=(W//2,H//2)))
        pygame.display.flip()
        clock.tick(60)

# ------------------------------
# MENU
# ------------------------------
def menu(screen,clock):
    play_rect=pygame.Rect(W//2-100,H//2,200,60)
    quit_rect=pygame.Rect(W//2-100,H//2+80,200,60)
    t=0
    theme_start = time.time()
    theme_duration = 6.0  # Approximate loop interval for the theme
    while True:
        for e in pygame.event.get():
            if e.type==pygame.QUIT:return False
            if e.type==pygame.MOUSEBUTTONDOWN:
                if play_rect.collidepoint(e.pos): return True
                if quit_rect.collidepoint(e.pos): return False
        t+=0.02
        if time.time() - theme_start > theme_duration:
            play_theme()
            theme_start = time.time()
        bg=(10+5*math.sin(t),12+5*math.sin(t*1.2),16+5*math.sin(t*0.8))
        screen.fill(tuple(map(int,bg)))
        text(screen,"ULTRA!TETRIIS",72,W//2,H//2-100)
        for r,tx,clr in[(play_rect,"PLAY",(0,200,0)),(quit_rect,"QUIT",(200,0,0))]:
            h=r.collidepoint(pygame.mouse.get_pos())
            s=pygame.Surface(r.size,pygame.SRCALPHA)
            s.fill((*clr,255 if h else 150))
            screen.blit(s,r)
            text(screen,tx,28,r.centerx,r.centery)
        text(screen,"© 2025 Samsoft    © 1990 The Tetris Company",16,W//2,H-30)
        pygame.display.flip()
        clock.tick(60)

# ------------------------------
# GAME LOOP
# ------------------------------
def game(screen,clock):
    grid=[[None]*COLS for _ in range(ROWS)]
    bag=newbag()
    cur=Piece(bag.popleft())
    fall_timer=0
    fall_speed=0.5
    score=0

    while True:
        dt=clock.tick(60)/1000
        fall_timer+=dt
        for e in pygame.event.get():
            if e.type==pygame.QUIT:return False
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_ESCAPE:return True
                if e.key==pygame.K_LEFT:cur.mv(grid,-1,0)
                if e.key==pygame.K_RIGHT:cur.mv(grid,1,0)
                if e.key==pygame.K_DOWN:cur.mv(grid,0,1)
                if e.key==pygame.K_UP:cur.rot(grid)
                if e.key==pygame.K_SPACE:
                    dy=cur.drop(grid)
                    cur.y+=dy
                    for cx,cy in cells(cur.sh,cur.x,cur.y):
                        if cy>=0:grid[cy][cx]=cur.c
                    grid,cl=clr(grid)
                    score+=cl*100
                    if not bag: bag=newbag()
                    cur=Piece(bag.popleft())

        if fall_timer>fall_speed:
            fall_timer=0
            if not cur.mv(grid,0,1):
                for cx,cy in cells(cur.sh,cur.x,cur.y):
                    if cy<0:return False  # game over
                    grid[cy][cx]=cur.c
                grid,cl=clr(grid)
                score+=cl*100
                if not bag: bag=newbag()
                cur=Piece(bag.popleft())

        surf=pygame.Surface((COLS*BLK,ROWS*BLK))
        drawboard(surf,grid)
        for cx,cy in cells(cur.sh,cur.x,cur.y):
            if cy>=0: drawcell(surf,cx,cy,cur.c)
        screen.blit(surf,(0,0))
        text(screen,f"SCORE {int(score)}",24,COLS*BLK+100,40)
        pygame.display.flip()

# ------------------------------
# MAIN
# ------------------------------
def main():
    pygame.init()
    pygame.font.init()
    screen=pygame.display.set_mode((W,H))
    pygame.display.set_caption("Ultra!Tetris — Samsoft Edition")
    clock=pygame.time.Clock()
    intro(screen,clock)
    while True:
        if not menu(screen,clock):break
        if not game(screen,clock):break
    pygame.quit();sys.exit()

if __name__=="__main__":
    main()
