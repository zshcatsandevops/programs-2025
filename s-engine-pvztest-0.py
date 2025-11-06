#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ultra PVZ SexyEngine 3.0 — Replanted Edition
=============================================
A complete PvZ engine with SexyEngine architecture patterns.
Now with happy zombie faces and enhanced graphics!

Features:
- SexyEngine-style resource management and rendering
- Happy smiling zombies (they're just hungry, not mean!)
- Enhanced particle effects and animations
- PopCap-quality polish and game feel
- Complete PvZ Replanted mechanics

(With fixes and smiles added!)
"""

import math
import random
import sys
import time
import os
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any
from enum import Enum

import pygame

# SexyEngine-style initialization
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

# -----------------------------------------------------------------------------
# SexyEngine Framework Core
# -----------------------------------------------------------------------------
class SexyEngine:
    """Core engine following PopCap's SexyFramework patterns"""
    
    class Resources:
        """Resource manager for game assets"""
        _cache: Dict[str, Any] = {}
        
        @classmethod
        def get_color(cls, name: str) -> tuple:
            colors = {
                'lawn_green': (90, 170, 90),
                'lawn_dark': (70, 150, 70),
                'sky_blue': (135, 206, 235),
                'sun_yellow': (255, 240, 100),
                'sun_glow': (255, 255, 180),
                'zombie_skin': (180, 175, 170),
                'zombie_happy': (255, 200, 200),
                'plant_green': (100, 200, 100),
                'pea_green': (150, 255, 150),
                'nut_brown': (180, 130, 80),
                'ui_panel': (70, 140, 70),
                'ui_dark': (50, 100, 50),
                'text_white': (248, 248, 248),
                'text_yellow': (255, 240, 100),
                'button_blue': (100, 170, 210),
                'button_hover': (140, 210, 250),
                'particle_sparkle': (255, 255, 200),
            }
            return colors.get(name, (255, 255, 255))
    
    class Particle:
        """Particle system for visual effects"""
        def __init__(self, x, y, vx, vy, color, size, lifetime):
            self.x, self.y = float(x), float(y)
            self.vx, self.vy = vx, vy
            self.color = color
            self.size = size
            self.lifetime = lifetime
            self.age = 0.0
            self.alive = True
            
        def update(self, dt):
            self.age += dt
            if self.age >= self.lifetime:
                self.alive = False
                return
            self.x += self.vx * dt
            self.y += self.vy * dt
            self.vy += 180 * dt  # gravity
            
        def draw(self, surface):
            alpha = 1.0 - (self.age / self.lifetime)
            size = int(self.size * (1.0 - self.age / self.lifetime * 0.5))
            if size > 0:
                pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), size)

class PopCapAnimation:
    """Animation system with easing and juice"""
    
    @staticmethod
    def ease_out_back(t: float) -> float:
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)
    
    @staticmethod
    def ease_in_out_quad(t: float) -> float:
        return 2 * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 2) / 2
    
    @staticmethod
    def bounce(t: float) -> float:
        return abs(math.sin(t * math.pi * 4)) * (1 - t)

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
class Config:
    # Window
    WIDTH = 1024
    HEIGHT = 600
    FPS = 60
    TITLE = "Plants vs Zombies: Replanted (SexyEngine Edition)"
    
    # Grid
    ROWS = 5
    COLS = 9
    CELL_WIDTH = 80
    CELL_HEIGHT = 100
    GRID_LEFT = 240
    GRID_TOP = 85
    
    # Economy
    STARTING_SUN = 150
    SUN_VALUE = 25
    SKY_SUN_INTERVAL = (8.0, 12.0)
    
    # Gameplay
    DIFFICULTY = 1.0
    WAVE_INTERVAL = 20.0
    ZOMBIE_SPAWN_RATE = 5.0
    VICTORY_TIME = 120.0 # 2 minutes

CFG = Config()

# -----------------------------------------------------------------------------
# Initialize Pygame
# -----------------------------------------------------------------------------
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
screen = pygame.display.set_mode((CFG.WIDTH, CFG.HEIGHT))
pygame.display.set_caption(CFG.TITLE)
clock = pygame.time.Clock()

# Fonts with fallback
def get_font(size, bold=False):
    fonts = ['Arial', 'Helvetica', 'DejaVuSans', 'FreeSans']
    for font_name in fonts:
        try:
            return pygame.font.SysFont(font_name, size, bold=bold)
        except:
            continue
    return pygame.font.Font(None, size)

FONT_SMALL = get_font(16)
FONT_MEDIUM = get_font(20)
FONT_LARGE = get_font(28, bold=True)
FONT_HUGE = get_font(48, bold=True)

# -----------------------------------------------------------------------------
# Sound System (Procedural)
# -----------------------------------------------------------------------------
class SoundEngine:
    """Procedural sound generation"""
    
    @staticmethod
    def generate_tone(frequency, duration, sample_rate=44100):
        frames = int(duration * sample_rate)
        arr = []
        for i in range(frames):
            t = i / sample_rate
            # Add harmonics for richer sound
            sample = (math.sin(2 * math.pi * frequency * t) * 0.5 +
                      math.sin(4 * math.pi * frequency * t) * 0.25 +
                      math.sin(8 * math.pi * frequency * t) * 0.125)
            # Envelope
            envelope = min(1.0, i / (sample_rate * 0.01))  # Attack
            if i > frames - sample_rate * 0.1:  # Release
                envelope *= (frames - i) / (sample_rate * 0.1)
            arr.append(int(sample * envelope * 16384))
        
        import array
        sound_array = array.array('h', arr)
        sound = pygame.mixer.Sound(buffer=sound_array.tobytes())
        sound.set_volume(0.3)
        return sound
    
    @staticmethod
    def init_sounds():
        sounds = {}
        try:
            sounds['plant'] = SoundEngine.generate_tone(440, 0.1)  # A4
            sounds['shoot'] = SoundEngine.generate_tone(880, 0.05)  # A5
            sounds['hit'] = SoundEngine.generate_tone(220, 0.1)  # A3
            sounds['sun'] = SoundEngine.generate_tone(660, 0.15)  # E5
            sounds['chomp'] = SoundEngine.generate_tone(110, 0.15)  # A2
        except Exception as e:
            print(f"Warning: Could not initialize procedural sounds. {e}")
        return sounds

