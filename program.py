#!/usr/bin/env python3
"""
Plants vs Zombies 1 - Complete Decompilation/Recreation
Optimized for Windows PC OS 25H2 - 600x400 Resolution
Complete game engine with all PvZ1 mechanics
"""

import pygame
import random
import math
import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple
from enum import Enum, auto

# Initialize Pygame
pygame.init()

# Constants - Window Configuration
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400
FPS = 60

# Grid Configuration
GRID_START_X = 80
GRID_START_Y = 80
CELL_WIDTH = 60
CELL_HEIGHT = 80
ROWS = 5
COLS = 9

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 200, 0)
DARK_GREEN = (0, 100, 0)
BROWN = (139, 69, 19)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
BLUE = (100, 150, 255)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)

# Game States
class GameState(Enum):
    MENU = auto()
    PLAYING = auto()
    LEVEL_SELECT = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    VICTORY = auto()

# Entity Types
class EntityType(Enum):
    PLANT = auto()
    ZOMBIE = auto()
    PROJECTILE = auto()
    SUN = auto()

# Plant Types
class PlantType(Enum):
    PEASHOOTER = 0
    SUNFLOWER = 1
    CHERRY_BOMB = 2
    WALL_NUT = 3
    POTATO_MINE = 4
    SNOW_PEA = 5
    CHOMPER = 6
    REPEATER = 7
    PUFF_SHROOM = 8
    SUN_SHROOM = 9
    FUME_SHROOM = 10
    GRAVE_BUSTER = 11
    HYPNO_SHROOM = 12
    SCAREDY_SHROOM = 13
    ICE_SHROOM = 14
    DOOM_SHROOM = 15
    LILY_PAD = 16
    SQUASH = 17
    THREEPEATER = 18
    TANGLE_KELP = 19
    JALAPENO = 20
    SPIKEWEED = 21
    TORCHWOOD = 22
    TALL_NUT = 23
    SEA_SHROOM = 24
    PLANTERN = 25
    CACTUS = 26
    BLOVER = 27
    SPLIT_PEA = 28
    STARFRUIT = 29
    PUMPKIN = 30
    MAGNET_SHROOM = 31
    CABBAGE_PULT = 32
    FLOWER_POT = 33
    KERNEL_PULT = 34
    COFFEE_BEAN = 35
    GARLIC = 36
    UMBRELLA_LEAF = 37
    MARIGOLD = 38
    MELON_PULT = 39

# Zombie Types
class ZombieType(Enum):
    NORMAL = 0
    FLAG = 1
    CONEHEAD = 2
    POLE_VAULTING = 3
    BUCKETHEAD = 4
    NEWSPAPER = 5
    SCREEN_DOOR = 6
    FOOTBALL = 7
    DANCING = 8
    BACKUP_DANCER = 9
    DUCKY_TUBE = 10
    SNORKEL = 11
    ZOMBONI = 12
    ZOMBIE_BOBSLED = 13
    DOLPHIN_RIDER = 14
    JACK_IN_THE_BOX = 15
    BALLOON = 16
    DIGGER = 17
    POGO = 18
    ZOMBIE_YETI = 19
    BUNGEE = 20
    LADDER = 21
    CATAPULT = 22
    GARGANTUAR = 23
    IMP = 24

@dataclass
class PlantData:
    """Plant statistics and properties"""
    name: str
    cost: int
    recharge: int  # frames
    health: int
    damage: int
    fire_rate: int  # frames
    color: Tuple[int, int, int]
    description: str

@dataclass
class ZombieData:
    """Zombie statistics and properties"""
    name: str
    health: int
    speed: float
    damage: int
    color: Tuple[int, int, int]
    reward: int  # sun dropped on kill

# Plant Database
PLANT_DATABASE = {
    PlantType.PEASHOOTER: PlantData("Peashooter", 100, 450, 300, 20, 90, GREEN, "Shoots peas at zombies"),
    PlantType.SUNFLOWER: PlantData("Sunflower", 50, 450, 300, 0, 1500, YELLOW, "Produces sun"),
    PlantType.CHERRY_BOMB: PlantData("Cherry Bomb", 150, 3000, 1, 1800, 1, RED, "Explodes in area"),
    PlantType.WALL_NUT: PlantData("Wall-nut", 50, 1800, 4000, 0, 0, BROWN, "Blocks zombies"),
    PlantType.POTATO_MINE: PlantData("Potato Mine", 25, 1800, 1, 1800, 1, BROWN, "Explodes on contact"),
    PlantType.SNOW_PEA: PlantData("Snow Pea", 175, 450, 300, 20, 90, BLUE, "Slows zombies"),
    PlantType.CHOMPER: PlantData("Chomper", 150, 450, 300, 1800, 2700, DARK_GREEN, "Eats zombies whole"),
    PlantType.REPEATER: PlantData("Repeater", 200, 450, 300, 20, 90, GREEN, "Shoots two peas"),
    PlantType.PUFF_SHROOM: PlantData("Puff-shroom", 0, 450, 300, 20, 90, PURPLE, "Short range shooter"),
    PlantType.SUN_SHROOM: PlantData("Sun-shroom", 25, 450, 300, 0, 1500, PURPLE, "Night sun producer"),
    PlantType.FUME_SHROOM: PlantData("Fume-shroom", 75, 450, 300, 20, 120, PURPLE, "Shoots fumes"),
    PlantType.HYPNO_SHROOM: PlantData("Hypno-shroom", 75, 1800, 1, 0, 0, PURPLE, "Hypnotizes zombies"),
    PlantType.SCAREDY_SHROOM: PlantData("Scaredy-shroom", 25, 450, 300, 20, 90, PURPLE, "Hides when close"),
    PlantType.ICE_SHROOM: PlantData("Ice-shroom", 75, 3000, 1, 0, 1, BLUE, "Freezes all zombies"),
    PlantType.DOOM_SHROOM: PlantData("Doom-shroom", 125, 3000, 1, 1800, 1, PURPLE, "Huge explosion"),
    PlantType.SQUASH: PlantData("Squash", 50, 1800, 1, 1800, 1, ORANGE, "Squashes zombies"),
    PlantType.THREEPEATER: PlantData("Threepeater", 325, 450, 300, 20, 90, GREEN, "Shoots 3 lanes"),
    PlantType.JALAPENO: PlantData("Jalapeno", 125, 3000, 1, 1800, 1, RED, "Burns entire lane"),
    PlantType.SPIKEWEED: PlantData("Spikeweed", 100, 450, 300, 20, 60, DARK_GREEN, "Damages zombies"),
    PlantType.TORCHWOOD: PlantData("Torchwood", 175, 450, 300, 0, 0, BROWN, "Ignites peas"),
    PlantType.TALL_NUT: PlantData("Tall-nut", 125, 1800, 8000, 0, 0, BROWN, "Tall blocker"),
    PlantType.CACTUS: PlantData("Cactus", 125, 450, 300, 20, 90, GREEN, "Pops balloons"),
    PlantType.SPLIT_PEA: PlantData("Split Pea", 125, 450, 300, 20, 90, GREEN, "Shoots both ways"),
    PlantType.STARFRUIT: PlantData("Starfruit", 125, 450, 300, 20, 90, YELLOW, "Shoots 5 stars"),
    PlantType.MAGNET_SHROOM: PlantData("Magnet-shroom", 100, 450, 300, 0, 900, PURPLE, "Removes metal"),
    PlantType.CABBAGE_PULT: PlantData("Cabbage-pult", 100, 450, 300, 40, 180, GREEN, "Lobs cabbages"),
    PlantType.KERNEL_PULT: PlantData("Kernel-pult", 100, 450, 300, 40, 180, YELLOW, "Stuns zombies"),
    PlantType.GARLIC: PlantData("Garlic", 50, 450, 400, 0, 0, WHITE, "Diverts zombies"),
    PlantType.UMBRELLA_LEAF: PlantData("Umbrella Leaf", 100, 450, 300, 0, 0, GREEN, "Blocks bungees"),
    PlantType.MARIGOLD: PlantData("Marigold", 50, 1800, 300, 0, 1500, ORANGE, "Drops coins"),
    PlantType.MELON_PULT: PlantData("Melon-pult", 300, 450, 300, 80, 180, GREEN, "Heavy damage"),
}

