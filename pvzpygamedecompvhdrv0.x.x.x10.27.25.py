import pygame
import sys
import random
import math
from pygame.locals import *

# Initialize pygame
pygame.init()
pygame.mixer.init()

# Constants - Changed to 800x600
WIDTH, HEIGHT = 800, 600
LAWN_X, LAWN_Y = 250, 100
GRID_ROWS, GRID_COLS = 5, 9
CELL_W, CELL_H = 80, 100
UI_HEIGHT = 100
HOUSE_W = 200
SPAWN_X = WIDTH - HOUSE_W

# Colors
SKY_BLUE = (113, 197, 207)
LAWN_GREEN = (120, 190, 33)
LAWN_DARK = (100, 160, 30)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
ORANGE = (255, 165, 0)
GOLD = (255, 215, 0)
DARK_GREEN = (60, 120, 30)
LIGHT_BLUE = (173, 216, 230)
BUTTON_HOVER = (200, 230, 255)
PURPLE = (128, 0, 128)
DARK_RED = (139, 0, 0)

# Game settings
FPS = 60

# Create window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ULTRA Plants vs Zombies - PyGame Edition")
clock = pygame.time.Clock()

# Fonts
FONT_SMALL = pygame.font.SysFont("Arial", 16)
FONT_MEDIUM = pygame.font.SysFont("Arial", 24)
FONT_BIG = pygame.font.SysFont("Arial", 36)
FONT_TITLE = pygame.font.SysFont("Arial", 48, bold=True)

