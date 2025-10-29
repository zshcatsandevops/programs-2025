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
NIGHT_SKY = (0, 0, 50)
WATER = (0, 100, 200)

UPSAMPLE_SCALE=2
UPSAMPLE_W,UPSAMPLE_H=WIDTH*UPSAMPLE_SCALE,HEIGHT*UPSAMPLE_SCALE

# === PLANT STATS ===
plant_stats = {
    'Peashooter': {'cost':100, 'cooldown':7.5, 'health':300},
    'Sunflower': {'cost':50, 'cooldown':7.5, 'health':300},
    'Cherry Bomb': {'cost':150, 'cooldown':50, 'health':300},
    'Wall-nut': {'cost':50, 'cooldown':30, 'health':4000},
    'Potato Mine': {'cost':25, 'cooldown':15, 'health':300},
    'Snow Pea': {'cost':175, 'cooldown':7.5, 'health':300},
    'Chomper': {'cost':150, 'cooldown':7.5, 'health':300},
    'Repeater': {'cost':200, 'cooldown':7.5, 'health':300},
    'Puff-Shroom': {'cost':0, 'cooldown':7.5, 'health':300},
    'Sun-Shroom': {'cost':25, 'cooldown':7.5, 'health':300},
    'Fume-Shroom': {'cost':75, 'cooldown':7.5, 'health':300},
    'Grave Buster': {'cost':75, 'cooldown':7.5, 'health':300},
    'Hypno-Shroom': {'cost':75, 'cooldown':30, 'health':300},
    'Scaredy-Shroom': {'cost':25, 'cooldown':7.5, 'health':300},
    'Ice-Shroom': {'cost':75, 'cooldown':50, 'health':300},
    'Doom-Shroom': {'cost':125, 'cooldown':50, 'health':300},
    'Lily Pad': {'cost':25, 'cooldown':7.5, 'health':300},
    'Squash': {'cost':50, 'cooldown':30, 'health':300},
    'Threepeater': {'cost':325, 'cooldown':7.5, 'health':300},
    'Tangle Kelp': {'cost':25, 'cooldown':30, 'health':300},
    'Jalapeno': {'cost':125, 'cooldown':50, 'health':300},
    'Spikeweed': {'cost':100, 'cooldown':7.5, 'health':300},
    'Torchwood': {'cost':175, 'cooldown':7.5, 'health':300},
    'Tall-Nut': {'cost':125, 'cooldown':30, 'health':8000},
    'Sea-Shroom': {'cost':0, 'cooldown':7.5, 'health':300},
    'Plantern': {'cost':25, 'cooldown':7.5, 'health':300},
    'Cactus': {'cost':125, 'cooldown':7.5, 'health':300},
    'Blover': {'cost':100, 'cooldown':7.5, 'health':300},
    'Split Pea': {'cost':125, 'cooldown':7.5, 'health':300},
    'Starfruit': {'cost':125, 'cooldown':7.5, 'health':300},
    'Pumpkin': {'cost':125, 'cooldown':30, 'health':4000},
    'Magnet-Shroom': {'cost':100, 'cooldown':15, 'health':300},
    'Cabbage-Pult': {'cost':100, 'cooldown':7.5, 'health':300},
    'Flower Pot': {'cost':25, 'cooldown':7.5, 'health':300},
    'Kernel-Pult': {'cost':100, 'cooldown':7.5, 'health':300},
    'Coffee Bean': {'cost':75, 'cooldown':7.5, 'health':300},
    'Garlic': {'cost':50, 'cooldown':7.5, 'health':300},
    'Umbrella Leaf': {'cost':100, 'cooldown':7.5, 'health':300},
    'Marigold': {'cost':50, 'cooldown':7.5, 'health':300},
    'Melon-Pult': {'cost':300, 'cooldown':7.5, 'health':300},
}

