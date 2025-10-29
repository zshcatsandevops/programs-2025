#!/usr/bin/env python3
import pygame, sys, random, math
pygame.init()

# 600x400 Config (Original scale, PvZ1 grid ~9x5 tiles)
WIDTH, HEIGHT, FPS = 600, 400, 60
GRID_X, GRID_Y, CELL_W, CELL_H, ROWS, COLS = 80, 80, 50, 60, 5, 9
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ULTRA PVZ 1.0 [C] Samsoft - Procedural Replanted Edition")
clock = pygame.time.Clock()

# Colors (Enhanced palette for Replanted HD vibe: brighter, more saturated)
SKY, GRASS, BROWN, WHITE, RED, YELLOW, GREEN, DARK_GREEN, GRAY, BLACK = (
    (135,206,235),(34,139,34),(139,69,19),(255,255,255),
    (255,0,0),(255,255,0),(0,255,0),(0,100,0),(128,128,128),(0,0,0)
)
ZOMBIE_SKIN = (150, 100, 50)  # Greenish-gray for undead
PLANT_POT = (100, 50, 0)       # Terracotta brown

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
        s.vy=random.uniform(0.5,1.5);s.a=0;s.r=random.randint(8,12); s.pulse=0
    def update(s):
        s.y+=s.vy;s.a+=2; s.pulse += 0.1
        if s.y>HEIGHT:s.y=-s.r;s.x=random.randint(0,WIDTH)
    def draw(s):
        # Procedural glow with pulse animation
        glow_surf = pygame.Surface((s.r*4,s.r*4), pygame.SRCALPHA)
        pulse_r = s.r + math.sin(s.pulse) * 2  # HD shimmer
        pygame.draw.circle(glow_surf, (255,255,0,int(50 + math.sin(s.pulse)*20)), (s.r*2, s.r*2), int(pulse_r*2), 0)
        screen.blit(glow_surf, (s.x - s.r*2, s.y - s.r*2))
        # Sun body with procedural rays
        pygame.draw.circle(screen, YELLOW, (int(s.x), int(s.y)), s.r)
        for i in range(8):  # Ray burst
            ray_end = (s.x + math.cos(s.a + i*math.pi/4)*s.r*1.5, s.y + math.sin(s.a + i*math.pi/4)*s.r*1.5)
            pygame.draw.line(screen, YELLOW, (s.x, s.y), ray_end, 2)

class MenuGrass:
    def __init__(s,x):s.x=x;s.y=HEIGHT;s.amp=random.uniform(3,8); s.wave=0
    def update(s,t):s.ang=math.sin(t*0.01+s.x*0.01)*s.amp; s.wave += 0.05
    def draw(s):
        # Procedural waving blades with wind variation
        ex=s.x+s.ang;ey=s.y-random.randint(40,60)
        blade_points = [(s.x, s.y), (ex, ey), (ex + math.sin(s.wave)*2, ey - 5)]
        pygame.draw.polygon(screen, GRASS, blade_points, 0)
        # Veins for HD detail
        mid_x = (s.x + ex) / 2
        pygame.draw.line(screen, DARK_GREEN, (mid_x, s.y), (mid_x + s.ang/2, ey), 1)
        pygame.draw.circle(screen, DARK_GREEN, (int(ex), int(ey)), 2)

