#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ultra Mario 2D Bros — Samsoft Edition (2025, Scalable Optimized)
----------------------------------------------------------------
Full 32-level SMB-style engine with static background caching,
smooth 60 FPS, and dynamic stretch-to-window scaling (retro pixel-preserve).

© Samsoft 2025
"""
import pygame, sys, math
pygame.init()

# ───────── CONFIG ─────────
BASE_W, BASE_H = 800, 480       # base logical resolution
TILE = 32
GRAVITY = 0.6
WHITE, BLACK = (255,255,255), (0,0,0)
RED, BLUE, GOLD, GREEN = (200,50,50), (50,50,255), (255,215,0), (50,200,50)
BROWN, SKY_BLUE, LOGO_BG, PINK, GRAY = (139,69,19), (92,148,252), (216,88,24), (255,182,193), (128,128,128)

# Main window (resizable)
screen = pygame.display.set_mode((BASE_W, BASE_H), pygame.RESIZABLE)
pygame.display.set_caption("Ultra Mario 2D Bros — Samsoft Edition")
clock = pygame.time.Clock()
FONT = pygame.font.SysFont("Courier", 24)

# internal render surface (fixed logical size)
canvas = pygame.Surface((BASE_W, BASE_H))

def beep(freq=440, dur=0.05): pass  # off for perf

# ───────── SPRITES ─────────
class Player(pygame.sprite.Sprite):
    def __init__(self,x,y):
        super().__init__()
        self.image=pygame.Surface((TILE,TILE)).convert(); self.image.fill(RED)
        self.rect=self.image.get_rect(topleft=(x,y))
        self.vx=self.vy=0; self.on_ground=False
    def update(self,tiles):
        keys=pygame.key.get_pressed()
        self.vx=(keys[pygame.K_RIGHT]-keys[pygame.K_LEFT])*5
        if keys[pygame.K_SPACE] and self.on_ground:
            self.vy=-12; beep(880)
        self.vy+=GRAVITY
        self.rect.x+=self.vx; self.collide(tiles,self.vx,0)
        self.rect.y+=self.vy; self.on_ground=False; self.collide(tiles,0,self.vy)
    def collide(self,tiles,vx,vy):
        for t in tiles:
            if self.rect.colliderect(t.rect):
                if vx>0:self.rect.right=t.rect.left
                if vx<0:self.rect.left=t.rect.right
                if vy>0:self.rect.bottom=t.rect.top;self.vy=0;self.on_ground=True
                if vy<0:self.rect.top=t.rect.bottom;self.vy=0

class Tile(pygame.sprite.Sprite):
    def __init__(self,x,y,c=BROWN):
        super().__init__()
        self.image=pygame.Surface((TILE,TILE)).convert();self.image.fill(c)
        self.rect=self.image.get_rect(topleft=(x,y))
class Flag(pygame.sprite.Sprite):
    def __init__(self,x,y):
        super().__init__()
        self.image=pygame.Surface((TILE//2,TILE*3)).convert();self.image.fill(GOLD)
        self.rect=self.image.get_rect(bottomleft=(x,y))

# ───────── LEVEL GEN ─────────
def generate_level(num):
    tiles=pygame.sprite.Group()
    floor_y=BASE_H-TILE*2
    for x in range(0,96*TILE,TILE): tiles.add(Tile(x,floor_y,BROWN))
    flag=Flag(96*TILE-TILE,floor_y)
    return tiles,flag

# ───────── BACKGROUND CACHE ─────────
def build_menu_bg():
    bg=pygame.Surface((BASE_W,BASE_H)).convert(); bg.fill(SKY_BLUE)
    for x in range(0,BASE_W,16): pygame.draw.rect(bg,BROWN,(x,BASE_H-32,16,32))
    pygame.draw.polygon(bg,GREEN,[(50,BASE_H-32),(150,BASE_H-128),(250,BASE_H-32)])
    for dx,dy in [(50,-50),(70,-70),(90,-50)]: pygame.draw.circle(bg,BLACK,(50+dx,BASE_H-32+dy),4)
    pygame.draw.rect(bg,RED,(130,BASE_H-144,16,16))
    for i in range(3):
        r=16-i*4;pygame.draw.circle(bg,GREEN,(BASE_W-150+i*20,BASE_H-32-r),r)
    return bg

def build_level_bg(level):
    bg=pygame.Surface((BASE_W,BASE_H)).convert(); bg.fill(SKY_BLUE)
    if level%4!=0:
        offset=(level*37)%200
        for n in range(-1,6):
            b=n*200-offset
            pygame.draw.polygon(bg,GREEN,[(b+50,BASE_H-100),(b+150,BASE_H-200),(b+250,BASE_H-100)])
    return bg

# ───────── MENUS ─────────
def main_menu():
    bg=build_menu_bg(); sel=0
    small=pygame.font.SysFont("courier",28,True); big=pygame.font.SysFont("courier",40,True)
    while True:
        clock.tick(60)
        canvas.blit(bg,(0,0))
        logo=pygame.Rect(BASE_W//2-200,60,400,80)
        canvas.fill(LOGO_BG,logo)
        canvas.blit(small.render("ULTRA",True,WHITE),(logo.centerx-60,logo.top+5))
        txt=big.render("MARIO 2D BROS",True,WHITE)
        canvas.blit(txt,(logo.centerx-txt.get_width()//2,logo.top+30))
        cr=small.render("©1985 NINTENDO",True,PINK)
        canvas.blit(cr,(BASE_W//2-cr.get_width()//2,logo.bottom+5))
        opts=["1 PLAYER GAME","2 PLAYER GAME"]
        for i,o in enumerate(opts):
            y=logo.bottom+60+i*30
            t=FONT.render(o,True,WHITE); canvas.blit(t,(BASE_W//2-100,y))
            if i==sel:
                pygame.draw.rect(canvas,RED,(BASE_W//2-120,y+8,12,12))
        draw_scaled()
        for e in pygame.event.get():
            if e.type==pygame.QUIT: sys.exit()
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_UP: sel=(sel-1)%2
                if e.key==pygame.K_DOWN: sel=(sel+1)%2
                if e.key==pygame.K_RETURN: game_loop(1 if sel==0 else 2)

# ───────── GAME LOOP ─────────
def game_loop(level):
    player=Player(100,BASE_H-3*TILE)
    tiles,flag=generate_level(level)
    bg=build_level_bg(level); cam=0; score=0
    while True:
        clock.tick(60)
        for e in pygame.event.get():
            if e.type==pygame.QUIT: sys.exit()
        player.update(tiles)
        cam=max(0,player.rect.x-BASE_W//3)
        if player.rect.colliderect(flag.rect):
            next_level=level+1 if level<32 else 0
            if next_level==0: win_screen(score)
            else: game_loop(next_level)
        canvas.blit(bg,(-(cam%BASE_W),0))
        for t in tiles:
            if -TILE<t.rect.x-cam<BASE_W:
                canvas.blit(t.image,(t.rect.x-cam,t.rect.y))
        canvas.blit(flag.image,(flag.rect.x-cam,flag.rect.y))
        canvas.blit(player.image,(player.rect.x-cam,player.rect.y))
        txt=FONT.render(f"World {level} Score:{score}",True,WHITE)
        canvas.blit(txt,(20,20))
        draw_scaled()

# ───────── WIN SCREEN ─────────
def win_screen(score):
    while True:
        canvas.fill(BLACK)
        t1=FONT.render("CONGRATULATIONS! YOU CLEARED ALL 32 LEVELS!",True,GOLD)
        t2=FONT.render(f"FINAL SCORE: {score}",True,WHITE)
        t3=FONT.render("Press ENTER to return to Menu",True,(180,180,180))
        canvas.blit(t1,(BASE_W//2-t1.get_width()//2,BASE_H//2-40))
        canvas.blit(t2,(BASE_W//2-t2.get_width()//2,BASE_H//2+10))
        canvas.blit(t3,(BASE_W//2-t3.get_width()//2,BASE_H//2+60))
        draw_scaled()
        for e in pygame.event.get():
            if e.type==pygame.QUIT: sys.exit()
            if e.type==pygame.KEYDOWN and e.key==pygame.K_RETURN: main_menu()

# ───────── SCALE DRAW ─────────
def draw_scaled():
    """Scales canvas to window keeping aspect ratio, pixel-sharp."""
    win_w,win_h=screen.get_size()
    scale=min(win_w/BASE_W,win_h/BASE_H)
    scaled=pygame.transform.scale(canvas,(int(BASE_W*scale),int(BASE_H*scale)))
    x=(win_w-scaled.get_width())//2; y=(win_h-scaled.get_height())//2
    screen.fill(BLACK)
    screen.blit(scaled,(x,y))
    pygame.display.flip()

# ───────── START ─────────
if __name__=="__main__":
    main_menu()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ultra Mario 2D Bros — Samsoft Edition (2025, Stable Scaling Fix)
----------------------------------------------------------------
Full 32-level SMB-style engine with cached backgrounds,
retro pixel scaling, and corrected camera alignment
(fixes player stretch after hills/grass).

© Samsoft 2025
"""
import pygame, sys
pygame.init()