# === ZOMBIE STATS ===
zombie_stats = {
    'Zombie': {'health': 200, 'speed': 0.5},
    'Flag Zombie': {'health': 200, 'speed': 0.5},
    'Conehead Zombie': {'health': 560, 'speed': 0.5},
    'Pole Vaulting Zombie': {'health': 340, 'speed': 1.0},
    'Buckethead Zombie': {'health': 1300, 'speed': 0.5},
    'Newspaper Zombie': {'health': 340, 'speed': 0.5},
    'Screen Door Zombie': {'health': 1300, 'speed': 0.5},
    'Football Zombie': {'health': 1700, 'speed': 1.0},
    'Dancing Zombie': {'health': 340, 'speed': 0.5},
    'Backup Dancer': {'health': 200, 'speed': 0.5},
    'Ducky Tube Zombie': {'health': 200, 'speed': 0.5},
    'Snorkel Zombie': {'health': 340, 'speed': 0.5},
    'Zomboni': {'health': 1300, 'speed': 0.5},
    'Zombie Bobsled Team': {'health': 200, 'speed': 1.0},
    'Dolphin Rider Zombie': {'health': 340, 'speed': 1.0},
    'Jack-in-the-Box Zombie': {'health': 340, 'speed': 1.0},
    'Balloon Zombie': {'health': 200, 'speed': 0.5},
    'Digger Zombie': {'health': 340, 'speed': 0.5},
    'Pogo Zombie': {'health': 340, 'speed': 1.0},
    'Bungee Zombie': {'health': 300, 'speed': 0},
    'Ladder Zombie': {'health': 560, 'speed': 0.5},
    'Catapult Zombie': {'health': 1000, 'speed': 0.5},
    'Gargantuar': {'health': 3000, 'speed': 0.5},
    'Imp': {'health': 200, 'speed': 1.5},
    'Dr. Zomboss': {'health': 10000, 'speed': 0},
}

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
        self.health = plant_stats.get(plant_type, {'health': 300})['health']
        if self.type in ['Peashooter', 'Snow Pea', 'Repeater', 'Threepeater', 'Split Pea', 'Cactus', 'Cabbage-Pult', 'Kernel-Pult', 'Melon-Pult', 'Fume-Shroom', 'Puff-Shroom', 'Scaredy-Shroom', 'Sea-Shroom']:
            self.shoot_timer = 0
        if self.type in ['Sunflower', 'Sun-Shroom', 'Marigold']:
            self.sun_timer = 0

    def update(self):
        center_x = GRID_X + self.col * CELL_W + CELL_W // 2
        center_y = GRID_Y + self.row * CELL_H + CELL_H // 2
        if hasattr(self, 'shoot_timer'):
            self.shoot_timer -= 1
            if self.shoot_timer <= 0:
                for z in zombies:
                    if z.row == self.row:
                        projectiles.append(Projectile(center_x + 20, center_y, self.row))
                        self.shoot_timer = 90
                        break
        if hasattr(self, 'sun_timer'):
            self.sun_timer -= 1
            if self.sun_timer <= 0:
                suns.append(Sun(center_x, center_y))
                self.sun_timer = 1440

    def draw(self):
        center_x = GRID_X + self.col * CELL_W + CELL_W // 2
        center_y = GRID_Y + self.row * CELL_H + CELL_H // 2
        pygame.draw.circle(screen, GREEN, (center_x, center_y), 20)
        # TODO: Type-specific draws

class Zombie:
    def __init__(self, row, zombie_type):
        self.row = row
        self.type = zombie_type
        self.x = WIDTH
        stats = zombie_stats.get(zombie_type, {'health': 200, 'speed': 0.5})
        self.health = stats['health']
        self.speed = stats['speed']
        self.eat_timer = 0

    def update(self):
        colliding_plant = None
        for p in plants:
            p_x = GRID_X + p.col * CELL_W + CELL_W // 2
            if p.row == self.row and abs(self.x - p_x) < 25:
                colliding_plant = p
                break
        if colliding_plant:
            self.eat_timer -= 1
            if self.eat_timer <= 0:
                colliding_plant.health -= 10
                self.eat_timer = 60
                if colliding_plant.health <= 0:
                    plants.remove(colliding_plant)
        else:
            self.x -= self.speed
        if self.x < 0:
            global game_active, menu_active
            game_active = False
            menu_active = True

    def draw(self):
        y = GRID_Y + self.row * CELL_H + CELL_H // 2
        pygame.draw.circle(screen, ZOMBIE_SKIN, (int(self.x), y), 20)
        if 'Conehead' in self.type:
            pygame.draw.polygon(screen, BROWN, [[int(self.x)-15, y-25], [int(self.x), y-40], [int(self.x)+15, y-25]])
        if 'Buckethead' in self.type:
            pygame.draw.rect(screen, GRAY, (int(self.x)-15, y-30, 30, 10))
        if 'Flag' in self.type:
            pygame.draw.line(screen, BLACK, (int(self.x)+20, y-30), (int(self.x)+20, y-50))
            pygame.draw.rect(screen, RED, (int(self.x)+20, y-50, 20, 10))
        # TODO: Draws for other types

