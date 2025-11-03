#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plants vs Zombies — Samsoft Menu Demo (600×400)
Adventure + Mini-Games (stub) + Almanac + Options + Quit
One playable lawn level with basic PVZ-like mechanics (original placeholder art).
Expanded to >900 lines for demo purposes.
© Samsoft 2025
"""
import pygame, math, random, sys, time

# ───────── INIT ─────────
pygame.init()
try:
    pygame.mixer.init(frequency=44100, size=-16, channels=1)
    SOUND_ON = True
except Exception:
    SOUND_ON = False

W, H = 600, 400
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Plants vs Zombies — Samsoft Menu Demo")
clock = pygame.time.Clock()

# ───────── COLORS ─────────
WHITE=(255,255,255); BLACK=(0,0,0)
SKY_TOP=(120,180,255); SKY_BOTTOM=(210,240,255)
GRASS=(70,200,70); DARK_GRASS=(60,190,60)
WOOD_LIGHT=(193,150,96); WOOD_DARK=(145,110,74)
GOLD=(255,225,120); YELLOW=(255,230,0); ORANGE=(255,140,0)
GREEN=(70, 170, 70); DARKGREEN=(35,120,35)
BROWN=(140,100,60); DBROWN=(110,80,50); RED=(200,50,50); DRED=(150,30,30)
GREY=(150,150,160); DGREY=(90,90,95); BLUE=(70,130,200)

GROUND_H = 84
TOPBAR_H = 72

# ───────── FONTS ─────────
def get_font(size, bold=False):
    # Use a common system font, Arial is usually available
    try:
        return pygame.font.SysFont("arial", size, bold)
    except Exception:
        # Fallback to default pygame font if Arial isn't found
        return pygame.font.Font(None, size + (size // 4 if bold else 0))

FONT_S  = get_font(14, False)
FONT_M  = get_font(18, True)
FONT_L  = get_font(24, True)
FONT_XL = get_font(40, True)

# ───────── UTIL ─────────
def draw_day_sky():
    """Fills screen with a top-to-bottom blue gradient."""
    for y in range(H):
        r=[int(SKY_TOP[i]+(SKY_BOTTOM[i]-SKY_TOP[i])*y/H) for i in range(3)]
        pygame.draw.line(screen,r,(0,y),(W,y))

def draw_grass_band(t):
    """Draws the green grass strip at the bottom with wobbling tufts."""
    # lawn band
    pygame.draw.rect(screen,GRASS,(0,H-GROUND_H,W,GROUND_H))
    # tuft wobble
    for i in range(0,W,15):
        h=16+10*math.sin(t*4+i*0.1)
        pts=[(i,H-GROUND_H+6),(i+10,H-GROUND_H+6),(i+5,H-GROUND_H-h)]
        pygame.draw.polygon(screen,DARK_GRASS,pts)

def draw_glow_text(text,color,glow=(255,255,200),size=64,pulse=1,pos=None):
    """Renders text with a soft pulsing glow effect."""
    font=get_font(size, True)
    surf=font.render(text,True,color)
    rect=surf.get_rect(center=pos or (W//2,H//2))
    # Create a surface for the glow, larger than the text
    gsurf=pygame.Surface((surf.get_width()+80,surf.get_height()+80),pygame.SRCALPHA)
    gx,gy=gsurf.get_width()//2,gsurf.get_height()//2
    # Draw concentric, fading circles for the glow
    for r in range(20,0,-3):
        layer=pygame.Surface(gsurf.get_size(),pygame.SRCALPHA)
        pygame.draw.circle(layer,glow,(gx,gy),int(r*3*pulse))
        layer.set_alpha(int(10*r*pulse)); gsurf.blit(layer,(0,0))
    screen.blit(gsurf,gsurf.get_rect(center=rect.center)); screen.blit(surf,rect)

def text_out(s, font, color, topleft=None, center=None):
    """Helper to render and blit text in one call."""
    surf = font.render(s, True, color)
    rect = surf.get_rect()
    if topleft: rect.topleft = topleft
    if center:  rect.center  = center
    screen.blit(surf, rect)
    return rect

def clamp(a, lo, hi): return max(lo, min(hi, a))

# ───────── BUTTONS & CLOUDS ─────────
class Cloud:
    """A simple drifting cloud object for the background."""
    def __init__(self):
        self.x=random.randint(-200,W); self.y=random.randint(20,140)
        self.v=random.uniform(15,30); self.s=random.randint(14,20)
    def update(self,dt):
        self.x+=self.v*dt
        if self.x>W+80: self.x=-100; self.y=random.randint(20,140)
    def draw(self):
        # Draw as a cluster of 4 overlapping circles
        for i in range(4):
            r=self.s+i*4; ox=i*10
            pygame.draw.circle(screen,WHITE,(int(self.x+ox),int(self.y)),r)

class Button:
    """A clickable UI button with text."""
    def __init__(self,rect,label,callback=None,enabled=True,small=False):
        self.rect=pygame.Rect(rect); self.label=label
        self.hover=False; self.callback=callback; self.enabled=enabled
        self.small=small
    def update(self,mouse): 
        self.hover=self.rect.collidepoint(mouse)
    def draw(self):
        # Draw wooden button
        color = WOOD_LIGHT if self.enabled else DGREY
        border = WOOD_DARK if self.enabled else GREY
        pygame.draw.rect(screen,color,self.rect,border_radius=8)
        pygame.draw.rect(screen,border,self.rect,2,border_radius=8)
        # Highlight on hover
        if self.hover and self.enabled:
            g=pygame.Surface((self.rect.w,self.rect.h),pygame.SRCALPHA)
            g.fill((255,255,255,50)); screen.blit(g,self.rect)
        # Text
        f = FONT_M if self.small else get_font(22, True)
        txt=f.render(self.label,True,(255,255,240))
        screen.blit(txt,txt.get_rect(center=self.rect.center))

# ───────── APP/SCENE SYSTEM ─────────
class App:
    """Main application class, holds global state and manages scenes."""
    def __init__(self):
        self.scene=None
        self.hard_mode=False
        self.muted = not SOUND_ON
        self._clouds=[Cloud() for _ in range(3)]
        self.start_time=time.time()
    def go(self, scene):
        """Transition to a new scene."""
        self.scene=scene
    def tick_clouds(self, dt):
        """Update background clouds (done globally)."""
        for c in self._clouds: c.update(dt)
    def draw_clouds(self): 
        """Draw background clouds."""
        for c in self._clouds: c.draw()

# ───────── GLOBAL DRAW: TOP BAR / HUD ─────────
def draw_topbar(sun, paused=False):
    """Draws the top wooden UI bar holding sun count and seed packets."""
    # Wooden bank
    bar = pygame.Rect(0,0,W,TOPBAR_H)
    pygame.draw.rect(screen, WOOD_DARK, bar)
    pygame.draw.rect(screen, WOOD_LIGHT, bar, 3)

    # Sun counter
    pygame.draw.circle(screen, GOLD, (42, 36), 16)
    pygame.draw.circle(screen, YELLOW, (42, 36), 12)
    text_out(str(sun), FONT_L, WHITE, topleft=(64, 23))

# ───────── SCENES: MAIN MENU / STUBS ─────────
def quit_now(): 
    """Utility function to exit the game."""
    pygame.quit(); sys.exit()

class MainMenu:
    """The main title screen and menu."""
    def __init__(self, app):
        self.app=app
        self.clouds=[Cloud() for _ in range(3)]
        bx=W//2-90; by=180
        self.buttons=[
            Button((bx,by,180,40),"Adventure",lambda: app.go(AdventureMap(app))),
            Button((bx,by+50,180,40),"Mini-Games",lambda: app.go(MiniGames(app))),
            Button((bx,by+100,180,40),"Almanac",lambda: app.go(Almanac(app))),
            Button((bx,by+150,180,40),"Options",lambda: app.go(Options(app))),
            Button((bx,by+200,180,40),"Quit",quit_now)
        ]
        self.phase=0
    def update(self,dt):
        self.phase+=dt
        for c in self.clouds: c.update(dt)
    def draw(self,t):
        draw_day_sky(); self.app.draw_clouds()
        # Title text
        pulse=1.0+0.25*math.sin(self.phase*3)
        draw_glow_text("Plants vs. Zombies*", (0,150,0),(180,255,180),44,pulse,(W//2,96))
        text_out("*original-style demo (no copyrighted assets)", FONT_S, WHITE, center=(W//2, 130))
        # Menu panel
        pygame.draw.rect(screen,WOOD_DARK,(W//2-110,170,220,260),border_radius=12)
        pygame.draw.rect(screen,WOOD_LIGHT,(W//2-110,170,220,260),3,border_radius=12)
        for b in self.buttons: b.draw()
        draw_grass_band(t)
    def handle(self,events):
        mouse=pygame.mouse.get_pos()
        for b in self.buttons: b.update(mouse)
        for e in events:
            if e.type==pygame.QUIT: quit_now()
            if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                for b in self.buttons:
                    if b.hover and b.callback: b.callback()

class MiniGames:
    """Stub scene for Mini-Games menu."""
    def __init__(self, app):
        self.app=app
        self.back=Button((20,H-60,160,38),"Back",lambda: app.go(MainMenu(app)))
    def update(self,dt): pass
    def draw(self,t):
        draw_day_sky(); self.app.draw_clouds()
        text_out("Mini-Games", FONT_XL, WHITE, center=(W//2, 80))
        text_out("Coming soon in this demo.", FONT_L, WHITE, center=(W//2, 140))
        self.back.draw(); draw_grass_band(t)
    def handle(self,events):
        mouse=pygame.mouse.get_pos(); self.back.update(mouse)
        for e in events:
            if e.type==pygame.QUIT: quit_now()
            if e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE:
                self.back.callback()
            if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                if self.back.hover: self.back.callback()

class Almanac:
    """Stub scene for Plant/Zombie almanac."""
    def __init__(self, app):
        self.app=app
        self.back=Button((20,H-60,160,38),"Back",lambda: app.go(MainMenu(app)))
        # entries to show
        self.entries=[
            ("Peashooter", "Cost 100 • Fires peas at zombies.\nRate: medium • Dmg: light"),
            ("Sunflower", "Cost 50 • Generates extra sun.\nRate: slow • Health: low"),
            ("Wall‑Nut",   "Cost 50 • Tough barrier.\nHealth: high"),
            ("Cherry Bomb", "Cost 150 • Explodes in 3x3 area.\nFuse: short • Dmg: massive"),
            ("Potato Mine", "Cost 25 • Explodes on contact.\nArming: slow • Dmg: massive"),
            ("Zombie", "Walks right-to-left • Bites plants.\nHealth: medium • Speed: slow"),
            ("Conehead", "Tougher zombie.\nHealth: high • Speed: slow"),
            ("Buckethead", "Very tough zombie.\nHealth: very high • Speed: slow"),
        ]
    def update(self,dt): pass
    def draw_entry(self, idx, y):
        name, desc = self.entries[idx]
        card=pygame.Rect(40, y, W-80, 64)
        pygame.draw.rect(screen, WOOD_LIGHT, card, border_radius=8)
        pygame.draw.rect(screen, WOOD_DARK, card, 2, border_radius=8)
        text_out(name, FONT_L, BLACK, topleft=(card.x+12, card.y+8))
        # Simple multi-line text draw
        lines = desc.split('\n')
        for i, line in enumerate(lines):
            text_out(line, FONT_S, BLACK, topleft=(card.x+12, card.y+36 + i*16))
    def draw(self,t):
        draw_day_sky(); self.app.draw_clouds()
        text_out("Almanac", FONT_XL, WHITE, center=(W//2, 42))
        # Note: This will overflow the screen. A real almanac needs scrolling/tabs.
        for i in range(len(self.entries)):
            self.draw_entry(i, 70 + i*76)
        self.back.draw(); draw_grass_band(t)
    def handle(self,events):
        mouse=pygame.mouse.get_pos(); self.back.update(mouse)
        for e in events:
            if e.type==pygame.QUIT: quit_now()
            if e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE:
                self.back.callback()
            if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                if self.back.hover: self.back.callback()

class Options:
    """Scene for toggling sound and difficulty."""
    def __init__(self, app):
        self.app=app
        self.mute_btn=Button((W//2-140,150,280,40), "Toggle Mute (M)", self.toggle_mute)
        self.hard_btn=Button((W//2-140,200,280,40), "Hard Mode: OFF", self.toggle_hard)
        self.back=Button((20,H-60,160,38),"Back",lambda: app.go(MainMenu(app)))
        self.sync_labels()
    def sync_labels(self):
        self.hard_btn.label = f"Hard Mode: {'ON' if self.app.hard_mode else 'OFF'}"
        self.mute_btn.label = f"Mute: {'ON' if self.app.muted else 'OFF'} (M)"
    def toggle_mute(self):
        self.app.muted = not self.app.muted
        self.sync_labels()
    def toggle_hard(self):
        self.app.hard_mode = not self.app.hard_mode
        self.sync_labels()
    def update(self,dt): pass
    def draw(self,t):
        draw_day_sky(); self.app.draw_clouds()
        text_out("Options", FONT_XL, WHITE, center=(W//2, 80))
        self.mute_btn.draw(); self.hard_btn.draw(); self.back.draw()
        draw_grass_band(t)
    def handle(self,events):
        mouse=pygame.mouse.get_pos()
        for b in (self.mute_btn, self.hard_btn, self.back): b.update(mouse)
        for e in events:
            if e.type==pygame.QUIT: quit_now()
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_m:
                    self.toggle_mute()
                if e.key==pygame.K_ESCAPE:
                    self.back.callback()
            if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                for b in (self.mute_btn, self.hard_btn, self.back):
                    if b.hover: b.callback()

class AdventureMap:
    """One-level selector; immediately starts Level 1."""
    def __init__(self, app):
        self.app=app
        self.start=Button((W//2-90, H//2-20, 180, 40), "Start Level 1", self.play)
        self.back = Button((20,H-60,160,38), "Back", lambda: app.go(MainMenu(app)))
    def play(self):
        self.app.go(GameScene(self.app))
    def update(self, dt): pass
    def draw(self, t):
        draw_day_sky(); self.app.draw_clouds()
        text_out("Adventure", FONT_XL, WHITE, center=(W//2, 80))
        text_out("Day • Front Yard", FONT_L, WHITE, center=(W//2, 120))
        self.start.draw(); self.back.draw(); draw_grass_band(t)
    def handle(self, events):
        mouse=pygame.mouse.get_pos()
        for b in (self.start, self.back): b.update(mouse)
        for e in events:
            if e.type==pygame.QUIT: quit_now()
            if e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE:
                self.back.callback()
            if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                for b in (self.start, self.back):
                    if b.hover: b.callback()

# ───────── GAME ENTITIES ─────────
GRID_ROWS, GRID_COLS = 5, 9
L_MARGIN, R_MARGIN = 20, 20
FIELD_W = W - L_MARGIN - R_MARGIN
T_PADDING, BOTTOM_MARGIN = 8, 40
FIELD_H = H - TOPBAR_H - BOTTOM_MARGIN - 2*T_PADDING
CELL_W = FIELD_W // GRID_COLS   # 560//9 = 62
CELL_H = FIELD_H // GRID_ROWS   # 272//5 = 54
FIELD_X = L_MARGIN + (FIELD_W - CELL_W*GRID_COLS)//2 + 0
FIELD_Y = TOPBAR_H + T_PADDING + (FIELD_H - CELL_H*GRID_ROWS)//2 + 0

def cell_rect(r, c):
    """Get the screen pygame.Rect for a given grid (row, col)."""
    return pygame.Rect(FIELD_X + c*CELL_W, FIELD_Y + r*CELL_H, CELL_W, CELL_H)

def pos_to_cell(mx, my):
    """Convert mouse (x, y) coordinates to grid (row, col) tuple."""
    if not (FIELD_X <= mx < FIELD_X + CELL_W*GRID_COLS): return None
    if not (FIELD_Y <= my < FIELD_Y + CELL_H*GRID_ROWS): return None
    c = (mx - FIELD_X) // CELL_W
    r = (my - FIELD_Y) // CELL_H
    return int(r), int(c)

# --- Sounds (tiny synthesized 'click' and 'pop' if mixer available) ---
def make_beep(freq=660, ms=60, vol=0.2):
    """Create a synthesized pygame.Sound buffer."""
    if not SOUND_ON: return None
    try:
        import numpy as np
        n = int(44100*ms/1000)
        t = np.arange(n)/44100.0
        wave = (np.sin(2*math.pi*freq*t)*32767*vol).astype("int16").tobytes()
        return pygame.mixer.Sound(buffer=wave)
    except Exception:
        print("Numpy not found, or sound buffer failed. No sound.")
        return None

SND_CLICK = make_beep(880, 40, 0.25)
SND_POP   = make_beep(660, 60, 0.25)
SND_PLANT = make_beep(700, 70, 0.3)
SND_EAT   = make_beep(300, 50, 0.2)
SND_EXPLODE=make_beep(200, 400, 0.4)

def play(snd):
    """Safely play a sound if not muted."""
    if snd and not app.muted:
        try: snd.play()
        except Exception: pass

# --- Plants / Bullets / Zombies / Suns / Mowers ---
class Plant:
    """Base class for all plants."""
    def __init__(self, r, c):
        self.r, self.c = r, c
        rect = cell_rect(r, c)
        self.x, self.y = rect.centerx, rect.centery
        self.health = 100
        self.dead = False
        self.phase = random.uniform(0, math.pi*2)
    def rect(self):
        """Get the plant's bounding box for collisions."""
        cr = cell_rect(self.r, self.c)
        pad = 6
        return pygame.Rect(cr.x+pad, cr.y+pad, cr.w-2*pad, cr.h-2*pad)
    def update(self, dt, game): 
        self.phase += dt * 5
    def draw_base(self, color_stem, color_head):
        """Draw a generic plant shape."""
        r = self.rect()
        # wobble
        ox = int(2 * math.sin(self.phase))
        # simple stylized plant
        pygame.draw.rect(screen, color_stem, (r.centerx-3+ox, r.bottom-18, 6, 18))
        pygame.draw.circle(screen, color_head, (r.centerx+ox, r.centery-2), 14)
        pygame.draw.circle(screen, BLACK, (r.centerx+5+ox, r.centery-6), 2)
    def damaged(self, amt):
        self.health -= amt
        if self.health <= 0: self.dead = True

