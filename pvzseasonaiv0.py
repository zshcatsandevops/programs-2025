#!/usr/bin/env python3
import pygame, sys, random, math
pygame.init()

# 600x400 Config (Original scale, PvZ1 grid ~9x5 tiles)
WIDTH, HEIGHT, FPS = 600, 400, 60
GRID_X, GRID_Y, CELL_W, CELL_H, ROWS, COLS = 80, 80, 50, 60, 5, 9
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ULTRA PVZ 1.0 [C] Samsoft - Procedural Replanted Edition")
clock = pygame.time.Clock()

# Colors (Enhanced palette)
SKY, GRASS, BROWN, WHITE, RED, YELLOW, GREEN, DARK_GREEN, GRAY, BLACK = (
    (135,206,235),(34,139,34),(139,69,19),(255,255,255),
    (255,0,0),(255,255,0),(0,255,0),(0,100,0),(128,128,128),(0,0,0)
)

# === MENU SYSTEM ===
class MenuButton:
    def __init__(self,x,y,w,h,text,color=GREEN,hover_color=YELLOW,action=None):
        self.rect=pygame.Rect(x,y,w,h)
        self.text=text;self.color=color;self.hover_color=hover_color
        self.action=action;self.font=pygame.font.SysFont('Arial',24,True)
    def draw(self,screen,hovered=False):
        color=self.hover_color if hovered else self.color
        pygame.draw.rect(screen,color,self.rect);pygame.draw.rect(screen,WHITE,self.rect,3)
        t=self.font.render(self.text,True,BLACK)
        screen.blit(t,t.get_rect(center=self.rect.center))
    def handle_click(self):
        if self.action:self.action()

menu_suns,menu_grass,menu_zombs,menu_tombs=[],[],[],[]
font_title=pygame.font.SysFont('Arial',36,True)
font_small=pygame.font.SysFont('Arial',18)
font_dave=pygame.font.SysFont('Arial',20,italic=True)

def start_standard(): 
    global menu_active, tutorial_active, cloudy_mode
    menu_active=False; tutorial_active=True; cloudy_mode=False
def start_cloudy(): 
    global menu_active, tutorial_active, cloudy_mode
    menu_active=False; tutorial_active=True; cloudy_mode=True
def quit_game(): 
    pygame.quit();sys.exit()