class Projectile:
    def __init__(self, x, y, row):
        self.x = x
        self.y = y
        self.row = row
        self.speed = 5

    def update(self):
        self.x += self.speed
        if self.x > WIDTH:
            if self in projectiles:
                projectiles.remove(self)
            return
        for z in zombies[:]:
            if z.row == self.row and abs(z.x - self.x) < 20:
                z.health -= 20
                if z.health <= 0:
                    zombies.remove(z)
                projectiles.remove(self)
                break

    def draw(self):
        pygame.draw.circle(screen, GREEN, (int(self.x), int(self.y)), 5)

class Sun:
    def __init__(self, x, y, from_sky=False):
        self.x = x
        self.y = y
        self.from_sky = from_sky
        self.vy = 1 if from_sky else 0
        self.timer = 600 if from_sky else 0
        self.grounded = False

    def update(self):
        if self.from_sky and not self.grounded:
            self.y += self.vy
            if self.y >= GRID_Y + random.randint(0, ROWS * CELL_H):
                self.grounded = True
                self.vy = 0
        elif not self.from_sky:
            self.y += self.vy
            if self.vy < 1:
                self.vy += 0.1  # gravity for plant sun
        if self.timer > 0:
            self.timer -= 1
        if self.timer <= 0 and self.from_sky:
            if self in suns:
                suns.remove(self)

    def draw(self):
        pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), 10)

class SeedPacket:
    def __init__(self, plant_type, index):
        self.type = plant_type
        self.rect = pygame.Rect(GRID_X + index * 55, 10, 50, 70)
        self.cooldown = 0

    def draw(self):
        color = GRAY if self.cooldown > 0 else GREEN
        pygame.draw.rect(screen, color, self.rect)
        t = font_small.render(self.type[:10], True, BLACK)
        screen.blit(t, (self.rect.x + 5, self.rect.centery - 10))

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
    global menu_active, tutorial_active, cloudy_mode, current_area, current_level
    menu_active=False; tutorial_active=True; cloudy_mode=False
    current_area = 1
    current_level = 1

def start_cloudy():
    global menu_active, tutorial_active, cloudy_mode, current_area, current_level
    menu_active=False; tutorial_active=True; cloudy_mode=True
    current_area = 4
    current_level = 1

def quit_game():
    pygame.quit(); sys.exit()