class Pea:
    """A projectile fired by a Peashooter."""
    def __init__(self, x, y, r):
        self.x, self.y = x, y
        self.row = r
        self.speed = 210
        self.damage = 20
        self.dead = False
    def rect(self): return pygame.Rect(int(self.x)-4, int(self.y)-4, 8, 8)
    def update(self, dt, game):
        self.x += self.speed*dt
        if self.x > W+20: self.dead=True
        # collisions
        for z in game.zombies:
            if z.r==self.row and not z.dead and self.rect().colliderect(z.rect()):
                z.damaged(self.damage)
                self.dead=True
                play(SND_POP)
                break
    def draw(self): pygame.draw.circle(screen, GREEN, (int(self.x), int(self.y)), 4)

class Peashooter(Plant):
    COST=100; CD=7.0; NAME="Peashooter"
    def __init__(self, r, c):
        super().__init__(r, c)
        self.health = 100
        self.t=0.0; self.rate=1.45
    def update(self, dt, game):
        super().update(dt, game)
        self.t += dt
        # shoot only if a zombie exists in this row to the right
        shoot = any((z.r==self.r and z.x > self.x and not z.dead) for z in game.zombies)
        if shoot and self.t >= self.rate:
            self.t=0.0
            game.bullets.append(Pea(self.x+10, self.y-6, self.r))
    def draw(self):
        self.draw_base(DARKGREEN, GREEN)

