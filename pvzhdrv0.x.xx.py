#!/usr/bin/env python3  
import pygame, sys, random, math  
pygame.init()  

# === CONFIG ===  
WIDTH, HEIGHT, FPS = 600, 400, 60  
GRID_X, GRID_Y, CELL_W, CELL_H, ROWS, COLS = 80, 80, 50, 60, 5, 9  
screen = pygame.display.set_mode((WIDTH, HEIGHT))  
pygame.display.set_caption("ULTRA PVZ 1.0 [C] Samsoft - PVZ: Modded Vol AI Edition (2000s Vector Crank + DLSS Sim)")  
clock = pygame.time.Clock()  

# === COLORS ===  
SKY, GRASS, BROWN, WHITE, RED, YELLOW, GREEN, DARK_GREEN, GRAY, BLACK = (  
    (135,206,235),(34,139,34),(139,69,19),(255,255,255),  
    (255,0,0),(255,255,0),(0,255,0),(0,100,0),(128,128,128),(0,0,0)  
)  
ZOMBIE_SKIN=(150,100,50)  
PLANT_POT=(100,50,0)  
SHADOW=(0,0,0,64)  
GOLD=(255,215,0)  

UPSAMPLE_SCALE=2  
UPSAMPLE_W,UPSAMPLE_H=WIDTH*UPSAMPLE_SCALE,HEIGHT*UPSAMPLE_SCALE  