# Zombie Database
ZOMBIE_DATABASE = {
    ZombieType.NORMAL: ZombieData("Normal Zombie", 200, 0.3, 100, (100, 200, 100), 0),
    ZombieType.FLAG: ZombieData("Flag Zombie", 200, 0.35, 100, (150, 150, 200), 0),
    ZombieType.CONEHEAD: ZombieData("Conehead Zombie", 560, 0.3, 100, (150, 150, 100), 0),
    ZombieType.POLE_VAULTING: ZombieData("Pole Vaulting Zombie", 340, 0.8, 100, (200, 150, 100), 0),
    ZombieType.BUCKETHEAD: ZombieData("Buckethead Zombie", 1100, 0.3, 100, (180, 180, 180), 0),
    ZombieType.NEWSPAPER: ZombieData("Newspaper Zombie", 300, 0.3, 100, (200, 200, 200), 0),
    ZombieType.SCREEN_DOOR: ZombieData("Screen Door Zombie", 1100, 0.25, 100, (150, 180, 150), 0),
    ZombieType.FOOTBALL: ZombieData("Football Zombie", 1400, 0.6, 100, (150, 0, 0), 0),
    ZombieType.DANCING: ZombieData("Dancing Zombie", 500, 0.2, 100, (200, 0, 200), 0),
    ZombieType.BACKUP_DANCER: ZombieData("Backup Dancer", 200, 0.2, 100, (180, 0, 180), 0),
    ZombieType.ZOMBONI: ZombieData("Zomboni", 1100, 0.4, 100, (150, 200, 200), 0),
    ZombieType.ZOMBIE_BOBSLED: ZombieData("Zombie Bobsled", 200, 0.6, 100, (100, 150, 200), 0),
    ZombieType.DOLPHIN_RIDER: ZombieData("Dolphin Rider", 340, 0.7, 100, (100, 150, 250), 0),
    ZombieType.JACK_IN_THE_BOX: ZombieData("Jack-in-the-Box", 500, 0.35, 100, (255, 100, 100), 0),
    ZombieType.BALLOON: ZombieData("Balloon Zombie", 280, 0.35, 100, (200, 150, 255), 0),
    ZombieType.DIGGER: ZombieData("Digger Zombie", 340, 0.4, 100, (150, 100, 50), 0),
    ZombieType.POGO: ZombieData("Pogo Zombie", 340, 0.45, 100, (200, 200, 0), 0),
    ZombieType.ZOMBIE_YETI: ZombieData("Zombie Yeti", 1100, 0.3, 100, (200, 200, 255), 0),
    ZombieType.BUNGEE: ZombieData("Bungee Zombie", 340, 0.3, 100, (150, 150, 200), 0),
    ZombieType.LADDER: ZombieData("Ladder Zombie", 340, 0.3, 100, (180, 150, 100), 0),
    ZombieType.CATAPULT: ZombieData("Catapult Zombie", 1100, 0.25, 100, (150, 100, 100), 0),
    ZombieType.GARGANTUAR: ZombieData("Gargantuar", 3000, 0.2, 500, (100, 50, 50), 0),
    ZombieType.IMP: ZombieData("Imp", 200, 0.5, 100, (150, 100, 150), 0),
}

class Particle:
    """Visual effect particle"""
    def __init__(self, x: float, y: float, color: Tuple[int, int, int],
                 velocity: Tuple[float, float], lifetime: int):
        self.x = x
        self.y = y
        self.color = color
        self.vx, self.vy = velocity
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = random.randint(2, 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2  # Gravity
        self.lifetime -= 1
        return self.lifetime > 0

    def render(self, surface: pygame.Surface):
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        color = (*self.color[:3], alpha)
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size)