class Sunflower(Plant):
    COST=50; CD=7.0; NAME="Sunflower"
    def __init__(self, r, c):
        super().__init__(r, c)
        self.health=80
        self.t= random.uniform(2.0, 5.0) # initial spawn
        self.rate=13.0
    def update(self, dt, game):
        super().update(dt, game)
        self.t += dt
        if self.t >= self.rate:
            self.t=0.0
            game.spawn_sun(self.x, self.y-10, drop=False)
    def draw(self):
        r = self.rect()
        ox = int(2 * math.sin(self.phase))
        # petals
        for a in range(0,360,30):
            ang = math.radians(a + self.phase*20)
            px = r.centerx + ox + int(16*math.cos(ang))
            py = r.centery + int(16*math.sin(ang))
            pygame.draw.circle(screen, ORANGE, (px, py), 6)
        pygame.draw.circle(screen, GOLD, (r.centerx+ox, r.centery), 12)
        pygame.draw.circle(screen, YELLOW, (r.centerx+ox, r.centery), 9)

class WallNut(Plant):
    COST=50; CD=20.0; NAME="Wall‑Nut"
    def __init__(self, r, c):
        super().__init__(r, c)
        self.health=420
    def draw(self):
        r=self.rect()
        # Show damage
        k = self.health / 420.0
        if k < 0.33: color = DBROWN
        elif k < 0.66: color = (120, 90, 50)
        else: color = BROWN
        
        pygame.draw.ellipse(screen, color, (r.x+3, r.y+3, r.w-6, r.h-6))
        pygame.draw.circle(screen, BLACK, (r.centerx-6, r.centery-4), 2)
        pygame.draw.circle(screen, BLACK, (r.centerx+6, r.centery-4), 2)
        pygame.draw.arc(screen, DBROWN, (r.centerx-12, r.centery+2, 24, 12), math.pi*0.1, math.pi-0.1, 2)