SOUNDS = SoundEngine.init_sounds()

def play_sound(name):
    if name in SOUNDS:
        try:
            SOUNDS[name].play()
        except:
            pass

# -----------------------------------------------------------------------------
# Enhanced Drawing Functions
# -----------------------------------------------------------------------------
def draw_text(surface, text, pos, color=None, font=None, center=False, shadow=True):
    if color is None:
        color = SexyEngine.Resources.get_color('text_white')
    if font is None:
        font = FONT_MEDIUM
    
    # Shadow for depth
    if shadow:
        shadow_surf = font.render(text, True, (0, 0, 0, 150))
        shadow_pos = (pos[0] + 2, pos[1] + 2)
        if center:
            # FIX: Use the original pos for centering, not the modified shadow_pos
            shadow_rect = shadow_surf.get_rect(center=shadow_pos)
            surface.blit(shadow_surf, shadow_rect)
        else:
            surface.blit(shadow_surf, shadow_pos)
    
    # Main text
    text_surf = font.render(text, True, color)
    if center:
        text_rect = text_surf.get_rect(center=pos)
        surface.blit(text_surf, text_rect)
    else:
        surface.blit(text_surf, pos)

def draw_button(surface, rect, text, hovered=False, pressed=False):
    # Button with PopCap-style polish
    color = SexyEngine.Resources.get_color('button_hover' if hovered else 'button_blue')
    
    # Shadow
    shadow_rect = rect.copy()
    shadow_rect.y += 4
    pygame.draw.rect(surface, (0, 0, 0, 128), shadow_rect, border_radius=12)
    
    # Button body
    if pressed:
        rect.y += 2
    pygame.draw.rect(surface, color, rect, border_radius=12)
    
    # Gradient effect (top highlight)
    highlight_rect = rect.copy()
    highlight_rect.height = rect.height // 3
    highlight_surf = pygame.Surface((highlight_rect.width, highlight_rect.height), pygame.SRCALPHA)
    highlight_surf.fill((255, 255, 255, 40))
    surface.blit(highlight_surf, highlight_rect, special_flags=pygame.BLEND_ADD)
    
    # Border
    pygame.draw.rect(surface, (255, 255, 255, 128), rect, width=2, border_radius=12)
    
    # Text
    draw_text(surface, text, rect.center, color=(255, 255, 255), center=True)

# -----------------------------------------------------------------------------
# Enhanced Plant/Zombie Drawing with Happy Faces
# -----------------------------------------------------------------------------
def draw_happy_zombie(surface, rect, t, zombie_type='normal'):
    """Draw a happy, smiling zombie!"""
    cx, cy = rect.center
    
    # Body bounce animation
    bounce = int(4 * math.sin(t * 3))
    
    # Body
    body_color = SexyEngine.Resources.get_color('zombie_skin')
    body_rect = pygame.Rect(cx - 25, cy - 20 + bounce, 50, 60)
    pygame.draw.ellipse(surface, body_color, body_rect)
    
    # Head
    head_color = SexyEngine.Resources.get_color('zombie_happy')
    head_rect = pygame.Rect(cx - 20, cy - 35 + bounce, 40, 40)
    pygame.draw.ellipse(surface, head_color, head_rect)
    
    # Happy eyes (^_^)
    eye_y = cy - 25 + bounce
    pygame.draw.arc(surface, (0, 0, 0), 
                    (cx - 12, eye_y - 5, 10, 10), 
                    0, math.pi, 3)
    pygame.draw.arc(surface, (0, 0, 0), 
                    (cx + 2, eye_y - 5, 10, 10), 
                    0, math.pi, 3)
    
    # Big smile :D
    smile_rect = pygame.Rect(cx - 15, cy - 20 + bounce, 30, 20)
    pygame.draw.arc(surface, (0, 0, 0), smile_rect, 0.2, math.pi - 0.2, 3)
    
    # Rosy cheeks
    pygame.draw.circle(surface, (255, 180, 180), (cx - 15, cy - 15 + bounce), 5)
    pygame.draw.circle(surface, (255, 180, 180), (cx + 15, cy - 15 + bounce), 5)
    
    # Hat for conehead
    if zombie_type == 'cone':
        cone_points = [
            (cx, cy - 50 + bounce),
            (cx - 15, cy - 30 + bounce),
            (cx + 15, cy - 30 + bounce)
        ]
        pygame.draw.polygon(surface, (255, 140, 0), cone_points)
        pygame.draw.polygon(surface, (200, 100, 0), cone_points, 2)
    elif zombie_type == 'bucket':
        bucket_rect = pygame.Rect(cx - 18, cy - 50 + bounce, 36, 25)
        pygame.draw.rect(surface, (150, 150, 150), bucket_rect, border_radius=4)
        pygame.draw.rect(surface, (100, 100, 100), bucket_rect, width=2, border_radius=4)
    
    # Arms waving happily
    arm_swing = int(10 * math.sin(t * 4))
    pygame.draw.line(surface, body_color, 
                     (cx - 20, cy + bounce), 
                     (cx - 30 + arm_swing, cy - 10 + bounce), 4)
    pygame.draw.line(surface, body_color, 
                     (cx + 20, cy + bounce), 
                     (cx + 30 - arm_swing, cy - 10 + bounce), 4)