class Projectile:
    """Base projectile class"""
    def __init__(self, x: float, y: float, damage: int, row: int,
                 velocity: float = 2.0, projectile_type: str = "pea"):
        self.x = x
        self.y = y
        self.damage = damage
        self.row = row
        self.velocity = velocity
        self.active = True
        self.projectile_type = projectile_type
        self.size = 8

    def update(self, zombies: List['Zombie']) -> List[Particle]:
        particles = []
        self.x += self.velocity

        # Check collision with zombies
        for zombie in zombies:
            if zombie.row == self.row and zombie.active:
                if (self.x >= zombie.x - 20 and self.x <= zombie.x + 20 and
                    abs(self.y - zombie.y) < 30):
                    zombie.take_damage(self.damage)
                    self.active = False
                    # Create hit particles
                    for _ in range(5):
                        particles.append(Particle(
                            self.x, self.y, GREEN,
                            (random.uniform(-2, 2), random.uniform(-3, 0)),
                            30
                        ))
                    break

        # Remove if off screen
        if self.x > SCREEN_WIDTH:
            self.active = False

        return particles

    def render(self, surface: pygame.Surface):
        if self.projectile_type == "pea":
            pygame.draw.circle(surface, GREEN, (int(self.x), int(self.y)), self.size)
            pygame.draw.circle(surface, DARK_GREEN, (int(self.x) - 2, int(self.y) - 2), 3)
        elif self.projectile_type == "snow_pea":
            pygame.draw.circle(surface, BLUE, (int(self.x), int(self.y)), self.size)
            pygame.draw.circle(surface, WHITE, (int(self.x) - 2, int(self.y) - 2), 3)
        elif self.projectile_type == "star":
            points = []
            for i in range(5):
                angle = math.pi * 2 * i / 5 - math.pi / 2
                points.append((self.x + math.cos(angle) * self.size,
                             self.y + math.sin(angle) * self.size))
            pygame.draw.polygon(surface, YELLOW, points)

class Sun:
    """Collectible sun resource"""
    def __init__(self, x: float, y: float, value: int = 25, fall: bool = True):
        self.x = x
        self.y = y
        self.value = value
        self.target_y = y if not fall else random.randint(100, 350)
        self.fall = fall
        self.active = True
        self.lifetime = 600  # 10 seconds
        self.size = 15
        self.collected = False

    def update(self):
        if self.fall and self.y < self.target_y:
            self.y += 0.5

        self.lifetime -= 1
        if self.lifetime <= 0:
            self.active = False

    def collect(self) -> int:
        if not self.collected:
            self.collected = True
            self.active = False
            return self.value
        return 0

    def render(self, surface: pygame.Surface):
        # Pulsing effect
        pulse = math.sin(pygame.time.get_ticks() * 0.01) * 2
        size = self.size + pulse

        # Outer glow
        pygame.draw.circle(surface, ORANGE, (int(self.x), int(self.y)), int(size) + 3)
        # Main sun
        pygame.draw.circle(surface, YELLOW, (int(self.x), int(self.y)), int(size))
        # Highlight
        pygame.draw.circle(surface, WHITE, (int(self.x) - 5, int(self.y) - 5), 5)

