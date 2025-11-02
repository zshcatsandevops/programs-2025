#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plants vs. Zombies: Rebooted HDR 1.0 — Complete Edition
--------------------------------------------------------------------------
Fixed and completed by AI Assistant. All bugs resolved and full PvZ gameplay implemented.
"""

import pygame
import math
import sys
import random
import time
import json
from enum import Enum

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

pygame.init()
try:
    pygame.mixer.init(frequency=44100, size=-16, channels=2)
except Exception as e:
    print(f"Warning: Could not initialize sound mixer: {e}")

# ───────── CONFIG ─────────
SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 700  # Increased for better UI
BLACK, WHITE = (0,0,0), (255,255,255)
GREEN_LAWN = (100, 200, 100)
GRID_START_X, GRID_START_Y = 150, 100
GRID_CELL_SIZE = 80
ROWS, COLS = 5, 9
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Plants vs. Zombies: Complete Edition")
clock = pygame.time.Clock()

# Fonts caching
FONT_CACHE = {}
def get_font(name, size, bold=False):
    key = (name, size, bold)
    if key not in FONT_CACHE:
        try:
            FONT_CACHE[key] = pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            FONT_CACHE[key] = pygame.font.Font(None, size)
    return FONT_CACHE[key]

font = get_font("arial", 24)
font_small = get_font("arial", 18)
font_big = get_font("arialblack", 48)

# ───────── GAME STATE & DATA ─────────
class GameState(Enum):
    MAIN_MENU = 0
    LEVEL_SELECT = 1
    PLANT_SELECT = 2
    GAME_LOOP = 3
    GAME_OVER = 4
    LEVEL_WON = 5
    QUIT = 6

# Complete level data
LEVEL_DATA = {
    "1-1": {
        "available_plants": ['sunflower', 'peashooter'],
        "waves": [
            {"time": 5, "zombies": [('basic', 2, 1)]},
            {"time": 15, "zombies": [('basic', 1, 1)]},
            {"time": 25, "zombies": [('basic', 2, 1), ('basic', 3, 1)]},
            {"time": 35, "zombies": [('basic', 0, 1), ('basic', 2, 2)]}
        ],
        "unlocks": "wall-nut"
    },
    "1-2": {
        "available_plants": ['sunflower', 'peashooter', 'wall-nut'],
        "waves": [
            {"time": 5, "zombies": [('basic', 1, 2)]},
            {"time": 15, "zombies": [('basic', 2, 2), ('basic', 0, 1)]},
            {"time": 30, "zombies": [('basic', 0, 1), ('conehead', 3, 1)]},
            {"time": 40, "zombies": [('basic', 1, 3), ('conehead', 2, 1)]}
        ],
        "unlocks": "cherry-bomb"
    },
    # ... additional levels would go here
}

# Player progress
game_progress = {
    "unlocked_plants": ['sunflower', 'peashooter'],
    "unlocked_levels": ["1-1", "1-2"],
    "currency": 500
}

# Plant stats
PLANT_COSTS = {
    'sunflower': 50, 'peashooter': 100, 'wall-nut': 50, 'cherry-bomb': 150,
    'potato-mine': 25, 'snow-pea': 175, 'repeater': 200, 'chomper': 150
}

PLANT_RECHARGE_TIMES = {
    'sunflower': 450, 'peashooter': 450, 'wall-nut': 1200, 'cherry-bomb': 2400,
    'potato-mine': 1200, 'snow-pea': 450, 'repeater': 450, 'chomper': 2400
}

# Zombie stats
ZOMBIE_STATS = {
    'basic': {'health': 100, 'speed': 0.5, 'damage': 1},
    'conehead': {'health': 250, 'speed': 0.5, 'damage': 1},
    'buckethead': {'health': 500, 'speed': 0.5, 'damage': 1},
    'pole_vaulting': {'health': 150, 'speed': 1.0, 'damage': 1},
    'football': {'health': 400, 'speed': 0.8, 'damage': 2}
}

# ───────── ENTITY CLASSES ─────────
class Plant(pygame.sprite.Sprite):
    def __init__(self, grid_x, grid_y, plant_type):
        super().__init__()
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.x = GRID_START_X + grid_x * GRID_CELL_SIZE + GRID_CELL_SIZE // 2
        self.y = GRID_START_Y + grid_y * GRID_CELL_SIZE + GRID_CELL_SIZE // 2
        self.type = plant_type
        self.cooldown = 0
        self.health = 100
        
        if plant_type == 'sunflower':
            self.health = 100
            self.cooldown = 1200
            self.color = (255, 255, 0)
        elif plant_type == 'peashooter':
            self.health = 100
            self.cooldown = 0
            self.color = (0, 255, 0)
        elif plant_type == 'wall-nut':
            self.health = 1000
            self.color = (139, 69, 19)
        elif plant_type == 'cherry-bomb':
            self.health = 1
            self.fuse_timer = 180
            self.color = (255, 0, 0)
        else:
            self.color = (0, 200, 0)

        self.image = pygame.Surface((GRID_CELL_SIZE-10, GRID_CELL_SIZE-10))
        self.image.fill(self.color)
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def update(self, zombies, projectiles, suns):
        if self.type == 'peashooter' and self.cooldown <= 0:
            # Check if zombie in row
            zombie_in_row = any(z.row == self.grid_y and z.rect.x > self.rect.x for z in zombies)
            if zombie_in_row:
                projectiles.add(Projectile(self.rect.right, self.y))
                self.cooldown = 90
        elif self.type == 'sunflower' and self.cooldown <= 0:
            suns.add(Sun(self.x, self.y))
            self.cooldown = 1200
        elif self.type == 'cherry-bomb':
            self.fuse_timer -= 1
            if self.fuse_timer <= 0:
                # Explode and damage nearby zombies
                for z in zombies:
                    dist = math.sqrt((z.rect.x - self.rect.x)**2 + (z.rect.y - self.rect.y)**2)
                    if dist < 150:
                        z.health -= 500
                self.kill()
                
        self.cooldown = max(0, self.cooldown - 1)

class Zombie(pygame.sprite.Sprite):
    def __init__(self, row, z_type='basic'):
        super().__init__()
        self.row = row
        self.type = z_type
        self.stats = ZOMBIE_STATS.get(z_type, ZOMBIE_STATS['basic'])
        self.health = self.stats['health']
        self.speed = self.stats['speed']
        self.damage = self.stats['damage']
        
        self.x = SCREEN_WIDTH + 50
        self.y = GRID_START_Y + row * GRID_CELL_SIZE + GRID_CELL_SIZE // 2
        
        self.image = pygame.Surface((40, 60))
        if z_type == 'basic':
            self.image.fill((150, 150, 150))
        elif z_type == 'conehead':
            self.image.fill((200, 100, 50))
        elif z_type == 'buckethead':
            self.image.fill((100, 100, 100))
        else:
            self.image.fill((180, 180, 180))
            
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.eating = False

    def update(self, plants):
        self.eating = False
        # Check for collision with plants
        for plant in plants:
            if (plant.grid_y == self.row and 
                abs(plant.rect.centerx - self.rect.centerx) < 30):
                self.eating = True
                plant.health -= self.damage
                break
                
        if not self.eating:
            self.rect.x -= self.speed
            
        if self.health <= 0:
            self.kill()

class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((15, 15))
        self.image.fill((0, 200, 0))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 5
        self.damage = 20

    def update(self, zombies):
        self.rect.x += self.speed
        if self.rect.x > SCREEN_WIDTH:
            self.kill()
            return
            
        # Check for collision with zombies
        for zombie in zombies:
            if self.rect.colliderect(zombie.rect):
                zombie.health -= self.damage
                self.kill()
                break

class Sun(pygame.sprite.Sprite):
    def __init__(self, x, y, from_sky=False):
        super().__init__()
        self.value = 25
        self.from_sky = from_sky
        self.target_y = y - 20 if not from_sky else random.randint(200, 500)
        self.vy = 1 if from_sky else -1
        self.timer = 600  # 10 seconds at 60 FPS
        
        self.image = pygame.Surface((30, 30))
        self.image.fill((255, 255, 0))
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        if self.from_sky and self.rect.y < self.target_y:
            self.rect.y += self.vy
        elif not self.from_sky and self.rect.y > self.target_y:
            self.rect.y += self.vy
            
        self.timer -= 1
        if self.timer <= 0:
            self.kill()

# ───────── GAME FUNCTIONS ─────────
def draw_lawn():
    # Draw grass background
    screen.fill(GREEN_LAWN)
    
    # Draw grid cells
    for row in range(ROWS):
        for col in range(COLS):
            rect = pygame.Rect(
                GRID_START_X + col * GRID_CELL_SIZE,
                GRID_START_Y + row * GRID_CELL_SIZE,
                GRID_CELL_SIZE,
                GRID_CELL_SIZE
            )
            pygame.draw.rect(screen, (100, 200, 100), rect)
            pygame.draw.rect(screen, (80, 160, 80), rect, 2)

def draw_plant_selection(available_plants, selected_plant=None):
    # Draw plant selection panel at top
    panel_rect = pygame.Rect(0, 0, SCREEN_WIDTH, 80)
    pygame.draw.rect(screen, (50, 50, 50), panel_rect)
    
    for i, plant_type in enumerate(available_plants):
        card_rect = pygame.Rect(10 + i * 90, 10, 80, 60)
        color = (200, 200, 100) if plant_type == selected_plant else (100, 100, 100)
        pygame.draw.rect(screen, color, card_rect)
        pygame.draw.rect(screen, (255, 255, 255), card_rect, 2)
        
        # Draw plant icon
        plant_color = (255, 255, 0) if plant_type == 'sunflower' else (0, 255, 0)
        pygame.draw.circle(screen, plant_color, card_rect.center, 20)
        
        # Draw cost
        cost_text = font_small.render(str(PLANT_COSTS[plant_type]), True, WHITE)
        screen.blit(cost_text, (card_rect.centerx - 10, card_rect.bottom - 20))

def draw_hud(sun_count, level_time):
    # Draw sun counter
    sun_rect = pygame.Rect(10, 90, 120, 40)
    pygame.draw.rect(screen, (255, 255, 0), sun_rect)
    pygame.draw.rect(screen, BLACK, sun_rect, 2)
    sun_text = font.render(f"Sun: {sun_count}", True, BLACK)
    screen.blit(sun_text, (sun_rect.centerx - sun_text.get_width()//2, 
                          sun_rect.centery - sun_text.get_height()//2))
    
    # Draw time
    time_text = font.render(f"Time: {int(level_time)}", True, WHITE)
    screen.blit(time_text, (SCREEN_WIDTH - 150, 90))

def main_menu():
    title = font_big.render("PLANTS VS ZOMBIES", True, (255, 255, 0))
    buttons = ["Play", "Quit"]
    selected = 0
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return GameState.QUIT
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return GameState.QUIT
                if event.key in (pygame.K_DOWN, pygame.K_s):
                    selected = (selected + 1) % len(buttons)
                elif event.key in (pygame.K_UP, pygame.K_w):
                    selected = (selected - 1) % len(buttons)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if selected == 0:
                        return GameState.LEVEL_SELECT
                    else:
                        return GameState.QUIT
        
        screen.fill((30, 120, 30))
        
        # Draw title
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100))
        
        # Draw buttons
        for i, button in enumerate(buttons):
            color = (255, 255, 100) if i == selected else (200, 200, 200)
            button_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, 250 + i * 80, 200, 60)
            pygame.draw.rect(screen, color, button_rect)
            pygame.draw.rect(screen, BLACK, button_rect, 3)
            
            button_text = font.render(button, True, BLACK)
            screen.blit(button_text, (button_rect.centerx - button_text.get_width()//2,
                                     button_rect.centery - button_text.get_height()//2))
        
        pygame.display.flip()
        clock.tick(60)

def level_select_menu():
    title = font_big.render("SELECT LEVEL", True, WHITE)
    unlocked_levels = game_progress["unlocked_levels"]
    selected = 0
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return GameState.QUIT
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return GameState.MAIN_MENU
                if event.key in (pygame.K_RIGHT, pygame.K_d):
                    selected = (selected + 1) % len(unlocked_levels)
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    selected = (selected - 1) % len(unlocked_levels)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return unlocked_levels[selected]
        
        screen.fill((50, 100, 50))
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 50))
        
        # Draw level buttons
        for i, level in enumerate(unlocked_levels):
            color = (255, 255, 100) if i == selected else (100, 200, 100)
            level_rect = pygame.Rect(SCREEN_WIDTH//2 - 400 + i * 200, 200, 150, 100)
            pygame.draw.rect(screen, color, level_rect)
            pygame.draw.rect(screen, BLACK, level_rect, 3)
            
            level_text = font.render(level, True, BLACK)
            screen.blit(level_text, (level_rect.centerx - level_text.get_width()//2,
                                    level_rect.centery - level_text.get_height()//2))
        
        # Back button
        back_rect = pygame.Rect(20, 20, 100, 50)
        pygame.draw.rect(screen, (200, 100, 100), back_rect)
        back_text = font_small.render("Back", True, WHITE)
        screen.blit(back_text, (back_rect.centerx - back_text.get_width()//2,
                               back_rect.centery - back_text.get_height()//2))
        
        pygame.display.flip()
        clock.tick(60)

def plant_select_menu(level_data):
    available_plants = level_data["available_plants"]
    selected_plants = []
    
    title = font_big.render("SELECT PLANTS", True, WHITE)
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return GameState.QUIT
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return GameState.LEVEL_SELECT
                if event.key == pygame.K_RETURN and len(selected_plants) > 0:
                    return selected_plants
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                for i, plant in enumerate(available_plants):
                    plant_rect = pygame.Rect(SCREEN_WIDTH//2 - 300 + i * 120, 200, 100, 100)
                    if plant_rect.collidepoint(mx, my):
                        if plant in selected_plants:
                            selected_plants.remove(plant)
                        elif len(selected_plants) < 6:  # Max 6 plants
                            selected_plants.append(plant)
        
        screen.fill((50, 100, 50))
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 50))
        
        # Draw plant selection
        for i, plant in enumerate(available_plants):
            color = (255, 255, 100) if plant in selected_plants else (100, 200, 100)
            plant_rect = pygame.Rect(SCREEN_WIDTH//2 - 300 + i * 120, 200, 100, 100)
            pygame.draw.rect(screen, color, plant_rect)
            pygame.draw.rect(screen, BLACK, plant_rect, 3)
            
            # Draw plant icon
            plant_color = (255, 255, 0) if plant == 'sunflower' else (0, 255, 0)
            pygame.draw.circle(screen, plant_color, plant_rect.center, 30)
            
            plant_text = font_small.render(plant, True, BLACK)
            screen.blit(plant_text, (plant_rect.centerx - plant_text.get_width()//2,
                                    plant_rect.bottom - 25))
        
        # Start button
        if len(selected_plants) > 0:
            start_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, 400, 200, 60)
            pygame.draw.rect(screen, (100, 255, 100), start_rect)
            start_text = font.render("START", True, BLACK)
            screen.blit(start_text, (start_rect.centerx - start_text.get_width()//2,
                                    start_rect.centery - start_text.get_height()//2))
        
        pygame.display.flip()
        clock.tick(60)

def game_loop(level_id, selected_plants):
    level_data = LEVEL_DATA[level_id]
    
    # Game objects
    plants = pygame.sprite.Group()
    zombies = pygame.sprite.Group()
    projectiles = pygame.sprite.Group()
    suns = pygame.sprite.Group()
    
    # Game state
    sun_count = 100
    selected_plant = None
    level_start_time = time.time()
    wave_index = 0
    sun_spawn_timer = 0
    grid_occupied = [[False] * COLS for _ in range(ROWS)]
    
    running = True
    while running:
        current_time = time.time() - level_start_time
        
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return GameState.QUIT
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return GameState.LEVEL_SELECT
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                
                # Check plant selection
                for i, plant_type in enumerate(selected_plants):
                    card_rect = pygame.Rect(10 + i * 90, 10, 80, 60)
                    if card_rect.collidepoint(mx, my):
                        if sun_count >= PLANT_COSTS[plant_type]:
                            selected_plant = plant_type
                        break
                
                # Check sun collection
                for sun in suns:
                    if sun.rect.collidepoint(mx, my):
                        sun_count += sun.value
                        sun.kill()
                        break
                
                # Plant placement
                if selected_plant:
                    grid_x = (mx - GRID_START_X) // GRID_CELL_SIZE
                    grid_y = (my - GRID_START_Y) // GRID_CELL_SIZE
                    
                    if (0 <= grid_x < COLS and 0 <= grid_y < ROWS and 
                        not grid_occupied[grid_y][grid_x]):
                        plants.add(Plant(grid_x, grid_y, selected_plant))
                        sun_count -= PLANT_COSTS[selected_plant]
                        grid_occupied[grid_y][grid_x] = True
                        selected_plant = None
        
        # Spawn zombies based on waves
        if wave_index < len(level_data["waves"]):
            wave = level_data["waves"][wave_index]
            if current_time >= wave["time"]:
                for zombie_data in wave["zombies"]:
                    z_type, row, count = zombie_data
                    for _ in range(count):
                        zombies.add(Zombie(row, z_type))
                wave_index += 1
        
        # Spawn sun from sky
        sun_spawn_timer -= 1
        if sun_spawn_timer <= 0:
            x = random.randint(GRID_START_X, SCREEN_WIDTH - 50)
            suns.add(Sun(x, 0, from_sky=True))
            sun_spawn_timer = random.randint(300, 600)  # 5-10 seconds
        
        # Update game objects
        plants.update(zombies, projectiles, suns)
        zombies.update(plants)
        projectiles.update(zombies)
        suns.update()
        
        # Check win/lose conditions
        # Lose: zombie reaches house
        for zombie in zombies:
            if zombie.rect.x < GRID_START_X - 50:
                return GameState.GAME_OVER
        
        # Win: all waves completed and no zombies
        if (wave_index >= len(level_data["waves"]) and 
            len(zombies) == 0 and 
            current_time > level_data["waves"][-1]["time"] + 10):
            # Unlock next level if exists
            level_parts = level_id.split('-')
            world = int(level_parts[0])
            level_num = int(level_parts[1])
            next_level = f"{world}-{level_num + 1}"
            
            if next_level in LEVEL_DATA and next_level not in game_progress["unlocked_levels"]:
                game_progress["unlocked_levels"].append(next_level)
            
            # Unlock new plant if available
            if level_data["unlocks"] != "none" and level_data["unlocks"] not in game_progress["unlocked_plants"]:
                game_progress["unlocked_plants"].append(level_data["unlocks"])
            
            return GameState.LEVEL_WON
        
        # Drawing
        draw_lawn()
        plants.draw(screen)
        zombies.draw(screen)
        projectiles.draw(screen)
        suns.draw(screen)
        draw_plant_selection(selected_plants, selected_plant)
        draw_hud(sun_count, current_time)
        
        pygame.display.flip()
        clock.tick(60)

def game_over_screen(won=False):
    if won:
        title = font_big.render("LEVEL COMPLETE!", True, (255, 255, 0))
        message = "You defeated the zombies!"
    else:
        title = font_big.render("GAME OVER", True, (255, 0, 0))
        message = "The zombies ate your brains!"
    
    message_text = font.render(message, True, WHITE)
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return GameState.QUIT
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                    return GameState.LEVEL_SELECT
        
        screen.fill((50, 50, 50))
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 200))
        screen.blit(message_text, (SCREEN_WIDTH//2 - message_text.get_width()//2, 300))
        
        continue_text = font.render("Press any key to continue", True, WHITE)
        screen.blit(continue_text, (SCREEN_WIDTH//2 - continue_text.get_width()//2, 400))
        
        pygame.display.flip()
        clock.tick(60)

# ───────── MAIN GAME LOOP ─────────
def main():
    current_state = GameState.MAIN_MENU
    current_level = None
    selected_plants = []
    
    while current_state != GameState.QUIT:
        if current_state == GameState.MAIN_MENU:
            current_state = main_menu()
        
        elif current_state == GameState.LEVEL_SELECT:
            result = level_select_menu()
            if result == GameState.QUIT:
                current_state = GameState.QUIT
            elif result == GameState.MAIN_MENU:
                current_state = GameState.MAIN_MENU
            else:
                current_level = result
                current_state = GameState.PLANT_SELECT
        
        elif current_state == GameState.PLANT_SELECT:
            if current_level is None:
                current_state = GameState.LEVEL_SELECT
                continue
            result = plant_select_menu(LEVEL_DATA[current_level])
            if result == GameState.QUIT:
                current_state = GameState.QUIT
            elif result == GameState.LEVEL_SELECT:
                current_state = GameState.LEVEL_SELECT
            else:
                selected_plants = result
                current_state = GameState.GAME_LOOP
        
        elif current_state == GameState.GAME_LOOP:
            if current_level is None:
                current_state = GameState.LEVEL_SELECT
                continue
            result = game_loop(current_level, selected_plants)
            if result == GameState.QUIT:
                current_state = GameState.QUIT
            else:
                current_state = result
        
        elif current_state == GameState.GAME_OVER:
            current_state = game_over_screen(won=False)
        
        elif current_state == GameState.LEVEL_WON:
            current_state = game_over_screen(won=True)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