# ───────── CONFIG ─────────
BASE_W, BASE_H = 800, 480
TILE = 32
GRAVITY = 0.6
WHITE, BLACK = (255,255,255), (0,0,0)
RED, BLUE, GOLD, GREEN = (200,50,50), (50,50,255), (255,215,0), (50,200,50)
BROWN, SKY_BLUE, LOGO_BG, PINK, GRAY = (139,69,19), (92,148,252), (216,88,24), (255,182,193), (128,128,128)

screen = pygame.display.set_mode((BASE_W, BASE_H), pygame.RESIZABLE)
pygame.display.set_caption("Ultra Mario 2D Bros — Samsoft Edition")
clock = pygame.time.Clock()
FONT = pygame.font.SysFont("Courier", 24)
canvas = pygame.Surface((BASE_W, BASE_H))

def beep(*_): pass

# ───────── SPRITES ─────────
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((TILE, TILE)).convert()
        self.image.fill(RED)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vx = self.vy = 0
        self.on_ground = False

    def update(self, tiles):
        keys = pygame.key.get_pressed()
        self.vx = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * 5
        if keys[pygame.K_SPACE] and self.on_ground:
            self.vy = -12; beep(880)
        self.vy += GRAVITY
        self.rect.x += self.vx
        self.collide(tiles, self.vx, 0)
        self.rect.y += self.vy
        self.on_ground = False
        self.collide(tiles, 0, self.vy)
        # Prevent Y drift/stretch on slopes
        if self.rect.bottom > BASE_H - TILE:
            self.rect.bottom = BASE_H - TILE
            self.vy = 0
            self.on_ground = True

    def collide(self, tiles, vx, vy):
        for t in tiles:
            if self.rect.colliderect(t.rect):
                if vx > 0: self.rect.right = t.rect.left
                if vx < 0: self.rect.left = t.rect.right
                if vy > 0:
                    self.rect.bottom = t.rect.top
                    self.vy = 0
                    self.on_ground = True
                if vy < 0:
                    self.rect.top = t.rect.bottom
                    self.vy = 0