class MenuZombie:
    def __init__(s):
        s.x=WIDTH+random.randint(0,100);s.y=random.randint(GRID_Y,GRID_Y+ROWS*CELL_H)
        s.vx=-random.uniform(0.2,0.5);s.bob=0; s.limp=0
    def update(s):
        s.x+=s.vx;s.bob+=0.1;s.limp += 0.02; s.y+=math.sin(s.bob)*0.3 + math.sin(s.limp)*0.1
        if s.x<-30:s.x=WIDTH+random.randint(0,100)
    def draw(s):
        # Procedural zombie with limp animation and ragged edges
        surf = pygame.Surface((40,50), pygame.SRCALPHA)
        # Body with procedural tears
        body_rect = pygame.Rect(10, 20, 20, 25)
        pygame.draw.rect(surf, ZOMBIE_SKIN, body_rect)
        for _ in range(3):  # Ragged edges
            tear_x = random.randint(body_rect.left, body_rect.right)
            pygame.draw.line(surf, BLACK, (tear_x, body_rect.top), (tear_x, body_rect.bottom), 1)
        # Head
        pygame.draw.circle(surf, ZOMBIE_SKIN, (20, 10), 8)
        # Eyes with glow
        pygame.draw.circle(surf, RED, (16, 8), 2)
        pygame.draw.circle(surf, RED, (24, 8), 2)
        pygame.draw.circle(surf, WHITE, (16, 8), 1)
        pygame.draw.circle(surf, WHITE, (24, 8), 1)
        screen.blit(surf, (s.x, s.y))