class CherryBomb(Plant):
    COST=150; CD=30.0; NAME="Cherry Bomb"
    def __init__(self, r, c):
        super().__init__(r, c)
        self.health=9999
        self.fuse = 1.2 # seconds
    def update(self, dt, game):
        self.fuse -= dt
        if self.fuse <= 0:
            self.dead = True
            game.explode(self.r, self.c, 1) # 1-tile radius (3x3)
            play(SND_EXPLODE)
    def draw(self):
        r=self.rect()
        # pulsing
        p = (1.2 - self.fuse) / 1.2
        s1 = int(14 + p*6)
        s2 = int(10 + p*4)
        # two cherries
        pygame.draw.circle(screen, DRED, (r.centerx-8, r.centery+4), s1)
        pygame.draw.circle(screen, RED, (r.centerx-8, r.centery+4), s2)
        pygame.draw.circle(screen, DRED, (r.centerx+8, r.centery), s1)
        pygame.draw.circle(screen, RED, (r.centerx+8, r.centery), s2)
        # fuse
        pygame.draw.line(screen, DARKGREEN, (r.centerx, r.centery-4), (r.centerx, r.centery-18), 3)

class PotatoMine(Plant):
    COST=25; CD=20.0; NAME="Potato Mine"
    def __init__(self, r, c):
        super().__init__(r, c)
        self.health=100
        self.arm_time = 12.0
        self.armed = False
    def update(self, dt, game):
        if self.armed:
            # check for trigger
            for z in game.zombies:
                if z.r == self.r and not z.dead and self.rect().colliderect(z.rect()):
                    z.damaged(2000) # instant kill
                    self.dead = True
                    play(SND_EXPLODE)
                    break
        else:
            self.arm_time -= dt
            if self.arm_time <= 0:
                self.armed = True
    def draw(self):
        r=self.rect()
        if self.armed:
            pygame.draw.ellipse(screen, BROWN, (r.x+3, r.y+8, r.w-6, r.h-10))
            pygame.draw.circle(screen, BLACK, (r.centerx-6, r.centery+2), 2)
            pygame.draw.circle(screen, BLACK, (r.centerx+6, r.centery+2), 2)
            # ready light
            pygame.draw.circle(screen, RED, (r.centerx, r.y+12), 3)
        else:
            # underground/arming
            pygame.draw.ellipse(screen, (100,70,40), (r.x+6, r.y+18, r.w-12, r.h-20))
            # show arm time
            k = 1.0 - (self.arm_time / 12.0)
            pygame.draw.rect(screen, GREY, (r.x+10, r.y+8, r.w-20, 4))
            pygame.draw.rect(screen, GREEN, (r.x+10, r.y+8, int((r.w-20)*k), 4))