# === LEVEL DATA FROM PVZ1 ===  
level_data = {  
    "1-1": {"flags": 0, "zombies": ['Zombie'], "special": None},  
    "1-2": {"flags": 1, "zombies": ['Zombie', 'Flag Zombie'], "special": None},  
    "1-3": {"flags": 1, "zombies": ['Zombie', 'Flag Zombie', 'Conehead Zombie'], "special": None},  
    "1-4": {"flags": 1, "zombies": ['Zombie', 'Flag Zombie', 'Conehead Zombie'], "special": None},  
    "1-5": {"flags": 1, "zombies": ['Zombie', 'Flag Zombie', 'Conehead Zombie'], "special": 'wallnut_bowling'},  
    "1-6": {"flags": 1, "zombies": ['Zombie', 'Flag Zombie', 'Conehead Zombie', 'Pole Vaulting Zombie'], "special": None},  
    "1-7": {"flags": 2, "zombies": ['Zombie', 'Flag Zombie', 'Conehead Zombie', 'Pole Vaulting Zombie'], "special": None},  
    "1-8": {"flags": 1, "zombies": ['Zombie', 'Flag Zombie', 'Conehead Zombie', 'Buckethead Zombie'], "special": None},  
    "1-9": {"flags": 2, "zombies": ['Zombie', 'Flag Zombie', 'Conehead Zombie', 'Pole Vaulting Zombie', 'Buckethead Zombie'], "special": None},  
    "1-10": {"flags": 2, "zombies": ['Zombie', 'Flag Zombie', 'Conehead Zombie', 'Pole Vaulting Zombie', 'Buckethead Zombie'], "special": 'conveyor'},  
    "2-1": {"flags": 1, "zombies": ['Zombie', 'Flag Zombie', 'Newspaper Zombie'], "special": None, "graves": True},  
    "2-2": {"flags": 2, "zombies": ['Zombie', 'Flag Zombie', 'Conehead Zombie', 'Buckethead Zombie', 'Newspaper Zombie'], "special": None, "graves": True},  
    "2-3": {"flags": 1, "zombies": ['Zombie', 'Flag Zombie', 'Conehead Zombie', 'Screen Door Zombie'], "special": None, "graves": True},  
    "2-4": {"flags": 2, "zombies": ['Zombie', 'Flag Zombie', 'Conehead Zombie', 'Pole Vaulting Zombie', 'Screen Door Zombie'], "special": None, "graves": True},  
    "2-5": {"flags": 0, "zombies": ['Zombie', 'Conehead Zombie', 'Buckethead Zombie'], "special": 'mini-game', "graves": True},  
    "2-6": {"flags": 1, "zombies": ['Zombie', 'Flag Zombie', 'Conehead Zombie', 'Football Zombie'], "special": None, "graves": True},  
    "2-7": {"flags": 2, "zombies": ['Zombie', 'Flag Zombie', 'Conehead Zombie', 'Screen Door Zombie', 'Football Zombie'], "special": None, "graves": True},  
    "2-8": {"flags": 1, "zombies": ['Zombie', 'Flag Zombie', 'Conehead Zombie', 'Dancing Zombie', 'Backup Dancer'], "special": None, "graves": True},  
    "2-9": {"flags": 2, "zombies": ['Zombie', 'Flag Zombie', 'Conehead Zombie', 'Screen Door Zombie', 'Dancing Zombie', 'Backup Dancer'], "special": None, "graves": True},  
    "2-10": {"flags": 2, "zombies": ['Zombie', 'Flag Zombie', 'Conehead Zombie', 'Screen Door Zombie', 'Football Zombie', 'Dancing Zombie', 'Backup Dancer'], "special": 'conveyor', "graves": True},  
    "3-1": {"flags": 1, "zombies": ['Zombie', 'Flag Zombie', 'Conehead Zombie', 'Ducky Tube Zombie'], "special": None},  
    "3-2": {"flags": 2, "zombies": ['Zombie', 'Flag Zombie', 'Conehead Zombie', 'Buckethead Zombie', 'Newspaper Zombie', 'Football Zombie', 'Ducky Tube Zombie'], "special": None},  
    "3-3": {"flags": 2, "zombies": ['Zombie', 'Flag Zombie', 'Conehead Zombie', 'Ducky Tube Zombie', 'Snorkel Zombie'], "special": None},  
    "3-4": {"flags": 3, "zombies": ['Zombie', 'Flag Zombie', 'Conehead Zombie', 'Pole Vaulting Zombie', 'Buckethead Zombie', 'Newspaper Zombie', 'Ducky Tube Zombie', 'Snorkel Zombie'], "special": None},  
    "3-5": {"flags": 2, "zombies": ['Zombie', 'Flag Zombie', 'Conehead Zombie', 'Football Zombie', 'Ducky Tube Zombie', 'Snorkel Zombie'], "special": 'mini-game'},  
    "3-6": {"flags": 2, "zombies": ['Zombie', 'Flag Zombie', 'Conehead Zombie', 'Ducky Tube Zombie', 'Zomboni', 'Zombie Bobsled Team'], "special": None},  
    "3-7": {"flags": 3, "zombies": ['Zombie', 'Flag Zombie', 'Conehead Zombie', 'Buckethead Zombie', 'Ducky Tube Zombie', 'Snorkel Zombie', 'Zomboni', 'Zombie Bobsled Team'], "special": None},  
    "3-8": {"flags": 2, "zombies": ['Zombie', 'Flag Zombie', 'Conehead Zombie', 'Ducky Tube Zombie', 'Dolphin Rider Zombie'], "special": None},  
    "3-9": {"flags": 3, "zombies": ['Zombie', 'Flag Zombie', 'Conehead Zombie', 'Pole Vaulting Zombie', 'Buckethead Zombie', 'Ducky Tube Zombie', 'Zomboni', 'Dolphin Rider Zombie', 'Zombie Bobsled Team'], "special": None},  
    "3-10": {"flags": 3, "zombies": ['Zombie', 'Flag Zombie', 'Conehead Zombie', 'Buckethead Zombie', 'Ducky Tube Zombie', 'Snorkel Zombie', 'Zomboni', 'Dolphin Rider Zombie', 'Zombie Bobsled Team'], "special": 'conveyor'},  
    "4-1": {"flags": 1, "zombies": ['Zombie', 'Flag Zombie', 'Conehead Zombie', 'Ducky Tube Zombie', 'Jack-in-the-Box Zombie'], "special": None, "fog": True},  
    "4-2": {"flags": 2, "zombies": ['Zombie', 'Flag Zombie', 'Conehead Zombie', 'Football Zombie', 'Ducky Tube Zombie', 'Jack-in-the-Box Zombie'], "special": None, "fog": True},  
    "4-3": {"flags": 1, "zombies": ['Zombie', 'Flag Zombie', 'Conehead Zombie', 'Ducky Tube Zombie', 'Balloon Zombie'], "special": None, "fog": True},  
    "4-4": {"flags": 2, "zombies": ['Zombie', 'Flag Zombie', 'Conehead Zombie', 'Ducky Tube Zombie', 'Dolphin Rider Zombie', 'Balloon Zombie'], "special": None, "fog": True},  
    "4-5": {"flags": 0, "zombies": [], "special": 'vasebreaker', "fog": True},  
    "4-6": {"flags": 1, "zombies": ['Zombie', 'Flag Zombie', 'Conehead Zombie', 'Ducky Tube Zombie', 'Digger Zombie'], "special": None, "fog": True},  
    "4-7": {"flags": 2, "zombies": ['Zombie', 'Flag Zombie', 'Conehead Zombie', 'Buckethead Zombie', 'Ducky Tube Zombie', 'Jack-in-the-Box Zombie', 'Digger Zombie'], "special": None, "fog": True},  
    "4-8": {"flags": 1, "zombies": ['Zombie', 'Flag Zombie', 'Conehead Zombie', 'Ducky Tube Zombie', 'Pogo Zombie'], "special": None, "fog": True},  
    "4-9": {"flags": 2, "zombies": ['Zombie', 'Flag Zombie', 'Conehead Zombie', 'Buckethead Zombie', 'Ducky Tube Zombie', 'Balloon Zombie', 'Pogo Zombie'], "special": None, "fog": True},  
    "4-10": {"flags": 2, "zombies": ['Zombie', 'Flag Zombie', 'Conehead Zombie', 'Buckethead Zombie', 'Ducky Tube Zombie', 'Jack-in-the-Box Zombie', 'Balloon Zombie', 'Digger Zombie', 'Pogo Zombie'], "special": 'conveyor', "fog": True},  
    "5-1": {"flags": 1, "zombies": ['Zombie', 'Conehead Zombie', 'Bungee Zombie', 'Flag Zombie'], "special": None, "roof": True},  
    "5-2": {"flags": 2, "zombies": ['Zombie', 'Conehead Zombie', 'Pole Vaulting Zombie', 'Buckethead Zombie', 'Bungee Zombie', 'Flag Zombie'], "special": None, "roof": True},  
    "5-3": {"flags": 2, "zombies": ['Zombie', 'Conehead Zombie', 'Bungee Zombie', 'Ladder Zombie', 'Flag Zombie'], "special": None, "roof": True},  
    "5-4": {"flags": 3, "zombies": ['Zombie', 'Conehead Zombie', 'Football Zombie', 'Pogo Zombie', 'Bungee Zombie', 'Ladder Zombie', 'Flag Zombie'], "special": None, "roof": True},  
    "5-5": {"flags": 2, "zombies": ['Zombie', 'Conehead Zombie', 'Buckethead Zombie', 'Bungee Zombie', 'Ladder Zombie', 'Flag Zombie'], "special": 'mini-game', "roof": True},  
    "5-6": {"flags": 2, "zombies": ['Zombie', 'Conehead Zombie', 'Bungee Zombie', 'Catapult Zombie', 'Flag Zombie'], "special": None, "roof": True},  
    "5-7": {"flags": 3, "zombies": ['Zombie', 'Conehead Zombie', 'Bungee Zombie', 'Ladder Zombie', 'Catapult Zombie', 'Flag Zombie'], "special": None, "roof": True},  
    "5-8": {"flags": 2, "zombies": ['Zombie', 'Conehead Zombie', 'Bungee Zombie', 'Gargantuar', 'Imp', 'Flag Zombie'], "special": None, "roof": True},  
    "5-9": {"flags": 3, "zombies": ['Zombie', 'Conehead Zombie', 'Buckethead Zombie', 'Jack-in-the-Box Zombie', 'Bungee Zombie', 'Ladder Zombie', 'Catapult Zombie', 'Gargantuar', 'Imp', 'Flag Zombie'], "special": None, "roof": True},  
    "5-10": {"flags": 3, "zombies": ['Zombie', 'Conehead Zombie', 'Buckethead Zombie', 'Screen Door Zombie', 'Football Zombie', 'Dancing Zombie', 'Backup Dancer', 'Ducky Tube Zombie', 'Snorkel Zombie', 'Zomboni', 'Zombie Bobsled Team', 'Dolphin Rider Zombie', 'Jack-in-the-Box Zombie', 'Balloon Zombie', 'Digger Zombie', 'Pogo Zombie', 'Ladder Zombie', 'Catapult Zombie', 'Gargantuar', 'Imp', 'Dr. Zomboss', 'Flag Zombie'], "special": 'boss', "roof": True},  
}  

