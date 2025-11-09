#!/usr/bin/env python3
"""
Plants vs Zombies PopCap Style v1.0
Full tower defense game with authentic mechanics
60 FPS @ 600x400 resolution
Single-file implementation
"""

import pygame
import random
import math
import sys
from enum import Enum
from typing import List, Tuple, Optional

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400
FPS = 60
GRID_ROWS = 5
GRID_COLS = 9
CELL_WIDTH = 60
CELL_HEIGHT = 70
GRID_START_X = 60
GRID_START_Y = 80

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (34, 139, 34)
DARK_GREEN = (0, 100, 0)
BROWN = (139, 69, 19)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 100, 255)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)

class PlantType(Enum):
    PEASHOOTER = 1
    SUNFLOWER = 2
    WALLNUT = 3
    SNOWPEA = 4
    REPEATER = 5
    CHOMPER = 6

class ZombieType(Enum):
    NORMAL = 1
    CONE = 2
    BUCKET = 3
    FOOTBALL = 4

class GameState(Enum):
    MENU = 1
    PLAYING = 2
    PAUSED = 3
    GAME_OVER = 4
    VICTORY = 5

class Projectile:
    def __init__(self, x, y, damage=20, speed=3, frozen=False):
        self.x = x
        self.y = y
        self.damage = damage
        self.speed = speed
        self.frozen = frozen
        self.radius = 4
        self.active = True
        
    def update(self):
        self.x += self.speed
        if self.x > SCREEN_WIDTH:
            self.active = False
            
    def draw(self, screen):
        color = BLUE if self.frozen else GREEN
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, BLACK, (int(self.x), int(self.y)), self.radius, 1)
        
    def check_collision(self, zombie):
        dist = math.sqrt((self.x - zombie.x)**2 + (self.y - zombie.y)**2)
        return dist < self.radius + 15

class Sun:
    def __init__(self, x, y, falling=True):
        self.x = x
        self.y = y
        self.target_y = random.randint(150, 350) if falling else y
        self.falling = falling
        self.lifetime = 600 if not falling else 1000
        self.collected = False
        self.radius = 15
        self.bounce = 0
        
    def update(self):
        if self.falling and self.y < self.target_y:
            self.y += 1
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.collected = True
        self.bounce += 0.1
            
    def draw(self, screen):
        if not self.collected:
            bounce_offset = math.sin(self.bounce) * 2
            pygame.draw.circle(screen, YELLOW, 
                             (int(self.x), int(self.y + bounce_offset)), self.radius)
            pygame.draw.circle(screen, ORANGE, 
                             (int(self.x), int(self.y + bounce_offset)), self.radius, 2)
            # Draw sun rays
            for i in range(8):
                angle = i * math.pi / 4
                x1 = self.x + math.cos(angle) * self.radius
                y1 = self.y + bounce_offset + math.sin(angle) * self.radius
                x2 = self.x + math.cos(angle) * (self.radius + 5)
                y2 = self.y + bounce_offset + math.sin(angle) * (self.radius + 5)
                pygame.draw.line(screen, YELLOW, (x1, y1), (x2, y2), 2)
                
    def check_click(self, mx, my):
        if self.collected:
            return False
        dist = math.sqrt((mx - self.x)**2 + (my - self.y)**2)
        if dist < self.radius + 10:
            self.collected = True
            return True
        return False