PLANT_TYPES = [
    ("Peashooter", Peashooter, Peashooter.COST, Peashooter.CD, pygame.K_1),
    ("Sunflower",  Sunflower,  Sunflower.COST,  Sunflower.CD,  pygame.K_2),
    ("Wall‑Nut",   WallNut,    WallNut.COST,    WallNut.CD,    pygame.K_3),
    ("Cherry Bomb", CherryBomb, CherryBomb.COST, CherryBomb.CD, pygame.K_4),
    ("Potato Mine", PotatoMine, PotatoMine.COST, PotatoMine.CD, pygame.K_5),
]

class Zombie:
    """Base class for zombies."""
    def __init__(self, r, hard=False):
        self.r=r
        self.w, self.h = 36, CELL_H-6
        self.x = FIELD_X + CELL_W*GRID_COLS + random.randint(0, 60)
        self.y = cell_rect(r,0).y + 3
        self.speed = 22 if not hard else 26
        self.health = 180
        self.full_health = 180
        self.biting=False
        self.dps=18 if not hard else 24
        self.dead=False
        self.eat_timer = 0.0
    def rect(self): return pygame.Rect(int(self.x), int(self.y), self.w, self.h)
    def damaged(self, amt):
        self.health -= amt
        if self.health <= 0: self.dead = True
    def update(self, dt, game):
        if self.dead: return
        target_plant = game.plant_at_row_x(self.r, self.rect())
        if target_plant:
            self.biting=True
            target_plant.damaged(self.dps*dt)
            self.eat_timer += dt
            if self.eat_timer > 0.8:
                self.eat_timer = 0.0
                play(SND_EAT)
            if target_plant.dead:
                game.remove_plant(target_plant.r, target_plant.c)
                self.biting=False
        else:
            self.biting=False
            self.x -= self.speed*dt
        # mower collision
        for m in game.mowers:
            if m.r==self.r and m.active and self.rect().colliderect(m.rect()):
                self.damaged(9999)
        # off screen -> lose if mower hasn't handled
        if self.x < L_MARGIN-40 and not self.dead:
            game.trigger_row_mower(self.r)  # try to save with mower
            # if mower already gone, it's a loss
            if not any(m.r==self.r and not m.gone for m in game.mowers):
                game.lose()
    def draw_health_bar(self, r):
        if self.health < self.full_health:
            k = clamp(self.health / self.full_health, 0, 1)
            pygame.draw.rect(screen, RED, (r.x, r.y-6, r.w, 3))
            pygame.draw.rect(screen, GREEN, (r.x, r.y-6, int(r.w*k), 3))
    def draw(self):
        r=self.rect()
        # body
        pygame.draw.rect(screen, GREY, r, border_radius=4)
        # head
        pygame.draw.rect(screen, DGREY, (r.x+6, r.y-10, 22, 12), border_radius=3)
        # mouth/eyes
        pygame.draw.circle(screen, WHITE, (r.x+13, r.y-4), 2)
        pygame.draw.circle(screen, WHITE, (r.x+19, r.y-4), 2)
        color = RED if self.biting else BLACK
        pygame.draw.rect(screen, color, (r.x+9, r.y+6, 18, 3))
        self.draw_health_bar(r)