def draw_peashooter(surface, rect, t):
    """Enhanced peashooter with personality"""
    cx, cy = rect.center
    
    # Stem
    stem_rect = pygame.Rect(cx - 8, cy + 10, 16, 30)
    pygame.draw.ellipse(surface, SexyEngine.Resources.get_color('plant_green'), stem_rect)
    
    # Head (pulsing slightly)
    pulse = 1 + 0.05 * math.sin(t * 2)
    head_size = int(30 * pulse)
    pygame.draw.circle(surface, SexyEngine.Resources.get_color('pea_green'), (cx, cy - 5), head_size)
    
    # Mouth (cannon)
    pygame.draw.circle(surface, (50, 100, 50), (cx + 15, cy - 5), 8)
    pygame.draw.circle(surface, (0, 0, 0), (cx + 15, cy - 5), 5)
    
    # Eyes
    pygame.draw.circle(surface, (255, 255, 255), (cx - 8, cy - 12), 6)
    pygame.draw.circle(surface, (255, 255, 255), (cx + 2, cy - 12), 6)
    pygame.draw.circle(surface, (0, 0, 0), (cx - 6, cy - 11), 3)
    pygame.draw.circle(surface, (0, 0, 0), (cx + 4, cy - 11), 3)
    
    # Happy smile
    pygame.draw.arc(surface, (0, 0, 0), (cx - 10, cy - 8, 20, 10), 0.2, math.pi - 0.2, 2)
    
    # Leaf details
    leaf_points = [(cx - 20, cy + 5), (cx - 25, cy + 15), (cx - 15, cy + 15)]
    pygame.draw.polygon(surface, SexyEngine.Resources.get_color('plant_green'), leaf_points)

def draw_sunflower(surface, rect, t):
    """Happy sunflower with rotation"""
    cx, cy = rect.center
    
    # Rotating petals
    petal_color = SexyEngine.Resources.get_color('sun_yellow')
    for i in range(16):
        angle = i * (math.pi * 2 / 16) + t * 0.5
        px = cx + int(math.cos(angle) * 25)
        py = cy + int(math.sin(angle) * 25)
        pygame.draw.circle(surface, petal_color, (px, py), 8)
    
    # Face
    face_color = (180, 140, 60)
    pygame.draw.circle(surface, face_color, (cx, cy), 18)
    
    # Happy face
    pygame.draw.circle(surface, (0, 0, 0), (cx - 6, cy - 4), 3)
    pygame.draw.circle(surface, (0, 0, 0), (cx + 6, cy - 4), 3)
    pygame.draw.arc(surface, (0, 0, 0), (cx - 8, cy - 2, 16, 12), 0.3, math.pi - 0.3, 2)
    
    # Stem
    pygame.draw.rect(surface, SexyEngine.Resources.get_color('plant_green'), 
                     (cx - 6, cy + 18, 12, 30), border_radius=6)

def draw_wallnut(surface, rect, t):
    """Tough, but happy wallnut"""
    cx, cy = rect.center
    
    # Nut body
    nut_color = SexyEngine.Resources.get_color('nut_brown')
    pygame.draw.ellipse(surface, nut_color, rect.inflate(-10, -10))
    
    # Texture lines
    for i in range(3):
        y = cy - 15 + i * 15
        pygame.draw.arc(surface, (140, 100, 60), 
                        (cx - 25, y - 5, 50, 10), 0, math.pi, 2)
    
    # Happy determined face
    pygame.draw.circle(surface, (0, 0, 0), (cx - 10, cy - 8), 4)
    pygame.draw.circle(surface, (0, 0, 0), (cx + 10, cy - 8), 4)
    
    # Big happy smile
    smile_rect = pygame.Rect(cx - 15, cy, 30, 20)
    pygame.draw.arc(surface, (0, 0, 0), smile_rect, 0.2, math.pi - 0.2, 3)