class MenuTomb:
    def __init__(s):
        s.x=random.randint(0,WIDTH);s.y=random.randint(HEIGHT-150,HEIGHT-50)
        s.w=random.randint(20,40);s.h=random.randint(30,60);s.rot=random.randint(-10,10); s.crack=0
    def draw(s):
        s.crack += 0.01  # Procedural crack growth
        surf=pygame.Surface((s.w,s.h),pygame.SRCALPHA)
        pygame.draw.rect(surf,GRAY,(0,0,s.w,s.h))
        pygame.draw.rect(surf,BLACK,(0,0,s.w,s.h),2)
        # Cracks for weathered HD look
        crack_y = int(s.h * 0.5 + math.sin(s.crack)*5)
        pygame.draw.line(surf, BLACK, (s.w//2, 0), (s.w//2, s.h), 1)
        pygame.draw.line(surf, BLACK, (0, crack_y), (s.w, crack_y), 1)
        txt=font_small.render("RIP",True,BLACK)
        surf.blit(txt,txt.get_rect(center=(s.w//2,s.h//2)))
        rot=pygame.transform.rotate(surf,s.rot)
        screen.blit(rot,rot.get_rect(center=(s.x,s.y)))

# === GAME ENTITIES (PvZ Replanted Mechanics: Plants, Zombies, Modes) ===
class Sun:
    def __init__(s, x, y): 
        s.x, s.y = x, y; s.vy = 1; s.spin=0
    def update(s): s.y += s.vy; s.spin += 0.2
    def draw(s): 
        # Procedural spinning sun with gradient glow
        glow = pygame.Surface((40,40), pygame.SRCALPHA)
        for r in range(20, 0, -1):
            alpha = int(255 * (r / 20))
            col = (*YELLOW, alpha)
            pygame.draw.circle(glow, col, (20,20), r)
        screen.blit(glow, (s.x-20, s.y-20))
        # Rays with rotation
        for i in range(12):
            angle = s.spin + i * math.pi / 6
            end_x = s.x + math.cos(angle) * 15
            end_y = s.y + math.sin(angle) * 15
            pygame.draw.line(screen, YELLOW, (s.x, s.y), (end_x, end_y), 2)
        pygame.draw.circle(screen, (255, 255, 200), (int(s.x), int(s.y)), 8)  # Core
    def collect(s, x, y): return abs(x - s.x) < 20 and abs(y - s.y) < 20

class Pea:
    def __init__(s, x, y): s.x, s.y = x + 25, y + 20; s.v = 9; s.trail=0
    def update(s): s.x += s.v; s.trail += 1
    def draw(s): 
        # Procedural pea with motion trail
        if s.trail % 3 == 0:
            trail_surf = pygame.Surface((15,10), pygame.SRCALPHA)
            pygame.draw.ellipse(trail_surf, (0,200,0,50), (0,0,15,10))
            screen.blit(trail_surf, (s.x-15, s.y-5))
        # Pea body with shine
        pygame.draw.ellipse(screen, GREEN, (int(s.x)-5, int(s.y)-5, 10, 10))
        pygame.draw.circle(screen, (100,255,100), (int(s.x)+2, int(s.y)-2), 2)  # Highlight
    def hit(s, z): return z.x < s.x < z.x + 40 and z.y < s.y < z.y + 60

class Plant:
    def __init__(s, r, c, ptype):
        s.x = GRID_X + c * CELL_W; s.y = GRID_Y + r * CELL_H
        s.row = r; s.ptype = ptype; s.t = 0; s.hp = 6
        if ptype == 'wallnut': s.hp = 72
        s.cost = {'peashooter': 100, 'sunflower': 50, 'wallnut': 50}[ptype]
        s.grow = 0  # Procedural growth animation
    def update(s, peas, suns):
        s.t += 1; s.grow += 0.05
        if s.ptype == 'peashooter' and s.t % 85 == 0:
            peas.append(Pea(s.x, s.y))
        elif s.ptype == 'sunflower' and s.t % 1440 == 0:
            suns.append(Sun(s.x + 20, s.y))
    def draw(s):
        surf = pygame.Surface((50, 70), pygame.SRCALPHA)  # Plant canvas
        # Pot base (procedural cracks if damaged)
        pot_h = 20 + math.sin(s.grow) * 2
        pygame.draw.rect(surf, PLANT_POT, (5, 50, 40, pot_h))
        if s.hp < s.hp * 0.5:  # Cracks
            pygame.draw.line(surf, BLACK, (10, 50), (40, 50 + pot_h), 2)
        # Stem with veins
        stem_h = 30 + math.cos(s.grow) * 3
        pygame.draw.rect(surf, GREEN, (22, 20, 6, stem_h))
        for i in range(3):  # Veins
            vein_y = 25 + i*8
            pygame.draw.line(surf, DARK_GREEN, (22, vein_y), (28, vein_y + random.randint(-1,1)), 1)
        if s.ptype == 'peashooter':
            # Flower head with procedural petals
            head_y = 20
            pygame.draw.circle(surf, GREEN, (25, head_y), 12)
            for i in range(8):
                petal_angle = i * math.pi / 4
                petal_end = (25 + math.cos(petal_angle) * 15, head_y + math.sin(petal_angle) * 15)
                pygame.draw.ellipse(surf, (0, 200, 0), (petal_end[0]-3, petal_end[1]-3, 6, 6))
            # Mouth (shooting animation)
            mouth_w = 4 + math.sin(s.t * 0.2) * 2
            pygame.draw.rect(surf, BLACK, (22, head_y + 5, mouth_w, 3))
        elif s.ptype == 'sunflower':
            # Petals with rotation
            head_y = 20; rot = s.t * 0.01
            for i in range(12):
                angle = rot + i * math.pi / 6
                px = 25 + math.cos(angle) * 18
                py = head_y + math.sin(angle) * 18
                pygame.draw.ellipse(surf, YELLOW, (px-4, py-2, 8, 4))
            pygame.draw.circle(surf, (255, 255, 100), (25, head_y), 8)  # Center
        elif s.ptype == 'wallnut':
            # Nut shell with segments
            pygame.draw.ellipse(surf, BROWN, (10, 20, 30, 35))
            for i in range(6):  # Shell lines
                line_angle = i * math.pi / 3
                line_end_x = 25 + math.cos(line_angle) * 15
                line_end_y = 37.5 + math.sin(line_angle) * 17.5
                pygame.draw.line(surf, DARK_GREEN, (25, 37.5), (line_end_x, line_end_y), 2)
        screen.blit(surf, (s.x - 5, s.y - 10))

class Zombie:
    def __init__(s, r, ztype='normal'):
        s.x = WIDTH; s.y = GRID_Y + r * CELL_H
        s.ztype = ztype; s.v = 0.22; s.eating = False; s.eat_t = 0
        s.hp = {'normal': 10, 'conehead': 28, 'buckethead': 65}[ztype]
        s.retro = random.random() < 0.05
        s.shamble = 0  # Procedural walk cycle
    def update(s, plants):
        s.shamble += 0.1
        if not s.eating:
            s.x -= s.v
        else:
            s.eat_t += 1
            if s.eat_t % 60 == 0:
                s.target.hp -= 1
                if s.target.hp <= 0:
                    plants.remove(s.target)
                    s.eating = False; s.target = None
        if not s.eating:
            for p in plants:
                if p.row == (s.y - GRID_Y) // CELL_H and s.x < p.x + 40 < s.x + 40:
                    s.eating = True; s.target = p; s.eat_t = 0
                    break
    def draw(s):
        surf = pygame.Surface((50, 70), pygame.SRCALPHA)  # Larger for details
        # Legs with shamble bend
        leg_offset = math.sin(s.shamble) * 3
        pygame.draw.rect(surf, (80, 40, 20), (15 + leg_offset, 50, 8, 15))  # Left leg
        pygame.draw.rect(surf, (80, 40, 20), (27 - leg_offset, 50, 8, 15))  # Right leg
        # Body with suit texture
        body_h = 25 + (1 if s.eating else 0)
        pygame.draw.rect(surf, (50, 30, 10), (15, 25, 20, body_h))
        # Procedural buttons/tears
        for i in range(3):
            btn_y = 30 + i*6
            pygame.draw.circle(surf, BLACK, (25, btn_y), 1)
        if random.random() < 0.3:  # Tear
            pygame.draw.line(surf, BLACK, (35, 30), (45, 40), 2)
        # Arms (flailing if eating)
        arm_swing = math.sin(s.shamble * 2) * 5 if not s.eating else 0
        pygame.draw.rect(surf, ZOMBIE_SKIN, (8 + arm_swing, 30, 7, 15))  # Left arm
        pygame.draw.rect(surf, ZOMBIE_SKIN, (35 - arm_swing, 30, 7, 15))  # Right arm
        # Head with procedural drool if eating
        head_y = 15 + math.sin(s.shamble) * 1
        pygame.draw.circle(surf, ZOMBIE_SKIN, (25, head_y), 10)
        # Eyes (glowing red)
        eye_offset = math.sin(s.eat_t * 0.3) * 1 if s.eating else 0
        pygame.draw.circle(surf, RED, (20 + eye_offset, head_y - 2), 3)
        pygame.draw.circle(surf, RED, (30 - eye_offset, head_y - 2), 3)
        pygame.draw.circle(surf, WHITE, (20 + eye_offset, head_y - 2), 1)
        pygame.draw.circle(surf, WHITE, (30 - eye_offset, head_y - 2), 1)
        # Mouth with teeth
        mouth_w = 6 + (s.eat_t % 10 if s.eating else 0)
        pygame.draw.rect(surf, BLACK, (20, head_y + 4, mouth_w, 4))
        for i in range(3):
            tooth_x = 21 + i*2
            pygame.draw.rect(surf, WHITE, (tooth_x, head_y + 6, 1, 2))
        # Armor if applicable
        if s.ztype == 'conehead':
            cone_points = [(20, head_y - 12), (25, head_y - 20), (30, head_y - 12)]
            pygame.draw.polygon(surf, (255, 165, 0), cone_points)  # Orange cone
            pygame.draw.polygon(surf, BLACK, cone_points, 2)
        elif s.ztype == 'buckethead':
            pygame.draw.rect(surf, GRAY, (15, head_y - 15, 20, 10))
            pygame.draw.rect(surf, BLACK, (15, head_y - 15, 20, 10), 2)
        if s.retro:  # Pixelate effect
            for dx in range(0, 50, 5):
                for dy in range(0, 70, 5):
                    if surf.get_at((dx, dy))[3] > 0:
                        pygame.draw.rect(screen, surf.get_at((dx, dy))[:3], (s.x + dx//5*5, s.y + dy//5*5, 5, 5))
            return
        screen.blit(surf, (s.x - 5, s.y - 10))

class CrazyDave:
    def __init__(s):
        s.x=20;s.y=HEIGHT-80;s.t=0
        s.lines=["Wabbits?! No, ZOMBIES! Plant peas!","Click sun for points! DANG!","Ready? Let's grow!"]
        s.i=0;s.show=True; s.bob=0
    def update(s):
        s.t+=1; s.bob += 0.05
        if s.t>300:
            s.i=(s.i+1)%len(s.lines);s.t=0
            if s.i==0 and len(plants)>0:s.show=False
    def draw(s):
        if not s.show:return
        surf = pygame.Surface((40, 80), pygame.SRCALPHA)
        # Hat (pot) with procedural dents
        hat_y = -20 + math.sin(s.bob) * 1
        pygame.draw.ellipse(surf, (150, 75, 0), (5, hat_y, 30, 15))  # Pot
        for _ in range(2):  # Dents
            dent_x = random.randint(5, 35)
            pygame.draw.circle(surf, BLACK, (dent_x, hat_y + 7), 2)
        # Head with beard stubble
        pygame.draw.circle(surf, (255, 200, 150), (20, 0), 15)
        # Stubble
        for i in range(8):
            stubble_x = 10 + i*2
            pygame.draw.line(surf, BLACK, (stubble_x, 10), (stubble_x + random.randint(-1,1), 12), 1)
        # Eyes and mouth
        pygame.draw.circle(surf, BLACK, (15, -5), 2)
        pygame.draw.circle(surf, BLACK, (25, -5), 2)
        pygame.draw.arc(surf, BLACK, (15, 2, 10, 5), 0, math.pi, 2)  # Smile
        # Body (blue overalls)
        pygame.draw.rect(surf, (0,0,200), (10, 15, 20, 40))
        # Straps
        pygame.draw.line(surf, (100,100,255), (10, 20), (30, 20), 3)
        pygame.draw.line(surf, (100,100,255), (10, 35), (30, 35), 3)
        screen.blit(surf, (s.x, s.y + hat_y))
        # Bubble (unchanged)
        bub=pygame.Surface((200,60),pygame.SRCALPHA)
        pygame.draw.rect(bub,WHITE,(0,0,200,60),3)
        pygame.draw.polygon(bub,WHITE,[(150,0),(170,-10),(190,0)])
        txt=font_dave.render(s.lines[s.i],True,BLACK)
        bub.blit(txt,(10,10))
        screen.blit(bub,(s.x-50,s.y-60))

# === STATE INIT ===
suns, plants, peas, zombs = [], [], [], []
sun_pts, spawn, over, frame, wave = 50, 0, False, 0, 0
font = pygame.font.SysFont(None, 24)
dave = CrazyDave()
menu_active, tutorial_active, cloudy_mode = True, False, False
menu_t = 0
selected_plant = None
seed_types = ['peashooter', 'sunflower', 'wallnut', 'shovel']
seed_rects = [pygame.Rect(10 + i*60, 40, 50, 30) for i in range(len(seed_types))]

# Procedural menu setup
for _ in range(10): menu_suns.append(MenuSun())
for i in range(WIDTH//5): menu_grass.append(MenuGrass(i*5+random.randint(-2,2)))
for _ in range(2): menu_zombs.append(MenuZombie())
for _ in range(8): menu_tombs.append(MenuTomb())

# === MAIN LOOP ===
while True:
    frame += 1; clock.tick(FPS); menu_t += 1
    mouse = pygame.mouse.get_pos()
    for e in pygame.event.get():
        if e.type == pygame.QUIT: pygame.quit(); sys.exit()
        if e.type == pygame.MOUSEBUTTONDOWN:
            mx, my = e.pos
            if e.button == 1:  # Left-click
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
                    # Place plant or remove with shovel
                    if selected_plant:
                        r = (my - GRID_Y) // CELL_H; c = (mx - GRID_X) // CELL_W
                        if 0 <= r < ROWS and 0 <= c < COLS:
                            if selected_plant != 'shovel':
                                cost = {'peashooter': 100, 'sunflower': 50, 'wallnut': 50}.get(selected_plant, 0)
                                if sun_pts >= cost and not any(p.row == r and p.x == GRID_X + c * CELL_W for p in plants):
                                    plants.append(Plant(r, c, selected_plant))
                                    sun_pts -= cost
                                    selected_plant = None
                            else:
                                for p in plants[:]:
                                    if p.row == r and p.x == GRID_X + c * CELL_W:
                                        plants.remove(p)
                                        selected_plant = None
                                        break
            elif e.button == 3:  # Right-click to cancel
                selected_plant = None

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
        pulse = font_small.render("60 FPS | Procedural Rendering Engaged", True,
                                  YELLOW if math.sin(menu_t * 0.1) > 0 else RED)
        screen.blit(pulse, pulse.get_rect(center=(WIDTH//2, HEIGHT - 30)))

    else:
        sun_rate = 1440 if cloudy_mode else 720
        if random.randint(1, sun_rate) == 1: suns.append(Sun(random.randint(100, WIDTH - 100), random.randint(50, 150)))
        for s in suns: s.update()
        for p in plants: p.update(peas, suns)
        for pe in peas[:]:
            pe.update()
            for z in zombs[:]:
                if pe.hit(z):
                    z.hp -= 1; peas.remove(pe)
                    if z.hp <= 0: zombs.remove(z)
                    break
            if pe.x > WIDTH: peas.remove(pe)
        spawn += 1
        if spawn > 300:
            num_zombs = max(1, wave // 5 + 1)
            for _ in range(num_zombs):
                r = random.randint(0, ROWS - 1)
                chances = {'normal': 0.6, 'conehead': 0.3, 'buckethead': 0.1}
                ztype = random.choices(list(chances.keys()), weights=list(chances.values()))[0]
                zombs.append(Zombie(r, ztype))
            spawn = 0; wave += 1
        for z in zombs: z.update(plants)
        if any(z.x < 50 for z in zombs): over = True
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
        # Draw seed bar (procedural icons)
        for i, rect in enumerate(seed_rects):
            color = GREEN if selected_plant == seed_types[i] else GRAY
            pygame.draw.rect(screen, color, rect)
            if seed_types[i] == 'shovel':
                pygame.draw.line(screen, BROWN, (rect.x + 25, rect.y + 10), (rect.x + 25, rect.y + 25), 3)
                pygame.draw.rect(screen, GRAY, (rect.x + 20, rect.y + 25, 10, 5))
                txt = font_small.render("Shvl", True, BLACK)
                screen.blit(txt, (rect.x + 5, rect.y + 5))
            else:
                # Mini procedural plant preview
                preview_y = rect.y + 5
                if seed_types[i] == 'peashooter':
                    pygame.draw.rect(screen, GREEN, (rect.x + 20, preview_y + 15, 4, 10))
                    pygame.draw.circle(screen, GREEN, (rect.x + 22, preview_y + 5), 6)
                elif seed_types[i] == 'sunflower':
                    pygame.draw.rect(screen, GREEN, (rect.x + 20, preview_y + 15, 4, 10))
                    pygame.draw.circle(screen, YELLOW, (rect.x + 22, preview_y + 5), 6)
                elif seed_types[i] == 'wallnut':
                    pygame.draw.ellipse(screen, BROWN, (rect.x + 15, preview_y + 5, 20, 15))
                cost_txt = font_small.render(str({'peashooter': 100, 'sunflower': 50, 'wallnut': 50}[seed_types[i]]), True, BLACK)
                screen.blit(cost_txt, (rect.x + 5, rect.y + 20))

    pygame.display.flip()