buttons=[MenuButton(WIDTH//2-100,HEIGHT//2-60,200,40,"STANDARD MODE",action=start_standard),
         MenuButton(WIDTH//2-100,HEIGHT//2-10,200,40,"CLOUDY DAY MODE",action=start_cloudy),
         MenuButton(WIDTH//2-80,HEIGHT//2+40,160,40,"QUIT",RED,action=quit_game)]

class MenuSun:
    def __init__(s):
        s.x=random.randint(0,WIDTH);s.y=random.randint(0,HEIGHT//2)
        s.vy=random.uniform(0.5,1.5);s.a=0;s.r=random.randint(8,12)
    def update(s):
        s.y+=s.vy;s.a+=2
        if s.y>HEIGHT:s.y=-s.r;s.x=random.randint(0,WIDTH)
    def draw(s):
        glow=pygame.Surface((s.r*4,s.r*4),pygame.SRCALPHA)
        pygame.draw.circle(glow,(255,255,0,50),(s.r*2,s.r*2),s.r*2)
        screen.blit(glow,(s.x-s.r*2,s.y-s.r*2))
        pygame.draw.circle(screen,YELLOW,(int(s.x),int(s.y)),s.r)

class MenuGrass:
    def __init__(s,x):s.x=x;s.y=HEIGHT;s.amp=random.uniform(3,8)
    def update(s,t):s.ang=math.sin(t*0.01+s.x*0.01)*s.amp
    def draw(s):
        ex=s.x+s.ang;ey=s.y-random.randint(40,60)
        pygame.draw.line(screen,GRASS,(s.x,s.y),(ex,ey),2)
        pygame.draw.circle(screen,DARK_GREEN,(int(ex),int(ey)),2)

class MenuZombie:
    def __init__(s):
        s.x=WIDTH+random.randint(0,100);s.y=random.randint(GRID_Y,GRID_Y+ROWS*CELL_H)
        s.vx=-random.uniform(0.2,0.5);s.bob=0
    def update(s):
        s.x+=s.vx;s.bob+=0.1;s.y+=math.sin(s.bob)*0.3
        if s.x<-30:s.x=WIDTH+random.randint(0,100)
    def draw(s):
        a=pygame.Surface((40,50),pygame.SRCALPHA)
        pygame.draw.rect(a,(100,50,50,128),(0,0,40,50))
        pygame.draw.circle(a,RED,(13,13),3);pygame.draw.circle(a,RED,(27,13),3)
        screen.blit(a,(s.x,s.y))

class MenuTomb:
    def __init__(s):
        s.x=random.randint(0,WIDTH);s.y=random.randint(HEIGHT-150,HEIGHT-50)
        s.w=random.randint(20,40);s.h=random.randint(30,60);s.rot=random.randint(-10,10)
    def draw(s):
        surf=pygame.Surface((s.w,s.h),pygame.SRCALPHA)
        pygame.draw.rect(surf,GRAY,(0,0,s.w,s.h))
        pygame.draw.rect(surf,BLACK,(0,0,s.w,s.h),2)
        txt=font_small.render("RIP",True,BLACK)
        surf.blit(txt,txt.get_rect(center=(s.w//2,s.h//2)))
        rot=pygame.transform.rotate(surf,s.rot)
        screen.blit(rot,rot.get_rect(center=(s.x,s.y)))

# === GAME ENTITIES (PvZ Replanted Mechanics: Plants, Zombies, Modes) ===
class Sun:
    def __init__(s, x, y): 
        s.x, s.y = x, y
        s.vy = 1
    def update(s): s.y += s.vy
    def draw(s): pygame.draw.circle(screen, YELLOW, (int(s.x), int(s.y)), 15)
    def collect(s, x, y): return abs(x - s.x) < 20 and abs(y - s.y) < 20

class Pea:
    def __init__(s, x, y): s.x, s.y = x + 25, y + 20; s.v = 9
    def update(s): s.x += s.v
    def draw(s): pygame.draw.circle(screen, GREEN, (int(s.x), int(s.y)), 5)
    def hit(s, z): return z.x < s.x < z.x + 40 and z.y < s.y < z.y + 60

class Plant:
    def __init__(s, r, c, ptype):
        s.x = GRID_X + c * CELL_W; s.y = GRID_Y + r * CELL_H
        s.row = r; s.ptype = ptype; s.t = 0; s.hp = 6  # Default hp ~300 dmg units /50 bite
        if ptype == 'wallnut': s.hp = 72  # ~4000 dmg
        s.cost = {'peashooter': 100, 'sunflower': 50, 'wallnut': 50}[ptype]
    def update(s, peas, suns):
        s.t += 1
        if s.ptype == 'peashooter' and s.t % 85 == 0:
            peas.append(Pea(s.x, s.y))
        elif s.ptype == 'sunflower' and s.t % 1440 == 0:
            suns.append(Sun(s.x + 20, s.y))
    def draw(s):
        color = GREEN if s.ptype in ['peashooter', 'sunflower'] else BROWN
        pygame.draw.rect(screen, color, (s.x + 5, s.y + 5, 40, 50))
        if s.ptype == 'sunflower':
            pygame.draw.circle(screen, YELLOW, (int(s.x + 25), int(s.y + 30)), 10)
        elif s.ptype == 'wallnut':
            pygame.draw.ellipse(screen, BROWN, (s.x + 5, s.y + 5, 40, 50))

class Zombie:
    def __init__(s, r, ztype='normal'):
        s.x = WIDTH; s.y = GRID_Y + r * CELL_H
        s.ztype = ztype; s.v = 0.22; s.eating = False; s.eat_t = 0
        s.hp = {'normal': 10, 'conehead': 28, 'buckethead': 65}[ztype]
        s.retro = random.random() < 0.05  # Rare secret retro skin
    def update(s, plants):
        if not s.eating:
            s.x -= s.v
        else:
            s.eat_t += 1
            if s.eat_t % 60 == 0:  # Bite every 1s
                s.target.hp -= 1
                if s.target.hp <= 0:
                    plants.remove(s.target)
                    s.eating = False; s.target = None
        # Check for plant collision
        if not s.eating:
            for p in plants:
                if p.row == (s.y - GRID_Y) // CELL_H and s.x < p.x + 40 < s.x + 40:
                    s.eating = True; s.target = p; s.eat_t = 0
                    break
    def draw(s):
        if s.retro:  # Pixelated secret
            a = pygame.Surface((40, 60), pygame.SRCALPHA)
            for i in range(0, 40, 4):
                for j in range(0, 60, 4):
                    pygame.draw.rect(a, (100,50,50), (i, j, 4, 4))
        else:
            a = pygame.Surface((40, 60), pygame.SRCALPHA)
            pygame.draw.rect(a, (100,50,50,128), (0,0,40,60))
        pygame.draw.circle(a, RED, (13,13),3); pygame.draw.circle(a, RED, (27,13),3)
        if s.ztype == 'conehead':
            pygame.draw.polygon(a, BROWN, [(10,0), (20, -10), (30,0)])
        elif s.ztype == 'buckethead':
            pygame.draw.rect(a, GRAY, (5,0,30,10))
        screen.blit(a, (s.x, s.y))

class CrazyDave:
    def __init__(s):
        s.x=20;s.y=HEIGHT-80;s.t=0
        s.lines=["Wabbits?! No, ZOMBIES! Plant peas!","Click sun for points! DANG!","Ready? Let's grow!"]
        s.i=0;s.show=True
    def update(s):
        s.t+=1
        if s.t>300:
            s.i=(s.i+1)%len(s.lines);s.t=0
            if s.i==0 and len(plants)>0:s.show=False
    def draw(s):
        if not s.show:return
        pygame.draw.rect(screen,(0,0,255),(s.x+10,s.y+20,20,40))
        pygame.draw.rect(screen,(255,200,150),(s.x+5,s.y-10,30,30))
        pygame.draw.ellipse(screen,BROWN,(s.x,s.y-30,40,20))
        pygame.draw.rect(screen,BROWN,(s.x+15,s.y-30,10,15))
        bub=pygame.Surface((200,60),pygame.SRCALPHA)
        pygame.draw.rect(bub,WHITE,(0,0,200,60),3)
        pygame.draw.polygon(bub,WHITE,[(150,0),(170,-10),(190,0)])  # Tail fix
        txt=font_dave.render(s.lines[s.i],True,BLACK)
        bub.blit(txt,(10,10))
        screen.blit(bub,(s.x-50,s.y-60))

# === STATE INIT ===
suns, plants, peas, zombs = [], [], [], []
sun_pts, spawn, over, frame, wave = 50, 0, False, 0, 0  # Start 50 sun
font = pygame.font.SysFont(None, 24)
dave = CrazyDave()
menu_active, tutorial_active, cloudy_mode = True, False, False
menu_t = 0
selected_plant = None  # For seed selection
seed_types = ['peashooter', 'sunflower', 'wallnut']
seed_rects = [pygame.Rect(10 + i*60, 40, 50, 30) for i in range(len(seed_types))]

# procedural menu setup
for _ in range(10):menu_suns.append(MenuSun())
for i in range(WIDTH//5):menu_grass.append(MenuGrass(i*5+random.randint(-2,2)))
for _ in range(2):menu_zombs.append(MenuZombie())
for _ in range(8):menu_tombs.append(MenuTomb())

# === MAIN LOOP ===
while True:
    frame += 1; clock.tick(FPS); menu_t += 1
    mouse = pygame.mouse.get_pos()
    for e in pygame.event.get():
        if e.type == pygame.QUIT: pygame.quit(); sys.exit()
        if e.type == pygame.MOUSEBUTTONDOWN:
            mx, my = e.pos
            if menu_active:
                for b in buttons:
                    if b.rect.collidepoint(mx, my): b.handle_click()
            else:
                # Collect sun
                for s in suns[:]:
                    if s.collect(mx, my): sun_pts += 25; suns.remove(s); break
                # Select seed
                for i, rect in enumerate(seed_rects):
                    if rect.collidepoint(mx, my):
                        selected_plant = seed_types[i]
                        break
                # Place plant
                if selected_plant:
                    r = (my - GRID_Y) // CELL_H; c = (mx - GRID_X) // CELL_W
                    cost = {'peashooter': 100, 'sunflower': 50, 'wallnut': 50}[selected_plant]
                    if 0 <= r < ROWS and 0 <= c < COLS and sun_pts >= cost:
                        if not any(p.row == r and p.x == GRID_X + c * CELL_W for p in plants):
                            plants.append(Plant(r, c, selected_plant))
                            sun_pts -= cost
                            selected_plant = None  # Reset after place

    if menu_active:
        for m in menu_suns: m.update()
        for z in menu_zombs: z.update()
        for g in menu_grass: g.update(menu_t)
        screen.fill(SKY)
        pygame.draw.rect(screen, GRASS, (0, HEIGHT - 100, WIDTH, 100))
        for g in menu_grass: g.draw()
        for t in menu_tombs: t.draw()
        for m in menu_suns: m.draw()
        for z in menu_zombs: z.draw()
        title = font_title.render("ULTRA PVZ 1.0 Replanted", True, WHITE)
        screen.blit(title, title.get_rect(center=(WIDTH//2, HEIGHT//4)))
        sub = font_small.render("[C] Samsoft | Procedural Replanted Edition", True, WHITE)
        screen.blit(sub, sub.get_rect(center=(WIDTH//2, HEIGHT//4 + 40)))
        for b in buttons: b.draw(screen, b.rect.collidepoint(mouse))
        pulse = font_small.render("60 FPS | Famicom Velocity Engaged", True,
                                  YELLOW if math.sin(menu_t * 0.1) > 0 else RED)
        screen.blit(pulse, pulse.get_rect(center=(WIDTH//2, HEIGHT - 30)))

    else:
        # Sun spawn rate: normal 1/720 (~12s), cloudy 1/1440 (~24s)
        sun_rate = 1440 if cloudy_mode else 720
        if random.randint(1, sun_rate) == 1: suns.append(Sun(random.randint(100, WIDTH - 100), random.randint(50, 150)))
        for s in suns: s.update()
        
        # Plant updates
        for p in plants: p.update(peas, suns)
        
        # Pea updates and hits
        for pe in peas[:]:
            pe.update()
            for z in zombs[:]:
                if pe.hit(z):
                    z.hp -= 1; peas.remove(pe)
                    if z.hp <= 0: zombs.remove(z)
                    break
            if pe.x > WIDTH: peas.remove(pe)
        
        # Zombie spawn: wave system
        spawn += 1
        if spawn > 300:  # ~5s per wave
            num_zombs = max(1, wave // 5 + 1)  # Increase with waves
            for _ in range(num_zombs):
                r = random.randint(0, ROWS - 1)
                chances = {'normal': 0.6, 'conehead': 0.3, 'buckethead': 0.1}
                ztype = random.choices(list(chances.keys()), weights=list(chances.values()))[0]
                zombs.append(Zombie(r, ztype))
            spawn = 0; wave += 1
        
        # Zombie updates
        for z in zombs: z.update(plants)
        
        # Game over check
        if any(z.x < 50 for z in zombs): over = True
        
        # Draw game
        screen.fill(SKY)
        pygame.draw.rect(screen, GRASS, (0, GRID_Y + CELL_H * ROWS, WIDTH, HEIGHT - (GRID_Y + CELL_H * ROWS)))
        for r in range(ROWS):
            for c in range(COLS):
                pygame.draw.rect(screen, BROWN, (GRID_X + c * CELL_W, GRID_Y + r * CELL_H, CELL_W - 1, CELL_H - 1), 1)
        for s in suns: s.draw()
        for p in plants: p.draw()
        for pe in peas: pe.draw()
        for z in zombs: z.draw()
        screen.blit(font.render(f"Sun: {sun_pts}", True, WHITE), (10, 10))
        if tutorial_active:
            dave.update(); dave.draw()
            if len(plants) > 0 and len(zombs) > 0: tutorial_active = False
        if over:
            msg = font.render("Zombies ate your brains!", True, RED)
            screen.blit(msg, (200, 180))
        
        # Draw seed bar
        for i, rect in enumerate(seed_rects):
            pygame.draw.rect(screen, GREEN if selected_plant == seed_types[i] else GRAY, rect)
            txt = font_small.render(seed_types[i][:4], True, BLACK)  # Short name
            screen.blit(txt, (rect.x + 5, rect.y + 5))
            cost_txt = font_small.render(str({'peashooter': 100, 'sunflower': 50, 'wallnut': 50}[seed_types[i]]), True, BLACK)
            screen.blit(cost_txt, (rect.x + 5, rect.y + 15))

    pygame.display.flip()