class Plant:
    def __init__(self, plant_type, row, col):
        self.type = plant_type
        self.row = row
        self.col = col
        self.x = GRID_START_X + col * CELL_WIDTH + CELL_WIDTH // 2
        self.y = GRID_START_Y + row * CELL_HEIGHT + CELL_HEIGHT // 2
        self.health = self.get_max_health()
        self.shoot_cooldown = 0
        self.sun_cooldown = 0
        self.animation_frame = 0
        
    def get_max_health(self):
        health_map = {
            PlantType.PEASHOOTER: 100,
            PlantType.SUNFLOWER: 100,
            PlantType.WALLNUT: 300,
            PlantType.SNOWPEA: 100,
            PlantType.REPEATER: 100,
            PlantType.CHOMPER: 150
        }
        return health_map.get(self.type, 100)
        
    def get_shoot_rate(self):
        rate_map = {
            PlantType.PEASHOOTER: 90,
            PlantType.SNOWPEA: 90,
            PlantType.REPEATER: 45,
            PlantType.CHOMPER: 180
        }
        return rate_map.get(self.type, 0)
        
    def update(self, zombies, projectiles, suns):
        self.animation_frame += 0.1
        
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
            
        if self.sun_cooldown > 0:
            self.sun_cooldown -= 1
            
        # Check if any zombie in same row
        zombies_in_row = [z for z in zombies if z.row == self.row and z.x > self.x]
        
        if self.type == PlantType.SUNFLOWER:
            if self.sun_cooldown <= 0:
                suns.append(Sun(self.x, self.y - 20, falling=False))
                self.sun_cooldown = 500
                
        elif self.type in [PlantType.PEASHOOTER, PlantType.SNOWPEA, PlantType.REPEATER]:
            if zombies_in_row and self.shoot_cooldown <= 0:
                frozen = (self.type == PlantType.SNOWPEA)
                projectiles.append(Projectile(self.x + 15, self.y, frozen=frozen))
                if self.type == PlantType.REPEATER:
                    projectiles.append(Projectile(self.x + 25, self.y, frozen=frozen))
                self.shoot_cooldown = self.get_shoot_rate()
                
        elif self.type == PlantType.CHOMPER:
            for zombie in zombies_in_row:
                if abs(zombie.x - self.x) < 40:
                    zombie.health = 0
                    self.shoot_cooldown = 180
                    break
                    
    def draw(self, screen):
        # Draw plant based on type
        anim = math.sin(self.animation_frame) * 3
        
        if self.type == PlantType.PEASHOOTER:
            pygame.draw.circle(screen, GREEN, (int(self.x), int(self.y + anim)), 15)
            pygame.draw.circle(screen, DARK_GREEN, (int(self.x + 5), int(self.y + anim)), 8)
            pygame.draw.rect(screen, DARK_GREEN, (self.x + 10, self.y - 3, 10, 6))
            
        elif self.type == PlantType.SUNFLOWER:
            pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y + anim)), 12)
            for i in range(8):
                angle = i * math.pi / 4 + self.animation_frame
                x = self.x + math.cos(angle) * 15
                y = self.y + anim + math.sin(angle) * 15
                pygame.draw.circle(screen, YELLOW, (int(x), int(y)), 4)
            pygame.draw.circle(screen, BROWN, (int(self.x), int(self.y + anim)), 6)
            
        elif self.type == PlantType.WALLNUT:
            pygame.draw.ellipse(screen, BROWN, 
                              (self.x - 15, self.y - 20, 30, 40))
            pygame.draw.ellipse(screen, BLACK,
                              (self.x - 15, self.y - 20, 30, 40), 1)
                              
        elif self.type == PlantType.SNOWPEA:
            pygame.draw.circle(screen, BLUE, (int(self.x), int(self.y + anim)), 15)
            pygame.draw.circle(screen, WHITE, (int(self.x + 5), int(self.y + anim)), 8)
            pygame.draw.rect(screen, BLUE, (self.x + 10, self.y - 3, 10, 6))
            
        elif self.type == PlantType.REPEATER:
            pygame.draw.circle(screen, DARK_GREEN, (int(self.x), int(self.y + anim)), 15)
            pygame.draw.circle(screen, GREEN, (int(self.x + 5), int(self.y + anim)), 8)
            pygame.draw.rect(screen, DARK_GREEN, (self.x + 10, self.y - 3, 15, 6))
            pygame.draw.rect(screen, DARK_GREEN, (self.x + 10, self.y - 8, 12, 4))
            
        elif self.type == PlantType.CHOMPER:
            pygame.draw.ellipse(screen, PURPLE,
                              (self.x - 15, self.y - 15 + anim, 30, 30))
            # Draw teeth
            for i in range(5):
                x = self.x - 10 + i * 5
                y = self.y - 5 + anim
                pygame.draw.polygon(screen, WHITE, 
                                   [(x, y), (x + 2, y - 5), (x + 4, y)])
                                   
        # Health bar
        if self.health < self.get_max_health():
            bar_width = 30
            bar_height = 4
            health_pct = self.health / self.get_max_health()
            pygame.draw.rect(screen, RED, 
                           (self.x - bar_width//2, self.y - 25, bar_width, bar_height))
            pygame.draw.rect(screen, GREEN,
                           (self.x - bar_width//2, self.y - 25, 
                            int(bar_width * health_pct), bar_height))

class Zombie:
    def __init__(self, zombie_type, row, wave_num=1):
        self.type = zombie_type
        self.row = row
        self.x = SCREEN_WIDTH + random.randint(0, 100)
        self.y = GRID_START_Y + row * CELL_HEIGHT + CELL_HEIGHT // 2
        self.health = self.get_max_health(wave_num)
        self.speed = self.get_speed()
        self.damage = 10
        self.frozen_timer = 0
        self.eating = False
        self.animation_frame = 0
        self.target_plant = None
        
    def get_max_health(self, wave_num):
        base_health = {
            ZombieType.NORMAL: 100,
            ZombieType.CONE: 200,
            ZombieType.BUCKET: 300,
            ZombieType.FOOTBALL: 500
        }
        return base_health.get(self.type, 100) * (1 + wave_num * 0.1)
        
    def get_speed(self):
        speed_map = {
            ZombieType.NORMAL: 0.3,
            ZombieType.CONE: 0.3,
            ZombieType.BUCKET: 0.2,
            ZombieType.FOOTBALL: 0.6
        }
        return speed_map.get(self.type, 0.3)
        
    def update(self, plants):
        self.animation_frame += 0.1
        
        if self.frozen_timer > 0:
            self.frozen_timer -= 1
            
        speed = self.speed * (0.3 if self.frozen_timer > 0 else 1.0)
        
        # Check for plants to eat
        self.eating = False
        for plant in plants:
            if plant.row == self.row and abs(plant.x - self.x) < 20:
                self.eating = True
                self.target_plant = plant
                plant.health -= self.damage * 0.5
                break
                
        if not self.eating:
            self.x -= speed
            
    def draw(self, screen):
        # Zombie walk animation
        walk_offset = math.sin(self.animation_frame * 2) * 2 if not self.eating else 0
        
        # Body
        body_color = GRAY if self.frozen_timer <= 0 else BLUE
        pygame.draw.ellipse(screen, body_color,
                          (self.x - 10, self.y - 20 + walk_offset, 20, 35))
                          
        # Head
        pygame.draw.circle(screen, body_color, 
                         (int(self.x), int(self.y - 25 + walk_offset)), 8)
                         
        # Type-specific features
        if self.type == ZombieType.CONE:
            # Traffic cone
            pygame.draw.polygon(screen, ORANGE,
                               [(self.x - 5, self.y - 30 + walk_offset),
                                (self.x + 5, self.y - 30 + walk_offset),
                                (self.x, self.y - 40 + walk_offset)])
                                
        elif self.type == ZombieType.BUCKET:
            # Bucket
            pygame.draw.rect(screen, GRAY,
                           (self.x - 8, self.y - 35 + walk_offset, 16, 10))
            pygame.draw.rect(screen, BLACK,
                           (self.x - 8, self.y - 35 + walk_offset, 16, 10), 1)
                           
        elif self.type == ZombieType.FOOTBALL:
            # Football helmet
            pygame.draw.ellipse(screen, RED,
                              (self.x - 10, self.y - 35 + walk_offset, 20, 12))
                              
        # Arms
        arm_angle = math.sin(self.animation_frame * 3) * 0.3 if not self.eating else 0.5
        pygame.draw.line(screen, body_color,
                       (self.x - 5, self.y - 10 + walk_offset),
                       (self.x - 10 - math.sin(arm_angle) * 5, self.y + walk_offset), 3)
        pygame.draw.line(screen, body_color,
                       (self.x + 5, self.y - 10 + walk_offset),
                       (self.x + 10 - math.sin(arm_angle) * 5, self.y + walk_offset), 3)
                       
        # Health bar
        if self.health < self.get_max_health(1):
            bar_width = 30
            bar_height = 3
            health_pct = self.health / self.get_max_health(1)
            pygame.draw.rect(screen, RED,
                           (self.x - bar_width//2, self.y - 40, bar_width, bar_height))
            pygame.draw.rect(screen, GREEN,
                           (self.x - bar_width//2, self.y - 40,
                            int(bar_width * health_pct), bar_height))

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Plants vs Zombies v1.0 - 60 FPS")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.big_font = pygame.font.Font(None, 48)
        
        self.reset_game()
        
    def reset_game(self):
        self.state = GameState.MENU
        self.sun_count = 150
        self.plants = []
        self.zombies = []
        self.projectiles = []
        self.suns = []
        self.selected_plant = PlantType.PEASHOOTER
        self.wave_number = 1
        self.zombie_spawn_timer = 0
        self.sun_spawn_timer = 0
        self.zombies_spawned = 0
        self.zombies_to_spawn = 5
        self.game_timer = 0
        self.victory_timer = 0
        self.grid = [[None for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        
    def get_plant_cost(self, plant_type):
        costs = {
            PlantType.PEASHOOTER: 100,
            PlantType.SUNFLOWER: 50,
            PlantType.WALLNUT: 50,
            PlantType.SNOWPEA: 175,
            PlantType.REPEATER: 200,
            PlantType.CHOMPER: 150
        }
        return costs.get(plant_type, 100)
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == GameState.PLAYING:
                        self.state = GameState.PAUSED
                    elif self.state == GameState.PAUSED:
                        self.state = GameState.PLAYING
                    elif self.state in [GameState.GAME_OVER, GameState.VICTORY]:
                        self.reset_game()
                        
                if self.state == GameState.MENU:
                    if event.key == pygame.K_SPACE:
                        self.state = GameState.PLAYING
                        
                if self.state == GameState.PLAYING:
                    # Plant selection hotkeys
                    if event.key == pygame.K_1:
                        self.selected_plant = PlantType.PEASHOOTER
                    elif event.key == pygame.K_2:
                        self.selected_plant = PlantType.SUNFLOWER
                    elif event.key == pygame.K_3:
                        self.selected_plant = PlantType.WALLNUT
                    elif event.key == pygame.K_4:
                        self.selected_plant = PlantType.SNOWPEA
                    elif event.key == pygame.K_5:
                        self.selected_plant = PlantType.REPEATER
                    elif event.key == pygame.K_6:
                        self.selected_plant = PlantType.CHOMPER
                        
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == GameState.PLAYING:
                    mx, my = pygame.mouse.get_pos()
                    
                    # Check sun collection
                    for sun in self.suns:
                        if sun.check_click(mx, my):
                            self.sun_count += 25
                            
                    # Check plant placement
                    if (GRID_START_X <= mx <= GRID_START_X + GRID_COLS * CELL_WIDTH and
                        GRID_START_Y <= my <= GRID_START_Y + GRID_ROWS * CELL_HEIGHT):
                        
                        col = (mx - GRID_START_X) // CELL_WIDTH
                        row = (my - GRID_START_Y) // CELL_HEIGHT
                        
                        if (0 <= row < GRID_ROWS and 0 <= col < GRID_COLS and
                            self.grid[row][col] is None):
                            
                            cost = self.get_plant_cost(self.selected_plant)
                            if self.sun_count >= cost:
                                plant = Plant(self.selected_plant, row, col)
                                self.plants.append(plant)
                                self.grid[row][col] = plant
                                self.sun_count -= cost
                                
                    # Check plant selection buttons
                    button_y = 20
                    for i, plant_type in enumerate(PlantType):
                        button_x = 80 + i * 80
                        if (button_x <= mx <= button_x + 70 and
                            button_y <= my <= button_y + 40):
                            self.selected_plant = plant_type
                            
        return True
        
    def spawn_zombie(self):
        if self.zombies_spawned < self.zombies_to_spawn:
            row = random.randint(0, GRID_ROWS - 1)
            
            # Determine zombie type based on wave
            if self.wave_number < 3:
                zombie_type = ZombieType.NORMAL
            elif self.wave_number < 5:
                zombie_type = random.choice([ZombieType.NORMAL, ZombieType.CONE])
            elif self.wave_number < 8:
                zombie_type = random.choice([ZombieType.NORMAL, ZombieType.CONE, 
                                            ZombieType.BUCKET])
            else:
                zombie_type = random.choice(list(ZombieType))
                
            zombie = Zombie(zombie_type, row, self.wave_number)
            self.zombies.append(zombie)
            self.zombies_spawned += 1
            
    def update(self):
        if self.state != GameState.PLAYING:
            return
            
        self.game_timer += 1
        
        # Spawn zombies
        self.zombie_spawn_timer += 1
        if self.zombie_spawn_timer > 180:
            self.spawn_zombie()
            self.zombie_spawn_timer = 0
            
        # Spawn falling suns
        self.sun_spawn_timer += 1
        if self.sun_spawn_timer > 600:
            self.suns.append(Sun(random.randint(100, 500), -20, falling=True))
            self.sun_spawn_timer = 0
            
        # Update plants
        for plant in self.plants[:]:
            plant.update(self.zombies, self.projectiles, self.suns)
            if plant.health <= 0:
                self.plants.remove(plant)
                self.grid[plant.row][plant.col] = None
                
        # Update zombies
        for zombie in self.zombies[:]:
            zombie.update(self.plants)
            if zombie.health <= 0:
                self.zombies.remove(zombie)
            elif zombie.x < 60:
                self.state = GameState.GAME_OVER
                
        # Update projectiles
        for proj in self.projectiles[:]:
            proj.update()
            if not proj.active:
                self.projectiles.remove(proj)
                continue
                
            for zombie in self.zombies:
                if proj.check_collision(zombie):
                    zombie.health -= proj.damage
                    if proj.frozen:
                        zombie.frozen_timer = 180
                    proj.active = False
                    break
                    
        # Update suns
        for sun in self.suns[:]:
            sun.update()
            if sun.collected:
                self.suns.remove(sun)
                
        # Check wave completion
        if self.zombies_spawned >= self.zombies_to_spawn and len(self.zombies) == 0:
            self.wave_number += 1
            self.zombies_spawned = 0
            self.zombies_to_spawn = 5 + self.wave_number * 2
            self.zombie_spawn_timer = -300  # Delay before next wave
            
            if self.wave_number > 10:
                self.state = GameState.VICTORY
                
    def draw_grid(self):
        # Draw lawn
        for row in range(GRID_ROWS):
            color = GREEN if row % 2 == 0 else DARK_GREEN
            pygame.draw.rect(self.screen, color,
                           (GRID_START_X, GRID_START_Y + row * CELL_HEIGHT,
                            GRID_COLS * CELL_WIDTH, CELL_HEIGHT))
                            
        # Draw grid lines
        for row in range(GRID_ROWS + 1):
            y = GRID_START_Y + row * CELL_HEIGHT
            pygame.draw.line(self.screen, BLACK,
                           (GRID_START_X, y),
                           (GRID_START_X + GRID_COLS * CELL_WIDTH, y), 1)
                           
        for col in range(GRID_COLS + 1):
            x = GRID_START_X + col * CELL_WIDTH
            pygame.draw.line(self.screen, BLACK,
                           (x, GRID_START_Y),
                           (x, GRID_START_Y + GRID_ROWS * CELL_HEIGHT), 1)
                           
    def draw_ui(self):
        # Plant selection bar
        button_y = 20
        for i, plant_type in enumerate(PlantType):
            button_x = 80 + i * 80
            cost = self.get_plant_cost(plant_type)
            color = LIGHT_GRAY if self.sun_count >= cost else GRAY
            
            if plant_type == self.selected_plant:
                pygame.draw.rect(self.screen, YELLOW,
                               (button_x - 2, button_y - 2, 74, 44), 2)
                               
            pygame.draw.rect(self.screen, color,
                           (button_x, button_y, 70, 40))
            pygame.draw.rect(self.screen, BLACK,
                           (button_x, button_y, 70, 40), 1)
                           
            # Draw mini plant icon
            icon_x = button_x + 20
            icon_y = button_y + 15
            
            if plant_type == PlantType.PEASHOOTER:
                pygame.draw.circle(self.screen, GREEN, (icon_x, icon_y), 8)
            elif plant_type == PlantType.SUNFLOWER:
                pygame.draw.circle(self.screen, YELLOW, (icon_x, icon_y), 8)
            elif plant_type == PlantType.WALLNUT:
                pygame.draw.ellipse(self.screen, BROWN,
                                  (icon_x - 8, icon_y - 10, 16, 20))
            elif plant_type == PlantType.SNOWPEA:
                pygame.draw.circle(self.screen, BLUE, (icon_x, icon_y), 8)
            elif plant_type == PlantType.REPEATER:
                pygame.draw.circle(self.screen, DARK_GREEN, (icon_x, icon_y), 8)
            elif plant_type == PlantType.CHOMPER:
                pygame.draw.ellipse(self.screen, PURPLE,
                                  (icon_x - 8, icon_y - 8, 16, 16))
                                  
            # Draw cost
            cost_text = self.font.render(str(cost), True, BLACK)
            self.screen.blit(cost_text, (button_x + 35, button_y + 20))
            
            # Draw hotkey
            key_text = self.font.render(str(i + 1), True, BLACK)
            self.screen.blit(key_text, (button_x + 5, button_y + 2))
            
        # Sun counter
        pygame.draw.circle(self.screen, YELLOW, (30, 40), 20)
        pygame.draw.circle(self.screen, ORANGE, (30, 40), 20, 2)
        sun_text = self.font.render(str(self.sun_count), True, BLACK)
        self.screen.blit(sun_text, (15, 60))
        
        # Wave counter
        wave_text = self.font.render(f"Wave: {self.wave_number}", True, WHITE)
        self.screen.blit(wave_text, (10, 10))
        
        # FPS counter
        fps = int(self.clock.get_fps())
        fps_text = self.font.render(f"FPS: {fps}", True, WHITE)
        self.screen.blit(fps_text, (SCREEN_WIDTH - 80, 10))
        
    def draw(self):
        self.screen.fill(BLACK)
        
        if self.state == GameState.MENU:
            title_text = self.big_font.render("Plants vs Zombies", True, GREEN)
            title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 100))
            self.screen.blit(title_text, title_rect)
            
            subtitle = self.font.render("PopCap Style v1.0", True, WHITE)
            subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH//2, 150))
            self.screen.blit(subtitle, subtitle_rect)
            
            start_text = self.font.render("Press SPACE to Start", True, YELLOW)
            start_rect = start_text.get_rect(center=(SCREEN_WIDTH//2, 250))
            self.screen.blit(start_text, start_rect)
            
            controls = [
                "Controls:",
                "1-6: Select Plants",
                "Click: Place Plant / Collect Sun",
                "ESC: Pause",
                "",
                "Defend your lawn from zombie waves!"
            ]
            
            y = 300
            for line in controls:
                text = self.font.render(line, True, WHITE)
                rect = text.get_rect(center=(SCREEN_WIDTH//2, y))
                self.screen.blit(text, rect)
                y += 25
                
        elif self.state == GameState.PLAYING:
            self.draw_grid()
            
            # Draw game objects
            for plant in self.plants:
                plant.draw(self.screen)
                
            for zombie in self.zombies:
                zombie.draw(self.screen)
                
            for proj in self.projectiles:
                proj.draw(self.screen)
                
            for sun in self.suns:
                sun.draw(self.screen)
                
            self.draw_ui()
            
        elif self.state == GameState.PAUSED:
            self.draw_grid()
            for plant in self.plants:
                plant.draw(self.screen)
            for zombie in self.zombies:
                zombie.draw(self.screen)
                
            # Pause overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(128)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))
            
            pause_text = self.big_font.render("PAUSED", True, YELLOW)
            pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(pause_text, pause_rect)
            
            resume_text = self.font.render("Press ESC to Resume", True, WHITE)
            resume_rect = resume_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
            self.screen.blit(resume_text, resume_rect)
            
        elif self.state == GameState.GAME_OVER:
            game_over_text = self.big_font.render("GAME OVER", True, RED)
            game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(game_over_text, game_over_rect)
            
            score_text = self.font.render(f"You survived {self.wave_number - 1} waves", True, WHITE)
            score_rect = score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
            self.screen.blit(score_text, score_rect)
            
            restart_text = self.font.render("Press ESC to Return to Menu", True, YELLOW)
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 80))
            self.screen.blit(restart_text, restart_rect)
            
        elif self.state == GameState.VICTORY:
            victory_text = self.big_font.render("VICTORY!", True, YELLOW)
            victory_rect = victory_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(victory_text, victory_rect)
            
            complete_text = self.font.render("You defeated all zombie waves!", True, GREEN)
            complete_rect = complete_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
            self.screen.blit(complete_text, complete_rect)
            
            restart_text = self.font.render("Press ESC to Return to Menu", True, WHITE)
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 80))
            self.screen.blit(restart_text, restart_rect)
            
        pygame.display.flip()
        
    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
            
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