unlock_after = {  
    "1-1": 'Sunflower',  
    "1-2": 'Cherry Bomb',  
    "1-3": 'Wall-nut',  
    "1-5": 'Potato Mine',  
    "1-6": 'Snow Pea',  
    "1-7": 'Chomper',  
    "1-8": 'Repeater',  
    "1-10": 'Puff-Shroom',  
    "2-1": 'Sun-Shroom',  
    "2-2": 'Fume-Shroom',  
    "2-3": 'Grave Buster',  
    "2-5": 'Hypno-Shroom',  
    "2-6": 'Scaredy-Shroom',  
    "2-7": 'Ice-Shroom',  
    "2-8": 'Doom-Shroom',  
    "2-10": 'Lily Pad',  
    "3-1": 'Squash',  
    "3-2": 'Threepeater',  
    "3-3": 'Tangle Kelp',  
    "3-5": 'Jalapeno',  
    "3-6": 'Spikeweed',  
    "3-7": 'Torchwood',  
    "3-8": 'Tall-Nut',  
    "3-10": 'Sea-Shroom',  
    "4-1": 'Plantern',  
    "4-2": 'Cactus',  
    "4-3": 'Blover',  
    "4-5": 'Split Pea',  
    "4-6": 'Starfruit',  
    "4-7": 'Pumpkin',  
    "4-8": 'Magnet-Shroom',  
    "4-10": 'Cabbage-Pult',  
    "5-1": 'Flower Pot',  
    "5-2": 'Kernel-Pult',  
    "5-3": 'Coffee Bean',  
    "5-5": 'Garlic',  
    "5-6": 'Umbrella Leaf',  
    "5-7": 'Marigold',  
    "5-8": 'Melon-Pult',  
}  

