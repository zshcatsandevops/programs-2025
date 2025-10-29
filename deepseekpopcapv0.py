#!/usr/bin/env python3
import pygame
import sys
import random
import math
from pygame.locals import *
from enum import Enum

pygame.init()
pygame.mixer.init()

# === CONFIG ===
WIDTH, HEIGHT = 1024, 768
FPS = 60
GRID_X, GRID_Y = 100, 120
CELL_W, CELL_H = 80, 100
ROWS, COLS = 5, 9
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Plants vs. Zombies - Complete Edition")
clock = pygame.time.Clock()

# === COLORS ===
SKY_BLUE = (135, 206, 235)
GRASS_GREEN = (34, 139, 34)
BROWN = (139, 69, 19)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
ZOMBIE_GREEN = (150, 200, 150)
SUN_YELLOW = (255, 215, 0)
PLANT_GREEN = (100, 200, 100)
MENU_GREEN = (50, 150, 50)
MENU_HIGHLIGHT = (100, 255, 100)
POPCAP_BLUE = (0, 100, 200)
EA_RED = (200, 0, 0)

# === ENUMS ===
class PlantType(Enum):
    PEASHOOTER = "Peashooter"
    SUNFLOWER = "Sunflower"
    WALLNUT = "Wall-nut"
    CHERRYBOMB = "Cherry Bomb"
    SNOWPEA = "Snow Pea"
    POTATOMINE = "Potato Mine"
    REPEATER = "Repeater"

class ZombieType(Enum):
    BASIC = "Zombie"
    CONEHEAD = "Conehead"
    BUCKETHEAD = "Buckethead"
    POLEVAULT = "Pole Vaulting"
    FOOTBALL = "Football"

class GameState(Enum):
    INTRO = 0
    MAIN_MENU = 1
    PLAYING = 2
    PAUSED = 3
    GAME_OVER = 4