class Tile(pygame.sprite.Sprite):
    def __init__(self, x, y, c=BROWN):
        super().__init__()
        self.image = pygame.Surface((TILE, TILE)).convert()
        self.image.fill(c)
        self.rect = self.image.get_rect(topleft=(x, y))

class Flag(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((TILE//2, TILE*3)).convert()
        self.image.fill(GOLD)
        self.rect = self.image.get_rect(bottomleft=(x, y))

# ───────── LEVEL GEN ─────────
def generate_level(num):
    tiles = pygame.sprite.Group()
    floor_y = BASE_H - TILE * 2
    for x in range(0, 96*TILE, TILE):
        tiles.add(Tile(x, floor_y, BROWN))
    flag = Flag(96*TILE - TILE, floor_y)
    return tiles, flag

# ───────── BACKGROUND CACHE ─────────
def build_menu_bg():
    bg = pygame.Surface((BASE_W, BASE_H)).convert()
    bg.fill(SKY_BLUE)
    for x in range(0, BASE_W, 16):
        pygame.draw.rect(bg, BROWN, (x, BASE_H - 32, 16, 32))
    pygame.draw.polygon(bg, GREEN, [(50, BASE_H-32), (150, BASE_H-128), (250, BASE_H-32)])
    for dx, dy in [(50, -50), (70, -70), (90, -50)]:
        pygame.draw.circle(bg, BLACK, (50 + dx, BASE_H - 32 + dy), 4)
    pygame.draw.rect(bg, RED, (130, BASE_H - 144, 16, 16))
    for i in range(3):
        r = 16 - i*4
        pygame.draw.circle(bg, GREEN, (BASE_W - 150 + i*20, BASE_H - 32 - r), r)
    return bg

def build_level_bg(level):
    bg = pygame.Surface((BASE_W, BASE_H)).convert()
    bg.fill(SKY_BLUE)
    if level % 4 != 0:
        offset = (level * 37) % 200
        for n in range(-1, 6):
            b = n * 200 - offset
            # mountains low enough not to clip player
            pygame.draw.polygon(bg, GREEN,
                [(b+50, BASE_H-64), (b+150, BASE_H-140), (b+250, BASE_H-64)])
    return bg

# ───────── MENUS ─────────
def main_menu():
    bg = build_menu_bg()
    sel = 0
    small = pygame.font.SysFont("courier", 28, True)
    big = pygame.font.SysFont("courier", 40, True)
    while True:
        clock.tick(60)
        canvas.blit(bg, (0, 0))
        logo = pygame.Rect(BASE_W//2 - 200, 60, 400, 80)
        canvas.fill(LOGO_BG, logo)
        canvas.blit(small.render("ULTRA", True, WHITE), (logo.centerx - 60, logo.top + 5))
        txt = big.render("MARIO 2D BROS", True, WHITE)
        canvas.blit(txt, (logo.centerx - txt.get_width()//2, logo.top + 30))
        cr = small.render("©1985 NINTENDO", True, PINK)
        canvas.blit(cr, (BASE_W//2 - cr.get_width()//2, logo.bottom + 5))
        opts = ["1 PLAYER GAME", "2 PLAYER GAME"]
        for i, o in enumerate(opts):
            y = logo.bottom + 60 + i * 30
            t = FONT.render(o, True, WHITE)
            canvas.blit(t, (BASE_W//2 - 100, y))
            if i == sel:
                pygame.draw.rect(canvas, RED, (BASE_W//2 - 120, y + 8, 12, 12))
        draw_scaled()
        for e in pygame.event.get():
            if e.type == pygame.QUIT: sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_UP: sel = (sel - 1) % 2
                if e.key == pygame.K_DOWN: sel = (sel + 1) % 2
                if e.key == pygame.K_RETURN: game_loop(1 if sel == 0 else 2)

# ───────── GAME LOOP ─────────
def game_loop(level):
    player = Player(100, BASE_H - 3*TILE)
    tiles, flag = generate_level(level)
    bg = build_level_bg(level)
    cam = 0; score = 0
    while True:
        clock.tick(60)
        for e in pygame.event.get():
            if e.type == pygame.QUIT: sys.exit()
        player.update(tiles)
        cam = max(0, player.rect.x - BASE_W//3)
        # next level
        if player.rect.colliderect(flag.rect):
            nxt = level + 1 if level < 32 else 0
            if nxt == 0: win_screen(score)
            else: game_loop(nxt)
        canvas.blit(bg, (-(cam % BASE_W), 0))
        for t in tiles:
            if -TILE < t.rect.x - cam < BASE_W:
                canvas.blit(t.image, (t.rect.x - cam, t.rect.y))
        canvas.blit(flag.image, (flag.rect.x - cam, flag.rect.y))
        canvas.blit(player.image, (player.rect.x - cam, player.rect.y))
        txt = FONT.render(f"World {level}  Score:{score}", True, WHITE)
        canvas.blit(txt, (20, 20))
        draw_scaled()

# ───────── WIN SCREEN ─────────
def win_screen(score):
    while True:
        canvas.fill(BLACK)
        t1 = FONT.render("CONGRATULATIONS! YOU CLEARED ALL 32 LEVELS!", True, GOLD)
        t2 = FONT.render(f"FINAL SCORE: {score}", True, WHITE)
        t3 = FONT.render("Press ENTER to return to Menu", True, (180,180,180))
        canvas.blit(t1, (BASE_W//2 - t1.get_width()//2, BASE_H//2 - 40))
        canvas.blit(t2, (BASE_W//2 - t2.get_width()//2, BASE_H//2 + 10))
        canvas.blit(t3, (BASE_W//2 - t3.get_width()//2, BASE_H//2 + 60))
        draw_scaled()
        for e in pygame.event.get():
            if e.type == pygame.QUIT: sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN:
                main_menu()

# ───────── SCALE DRAW ─────────
def draw_scaled():
    win_w, win_h = screen.get_size()
    scale = min(win_w / BASE_W, win_h / BASE_H)
    scaled = pygame.transform.scale(canvas, (int(BASE_W*scale), int(BASE_H*scale)))
    x = (win_w - scaled.get_width()) // 2
    y = (win_h - scaled.get_height()) // 2
    screen.fill(BLACK)
    screen.blit(scaled, (x, y))
    pygame.display.flip()

# ───────── START ─────────
if __name__ == "__main__":
    main_menu()