# === GAME CLASSES ===  
class Plant:  
    def __init__(self, col, row, plant_type):  
        self.col = col  
        self.row = row  
        self.type = plant_type  
        self.health = 100  # Example  
        # Add type-specific behavior, e.g., shoot timer for Peashooter  

    def update(self):  
        # Implement logic: shoot, produce sun, etc.  
        pass  

    def draw(self):  
        # Draw plant based on type  
        pass  

class Zombie:  
    def __init__(self, row, zombie_type):  
        self.row = row  
        self.type = zombie_type  
        self.x = WIDTH  
        self.health = 100  # Example, vary by type  
        self.speed = 1  # Example  

    def update(self):  
        self.x -= self.speed  
        # Eat plants if colliding  
        pass  

    def draw(self):  
        # Draw zombie based on type  
        pygame.draw.circle(screen, ZOMBIE_SKIN, (int(self.x), GRID_Y + self.row * CELL_H + CELL_H // 2), 20)  

class Projectile:  
    def __init__(self, x, y):  
        self.x = x  
        self.y = y  
        self.speed = 5  

    def update(self):  
        self.x += self.speed  
        # Check collision with zombies  
        pass  

    def draw(self):  
        pygame.draw.circle(screen, GREEN, (int(self.x), int(self.y)), 5)  

# === MENU SYSTEM ===  
class MenuButton:  
    def __init__(self,x,y,w,h,text,color=GREEN,hover_color=YELLOW,action=None):  
        self.rect=pygame.Rect(x,y,w,h)  
        self.text=text;self.color=color;self.hover_color=hover_color  
        self.action=action;self.font=pygame.font.SysFont('Arial',24,True)  
    def draw(self,screen,hovered=False):  
        color=self.hover_color if hovered else self.color  
        shadow=pygame.Surface((self.rect.w+4,self.rect.h+4),pygame.SRCALPHA)  
        pygame.draw.rect(shadow,SHADOW,(2,2,self.rect.w,self.rect.h))  
        screen.blit(shadow,(self.rect.x-2,self.rect.y-2))  
        pygame.draw.rect(screen,color,self.rect)  
        pygame.draw.rect(screen,WHITE,self.rect,3)  
        t=self.font.render(self.text,True,BLACK)  
        screen.blit(t,t.get_rect(center=self.rect.center))  
    def handle_click(self):  
        if self.action:self.action()  

font_title=pygame.font.SysFont('Arial',36,True)  
font_small=pygame.font.SysFont('Arial',18)  
font_dave=pygame.font.SysFont('Arial',20,italic=True)  

def start_standard():  
    global menu_active, tutorial_active, cloudy_mode, current_area  
    menu_active=False; tutorial_active=True; cloudy_mode=False  
    current_area = 1  

def start_cloudy():  
    global menu_active, tutorial_active, cloudy_mode, current_area  
    menu_active=False; tutorial_active=True; cloudy_mode=True  
    current_area = 4  # Start in Fog for cloudy mode  

def quit_game():  
    pygame.quit(); sys.exit()  

buttons=[  
    MenuButton(WIDTH//2-100,HEIGHT//2-60,200,40,"STANDARD MODE",action=start_standard),  
    MenuButton(WIDTH//2-100,HEIGHT//2-10,200,40,"CLOUDY DAY MODE",action=start_cloudy),  
    MenuButton(WIDTH//2-80,HEIGHT//2+40,160,40,"QUIT",RED,action=quit_game)  
]  

# === VISUAL OBJECTS ===  
class MenuSun:  
    def __init__(s):  
        s.x=random.randint(0,WIDTH);s.y=random.randint(0,HEIGHT//2)  
        s.vy=random.uniform(0.5,1.5);s.a=0;s.r=random.randint(8,12)  
        s.pulse=0;s.noise=0  
    def update(s):  
        s.y+=s.vy;s.a+=2;s.pulse+=0.1;s.noise+=0.01  
        if s.y>HEIGHT:s.y=-s.r;s.x=random.randint(0,WIDTH)  
    def draw(s):  
        pulse_r=s.r+math.sin(s.pulse)*2  
        glow=pygame.Surface((s.r*5,s.r*5),pygame.SRCALPHA)  
        for layer in range(3):  
            offx=random.uniform(-0.5,0.5) if layer==2 else 0  
            offy=random.uniform(-0.5,0.5) if layer==2 else 0  
            for rr in range(int(pulse_r*2),0,-2):  
                raw_alpha=40*(rr/(pulse_r*2))+math.sin(s.pulse+layer)*10  
                alpha=max(0,min(255,int(raw_alpha)))  
                pygame.draw.circle(glow,(255,255,0,alpha),  
                    (int(s.r*2.5+offx),int(s.r*2.5+offy)),rr)  
        screen.blit(glow,(s.x-s.r*2.5,s.y-s.r*2.5))  
        pygame.draw.circle(screen,YELLOW,(int(s.x),int(s.y)),s.r)  
        for _ in range(12):  
            ang=s.noise+random.uniform(0,2*math.pi)  
            ox=s.x+math.cos(ang)*s.r; oy=s.y+math.sin(ang)*s.r  
            pygame.draw.circle(screen,WHITE,(int(ox),int(oy)),1)  
        for i in range(16):  
            ang=s.a+i*math.pi/8  
            mx=s.x+math.cos(ang)*(s.r*0.5)  
            my=s.y+math.sin(ang)*(s.r*0.5)  
            ex=s.x+math.cos(ang)*(s.r*2)  
            ey=s.y+math.sin(ang)*(s.r*2)  
            pygame.draw.line(screen,YELLOW,(s.x,s.y),(mx,my),3)  
            pygame.draw.line(screen,YELLOW,(mx,my),(ex,ey),2)  

class MenuGrass:  
    def __init__(s,x):  
        s.x=x; s.y=HEIGHT; s.amp=random.uniform(3,8)  
        s.wave=0; s.twist=0  
    def update(s,t):  
        s.ang=math.sin(t*0.01+s.x*0.01)*s.amp  
        s.wave+=0.05; s.twist+=0.02  
    def draw(s):  
        ex=s.x+s.ang; ey=s.y-random.randint(40,60)  
        twist=math.sin(s.twist)*2  
        pts=[(s.x,s.y),(ex+twist,ey-10),(ex-twist,ey)]  
        pygame.draw.polygon(screen,DARK_GREEN,pts)  
        pygame.draw.lines(screen,GRASS,False,pts,2)  

# === INITIALIZE MENU ELEMENTS ===  
menu_suns=[MenuSun() for _ in range(12)]  
menu_grass=[MenuGrass(x) for x in range(0,WIDTH,10)]  
menu_active=True  
tutorial_active=False  
game_active = False  
cloudy_mode=False  
time_elapsed=0  

# === GAME STATE ===  
unlocked_plants = ['Peashooter']  
current_area = 1  
current_level = 1  
current = "1-1"  
config = level_data[current]  
current_seed_packets = unlocked_plants.copy()  
plants = []  
zombies = []  
projectiles = []  
sun_amount = 50  
selected_plant = None  
spawn_timer = 200  
wave_current = 0  
waves_total = config.get("flags", 0) + 1  # Example  

def load_level():  
    global current, config, current_seed_packets, waves_total, wave_current, spawn_timer, plants, zombies, projectiles  
    current = f"{current_area}-{current_level}"  
    config = level_data.get(current, {"flags": 0, "zombies": ['Zombie'], "special": None})  
    if config.get('special') == 'conveyor' or config.get('special') == 'mini-game':  
        # Set specific packets for special levels  
        current_seed_packets = unlocked_plants.copy()  # Stub: customize per level  
    else:  
        current_seed_packets = unlocked_plants.copy()  
    plants = []  
    zombies = []  
    projectiles = []  
    wave_current = 0  
    waves_total = config.get("flags", 0) + 1  
    spawn_timer = 200  

# === MAIN LOOP ===  
while True:  
    clock.tick(FPS)  
    for e in pygame.event.get():  
        if e.type==pygame.QUIT: quit_game()  
        elif e.type==pygame.MOUSEBUTTONDOWN:  
            if menu_active:  
                for b in buttons:  
                    if b.rect.collidepoint(e.pos): b.handle_click()  
            elif game_active:  
                # Handle planting  
                if selected_plant:  
                    mx, my = e.pos  
                    col = (mx - GRID_X) // CELL_W  
                    row = (my - GRID_Y) // CELL_H  
                    if 0 <= col < COLS and 0 <= row < ROWS:  
                        # Check if empty and valid (e.g., Lily Pad for pool)  
                        plants.append(Plant(col, row, selected_plant))  
                        selected_plant = None  
        elif e.type == pygame.KEYDOWN:  
            if tutorial_active and e.key == pygame.K_SPACE:  
                tutorial_active = False  
                game_active = True  
                load_level()  

    screen.fill(SKY)  
    time_elapsed += 1  

    # Background animation  
    for g in menu_grass:  
        g.update(time_elapsed)  
        g.draw()  
    for s in menu_suns:  
        s.update()  
        s.draw()  

    if menu_active:  
        title=font_title.render("Plants vs Zombies - Replanted",True,WHITE)  
        screen.blit(title,title.get_rect(center=(WIDTH//2,70)))  
        mpos=pygame.mouse.get_pos()  
        for b in buttons:  
            b.draw(screen,b.rect.collidepoint(mpos))  
        dave=font_dave.render("Crazy Dave: 'Roll over, Catsan! Heh heh!'",True,WHITE)  
        screen.blit(dave,(20,HEIGHT-40))  
    elif tutorial_active:  
        # Simple tutorial screen  
        title = font_title.render("Tutorial: Plant to defend!", True, WHITE)  
        screen.blit(title, title.get_rect(center=(WIDTH//2, HEIGHT//2)))  
        # Add more tutorial text if needed  
    elif game_active:  
        # Draw grid  
        for row in range(ROWS):  
            for col in range(COLS):  
                pygame.draw.rect(screen, GRASS if row % 2 == col % 2 else DARK_GREEN, (GRID_X + col * CELL_W, GRID_Y + row * CELL_H, CELL_W, CELL_H))  
        # Update and draw game objects  
        for p in plants:  
            p.update()  
            p.draw()  
        for z in zombies:  
            z.update()  
            z.draw()  
        for proj in projectiles:  
            proj.update()  
            proj.draw()  
        # Spawn zombies  
        spawn_timer -= 1  
        if spawn_timer <= 0:  
            # Spawn a zombie from config['zombies'] in random row  
            row = random.randint(0, ROWS-1)  
            z_type = random.choice(config['zombies'])  
            zombies.append(Zombie(row, z_type))  
            spawn_timer = random.randint(100, 300)  # Example  
        # Other game logic: win/lose conditions, sun production, etc.  

    pygame.display.flip()  