# === INTRO SEQUENCES ===
class IntroSequence:
    def __init__(self):
        self.state = GameState.INTRO
        self.current_intro = 0  # 0=PopCap, 1=EA, 2=Main Menu
        self.intro_timer = 0
        self.intro_duration = 3000  # 3 seconds per intro
        
    def update(self):
        self.intro_timer += 1000 / FPS
        if self.intro_timer >= self.intro_duration:
            self.current_intro += 1
            self.intro_timer = 0
            if self.current_intro >= 2:  # After EA intro, go to main menu
                return GameState.MAIN_MENU
        return GameState.INTRO
        
    def draw(self, surface):
        if self.current_intro == 0:  # PopCap intro
            surface.fill(POPCAP_BLUE)
            font_large = pygame.font.Font(None, 120)
            font_small = pygame.font.Font(None, 48)
            
            popcap_text = font_large.render("POPCAP", True, WHITE)
            games_text = font_small.render("GAMES", True, WHITE)
            presents_text = font_small.render("presents", True, WHITE)
            
            surface.blit(popcap_text, (WIDTH//2 - popcap_text.get_width()//2, HEIGHT//2 - 100))
            surface.blit(games_text, (WIDTH//2 - games_text.get_width()//2, HEIGHT//2 + 20))
            surface.blit(presents_text, (WIDTH//2 - presents_text.get_width()//2, HEIGHT//2 + 100))
            
        elif self.current_intro == 1:  # EA intro
            surface.fill(BLACK)
            font_large = pygame.font.Font(None, 150)
            font_small = pygame.font.Font(None, 36)
            
            ea_text = font_large.render("EA", True, EA_RED)
            games_text = font_small.render("ELECTRONIC ARTS", True, WHITE)
            partner_text = font_small.render("In partnership with", True, WHITE)
            
            surface.blit(partner_text, (WIDTH//2 - partner_text.get_width()//2, HEIGHT//2 - 100))
            surface.blit(ea_text, (WIDTH//2 - ea_text.get_width()//2, HEIGHT//2 - 20))
            surface.blit(games_text, (WIDTH//2 - games_text.get_width()//2, HEIGHT//2 + 100))

class MainMenu:
    def __init__(self):
        self.state = GameState.MAIN_MENU
        self.buttons = [
            {"text": "ADVENTURE", "action": "start_game", "rect": pygame.Rect(0, 0, 300, 60)},
            {"text": "SURVIVAL", "action": "survival", "rect": pygame.Rect(0, 0, 300, 60)},
            {"text": "PUZZLE", "action": "puzzle", "rect": pygame.Rect(0, 0, 300, 60)},
            {"text": "OPTIONS", "action": "options", "rect": pygame.Rect(0, 0, 300, 60)},
            {"text": "QUIT", "action": "quit", "rect": pygame.Rect(0, 0, 300, 60)}
        ]
        self.selected_button = None
        self.background_offset = 0
        self.zombies = []
        self.plants = []
        self.init_animated_background()
        
    def init_animated_background(self):
        # Create some decorative zombies and plants for the menu background
        for i in range(3):
            self.zombies.append({
                "x": WIDTH + random.randint(0, 300),
                "y": 200 + i * 150,
                "speed": random.uniform(0.2, 0.5),
                "type": random.choice([ZombieType.BASIC, ZombieType.CONEHEAD, ZombieType.BUCKETHEAD])
            })
            
        for i in range(5):
            self.plants.append({
                "x": 100 + i * 180,
                "y": 500,
                "type": random.choice([PlantType.SUNFLOWER, PlantType.PEASHOOTER, PlantType.WALLNUT])
            })
        
    def update(self):
        # Animate background
        self.background_offset = (self.background_offset + 0.5) % 100
        
        # Update zombie positions
        for zombie in self.zombies:
            zombie["x"] -= zombie["speed"]
            if zombie["x"] < -100:
                zombie["x"] = WIDTH + 100
                zombie["y"] = 200 + random.randint(0, 3) * 150
                
    def handle_click(self, pos):
        for i, button in enumerate(self.buttons):
            if button["rect"].collidepoint(pos):
                return button["action"]
        return None
        
    def draw(self, surface):
        # Draw animated background
        self.draw_animated_background(surface)
        
        # Draw title
        font_title = pygame.font.Font(None, 120)
        font_subtitle = pygame.font.Font(None, 36)
        
        title_text = font_title.render("PLANTS vs ZOMBIES", True, MENU_GREEN)
        subtitle_text = font_subtitle.render("Defend Your Lawn!", True, WHITE)
        
        # Title background effect
        title_bg = pygame.Surface((title_text.get_width() + 40, title_text.get_height() + 20), pygame.SRCALPHA)
        title_bg.fill((0, 0, 0, 128))
        surface.blit(title_bg, (WIDTH//2 - title_bg.get_width()//2, 80))
        
        surface.blit(title_text, (WIDTH//2 - title_text.get_width()//2, 100))
        surface.blit(subtitle_text, (WIDTH//2 - subtitle_text.get_width()//2, 220))
        
        # Draw buttons
        button_y = 300
        for i, button in enumerate(self.buttons):
            button["rect"].x = WIDTH//2 - 150
            button["rect"].y = button_y
            button_y += 80
            
            # Button background
            color = MENU_HIGHLIGHT if button["rect"].collidepoint(pygame.mouse.get_pos()) else MENU_GREEN
            pygame.draw.rect(surface, color, button["rect"], border_radius=15)
            pygame.draw.rect(surface, WHITE, button["rect"], 3, border_radius=15)
            
            # Button text
            font_button = pygame.font.Font(None, 48)
            text = font_button.render(button["text"], True, WHITE)
            surface.blit(text, (button["rect"].centerx - text.get_width()//2, 
                              button["rect"].centery - text.get_height()//2))
        
        # Draw footer
        font_footer = pygame.font.Font(None, 24)
        footer_text = font_footer.render("© 2024 PopCap Games, Inc. Electronic Arts Inc.", True, WHITE)
        surface.blit(footer_text, (WIDTH//2 - footer_text.get_width()//2, HEIGHT - 50))
        
    def draw_animated_background(self, surface):
        # Draw sky gradient
        for y in range(HEIGHT):
            shade = max(100, 235 - y // 8)
            color = (135, 206, shade)
            pygame.draw.line(surface, color, (0, y), (WIDTH, y))
        
        # Draw grass with parallax effect
        for i in range(20):
            x = (i * 100 + self.background_offset) % (WIDTH + 100) - 50
            pygame.draw.rect(surface, GRASS_GREEN, (x, 450, 100, HEIGHT - 450))
        
        # Draw decorative plants
        for plant in self.plants:
            color = PLANT_GREEN
            if plant["type"] == PlantType.SUNFLOWER:
                color = SUN_YELLOW
            elif plant["type"] == PlantType.WALLNUT:
                color = BROWN
                
            pygame.draw.circle(surface, color, (int(plant["x"]), int(plant["y"])), 25)
        
        # Draw decorative zombies
        for zombie in self.zombies:
            color = ZOMBIE_GREEN
            if zombie["type"] == ZombieType.CONEHEAD:
                color = (200, 200, 100)
            elif zombie["type"] == ZombieType.BUCKETHEAD:
                color = (150, 150, 150)
                
            pygame.draw.rect(surface, color, (zombie["x"] - 25, zombie["y"] - 40, 50, 80))
            pygame.draw.circle(surface, ZOMBIE_GREEN, (int(zombie["x"]), int(zombie["y"] - 40)), 20)

# === CORE GAME ENGINE CLASSES ===
class Sun:
    def __init__(self, x, y, value=25):
        self.x = x
        self.y = y
        self.target_y = y + random.randint(50, 200)
        self.value = value
        self.speed = 1
        self.collected = False
        self.timer = 10000  # 10 seconds
        self.created_time = pygame.time.get_ticks()
        
    def update(self):
        if self.y < self.target_y:
            self.y += self.speed
            
        # Remove if expired
        if pygame.time.get_ticks() - self.created_time > self.timer:
            return True
        return False
            
    def draw(self, surface):
        pygame.draw.circle(surface, SUN_YELLOW, (int(self.x), int(self.y)), 20)
        pygame.draw.circle(surface, YELLOW, (int(self.x), int(self.y)), 15)
        
    def is_clicked(self, pos):
        distance = math.sqrt((pos[0] - self.x)**2 + (pos[1] - self.y)**2)
        return distance <= 20

class Projectile:
    def __init__(self, x, y, damage=20, slow=False):
        self.x = x
        self.y = y
        self.speed = 10
        self.damage = damage
        self.slow = slow
        self.active = True
        
    def update(self):
        self.x += self.speed
        if self.x > WIDTH:
            self.active = False
            
    def draw(self, surface):
        color = (0, 100, 255) if self.slow else (200, 200, 100)
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), 8)

class Plant:
    def __init__(self, plant_type, row, col):
        self.type = plant_type
        self.row = row
        self.col = col
        self.x = GRID_X + col * CELL_W + CELL_W // 2
        self.y = GRID_Y + row * CELL_H + CELL_H // 2
        self.health = 300
        self.attack_cooldown = 0
        self.sun_cooldown = 0
        
        # Stats based on type
        self.set_stats()
        
    def set_stats(self):
        stats = {
            PlantType.PEASHOOTER: {"health": 300, "cost": 100, "reload": 1.5, "damage": 20},
            PlantType.SUNFLOWER: {"health": 300, "cost": 50, "reload": 24, "sun": 25},
            PlantType.WALLNUT: {"health": 4000, "cost": 50, "reload": 30},
            PlantType.CHERRYBOMB: {"health": 300, "cost": 150, "reload": 50, "damage": 1800},
            PlantType.SNOWPEA: {"health": 300, "cost": 175, "reload": 1.5, "damage": 20, "slow": True},
            PlantType.POTATOMINE: {"health": 300, "cost": 25, "reload": 20, "damage": 1800, "armed": False},
            PlantType.REPEATER: {"health": 300, "cost": 200, "reload": 1.5, "damage": 40}
        }
        
        self.stats = stats.get(self.type, {})
        self.health = self.stats.get("health", 300)
        self.cost = self.stats.get("cost", 0)
        self.reload_time = self.stats.get("reload", 0)
        self.damage = self.stats.get("damage", 0)
        self.sun_production = self.stats.get("sun", 0)
        self.slow_effect = self.stats.get("slow", False)
        self.armed = self.stats.get("armed", True)
        
        if self.type == PlantType.POTATOMINE:
            self.armed = False
            self.arm_time = pygame.time.get_ticks()
            
    def update(self, game):
        current_time = pygame.time.get_ticks()
        
        # Handle potato mine arming
        if self.type == PlantType.POTATOMINE and not self.armed:
            if current_time - self.arm_time > 4000:  # 4 seconds to arm
                self.armed = True
            return
                
        # Sun production
        if self.type == PlantType.SUNFLOWER:
            if self.sun_cooldown <= 0:
                game.suns.append(Sun(self.x + random.randint(-20, 20), self.y - 30, self.sun_production))
                self.sun_cooldown = self.reload_time * 1000  # Convert to milliseconds
            else:
                self.sun_cooldown -= 1000 / FPS
                
        # Attack cooldown
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1000 / FPS
            
    def can_attack(self):
        return (self.attack_cooldown <= 0 and 
                self.type in [PlantType.PEASHOOTER, PlantType.SNOWPEA, PlantType.REPEATER])
                
    def attack(self, game):
        if self.can_attack():
            projectile = Projectile(self.x + 20, self.y, self.damage, self.slow_effect)
            game.projectiles.append(projectile)
            
            if self.type == PlantType.REPEATER:
                # Second pea for repeater
                projectile2 = Projectile(self.x + 10, self.y, self.damage, self.slow_effect)
                game.projectiles.append(projectile2)
                
            self.attack_cooldown = self.reload_time * 1000
            return True
        return False
        
    def draw(self, surface):
        # Base plant circle
        color = PLANT_GREEN
        if self.type == PlantType.WALLNUT:
            color = BROWN
        elif self.type == PlantType.SUNFLOWER:
            color = SUN_YELLOW
        elif self.type == PlantType.CHERRYBOMB:
            color = RED
        elif self.type == PlantType.SNOWPEA:
            color = (200, 200, 255)
        elif self.type == PlantType.POTATOMINE:
            color = (100, 100, 100) if not self.armed else (150, 75, 0)
            
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), 25)
        
        # Plant-specific details
        if self.type == PlantType.PEASHOOTER or self.type == PlantType.SNOWPEA or self.type == PlantType.REPEATER:
            # Draw shooter mouth
            pygame.draw.circle(surface, BLACK, (int(self.x + 15), int(self.y)), 8)
        elif self.type == PlantType.SUNFLOWER:
            # Draw sunflower face
            pygame.draw.circle(surface, (200, 150, 0), (int(self.x), int(self.y)), 15)
        elif self.type == PlantType.WALLNUT:
            # Draw nut texture
            pygame.draw.circle(surface, (100, 50, 0), (int(self.x), int(self.y)), 20)
            
        # Health bar
        health_percent = self.health / self.stats.get("health", 300)
        bar_width = 40
        bar_height = 5
        pygame.draw.rect(surface, RED, (self.x - bar_width//2, self.y - 40, bar_width, bar_height))
        pygame.draw.rect(surface, GREEN, (self.x - bar_width//2, self.y - 40, bar_width * health_percent, bar_height))

class Zombie:
    def __init__(self, zombie_type, row):
        self.type = zombie_type
        self.row = row
        self.x = WIDTH + 50
        self.y = GRID_Y + row * CELL_H + CELL_H // 2
        self.set_stats()
        self.health = self.max_health
        self.slow_timer = 0
        self.eating = False
        self.eating_plant = None
        self.eat_cooldown = 0
        
    def set_stats(self):
        stats = {
            ZombieType.BASIC: {"health": 100, "speed": 0.5, "damage": 1},
            ZombieType.CONEHEAD: {"health": 260, "speed": 0.5, "damage": 1},
            ZombieType.BUCKETHEAD: {"health": 1100, "speed": 0.5, "damage": 1},
            ZombieType.POLEVAULT: {"health": 200, "speed": 1.8, "damage": 1, "can_jump": True},
            ZombieType.FOOTBALL: {"health": 270, "speed": 1.2, "damage": 1}
        }
        
        self.stats = stats.get(self.type, {})
        self.max_health = self.stats.get("health", 100)
        self.speed = self.stats.get("speed", 0.5)
        self.damage = self.stats.get("damage", 1)
        self.can_jump = self.stats.get("can_jump", False)
        self.has_jumped = False
        
    def update(self, game):
        # Handle slow effect
        if self.slow_timer > 0:
            self.slow_timer -= 1000 / FPS
            current_speed = self.speed * 0.5
        else:
            current_speed = self.speed
            
        if self.eating:
            if self.eat_cooldown <= 0:
                if self.eating_plant and self.eating_plant.health > 0:
                    self.eating_plant.health -= self.damage
                    self.eat_cooldown = 1000  # 1 second between bites
                else:
                    self.eating = False
                    self.eating_plant = None
            else:
                self.eat_cooldown -= 1000 / FPS
        else:
            self.x -= current_speed
            
        # Check if zombie reached house
        if self.x < GRID_X:
            game.game_over = True
            
    def start_eating(self, plant):
        self.eating = True
        self.eating_plant = plant
        
    def take_damage(self, damage, slow=False):
        self.health -= damage
        if slow:
            self.slow_timer = 2000  # 2 seconds slow
            
    def draw(self, surface):
        # Base zombie body
        color = ZOMBIE_GREEN
        if self.type == ZombieType.CONEHEAD:
            color = (200, 200, 100)  # Cone color
        elif self.type == ZombieType.BUCKETHEAD:
            color = (150, 150, 150)  # Bucket color
        elif self.type == ZombieType.FOOTBALL:
            color = (200, 100, 100)  # Football uniform
            
        pygame.draw.rect(surface, color, (self.x - 25, self.y - 40, 50, 80))
        
        # Zombie head
        head_color = ZOMBIE_GREEN
        pygame.draw.circle(surface, head_color, (int(self.x), int(self.y - 40)), 20)
        
        # Health bar
        health_percent = self.health / self.max_health
        bar_width = 40
        bar_height = 5
        pygame.draw.rect(surface, RED, (self.x - bar_width//2, self.y - 60, bar_width, bar_height))
        pygame.draw.rect(surface, GREEN, (self.x - bar_width//2, self.y - 60, bar_width * health_percent, bar_height))
        
        # Slow effect visualization
        if self.slow_timer > 0:
            pygame.draw.circle(surface, (0, 100, 255), (int(self.x), int(self.y - 50)), 8)

class Game:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.plants = []
        self.zombies = []
        self.projectiles = []
        self.suns = []
        self.sun_count = 50
        self.selected_plant = None
        self.wave_timer = 0
        self.zombies_killed = 0
        self.zombies_spawned = 0
        self.wave_number = 0
        self.game_over = False
        self.lawn_mowers = [LawnMower(row) for row in range(ROWS)]
        self.state = GameState.PLAYING
        
    def update(self):
        if self.game_over or self.state != GameState.PLAYING:
            return
            
        # Update plants
        for plant in self.plants[:]:
            plant.update(self)
            if plant.health <= 0:
                self.plants.remove(plant)
                
        # Update projectiles
        for projectile in self.projectiles[:]:
            projectile.update()
            if not projectile.active:
                self.projectiles.remove(projectile)
                
        # Update zombies
        for zombie in self.zombies[:]:
            zombie.update(self)
            
            # Check if zombie needs to eat plant
            if not zombie.eating:
                for plant in self.plants:
                    if (plant.row == zombie.row and 
                        abs(plant.x - zombie.x) < 30 and
                        plant.health > 0):
                        zombie.start_eating(plant)
                        break
                        
            # Check if zombie died
            if zombie.health <= 0:
                self.zombies.remove(zombie)
                self.zombies_killed += 1
                
        # Update suns
        for sun in self.suns[:]:
            if sun.update():
                self.suns.remove(sun)
                
        # Check projectile collisions
        for projectile in self.projectiles[:]:
            for zombie in self.zombies:
                if (abs(projectile.x - zombie.x) < 30 and 
                    abs(projectile.y - zombie.y) < 40):
                    zombie.take_damage(projectile.damage, projectile.slow)
                    if projectile in self.projectiles:
                        self.projectiles.remove(projectile)
                    break
                    
        # Auto generate sun
        if random.random() < 0.001:  # 0.1% chance per frame
            self.suns.append(Sun(random.randint(GRID_X, GRID_X + COLS * CELL_W), GRID_Y - 50))
            
        # Spawn zombies
        self.wave_timer += 1000 / FPS
        if self.wave_timer > 10000:  # Every 10 seconds
            self.spawn_zombie_wave()
            self.wave_timer = 0
            
        # Auto plant shooting
        for plant in self.plants:
            if plant.can_attack():
                # Check if there's a zombie in the same row
                for zombie in self.zombies:
                    if zombie.row == plant.row and zombie.x > plant.x:
                        plant.attack(self)
                        break
                        
        # Check lawn mowers
        for mower in self.lawn_mowers:
            mower.update(self)
            
    def spawn_zombie_wave(self):
        self.wave_number += 1
        zombies_to_spawn = min(2 + self.wave_number // 2, 8)
        
        for _ in range(zombies_to_spawn):
            row = random.randint(0, ROWS - 1)
            zombie_type = random.choice([
                ZombieType.BASIC, 
                ZombieType.CONEHEAD,
                ZombieType.BUCKETHEAD
            ])
            
            # Increase difficulty with waves
            if self.wave_number > 3 and random.random() < 0.3:
                zombie_type = ZombieType.POLEVAULT
            if self.wave_number > 5 and random.random() < 0.2:
                zombie_type = ZombieType.FOOTBALL
                
            self.zombies.append(Zombie(zombie_type, row))
            self.zombies_spawned += 1
            
    def add_plant(self, plant_type, row, col):
        # Check if cell is empty
        for plant in self.plants:
            if plant.row == row and plant.col == col:
                return False
                
        plant = Plant(plant_type, row, col)
        if self.sun_count >= plant.cost:
            self.plants.append(plant)
            self.sun_count -= plant.cost
            return True
        return False
        
    def collect_sun(self, sun):
        self.sun_count += sun.value
        self.suns.remove(sun)
        
    def get_cell_from_pos(self, pos):
        x, y = pos
        if (GRID_X <= x < GRID_X + COLS * CELL_W and 
            GRID_Y <= y < GRID_Y + ROWS * CELL_H):
            col = (x - GRID_X) // CELL_W
            row = (y - GRID_Y) // CELL_H
            return row, col
        return None, None

class LawnMower:
    def __init__(self, row):
        self.row = row
        self.x = GRID_X - 30
        self.y = GRID_Y + row * CELL_H + CELL_H // 2
        self.active = False
        self.speed = 5
        
    def update(self, game):
        if self.active:
            self.x += self.speed
            # Check collision with zombies
            for zombie in game.zombies[:]:
                if (zombie.row == self.row and 
                    abs(zombie.x - self.x) < 40):
                    zombie.health = 0  # Instant kill
                    
            # Deactivate if off screen
            if self.x > WIDTH:
                self.active = False
                
    def activate(self):
        self.active = True
        
    def draw(self, surface):
        color = (200, 0, 0) if self.active else (100, 100, 100)
        pygame.draw.rect(surface, color, (self.x - 15, self.y - 20, 30, 40))

class PlantSelector:
    def __init__(self):
        self.plants = [
            PlantType.PEASHOOTER,
            PlantType.SUNFLOWER, 
            PlantType.WALLNUT,
            PlantType.CHERRYBOMB,
            PlantType.SNOWPEA,
            PlantType.POTATOMINE,
            PlantType.REPEATER
        ]
        self.x = 50
        self.y = 50
        self.cell_size = 60
        self.spacing = 10
        
    def draw(self, surface, sun_count, selected_plant=None):
        for i, plant_type in enumerate(self.plants):
            x = self.x
            y = self.y + i * (self.cell_size + self.spacing)
            
            # Background
            color = (200, 200, 200)
            if selected_plant == plant_type:
                color = (255, 255, 100)
                
            pygame.draw.rect(surface, color, (x, y, self.cell_size, self.cell_size))
            pygame.draw.rect(surface, BLACK, (x, y, self.cell_size, self.cell_size), 2)
            
            # Plant icon
            plant_color = PLANT_GREEN
            if plant_type == PlantType.SUNFLOWER:
                plant_color = SUN_YELLOW
            elif plant_type == PlantType.WALLNUT:
                plant_color = BROWN
            elif plant_type == PlantType.CHERRYBOMB:
                plant_color = RED
                
            pygame.draw.circle(surface, plant_color, 
                             (x + self.cell_size // 2, y + self.cell_size // 2), 
                             20)
            
            # Cost
            cost = Plant(plant_type, 0, 0).cost
            font = pygame.font.Font(None, 24)
            cost_text = font.render(str(cost), True, BLACK)
            surface.blit(cost_text, (x + 5, y + 5))
            
            # Grey out if can't afford
            if sun_count < cost:
                s = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
                s.fill((100, 100, 100, 128))
                surface.blit(s, (x, y))
                
    def get_plant_at_pos(self, pos):
        x, y = pos
        for i, plant_type in enumerate(self.plants):
            rect_x = self.x
            rect_y = self.y + i * (self.cell_size + self.spacing)
            if (rect_x <= x <= rect_x + self.cell_size and 
                rect_y <= y <= rect_y + self.cell_size):
                return plant_type
        return None

# === MAIN GAME LOOP ===
def main():
    game_state = GameState.INTRO
    intro = IntroSequence()
    main_menu = MainMenu()
    game = Game()
    plant_selector = PlantSelector()
    
    # Main game loop
    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
                
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    pos = pygame.mouse.get_pos()
                    
                    if game_state == GameState.INTRO:
                        # Skip intro on click
                        game_state = GameState.MAIN_MENU
                        
                    elif game_state == GameState.MAIN_MENU:
                        action = main_menu.handle_click(pos)
                        if action == "start_game":
                            game_state = GameState.PLAYING
                        elif action == "quit":
                            running = False
                            
                    elif game_state == GameState.PLAYING:
                        # Check plant selector
                        selected_plant = plant_selector.get_plant_at_pos(pos)
                        if selected_plant:
                            game.selected_plant = selected_plant
                        else:
                            # Check sun collection
                            for sun in game.suns[:]:
                                if sun.is_clicked(pos):
                                    game.collect_sun(sun)
                                    break
                            else:
                                # Plant placement
                                row, col = game.get_cell_from_pos(pos)
                                if row is not None and game.selected_plant:
                                    game.add_plant(game.selected_plant, row, col)
                                
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    if game_state == GameState.PLAYING:
                        game.selected_plant = None
                    elif game_state == GameState.MAIN_MENU:
                        running = False
                elif event.key == K_r and game_state == GameState.PLAYING:
                    game.reset()
                elif event.key == K_m:  # Return to menu
                    game_state = GameState.MAIN_MENU
                    game.reset()
                    
        # Update game state
        if game_state == GameState.INTRO:
            new_state = intro.update()
            if new_state != GameState.INTRO:
                game_state = new_state
                
        elif game_state == GameState.MAIN_MENU:
            main_menu.update()
            
        elif game_state == GameState.PLAYING:
            game.update()
        
        # Draw everything based on state
        if game_state == GameState.INTRO:
            intro.draw(screen)
            
        elif game_state == GameState.MAIN_MENU:
            main_menu.draw(screen)
            
        elif game_state == GameState.PLAYING:
            screen.fill(SKY_BLUE)
            
            # Draw grid
            for row in range(ROWS):
                for col in range(COLS):
                    rect = pygame.Rect(
                        GRID_X + col * CELL_W,
                        GRID_Y + row * CELL_H,
                        CELL_W, CELL_H
                    )
                    pygame.draw.rect(screen, GRASS_GREEN, rect)
                    pygame.draw.rect(screen, BLACK, rect, 1)
                    
            # Draw lawn mowers
            for mower in game.lawn_mowers:
                mower.draw(screen)
                    
            # Draw plants
            for plant in game.plants:
                plant.draw(screen)
                
            # Draw zombies
            for zombie in game.zombies:
                zombie.draw(screen)
                
            # Draw projectiles
            for projectile in game.projectiles:
                projectile.draw(screen)
                
            # Draw suns
            for sun in game.suns:
                sun.draw(screen)
                
            # Draw plant selector
            plant_selector.draw(screen, game.sun_count, game.selected_plant)
            
            # Draw HUD
            font = pygame.font.Font(None, 36)
            sun_text = font.render(f"Sun: {game.sun_count}", True, BLACK)
            wave_text = font.render(f"Wave: {game.wave_number}", True, BLACK)
            kills_text = font.render(f"Zombies Killed: {game.zombies_killed}", True, BLACK)
            menu_text = font.render("Press M for Menu", True, BLACK)
            
            screen.blit(sun_text, (WIDTH - 200, 20))
            screen.blit(wave_text, (WIDTH - 200, 60))
            screen.blit(kills_text, (WIDTH - 200, 100))
            screen.blit(menu_text, (WIDTH - 200, 140))
            
            # Game over screen
            if game.game_over:
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 128))
                screen.blit(overlay, (0, 0))
                
                font_large = pygame.font.Font(None, 72)
                game_over_text = font_large.render("GAME OVER", True, RED)
                restart_text = font.render("Press R to restart or M for Menu", True, WHITE)
                
                screen.blit(game_over_text, (WIDTH//2 - 150, HEIGHT//2 - 50))
                screen.blit(restart_text, (WIDTH//2 - 180, HEIGHT//2 + 50))
            
        pygame.display.flip()
        clock.tick(FPS)
        
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