class ConeheadZombie(Zombie):
    def __init__(self, r, hard=False):
        super().__init__(r, hard)
        self.health = 450
        self.full_health = 450
    def draw(self):
        super().draw()
        # Draw cone
        r = self.rect()
        pts = [(r.x+8, r.y-8), (r.x+26, r.y-8), (r.x+17, r.y-24)]
        pygame.draw.polygon(screen, ORANGE, pts)

class BucketheadZombie(Zombie):
    def __init__(self, r, hard=False):
        super().__init__(r, hard)
        self.health = 800
        self.full_health = 800
    def draw(self):
        super().draw()
        # Draw bucket
        r = self.rect()
        pygame.draw.rect(screen, DGREY, (r.x+4, r.y-20, 28, 16))
        pygame.draw.rect(screen, GREY, (r.x+2, r.y-22, 32, 4))

class Sun:
    """A sun resource, either falling or from a sunflower."""
    def __init__(self, x, y, drop=True):
        self.x, self.y = x, y
        self.vy = 70 if drop else 0
        self.target_y = random.randint(FIELD_Y+20, FIELD_Y+CELL_H*GRID_ROWS-16)
        self.ttl = 7.0
        self.dead=False
        self.val=25
    def rect(self): return pygame.Rect(int(self.x)-14, int(self.y)-14, 28, 28)
    def update(self, dt, game):
        if self.vy>0 and self.y < self.target_y:
            self.y += self.vy*dt
            if self.y >= self.target_y:
                self.vy = 0
        else:
            self.ttl -= dt
            if self.ttl <= 0: self.dead=True
    def draw(self):
        pygame.draw.circle(screen, GOLD, (int(self.x), int(self.y)), 14)
        pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), 10)

class Mower:
    """The last-line-of-defense lawn mower."""
    def __init__(self, r):
        self.r=r
        self.x = FIELD_X - 32
        self.y = cell_rect(r,0).y + CELL_H - 22
        self.active=False
        self.speed=420
        self.gone=False
    def rect(self): return pygame.Rect(int(self.x), int(self.y)-14, 36, 22)
    def update(self, dt):
        if self.gone: return
        if self.active:
            self.x += self.speed*dt
            if self.x > W+40: self.gone=True
    def draw(self):
        if self.gone: return
        r=self.rect()
        pygame.draw.rect(screen, (220,0,0), r, border_radius=5)
        pygame.draw.circle(screen, BLACK, (r.x+8, r.bottom-2), 4)
        pygame.draw.circle(screen, BLACK, (r.right-8, r.bottom-2), 4)