# Load images (procedurally generated placeholders)
def load_surfaces():
    global SUN_SURF, CARD_SURFS, PLANT_SURFS, ZOMBIE_SURFS, PEA_SURF, LAWNMOWER_SURF, FIRE_PEA_SURF, ZOMBIE_KING_SURF
    # Sun
    SUN_SURF = pygame.Surface((40, 40), pygame.SRCALPHA)
    pygame.draw.circle(SUN_SURF, (255, 220, 50), (20, 20), 20)
    pygame.draw.circle(SUN_SURF, (255, 255, 150), (20, 20), 15)
    # Plant cards
    CARD_SURFS = {}
    plant_colors = {
        "peashooter": (50, 150, 50),
        "sunflower": (255, 220, 50),
        "wallnut": (150, 100, 50),
        "cherrybomb": (255, 50, 50),
        "snowpea": (150, 200, 255),
        "repeater": (100, 200, 100),
        "potatomine": (200, 150, 100),
        "chomper": (100, 50, 150),
        "gatlingpea": (50, 200, 50),
        "twinsunflower": (255, 255, 100),
        "spikeweed": (100, 100, 100),
        "jalapeno": (255, 100, 0)
    }
    for name, color in plant_colors.items():
        surf = pygame.Surface((65, 85), pygame.SRCALPHA)
        pygame.draw.rect(surf, color, (0, 0, 65, 85), border_radius=8)
        pygame.draw.rect(surf, BLACK, (0, 0, 65, 85), 2, border_radius=8)
        text = FONT_SMALL.render(name[:6], True, BLACK)
        surf.blit(text, (32 - text.get_width()//2, 42 - text.get_height()//2))
        CARD_SURFS[name] = surf
    # Plant sprites
    PLANT_SURFS = {}
    for name in plant_colors:
        surf = pygame.Surface((60, 80), pygame.SRCALPHA)
        if name == "twinsunflower":
            pygame.draw.circle(surf, (255, 255, 100), (20, 30), 15)
            pygame.draw.circle(surf, (255, 255, 100), (40, 30), 15)
        elif name == "gatlingpea":
            pygame.draw.rect(surf, plant_colors[name], (10, 10, 40, 60), border_radius=5)
            for i in range(4):
                pygame.draw.rect(surf, (50, 50, 50), (15 + i*8, 5, 4, 10))
        elif name == "spikeweed":
            pygame.draw.circle(surf, plant_colors[name], (30, 40), 20)
            for i in range(8):
                angle = i * math.pi / 4
                x1 = 30 + 15 * math.cos(angle)
                y1 = 40 + 15 * math.sin(angle)
                x2 = 30 + 25 * math.cos(angle)
                y2 = 40 + 25 * math.sin(angle)
                pygame.draw.line(surf, BLACK, (x1, y1), (x2, y2), 3)
        elif name == "jalapeno":
            pygame.draw.rect(surf, (255, 100, 0), (10, 10, 40, 60), border_radius=5)
            pygame.draw.circle(surf, (255, 200, 0), (45, 20), 8)
        else:
            pygame.draw.rect(surf, plant_colors[name], (10, 10, 40, 60), border_radius=5)
        PLANT_SURFS[name] = surf
    # Zombie sprites
    ZOMBIE_SURFS = {}
    zombie_types = ["regular", "cone", "bucket", "newspaper", "football", "dancer", "gargantuar", "king"]
    zombie_colors = {
        "regular": (150, 150, 150),
        "cone": (100, 100, 200),
        "bucket": (100, 100, 100),
        "newspaper": (200, 200, 150),
        "football": (150, 100, 50),
        "dancer": (200, 100, 200),
        "gargantuar": (100, 50, 50),
        "king": (200, 150, 50)
    }
    for ztype in zombie_types:
        surf = pygame.Surface((60, 100), pygame.SRCALPHA)
        if ztype == "gargantuar":
            surf = pygame.Surface((80, 120), pygame.SRCALPHA)
            pygame.draw.rect(surf, zombie_colors[ztype], (10, 10, 60, 100), border_radius=5)
        elif ztype == "king":
            pygame.draw.rect(surf, zombie_colors[ztype], (10, 10, 40, 80), border_radius=5)
            points = [(20, 5), (25, 15), (30, 5), (35, 15), (40, 5), (45, 15), (50, 5)]
            pygame.draw.polygon(surf, GOLD, points)
        elif ztype == "dancer":
            pygame.draw.rect(surf, zombie_colors[ztype], (10, 10, 40, 80), border_radius=5)
            pygame.draw.rect(surf, (200, 200, 200), (25, 5, 10, 10))
        else:
            pygame.draw.rect(surf, zombie_colors[ztype], (10, 10, 40, 80), border_radius=5)
        ZOMBIE_SURFS[ztype] = surf
    # Pea projectile
    PEA_SURF = pygame.Surface((20, 20), pygame.SRCALPHA)
    pygame.draw.circle(PEA_SURF, (50, 200, 50), (10, 10), 10)
    # Fire pea projectile
    FIRE_PEA_SURF = pygame.Surface((20, 20), pygame.SRCALPHA)
    pygame.draw.circle(FIRE_PEA_SURF, (255, 100, 0), (10, 10), 10)
    pygame.draw.circle(FIRE_PEA_SURF, (255, 200, 0), (10, 10), 6)
    # Lawnmower
    LAWNMOWER_SURF = pygame.Surface((60, 60), pygame.SRCALPHA)
    pygame.draw.rect(LAWNMOWER_SURF, (200, 200, 200), (0, 20, 50, 30))
    pygame.draw.rect(LAWNMOWER_SURF, (150, 150, 150), (10, 10, 30, 10))

# Plant and zombie stats
PLANT_DATA = {
    "peashooter": {"cost": 100, "recharge": 7.5, "health": 100, "damage": 20, "cooldown": 1.5},
    "sunflower": {"cost": 50, "recharge": 7.5, "health": 100, "sun_production": 25, "cooldown": 24},
    "wallnut": {"cost": 50, "recharge": 30, "health": 400},
    "cherrybomb": {"cost": 150, "recharge": 50, "health": 100, "damage": 1800, "cooldown": 3},
    "snowpea": {"cost": 175, "recharge": 7.5, "health": 100, "damage": 20, "cooldown": 1.5, "slow": 0.5},
    "repeater": {"cost": 200, "recharge": 7.5, "health": 100, "damage": 20, "cooldown": 1.5, "double": True},
    "potatomine": {"cost": 25, "recharge": 30, "health": 100, "damage": 1800, "cooldown": 15},
    "chomper": {"cost": 150, "recharge": 7.5, "health": 100, "damage": 1000, "cooldown": 42},
    "gatlingpea": {"cost": 250, "recharge": 7.5, "health": 100, "damage": 20, "cooldown": 0.5, "quad": True},
    "twinsunflower": {"cost": 125, "recharge": 7.5, "health": 100, "sun_production": 50, "cooldown": 20},
    "spikeweed": {"cost": 100, "recharge": 7.5, "health": 100, "damage": 10, "cooldown": 0.2},
    "jalapeno": {"cost": 125, "recharge": 30, "health": 100, "damage": 1800, "cooldown": 5}
}
ZOMBIE_DATA = {
    "regular": {"health": 200, "damage": 1, "speed": 0.5},
    "cone": {"health": 400, "damage": 1, "speed": 0.5},
    "bucket": {"health": 600, "damage": 1, "speed": 0.5},
    "newspaper": {"health": 200, "damage": 1, "speed": 0.7, "rage_speed": 1.5},
    "football": {"health": 800, "damage": 2, "speed": 0.8},
    "dancer": {"health": 300, "damage": 1, "speed": 0.6, "summon_rate": 5},
    "gargantuar": {"health": 1500, "damage": 5, "speed": 0.3, "throw_range": 3},
    "king": {"health": 1200, "damage": 2, "speed": 0.4, "command_range": 5}
}

def cell_at(x, y):
    if x < LAWN_X or y < LAWN_Y:
        return None
    col = (x - LAWN_X) // CELL_W
    row = (y - LAWN_Y) // CELL_H
    if col >= GRID_COLS or row >= GRID_ROWS:
        return None
    return (col, row)

# === ENTITIES ===
class Sun:
    def __init__(self, x, y, falling=True):
        self.x = x
        self.y = y
        self.falling = falling
        self.target_y = y + 100 if falling else y
        self.speed = 1
        self.value = 25
        self.timer = 10 * FPS
        self.dead = False
        self.collected = False
    def update(self, dt):
        if self.falling and self.y < self.target_y:
            self.y += self.speed
        else:
            self.falling = False
            self.timer -= 1
            if self.timer <= 0:
                self.dead = True
    def draw(self, surf):
        surf.blit(SUN_SURF, (self.x - 20, self.y - 20))
    def hit(self, x, y):
        return abs(x - self.x) < 30 and abs(y - self.y) < 30

class Plant:
    def __init__(self, col, row, name):
        self.col = col
        self.row = row
        self.name = name
        self.x = LAWN_X + col * CELL_W + CELL_W // 2
        self.y = LAWN_Y + row * CELL_H + CELL_H // 2
        self.health = PLANT_DATA[name]["health"]
        self.cooldown = 0
        self.armed = False
        self.eating = False
        self.eat_timer = 0
        self.dead = False
    def update(self, dt, world):
        data = PLANT_DATA[self.name]
        if self.cooldown > 0:
            self.cooldown -= dt
        if self.name == "sunflower" and self.cooldown <= 0:
            world.suns.append(Sun(self.x, self.y, False))
            self.cooldown = data["cooldown"]
        elif self.name == "twinsunflower" and self.cooldown <= 0:
            world.suns.append(Sun(self.x - 15, self.y, False))
            world.suns.append(Sun(self.x + 15, self.y, False))
            self.cooldown = data["cooldown"]
        elif self.name in ["peashooter", "snowpea", "repeater", "gatlingpea"] and self.cooldown <= 0:
            for z in world.zombies:
                if z.row == self.row and z.x > self.x and not z.dead:
                    if self.name == "gatlingpea":
                        for i in range(4):
                            pea = Pea(self.x, self.y, self.row, data.get("slow", 0))
                            world.peas.append(pea)
                    else:
                        pea = Pea(self.x, self.y, self.row, data.get("slow", 0))
                        world.peas.append(pea)
                        if self.name == "repeater":
                            world.peas.append(Pea(self.x + 10, self.y, self.row, 0))
                    self.cooldown = data["cooldown"]
                    break
        elif self.name == "spikeweed" and self.cooldown <= 0:
            for z in world.zombies:
                if z.row == self.row and abs(z.col - self.col) <= 1 and not z.dead:
                    z.health -= data["damage"] * dt
            self.cooldown = data["cooldown"]
        elif self.name == "potatomine":
            if not self.armed and self.cooldown <= 0:
                self.armed = True
            elif self.armed:
                for z in world.zombies:
                    if z.row == self.row and abs(z.col - self.col) <= 1 and not z.dead:
                        for z2 in world.zombies:
                            if z2.row == self.row and abs(z2.col - self.col) <= 1:
                                z2.health -= data["damage"]
                        self.dead = True
                        break
        elif self.name == "jalapeno":
            if not self.armed and self.cooldown <= 0:
                self.armed = True
            elif self.armed:
                for z in world.zombies:
                    if z.row == self.row and not z.dead:
                        z.health -= data["damage"]
                self.dead = True
        elif self.name == "chomper":
            if self.eating:
                self.eat_timer -= dt
                if self.eat_timer <= 0:
                    self.eating = False
                    self.cooldown = data["cooldown"]
            elif self.cooldown <= 0:
                for z in world.zombies:
                    if z.row == self.row and abs(z.col - self.col) <= 1 and not z.dead:
                        z.dead = True
                        self.eating = True
                        self.eat_timer = 20
                        break
        if self.health <= 0:
            self.dead = True
    def draw(self, surf):
        surf.blit(PLANT_SURFS[self.name], (self.x - 30, self.y - 40))
        max_health = PLANT_DATA[self.name]["health"]
        ratio = self.health / max_health
        bar_w = 40
        pygame.draw.rect(surf, RED, (self.x - 20, self.y - 50, bar_w, 5))
        pygame.draw.rect(surf, GREEN, (self.x - 20, self.y - 50, bar_w * ratio, 5))

class Zombie:
    def __init__(self, ztype, row):
        self.type = ztype
        self.row = row
        self.col = GRID_COLS
        self.x = LAWN_X + self.col * CELL_W + CELL_W // 2
        self.y = LAWN_Y + row * CELL_H + CELL_H // 2
        self.health = ZOMBIE_DATA[ztype]["health"]
        self.speed = ZOMBIE_DATA[ztype]["speed"]
        self.damage = ZOMBIE_DATA[ztype]["damage"]
        self.eating = None
        self.slowed = 0
        self.raging = False
        self.dead = False
        self.summon_timer = 0
        self.throw_timer = 0
        self.command_timer = 0
    def update(self, dt, world):
        actual_speed = self.speed
        if self.slowed > 0:
            actual_speed *= 0.5
            self.slowed -= dt
        if self.type == "newspaper" and self.health < ZOMBIE_DATA["newspaper"]["health"] * 0.5 and not self.raging:
            self.raging = True
            self.speed = ZOMBIE_DATA["newspaper"]["rage_speed"]
        if self.type == "dancer":
            self.summon_timer += dt
            if self.summon_timer > ZOMBIE_DATA["dancer"]["summon_rate"]:
                self.summon_timer = 0
                if len([z for z in world.zombies if z.row == self.row]) < 3:
                    world.zombies.append(Zombie("regular", self.row))
        if self.type == "gargantuar":
            self.throw_timer += dt
            if self.throw_timer > 10:
                self.throw_timer = 0
                closest_plant = None
                min_dist = float('inf')
                for p in world.plants:
                    if p.row == self.row and not p.dead:
                        dist = abs(p.col - self.col)
                        if dist < min_dist and dist <= ZOMBIE_DATA["gargantuar"]["throw_range"]:
                            min_dist = dist
                            closest_plant = p
                if closest_plant:
                    closest_plant.health = 0
        if self.type == "king":
            self.command_timer += dt
            if self.command_timer > 5:
                self.command_timer = 0
                for z in world.zombies:
                    if z != self and abs(z.row - self.row) <= 2 and abs(z.col - self.col) <= ZOMBIE_DATA["king"]["command_range"]:
                        z.speed *= 1.5
                        z.slowed = max(0, z.slowed)
        if self.eating:
            if self.eating.dead:
                self.eating = None
            else:
                self.eating.health -= self.damage * dt
                return
        target_col = int(self.col)
        for p in world.plants_by_row[self.row]:
            if int(p.col) == target_col and not p.dead:
                self.eating = p
                return
        self.col -= actual_speed * dt
        self.x = LAWN_X + self.col * CELL_W + CELL_W // 2
        if self.col < 0:
            world.game_over = True
        if self.health <= 0:
            self.dead = True
    def draw(self, surf):
        if self.type == "gargantuar":
            surf.blit(ZOMBIE_SURFS[self.type], (self.x - 40, self.y - 60))
        else:
            surf.blit(ZOMBIE_SURFS[self.type], (self.x - 30, self.y - 50))
        max_health = ZOMBIE_DATA[self.type]["health"]
        ratio = self.health / max_health
        bar_w = 40
        bar_x = self.x - 20
        if self.type == "gargantuar":
            bar_w = 60
            bar_x = self.x - 30
        pygame.draw.rect(surf, RED, (bar_x, self.y - 60, bar_w, 5))
        pygame.draw.rect(surf, GREEN, (bar_x, self.y - 60, bar_w * ratio, 5))

class Pea:
    def __init__(self, x, y, row, slow=0):
        self.x = x
        self.y = y
        self.row = row
        self.speed = 5
        self.damage = 20
        self.slow = slow
        self.dead = False
    def update(self, dt, zombies):
        self.x += self.speed
        for z in zombies:
            if z.row == self.row and abs(z.x - self.x) < 30 and not z.dead:
                z.health -= self.damage
                if self.slow > 0:
                    z.slowed = self.slow
                self.dead = True
                break
        if self.x > WIDTH:
            self.dead = True
    def draw(self, surf):
        surf.blit(PEA_SURF, (self.x - 10, self.y - 10))

class LawnMower:
    def __init__(self, row):
        self.row = row
        self.x = LAWN_X - 30
        self.y = LAWN_Y + row * CELL_H + CELL_H // 2
        self.active = False
        self.speed = 10
        self.dead = False
    def update(self, dt):
        if self.active:
            self.x += self.speed
            if self.x > WIDTH:
                self.dead = True
    def draw(self, surf):
        if not self.active:
            surf.blit(LAWNMOWER_SURF, (self.x, self.y - 30))

class CrazyDave:
    def __init__(self):
        self.messages = [
            "Welcome to ULTRA Plants vs Zombies!",
            "New plants: Gatling Pea, Twin Sunflower, Spikeweed, Jalapeno!",
            "New zombies: Dancer, Gargantuar, Zombie King!",
            "Collect sun, plant defenders, and survive all waves!",
            "Good luck!"
        ]
        self.current_message = 0
        self.done = False
    def next(self):
        self.current_message += 1
        if self.current_message >= len(self.messages):
            self.done = True
    def draw(self, surf):
        if self.done:
            return
        message = self.messages[self.current_message]
        text = FONT_MEDIUM.render(message, True, BLACK)
        bubble_rect = pygame.Rect(50, 50, text.get_width() + 40, text.get_height() + 40)
        pygame.draw.rect(surf, WHITE, bubble_rect, border_radius=10)
        pygame.draw.rect(surf, BLACK, bubble_rect, 2, border_radius=10)
        surf.blit(text, (bubble_rect.centerx - text.get_width()//2, bubble_rect.centery - text.get_height()//2))
        cont = FONT_SMALL.render("Press SPACE to continue", True, BLACK)
        surf.blit(cont, (bubble_rect.centerx - cont.get_width()//2, bubble_rect.bottom + 10))

class Intro:
    def __init__(self):
        self.state = "fade_in"
        self.alpha = 0
        self.timer = 0
    def update(self, dt):
        self.timer += dt
        if self.state == "fade_in":
            self.alpha = min(255, self.alpha + 2)
            if self.alpha >= 255:
                self.state = "show"
                self.timer = 0
        elif self.state == "show":
            if self.timer > 3:
                self.state = "fade_out"
        elif self.state == "fade_out":
            self.alpha = max(0, self.alpha - 2)
            if self.alpha <= 0:
                self.state = "done"
    def draw(self, surf):
        surf.fill(BLACK)
        title = FONT_BIG.render("ULTRA Plants vs Zombies", True, GOLD)
        title.set_alpha(self.alpha)
        surf.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - title.get_height()//2))
        sub = FONT_MEDIUM.render("PyGame Edition", True, WHITE)
        sub.set_alpha(self.alpha)
        surf.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2 + 50))

class MainMenu:
    def __init__(self):
        # Fixed button sizes and positions for 800x600
        button_width = 250
        button_height = 50
        button_x = WIDTH//2 - button_width//2
        start_y = HEIGHT//2 - 120
        
        self.buttons = [
            {"text": "Adventure", "rect": pygame.Rect(button_x, start_y, button_width, button_height), "action": "adventure"},
            {"text": "Survival", "rect": pygame.Rect(button_x, start_y + 70, button_width, button_height), "action": "survival"},
            {"text": "Mini-Games", "rect": pygame.Rect(button_x, start_y + 140, button_width, button_height), "action": "minigames"},
            {"text": "Zombatar", "rect": pygame.Rect(button_x, start_y + 210, button_width, button_height), "action": "zombatar"},
            {"text": "Options", "rect": pygame.Rect(button_x, start_y + 280, button_width, button_height), "action": "options"},
            {"text": "Quit", "rect": pygame.Rect(button_x, start_y + 350, button_width, button_height), "action": "quit"}
        ]
        self.hovered_button = None
    def handle_event(self, event):
        if event.type == MOUSEMOTION:
            self.hovered_button = None
            for button in self.buttons:
                if button["rect"].collidepoint(event.pos):
                    self.hovered_button = button
                    break
        elif event.type == MOUSEBUTTONDOWN:
            for button in self.buttons:
                if button["rect"].collidepoint(event.pos):
                    return button["action"]
        return None
    def draw(self, surf):
        for y in range(HEIGHT):
            color_ratio = y / HEIGHT
            r = int(SKY_BLUE[0] * (1 - color_ratio) + LIGHT_BLUE[0] * color_ratio)
            g = int(SKY_BLUE[1] * (1 - color_ratio) + LIGHT_BLUE[1] * color_ratio)
            b = int(SKY_BLUE[2] * (1 - color_ratio) + LIGHT_BLUE[2] * color_ratio)
            pygame.draw.line(surf, (r, g, b), (0, y), (WIDTH, y))
        title_shadow = FONT_TITLE.render("ULTRA Plants vs Zombies", True, DARK_GREEN)
        title_text = FONT_TITLE.render("ULTRA Plants vs Zombies", True, GOLD)
        surf.blit(title_shadow, (WIDTH//2 - title_shadow.get_width()//2 + 3, 83))
        surf.blit(title_text, (WIDTH//2 - title_text.get_width()//2, 80))
        subtitle = FONT_MEDIUM.render("PyGame Edition", True, WHITE)
        surf.blit(subtitle, (WIDTH//2 - subtitle.get_width()//2, 140))
        for i in range(4):  # Adjusted number of suns
            x = 100 + i * 200
            y = 250
            pygame.draw.circle(surf, (255, 220, 50, 200), (x, y), 30)
            pygame.draw.circle(surf, (255, 255, 150), (x, y), 20)
        for i in range(2):  # Adjusted number of zombies
            x = 150 + i * 350
            y = 350
            pygame.draw.rect(surf, (150, 150, 150), (x, y, 30, 50), border_radius=5)
        for button in self.buttons:
            if button == self.hovered_button:
                color = BUTTON_HOVER
                border_color = GOLD
            else:
                color = LAWN_GREEN
                border_color = DARK_GREEN
            pygame.draw.rect(surf, color, button["rect"], border_radius=15)
            pygame.draw.rect(surf, border_color, button["rect"], 3, border_radius=15)
            text = FONT_MEDIUM.render(button["text"], True, BLACK)
            surf.blit(text, (button["rect"].centerx - text.get_width()//2, 
                            button["rect"].centery - text.get_height()//2))
        footer = FONT_SMALL.render("[C] Samsoft Computing [C] 1999-2025", True, WHITE)
        surf.blit(footer, (WIDTH//2 - footer.get_width()//2, HEIGHT - 40))

class OptionsMenu:
    def __init__(self):
        self.buttons = [
            {"text": "Back", "rect": pygame.Rect(WIDTH//2 - 150, HEIGHT//2 + 120, 300, 60), "action": "back"}
        ]
        self.sliders = [
            {"label": "Music Volume", "rect": pygame.Rect(WIDTH//2 - 150, HEIGHT//2 - 60, 300, 30), "value": 50},
            {"label": "Sound Volume", "rect": pygame.Rect(WIDTH//2 - 150, HEIGHT//2, 300, 30), "value": 70},
            {"label": "Game Speed", "rect": pygame.Rect(WIDTH//2 - 150, HEIGHT//2 + 60, 300, 30), "value": 50}
        ]
        self.hovered_button = None
        self.dragging_slider = None
    def handle_event(self, event):
        if event.type == MOUSEMOTION:
            self.hovered_button = None
            for button in self.buttons:
                if button["rect"].collidepoint(event.pos):
                    self.hovered_button = button
                    break
            if self.dragging_slider is not None and event.buttons[0]:
                slider = self.sliders[self.dragging_slider]
                relative_x = event.pos[0] - slider["rect"].x
                slider["value"] = max(0, min(100, int(relative_x / slider["rect"].width * 100)))
        elif event.type == MOUSEBUTTONDOWN:
            for i, slider in enumerate(self.sliders):
                if slider["rect"].collidepoint(event.pos):
                    self.dragging_slider = i
                    relative_x = event.pos[0] - slider["rect"].x
                    slider["value"] = max(0, min(100, int(relative_x / slider["rect"].width * 100)))
                    break
            for button in self.buttons:
                if button["rect"].collidepoint(event.pos):
                    return button["action"]
        elif event.type == MOUSEBUTTONUP:
            self.dragging_slider = None
        return None
    def draw(self, surf):
        surf.fill(SKY_BLUE)
        title = FONT_BIG.render("ULTRA Options", True, BLACK)
        surf.blit(title, (WIDTH//2 - title.get_width()//2, 100))
        for slider in self.sliders:
            pygame.draw.rect(surf, (200, 200, 200), slider["rect"], border_radius=5)
            pygame.draw.rect(surf, BLACK, slider["rect"], 2, border_radius=5)
            fill_width = int(slider["rect"].width * slider["value"] / 100)
            fill_rect = pygame.Rect(slider["rect"].x, slider["rect"].y, fill_width, slider["rect"].height)
            pygame.draw.rect(surf, LAWN_GREEN, fill_rect, border_radius=5)
            handle_x = slider["rect"].x + fill_width - 5
            handle_rect = pygame.Rect(handle_x, slider["rect"].y - 5, 10, slider["rect"].height + 10)
            pygame.draw.rect(surf, DARK_GREEN, handle_rect, border_radius=5)
            label = FONT_MEDIUM.render(slider["label"], True, BLACK)
            surf.blit(label, (slider["rect"].x, slider["rect"].y - 30))
            value_text = FONT_SMALL.render(f"{slider['value']}%", True, BLACK)
            surf.blit(value_text, (slider["rect"].right + 10, slider["rect"].y))

# === WORLD ===
class World:
    def __init__(self):
        self.reset()
    def reset(self):
        self.plants = []
        self.plants_by_row = [[] for _ in range(GRID_ROWS)]
        self.zombies = []
        self.peas = []
        self.suns = []
        self.mowers = [LawnMower(r) for r in range(GRID_ROWS)]
        self.sun_count = 100
        self.selected = None
        self.recharge_timers = {k: 0.0 for k in PLANT_DATA}
        self.wave = 1
        self.total_waves = 8
        self.zombies_this_wave = 0
        self.spawn_timer = 0
        self.spawn_delay = 7.0
        self.game_over = False
        self.victory = False
        self.tutorial = True
        self.dave = CrazyDave()
        self.score = 0
        self.zombies_killed = 0
    def plant_at(self, col, row):
        for p in self.plants_by_row[row]:
            if p.col == col:
                return p
        return None
    def add_plant(self, name, col, row):
        p = Plant(col, row, name)
        self.plants.append(p)
        self.plants_by_row[row].append(p)
        self.sun_count -= PLANT_DATA[name]["cost"]
        self.recharge_timers[name] = PLANT_DATA[name]["recharge"]
    def remove_plant(self, p):
        if p in self.plants:
            self.plants.remove(p)
        if p in self.plants_by_row[p.row]:
            self.plants_by_row[p.row].remove(p)
    def update(self, dt):
        if self.game_over or self.victory or (self.tutorial and not self.dave.done):
            return
        for k in self.recharge_timers:
            self.recharge_timers[k] = max(0, self.recharge_timers[k] - dt)
        if random.random() < 0.01:
            x = random.randint(LAWN_X + 50, SPAWN_X - 50)
            self.suns.append(Sun(x, LAWN_Y, True))
        self.spawn_timer += dt
        if self.zombies_this_wave < self.wave * 5 and self.spawn_timer > self.spawn_delay:
            self.spawn_timer = 0
            zombie_weights = {
                "regular": 10,
                "cone": 8,
                "bucket": 6,
                "newspaper": 5,
                "football": 4
            }
            if self.wave >= 3:
                zombie_weights["dancer"] = 3
            if self.wave >= 5:
                zombie_weights["gargantuar"] = 2
            if self.wave >= 7:
                zombie_weights["king"] = 1
            zombie_list = []
            for ztype, weight in zombie_weights.items():
                zombie_list.extend([ztype] * weight)
            ztype = random.choice(zombie_list)
            row = random.randint(0, 4)
            self.zombies.append(Zombie(ztype, row))
            self.zombies_this_wave += 1
        elif self.zombies_this_wave >= self.wave * 5 and not any(not z.dead for z in self.zombies):
            if self.wave >= self.total_waves:
                self.victory = True
                self.score += 1000 * self.wave
            else:
                self.wave += 1
                self.zombies_this_wave = 0
                self.spawn_delay = max(2.0, self.spawn_delay - 0.5)
                self.score += 100 * self.wave
        for p in self.plants[:]:
            if p.dead:
                self.remove_plant(p)
            else:
                p.update(dt, self)
        for z in self.zombies[:]:
            z.update(dt, self)
            if z.dead:
                self.zombies.remove(z)
                self.zombies_killed += 1
                self.score += ZOMBIE_DATA[z.type]["health"] // 10
        for pea in self.peas[:]:
            pea.update(dt, self.zombies)
            if pea.dead:
                self.peas.remove(pea)
        for sun in self.suns[:]:
            sun.update(dt)
            if sun.dead:
                self.suns.remove(sun)
        for m in self.mowers:
            m.update(dt)
            if not m.active:
                for z in self.zombies:
                    if z.row == m.row and z.x < m.x + 60 and not z.dead:
                        m.active = True
                        break
    def draw_lawn(self, surf):
        pygame.draw.rect(surf, (139, 90, 43), (0, LAWN_Y, HOUSE_W, HEIGHT - LAWN_Y))
        pygame.draw.rect(surf, (100, 70, 30), (10, LAWN_Y + 10, HOUSE_W - 20, 50))
        pygame.draw.rect(surf, (80, 60, 20), (20, LAWN_Y + 70, 30, 100))
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                x = LAWN_X + c * CELL_W
                y = LAWN_Y + r * CELL_H
                color = LAWN_GREEN if (r + c) % 2 == 0 else LAWN_DARK
                pygame.draw.rect(surf, color, (x, y, CELL_W, CELL_H))
                pygame.draw.rect(surf, BLACK, (x, y, CELL_W, CELL_H), 1)
        pygame.draw.line(surf, BLACK, (SPAWN_X, LAWN_Y), (SPAWN_X, HEIGHT), 3)

    def draw_ui(self, surf):
        pygame.draw.rect(surf, (180, 180, 180), (0, 0, WIDTH, UI_HEIGHT))
        pygame.draw.line(surf, BLACK, (0, UI_HEIGHT), (WIDTH, UI_HEIGHT), 2)

        # Sun counter
        pygame.draw.rect(surf, (255, 220, 150), (10, 10, 80, 60), border_radius=10)
        pygame.draw.rect(surf, BLACK, (10, 10, 80, 60), 2, border_radius=10)
        surf.blit(SUN_SURF, (20, 20))
        sun_txt = FONT_BIG.render(str(int(self.sun_count)), True, BLACK)
        surf.blit(sun_txt, (100, 25))

        # Wave & Score — right-aligned
        right_margin = 20
        wave_txt = FONT_MEDIUM.render(f"Wave: {self.wave}/{self.total_waves}", True, BLACK)
        surf.blit(wave_txt, (WIDTH - wave_txt.get_width() - right_margin, 15))
        score_txt = FONT_SMALL.render(f"Score: {self.score}", True, BLACK)
        surf.blit(score_txt, (WIDTH - score_txt.get_width() - right_margin, 45))

        # Plant cards — dynamic spacing for 800px width
        card_width = 65
        card_height = 85
        left_margin = 180
        right_bound = WIDTH - right_margin
        available_width = right_bound - left_margin
        min_spacing = 60
        ideal_spacing = max(min_spacing, available_width / len(PLANT_DATA))
        x = left_margin
        for name in PLANT_DATA:
            card = CARD_SURFS[name].copy()
            t = self.recharge_timers[name]
            maxt = PLANT_DATA[name]["recharge"]
            affordable = self.sun_count >= PLANT_DATA[name]["cost"]
            if t > 0 or not affordable:
                overlay = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 150))
                card.blit(overlay, (0, 0))
            if self.selected == name:
                pygame.draw.rect(card, ORANGE, (0, 0, card_width, card_height), 4, border_radius=8)
            surf.blit(card, (x, 5))
            if t > 0:
                h = int((t / maxt) * card_height)
                cover = pygame.Surface((card_width, h), pygame.SRCALPHA)
                cover.fill((0, 0, 0, 180))
                surf.blit(cover, (x, 5 + card_height - h))
            cost_txt = FONT_SMALL.render(str(PLANT_DATA[name]["cost"]), True, BLACK)
            surf.blit(cost_txt, (x + card_width//2 - cost_txt.get_width()//2, 70))
            x += ideal_spacing

    def draw_game(self, surf):
        surf.fill(SKY_BLUE)
        self.draw_lawn(surf)
        for s in self.suns:
            s.draw(surf)
        for m in self.mowers:
            m.draw(surf)
        for p in self.plants:
            p.draw(surf)
        for pea in self.peas:
            pea.draw(surf)
        for z in self.zombies:
            z.draw(surf)
        self.draw_ui(surf)
        if self.tutorial and not self.dave.done:
            self.dave.draw(surf)
        if self.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            surf.blit(overlay, (0, 0))
            txt = FONT_BIG.render("GAME OVER!", True, RED)
            surf.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 50))
            score_txt = FONT_MEDIUM.render(f"Final Score: {self.score}", True, WHITE)
            surf.blit(score_txt, (WIDTH // 2 - score_txt.get_width() // 2, HEIGHT // 2))
            restart = FONT_MEDIUM.render("Press R to restart or ESC for menu", True, WHITE)
            surf.blit(restart, (WIDTH // 2 - restart.get_width() // 2, HEIGHT // 2 + 50))
        if self.victory:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            surf.blit(overlay, (0, 0))
            txt = FONT_BIG.render("VICTORY!", True, GREEN)
            surf.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 50))
            score_txt = FONT_MEDIUM.render(f"Final Score: {self.score}", True, WHITE)
            surf.blit(score_txt, (WIDTH // 2 - score_txt.get_width() // 2, HEIGHT // 2))
            restart = FONT_MEDIUM.render("Press R to restart or ESC for menu", True, WHITE)
            surf.blit(restart, (WIDTH // 2 - restart.get_width() // 2, HEIGHT // 2 + 50))

# === MAIN LOOP ===
def main():
    load_surfaces()
    intro = Intro()
    menu = MainMenu()
    options = OptionsMenu()
    world = None
    state = "intro"
    dt = 0
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        for e in pygame.event.get():
            if e.type == QUIT:
                running = False
            if state == "menu":
                res = menu.handle_event(e)
                if res == "adventure":
                    world = World()
                    state = "game"
                elif res == "options":
                    state = "options"
                elif res == "quit":
                    running = False
            elif state == "options":
                res = options.handle_event(e)
                if res == "back":
                    state = "menu"
            elif state == "game" and world:
                if e.type == KEYDOWN:
                    if e.key == K_ESCAPE:
                        state = "menu"
                    elif e.key == K_r and (world.game_over or world.victory):
                        world = World()
                    elif e.key == K_SPACE and world.tutorial and not world.dave.done:
                        world.dave.next()
                elif e.type == MOUSEBUTTONDOWN and not world.game_over and not world.victory:
                    mx, my = e.pos
                    for s in world.suns[:]:
                        if s.hit(mx, my):
                            world.sun_count += s.value
                            world.suns.remove(s)
                            break
                    if my < UI_HEIGHT:
                        # Use same spacing logic as draw_ui
                        card_width = 65
                        left_margin = 180
                        right_margin = 20
                        available_width = WIDTH - right_margin - left_margin
                        ideal_spacing = max(60, available_width / len(PLANT_DATA))
                        x = left_margin
                        for name in PLANT_DATA:
                            rect = pygame.Rect(x, 5, card_width, 85)
                            if rect.collidepoint(mx, my):
                                if world.recharge_timers[name] <= 0 and world.sun_count >= PLANT_DATA[name]["cost"]:
                                    world.selected = name
                            x += ideal_spacing
                    else:
                        cell = cell_at(mx, my)
                        if cell and world.selected:
                            col, row = cell
                            if not world.plant_at(col, row):
                                world.add_plant(world.selected, col, row)
                                world.selected = None
            elif state == "intro" and e.type in (KEYDOWN, MOUSEBUTTONDOWN):
                intro.state = "done"
        if state == "intro":
            intro.update(dt)
            if intro.state == "done":
                state = "menu"
        elif state == "game" and world:
            world.update(dt)
        if state == "intro":
            screen.fill(BLACK)
            intro.draw(screen)
        elif state == "menu":
            menu.draw(screen)
        elif state == "options":
            options.draw(screen)
        elif state == "game" and world:
            world.draw_game(screen)
        pygame.display.flip()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