def draw_sun(surface, pos, radius, t):
    """Animated sun with glow effect"""
    x, y = pos
    
    # Glow effect
    for i in range(3):
        glow_radius = radius + 10 + i * 5
        glow_alpha = 60 - i * 20
        glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*SexyEngine.Resources.get_color('sun_glow'), glow_alpha), 
                           (glow_radius, glow_radius), glow_radius)
        surface.blit(glow_surf, (x - glow_radius, y - glow_radius))
    
    # Main sun
    pygame.draw.circle(surface, SexyEngine.Resources.get_color('sun_yellow'), (x, y), radius)
    
    # Happy face
    pygame.draw.circle(surface, (0, 0, 0), (x - radius//3, y - radius//3), 2)
    pygame.draw.circle(surface, (0, 0, 0), (x + radius//3, y - radius//3), 2)
    pygame.draw.arc(surface, (0, 0, 0), 
                    (x - radius//2, y - radius//3, radius, radius//2), 
                    0.3, math.pi - 0.3, 2)

# -----------------------------------------------------------------------------
# Game Entities
# -----------------------------------------------------------------------------
class Plant:
    def __init__(self, col, row, plant_type):
        self.col = col
        self.row = row
        self.type = plant_type
        self.hp = self.max_hp = {'peashooter': 300, 'sunflower': 250, 'wallnut': 1200}[plant_type]
        self.timer = 0.0
        self.alive = True
        self.rect = pygame.Rect(CFG.GRID_LEFT + col * CFG.CELL_WIDTH,
                                CFG.GRID_TOP + row * CFG.CELL_HEIGHT,
                                CFG.CELL_WIDTH, CFG.CELL_HEIGHT)
        
    def update(self, dt, game_state):
        self.timer += dt
        
        if self.type == 'peashooter':
            if self.timer >= 1.5:
                # Check for zombies in lane
                for zombie in game_state.zombies:
                    if zombie.row == self.row and zombie.x > self.rect.centerx:
                        game_state.projectiles.append(
                            Projectile(self.rect.centerx + 20, self.rect.centery - 5, 'pea')
                        )
                        play_sound('shoot')
                        self.timer = 0.0
                        break
                        
        elif self.type == 'sunflower':
            if self.timer >= 8.0:
                sun_x = self.rect.centerx + random.randint(-20, 20)
                sun_y = self.rect.centery
                game_state.suns.append(Sun(sun_x, sun_y, stationary=True))
                self.timer = 0.0
    
    def draw(self, surface, t):
        if self.type == 'peashooter':
            draw_peashooter(surface, self.rect, t)
        elif self.type == 'sunflower':
            draw_sunflower(surface, self.rect, t)
        elif self.type == 'wallnut':
            draw_wallnut(surface, self.rect, t)
        
        # Health bar if damaged
        if self.hp < self.max_hp:
            bar_rect = pygame.Rect(self.rect.x, self.rect.bottom - 8, self.rect.width, 4)
            pygame.draw.rect(surface, (100, 0, 0), bar_rect)
            fill_width = int(bar_rect.width * (self.hp / self.max_hp))
            pygame.draw.rect(surface, (0, 200, 0), (bar_rect.x, bar_rect.y, fill_width, bar_rect.height))

class Zombie:
    def __init__(self, row, zombie_type='normal'):
        self.row = row
        self.type = zombie_type
        self.x = float(CFG.WIDTH + 20)
        self.y = float(CFG.GRID_TOP + row * CFG.CELL_HEIGHT + CFG.CELL_HEIGHT // 2)
        self.hp = self.max_hp = {'normal': 200, 'cone': 370, 'bucket': 650}[zombie_type]
        self.speed = 15.0
        self.eating = False
        self.eat_target = None
        self.animation_time = random.random() * math.pi * 2
        self.rect = pygame.Rect(int(self.x) - 30, int(self.y) - 40, 60, 80)
        
    def update(self, dt, game_state):
        self.animation_time += dt
        
        # Check for plants to eat
        self.eating = False
        self.eat_target = None
        for plant in game_state.plants:
            if plant.row == self.row and plant.alive:
                if abs(self.x - plant.rect.centerx) < 40:
                    self.eating = True
                    self.eat_target = plant
                    plant.hp -= 30 * dt  # Eating damage
                    if plant.hp <= 0:
                        plant.alive = False
                        play_sound('chomp')
                    break
        
        # Move if not eating
        if not self.eating:
            self.x -= self.speed * dt
            
        self.rect.x = int(self.x) - 30
        self.rect.y = int(self.y) - 40
    
    def draw(self, surface, t):
        draw_happy_zombie(surface, self.rect, self.animation_time + t, self.type)
        
        # Health bar
        if self.hp < self.max_hp:
            bar_rect = pygame.Rect(self.rect.x, self.rect.y - 10, self.rect.width, 4)
            pygame.draw.rect(surface, (100, 0, 0), bar_rect)
            fill_width = int(bar_rect.width * (self.hp / self.max_hp))
            pygame.draw.rect(surface, (200, 0, 0), (bar_rect.x, bar_rect.y, fill_width, bar_rect.height))

class Projectile:
    def __init__(self, x, y, proj_type='pea'):
        self.x = float(x)
        self.y = float(y)
        self.type = proj_type
        self.speed = 200.0
        self.damage = {'pea': 20, 'snow': 20, 'fire': 40}[proj_type]
        self.rect = pygame.Rect(int(self.x) - 8, int(self.y) - 8, 16, 16)
        
    def update(self, dt, game_state):
        self.x += self.speed * dt
        self.rect.x = int(self.x) - 8
        self.rect.y = int(self.y) - 8
        
        # Check zombie collisions
        for zombie in game_state.zombies:
            if zombie.row == int((self.y - CFG.GRID_TOP) // CFG.CELL_HEIGHT):
                if self.rect.colliderect(zombie.rect):
                    zombie.hp -= self.damage
                    play_sound('hit')
                    
                    # Particle effect
                    for _ in range(5):
                        vx = random.uniform(-50, 50)
                        vy = random.uniform(-100, -50)
                        color = SexyEngine.Resources.get_color('pea_green')
                        game_state.particles.append(
                            SexyEngine.Particle(self.x, self.y, vx, vy, color, 3, 0.5)
                        )
                    
                    return True  # Remove this projectile
        
        return self.x > CFG.WIDTH + 50  # Remove if off-screen
    
    def draw(self, surface):
        color = {'pea': SexyEngine.Resources.get_color('pea_green'),
                 'snow': (150, 200, 255),
                 'fire': (255, 150, 50)}[self.type]
        pygame.draw.circle(surface, color, self.rect.center, 8)
        pygame.draw.circle(surface, (255, 255, 255), 
                           (self.rect.centerx - 2, self.rect.centery - 2), 2)

class Sun:
    def __init__(self, x, y, stationary=False):
        self.x = float(x)
        self.y = float(y)
        self.target_y = y + random.randint(50, 150) if not stationary else y
        self.vy = 0.0 if stationary else 30.0
        self.lifetime = 10.0
        self.value = CFG.SUN_VALUE
        self.rect = pygame.Rect(int(self.x) - 20, int(self.y) - 20, 40, 40)
        self.collected = False
        
    def update(self, dt):
        if self.y < self.target_y:
            self.y += self.vy * dt
            if self.y >= self.target_y:
                self.y = self.target_y
                
        self.lifetime -= dt
        self.rect.center = (int(self.x), int(self.y))
        
        return self.lifetime <= 0  # Return True if expired
    
    def draw(self, surface, t):
        # Pulsing effect
        pulse = 1.0 + 0.1 * math.sin(t * 3)
        radius = int(20 * pulse)
        draw_sun(surface, self.rect.center, radius, t)

class LawnMower:
    def __init__(self, row):
        self.row = row
        self.x = CFG.GRID_LEFT - 80
        self.y = CFG.GRID_TOP + row * CFG.CELL_HEIGHT + CFG.CELL_HEIGHT // 2
        self.activated = False
        self.speed = 0.0
        self.rect = pygame.Rect(self.x - 30, self.y - 20, 60, 40)
        
    def activate(self):
        if not self.activated:
            self.activated = True
            self.speed = 400.0
            
    def update(self, dt, game_state):
        if self.activated:
            self.x += self.speed * dt
            self.rect.x = int(self.x) - 30
            
            # Mow down zombies
            for zombie in list(game_state.zombies):
                if zombie.row == self.row and self.rect.colliderect(zombie.rect):
                    game_state.zombies.remove(zombie)
                    # Particle effect
                    for _ in range(10):
                        vx = random.uniform(-100, 100)
                        vy = random.uniform(-150, -50)
                        color = SexyEngine.Resources.get_color('zombie_skin')
                        game_state.particles.append(
                            SexyEngine.Particle(zombie.x, zombie.y, vx, vy, color, 5, 1.0)
                        )
            
            return self.x > CFG.WIDTH + 100  # Return True if off-screen
        
        # Check if zombie reached the mower
        for zombie in game_state.zombies:
            if zombie.row == self.row and zombie.x <= self.x + 40:
                self.activate()
                
        return False
    
    def draw(self, surface):
        # Mower body
        color = (180, 50, 50) if not self.activated else (255, 100, 100)
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        
        # Blade
        blade_rect = pygame.Rect(self.rect.right - 15, self.rect.y + 5, 20, 30)
        pygame.draw.ellipse(surface, (200, 200, 200), blade_rect)
        
        # Wheels
        for i in range(2):
            wheel_x = self.rect.x + 10 + i * 30
            pygame.draw.circle(surface, (50, 50, 50), (wheel_x, self.rect.bottom), 8)

# -----------------------------------------------------------------------------
# Game State Manager
# -----------------------------------------------------------------------------
class GameState:
    def __init__(self):
        self.plants = []
        self.zombies = []
        self.projectiles = []
        self.suns = []
        self.lawn_mowers = [LawnMower(row) for row in range(CFG.ROWS)]
        self.particles = []
        
        self.sun_bank = CFG.STARTING_SUN
        self.selected_plant = None
        self.shovel_mode = False
        
        self.wave_timer = 0.0
        self.spawn_timer = random.uniform(3.0, 6.0)
        self.sky_sun_timer = random.uniform(*CFG.SKY_SUN_INTERVAL)
        self.game_time = 0.0
        
        self.paused = False
        self.game_over = False
        self.victory = False
        self.victory_time = CFG.VICTORY_TIME
        
        # Plant costs and cooldowns
        self.plant_costs = {'peashooter': 100, 'sunflower': 50, 'wallnut': 50}
        self.plant_cooldowns = {'peashooter': 0.0, 'sunflower': 0.0, 'wallnut': 0.0}
        self.cooldown_times = {'peashooter': 7.5, 'sunflower': 7.5, 'wallnut': 30.0}
    
    def can_afford_plant(self, plant_type):
        return self.sun_bank >= self.plant_costs[plant_type] and self.plant_cooldowns[plant_type] <= 0
    
    def place_plant(self, col, row, plant_type):
        # Check if tile is empty
        for plant in self.plants:
            if plant.col == col and plant.row == row and plant.alive:
                return False
        
        if self.can_afford_plant(plant_type):
            self.plants.append(Plant(col, row, plant_type))
            self.sun_bank -= self.plant_costs[plant_type]
            self.plant_cooldowns[plant_type] = self.cooldown_times[plant_type]
            play_sound('plant')
            return True
        return False
    
    def remove_plant(self, col, row):
        for plant in self.plants:
            if plant.col == col and plant.row == row and plant.alive:
                plant.alive = False
                # Give back some sun
                self.sun_bank += self.plant_costs[plant.type] // 4
                return True
        return False
    
    def update(self, dt):
        if self.paused or self.game_over or self.victory:
            return
        
        self.game_time += dt
        
        # Update cooldowns
        for plant_type in self.plant_cooldowns:
            if self.plant_cooldowns[plant_type] > 0:
                self.plant_cooldowns[plant_type] -= dt
        
        # Spawn sky suns
        self.sky_sun_timer -= dt
        if self.sky_sun_timer <= 0:
            x = random.randint(CFG.GRID_LEFT, CFG.GRID_LEFT + CFG.COLS * CFG.CELL_WIDTH)
            self.suns.append(Sun(x, -30, stationary=False))
            self.sky_sun_timer = random.uniform(*CFG.SKY_SUN_INTERVAL)
        
        # Spawn zombies (if before victory time)
        self.spawn_timer -= dt
        if self.game_time < self.victory_time and self.spawn_timer <= 0:
            row = random.randint(0, CFG.ROWS - 1)
            # Increase difficulty over time
            zombie_type = 'normal'
            if self.game_time > 30 and random.random() < 0.3:
                zombie_type = 'cone'
            elif self.game_time > 60 and random.random() < 0.15:
                zombie_type = 'bucket'
            
            self.zombies.append(Zombie(row, zombie_type))
            self.spawn_timer = random.uniform(3.0, 7.0) / (1 + self.game_time / 60)
        
        # Update entities
        self.plants = [p for p in self.plants if p.alive]
        for plant in self.plants:
            plant.update(dt, self)
        
        # Update projectiles
        new_projectiles = []
        for proj in self.projectiles:
            if not proj.update(dt, self):
                new_projectiles.append(proj)
        self.projectiles = new_projectiles
        
        # Update zombies
        self.zombies = [z for z in self.zombies if z.hp > 0]
        for zombie in self.zombies:
            zombie.update(dt, self)
            # Check for game over
            if zombie.x < CFG.GRID_LEFT - 100:
                self.game_over = True
        
        # Update suns
        new_suns = []
        for sun in self.suns:
            if not sun.update(dt) and not sun.collected:
                new_suns.append(sun)
        self.suns = new_suns
        
        # Update lawn mowers
        new_mowers = []
        for mower in self.lawn_mowers:
            if not mower.update(dt, self):
                new_mowers.append(mower)
        self.lawn_mowers = new_mowers
        
        # Update particles
        self.particles = [p for p in self.particles if p.alive]
        for particle in self.particles:
            particle.update(dt)
        
        # Check for victory
        if not self.victory and self.game_time >= self.victory_time:
            # Check if all zombies are cleared
            if not self.zombies:
                self.victory = True
                # Victory particle burst
                for _ in range(100):
                    vx = random.uniform(-300, 300)
                    vy = random.uniform(-500, -100)
                    color = random.choice([SexyEngine.Resources.get_color('sun_yellow'),
                                           SexyEngine.Resources.get_color('pea_green'),
                                           SexyEngine.Resources.get_color('button_blue')])
                    self.particles.append(
                        SexyEngine.Particle(CFG.WIDTH // 2, CFG.HEIGHT // 2, vx, vy, color, 8, 3.0)
                    )
    
    def handle_click(self, x, y):
        # Check sun collection
        for sun in self.suns:
            if not sun.collected and sun.rect.collidepoint(x, y):
                sun.collected = True
                self.sun_bank += sun.value
                play_sound('sun')
                # Particle effect
                for _ in range(10):
                    vx = random.uniform(-100, 100)
                    vy = random.uniform(-100, 100)
                    color = SexyEngine.Resources.get_color('sun_yellow')
                    self.particles.append(
                        SexyEngine.Particle(sun.x, sun.y, vx, vy, color, 4, 0.5)
                    )
                return
        
        # Check grid placement
        if CFG.GRID_LEFT <= x < CFG.GRID_LEFT + CFG.COLS * CFG.CELL_WIDTH:
            if CFG.GRID_TOP <= y < CFG.GRID_TOP + CFG.ROWS * CFG.CELL_HEIGHT:
                col = (x - CFG.GRID_LEFT) // CFG.CELL_WIDTH
                row = (y - CFG.GRID_TOP) // CFG.CELL_HEIGHT
                
                if self.shovel_mode:
                    self.remove_plant(col, row)
                elif self.selected_plant:
                    self.place_plant(col, row, self.selected_plant)

# -----------------------------------------------------------------------------
# UI Components
# -----------------------------------------------------------------------------
class PlantSelector:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.cards = [
            {'type': 'sunflower', 'icon': draw_sunflower},
            {'type': 'peashooter', 'icon': draw_peashooter},
            {'type': 'wallnut', 'icon': draw_wallnut},
        ]
        self.card_width = 70
        self.card_height = 90
        self.spacing = 5
        
    def draw(self, surface, game_state, t):
        for i, card in enumerate(self.cards):
            x = self.x + i * (self.card_width + self.spacing)
            rect = pygame.Rect(x, self.y, self.card_width, self.card_height)
            
            # Card background
            can_afford = game_state.can_afford_plant(card['type'])
            selected = game_state.selected_plant == card['type']
            
            if selected:
                pygame.draw.rect(surface, SexyEngine.Resources.get_color('sun_yellow'), rect, border_radius=8)
            elif can_afford:
                pygame.draw.rect(surface, SexyEngine.Resources.get_color('ui_panel'), rect, border_radius=8)
            else:
                pygame.draw.rect(surface, SexyEngine.Resources.get_color('ui_dark'), rect, border_radius=8)
            
            # Border
            pygame.draw.rect(surface, (0, 0, 0, 100), rect, width=2, border_radius=8)
            
            # Icon
            icon_rect = pygame.Rect(x + 10, self.y + 10, self.card_width - 20, 50)
            card['icon'](surface, icon_rect, t)
            
            # Cost
            cost = game_state.plant_costs[card['type']]
            cost_text = str(cost)
            draw_text(surface, cost_text, (x + self.card_width // 2, self.y + 75),
                      color=SexyEngine.Resources.get_color('sun_yellow'), center=True, font=FONT_MEDIUM)
            
            # Cooldown overlay
            cooldown = game_state.plant_cooldowns[card['type']]
            max_cooldown = game_state.cooldown_times[card['type']]
            if cooldown > 0:
                overlay_height = int(rect.height * (cooldown / max_cooldown))
                overlay_rect = pygame.Rect(rect.x, rect.y, rect.width, overlay_height)
                overlay_surf = pygame.Surface((overlay_rect.width, overlay_rect.height), pygame.SRCALPHA)
                overlay_surf.fill((0, 0, 0, 180))
                surface.blit(overlay_surf, overlay_rect)
    
    def handle_click(self, x, y, game_state):
        for i, card in enumerate(self.cards):
            card_x = self.x + i * (self.card_width + self.spacing)
            rect = pygame.Rect(card_x, self.y, self.card_width, self.card_height)
            if rect.collidepoint(x, y):
                if game_state.can_afford_plant(card['type']):
                    game_state.selected_plant = card['type']
                    game_state.shovel_mode = False
                return True
        return False

# -----------------------------------------------------------------------------
# Main Menu
# -----------------------------------------------------------------------------
class MainMenu:
    def __init__(self):
        self.buttons = [
            {'text': 'Start Game', 'rect': pygame.Rect(CFG.WIDTH // 2 - 100, 250, 200, 50)},
            {'text': 'Options', 'rect': pygame.Rect(CFG.WIDTH // 2 - 100, 320, 200, 50)},
            {'text': 'Quit', 'rect': pygame.Rect(CFG.WIDTH // 2 - 100, 390, 200, 50)},
        ]
        self.particles = []
        self.animation_time = 0.0
    
    def update(self, dt):
        self.animation_time += dt
        
        # Random particle spawns
        if random.random() < 0.02:
            x = random.randint(50, CFG.WIDTH - 50)
            self.particles.append(
                SexyEngine.Particle(x, CFG.HEIGHT + 10, 0, -100,
                                    SexyEngine.Resources.get_color('sun_yellow'), 8, 5.0)
            )
        
        # Update particles
        self.particles = [p for p in self.particles if p.alive]
        for particle in self.particles:
            particle.update(dt)
    
    def draw(self, surface):
        # Background gradient
        for y in range(CFG.HEIGHT):
            t = y / CFG.HEIGHT
            r = int(135 * (1 - t) + 50 * t)
            g = int(206 * (1 - t) + 120 * t)
            b = int(235 * (1 - t) + 50 * t)
            pygame.draw.line(surface, (r, g, b), (0, y), (CFG.WIDTH, y))
        
        # Particles
        for particle in self.particles:
            particle.draw(surface)
        
        # Title with animation
        title_scale = 1.0 + 0.05 * math.sin(self.animation_time * 2)
        title_font = get_font(int(64 * title_scale), bold=True)
        draw_text(surface, "Plants vs Zombies", (CFG.WIDTH // 2, 100),
                  color=SexyEngine.Resources.get_color('text_white'),
                  font=title_font, center=True)
        
        draw_text(surface, "SexyEngine Replanted Edition", (CFG.WIDTH // 2, 160),
                  color=SexyEngine.Resources.get_color('sun_yellow'),
                  font=FONT_LARGE, center=True)
        
        # Buttons
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            hovered = button['rect'].collidepoint(mouse_pos)
            draw_button(surface, button['rect'].copy(), button['text'], hovered=hovered)
    
    def handle_click(self, x, y):
        for button in self.buttons:
            if button['rect'].collidepoint(x, y):
                return button['text']
        return None

# -----------------------------------------------------------------------------
# Main Game Class
# -----------------------------------------------------------------------------
class PvZGame:
    def __init__(self):
        self.state = 'menu'
        self.menu = MainMenu()
        self.game_state = None
        self.plant_selector = None
        self.animation_time = 0.0
        
    def start_game(self):
        self.state = 'playing'
        self.game_state = GameState()
        self.plant_selector = PlantSelector(10, 5)
    
    def update(self, dt):
        self.animation_time += dt
        
        if self.state == 'menu':
            self.menu.update(dt)
        elif self.state == 'playing':
            if self.game_state:
                self.game_state.update(dt)
    
    def draw(self, surface):
        if self.state == 'menu':
            self.menu.draw(surface)
        elif self.state == 'playing':
            self.draw_game(surface)
    
    def draw_game(self, surface):
        # Sky gradient background
        for y in range(CFG.HEIGHT):
            t = y / CFG.HEIGHT
            r = int(135 * (1 - t * 0.5))
            g = int(206 * (1 - t * 0.3))
            b = int(235 * (1 - t * 0.1))
            pygame.draw.line(surface, (r, g, b), (0, y), (CFG.WIDTH, y))
        
        # Draw lawn
        for row in range(CFG.ROWS):
            for col in range(CFG.COLS):
                x = CFG.GRID_LEFT + col * CFG.CELL_WIDTH
                y = CFG.GRID_TOP + row * CFG.CELL_HEIGHT
                
                # Alternating grass pattern
                if (row + col) % 2 == 0:
                    color = SexyEngine.Resources.get_color('lawn_green')
                else:
                    color = SexyEngine.Resources.get_color('lawn_dark')
                
                rect = pygame.Rect(x, y, CFG.CELL_WIDTH - 2, CFG.CELL_HEIGHT - 2)
                pygame.draw.rect(surface, color, rect)
                
                # Grass texture lines
                for i in range(3):
                    line_y = y + 20 + i * 25
                    pygame.draw.line(surface, (color[0] - 20, color[1] - 20, color[2] - 20),
                                     (x + 5, line_y), (x + CFG.CELL_WIDTH - 7, line_y), 1)
        
        # Draw game entities
        if self.game_state:
            # Lawn mowers
            for mower in self.game_state.lawn_mowers:
                mower.draw(surface)
            
            # Plants
            for plant in self.game_state.plants:
                if plant.alive:
                    plant.draw(surface, self.animation_time)
            
            # Zombies
            for zombie in self.game_state.zombies:
                zombie.draw(surface, self.animation_time)
            
            # Projectiles
            for proj in self.game_state.projectiles:
                proj.draw(surface)
            
            # Suns
            for sun in self.game_state.suns:
                if not sun.collected:
                    sun.draw(surface, self.animation_time)
            
            # Particles
            for particle in self.game_state.particles:
                particle.draw(surface)
            
            # UI Panel
            panel_rect = pygame.Rect(0, 0, CFG.WIDTH, 105) # Increased height
            panel_surf = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
            panel_surf.fill((*SexyEngine.Resources.get_color('ui_dark'), 200))
            surface.blit(panel_surf, (0,0))
            pygame.draw.line(surface, (0,0,0,150), (0, panel_rect.bottom), (CFG.WIDTH, panel_rect.bottom), 3)

            
            # Plant selector
            if self.plant_selector:
                self.plant_selector.draw(surface, self.game_state, self.animation_time)
            
            # Sun counter
            sun_rect = pygame.Rect(self.plant_selector.x + self.plant_selector.card_width * 3 + self.plant_selector.spacing * 3, 10, 150, 60)
            pygame.draw.rect(surface, SexyEngine.Resources.get_color('ui_panel'), sun_rect, border_radius=10)
            pygame.draw.rect(surface, (0, 0, 0), sun_rect, width=2, border_radius=10)
            draw_sun(surface, (sun_rect.x + 30, sun_rect.centery), 20, self.animation_time)
            draw_text(surface, str(self.game_state.sun_bank), 
                      (sun_rect.centerx + 15, sun_rect.centery),
                      color=SexyEngine.Resources.get_color('text_yellow'),
                      font=FONT_LARGE, center=True)
            
            # Shovel button
            shovel_rect = pygame.Rect(sun_rect.right + 10, 10, 60, 60)
            if self.game_state.shovel_mode:
                pygame.draw.rect(surface, SexyEngine.Resources.get_color('sun_yellow'), 
                                 shovel_rect, border_radius=10)
            else:
                pygame.draw.rect(surface, SexyEngine.Resources.get_color('ui_panel'), 
                                 shovel_rect, border_radius=10)
            pygame.draw.rect(surface, (0, 0, 0), shovel_rect, width=2, border_radius=10)
            draw_text(surface, "⚒", shovel_rect.center, font=FONT_LARGE, center=True)
            
            # Game status
            if self.game_state.paused:
                overlay = pygame.Surface((CFG.WIDTH, CFG.HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 128))
                surface.blit(overlay, (0, 0))
                draw_text(surface, "PAUSED", (CFG.WIDTH // 2, CFG.HEIGHT // 2),
                          font=FONT_HUGE, center=True, color=SexyEngine.Resources.get_color('text_yellow'))
                draw_text(surface, "Press P to continue", (CFG.WIDTH // 2, CFG.HEIGHT // 2 + 60),
                          font=FONT_LARGE, center=True)
                draw_text(surface, "Press R to restart", (CFG.WIDTH // 2, CFG.HEIGHT // 2 + 100),
                          font=FONT_LARGE, center=True)
                          
            elif self.game_state.game_over:
                overlay = pygame.Surface((CFG.WIDTH, CFG.HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 128))
                surface.blit(overlay, (0, 0))
                draw_text(surface, "THE ZOMBIES ATE YOUR BRAINS!", (CFG.WIDTH // 2, CFG.HEIGHT // 2),
                          font=FONT_HUGE, center=True, color=(255, 100, 100))
                draw_text(surface, "Press R to restart", (CFG.WIDTH // 2, CFG.HEIGHT // 2 + 60),
                          font=FONT_LARGE, center=True)
            
            elif self.game_state.victory:
                overlay = pygame.Surface((CFG.WIDTH, CFG.HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 128))
                surface.blit(overlay, (0, 0))
                draw_text(surface, "VICTORY!", (CFG.WIDTH // 2, CFG.HEIGHT // 2 - 40),
                          font=FONT_HUGE, center=True, color=SexyEngine.Resources.get_color('sun_yellow'))
                draw_text(surface, "You saved your brains!", (CFG.WIDTH // 2, CFG.HEIGHT // 2 + 30),
                          font=FONT_LARGE, center=True)
                draw_text(surface, "Press R to restart", (CFG.WIDTH // 2, CFG.HEIGHT // 2 + 70),
                          font=FONT_LARGE, center=True)
    
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.state == 'playing':
                    self.state = 'menu'
                else:
                    return False  # Quit
            elif event.key == pygame.K_p and self.state == 'playing':
                if self.game_state:
                    self.game_state.paused = not self.game_state.paused
            elif event.key == pygame.K_r and self.state == 'playing':
                if self.game_state and (self.game_state.game_over or self.game_state.victory or self.game_state.paused):
                    self.start_game()
            elif event.key == pygame.K_s and self.state == 'playing':
                if self.game_state:
                    self.game_state.shovel_mode = not self.game_state.shovel_mode
                    self.game_state.selected_plant = None
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                x, y = event.pos
                
                if self.state == 'menu':
                    action = self.menu.handle_click(x, y)
                    if action == 'Start Game':
                        self.start_game()
                    elif action == 'Quit':
                        return False
                
                elif self.state == 'playing' and self.game_state:
                    if not self.game_state.paused and not self.game_state.game_over and not self.game_state.victory:
                        # Check UI panel
                        if y <= 105:
                            # Check plant selector
                            if self.plant_selector and self.plant_selector.handle_click(x, y, self.game_state):
                                pass
                            # Check shovel button
                            elif pygame.Rect(self.plant_selector.x + self.plant_selector.card_width * 3 + self.plant_selector.spacing * 3 + 160, 10, 60, 60).collidepoint(x, y):
                                self.game_state.shovel_mode = not self.game_state.shovel_mode
                                self.game_state.selected_plant = None
                            else:
                                self.game_state.handle_click(x, y)
                        else:
                             self.game_state.handle_click(x, y)
            
            elif event.button == 3:  # Right click
                if self.state == 'playing' and self.game_state:
                    self.game_state.selected_plant = None
                    self.game_state.shovel_mode = False
        
        return True  # Continue running

# -----------------------------------------------------------------------------
# Main Game Loop
# -----------------------------------------------------------------------------
def main():
    game = PvZGame()
    running = True
    dt = 0
    
    print("=" * 60)
    print("Plants vs Zombies: SexyEngine Replanted Edition")
    print("=" * 60)
    print("Controls:")
    print("  - Click plants to select, then click lawn to place")
    print("  - Click suns to collect")
    print("  - S key or shovel button to remove plants")
    print("  - P to pause")
    print("  - R to restart (when paused, game over, or victory)")
    print("  - ESC to return to menu")
    print("=" * 60)
    
    while running:
        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                if not game.handle_event(event):
                    running = False
        
        # Update
        game.update(dt)
        
        # Draw
        game.draw(screen)
        pygame.display.flip()
        
        # Frame timing
        dt = clock.tick(CFG.FPS) / 1000.0
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