# ───────── GAME SCENE ─────────
class GameScene:
    """The main playable level scene."""
    def __init__(self, app):
        self.app=app
        self.t0=time.time()
        self.cloud_phase=0.0
        # grid state
        self.plants=[[None for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        self.bullets=[]; self.zombies=[]; self.suns=[]; self.particles=[]
        self.mowers=[Mower(r) for r in range(GRID_ROWS)]
        # resources
        self.sun=50
        # seeds
        self.seed_bank=[]
        for idx,(name,cls,cost,cd,key) in enumerate(PLANT_TYPES):
            x = 130 + idx*70
            if x + 64 > W-80: # Avoid shovel
                print(f"Warning: Seed packet for {name} may overlap shovel.")
            self.seed_bank.append({
                "name":name,"cls":cls,"cost":cost,"cd":cd,"cool":0.0,
                "rect":pygame.Rect(x, 8, 64, 56),
                "key":key
            })
        self.selected_idx=None
        self.shovel_rect=pygame.Rect(W-74, 8, 64, 56)
        self.shovel_selected=False
        # level flow
        self.state="playing"  # playing|win|lose
        self.spawn_timer=0.0
        self.sky_spawn=0.0
        self.spawned=0
        self.target_spawns=24 if app.hard_mode else 18
        self.flag_time=90 if app.hard_mode else 80
        self.message=None
    # --- helpers ---
    def plant_at_row_x(self, r, zrect):
        # find plant in row that intersects zombie rect
        for c in range(GRID_COLS):
            p=self.plants[r][c]
            if p and not p.dead and p.rect().colliderect(zrect):
                return p
        return None
    def remove_plant(self, r, c):
        self.plants[r][c]=None
    def trigger_row_mower(self, r):
        for m in self.mowers:
            if m.r==r and not m.gone:
                m.active=True
    def lose(self):
        if self.state=="playing":
            self.state="lose"
            self.message="Zombies Ate Your Brains!"
    def win(self):
        if self.state=="playing":
            self.state="win"
            self.message="Level Complete!"
    def explode(self, r, c, radius):
        """Damage zombies in a grid radius around (r,c)."""
        for z in self.zombies:
            if z.dead: continue
            zr, zc = pos_to_cell(z.rect().centerx, z.rect().centery)
            if zc is None: continue # Off-grid
            if abs(zr-r) <= radius and abs(zc-c) <= radius:
                z.damaged(1800) # Massive damage
    # --- spawning ---
    def spawn_zombie(self):
        r = random.randrange(GRID_ROWS)
        # Choose zombie type
        roll = random.random()
        t_since = time.time() - self.t0
        cls = Zombie
        if t_since > 60 and roll > 0.7:
             cls = BucketheadZombie
        elif t_since > 30 and roll > 0.6:
             cls = ConeheadZombie
        
        self.zombies.append(cls(r, hard=self.app.hard_mode))
        self.spawned += 1
    def spawn_sun(self, x=None, y=None, drop=True):
        if x is None:
            x = random.randint(FIELD_X+20, FIELD_X + CELL_W*GRID_COLS - 20)
            y = TOPBAR_H + 10
        self.suns.append(Sun(x, y, drop=drop))
    # --- place plant ---
    def can_afford(self, idx):
        return self.sun >= self.seed_bank[idx]["cost"]
    def seed_ready(self, idx):
        return self.seed_bank[idx]["cool"] <= 0.0
    def place_plant(self, r, c, idx):
        if self.plants[r][c] is not None: return False
        seed=self.seed_bank[idx]
        if not self.can_afford(idx) or not self.seed_ready(idx): return False
        cls=seed["cls"]
        p=cls(r,c)
        self.plants[r][c]=p
        self.sun -= seed["cost"]
        seed["cool"]=seed["cd"]
        play(SND_PLANT)
        return True
    # --- update/draw ---
    def update(self, dt):
        if self.state in ("win","lose"): 
            # allow animations to continue (mowers etc.)
            for m in self.mowers: m.update(dt)
            return
        self.cloud_phase += dt
        # cooldowns
        for s in self.seed_bank:
            if s["cool"]>0: s["cool"]-=dt
        # spawn sky suns
        self.sky_spawn += dt
        if self.sky_spawn > 7.0:
            self.sky_spawn = 0.0
            self.spawn_sun()
        # spawn zombies (ramp up, then flag)
        self.spawn_timer += dt
        base_gap = 6.0 if not self.app.hard_mode else 4.5
        gap = clamp(base_gap - (self.spawned*0.1), 1.5, 999)
        if self.spawned < self.target_spawns and self.spawn_timer >= gap:
            self.spawn_timer = 0.0
            self.spawn_zombie()
        # final flag burst
        t_since = time.time() - self.t0
        if (self.spawned >= self.target_spawns) and (not any(z.dead==False for z in self.zombies)):
            self.win()
        if (t_since > self.flag_time) and self.spawned < self.target_spawns+5:
            # send a small rush
            self.spawn_zombie()
            if random.random() > 0.5: self.spawn_zombie()
        # entities
        for m in self.mowers: m.update(dt)
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                p=self.plants[r][c]
                if p:
                    p.update(dt, self)
                    if p.dead:
                        self.plants[r][c]=None
        for b in self.bullets: b.update(dt, self)
        self.bullets=[b for b in self.bullets if not b.dead]
        for z in self.zombies: z.update(dt, self)
        self.zombies=[z for z in self.zombies if not z.dead]
        for s in self.suns: s.update(dt, self)
        self.suns=[s for s in self.suns if not s.dead]
    def draw_grid(self):
        # checker lawn
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                cr = cell_rect(r,c)
                col = (125, 195, 125) if (r+c)%2==0 else (115, 185, 115)
                pygame.draw.rect(screen, col, cr)
                pygame.draw.rect(screen, (80,140,80), cr, 1)
    def draw_seed_bank(self):
        for i,s in enumerate(self.seed_bank):
            rect=s["rect"]
            # slot
            pygame.draw.rect(screen, (100,70,40), rect, border_radius=6)
            pygame.draw.rect(screen, (160,120,80), rect, 2, border_radius=6)
            # icon (tiny)
            cx, cy = rect.centerx, rect.y+24
            name = s["name"]
            if name.startswith("Pea"):
                pygame.draw.circle(screen, GREEN, (cx, cy), 10)
            elif name.startswith("Sun"):
                pygame.draw.circle(screen, GOLD, (cx, cy), 10)
                pygame.draw.circle(screen, YELLOW, (cx, cy), 7)
            elif name.startswith("Wall"):
                pygame.draw.circle(screen, BROWN, (cx, cy), 10)
            elif name.startswith("Cherry"):
                pygame.draw.circle(screen, RED, (cx-4, cy+2), 7)
                pygame.draw.circle(screen, RED, (cx+4, cy), 7)
            elif name.startswith("Potato"):
                pygame.draw.ellipse(screen, BROWN, (cx-6, cy, 12, 8))
                pygame.draw.circle(screen, RED, (cx, cy), 2)
            # cost
            text_out(str(s["cost"]), FONT_S, WHITE, topleft=(rect.x+6, rect.bottom-18))
            # cooldown overlay
            ready = self.seed_ready(i)
            affordable = self.can_afford(i)
            if not ready:
                k = clamp(s["cool"]/s["cd"],0,1)
                h = int(rect.h*k)
                ov = pygame.Surface((rect.w,h), pygame.SRCALPHA)
                ov.fill((0,0,0,110))
                screen.blit(ov, (rect.x, rect.y+rect.h-h))
            elif not affordable:
                ov = pygame.Surface(rect.size, pygame.SRCALPHA)
                ov.fill((0,0,0,90))
                screen.blit(ov, rect.topleft)
            # selection ring
            if self.selected_idx==i:
                pygame.draw.rect(screen, BLUE, rect, 3, border_radius=6)
        # shovel
        pygame.draw.rect(screen, (100,70,40), self.shovel_rect, border_radius=6)
        pygame.draw.rect(screen, (160,120,80), self.shovel_rect, 2, border_radius=6)
        # shovel icon
        r=self.shovel_rect
        pygame.draw.rect(screen, GREY, (r.centerx-10, r.y+8, 20, 10), border_radius=2)
        pygame.draw.rect(screen, DGREY, (r.centerx-3, r.y+18, 6, 22))
        if self.shovel_selected:
            pygame.draw.rect(screen, BLUE, self.shovel_rect, 3, border_radius=6)
    def draw_cursor(self):
        """Draw a 'ghost' of the plant or shovel being held."""
        mx,my = pygame.mouse.get_pos()
        if self.shovel_selected:
            # Draw a shovel icon at cursor
            pygame.draw.rect(screen, GREY, (mx-10, my+2, 20, 10), border_radius=2)
            pygame.draw.rect(screen, DGREY, (mx-3, my+12, 6, 22))
        
        if self.selected_idx is not None:
            pos = pos_to_cell(mx,my)
            # Ghost preview on grid
            if pos:
                r,c = pos
                g=cell_rect(r,c)
                can_plant = (self.plants[r][c] is None and self.can_afford(self.selected_idx) and self.seed_ready(self.selected_idx))
                color = (0,180,255,70) if can_plant else (255,0,0,70)
                overlay=pygame.Surface((g.w,g.h), pygame.SRCALPHA); overlay.fill(color)
                screen.blit(overlay, (g.x,g.y))
            # Ghost preview at cursor (simpler)
            name = self.seed_bank[self.selected_idx]["name"]
            if name.startswith("Pea"):
                pygame.draw.circle(screen, (0,255,0,100), (mx,my), 10)
            elif name.startswith("Sun"):
                pygame.draw.circle(screen, (255,255,0,100), (mx,my), 10)
            
    def draw(self, t, draw_ui=True):
        draw_day_sky(); self.app.draw_clouds()
        self.draw_grid()
        
        # mowers under plants/zombies
        for m in self.mowers: m.draw()
        # plants
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                p=self.plants[r][c]
                if p: p.draw()
        # bullets, zombies, suns
        for b in self.bullets: b.draw()
        for z in self.zombies: z.draw()
        for s in self.suns: s.draw()

        if draw_ui:
            draw_topbar(self.sun)
            self.draw_seed_bank()
            self.draw_cursor()
            
            # state overlays
            if self.state in ("win","lose"):
                ov=pygame.Surface((W,H), pygame.SRCALPHA); ov.fill((0,0,0,120))
                screen.blit(ov,(0,0))
                text_out(self.message, FONT_XL, WHITE, center=(W//2, H//2-10))
                text_out("Click to continue", FONT_M, WHITE, center=(W//2, H//2+26))
        
        draw_grass_band(t)
        
    def handle(self, events):
        for e in events:
            if e.type==pygame.QUIT: quit_now()
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_ESCAPE:
                    self.app.go(MainMenu(self.app))
                if e.key==pygame.K_m:
                    self.app.muted = not self.app.muted
                # hotkeys 1-5
                for i,s in enumerate(self.seed_bank):
                    if e.key==s["key"]:
                        if self.selected_idx==i: self.selected_idx=None
                        else:
                            self.selected_idx=i; self.shovel_selected=False
            
            if e.type==pygame.MOUSEBUTTONDOWN:
                mx,my = e.pos
                if e.button == 3: # Right-click to deselect
                    self.selected_idx = None
                    self.shovel_selected = False
                    return

                if e.button == 1:
                    if self.state in ("win","lose"):
                        # return to Adventure
                        self.app.go(AdventureMap(self.app)); return
                    # shovel?
                    if self.shovel_rect.collidepoint(mx,my):
                        self.shovel_selected = not self.shovel_selected
                        if self.shovel_selected: self.selected_idx=None
                        play(SND_CLICK)
                        return
                    # seed selection
                    for i,s in enumerate(self.seed_bank):
                        if s["rect"].collidepoint(mx,my):
                            if self.seed_ready(i) and self.can_afford(i):
                                self.selected_idx = i if self.selected_idx!=i else None
                                self.shovel_selected=False
                                play(SND_CLICK)
                            elif not self.seed_ready(i):
                                pass # play('cooldown')
                            elif not self.can_afford(i):
                                pass # play('negative')
                            return
                    # suns
                    for s in self.suns:
                        if s.rect().collidepoint(mx,my):
                            self.sun += s.val
                            s.dead=True
                            play(SND_POP)
                            return
                    # plant placement / shovel use
                    pos = pos_to_cell(mx,my)
                    if pos:
                        r,c = pos
                        if self.shovel_selected:
                            if self.plants[r][c]:
                                self.plants[r][c]=None # Dig up
                                play(SND_POP)
                            self.shovel_selected = False # Use shovel once
                            return
                        if self.selected_idx is not None:
                            if self.place_plant(r,c,self.selected_idx):
                                # successful plant, deselect
                                self.selected_idx = None
                            return

# ───────── MAIN LOOP ─────────
def main():
    global app
    app=App()
    app.go(MainMenu(app))
    t0=time.time()
    
    while True:
        # Get events
        events=pygame.event.get()
        
        # Calculate delta time
        dt=clock.tick(60)/1000.0
        
        # --- Update ---
        if app.scene: 
            # Scene handles its own events
            if hasattr(app.scene,'handle'): 
                app.scene.handle(events)
            
            # Scene updates its own logic
            if hasattr(app.scene,'update'): 
                app.scene.update(dt)
                
        # Global updates
        app.tick_clouds(dt)
        
        # --- Draw ---
        if app.scene and hasattr(app.scene,'draw'):
            app.scene.draw(time.time()-t0)
        else:
            # Fallback draw
            screen.fill((30,30,30))
            text_out("Error: No Scene", FONT_L, RED, center=(W//2, H//2))
            
        pygame.display.flip()

if __name__=="__main__":
    main()