buttons=[
    MenuButton(WIDTH//2-100,HEIGHT//2-60,200,40,"STANDARD MODE",action=start_standard),
    MenuButton(WIDTH//2-100,HEIGHT//2-10,200,40,"CLOUDY DAY MODE",action=start_cloudy),
    MenuButton(WIDTH//2-80,HEIGHT//2+40,160,40,"QUIT",RED,action=quit_game)
]

# === VISUAL OBJECTS ===
class MenuSun:
    def __init__(self):
        self.x=random.randint(0,WIDTH);self.y=random.randint(0,HEIGHT//2)
        self.vy=random.uniform(0.5,1.5);self.a=0;self.r=random.randint(8,12)
        self.pulse=0;self.noise=0
    def update(self):
        self.y+=self.vy;self.a+=2;self.pulse+=0.1;self.noise+=0.01
        if self.y>HEIGHT:self.y=-self.r;self.x=random.randint(0,WIDTH)
    def draw(self):
        pulse_r=self.r+math.sin(self.pulse)*2
        glow=pygame.Surface((self.r*5,self.r*5),pygame.SRCALPHA)
        for layer in range(3):
            offx=random.uniform(-0.5,0.5) if layer==2 else 0
            offy=random.uniform(-0.5,0.5) if layer==2 else 0
            for rr in range(int(pulse_r*2),0,-2):
                raw_alpha=40*(rr/(pulse_r*2))+math.sin(self.pulse+layer)*10
                alpha=max(0,min(255,int(raw_alpha)))
                pygame.draw.circle(glow,(255,255,0,alpha),
                    (int(self.r*2.5+offx),int(self.r*2.5+offy)),rr)
        screen.blit(glow,(self.x-self.r*2.5,self.y-self.r*2.5))
        pygame.draw.circle(screen,YELLOW,(int(self.x),int(self.y)),self.r)
        for _ in range(12):
            ang=self.noise+random.uniform(0,2*math.pi)
            ox=self.x+math.cos(ang)*self.r; oy=self.y+math.sin(ang)*self.r
            pygame.draw.circle(screen,WHITE,(int(ox),int(oy)),1)
        for i in range(16):
            ang=self.a+i*math.pi/8
            mx=self.x+math.cos(ang)*(self.r*0.5)
            my=self.y+math.sin(ang)*(self.r*0.5)
            ex=self.x+math.cos(ang)*(self.r*2)
            ey=self.y+math.sin(ang)*(self.r*2)
            pygame.draw.line(screen,YELLOW,(self.x,self.y),(mx,my),3)
            pygame.draw.line(screen,YELLOW,(mx,my),(ex,ey),2)

class MenuGrass:
    def __init__(self,x):
        self.x=x; self.y=HEIGHT; self.amp=random.uniform(3,8)
        self.wave=0; self.twist=0
    def update(self,t):
        self.ang=math.sin(t*0.01+self.x*0.01)*self.amp
        self.wave+=0.05; self.twist+=0.02
    def draw(self):
        ex=self.x+self.ang; ey=self.y-random.randint(40,60)
        twist=math.sin(self.twist)*2
        pts=[(self.x,self.y),(ex+twist,ey-10),(ex-twist,ey)]
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
suns = []
seed_packets = []
sun_amount = 50
selected_plant = None
spawn_timer = 200
wave_current = 0
waves_total = 1
in_wave = False
wave_timer = 100
zombies_to_spawn = 0
sky_sun_timer = 300

def load_level():
    global current, config, current_seed_packets, waves_total, wave_current, spawn_timer, plants, zombies, projectiles, suns, seed_packets, sun_amount, in_wave, wave_timer, zombies_to_spawn, sky_sun_timer
    current = f"{current_area}-{current_level}"
    config = level_data.get(current, {"flags": 0, "zombies": ['Zombie'], "special": None})
    if config.get('special') in ['conveyor', 'mini-game']:
        current_seed_packets = unlocked_plants.copy()  # Customize for specials if needed
    else:
        current_seed_packets = unlocked_plants.copy()
    seed_packets = [SeedPacket(p, i) for i, p in enumerate(current_seed_packets)]
    plants = []
    zombies = []
    projectiles = []
    suns = []
    sun_amount = 50
    wave_current = 0
    waves_total = config.get("flags", 0) + 1
    in_wave = False
    wave_timer = 100
    zombies_to_spawn = 0
    spawn_timer = 200
    sky_sun_timer = random.randint(300, 600)

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
                mx, my = e.pos
                for sp in seed_packets:
                    if sp.rect.collidepoint(e.pos) and sp.cooldown <= 0 and sun_amount >= plant_stats.get(sp.type, {'cost': 0})['cost']:
                        selected_plant = sp.type
                for s in suns[:]:
                    if pygame.Rect(s.x - 10, s.y - 10, 20, 20).collidepoint(e.pos):
                        sun_amount += 25
                        suns.remove(s)
                if selected_plant:
                    col = (mx - GRID_X) // CELL_W
                    row = (my - GRID_Y) // CELL_H
                    if 0 <= col < COLS and 0 <= row < ROWS and not any(p.col == col and p.row == row for p in plants):
                        sun_amount -= plant_stats[selected_plant]['cost']
                        plants.append(Plant(col, row, selected_plant))
                        for sp in seed_packets:
                            if sp.type == selected_plant:
                                sp.cooldown = int(plant_stats[selected_plant]['cooldown'] * FPS)
                        selected_plant = None
                    else:
                        selected_plant = None
        elif e.type == pygame.KEYDOWN:
            if tutorial_active and e.key == pygame.K_SPACE:
                tutorial_active = False
                game_active = True
                load_level()

    time_elapsed += 1

    # Background animation (menu only)
    if menu_active:
        screen.fill(SKY)
        for g in menu_grass:
            g.update(time_elapsed)
            g.draw()
        for s in menu_suns:
            s.update()
            s.draw()
    elif game_active:
        is_night = current_area in (2, 4)
        is_pool = current_area in (3, 4)
        is_roof = current_area == 5
        # is_fog = config.get("fog", False)  # TODO: Implement fog overlay
        screen.fill(NIGHT_SKY if is_night else SKY)
        # Draw grid
        for row in range(ROWS):
            for col in range(COLS):
                color = GRASS if row % 2 == col % 2 else DARK_GREEN
                if is_pool and row in (2, 3):
                    color = WATER
                if is_roof:
                    color = GRAY
                pygame.draw.rect(screen, color, (GRID_X + col * CELL_W, GRID_Y + row * CELL_H, CELL_W, CELL_H))
        # Update and draw game objects
        if config.get('special') not in ['conveyor', 'mini-game', 'vasebreaker', 'boss', 'wallnut_bowling']:  # Normal logic
            sky_sun_timer -= 1
            if sky_sun_timer <= 0:
                suns.append(Sun(random.randint(GRID_X, GRID_X + COLS * CELL_W), -10, True))
                sky_sun_timer = random.randint(300, 600)
            if not in_wave:
                wave_timer -= 1
                if wave_timer <= 0:
                    wave_current += 1
                    in_wave = True
                    zombies_to_spawn = 5 + (wave_current - 1) * 5 + current_level * 2
                    spawn_timer = 30
            else:
                spawn_timer -= 1
                if spawn_timer <= 0 and zombies_to_spawn > 0:
                    row = random.randint(0, ROWS - 1)
                    z_type = random.choice(config['zombies'])
                    zombies.append(Zombie(row, z_type))
                    zombies_to_spawn -= 1
                    spawn_timer = random.randint(50, 150)
            if zombies_to_spawn == 0 and len(zombies) == 0 and in_wave:
                in_wave = False
                wave_timer = 500
                if wave_current == waves_total:
                    # Win level
                    if current in unlock_after:
                        if unlock_after[current] not in unlocked_plants:
                            unlocked_plants.append(unlock_after[current])
                    current_level += 1
                    if current_level > 10:
                        current_area += 1
                        current_level = 1
                        if current_area > 5:
                            menu_active = True
                            game_active = False
                    else:
                        load_level()
        # Update objects
        for p in plants:
            p.update()
        for z in zombies:
            z.update()
        for proj in projectiles[:]:
            proj.update()
        for s in suns:
            s.update()
        # Draw objects
        for p in plants:
            p.draw()
        for z in zombies:
            z.draw()
        for proj in projectiles:
            proj.draw()
        for s in suns:
            s.draw()
        for sp in seed_packets:
            sp.draw()
            sp.cooldown -= 1
            if sp.cooldown > 0:
                dark = pygame.Surface((sp.rect.w, sp.rect.h), pygame.SRCALPHA)
                dark.fill((0, 0, 0, 128))
                screen.blit(dark, sp.rect.topleft)
        # Draw sun amount
        t = font_small.render(f"Sun: {sun_amount}", True, YELLOW)
        screen.blit(t, (10, 10))
    elif tutorial_active:
        screen.fill(SKY)
        title = font_title.render("Tutorial: Plant to defend!", True, WHITE)
        screen.blit(title, title.get_rect(center=(WIDTH//2, HEIGHT//2)))

    if menu_active:
        # Draw graveyard stone
        stone_rect = pygame.Rect(WIDTH//2 - 200, 30, 400, 100)
        pygame.draw.rect(screen, GRAY, stone_rect)
        pygame.draw.rect(screen, BLACK, stone_rect, 3)
        # Add cracks for stone effect
        pygame.draw.line(screen, BLACK, (stone_rect.left + 50, stone_rect.top + 20), (stone_rect.left + 100, stone_rect.bottom - 20), 2)
        pygame.draw.line(screen, BLACK, (stone_rect.right - 50, stone_rect.top + 30), (stone_rect.right - 100, stone_rect.bottom - 10), 2)
        title = font_title.render("Plants vs Zombies - Replanted", True, BLACK)
        screen.blit(title, title.get_rect(center=stone_rect.center))
        mpos=pygame.mouse.get_pos()
        for b in buttons:
            b.draw(screen,b.rect.collidepoint(mpos))
        dave=font_dave.render("Crazy Dave: 'Roll over, Catsan! Heh heh!'",True,WHITE)
        screen.blit(dave,(20,HEIGHT-40))

    pygame.display.flip()
