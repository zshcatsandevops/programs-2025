import pygame
import sys
import random
import math
from pygame.locals import *

# Initialize pygame
pygame.init()
pygame.mixer.init()

# Constants
WIDTH, HEIGHT = 1000, 600
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

# Game settings
FPS = 60

# Create window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Plants vs Zombies")
clock = pygame.time.Clock()

# Fonts
FONT_SMALL = pygame.font.SysFont("Arial", 16)
FONT_MEDIUM = pygame.font.SysFont("Arial", 24)
FONT_BIG = pygame.font.SysFont("Arial", 36)

# Load images (in a real game, these would be actual image files)
def load_surfaces():
    global SUN_SURF, CARD_SURFS, PLANT_SURFS, ZOMBIE_SURFS, PEA_SURF, LAWNMOWER_SURF
    
    # Create placeholder surfaces
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
        "chomper": (100, 50, 150)
    }
    
    for name, color in plant_colors.items():
        surf = pygame.Surface((65, 85), pygame.SRCALPHA)
        pygame.draw.rect(surf, color, (0, 0, 65, 85), border_radius=8)
        pygame.draw.rect(surf, BLACK, (0, 0, 65, 85), 2, border_radius=8)
        text = FONT_SMALL.render(name[:6], True, BLACK)
        surf.blit(text, (32 - text.get_width()//2, 42 - text.get_height()//2))
        CARD_SURFS[name] = surf
    
    # Plant surfaces
    PLANT_SURFS = {}
    for name in plant_colors:
        surf = pygame.Surface((60, 80), pygame.SRCALPHA)
        pygame.draw.rect(surf, plant_colors[name], (10, 10, 40, 60), border_radius=5)
        PLANT_SURFS[name] = surf
    
    # Zombie surfaces
    ZOMBIE_SURFS = {}
    zombie_types = ["regular", "cone", "bucket", "newspaper", "football"]
    zombie_colors = {
        "regular": (150, 150, 150),
        "cone": (100, 100, 200),
        "bucket": (100, 100, 100),
        "newspaper": (200, 200, 150),
        "football": (150, 100, 50)
    }
    
    for ztype in zombie_types:
        surf = pygame.Surface((60, 100), pygame.SRCALPHA)
        pygame.draw.rect(surf, zombie_colors[ztype], (10, 10, 40, 80), border_radius=5)
        ZOMBIE_SURFS[ztype] = surf
    
    # Pea surface
    PEA_SURF = pygame.Surface((20, 20), pygame.SRCALPHA)
    pygame.draw.circle(PEA_SURF, (50, 200, 50), (10, 10), 10)
    
    # Lawnmower surface
    LAWNMOWER_SURF = pygame.Surface((60, 60), pygame.SRCALPHA)
    pygame.draw.rect(LAWNMOWER_SURF, (200, 200, 200), (0, 20, 50, 30))
    pygame.draw.rect(LAWNMOWER_SURF, (150, 150, 150), (10, 10, 30, 10))

# Plant data
PLANT_DATA = {
    "peashooter": {"cost": 100, "recharge": 7.5, "health": 100, "damage": 20, "cooldown": 1.5},
    "sunflower": {"cost": 50, "recharge": 7.5, "health": 100, "sun_production": 25, "cooldown": 24},
    "wallnut": {"cost": 50, "recharge": 30, "health": 400},
    "cherrybomb": {"cost": 150, "recharge": 50, "health": 100, "damage": 1800, "cooldown": 3},
    "snowpea": {"cost": 175, "recharge": 7.5, "health": 100, "damage": 20, "cooldown": 1.5, "slow": 0.5},
    "repeater": {"cost": 200, "recharge": 7.5, "health": 100, "damage": 20, "cooldown": 1.5, "double": True},
    "potatomine": {"cost": 25, "recharge": 30, "health": 100, "damage": 1800, "cooldown": 15},
    "chomper": {"cost": 150, "recharge": 7.5, "health": 100, "damage": 1000, "cooldown": 42}
}

# Zombie data
ZOMBIE_DATA = {
    "regular": {"health": 200, "damage": 1, "speed": 0.5},
    "cone": {"health": 400, "damage": 1, "speed": 0.5},
    "bucket": {"health": 600, "damage": 1, "speed": 0.5},
    "newspaper": {"health": 200, "damage": 1, "speed": 0.7, "rage_speed": 1.5},
    "football": {"health": 800, "damage": 2, "speed": 0.8}
}

# Helper functions
def cell_at(x, y):
    if x < LAWN_X or y < LAWN_Y:
        return None
    col = (x - LAWN_X) // CELL_W
    row = (y - LAWN_Y) // CELL_H
    if col >= GRID_COLS or row >= GRID_ROWS:
        return None
    return (col, row)

# Game classes
class Sun:
    def __init__(self, x, y, falling=True):
        self.x = x
        self.y = y
        self.falling = falling
        self.target_y = y + 100 if falling else y
        self.speed = 1 if falling else 0
        self.value = 25
        self.timer = 10 * FPS  # 10 seconds
        self.dead = False
        self.collected = False
        
    def update(self, dt):
        if self.falling:
            if self.y < self.target_y:
                self.y += self.speed
            else:
                self.falling = False
        else:
            self.timer -= 1
            if self.timer <= 0:
                self.dead = True
                
    def draw(self, surf):
        surf.blit(SUN_SURF, (self.x - 20, self.y - 20))
        
    def hit(self, x, y):
        return (abs(x - self.x) < 30 and abs(y - self.y) < 30)

class Plant:
    def __init__(self, col, row, name):
        self.col = col
        self.row = row
        self.name = name
        self.x = LAWN_X + col * CELL_W + CELL_W // 2
        self.y = LAWN_Y + row * CELL_H + CELL_H // 2
        self.health = PLANT_DATA[name]["health"]
        self.cooldown = 0
        self.armed = False  # for potato mine
        self.eating = False  # for chomper
        self.eat_timer = 0
        self.dead = False
        
    def update(self, dt, world):
        data = PLANT_DATA[self.name]
        
        # Update cooldowns
        if self.cooldown > 0:
            self.cooldown -= dt
            
        # Plant-specific behavior
        if self.name == "sunflower" and self.cooldown <= 0:
            world.suns.append(Sun(self.x, self.y, False))
            self.cooldown = data["cooldown"]
            
        elif self.name in ["peashooter", "snowpea", "repeater"] and self.cooldown <= 0:
            # Check if there's a zombie in the same row
            for z in world.zombies:
                if z.row == self.row and z.x < WIDTH - HOUSE_W and z.x > self.x and not z.dead:
                    # Shoot pea
                    pea = Pea(self.x, self.y, self.row, data.get("slow", 0))
                    world.peas.append(pea)
                    
                    # Repeater shoots two peas
                    if self.name == "repeater":
                        world.peas.append(Pea(self.x + 10, self.y, self.row, 0))
                    
                    self.cooldown = data["cooldown"]
                    break
                    
        elif self.name == "potatomine":
            if not self.armed and self.cooldown <= 0:
                self.armed = True
            elif self.armed:
                # Check for zombies in adjacent cells
                for z in world.zombies:
                    if z.row == self.row and abs(z.col - self.col) <= 1 and not z.dead:
                        # Explode
                        for z2 in world.zombies:
                            if z2.row == self.row and abs(z2.col - self.col) <= 1:
                                z2.health -= data["damage"]
                        self.dead = True
                        break
                        
        elif self.name == "chomper":
            if self.eating:
                self.eat_timer -= dt
                if self.eat_timer <= 0:
                    self.eating = False
                    self.cooldown = data["cooldown"]
            elif self.cooldown <= 0:
                # Check for zombies in front
                for z in world.zombies:
                    if z.row == self.row and abs(z.col - self.col) <= 1 and not z.dead:
                        z.dead = True
                        self.eating = True
                        self.eat_timer = 20  # 20 seconds to digest
                        break
        
        # Check health
        if self.health <= 0:
            self.dead = True
            
    def draw(self, surf):
        surf.blit(PLANT_SURFS[self.name], (self.x - 30, self.y - 40))
        
        # Draw health bar
        max_health = PLANT_DATA[self.name]["health"]
        health_ratio = self.health / max_health
        bar_width = 40
        pygame.draw.rect(surf, (255, 0, 0), (self.x - 20, self.y - 50, bar_width, 5))
        pygame.draw.rect(surf, (0, 255, 0), (self.x - 20, self.y - 50, bar_width * health_ratio, 5))

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
        
    def update(self, dt, world):
        # Apply slow effect
        actual_speed = self.speed
        if self.slowed > 0:
            actual_speed *= 0.5
            self.slowed -= dt
            
        # Newspaper zombie rage
        if self.type == "newspaper" and self.health < ZOMBIE_DATA["newspaper"]["health"] * 0.5 and not self.raging:
            self.raging = True
            self.speed = ZOMBIE_DATA["newspaper"]["rage_speed"]
            
        # Check if eating a plant
        if self.eating:
            if self.eating.dead:
                self.eating = None
            else:
                self.eating.health -= self.damage * dt
                return
                
        # Check for plants in front
        target_col = int(self.col)
        for p in world.plants_by_row[self.row]:
            if int(p.col) == target_col and not p.dead:
                self.eating = p
                return
                
        # Move left
        self.col -= actual_speed * dt
        self.x = LAWN_X + self.col * CELL_W + CELL_W // 2
        
        # Check if reached the house
        if self.col < 0:
            world.game_over = True
            
        # Check health
        if self.health <= 0:
            self.dead = True
            
    def draw(self, surf):
        surf.blit(ZOMBIE_SURFS[self.type], (self.x - 30, self.y - 50))
        
        # Draw health bar
        max_health = ZOMBIE_DATA[self.type]["health"]
        health_ratio = self.health / max_health
        bar_width = 40
        pygame.draw.rect(surf, (255, 0, 0), (self.x - 20, self.y - 60, bar_width, 5))
        pygame.draw.rect(surf, (0, 255, 0), (self.x - 20, self.y - 60, bar_width * health_ratio, 5))

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
        
        # Check for collision with zombies
        for z in zombies:
            if z.row == self.row and abs(z.x - self.x) < 30 and not z.dead:
                z.health -= self.damage
                if self.slow > 0:
                    z.slowed = self.slow
                self.dead = True
                break
                
        # Check if off screen
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
            
            # Check if off screen
            if self.x > WIDTH:
                self.dead = True
                
    def draw(self, surf):
        if not self.active:
            surf.blit(LAWNMOWER_SURF, (self.x, self.y - 30))

class CrazyDave:
    def __init__(self):
        self.messages = [
            "Welcome to Plants vs Zombies!",
            "Click on the suns to collect them.",
            "Select a plant card and click on the lawn to plant it.",
            "Sunflowers produce sun, Peashooters shoot peas.",
            "Defend your house from the zombies!",
            "Good luck!"
        ]
        self.current_message = 0
        self.done = False
        self.timer = 0
        
    def next(self):
        self.current_message += 1
        if self.current_message >= len(self.messages):
            self.done = True
            
    def draw(self, surf):
        if self.done:
            return
            
        # Draw speech bubble
        message = self.messages[self.current_message]
        text = FONT_MEDIUM.render(message, True, BLACK)
        
        bubble_rect = pygame.Rect(50, 50, text.get_width() + 40, text.get_height() + 40)
        pygame.draw.rect(surf, WHITE, bubble_rect, border_radius=10)
        pygame.draw.rect(surf, BLACK, bubble_rect, 2, border_radius=10)
        
        surf.blit(text, (bubble_rect.centerx - text.get_width()//2, bubble_rect.centery - text.get_height()//2))
        
        # Draw "Press SPACE to continue"
        continue_text = FONT_SMALL.render("Press SPACE to continue", True, BLACK)
        surf.blit(continue_text, (bubble_rect.centerx - continue_text.get_width()//2, bubble_rect.bottom + 10))

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
            if self.timer > 3:  # Show for 3 seconds
                self.state = "fade_out"
                
        elif self.state == "fade_out":
            self.alpha = max(0, self.alpha - 2)
            if self.alpha <= 0:
                self.state = "done"
                
    def draw(self, surf):
        surf.fill(BLACK)
        
        title = FONT_BIG.render("Plants vs Zombies", True, WHITE)
        title.set_alpha(self.alpha)
        surf.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - title.get_height()//2))
        
        subtitle = FONT_MEDIUM.render("PyGame Edition", True, WHITE)
        subtitle.set_alpha(self.alpha)
        surf.blit(subtitle, (WIDTH//2 - subtitle.get_width()//2, HEIGHT//2 + 50))

class MainMenu:
    def __init__(self):
        self.buttons = [
            {"text": "Adventure", "rect": pygame.Rect(WIDTH//2 - 100, HEIGHT//2 - 50, 200, 50)},
            {"text": "Options", "rect": pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 20, 200, 50)},
            {"text": "Quit", "rect": pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 90, 200, 50)}
        ]
        
    def handle(self, event):
        if event.type == MOUSEBUTTONDOWN:
            for button in self.buttons:
                if button["rect"].collidepoint(event.pos):
                    return button["text"].lower()
        return None
        
    def draw(self, surf):
        surf.fill(SKY_BLUE)
        
        title = FONT_BIG.render("Plants vs Zombies", True, BLACK)
        surf.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//4))
        
        for button in self.buttons:
            pygame.draw.rect(surf, LAWN_GREEN, button["rect"], border_radius=10)
            pygame.draw.rect(surf, BLACK, button["rect"], 2, border_radius=10)
            
            text = FONT_MEDIUM.render(button["text"], True, BLACK)
            surf.blit(text, (button["rect"].centerx - text.get_width()//2, 
                            button["rect"].centery - text.get_height()//2))

# === WORLD ================================================================
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
        self.sun_count = 50
        self.selected = None
        self.recharge_timers = {k: 0.0 for k in PLANT_DATA}
        self.wave = 1
        self.total_waves = 5
        self.zombies_this_wave = 0
        self.spawn_timer = 0
        self.spawn_delay = 7.0
        self.game_over = False
        self.victory = False
        self.tutorial = True
        self.dave = CrazyDave()

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

    # --- Update ------------------------------------------------------------
    def update(self, dt):
        if self.game_over or self.victory:
            return
        if self.tutorial and not self.dave.done:
            return

        # recharge cards
        for k in self.recharge_timers:
            self.recharge_timers[k] = max(0, self.recharge_timers[k] - dt)

        # sun spawns
        if random.random() < 0.008:
            x = random.randint(LAWN_X + 50, SPAWN_X - 50)
            self.suns.append(Sun(x, LAWN_Y, True))

        # zombie waves
        self.spawn_timer += dt
        if self.zombies_this_wave < self.wave * 4 and self.spawn_timer > self.spawn_delay:
            self.spawn_timer = 0
            ztype = random.choice(list(ZOMBIE_DATA.keys()))
            row = random.randint(0, 4)
            self.zombies.append(Zombie(ztype, row))
            self.zombies_this_wave += 1
        elif self.zombies_this_wave >= self.wave * 4 and not any(not z.dead for z in self.zombies):
            if self.wave >= self.total_waves:
                self.victory = True
            else:
                self.wave += 1
                self.zombies_this_wave = 0
                self.spawn_delay = max(3.0, self.spawn_delay - 1.0)

        # entities
        for p in self.plants[:]:
            if p.dead:
                self.remove_plant(p)
            else:
                p.update(dt, self)
                
        for z in self.zombies[:]:
            z.update(dt, self)
            if z.dead:
                self.zombies.remove(z)
                
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
            
            # Check if zombie reached mower
            if not m.active:
                for z in self.zombies:
                    if z.row == m.row and z.x < m.x + 60 and not z.dead:
                        m.active = True
                        break

    # --- Draw --------------------------------------------------------------
    def draw_lawn(self, surf):
        pygame.draw.rect(surf, (139, 90, 43), (0, LAWN_Y, HOUSE_W, HEIGHT - LAWN_Y))
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                x = LAWN_X + c * CELL_W
                y = LAWN_Y + r * CELL_H
                color = LAWN_GREEN if (r + c) % 2 == 0 else LAWN_DARK
                pygame.draw.rect(surf, color, (x, y, CELL_W, CELL_H))
                pygame.draw.rect(surf, BLACK, (x, y, CELL_W, CELL_H), 1)
        pygame.draw.line(surf, BLACK, (SPAWN_X, LAWN_Y), (SPAWN_X, HEIGHT), 3)

    def draw_ui(self, surf):
        pygame.draw.rect(surf, (220, 220, 220), (0, 0, WIDTH, UI_HEIGHT))
        pygame.draw.line(surf, BLACK, (0, UI_HEIGHT), (WIDTH, UI_HEIGHT), 2)
        # sun counter
        pygame.draw.rect(surf, (255, 220, 150), (10, 10, 80, 60), border_radius=10)
        pygame.draw.rect(surf, BLACK, (10, 10, 80, 60), 2, border_radius=10)
        surf.blit(SUN_SURF, (20, 20))
        sun_txt = FONT_BIG.render(str(int(self.sun_count)), True, BLACK)
        surf.blit(sun_txt, (100, 25))
        # cards
        x = 180
        for name in PLANT_DATA:
            card = CARD_SURFS[name].copy()
            t = self.recharge_timers[name]
            maxt = PLANT_DATA[name]["recharge"]
            affordable = self.sun_count >= PLANT_DATA[name]["cost"]
            if t > 0 or not affordable:
                overlay = pygame.Surface((65, 85), SRCALPHA)
                overlay.fill((0, 0, 0, 150))
                card.blit(overlay, (0, 0))
            if self.selected == name:
                pygame.draw.rect(card, ORANGE, (0, 0, 65, 85), 4, border_radius=8)
            surf.blit(card, (x, 5))
            if t > 0:
                h = int((t / maxt) * 85)
                cover = pygame.Surface((65, h), SRCALPHA)
                cover.fill((0, 0, 0, 180))
                surf.blit(cover, (x, 5 + 85 - h))
            x += 75

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
            txt = FONT_BIG.render("GAME OVER!", True, RED)
            surf.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2))
        if self.victory:
            txt = FONT_BIG.render("YOU WIN!", True, GREEN)
            surf.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2))

# === MAIN GAME LOOP =======================================================
def main():
    load_surfaces()
    intro = Intro()
    menu = MainMenu()
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
                res = menu.handle(e)
                if res == "adventure":
                    world = World()
                    state = "game"
                elif res == "quit":
                    running = False
            elif state == "game" and world:
                if e.type == KEYDOWN and e.key == K_ESCAPE:
                    state = "menu"
                elif e.type == KEYDOWN and e.key == K_SPACE and world.tutorial and not world.dave.done:
                    world.dave.next()
                elif e.type == MOUSEBUTTONDOWN and not world.game_over and not world.victory:
                    mx, my = e.pos
                    # Sun collection
                    for s in world.suns[:]:
                        if s.hit(mx, my):
                            world.sun_count += 25
                            world.suns.remove(s)
                            break
                    # Seed selection
                    if my < UI_HEIGHT:
                        x = 180
                        for name in PLANT_DATA:
                            rect = pygame.Rect(x, 5, 65, 85)
                            if rect.collidepoint(mx, my):
                                if world.recharge_timers[name] <= 0 and world.sun_count >= PLANT_DATA[name]["cost"]:
                                    world.selected = name
                            x += 75
                    else:
                        cell = cell_at(mx, my)
                        if cell and world.selected:
                            col, row = cell
                            if not world.plant_at(col, row):
                                world.add_plant(world.selected, col, row)
                                world.selected = None
            # Intro skip
            elif state == "intro" and e.type in (KEYDOWN, MOUSEBUTTONDOWN):
                intro.state = "done"

        # --- Update per state ---
        if state == "intro":
            intro.update(dt)
            if intro.state == "done":
                state = "menu"

        elif state == "game" and world:
            world.update(dt)

        # --- Draw per state ---
        if state == "intro":
            screen.fill(BLACK)
            intro.draw(screen)

        elif state == "menu":
            menu.draw(screen)

        elif state == "game" and world:
            world.draw_game(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

# === ENTRYPOINT ===========================================================
if __name__ == "__main__":
    main()