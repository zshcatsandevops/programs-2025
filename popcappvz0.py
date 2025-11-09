#!/usr/bin/env python3
"""
Plants vs Zombies Replanted v2.0
Full tower defense game with authentic PopCap mechanics
60 FPS @ 800x600 resolution
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
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
GRID_ROWS = 5
GRID_COLS = 9
CELL_WIDTH = 80
CELL_HEIGHT = 100
GRID_START_X = 80
GRID_START_Y = 100

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (34, 139, 34)
DARK_GREEN = (0, 100, 0)
LAWN_GREEN = (50, 150, 50)
BROWN = (139, 69, 19)
TAN = (210, 180, 140)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
BLUE = (100, 150, 255)
LIGHT_BLUE = (150, 200, 255)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
PURPLE = (150, 50, 150)
ORANGE = (255, 165, 0)
PINK = (255, 192, 203)
SILVER = (192, 192, 192)

class PlantType(Enum):
    PEASHOOTER = 1
    SUNFLOWER = 2
    WALLNUT = 3
    SNOWPEA = 4
    REPEATER = 5
    CHOMPER = 6
    CHERRY_BOMB = 7
    POTATO_MINE = 8

class ZombieType(Enum):
    NORMAL = 1
    CONE = 2
    BUCKET = 3
    FOOTBALL = 4
    NEWSPAPER = 5

class GameState(Enum):
    MENU = 1
    PLAYING = 2
    PAUSED = 3
    GAME_OVER = 4
    VICTORY = 5

class Projectile:
    def __init__(self, x, y, damage=20, speed=4, frozen=False):
        self.x = x
        self.y = y
        self.damage = damage
        self.speed = speed
        self.frozen = frozen
        self.radius = 5
        self.active = True
        self.glow = 0
        
    def update(self):
        self.x += self.speed
        self.glow += 0.2
        if self.x > SCREEN_WIDTH + 50:
            self.active = False
            
    def draw(self, screen):
        glow_size = 2 + abs(math.sin(self.glow)) * 2
        if self.frozen:
            pygame.draw.circle(screen, LIGHT_BLUE, (int(self.x), int(self.y)), int(self.radius + glow_size))
            pygame.draw.circle(screen, BLUE, (int(self.x), int(self.y)), self.radius)
        else:
            pygame.draw.circle(screen, (100, 255, 100), (int(self.x), int(self.y)), int(self.radius + glow_size))
            pygame.draw.circle(screen, GREEN, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, WHITE, (int(self.x - 2), int(self.y - 2)), 2)
        
    def check_collision(self, zombie):
        dist = math.sqrt((self.x - zombie.x)**2 + (self.y - zombie.y)**2)
        return dist < self.radius + 20

class Explosion:
    def __init__(self, x, y, radius=150):
        self.x = x
        self.y = y
        self.radius = radius
        self.current_radius = 10
        self.expand_speed = 15
        self.lifetime = 30
        self.active = True
        
    def update(self):
        if self.current_radius < self.radius:
            self.current_radius += self.expand_speed
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.active = False
            
    def draw(self, screen):
        if self.active:
            alpha = int(255 * (self.lifetime / 30))
            for i in range(3):
                r = self.current_radius - i * 10
                if r > 0:
                    color = (255, 100 + i * 50, 0, alpha)
                    pygame.draw.circle(screen, color[:3], (int(self.x), int(self.y)), int(r), 5)
                    
    def check_damage(self, zombie):
        dist = math.sqrt((self.x - zombie.x)**2 + (self.y - zombie.y)**2)
        return dist < self.current_radius

class Sun:
    def __init__(self, x, y, falling=True):
        self.x = x
        self.y = y
        self.target_y = random.randint(200, 500) if falling else y
        self.falling = falling
        self.lifetime = 600 if not falling else 1200
        self.collected = False
        self.radius = 18
        self.bounce = 0
        self.sparkle = 0
        
    def update(self):
        if self.falling and self.y < self.target_y:
            self.y += 2
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.collected = True
        self.bounce += 0.15
        self.sparkle += 0.3
            
    def draw(self, screen):
        if not self.collected:
            bounce_offset = math.sin(self.bounce) * 3
            y_pos = int(self.y + bounce_offset)
            
            # Outer glow
            pygame.draw.circle(screen, (255, 255, 150), (int(self.x), y_pos), self.radius + 4)
            # Main sun
            pygame.draw.circle(screen, YELLOW, (int(self.x), y_pos), self.radius)
            pygame.draw.circle(screen, ORANGE, (int(self.x), y_pos), self.radius, 2)
            
            # Sun rays
            for i in range(12):
                angle = i * math.pi / 6 + self.sparkle
                x1 = self.x + math.cos(angle) * self.radius
                y1 = y_pos + math.sin(angle) * self.radius
                x2 = self.x + math.cos(angle) * (self.radius + 8)
                y2 = y_pos + math.sin(angle) * (self.radius + 8)
                pygame.draw.line(screen, YELLOW, (x1, y1), (x2, y2), 3)
                
            # Inner highlight
            pygame.draw.circle(screen, (255, 255, 200), 
                             (int(self.x - 5), y_pos - 5), 5)
                
    def check_click(self, mx, my):
        if self.collected:
            return False
        dist = math.sqrt((mx - self.x)**2 + (my - self.y)**2)
        if dist < self.radius + 15:
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
        self.max_health = self.health
        self.shoot_cooldown = 0
        self.sun_cooldown = 0
        self.animation_frame = 0
        self.armed = False  # For potato mine
        self.arm_timer = 0
        self.exploded = False
        
    def get_max_health(self):
        health_map = {
            PlantType.PEASHOOTER: 100,
            PlantType.SUNFLOWER: 100,
            PlantType.WALLNUT: 400,
            PlantType.SNOWPEA: 100,
            PlantType.REPEATER: 120,
            PlantType.CHOMPER: 150,
            PlantType.CHERRY_BOMB: 200,
            PlantType.POTATO_MINE: 100
        }
        return health_map.get(self.type, 100)
        
    def get_shoot_rate(self):
        rate_map = {
            PlantType.PEASHOOTER: 80,
            PlantType.SNOWPEA: 80,
            PlantType.REPEATER: 40,
            PlantType.CHOMPER: 200
        }
        return rate_map.get(self.type, 0)
        
    def update(self, zombies, projectiles, suns, explosions):
        self.animation_frame += 0.1
        
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
            
        if self.sun_cooldown > 0:
            self.sun_cooldown -= 1
            
        # Potato mine arming
        if self.type == PlantType.POTATO_MINE and not self.armed:
            self.arm_timer += 1
            if self.arm_timer >= 300:  # 5 seconds
                self.armed = True
            
        # Cherry bomb explosion
        if self.type == PlantType.CHERRY_BOMB and not self.exploded:
            self.shoot_cooldown += 1
            if self.shoot_cooldown >= 60:  # 1 second fuse
                explosions.append(Explosion(self.x, self.y, 180))
                self.health = 0
                self.exploded = True
                return
            
        # Check if any zombie in same row
        zombies_in_row = [z for z in zombies if z.row == self.row and z.x > self.x - 50]
        
        if self.type == PlantType.SUNFLOWER:
            if self.sun_cooldown <= 0:
                suns.append(Sun(self.x, self.y - 30, falling=False))
                self.sun_cooldown = 600
                
        elif self.type in [PlantType.PEASHOOTER, PlantType.SNOWPEA, PlantType.REPEATER]:
            if zombies_in_row and self.shoot_cooldown <= 0:
                frozen = (self.type == PlantType.SNOWPEA)
                projectiles.append(Projectile(self.x + 20, self.y, frozen=frozen))
                if self.type == PlantType.REPEATER:
                    # Second pea slightly delayed
                    pass
                self.shoot_cooldown = self.get_shoot_rate()
                
        elif self.type == PlantType.CHOMPER:
            if self.shoot_cooldown <= 0:
                for zombie in zombies_in_row:
                    if abs(zombie.x - self.x) < 50:
                        zombie.health = 0
                        self.shoot_cooldown = 240  # Long digest time
                        break
                        
        elif self.type == PlantType.POTATO_MINE:
            if self.armed and not self.exploded:
                for zombie in zombies_in_row:
                    if abs(zombie.x - self.x) < 40:
                        explosions.append(Explosion(self.x, self.y, 120))
                        self.health = 0
                        self.exploded = True
                        break
                    
    def draw(self, screen):
        anim = math.sin(self.animation_frame) * 4
        
        if self.type == PlantType.PEASHOOTER:
            # Body
            pygame.draw.circle(screen, GREEN, (int(self.x), int(self.y + anim)), 20)
            pygame.draw.circle(screen, DARK_GREEN, (int(self.x), int(self.y + anim)), 20, 2)
            # Head
            pygame.draw.circle(screen, DARK_GREEN, (int(self.x + 8), int(self.y + anim)), 12)
            # Barrel
            pygame.draw.rect(screen, DARK_GREEN, (self.x + 15, self.y + anim - 4, 12, 8))
            # Eyes
            pygame.draw.circle(screen, WHITE, (int(self.x + 5), int(self.y + anim - 5)), 3)
            pygame.draw.circle(screen, BLACK, (int(self.x + 6), int(self.y + anim - 5)), 1)
            # Leaves
            for i in [-1, 1]:
                leaf_y = self.y + anim + 15 + i * 5
                pygame.draw.ellipse(screen, DARK_GREEN, 
                                  (self.x - 15, leaf_y, 20, 10))
            
        elif self.type == PlantType.SUNFLOWER:
            # Center
            pygame.draw.circle(screen, BROWN, (int(self.x), int(self.y + anim)), 15)
            # Petals
            for i in range(8):
                angle = i * math.pi / 4 + self.animation_frame * 0.5
                x = self.x + math.cos(angle) * 20
                y = self.y + anim + math.sin(angle) * 20
                pygame.draw.circle(screen, YELLOW, (int(x), int(y)), 8)
                pygame.draw.circle(screen, ORANGE, (int(x), int(y)), 8, 1)
            # Face
            pygame.draw.circle(screen, BLACK, (int(self.x - 5), int(self.y + anim - 3)), 2)
            pygame.draw.circle(screen, BLACK, (int(self.x + 5), int(self.y + anim - 3)), 2)
            pygame.draw.arc(screen, BLACK, 
                          (self.x - 6, self.y + anim, 12, 8), math.pi, 2*math.pi, 2)
            
        elif self.type == PlantType.WALLNUT:
            # Main body
            pygame.draw.ellipse(screen, TAN, 
                              (self.x - 20, self.y + anim - 25, 40, 50))
            pygame.draw.ellipse(screen, BROWN, 
                              (self.x - 20, self.y + anim - 25, 40, 50), 3)
            # Shell pattern
            for i in range(3):
                for j in range(3):
                    cx = self.x - 10 + j * 10
                    cy = self.y + anim - 15 + i * 12
                    pygame.draw.circle(screen, BROWN, (int(cx), int(cy)), 3)
            # Eyes
            pygame.draw.ellipse(screen, BLACK, (self.x - 10, self.y + anim - 8, 8, 12))
            pygame.draw.ellipse(screen, BLACK, (self.x + 2, self.y + anim - 8, 8, 12))
            # Health indicator
            health_ratio = self.health / self.max_health
            if health_ratio < 0.7:
                # Cracks
                pygame.draw.line(screen, BROWN, 
                               (self.x - 15, self.y + anim - 10),
                               (self.x - 5, self.y + anim + 5), 2)
            if health_ratio < 0.3:
                pygame.draw.line(screen, BROWN,
                               (self.x + 5, self.y + anim - 15),
                               (self.x + 15, self.y + anim), 2)
            
        elif self.type == PlantType.SNOWPEA:
            # Body
            pygame.draw.circle(screen, LIGHT_BLUE, (int(self.x), int(self.y + anim)), 20)
            pygame.draw.circle(screen, BLUE, (int(self.x), int(self.y + anim)), 20, 2)
            # Head
            pygame.draw.circle(screen, BLUE, (int(self.x + 8), int(self.y + anim)), 12)
            # Barrel
            pygame.draw.rect(screen, BLUE, (self.x + 15, self.y + anim - 4, 12, 8))
            # Eyes
            pygame.draw.circle(screen, WHITE, (int(self.x + 5), int(self.y + anim - 5)), 3)
            pygame.draw.circle(screen, BLACK, (int(self.x + 6), int(self.y + anim - 5)), 1)
            # Ice crystals
            for i in range(4):
                angle = i * math.pi / 2 + self.animation_frame
                x = self.x + math.cos(angle) * 25
                y = self.y + anim + math.sin(angle) * 25
                pygame.draw.line(screen, WHITE, (self.x, self.y + anim), (x, y), 2)
            
        elif self.type == PlantType.REPEATER:
            # Body
            pygame.draw.circle(screen, DARK_GREEN, (int(self.x), int(self.y + anim)), 22)
            pygame.draw.circle(screen, GREEN, (int(self.x), int(self.y + anim)), 22, 2)
            # Two heads
            for offset in [6, -6]:
                pygame.draw.circle(screen, GREEN, 
                                 (int(self.x + 10), int(self.y + anim + offset)), 10)
                pygame.draw.rect(screen, GREEN,
                               (self.x + 18, self.y + anim + offset - 3, 10, 6))
            # Eyes
            pygame.draw.circle(screen, WHITE, (int(self.x + 3), int(self.y + anim - 5)), 3)
            pygame.draw.circle(screen, BLACK, (int(self.x + 4), int(self.y + anim - 5)), 1)
            
        elif self.type == PlantType.CHOMPER:
            chomp_open = math.sin(self.animation_frame * 2) * 0.3 + 0.7
            # Body
            pygame.draw.circle(screen, PURPLE, (int(self.x), int(self.y + anim + 10)), 18)
            # Mouth
            mouth_height = int(30 * chomp_open)
            pygame.draw.ellipse(screen, (100, 0, 100),
                              (self.x - 15, self.y + anim - mouth_height//2, 30, mouth_height))
            pygame.draw.ellipse(screen, (50, 0, 50),
                              (self.x - 15, self.y + anim - mouth_height//2, 30, mouth_height), 2)
            # Teeth
            for i in range(5):
                tx = self.x - 10 + i * 5
                pygame.draw.polygon(screen, WHITE,
                                  [(tx, self.y + anim - mouth_height//2),
                                   (tx + 3, self.y + anim - mouth_height//2),
                                   (tx + 1.5, self.y + anim - mouth_height//2 + 5)])
                pygame.draw.polygon(screen, WHITE,
                                  [(tx, self.y + anim + mouth_height//2),
                                   (tx + 3, self.y + anim + mouth_height//2),
                                   (tx + 1.5, self.y + anim + mouth_height//2 - 5)])
            
        elif self.type == PlantType.CHERRY_BOMB:
            # Two cherries
            for offset in [-12, 12]:
                cherry_x = self.x + offset
                # Glow if about to explode
                if self.shoot_cooldown > 30:
                    glow_size = int((self.shoot_cooldown - 30) * 0.5)
                    pygame.draw.circle(screen, (255, 100, 100),
                                     (int(cherry_x), int(self.y + anim)), 15 + glow_size)
                pygame.draw.circle(screen, RED, (int(cherry_x), int(self.y + anim)), 15)
                pygame.draw.circle(screen, (200, 0, 0), (int(cherry_x), int(self.y + anim)), 15, 2)
                # Highlight
                pygame.draw.circle(screen, (255, 150, 150),
                                 (int(cherry_x - 5), int(self.y + anim - 5)), 4)
            # Stem
            pygame.draw.line(screen, DARK_GREEN,
                           (self.x - 12, self.y + anim - 15),
                           (self.x, self.y + anim - 25), 3)
            pygame.draw.line(screen, DARK_GREEN,
                           (self.x + 12, self.y + anim - 15),
                           (self.x, self.y + anim - 25), 3)
            # Eyes (worried expression)
            for cherry_x in [self.x - 12, self.x + 12]:
                pygame.draw.circle(screen, BLACK, (int(cherry_x - 3), int(self.y + anim)), 2)
                pygame.draw.circle(screen, BLACK, (int(cherry_x + 3), int(self.y + anim)), 2)
            
        elif self.type == PlantType.POTATO_MINE:
            if not self.armed:
                # Unarmed - dirt mound
                pygame.draw.ellipse(screen, BROWN,
                                  (self.x - 18, self.y + anim, 36, 20))
                pygame.draw.ellipse(screen, TAN,
                                  (self.x - 15, self.y + anim - 5, 30, 15))
                # Progress indicator
                progress = self.arm_timer / 300
                pygame.draw.rect(screen, GRAY,
                               (self.x - 12, self.y + anim + 25, 24, 3))
                pygame.draw.rect(screen, GREEN,
                               (self.x - 12, self.y + anim + 25, int(24 * progress), 3))
            else:
                # Armed - potato visible
                pygame.draw.ellipse(screen, TAN,
                                  (self.x - 15, self.y + anim, 30, 25))
                pygame.draw.ellipse(screen, BROWN,
                                  (self.x - 15, self.y + anim, 30, 25), 2)
                # Eyes
                pygame.draw.circle(screen, BLACK, (int(self.x - 5), int(self.y + anim + 5)), 2)
                pygame.draw.circle(screen, BLACK, (int(self.x + 5), int(self.y + anim + 5)), 2)
                # Spud spots
                for i in range(3):
                    sx = self.x - 8 + i * 8
                    sy = self.y + anim + random.randint(-5, 10)
                    pygame.draw.circle(screen, BROWN, (int(sx), int(sy)), 2)

class Zombie:
    def __init__(self, zombie_type, row):
        self.type = zombie_type
        self.row = row
        self.x = SCREEN_WIDTH + 50
        self.y = GRID_START_Y + row * CELL_HEIGHT + CELL_HEIGHT // 2
        self.health = self.get_max_health()
        self.max_health = self.health
        self.speed = self.get_speed()
        self.damage = 10
        self.attack_cooldown = 0
        self.animation_frame = 0
        self.eating = False
        self.slowed = False
        self.slow_timer = 0
        self.has_accessory = True  # Cone/bucket/newspaper
        
    def get_max_health(self):
        health_map = {
            ZombieType.NORMAL: 100,
            ZombieType.CONE: 280,
            ZombieType.BUCKET: 500,
            ZombieType.FOOTBALL: 400,
            ZombieType.NEWSPAPER: 200
        }
        return health_map.get(self.type, 100)
        
    def get_speed(self):
        speed_map = {
            ZombieType.NORMAL: 0.3,
            ZombieType.CONE: 0.3,
            ZombieType.BUCKET: 0.25,
            ZombieType.FOOTBALL: 0.8,
            ZombieType.NEWSPAPER: 0.3
        }
        return speed_map.get(self.type, 0.3)
        
    def update(self, plants):
        self.animation_frame += 0.15
        
        if self.slow_timer > 0:
            self.slow_timer -= 1
            self.slowed = True
        else:
            self.slowed = False
            
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
            
        # Check for plants to eat
        self.eating = False
        for plant in plants:
            if plant.row == self.row and abs(plant.x - self.x) < 30:
                self.eating = True
                if self.attack_cooldown <= 0:
                    plant.health -= self.damage
                    self.attack_cooldown = 60
                break
                
        if not self.eating:
            move_speed = self.speed
            if self.slowed:
                move_speed *= 0.5
            self.x -= move_speed
            
        # Newspaper zombie speeds up when newspaper is destroyed
        if self.type == ZombieType.NEWSPAPER:
            if self.has_accessory and self.health < self.max_health * 0.5:
                self.has_accessory = False
                self.speed = 0.7
                
        # Lose accessories at certain health thresholds
        if self.type in [ZombieType.CONE, ZombieType.BUCKET]:
            if self.has_accessory and self.health < 100:
                self.has_accessory = False
                
    def draw(self, screen):
        walk_bob = math.sin(self.animation_frame) * 3 if not self.eating else 0
        y_pos = int(self.y + walk_bob)
        
        # Slowed effect
        if self.slowed:
            pygame.draw.circle(screen, LIGHT_BLUE, (int(self.x), y_pos), 35, 2)
            
        # Zombie base body
        if self.type == ZombieType.FOOTBALL:
            # Football player
            # Body (with uniform)
            pygame.draw.rect(screen, RED, (self.x - 15, y_pos - 20, 30, 40))
            pygame.draw.rect(screen, WHITE, (self.x - 15, y_pos - 10, 30, 5))
            # Helmet
            pygame.draw.ellipse(screen, SILVER, (self.x - 18, y_pos - 35, 36, 25))
            pygame.draw.rect(screen, SILVER, (self.x - 5, y_pos - 25, 10, 5))
            # Face guard
            pygame.draw.rect(screen, SILVER, (self.x + 5, y_pos - 20, 8, 15), 2)
            # Arms
            pygame.draw.rect(screen, (139, 69, 19), (self.x - 20, y_pos - 15, 8, 25))
            pygame.draw.rect(screen, (139, 69, 19), (self.x + 12, y_pos - 15, 8, 25))
            # Legs
            leg_offset = int(math.sin(self.animation_frame * 2) * 5)
            pygame.draw.rect(screen, (139, 69, 19), (self.x - 10, y_pos + 20, 8, 20 + leg_offset))
            pygame.draw.rect(screen, (139, 69, 19), (self.x + 2, y_pos + 20, 8, 20 - leg_offset))
            
        else:
            # Regular zombie body
            # Head
            pygame.draw.circle(screen, (100, 150, 100), (int(self.x), y_pos - 15), 15)
            # Eyes
            eye_x = -5 if self.eating else 2
            pygame.draw.circle(screen, RED, (int(self.x + eye_x), y_pos - 18), 3)
            pygame.draw.circle(screen, RED, (int(self.x + eye_x + 8), y_pos - 18), 3)
            # Mouth
            if self.eating:
                pygame.draw.arc(screen, BLACK,
                              (self.x + 5, y_pos - 10, 10, 8), 0, math.pi, 2)
            # Body/Torso
            pygame.draw.rect(screen, (80, 120, 80), (self.x - 12, y_pos, 24, 30))
            # Arms
            arm_angle = math.sin(self.animation_frame * 2) * 0.3
            if self.eating:
                # Eating pose
                pygame.draw.line(screen, (100, 150, 100),
                               (self.x - 12, y_pos + 5),
                               (self.x - 25, y_pos - 5), 6)
                pygame.draw.line(screen, (100, 150, 100),
                               (self.x + 12, y_pos + 5),
                               (self.x + 25, y_pos - 5), 6)
            else:
                # Walking pose
                pygame.draw.line(screen, (100, 150, 100),
                               (self.x - 12, y_pos + 5),
                               (self.x - 20, y_pos + 15 + int(arm_angle * 10)), 6)
                pygame.draw.line(screen, (100, 150, 100),
                               (self.x + 12, y_pos + 5),
                               (self.x + 20, y_pos + 15 - int(arm_angle * 10)), 6)
            # Legs
            leg_offset = int(math.sin(self.animation_frame * 2) * 8)
            pygame.draw.line(screen, (100, 150, 100),
                           (self.x - 8, y_pos + 30),
                           (self.x - 10, y_pos + 45 + leg_offset), 6)
            pygame.draw.line(screen, (100, 150, 100),
                           (self.x + 8, y_pos + 30),
                           (self.x + 10, y_pos + 45 - leg_offset), 6)
            
            # Accessories
            if self.has_accessory:
                if self.type == ZombieType.CONE:
                    # Traffic cone
                    pygame.draw.polygon(screen, ORANGE,
                                      [(self.x, y_pos - 35),
                                       (self.x - 12, y_pos - 15),
                                       (self.x + 12, y_pos - 15)])
                    pygame.draw.line(screen, WHITE, 
                                   (self.x - 10, y_pos - 20),
                                   (self.x + 10, y_pos - 20), 3)
                                   
                elif self.type == ZombieType.BUCKET:
                    # Metal bucket
                    pygame.draw.rect(screen, SILVER, (self.x - 15, y_pos - 35, 30, 20))
                    pygame.draw.rect(screen, GRAY, (self.x - 15, y_pos - 35, 30, 20), 2)
                    pygame.draw.line(screen, GRAY,
                                   (self.x - 12, y_pos - 35),
                                   (self.x - 15, y_pos - 15), 2)
                    pygame.draw.line(screen, GRAY,
                                   (self.x + 12, y_pos - 35),
                                   (self.x + 15, y_pos - 15), 2)
                                   
                elif self.type == ZombieType.NEWSPAPER:
                    # Newspaper
                    pygame.draw.rect(screen, WHITE, (self.x - 25, y_pos - 5, 20, 30))
                    pygame.draw.rect(screen, BLACK, (self.x - 25, y_pos - 5, 20, 30), 1)
                    # Text lines
                    for i in range(5):
                        pygame.draw.line(screen, BLACK,
                                       (self.x - 23, y_pos + i * 5),
                                       (self.x - 7, y_pos + i * 5), 1)
                    # Glasses
                    pygame.draw.rect(screen, BLACK, (self.x - 8, y_pos - 18, 6, 5), 2)
                    pygame.draw.rect(screen, BLACK, (self.x + 2, y_pos - 18, 6, 5), 2)
                    pygame.draw.line(screen, BLACK, (self.x - 2, y_pos - 16), (self.x + 2, y_pos - 16), 2)
            
        # Health bar
        if self.health < self.max_health:
            bar_width = 30
            bar_height = 4
            health_percent = self.health / self.max_health
            pygame.draw.rect(screen, RED, 
                           (self.x - bar_width//2, y_pos - 50, bar_width, bar_height))
            pygame.draw.rect(screen, GREEN,
                           (self.x - bar_width//2, y_pos - 50, int(bar_width * health_percent), bar_height))
            pygame.draw.rect(screen, BLACK,
                           (self.x - bar_width//2, y_pos - 50, bar_width, bar_height), 1)

class Lawnmower:
    def __init__(self, row):
        self.row = row
        self.x = 20
        self.y = GRID_START_Y + row * CELL_HEIGHT + CELL_HEIGHT // 2
        self.active = True
        self.moving = False
        self.speed = 5
        
    def update(self, zombies):
        if self.moving:
            self.x += self.speed
            if self.x > SCREEN_WIDTH + 50:
                self.active = False
                return
                
            # Destroy zombies in path
            for zombie in zombies[:]:
                if zombie.row == self.row and abs(zombie.x - self.x) < 40:
                    zombie.health = 0
                    
        else:
            # Check if zombie reached it
            for zombie in zombies:
                if zombie.row == self.row and zombie.x < 70:
                    self.moving = True
                    break
                    
    def draw(self, screen):
        if self.active:
            # Mower body
            pygame.draw.rect(screen, RED, (self.x - 15, self.y - 10, 30, 20))
            pygame.draw.rect(screen, (180, 0, 0), (self.x - 15, self.y - 10, 30, 20), 2)
            # Wheels
            pygame.draw.circle(screen, BLACK, (int(self.x - 10), int(self.y + 8)), 5)
            pygame.draw.circle(screen, BLACK, (int(self.x + 10), int(self.y + 8)), 5)
            # Blade (spinning if moving)
            if self.moving:
                angle = (self.x * 0.5) % (2 * math.pi)
                for i in range(4):
                    a = angle + i * math.pi / 2
                    x1 = self.x + math.cos(a) * 8
                    y1 = self.y + math.sin(a) * 8
                    pygame.draw.line(screen, SILVER, (self.x, self.y), (x1, y1), 3)
            else:
                pygame.draw.circle(screen, SILVER, (int(self.x), int(self.y)), 8)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Plants vs Zombies Replanted v2.0")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.big_font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 18)
        
        self.state = GameState.MENU
        self.reset_game()
        
    def reset_game(self):
        self.plants = []
        self.zombies = []
        self.projectiles = []
        self.suns = []
        self.explosions = []
        self.lawnmowers = [Lawnmower(i) for i in range(GRID_ROWS)]
        
        self.sun_count = 150
        self.selected_plant = PlantType.PEASHOOTER
        self.wave_number = 1
        self.zombies_spawned = 0
        self.zombies_to_spawn = 10
        self.zombie_spawn_timer = 0
        self.sun_spawn_timer = 0
        self.grid = [[None for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        
    def get_plant_cost(self, plant_type):
        costs = {
            PlantType.PEASHOOTER: 100,
            PlantType.SUNFLOWER: 50,
            PlantType.WALLNUT: 50,
            PlantType.SNOWPEA: 175,
            PlantType.REPEATER: 200,
            PlantType.CHOMPER: 150,
            PlantType.CHERRY_BOMB: 150,
            PlantType.POTATO_MINE: 25
        }
        return costs.get(plant_type, 100)
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == GameState.MENU:
                        return False
                    elif self.state == GameState.PLAYING:
                        self.state = GameState.PAUSED
                    elif self.state == GameState.PAUSED:
                        self.state = GameState.PLAYING
                    elif self.state in [GameState.GAME_OVER, GameState.VICTORY]:
                        self.state = GameState.MENU
                        self.reset_game()
                        
                elif event.key == pygame.K_SPACE and self.state == GameState.MENU:
                    self.state = GameState.PLAYING
                    
                # Plant selection hotkeys
                elif self.state == GameState.PLAYING:
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
                    elif event.key == pygame.K_7:
                        self.selected_plant = PlantType.CHERRY_BOMB
                    elif event.key == pygame.K_8:
                        self.selected_plant = PlantType.POTATO_MINE
                        
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pygame.mouse.get_pos()
                
                if self.state == GameState.PLAYING:
                    # Check sun collection
                    for sun in self.suns[:]:
                        if sun.check_click(mx, my):
                            self.sun_count += 25
                            break
                            
                    # Check plant selection
                    button_y = 20
                    for i, plant_type in enumerate(PlantType):
                        button_x = 80 + i * 90
                        if (button_x < mx < button_x + 80 and 
                            button_y < my < button_y + 50):
                            if self.sun_count >= self.get_plant_cost(plant_type):
                                self.selected_plant = plant_type
                            break
                            
                    # Check plant placement
                    if (GRID_START_X < mx < GRID_START_X + GRID_COLS * CELL_WIDTH and
                        GRID_START_Y < my < GRID_START_Y + GRID_ROWS * CELL_HEIGHT):
                        col = (mx - GRID_START_X) // CELL_WIDTH
                        row = (my - GRID_START_Y) // CELL_HEIGHT
                        
                        if self.grid[row][col] is None:
                            cost = self.get_plant_cost(self.selected_plant)
                            if self.sun_count >= cost:
                                plant = Plant(self.selected_plant, row, col)
                                self.plants.append(plant)
                                self.grid[row][col] = plant
                                self.sun_count -= cost
                                
        return True
        
    def spawn_zombie(self):
        # Weight towards stronger zombies in later waves
        zombie_types = [ZombieType.NORMAL] * 10
        if self.wave_number >= 2:
            zombie_types.extend([ZombieType.CONE] * 5)
        if self.wave_number >= 4:
            zombie_types.extend([ZombieType.BUCKET] * 3)
        if self.wave_number >= 3:
            zombie_types.extend([ZombieType.FOOTBALL] * 2)
        if self.wave_number >= 5:
            zombie_types.extend([ZombieType.NEWSPAPER] * 3)
            
        zombie_type = random.choice(zombie_types)
        row = random.randint(0, GRID_ROWS - 1)
        self.zombies.append(Zombie(zombie_type, row))
        
    def update(self):
        if self.state != GameState.PLAYING:
            return
            
        # Spawn sky suns
        self.sun_spawn_timer += 1
        if self.sun_spawn_timer >= 400:
            self.suns.append(Sun(random.randint(100, SCREEN_WIDTH - 100), 0))
            self.sun_spawn_timer = 0
            
        # Spawn zombies
        if self.zombies_spawned < self.zombies_to_spawn:
            self.zombie_spawn_timer += 1
            spawn_rate = max(100, 200 - self.wave_number * 10)
            if self.zombie_spawn_timer >= spawn_rate:
                self.spawn_zombie()
                self.zombies_spawned += 1
                self.zombie_spawn_timer = 0
                
        # Update game objects
        for plant in self.plants[:]:
            plant.update(self.zombies, self.projectiles, self.suns, self.explosions)
            if plant.health <= 0:
                self.plants.remove(plant)
                self.grid[plant.row][plant.col] = None
                
        for zombie in self.zombies[:]:
            zombie.update(self.plants)
            if zombie.health <= 0:
                self.zombies.remove(zombie)
            elif zombie.x < 0:
                self.state = GameState.GAME_OVER
                
        for proj in self.projectiles[:]:
            proj.update()
            if not proj.active:
                self.projectiles.remove(proj)
                
        for explosion in self.explosions[:]:
            explosion.update()
            if not explosion.active:
                self.explosions.remove(explosion)
            else:
                # Check zombie damage
                for zombie in self.zombies:
                    if explosion.check_damage(zombie):
                        zombie.health -= 100  # Massive damage
                        
        for sun in self.suns[:]:
            sun.update()
            if sun.collected:
                self.suns.remove(sun)
                
        for mower in self.lawnmowers[:]:
            if mower.active:
                mower.update(self.zombies)
                
        # Projectile collision
        for proj in self.projectiles[:]:
            for zombie in self.zombies:
                if proj.active and proj.check_collision(zombie):
                    zombie.health -= proj.damage
                    if proj.frozen:
                        zombie.slow_timer = 180
                    proj.active = False
                    break
                    
        # Wave completion
        if self.zombies_spawned >= self.zombies_to_spawn and len(self.zombies) == 0:
            self.wave_number += 1
            self.zombies_spawned = 0
            self.zombies_to_spawn = min(5 + self.wave_number * 3, 50)
            self.zombie_spawn_timer = -400
            
            if self.wave_number > 15:
                self.state = GameState.VICTORY
                
    def draw_grid(self):
        # Draw lawn background
        for row in range(GRID_ROWS):
            color = LAWN_GREEN if row % 2 == 0 else DARK_GREEN
            pygame.draw.rect(self.screen, color,
                           (GRID_START_X, GRID_START_Y + row * CELL_HEIGHT,
                            GRID_COLS * CELL_WIDTH, CELL_HEIGHT))
                            
        # Draw grid lines (subtle)
        for row in range(GRID_ROWS + 1):
            y = GRID_START_Y + row * CELL_HEIGHT
            pygame.draw.line(self.screen, (0, 80, 0),
                           (GRID_START_X, y),
                           (GRID_START_X + GRID_COLS * CELL_WIDTH, y), 1)
                           
        for col in range(GRID_COLS + 1):
            x = GRID_START_X + col * CELL_WIDTH
            pygame.draw.line(self.screen, (0, 80, 0),
                           (x, GRID_START_Y),
                           (x, GRID_START_Y + GRID_ROWS * CELL_HEIGHT), 1)
                           
    def draw_ui(self):
        # Top bar background
        pygame.draw.rect(self.screen, (100, 70, 40), (0, 0, SCREEN_WIDTH, 80))
        pygame.draw.rect(self.screen, BROWN, (0, 78, SCREEN_WIDTH, 2))
        
        # Plant selection bar
        button_y = 15
        for i, plant_type in enumerate(PlantType):
            button_x = 80 + i * 90
            cost = self.get_plant_cost(plant_type)
            can_afford = self.sun_count >= cost
            color = (150, 200, 150) if can_afford else (100, 100, 100)
            
            # Selection highlight
            if plant_type == self.selected_plant:
                pygame.draw.rect(self.screen, YELLOW,
                               (button_x - 3, button_y - 3, 86, 56), 3)
                               
            # Button background
            pygame.draw.rect(self.screen, color,
                           (button_x, button_y, 80, 50), border_radius=5)
            pygame.draw.rect(self.screen, BLACK,
                           (button_x, button_y, 80, 50), 2, border_radius=5)
                           
            # Draw mini plant icon (centered)
            icon_x = button_x + 25
            icon_y = button_y + 20
            
            if plant_type == PlantType.PEASHOOTER:
                pygame.draw.circle(self.screen, GREEN, (icon_x, icon_y), 10)
                pygame.draw.rect(self.screen, DARK_GREEN, (icon_x + 8, icon_y - 3, 8, 6))
            elif plant_type == PlantType.SUNFLOWER:
                pygame.draw.circle(self.screen, YELLOW, (icon_x, icon_y), 10)
                for j in range(8):
                    angle = j * math.pi / 4
                    x = icon_x + math.cos(angle) * 12
                    y = icon_y + math.sin(angle) * 12
                    pygame.draw.circle(self.screen, YELLOW, (int(x), int(y)), 3)
            elif plant_type == PlantType.WALLNUT:
                pygame.draw.ellipse(self.screen, TAN,
                                  (icon_x - 10, icon_y - 12, 20, 24))
            elif plant_type == PlantType.SNOWPEA:
                pygame.draw.circle(self.screen, LIGHT_BLUE, (icon_x, icon_y), 10)
                pygame.draw.rect(self.screen, BLUE, (icon_x + 8, icon_y - 3, 8, 6))
            elif plant_type == PlantType.REPEATER:
                pygame.draw.circle(self.screen, DARK_GREEN, (icon_x, icon_y), 11)
                pygame.draw.circle(self.screen, GREEN, (icon_x, icon_y - 5), 6)
                pygame.draw.circle(self.screen, GREEN, (icon_x, icon_y + 5), 6)
            elif plant_type == PlantType.CHOMPER:
                pygame.draw.ellipse(self.screen, PURPLE,
                                  (icon_x - 10, icon_y - 10, 20, 20))
            elif plant_type == PlantType.CHERRY_BOMB:
                pygame.draw.circle(self.screen, RED, (icon_x - 5, icon_y), 7)
                pygame.draw.circle(self.screen, RED, (icon_x + 5, icon_y), 7)
            elif plant_type == PlantType.POTATO_MINE:
                pygame.draw.ellipse(self.screen, TAN,
                                  (icon_x - 8, icon_y - 5, 16, 12))
                                  
            # Draw cost
            cost_text = self.font.render(str(cost), True, WHITE if can_afford else GRAY)
            self.screen.blit(cost_text, (button_x + 48, button_y + 22))
            
            # Draw hotkey
            key_text = self.small_font.render(str(i + 1), True, BLACK)
            self.screen.blit(key_text, (button_x + 5, button_y + 5))
            
        # Sun counter (larger and more prominent)
        sun_x, sun_y = 30, 35
        pygame.draw.circle(self.screen, (255, 255, 150), (sun_x, sun_y), 28)
        pygame.draw.circle(self.screen, YELLOW, (sun_x, sun_y), 25)
        pygame.draw.circle(self.screen, ORANGE, (sun_x, sun_y), 25, 3)
        
        # Sun rays
        for i in range(8):
            angle = i * math.pi / 4
            x1 = sun_x + math.cos(angle) * 25
            y1 = sun_y + math.sin(angle) * 25
            x2 = sun_x + math.cos(angle) * 32
            y2 = sun_y + math.sin(angle) * 32
            pygame.draw.line(self.screen, YELLOW, (x1, y1), (x2, y2), 3)
            
        sun_text = self.font.render(str(self.sun_count), True, BLACK)
        text_rect = sun_text.get_rect(center=(sun_x, sun_y + 38))
        self.screen.blit(sun_text, text_rect)
        
        # Wave info
        wave_text = self.big_font.render(f"Wave {self.wave_number}", True, WHITE)
        self.screen.blit(wave_text, (SCREEN_WIDTH - 250, 20))
        
        zombies_left = self.zombies_to_spawn - self.zombies_spawned + len(self.zombies)
        zombie_text = self.font.render(f"Zombies: {zombies_left}", True, WHITE)
        self.screen.blit(zombie_text, (SCREEN_WIDTH - 250, 60))
        
    def draw(self):
        self.screen.fill((50, 30, 20))  # Dark brown background
        
        if self.state == GameState.MENU:
            # Title screen
            title_text = self.big_font.render("Plants vs Zombies", True, GREEN)
            title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 120))
            self.screen.blit(title_text, title_rect)
            
            subtitle = self.font.render("Replanted Edition v2.0", True, YELLOW)
            subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH//2, 170))
            self.screen.blit(subtitle, subtitle_rect)
            
            # Draw animated plants
            for i in range(5):
                x = 150 + i * 120
                plant_y = 250 + math.sin(pygame.time.get_ticks() * 0.002 + i) * 10
                
                if i == 0:  # Peashooter
                    pygame.draw.circle(self.screen, GREEN, (x, int(plant_y)), 20)
                elif i == 1:  # Sunflower
                    pygame.draw.circle(self.screen, YELLOW, (x, int(plant_y)), 15)
                    for j in range(8):
                        angle = j * math.pi / 4
                        px = x + math.cos(angle) * 25
                        py = plant_y + math.sin(angle) * 25
                        pygame.draw.circle(self.screen, YELLOW, (int(px), int(py)), 6)
                elif i == 2:  # Wallnut
                    pygame.draw.ellipse(self.screen, TAN, (x - 20, plant_y - 25, 40, 50))
                elif i == 3:  # Cherry Bomb
                    pygame.draw.circle(self.screen, RED, (x - 10, int(plant_y)), 15)
                    pygame.draw.circle(self.screen, RED, (x + 10, int(plant_y)), 15)
                elif i == 4:  # Chomper
                    pygame.draw.circle(self.screen, PURPLE, (x, int(plant_y)), 20)
            
            start_text = self.big_font.render("Press SPACE to Start", True, YELLOW)
            start_rect = start_text.get_rect(center=(SCREEN_WIDTH//2, 350))
            self.screen.blit(start_text, start_rect)
            
            controls = [
                "Controls:",
                "1-8: Select Plants | Click: Place/Collect | ESC: Pause",
                "",
                "Peashooter (100) | Sunflower (50) | Wall-nut (50) | Snow Pea (175)",
                "Repeater (200) | Chomper (150) | Cherry Bomb (150) | Potato Mine (25)",
                "",
                "Defend your lawn from 15 waves of zombies!"
            ]
            
            y = 420
            for line in controls:
                text = self.small_font.render(line, True, WHITE)
                rect = text.get_rect(center=(SCREEN_WIDTH//2, y))
                self.screen.blit(text, rect)
                y += 20
                
        elif self.state == GameState.PLAYING:
            self.draw_grid()
            
            # Draw lawnmowers
            for mower in self.lawnmowers:
                if mower.active:
                    mower.draw(self.screen)
            
            # Draw game objects
            for explosion in self.explosions:
                explosion.draw(self.screen)
                
            for plant in self.plants:
                plant.draw(self.screen)
                
            for zombie in self.zombies:
                zombie.draw(self.screen)
                
            for proj in self.projectiles:
                proj.draw(self.screen)
                
            for sun in self.suns:
                sun.draw(self.screen)
                
            self.draw_ui()
            
            # FPS counter
            fps = int(self.clock.get_fps())
            fps_text = self.small_font.render(f"FPS: {fps}", True, WHITE)
            self.screen.blit(fps_text, (10, SCREEN_HEIGHT - 25))
            
        elif self.state == GameState.PAUSED:
            self.draw_grid()
            for plant in self.plants:
                plant.draw(self.screen)
            for zombie in self.zombies:
                zombie.draw(self.screen)
                
            # Pause overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(180)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))
            
            pause_text = self.big_font.render("PAUSED", True, YELLOW)
            pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 30))
            self.screen.blit(pause_text, pause_rect)
            
            resume_text = self.font.render("Press ESC to Resume", True, WHITE)
            resume_rect = resume_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 30))
            self.screen.blit(resume_text, resume_rect)
            
        elif self.state == GameState.GAME_OVER:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.fill((80, 0, 0))
            self.screen.blit(overlay, (0, 0))
            
            game_over_text = self.big_font.render("GAME OVER", True, RED)
            game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
            self.screen.blit(game_over_text, game_over_rect)
            
            # Draw zombie animation
            zombie_x = SCREEN_WIDTH // 2
            zombie_y = SCREEN_HEIGHT // 2 + 20
            pygame.draw.circle(self.screen, (100, 150, 100), (zombie_x, zombie_y), 30)
            pygame.draw.circle(self.screen, RED, (zombie_x - 10, zombie_y - 10), 5)
            pygame.draw.circle(self.screen, RED, (zombie_x + 10, zombie_y - 10), 5)
            
            score_text = self.font.render(f"You survived {self.wave_number - 1} waves!", True, WHITE)
            score_rect = score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 80))
            self.screen.blit(score_text, score_rect)
            
            restart_text = self.font.render("Press ESC to Return to Menu", True, YELLOW)
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 120))
            self.screen.blit(restart_text, restart_rect)
            
        elif self.state == GameState.VICTORY:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.fill((0, 80, 0))
            self.screen.blit(overlay, (0, 0))
            
            victory_text = self.big_font.render("VICTORY!", True, YELLOW)
            victory_rect = victory_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
            self.screen.blit(victory_text, victory_rect)
            
            # Draw celebration plants
            for i in range(5):
                x = 200 + i * 100
                y = SCREEN_HEIGHT // 2 + 20 + math.sin(pygame.time.get_ticks() * 0.005 + i) * 20
                pygame.draw.circle(self.screen, YELLOW, (int(x), int(y)), 20)
                for j in range(8):
                    angle = j * math.pi / 4 + pygame.time.get_ticks() * 0.002
                    px = x + math.cos(angle) * 30
                    py = y + math.sin(angle) * 30
                    pygame.draw.circle(self.screen, YELLOW, (int(px), int(py)), 8)
            
            complete_text = self.font.render("You defeated all zombie waves!", True, GREEN)
            complete_rect = complete_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 80))
            self.screen.blit(complete_text, complete_rect)
            
            restart_text = self.font.render("Press ESC to Return to Menu", True, WHITE)
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 120))
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