class Plant:
    """Base plant class"""
    def __init__(self, plant_type: PlantType, row: int, col: int):
        self.plant_type = plant_type
        self.data = PLANT_DATABASE[plant_type]
        self.row = row
        self.col = col
        self.x = GRID_START_X + col * CELL_WIDTH + CELL_WIDTH // 2
        self.y = GRID_START_Y + row * CELL_HEIGHT + CELL_HEIGHT // 2
        self.health = self.data.health
        self.max_health = self.data.health
        self.fire_cooldown = 0
        self.sun_cooldown = 0
        self.active = True
        self.animation_frame = 0
        self.armed = False  # For potato mine
        self.arming_time = 900  # 15 seconds for potato mine

    def update(self, zombies: List['Zombie'], game) -> Tuple[List[Projectile], List[Sun], List[Particle]]:
        projectiles = []
        suns = []
        particles = []

        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1
        if self.sun_cooldown > 0:
            self.sun_cooldown -= 1

        self.animation_frame = (self.animation_frame + 1) % 60

        # Special plant behaviors
        if self.plant_type == PlantType.SUNFLOWER:
            if self.sun_cooldown == 0:
                suns.append(Sun(self.x, self.y - 20, 25, fall=False))
                self.sun_cooldown = self.data.fire_rate

        elif self.plant_type == PlantType.PEASHOOTER:
            if self.fire_cooldown == 0:
                # Check if zombie in lane
                for zombie in zombies:
                    if zombie.row == self.row and zombie.x > self.x and zombie.active:
                        projectiles.append(Projectile(self.x + 20, self.y, self.data.damage, self.row))
                        self.fire_cooldown = self.data.fire_rate
                        break

        elif self.plant_type == PlantType.REPEATER:
            if self.fire_cooldown == 0:
                for zombie in zombies:
                    if zombie.row == self.row and zombie.x > self.x and zombie.active:
                        projectiles.append(Projectile(self.x + 20, self.y, self.data.damage, self.row))
                        projectiles.append(Projectile(self.x + 30, self.y, self.data.damage, self.row))
                        self.fire_cooldown = self.data.fire_rate
                        break

        elif self.plant_type == PlantType.SNOW_PEA:
            if self.fire_cooldown == 0:
                for zombie in zombies:
                    if zombie.row == self.row and zombie.x > self.x and zombie.active:
                        proj = Projectile(self.x + 20, self.y, self.data.damage, self.row, projectile_type="snow_pea")
                        projectiles.append(proj)
                        self.fire_cooldown = self.data.fire_rate
                        break

        elif self.plant_type == PlantType.CHERRY_BOMB:
            if self.fire_cooldown == 0:
                # Explode after 1 second
                if self.animation_frame > 60:
                    for zombie in zombies:
                        if abs(zombie.row - self.row) <= 1 and abs(zombie.x - self.x) < 100:
                            zombie.take_damage(self.data.damage)
                    # Create explosion particles
                    for _ in range(30):
                        particles.append(Particle(
                            self.x, self.y, RED,
                            (random.uniform(-5, 5), random.uniform(-5, 5)),
                            60
                        ))
                    self.active = False

        elif self.plant_type == PlantType.POTATO_MINE:
            if not self.armed:
                self.arming_time -= 1
                if self.arming_time <= 0:
                    self.armed = True
            else:
                # Check for zombie collision
                for zombie in zombies:
                    if zombie.row == self.row and abs(zombie.x - self.x) < 30 and zombie.active:
                        zombie.take_damage(self.data.damage)
                        # Explosion particles
                        for _ in range(20):
                            particles.append(Particle(
                                self.x, self.y, ORANGE,
                                (random.uniform(-4, 4), random.uniform(-4, 4)),
                                50
                            ))
                        self.active = False
                        break

        elif self.plant_type == PlantType.THREEPEATER:
            if self.fire_cooldown == 0:
                # Check any zombie in any of 3 lanes
                shoot = False
                for zombie in zombies:
                    if abs(zombie.row - self.row) <= 1 and zombie.x > self.x and zombie.active:
                        shoot = True
                        break
                if shoot:
                    for offset in [-1, 0, 1]:
                        target_row = self.row + offset
                        if 0 <= target_row < ROWS:
                            target_y = GRID_START_Y + target_row * CELL_HEIGHT + CELL_HEIGHT // 2
                            projectiles.append(Projectile(self.x + 20, target_y, self.data.damage, target_row))
                    self.fire_cooldown = self.data.fire_rate

        elif self.plant_type == PlantType.JALAPENO:
            if self.animation_frame > 30:
                # Burn entire lane
                for zombie in zombies:
                    if zombie.row == self.row and zombie.active:
                        zombie.take_damage(self.data.damage)
                # Fire particles
                for i in range(20):
                    x = self.x + random.randint(-200, 400)
                    particles.append(Particle(
                        x, self.y, RED,
                        (random.uniform(-2, 2), random.uniform(-3, 3)),
                        45
                    ))
                self.active = False

        elif self.plant_type == PlantType.STARFRUIT:
            if self.fire_cooldown == 0:
                for zombie in zombies:
                    if zombie.active:
                        # Shoot 5 stars in different directions
                        angles = [0, 72, 144, 216, 288]
                        for angle in angles:
                            rad = math.radians(angle)
                            vx = math.cos(rad) * 2
                            vy = math.sin(rad) * 2
                            proj = Projectile(self.x, self.y, self.data.damage, self.row, projectile_type="star")
                            proj.velocity = vx
                            proj.vy = vy
                            projectiles.append(proj)
                        self.fire_cooldown = self.data.fire_rate
                        break

        elif self.plant_type == PlantType.CHOMPER:
            if self.fire_cooldown == 0:
                for zombie in zombies:
                    if zombie.row == self.row and abs(zombie.x - self.x) < 40 and zombie.active:
                        zombie.take_damage(self.data.damage)
                        self.fire_cooldown = self.data.fire_rate  # Long recharge
                        break

        elif self.plant_type == PlantType.MELON_PULT:
            if self.fire_cooldown == 0:
                for zombie in zombies:
                    if zombie.row == self.row and zombie.x > self.x and zombie.active:
                        projectiles.append(Projectile(self.x + 20, self.y, self.data.damage, self.row))
                        self.fire_cooldown = self.data.fire_rate
                        break

        return projectiles, suns, particles

    def take_damage(self, damage: int):
        self.health -= damage
        if self.health <= 0:
            self.active = False

    def render(self, surface: pygame.Surface):
        # Plant body
        size = 20

        if self.plant_type == PlantType.SUNFLOWER:
            # Yellow flower
            pygame.draw.circle(surface, YELLOW, (int(self.x), int(self.y)), size)
            # Petals
            for i in range(8):
                angle = (i * 45 + self.animation_frame * 2) * math.pi / 180
                px = self.x + math.cos(angle) * size
                py = self.y + math.sin(angle) * size
                pygame.draw.circle(surface, ORANGE, (int(px), int(py)), 8)
            # Center
            pygame.draw.circle(surface, BROWN, (int(self.x), int(self.y)), 10)
            # Stem
            pygame.draw.rect(surface, GREEN, (self.x - 5, self.y + 10, 10, 30))

        elif self.plant_type in [PlantType.PEASHOOTER, PlantType.REPEATER, PlantType.SNOW_PEA]:
            # Head
            color = BLUE if self.plant_type == PlantType.SNOW_PEA else GREEN
            pygame.draw.circle(surface, color, (int(self.x), int(self.y)), size)
            # Mouth
            pygame.draw.arc(surface, BLACK, (self.x - 10, self.y - 5, 20, 15), 0, math.pi, 3)
            # Eyes
            pygame.draw.circle(surface, BLACK, (int(self.x) - 8, int(self.y) - 8), 4)
            pygame.draw.circle(surface, BLACK, (int(self.x) + 8, int(self.y) - 8), 4)
            # Stem
            pygame.draw.rect(surface, DARK_GREEN, (self.x - 5, self.y + 15, 10, 25))

        elif self.plant_type in [PlantType.WALL_NUT, PlantType.TALL_NUT]:
            # Nut shell
            pygame.draw.circle(surface, BROWN, (int(self.x), int(self.y)), size + 5)
            # Face
            pygame.draw.circle(surface, (210, 180, 140), (int(self.x), int(self.y)), size)
            # Eyes
            pygame.draw.circle(surface, BLACK, (int(self.x) - 8, int(self.y) - 5), 3)
            pygame.draw.circle(surface, BLACK, (int(self.x) + 8, int(self.y) - 5), 3)
            # Mouth
            pygame.draw.line(surface, BLACK, (self.x - 8, self.y + 8), (self.x + 8, self.y + 8), 2)

        elif self.plant_type == PlantType.CHERRY_BOMB:
            # Two cherries
            pygame.draw.circle(surface, RED, (int(self.x) - 10, int(self.y)), 15)
            pygame.draw.circle(surface, RED, (int(self.x) + 10, int(self.y)), 15)
            # Highlights
            pygame.draw.circle(surface, (255, 100, 100), (int(self.x) - 13, int(self.y) - 5), 5)
            pygame.draw.circle(surface, (255, 100, 100), (int(self.x) + 7, int(self.y) - 5), 5)
            # Stem
            pygame.draw.line(surface, DARK_GREEN, (self.x - 10, self.y - 15), (self.x, self.y - 25), 3)
            pygame.draw.line(surface, DARK_GREEN, (self.x + 10, self.y - 15), (self.x, self.y - 25), 3)

        elif self.plant_type == PlantType.POTATO_MINE:
            if not self.armed:
                # Unarmed - brown potato
                pygame.draw.ellipse(surface, BROWN, (self.x - 15, self.y - 10, 30, 20))
                pygame.draw.circle(surface, (139, 90, 43), (int(self.x) - 5, int(self.y) - 3), 3)
                pygame.draw.circle(surface, (139, 90, 43), (int(self.x) + 5, int(self.y) + 2), 3)
            else:
                # Armed - visible with red light
                pygame.draw.ellipse(surface, BROWN, (self.x - 15, self.y - 10, 30, 20))
                pygame.draw.circle(surface, RED, (int(self.x), int(self.y)), 5)

        elif self.plant_type == PlantType.THREEPEATER:
            # Three heads
            for offset in [-15, 0, 15]:
                pygame.draw.circle(surface, GREEN, (int(self.x) + offset, int(self.y) - 10), 12)
            # Stem
            pygame.draw.rect(surface, DARK_GREEN, (self.x - 5, self.y + 5, 10, 30))

        elif self.plant_type == PlantType.JALAPENO:
            # Red pepper
            pygame.draw.ellipse(surface, RED, (self.x - 10, self.y - 25, 20, 45))
            pygame.draw.ellipse(surface, (255, 100, 100), (self.x - 8, self.y - 20, 10, 20))
            # Stem
            pygame.draw.rect(surface, GREEN, (self.x - 3, self.y - 30, 6, 10))

        elif self.plant_type == PlantType.STARFRUIT:
            # Star shape
            points = []
            for i in range(5):
                angle = math.pi * 2 * i / 5 - math.pi / 2 + self.animation_frame * 0.05
                points.append((self.x + math.cos(angle) * 20,
                             self.y + math.sin(angle) * 20))
            pygame.draw.polygon(surface, YELLOW, points)
            pygame.draw.circle(surface, ORANGE, (int(self.x), int(self.y)), 8)

        elif self.plant_type == PlantType.CHOMPER:
            # Large mouth
            pygame.draw.circle(surface, DARK_GREEN, (int(self.x), int(self.y)), size + 5)
            # Mouth opening
            mouth_open = 15 + abs(math.sin(self.animation_frame * 0.1)) * 10
            pygame.draw.ellipse(surface, (150, 0, 0),
                              (self.x - 15, self.y - mouth_open/2, 30, mouth_open))
            # Teeth
            for i in range(5):
                pygame.draw.polygon(surface, WHITE, [
                    (self.x - 12 + i*6, self.y - mouth_open/2),
                    (self.x - 9 + i*6, self.y - mouth_open/2 + 5),
                    (self.x - 6 + i*6, self.y - mouth_open/2)
                ])

        elif self.plant_type == PlantType.SPIKEWEED:
            # Ground spikes
            for i in range(5):
                x_pos = self.x - 20 + i * 10
                pygame.draw.polygon(surface, GRAY, [
                    (x_pos, self.y + 10),
                    (x_pos - 5, self.y + 20),
                    (x_pos + 5, self.y + 20)
                ])

        elif self.plant_type == PlantType.CABBAGE_PULT:
            # Catapult with cabbage
            pygame.draw.rect(surface, BROWN, (self.x - 15, self.y + 10, 30, 15))
            pygame.draw.circle(surface, GREEN, (int(self.x), int(self.y) - 10), 12)
            pygame.draw.circle(surface, DARK_GREEN, (int(self.x) - 3, int(self.y) - 13), 4)

        elif self.plant_type == PlantType.MELON_PULT:
            # Catapult with melon
            pygame.draw.rect(surface, BROWN, (self.x - 15, self.y + 10, 30, 15))
            pygame.draw.ellipse(surface, GREEN, (self.x - 15, self.y - 15, 30, 20))
            pygame.draw.ellipse(surface, DARK_GREEN, (self.x - 10, self.y - 12, 20, 14))

        else:
            # Generic plant
            pygame.draw.circle(surface, self.data.color, (int(self.x), int(self.y)), size)
            pygame.draw.rect(surface, DARK_GREEN, (self.x - 5, self.y + 15, 10, 25))

        # Health bar
        if self.health < self.max_health:
            health_width = 30
            health_height = 4
            health_percent = self.health / self.max_health
            pygame.draw.rect(surface, RED,
                           (self.x - health_width//2, self.y - 35, health_width, health_height))
            pygame.draw.rect(surface, GREEN,
                           (self.x - health_width//2, self.y - 35, health_width * health_percent, health_height))

class Zombie:
    """Base zombie class"""
    def __init__(self, zombie_type: ZombieType, row: int, start_x: float = None):
        self.zombie_type = zombie_type
        self.data = ZOMBIE_DATABASE[zombie_type]
        self.row = row
        self.x = start_x if start_x else SCREEN_WIDTH + 50
        self.y = GRID_START_Y + row * CELL_HEIGHT + CELL_HEIGHT // 2
        self.health = self.data.health
        self.max_health = self.data.health
        self.speed = self.data.speed
        self.damage = self.data.damage
        self.active = True
        self.eating = False
        self.animation_frame = 0
        self.eat_cooldown = 0
        self.slowed = False
        self.slow_timer = 0

    def update(self, plants: List[Plant]) -> bool:
        """Update zombie, return True if zombie reached house"""
        self.animation_frame = (self.animation_frame + 1) % 120

        if self.slow_timer > 0:
            self.slow_timer -= 1
            self.slowed = True
        else:
            self.slowed = False

        # Check if eating plant
        self.eating = False
        for plant in plants:
            if plant.row == self.row and plant.active:
                if abs(self.x - plant.x) < 25:
                    self.eating = True
                    if self.eat_cooldown == 0:
                        plant.take_damage(self.damage)
                        self.eat_cooldown = 60
                    break

        if self.eat_cooldown > 0:
            self.eat_cooldown -= 1

        # Move if not eating
        if not self.eating:
            speed = self.speed * 0.5 if self.slowed else self.speed
            self.x -= speed

        # Check if reached house
        if self.x < GRID_START_X - 50:
            return True

        return False

    def take_damage(self, damage: int):
        self.health -= damage
        if self.health <= 0:
            self.active = False

    def render(self, surface: pygame.Surface):
        size = 25

        # Zombie body
        if self.zombie_type == ZombieType.NORMAL:
            # Head
            pygame.draw.circle(surface, self.data.color, (int(self.x), int(self.y) - 10), 15)
            # Eyes
            pygame.draw.circle(surface, RED, (int(self.x) - 5, int(self.y) - 15), 3)
            pygame.draw.circle(surface, RED, (int(self.x) + 5, int(self.y) - 15), 3)
            # Body
            pygame.draw.rect(surface, self.data.color, (self.x - 12, self.y, 24, 30))
            # Arms
            arm_swing = math.sin(self.animation_frame * 0.1) * 10
            pygame.draw.rect(surface, self.data.color, (self.x - 20, self.y + 5 + arm_swing, 8, 20))
            pygame.draw.rect(surface, self.data.color, (self.x + 12, self.y + 5 - arm_swing, 8, 20))

        elif self.zombie_type == ZombieType.CONEHEAD:
            # Head with cone
            pygame.draw.circle(surface, self.data.color, (int(self.x), int(self.y) - 10), 15)
            pygame.draw.polygon(surface, ORANGE, [
                (self.x - 12, self.y - 25),
                (self.x + 12, self.y - 25),
                (self.x, self.y - 40)
            ])
            # Eyes
            pygame.draw.circle(surface, RED, (int(self.x) - 5, int(self.y) - 12), 3)
            pygame.draw.circle(surface, RED, (int(self.x) + 5, int(self.y) - 12), 3)
            # Body
            pygame.draw.rect(surface, self.data.color, (self.x - 12, self.y, 24, 30))

        elif self.zombie_type == ZombieType.BUCKETHEAD:
            # Head with bucket
            pygame.draw.circle(surface, self.data.color, (int(self.x), int(self.y) - 10), 15)
            pygame.draw.rect(surface, GRAY, (self.x - 15, self.y - 30, 30, 20))
            pygame.draw.rect(surface, LIGHT_GRAY, (self.x - 12, self.y - 32, 24, 3))
            # Eyes
            pygame.draw.circle(surface, RED, (int(self.x) - 5, int(self.y) - 12), 3)
            pygame.draw.circle(surface, RED, (int(self.x) + 5, int(self.y) - 12), 3)
            # Body
            pygame.draw.rect(surface, self.data.color, (self.x - 12, self.y, 24, 30))

        elif self.zombie_type == ZombieType.FOOTBALL:
            # Head with helmet
            pygame.draw.circle(surface, self.data.color, (int(self.x), int(self.y) - 10), 15)
            pygame.draw.ellipse(surface, RED, (self.x - 18, self.y - 28, 36, 22))
            pygame.draw.line(surface, WHITE, (self.x, self.y - 28), (self.x, self.y - 18), 2)
            # Body - bulkier
            pygame.draw.rect(surface, self.data.color, (self.x - 15, self.y, 30, 30))

        elif self.zombie_type == ZombieType.GARGANTUAR:
            # Huge zombie
            scale = 2
            pygame.draw.circle(surface, self.data.color, (int(self.x), int(self.y) - 20), 20 * scale)
            pygame.draw.rect(surface, self.data.color, (self.x - 20, self.y, 40, 50))
            # Pole
            pygame.draw.rect(surface, BROWN, (self.x + 15, self.y - 30, 8, 60))

        else:
            # Generic zombie
            pygame.draw.circle(surface, self.data.color, (int(self.x), int(self.y) - 10), 15)
            pygame.draw.circle(surface, RED, (int(self.x) - 5, int(self.y) - 13), 3)
            pygame.draw.circle(surface, RED, (int(self.x) + 5, int(self.y) - 13), 3)
            pygame.draw.rect(surface, self.data.color, (self.x - 12, self.y, 24, 30))

        # Eating animation
        if self.eating:
            pygame.draw.circle(surface, (255, 0, 0), (int(self.x) - 20, int(self.y) - 10), 5)

        # Slow effect
        if self.slowed:
            pygame.draw.circle(surface, BLUE, (int(self.x), int(self.y)), 30, 2)

        # Health bar
        health_width = 30
        health_height = 4
        health_percent = self.health / self.max_health
        pygame.draw.rect(surface, RED,
                       (self.x - health_width//2, self.y - 40, health_width, health_height))
        pygame.draw.rect(surface, GREEN,
                       (self.x - health_width//2, self.y - 40, health_width * health_percent, health_height))

class WaveManager:
    """Manages zombie waves and difficulty"""
    def __init__(self, level: int = 1):
        self.level = level
        self.waves = []
        self.current_wave = 0
        self.wave_timer = 0
        self.spawn_timer = 0
        self.zombies_to_spawn = []
        self.wave_complete = False
        self.level_complete = False
        self.generate_waves()

    def generate_waves(self):
        """Generate waves based on level difficulty"""
        base_zombies = 5 + self.level * 2

        for wave_num in range(1, 11):  # 10 waves per level
            wave_zombies = []
            zombie_count = base_zombies + wave_num

            for _ in range(zombie_count):
                # Difficulty-based zombie type selection
                rand = random.random()
                if self.level == 1:
                    zombie_type = ZombieType.NORMAL
                elif self.level == 2:
                    zombie_type = ZombieType.CONEHEAD if rand > 0.7 else ZombieType.NORMAL
                elif self.level == 3:
                    if rand > 0.8:
                        zombie_type = ZombieType.BUCKETHEAD
                    elif rand > 0.5:
                        zombie_type = ZombieType.CONEHEAD
                    else:
                        zombie_type = ZombieType.NORMAL
                else:
                    if rand > 0.9:
                        zombie_type = ZombieType.FOOTBALL
                    elif rand > 0.75:
                        zombie_type = ZombieType.BUCKETHEAD
                    elif rand > 0.5:
                        zombie_type = ZombieType.CONEHEAD
                    else:
                        zombie_type = ZombieType.NORMAL

                row = random.randint(0, ROWS - 1)
                wave_zombies.append((zombie_type, row))

            self.waves.append(wave_zombies)

    def update(self):
        """Update wave manager"""
        if self.current_wave >= len(self.waves):
            if not self.zombies_to_spawn:
                self.level_complete = True
            return []

        self.wave_timer += 1

        # Start new wave every 20 seconds
        if self.wave_timer > 1200 and not self.zombies_to_spawn:
            self.zombies_to_spawn = self.waves[self.current_wave].copy()
            self.current_wave += 1
            self.wave_timer = 0

        # Spawn zombies from current wave
        spawned = []
        if self.zombies_to_spawn:
            self.spawn_timer += 1
            if self.spawn_timer > 120:  # Spawn every 2 seconds
                zombie_type, row = self.zombies_to_spawn.pop(0)
                spawned.append(Zombie(zombie_type, row))
                self.spawn_timer = 0

        return spawned

    def get_progress(self) -> Tuple[int, int]:
        """Return current wave and total waves"""
        return (self.current_wave, len(self.waves))

class PlantCard:
    """Plant selection card"""
    def __init__(self, plant_type: PlantType, x: int, y: int, index: int):
        self.plant_type = plant_type
        self.data = PLANT_DATABASE[plant_type]
        self.x = x
        self.y = y
        self.width = 50
        self.height = 60
        self.recharge_timer = 0
        self.index = index
        self.available = True

    def update(self):
        if self.recharge_timer > 0:
            self.recharge_timer -= 1
            self.available = False
        else:
            self.available = True

    def use(self):
        if self.available:
            self.recharge_timer = self.data.recharge
            self.available = False

    def render(self, surface: pygame.Surface, sun: int, selected: bool = False):
        # Card background
        color = LIGHT_GRAY if self.available and sun >= self.data.cost else GRAY
        pygame.draw.rect(surface, color, (self.x, self.y, self.width, self.height))

        if selected:
            pygame.draw.rect(surface, YELLOW, (self.x, self.y, self.width, self.height), 3)
        else:
            pygame.draw.rect(surface, BLACK, (self.x, self.y, self.width, self.height), 2)

        # Plant icon (simplified)
        icon_x = self.x + self.width // 2
        icon_y = self.y + 20
        pygame.draw.circle(surface, self.data.color, (icon_x, icon_y), 12)

        # Cost
        font = pygame.font.Font(None, 16)
        cost_text = font.render(str(self.data.cost), True, BLACK if self.available else RED)
        surface.blit(cost_text, (self.x + 5, self.y + 40))

        # Recharge overlay
        if self.recharge_timer > 0:
            recharge_percent = self.recharge_timer / self.data.recharge
            overlay_height = int(self.height * recharge_percent)
            overlay = pygame.Surface((self.width, overlay_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            surface.blit(overlay, (self.x, self.y))

class Game:
    """Main game class"""
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Plants vs Zombies - Decompilation")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.MENU

        # Game objects
        self.plants: List[Plant] = []
        self.zombies: List[Zombie] = []
        self.projectiles: List[Projectile] = []
        self.suns: List[Sun] = []
        self.particles: List[Particle] = []

        # Game state
        self.sun_count = 150
        self.level = 1
        self.wave_manager = WaveManager(self.level)

        # Plant cards
        self.plant_cards = [
            PlantCard(PlantType.SUNFLOWER, 10, 10, 0),
            PlantCard(PlantType.PEASHOOTER, 65, 10, 1),
            PlantCard(PlantType.WALL_NUT, 120, 10, 2),
            PlantCard(PlantType.CHERRY_BOMB, 175, 10, 3),
            PlantCard(PlantType.SNOW_PEA, 230, 10, 4),
            PlantCard(PlantType.REPEATER, 285, 10, 5),
            PlantCard(PlantType.THREEPEATER, 340, 10, 6),
            PlantCard(PlantType.JALAPENO, 395, 10, 7),
        ]

        self.selected_card: Optional[PlantCard] = None
        self.grid_plants = [[None for _ in range(COLS)] for _ in range(ROWS)]

        # Sun spawn timer
        self.sun_spawn_timer = 0
        self.sun_spawn_interval = 600  # 10 seconds

        # Fonts
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)

        # Game over
        self.game_over_timer = 0

    def handle_events(self):
        """Handle input events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos

                if self.state == GameState.MENU:
                    # Start game button
                    if 200 <= mouse_x <= 400 and 200 <= mouse_y <= 250:
                        self.start_game()

                elif self.state == GameState.PLAYING:
                    # Check plant card selection
                    for card in self.plant_cards:
                        if (card.x <= mouse_x <= card.x + card.width and
                            card.y <= mouse_y <= card.y + card.height and
                            card.available and self.sun_count >= card.data.cost):
                            self.selected_card = card
                            break

                    # Check grid placement
                    if self.selected_card:
                        grid_x = (mouse_x - GRID_START_X) // CELL_WIDTH
                        grid_y = (mouse_y - GRID_START_Y) // CELL_HEIGHT

                        if (0 <= grid_x < COLS and 0 <= grid_y < ROWS and
                            self.grid_plants[grid_y][grid_x] is None):
                            # Place plant
                            plant = Plant(self.selected_card.plant_type, grid_y, grid_x)
                            self.plants.append(plant)
                            self.grid_plants[grid_y][grid_x] = plant
                            self.sun_count -= self.selected_card.data.cost
                            self.selected_card.use()
                            self.selected_card = None

                    # Check sun collection
                    for sun in self.suns:
                        if sun.active:
                            dist = math.sqrt((sun.x - mouse_x)**2 + (sun.y - mouse_y)**2)
                            if dist < sun.size + 10:
                                self.sun_count += sun.collect()
                                break

                elif self.state == GameState.GAME_OVER or self.state == GameState.VICTORY:
                    # Return to menu
                    if 200 <= mouse_x <= 400 and 250 <= mouse_y <= 300:
                        self.reset_game()
                        self.state = GameState.MENU

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == GameState.PLAYING:
                        self.state = GameState.PAUSED
                    elif self.state == GameState.PAUSED:
                        self.state = GameState.PLAYING
                    else:
                        self.state = GameState.MENU

    def start_game(self):
        """Start a new game"""
        self.reset_game()
        self.state = GameState.PLAYING

    def reset_game(self):
        """Reset game state"""
        self.plants.clear()
        self.zombies.clear()
        self.projectiles.clear()
        self.suns.clear()
        self.particles.clear()
        self.sun_count = 150
        self.wave_manager = WaveManager(self.level)
        self.grid_plants = [[None for _ in range(COLS)] for _ in range(ROWS)]
        self.selected_card = None
        self.game_over_timer = 0
        for card in self.plant_cards:
            card.recharge_timer = 0

    def update(self):
        """Update game logic"""
        if self.state != GameState.PLAYING:
            return

        # Update plant cards
        for card in self.plant_cards:
            card.update()

        # Spawn sun from sky
        self.sun_spawn_timer += 1
        if self.sun_spawn_timer >= self.sun_spawn_interval:
            x = random.randint(GRID_START_X, GRID_START_X + COLS * CELL_WIDTH)
            y = -20
            self.suns.append(Sun(x, y, 25, fall=True))
            self.sun_spawn_timer = 0

        # Update plants
        for plant in self.plants[:]:
            if not plant.active:
                self.plants.remove(plant)
                self.grid_plants[plant.row][plant.col] = None
                continue

            new_projectiles, new_suns, new_particles = plant.update(self.zombies, self)
            self.projectiles.extend(new_projectiles)
            self.suns.extend(new_suns)
            self.particles.extend(new_particles)

        # Update zombies
        for zombie in self.zombies[:]:
            if not zombie.active:
                self.zombies.remove(zombie)
                continue

            if zombie.update(self.plants):
                # Zombie reached house - game over
                self.state = GameState.GAME_OVER
                return

        # Spawn new zombies from wave manager
        new_zombies = self.wave_manager.update()
        self.zombies.extend(new_zombies)

        # Check level complete
        if self.wave_manager.level_complete and not self.zombies:
            self.state = GameState.VICTORY

        # Update projectiles
        for proj in self.projectiles[:]:
            if not proj.active:
                self.projectiles.remove(proj)
                continue

            new_particles = proj.update(self.zombies)
            self.particles.extend(new_particles)

        # Update suns
        for sun in self.suns[:]:
            if not sun.active:
                self.suns.remove(sun)
                continue
            sun.update()

        # Update particles
        self.particles = [p for p in self.particles if p.update()]

    def render(self):
        """Render game"""
        self.screen.fill((109, 170, 44))  # Lawn green

        if self.state == GameState.MENU:
            self.render_menu()
        elif self.state == GameState.PLAYING:
            self.render_game()
        elif self.state == GameState.PAUSED:
            self.render_game()
            self.render_pause()
        elif self.state == GameState.GAME_OVER:
            self.render_game()
            self.render_game_over()
        elif self.state == GameState.VICTORY:
            self.render_game()
            self.render_victory()

        pygame.display.flip()

    def render_menu(self):
        """Render main menu"""
        title = self.font_large.render("Plants vs Zombies", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)

        subtitle = self.font_small.render("Complete Decompilation", True, LIGHT_GRAY)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 140))
        self.screen.blit(subtitle, subtitle_rect)

        # Start button
        pygame.draw.rect(self.screen, GREEN, (200, 200, 200, 50))
        pygame.draw.rect(self.screen, WHITE, (200, 200, 200, 50), 2)
        start_text = self.font_medium.render("Start Game", True, WHITE)
        start_rect = start_text.get_rect(center=(300, 225))
        self.screen.blit(start_text, start_rect)

        # Instructions
        instructions = [
            "Click cards to select plants",
            "Click grid to place plants",
            "Click suns to collect them",
            "Defend your lawn from zombies!",
        ]
        for i, instruction in enumerate(instructions):
            text = self.font_small.render(instruction, True, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 300 + i * 25))
            self.screen.blit(text, text_rect)

    def render_game(self):
        """Render main game"""
        # Draw lawn grid
        for row in range(ROWS):
            for col in range(COLS):
                x = GRID_START_X + col * CELL_WIDTH
                y = GRID_START_Y + row * CELL_HEIGHT

                # Alternating lawn colors
                color = DARK_GREEN if (row + col) % 2 == 0 else GREEN
                pygame.draw.rect(self.screen, color, (x, y, CELL_WIDTH, CELL_HEIGHT))
                pygame.draw.rect(self.screen, (80, 140, 40), (x, y, CELL_WIDTH, CELL_HEIGHT), 1)

        # Draw particles (behind everything)
        for particle in self.particles:
            particle.render(self.screen)

        # Draw plants
        for plant in self.plants:
            plant.render(self.screen)

        # Draw zombies
        for zombie in self.zombies:
            zombie.render(self.screen)

        # Draw projectiles
        for proj in self.projectiles:
            proj.render(self.screen)

        # Draw suns
        for sun in self.suns:
            sun.render(self.screen)

        # Draw UI panel at top
        pygame.draw.rect(self.screen, (101, 67, 33), (0, 0, SCREEN_WIDTH, 75))

        # Draw plant cards
        for card in self.plant_cards:
            card.render(self.screen, self.sun_count, card == self.selected_card)

        # Draw sun counter
        sun_x = SCREEN_WIDTH - 100
        sun_y = 25
        pygame.draw.circle(self.screen, YELLOW, (sun_x, sun_y), 20)
        pygame.draw.circle(self.screen, ORANGE, (sun_x, sun_y), 20, 2)
        sun_text = self.font_medium.render(str(self.sun_count), True, BLACK)
        self.screen.blit(sun_text, (sun_x + 25, sun_y - 15))

        # Draw wave progress
        current_wave, total_waves = self.wave_manager.get_progress()
        wave_text = self.font_small.render(f"Wave: {current_wave}/{total_waves}", True, WHITE)
        self.screen.blit(wave_text, (10, SCREEN_HEIGHT - 30))

        # Draw level
        level_text = self.font_small.render(f"Level: {self.level}", True, WHITE)
        self.screen.blit(level_text, (SCREEN_WIDTH - 100, SCREEN_HEIGHT - 30))

    def render_pause(self):
        """Render pause overlay"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))

        pause_text = self.font_large.render("PAUSED", True, WHITE)
        pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(pause_text, pause_rect)

        continue_text = self.font_small.render("Press ESC to continue", True, WHITE)
        continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        self.screen.blit(continue_text, continue_rect)

    def render_game_over(self):
        """Render game over screen"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        gameover_text = self.font_large.render("GAME OVER", True, RED)
        gameover_rect = gameover_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(gameover_text, gameover_rect)

        zombie_text = self.font_medium.render("The zombies ate your brains!", True, WHITE)
        zombie_rect = zombie_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(zombie_text, zombie_rect)

        # Restart button
        pygame.draw.rect(self.screen, GREEN, (200, 250, 200, 50))
        pygame.draw.rect(self.screen, WHITE, (200, 250, 200, 50), 2)
        restart_text = self.font_medium.render("Main Menu", True, WHITE)
        restart_rect = restart_text.get_rect(center=(300, 275))
        self.screen.blit(restart_text, restart_rect)

    def render_victory(self):
        """Render victory screen"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        victory_text = self.font_large.render("VICTORY!", True, YELLOW)
        victory_rect = victory_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(victory_text, victory_rect)

        congrats_text = self.font_medium.render("You defended your lawn!", True, WHITE)
        congrats_rect = congrats_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(congrats_text, congrats_rect)

        # Continue button
        pygame.draw.rect(self.screen, GREEN, (200, 250, 200, 50))
        pygame.draw.rect(self.screen, WHITE, (200, 250, 200, 50), 2)
        continue_text = self.font_medium.render("Main Menu", True, WHITE)
        continue_rect = continue_text.get_rect(center=(300, 275))
        self.screen.blit(continue_text, continue_rect)

    def run(self):
        """Main game loop"""
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

def main():
    """Entry point"""
    game = Game()
    game.run()

if __name__ == "__main__":
    main()
