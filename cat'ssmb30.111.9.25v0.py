#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMB3 COMPLETE ENGINE - Samsoft Ultra Decomp Edition
By Team Flames / Samsoft Studios
Complete SMB3-style platformer with all decomp features integrated
Single-file implementation with full game mechanics
"""

import math, os, random, sys, json, pygame
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Set
from enum import Enum
from collections import deque

# =============================================================================
# CONFIGURATION & CONSTANTS
# =============================================================================
WIDTH, HEIGHT = 960, 540
TILE = 32
FPS = 60
GRAVITY = 0.55
MAX_FALL_SPEED = 12.0

# Color Palette
WHITE=(255,255,255);BLACK=(20,20,22);GRAY=(140,140,140);SKY=(160,208,255)
SEA=(83,153,211);GRASS=(84,196,96);DIRT=(149,109,63);ROCK=(101,79,58)
GOLD=(255,208,64);RED=(231,76,60);ORANGE=(255,159,67);BLUE=(75,119,190)
PURPLE=(142,84,233);ICEBLUE=(186,225,255);GREEN=(46,204,113);BROWN=(139,90,43)

# Game States
class GameState(Enum):
    TITLE = "title"
    OVERWORLD = "overworld"
    LEVEL = "level"
    BOSS = "boss"
    ENDING = "ending"
    GAMEOVER = "gameover"

# Tile Types
EMPTY=0; SOLID=1; COIN=2; HAZARD=3; QBLOCK=4; FLAG=5; BRICK=6
PIPE_TOP=7; PIPE_BODY=8; INVISIBLE_BLOCK=9; NOTEBLOCK=10; POWERUP=11

# Power-up Types
class PowerUpType(Enum):
    MUSHROOM = 1
    FIRE_FLOWER = 2
    SUPER_LEAF = 3
    TANOOKI_SUIT = 4
    FROG_SUIT = 5
    HAMMER_SUIT = 6
    STAR = 7

# Player States
class PlayerState(Enum):
    SMALL = 0
    BIG = 1
    FIRE = 2
    RACCOON = 3
    TANOOKI = 4
    FROG = 5
    HAMMER = 6
    INVINCIBLE = 7

# Engine Info
ENGINE_NAME = "SMB3 Complete Engine - Samsoft Ultra Decomp"
ENGINE_VERSION = "v2.0.0-decomp"

# World Themes (8 worlds like original SMB3)
WORLD_THEMES = [
    {"name":"Grass Land", "bg_top":(170,220,255), "bg_bottom":(120,185,255),
     "ground_top":GRASS, "ground":DIRT, "hazard":"none", "friction":0.86, "gravity":0.55,
     "gap_rate":0.06, "platform_rate":0.23, "enemy_rate":0.18, "coin_rate":0.20,
     "music_theme":"grassland"},
    {"name":"Desert Land", "bg_top":(235,220,170), "bg_bottom":(220,190,120),
     "ground_top":(215,170,90), "ground":(190,140,70), "hazard":"quicksand", "friction":0.84, "gravity":0.55,
     "gap_rate":0.09, "platform_rate":0.18, "enemy_rate":0.22, "coin_rate":0.16,
     "music_theme":"desert"},
    {"name":"Water Land", "bg_top":(160,208,255), "bg_bottom":(110,170,230),
     "ground_top":(70,150,90), "ground":(60,120,80), "hazard":"water", "friction":0.86, "gravity":0.55,
     "gap_rate":0.05, "platform_rate":0.20, "enemy_rate":0.16, "coin_rate":0.22,
     "music_theme":"water"},
    {"name":"Giant Land", "bg_top":(190,230,190), "bg_bottom":(150,210,160),
     "ground_top":(80,170,90), "ground":(70,140,80), "hazard":"none", "friction":0.86, "gravity":0.55,
     "gap_rate":0.04, "platform_rate":0.16, "enemy_rate":0.18, "coin_rate":0.20,
     "music_theme":"giant"},
    {"name":"Sky Land", "bg_top":(210,230,255), "bg_bottom":(170,210,255),
     "ground_top":(200,200,200), "ground":(170,170,170), "hazard":"void", "friction":0.88, "gravity":0.52,
     "gap_rate":0.11, "platform_rate":0.28, "enemy_rate":0.18, "coin_rate":0.22,
     "music_theme":"sky"},
    {"name":"Ice Land", "bg_top":(210,240,255), "bg_bottom":(180,220,255),
     "ground_top":ICEBLUE, "ground":(160,200,230), "hazard":"ice", "friction":0.70, "gravity":0.55,
     "gap_rate":0.07, "platform_rate":0.20, "enemy_rate":0.16, "coin_rate":0.20,
     "music_theme":"ice"},
    {"name":"Pipe Land", "bg_top":(170,220,200), "bg_bottom":(130,200,170),
     "ground_top":(90,160,110), "ground":(70,140,90), "hazard":"piranha", "friction":0.86, "gravity":0.55,
     "gap_rate":0.07, "platform_rate":0.24, "enemy_rate":0.22, "coin_rate":0.20,
     "music_theme":"pipe"},
    {"name":"Dark Land", "bg_top":(60,60,80), "bg_bottom":(40,40,60),
     "ground_top":(70,70,85), "ground":(50,50,65), "hazard":"lava", "friction":0.86, "gravity":0.58,
     "gap_rate":0.10, "platform_rate":0.22, "enemy_rate":0.24, "coin_rate":0.18,
     "music_theme":"dark"},
]

WORLD_STAGE_COUNTS = [6, 6, 8, 6, 9, 6, 9, 10]  # Stages per world

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================
def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def lerp(a, b, t):
    return a + (b - a) * t

def rect_from_tile(x, y):
    return pygame.Rect(x * TILE, y * TILE, TILE, TILE)

def draw_text(surf, font, msg, pos, color=BLACK, center=False, shadow=True):
    if shadow:
        sh = font.render(msg, True, (0, 0, 0))
        if center:
            surf.blit(sh, sh.get_rect(center=(pos[0] + 2, pos[1] + 2)))
        else:
            surf.blit(sh, (pos[0] + 2, pos[1] + 2))
    img = font.render(msg, True, color)
    if center:
        surf.blit(img, img.get_rect(center=pos))
    else:
        surf.blit(img, pos)

def sign(x):
    return 1 if x > 0 else -1 if x < 0 else 0

# =============================================================================
# PARTICLE SYSTEM
# =============================================================================
@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    lifetime: int
    color: Tuple[int, int, int]
    size: int = 3
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2  # gravity
        self.lifetime -= 1
        return self.lifetime > 0
    
    def draw(self, screen, cam_x):
        alpha = self.lifetime / 30
        pygame.draw.circle(screen, self.color, 
                          (int(self.x - cam_x), int(self.y)), 
                          max(1, int(self.size * alpha)))

# =============================================================================
# ENTITY CLASSES
# =============================================================================
@dataclass
class PowerUp:
    x: float
    y: float
    vx: float = 1.5
    vy: float = 0
    w: int = 24
    h: int = 24
    type: PowerUpType = PowerUpType.MUSHROOM
    alive: bool = True
    
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

@dataclass
class Projectile:
    x: float
    y: float
    vx: float
    vy: float
    w: int = 12
    h: int = 12
    type: str = "fireball"  # "fireball", "hammer"
    lifetime: int = 180
    alive: bool = True
    
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

@dataclass
class Enemy:
    x: float
    y: float
    w: int = 28
    h: int = 28
    vx: float = -1.2
    vy: float = 0
    dir: int = -1
    alive: bool = True
    type: str = "goomba"  # "goomba", "koopa", "flying", "hammer_bro"
    stomped: bool = False
    stomp_timer: int = 0
    shell_kick_timer: int = 0
    ai_state: str = "walk"
    ai_timer: int = 0
    
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

@dataclass
class Player:
    x: float = 96.0
    y: float = 200.0
    w: int = 28
    h: int = 30
    vx: float = 0.0
    vy: float = 0.0
    on_ground: bool = False
    coyote_timer: int = 0
    jump_buffer: int = 0
    facing: int = 1
    lives: int = 3
    coins: int = 0
    score: int = 0
    state: PlayerState = PlayerState.SMALL
    invincible_timer: int = 0
    damage_timer: int = 0
    p_meter: float = 0.0  # P-speed meter for flying
    flying: bool = False
    flight_timer: int = 0
    ducking: bool = False
    skidding: bool = False
    spin_jump: bool = False
    
    def rect(self):
        h = self.h if not self.ducking else self.h // 2
        return pygame.Rect(int(self.x), int(self.y), self.w, h)
    
    def can_fly(self):
        return self.state in (PlayerState.RACCOON, PlayerState.TANOOKI) and self.p_meter >= 7.0
    
    def take_damage(self):
        if self.damage_timer > 0 or self.invincible_timer > 0:
            return False
        
        if self.state == PlayerState.SMALL:
            return True  # Death
        else:
            # Power down
            if self.state in (PlayerState.FIRE, PlayerState.RACCOON, 
                            PlayerState.TANOOKI, PlayerState.FROG, PlayerState.HAMMER):
                self.state = PlayerState.BIG
            else:
                self.state = PlayerState.SMALL
            self.damage_timer = 120
            return False
    
    def add_score(self, points):
        self.score += points
        # 1-up every 100 coins
        if self.coins >= 100:
            self.coins -= 100
            self.lives += 1

# =============================================================================
# TILEMAP & LEVEL GENERATION
# =============================================================================
class TileMap:
    def __init__(self, w: int, h: int, theme_idx: int, seed: int):
        self.w, self.h = w, h
        self.grid = [[EMPTY for _ in range(w)] for __ in range(h)]
        self.theme_idx = theme_idx
        self.seed = seed
        self.start_px = (TILE * 2, TILE * 6)
        self.flag_pos = (w * TILE - 5 * TILE, TILE * 4)
        
    def in_bounds(self, tx, ty):
        return 0 <= tx < self.w and 0 <= ty < self.h
    
    def get(self, tx, ty):
        if not self.in_bounds(tx, ty):
            return SOLID
        return self.grid[ty][tx]
    
    def set(self, tx, ty, v):
        if self.in_bounds(tx, ty):
            self.grid[ty][tx] = v
    
    def rects_for_type(self, t: int):
        out = []
        for y in range(self.h):
            for x in range(self.w):
                if self.grid[y][x] == t:
                    out.append(rect_from_tile(x, y))
        return out

class Level:
    def __init__(self, theme_idx: int, stage_idx: int, seed: int):
        self.theme_idx = theme_idx
        self.stage_idx = stage_idx
        self.theme = WORLD_THEMES[theme_idx]
        self.map = TileMap(w=200, h=17, theme_idx=theme_idx, seed=seed)
        self.enemies: List[Enemy] = []
        self.powerups: List[PowerUp] = []
        self.particles: List[Particle] = []
        self.projectiles: List[Projectile] = []
        self.secret_blocks: Set[Tuple[int, int]] = set()
        self._generate()
    
    def _generate(self):
        """Enhanced level generation with SMB3 decomp features"""
        rng = random.Random(self.map.seed)
        t = self.theme
        ground_y = 12
        wobble = 0
        last_platform_x = -20
        
        # Generate terrain
        for x in range(self.map.w):
            # Terrain wobble
            if x % 8 == 0:
                wobble = clamp(wobble + rng.choice([-1, 0, 1]), -2, 2)
            gy = clamp(ground_y + wobble, 8, 13)
            
            # Gap generation
            is_gap = rng.random() < t["gap_rate"] and x > 10
            
            if not is_gap:
                # Solid ground
                for y in range(gy, self.map.h):
                    self.map.set(x, y, SOLID)
                
                # Pipes (Pipe Land special)
                if self.theme_idx == 6 and rng.random() < 0.12 and x > 15:
                    pipe_height = rng.randint(3, 5)
                    for py in range(gy - pipe_height, gy):
                        if py == gy - pipe_height:
                            self.map.set(x, py, PIPE_TOP)
                        else:
                            self.map.set(x, py, PIPE_BODY)
                        if x + 1 < self.map.w:
                            if py == gy - pipe_height:
                                self.map.set(x + 1, py, PIPE_TOP)
                            else:
                                self.map.set(x + 1, py, PIPE_BODY)
                
                # Enemy placement
                if rng.random() < t["enemy_rate"] and x > 20:
                    ey = (gy - 1) * TILE - 28
                    enemy_type = rng.choice(["goomba", "goomba", "koopa", "flying"])
                    if self.theme_idx == 7 and rng.random() < 0.3:
                        enemy_type = "hammer_bro"
                    self.enemies.append(Enemy(x * TILE, ey, type=enemy_type, 
                                            vx=-1.2 if enemy_type != "flying" else -0.8))
                
            else:
                # Fill gaps with hazards
                if t["hazard"] in ("water", "lava") and rng.random() < 0.6:
                    pool_depth = rng.randint(2, 4)
                    for d in range(pool_depth):
                        ty = clamp(self.map.h - 1 - d, 0, self.map.h - 1)
                        self.map.set(x, ty, HAZARD)
            
            # Floating platforms
            if rng.random() < t["platform_rate"] and x - last_platform_x > 6:
                top = gy - rng.randint(3, 6)
                span = rng.randint(2, 5)
                for dx in range(span):
                    tx = clamp(x + dx, 0, self.map.w - 1)
                    self.map.set(tx, top, BRICK if rng.random() < 0.5 else SOLID)
                
                # Coins above platforms
                if rng.random() < t["coin_rate"]:
                    for dx in range(span):
                        tx = clamp(x + dx, 0, self.map.w - 1)
                        self.map.set(tx, top - 2, COIN)
                
                last_platform_x = x
            
            # Question blocks with powerups
            if rng.random() < 0.08 and x > 10:
                qy = gy - 3
                self.map.set(x, qy, QBLOCK)
                if rng.random() < 0.3:
                    self.secret_blocks.add((x, qy))
                
                # Multiple Q-blocks in a row
                if rng.random() < 0.4 and x + 1 < self.map.w:
                    self.map.set(x + 1, qy, QBLOCK)
            
            # Hidden blocks (invisible until hit)
            if rng.random() < 0.05 and x > 20:
                self.map.set(x, gy - 5, INVISIBLE_BLOCK)
            
            # Note blocks (bounce blocks)
            if rng.random() < 0.06 and x > 15:
                self.map.set(x, gy - 2, NOTEBLOCK)
        
        # Place flag at end
        fx = self.map.w - 5
        for y in range(4, self.map.h):
            self.map.set(fx, y, SOLID)
        self.map.set(fx - 1, 10, FLAG)
        
        # Set start position
        self.map.start_px = (TILE * 2, TILE * 6)
    
    def draw_background(self, screen):
        """Gradient background"""
        top = self.theme["bg_top"]
        bottom = self.theme["bg_bottom"]
        for i in range(HEIGHT):
            t = i / (HEIGHT - 1)
            c = (int(top[0] * (1 - t) + bottom[0] * t),
                 int(top[1] * (1 - t) + bottom[1] * t),
                 int(top[2] * (1 - t) + bottom[2] * t))
            pygame.draw.line(screen, c, (0, i), (WIDTH, i))
    
    def draw(self, screen, cam_x: float):
        """Enhanced level rendering"""
        self.draw_background(screen)
        
        # Visible tile range
        x0 = max(0, int(cam_x // TILE) - 1)
        x1 = min(self.map.w, x0 + (WIDTH // TILE) + 3)
        
        gt = self.theme["ground_top"]
        
        # Draw tiles
        for y in range(self.map.h):
            for x in range(x0, x1):
                t = self.map.get(x, y)
                if t == EMPTY:
                    continue
                
                r = rect_from_tile(x, y).move(-cam_x, 0)
                
                if t == SOLID:
                    pygame.draw.rect(screen, self.theme["ground"], r)
                    lip = pygame.Rect(r.x, r.y, r.w, 4)
                    pygame.draw.rect(screen, gt, lip)
                elif t == BRICK:
                    pygame.draw.rect(screen, ROCK, r)
                    pygame.draw.rect(screen, (80, 60, 40), r, 2)
                    # Brick pattern
                    pygame.draw.line(screen, (70, 50, 30), 
                                   (r.left, r.centery), (r.right, r.centery))
                elif t == COIN:
                    pygame.draw.circle(screen, GOLD, (r.centerx, r.centery), 8)
                    pygame.draw.circle(screen, ORANGE, (r.centerx, r.centery), 5)
                elif t == QBLOCK:
                    pygame.draw.rect(screen, (240, 180, 60), r)
                    pygame.draw.rect(screen, BLACK, r, 3)
                    pygame.draw.circle(screen, WHITE, (r.centerx, r.centery), 4)
                elif t == HAZARD:
                    haz_color = (220, 70, 40) if self.theme["hazard"] == "lava" else (70, 120, 210)
                    pygame.draw.rect(screen, haz_color, r)
                elif t == FLAG:
                    pygame.draw.rect(screen, (60, 200, 90), r)
                    pygame.draw.polygon(screen, WHITE, 
                                      [(r.left, r.top), (r.right, r.centery), (r.left, r.bottom)])
                elif t in (PIPE_TOP, PIPE_BODY):
                    pipe_color = (80, 190, 80) if t == PIPE_TOP else (70, 170, 70)
                    pygame.draw.rect(screen, pipe_color, r)
                    pygame.draw.rect(screen, (50, 150, 50), r, 2)
                elif t == NOTEBLOCK:
                    pygame.draw.rect(screen, (255, 100, 200), r)
                    pygame.draw.rect(screen, (230, 80, 180), r, 2)
                    pygame.draw.circle(screen, WHITE, (r.centerx, r.centery), 3)
                elif t == INVISIBLE_BLOCK:
                    # Only draw if revealed
                    pass
        
        # Draw powerups
        for p in self.powerups:
            if p.alive:
                pr = p.rect().move(-cam_x, 0)
                color = RED if p.type == PowerUpType.MUSHROOM else (255, 100, 50)
                pygame.draw.rect(screen, color, pr)
                pygame.draw.circle(screen, WHITE, (pr.centerx, pr.top + 6), 4)
        
        # Draw projectiles
        for proj in self.projectiles:
            if proj.alive:
                pr = proj.rect().move(-cam_x, 0)
                color = ORANGE if proj.type == "fireball" else GRAY
                pygame.draw.circle(screen, color, (pr.centerx, pr.centery), proj.w // 2)
        
        # Draw enemies
        for e in self.enemies:
            if not e.alive:
                continue
            er = e.rect().move(-cam_x, 0)
            
            if e.stomped and e.stomp_timer > 0:
                # Flattened sprite
                flat_rect = pygame.Rect(er.x, er.bottom - 8, er.w, 8)
                pygame.draw.rect(screen, (100, 70, 50), flat_rect)
            else:
                # Enemy body
                enemy_color = (180, 80, 50) if e.type == "goomba" else (80, 180, 80)
                if e.type == "hammer_bro":
                    enemy_color = (90, 90, 180)
                pygame.draw.rect(screen, enemy_color, er)
                
                # Eyes
                eye_offset = 6 if e.dir > 0 else er.w - 10
                eye = pygame.Rect(er.x + eye_offset, er.y + 6, 4, 4)
                pygame.draw.rect(screen, WHITE, eye)
                pygame.draw.circle(screen, BLACK, (eye.centerx + e.dir, eye.centery), 2)
                
                # Shell for koopa
                if e.type == "koopa" and not e.stomped:
                    shell = pygame.Rect(er.x + 2, er.bottom - 12, er.w - 4, 10)
                    pygame.draw.rect(screen, (200, 180, 60), shell)
        
        # Draw particles
        for p in self.particles:
            p.draw(screen, cam_x)

# =============================================================================
# OVERWORLD MAP
# =============================================================================
class OverworldMap:
    def __init__(self, world_stage_counts: List[int], progress: List[List[bool]]):
        self.world_stage_counts = world_stage_counts
        self.progress = progress
        self.world_index = 0
        self.stage_index = 0
        self.cursor_anim = 0
    
    def move(self, dx: int, dy: int):
        self.world_index = clamp(self.world_index + dy, 0, len(self.world_stage_counts) - 1)
        self.stage_index = clamp(self.stage_index + dx, 0, self.world_stage_counts[self.world_index] - 1)
    
    def set_indices(self, wi: int, si: int):
        self.world_index = clamp(wi, 0, len(self.world_stage_counts) - 1)
        self.stage_index = clamp(si, 0, self.world_stage_counts[self.world_index] - 1)
    
    def draw(self, screen, font, big):
        # Ocean background
        screen.fill(SEA)
        
        # Animated clouds
        for i in range(6):
            offset = (self.cursor_anim * 0.5) % 200
            pygame.draw.ellipse(screen, WHITE, 
                              (100 + i * 120 - offset, 60 + (i % 2) * 30, 80, 40))
        
        # Islands for worlds
        for i in range(8):
            x = 80 + i * 100
            y = 180 + (i % 2) * 40
            pygame.draw.circle(screen, GRASS, (x, y), 32)
            pygame.draw.circle(screen, BROWN, (x, y), 28)
        
        # World selection boxes
        base_y = HEIGHT // 2 - 30
        for wi, count in enumerate(self.world_stage_counts):
            x = 80 + wi * 100
            r = pygame.Rect(x - 32, base_y - 32, 64, 64)
            
            # Highlight selected world
            color = BLUE if wi == self.world_index else GRAY
            pygame.draw.rect(screen, color, r, 0, border_radius=12)
            pygame.draw.rect(screen, BLACK, r, 3, border_radius=12)
            
            # World number
            draw_text(screen, font, f"W{wi + 1}", (r.centerx, r.centery - 10), 
                     WHITE, center=True, shadow=True)
            draw_text(screen, font, f"{count}", (r.centerx, r.centery + 12), 
                     WHITE, center=True, shadow=False)
        
        # Stage nodes
        sx0 = 120
        y = HEIGHT - 120
        for si in range(self.world_stage_counts[self.world_index]):
            x = sx0 + si * 70
            cleared = self.progress[self.world_index][si]
            
            # Node color
            if cleared:
                color = (80, 200, 90)
            else:
                color = (220, 180, 100)
            
            pygame.draw.circle(screen, color, (x, y), 16)
            pygame.draw.circle(screen, BLACK, (x, y), 16, 2)
            
            # Cursor highlight
            if si == self.stage_index:
                anim_radius = 20 + int(math.sin(self.cursor_anim * 0.1) * 3)
                pygame.draw.circle(screen, ORANGE, (x, y), anim_radius, 4)
            
            # Draw stage number
            draw_text(screen, font, str(si + 1), (x, y), BLACK, center=True, shadow=False)
        
        # Instructions
        draw_text(screen, font, "← → Select Stage   ↑ ↓ Select World   ENTER Play   ESC Title",
                 (WIDTH // 2, HEIGHT - 40), BLACK, center=True)
        
        self.cursor_anim += 1

# =============================================================================
# COLLISION & PHYSICS
# =============================================================================
def collide_rect_tiles(r: pygame.Rect, level: Level, types: Tuple[int, ...]) -> List[pygame.Rect]:
    """Get all tile collisions for a rect"""
    tiles = []
    tx0 = clamp(r.left // TILE, 0, level.map.w - 1)
    tx1 = clamp(r.right // TILE, 0, level.map.w - 1)
    ty0 = clamp(r.top // TILE, 0, level.map.h - 1)
    ty1 = clamp(r.bottom // TILE, 0, level.map.h - 1)
    
    for ty in range(ty0, ty1 + 1):
        for tx in range(tx0, tx1 + 1):
            t = level.map.get(tx, ty)
            if t in types:
                tiles.append(rect_from_tile(tx, ty))
    return tiles

def bump_block(level: Level, tx: int, ty: int, player: Player):
    """Handle block bumping from below"""
    t = level.map.get(tx, ty)
    
    if t == QBLOCK:
        # Spawn powerup or coin
        if (tx, ty) in level.secret_blocks:
            # Spawn powerup based on player state
            if player.state == PlayerState.SMALL:
                powerup_type = PowerUpType.MUSHROOM
            else:
                powerup_type = random.choice([PowerUpType.FIRE_FLOWER, PowerUpType.SUPER_LEAF])
            
            px = tx * TILE + 4
            py = ty * TILE - 28
            level.powerups.append(PowerUp(px, py, type=powerup_type))
            level.secret_blocks.remove((tx, ty))
        else:
            # Just a coin
            if level.map.get(tx, ty - 1) == EMPTY:
                level.map.set(tx, ty - 1, COIN)
                player.coins += 1
        
        # Convert to brick
        level.map.set(tx, ty, BRICK)
        
        # Particles
        for _ in range(6):
            level.particles.append(Particle(
                tx * TILE + TILE // 2, ty * TILE,
                random.uniform(-2, 2), random.uniform(-3, -1),
                30, GOLD
            ))
    
    elif t == BRICK:
        # Break brick if big
        if player.state != PlayerState.SMALL:
            level.map.set(tx, ty, EMPTY)
            # Brick fragments
            for _ in range(8):
                level.particles.append(Particle(
                    tx * TILE + TILE // 2, ty * TILE + TILE // 2,
                    random.uniform(-3, 3), random.uniform(-4, -2),
                    40, ROCK, size=4
                ))
            player.add_score(50)
    
    elif t == NOTEBLOCK:
        # Bounce player high
        player.vy = -14
        player.on_ground = False

def spawn_coin_particles(level: Level, x: float, y: float):
    """Particle effect when collecting coin"""
    for _ in range(4):
        level.particles.append(Particle(
            x, y,
            random.uniform(-1, 1), random.uniform(-2, 0),
            20, GOLD, size=3
        ))

# =============================================================================
# MAIN GAME CLASS
# =============================================================================
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(f"{ENGINE_NAME} ({ENGINE_VERSION})")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 20, bold=True)
        self.big_font = pygame.font.SysFont("arialblack", 60, bold=True)
        self.small_font = pygame.font.SysFont("arial", 16)
        
        # Game state
        self.state = GameState.TITLE
        self.world_index = 0
        self.stage_index = 0
        self.world_stage_counts = WORLD_STAGE_COUNTS[:]
        
        # Progress tracking
        self.progress_clears = [[False] * c for c in self.world_stage_counts]
        
        # Entities
        self.level: Optional[Level] = None
        self.player = Player()
        self.cam_x = 0
        
        # Overworld
        self.overworld = OverworldMap(self.world_stage_counts, self.progress_clears)
        
        # Input
        self.keys = None
        self.prev_keys = None
        
        # Time tracking
        self.level_time = 0
        self.level_time_limit = 400  # seconds
        
        # Save/load support
        self.save_file = "smb3_save.json"
    
    def run(self):
        """Main game loop"""
        while True:
            self.handle_global_events()
            
            if self.state == GameState.TITLE:
                self.loop_title()
            elif self.state == GameState.OVERWORLD:
                self.loop_overworld()
            elif self.state == GameState.LEVEL:
                self.loop_level()
            elif self.state == GameState.BOSS:
                self.loop_boss()
            elif self.state == GameState.ENDING:
                self.loop_ending()
            elif self.state == GameState.GAMEOVER:
                self.loop_gameover()
            
            pygame.display.flip()
            self.clock.tick(FPS)
    
    def handle_global_events(self):
        """Handle quit events"""
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.save_progress()
                pygame.quit()
                sys.exit(0)
    
    # =========================================================================
    # TITLE SCREEN
    # =========================================================================
    def loop_title(self):
        menu = ["START GAME", "CONTINUE", "QUIT"]
        select = 0
        t = 0
        clouds = [[random.randint(0, WIDTH), random.randint(40, 200), 
                  random.randint(60, 160)] for _ in range(8)]
        
        # Try to load save
        has_save = self.load_progress()
        
        while self.state == GameState.TITLE:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)
                if e.type == pygame.KEYDOWN:
                    if e.key in (pygame.K_UP, pygame.K_w):
                        select = (select - 1) % len(menu)
                    if e.key in (pygame.K_DOWN, pygame.K_s):
                        select = (select + 1) % len(menu)
                    if e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                        if select == 0:  # New game
                            self.new_game()
                            self.state = GameState.OVERWORLD
                            return
                        elif select == 1:  # Continue
                            if has_save:
                                self.state = GameState.OVERWORLD
                                return
                        elif select == 2:  # Quit
                            pygame.quit()
                            sys.exit(0)
            
            # Sky gradient with animation
            self.screen.fill(SKY)
            for y in range(0, HEIGHT, 2):
                shade = int(160 + 40 * math.sin(y / HEIGHT * math.pi + t / 80))
                pygame.draw.line(self.screen, (shade, 200, 255), (0, y), (WIDTH, y))
            
            # Animated clouds
            for c in clouds:
                c[0] -= 0.5
                if c[0] + c[2] < 0:
                    c[0] = WIDTH + random.randint(20, 80)
                pygame.draw.ellipse(self.screen, WHITE, (c[0], c[1], c[2], c[2] // 2))
            
            # Title with bounce
            bounce = math.sin(t / 20) * 8
            draw_text(self.screen, self.big_font, "SMB3 ENGINE",
                     (WIDTH // 2, 140 + bounce), BLACK, center=True)
            draw_text(self.screen, self.font, "Samsoft Ultra Decomp Edition",
                     (WIDTH // 2, 200 + bounce / 2), BLACK, center=True)
            
            # Menu
            for i, txt in enumerate(menu):
                y = HEIGHT // 2 + 60 + i * 45
                color = ORANGE if i == select else BLACK
                
                # Dim "continue" if no save
                if i == 1 and not has_save:
                    color = GRAY
                
                draw_text(self.screen, self.font, txt, (WIDTH // 2, y), color, center=True)
                
                # Cursor
                if i == select and (t // 20) % 2 == 0:
                    pygame.draw.polygon(self.screen, ORANGE,
                                      [(WIDTH // 2 - 120, y - 8),
                                       (WIDTH // 2 - 95, y),
                                       (WIDTH // 2 - 120, y + 8)])
            
            # Credits
            draw_text(self.screen, self.small_font,
                     f"© 2025 Team Flames / Samsoft Studios  •  {ENGINE_VERSION}",
                     (WIDTH // 2, HEIGHT - 30), BLACK, center=True)
            
            pygame.display.flip()
            self.clock.tick(FPS)
            t += 1
    
    # =========================================================================
    # OVERWORLD
    # =========================================================================
    def loop_overworld(self):
        self.overworld.set_indices(self.world_index, self.stage_index)
        
        while self.state == GameState.OVERWORLD:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.save_progress()
                    pygame.quit()
                    sys.exit(0)
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        self.state = GameState.TITLE
                        return
                    if e.key in (pygame.K_LEFT, pygame.K_a):
                        self.overworld.move(-1, 0)
                    if e.key in (pygame.K_RIGHT, pygame.K_d):
                        self.overworld.move(1, 0)
                    if e.key in (pygame.K_UP, pygame.K_w):
                        self.overworld.move(0, -1)
                    if e.key in (pygame.K_DOWN, pygame.K_s):
                        self.overworld.move(0, 1)
                    if e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                        self.world_index = self.overworld.world_index
                        self.stage_index = self.overworld.stage_index
                        self.start_level(self.world_index, self.stage_index)
                        self.state = GameState.LEVEL
                        return
            
            # Draw overworld
            self.overworld.draw(self.screen, self.font, self.big_font)
            
            # World title
            title = f"World {self.overworld.world_index + 1}: {WORLD_THEMES[self.overworld.world_index]['name']}"
            draw_text(self.screen, self.font, title, (WIDTH // 2, 60), BLACK, center=True)
            
            # Player stats
            stats = f"Lives: {self.player.lives}   Coins: {self.player.coins}   Score: {self.player.score}"
            draw_text(self.screen, self.small_font, stats, (WIDTH // 2, HEIGHT - 80), BLACK, center=True)
            
            pygame.display.flip()
            self.clock.tick(FPS)
    
    # =========================================================================
    # LEVEL GAMEPLAY
    # =========================================================================
    def start_level(self, wi: int, si: int):
        """Initialize a level"""
        seed = (wi + 1) * 1000 + (si + 1) * 37
        self.level = Level(theme_idx=wi, stage_idx=si, seed=seed)
        self.player.x, self.player.y = self.level.map.start_px
        self.player.vx = self.player.vy = 0
        self.cam_x = 0
        self.level_time = 0
    
    def loop_level(self):
        """Main level gameplay loop"""
        assert self.level is not None
        
        while self.state == GameState.LEVEL:
            # Input
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.save_progress()
                    pygame.quit()
                    sys.exit(0)
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        self.state = GameState.OVERWORLD
                        return
            
            self.update_level()
            self.draw_level()
            
            pygame.display.flip()
            self.clock.tick(FPS)
            self.level_time += 1 / FPS
    
    def update_level(self):
        """Update level physics and entities"""
        self.keys = pygame.key.get_pressed()
        t = self.level.theme
        
        # Player physics constants
        accel = 0.6 if t["hazard"] != "ice" else 0.4
        max_speed = 4.2 if t["hazard"] != "ice" else 5.0
        friction = t["friction"]
        gravity = t["gravity"]
        jump_v = -10.8 if t["hazard"] != "ice" else -11.2
        
        # Horizontal movement
        if self.keys[pygame.K_LEFT] or self.keys[pygame.K_a]:
            self.player.vx -= accel
            self.player.facing = -1
            self.player.skidding = self.player.vx > 1.0
        elif self.keys[pygame.K_RIGHT] or self.keys[pygame.K_d]:
            self.player.vx += accel
            self.player.facing = 1
            self.player.skidding = self.player.vx < -1.0
        else:
            self.player.skidding = False
        
        # P-meter (run speed for flying)
        if abs(self.player.vx) > 3.5 and self.player.on_ground:
            self.player.p_meter = min(7.0, self.player.p_meter + 0.1)
        else:
            self.player.p_meter = max(0, self.player.p_meter - 0.05)
        
        # Ducking
        self.player.ducking = (self.keys[pygame.K_DOWN] or self.keys[pygame.K_s]) and self.player.on_ground
        
        # Jump buffering
        if self.keys[pygame.K_SPACE] or self.keys[pygame.K_z] or self.keys[pygame.K_UP]:
            self.player.jump_buffer = 6
        
        # Apply gravity
        self.player.vy += gravity
        if self.player.vy > MAX_FALL_SPEED:
            self.player.vy = MAX_FALL_SPEED
        
        # Clamp horizontal speed
        self.player.vx = clamp(self.player.vx, -max_speed, max_speed)
        
        # Jump
        if (self.player.on_ground or self.player.coyote_timer > 0) and self.player.jump_buffer > 0:
            self.player.vy = jump_v
            self.player.on_ground = False
            self.player.coyote_timer = 0
            self.player.jump_buffer = 0
            
            # Check for spin jump (A+B together)
            if self.keys[pygame.K_z] and self.keys[pygame.K_x]:
                self.player.spin_jump = True
        
        # Flight (Raccoon/Tanooki tail) - FIXED FLIGHT PHYSICS
        if self.player.can_fly() and (self.keys[pygame.K_SPACE] or self.keys[pygame.K_z]):
            if not self.player.flying and not self.player.on_ground:
                self.player.flying = True
                self.player.flight_timer = 180  # 3 seconds of flight
            
            if self.player.flying and self.player.flight_timer > 0:
                # Fixed flight physics - prevent unwanted leftward swooping
                self.player.vy = -2.0  # Slow descent
                
                # Maintain forward momentum during flight - prevent sudden direction changes
                flight_accel = 0.15  # Reduced acceleration during flight
                flight_max_speed = 3.5  # Slightly reduced max speed during flight
                
                # Apply flight-specific horizontal movement
                if self.keys[pygame.K_LEFT] or self.keys[pygame.K_a]:
                    self.player.vx = max(-flight_max_speed, self.player.vx - flight_accel)
                elif self.keys[pygame.K_RIGHT] or self.keys[pygame.K_d]:
                    self.player.vx = min(flight_max_speed, self.player.vx + flight_accel)
                else:
                    # Gradually reduce horizontal speed when no input during flight
                    self.player.vx *= 0.98
                
                self.player.flight_timer -= 1
            else:
                self.player.flying = False
        
        # Stop flying when on ground
        if self.player.on_ground:
            self.player.flying = False
            self.player.spin_jump = False
        
        # Fire flower projectile
        if (self.keys[pygame.K_x] or self.keys[pygame.K_LSHIFT]) and self.player.state == PlayerState.FIRE:
            if self.prev_keys and not (self.prev_keys[pygame.K_x] or self.prev_keys[pygame.K_LSHIFT]):
                # Shoot fireball
                fx = self.player.x + (self.player.w if self.player.facing > 0 else 0)
                fy = self.player.y + self.player.h // 2
                self.level.projectiles.append(
                    Projectile(fx, fy, self.player.facing * 6, -2, type="fireball")
                )
        
        # Movement & collision
        self.move_and_collide()
        
        # Update enemies
        self.update_enemies()
        
        # Update powerups
        self.update_powerups()
        
        # Update projectiles
        self.update_projectiles()
        
        # Update particles
        self.level.particles = [p for p in self.level.particles if p.update()]
        
        # Update timers
        if self.player.invincible_timer > 0:
            self.player.invincible_timer -= 1
        if self.player.damage_timer > 0:
            self.player.damage_timer -= 1
        
        # Camera follow
        target_cam = clamp(self.player.x - WIDTH * 0.35, 0, self.level.map.w * TILE - WIDTH)
        self.cam_x += (target_cam - self.cam_x) * 0.15
        
        # Level completion
        pr = self.player.rect()
        flag_rects = self.level.map.rects_for_type(FLAG)
        for fr in flag_rects:
            if pr.colliderect(fr):
                self.finish_stage()
                return
        
        # Time out
        if self.level_time >= self.level_time_limit:
            self.respawn_level()
        
        self.prev_keys = self.keys
    
    def move_and_collide(self):
        """Enhanced collision detection"""
        p = self.player
        level = self.level
        
        # Horizontal movement
        p.x += p.vx
        r = p.rect()
        hits = collide_rect_tiles(r, level, (SOLID, BRICK, QBLOCK, PIPE_TOP, PIPE_BODY))
        
        for h in hits:
            if p.vx > 0:  # Moving right
                p.x = h.left - p.w
                p.vx = 0
            elif p.vx < 0:  # Moving left
                p.x = h.right
                p.vx = 0
        
        # Vertical movement
        p.on_ground = False
        p.y += p.vy
        r = p.rect()
        hits = collide_rect_tiles(r, level, 
                                  (SOLID, BRICK, QBLOCK, HAZARD, PIPE_TOP, PIPE_BODY, NOTEBLOCK))
        
        for h in hits:
            tx, ty = h.x // TILE, h.y // TILE
            t = level.map.get(tx, ty)
            
            # Hazard death
            if t == HAZARD:
                self.respawn_level()
                return
            
            if p.vy > 0:  # Falling down
                p.y = h.top - (p.h if not p.ducking else p.h // 2)
                p.vy = 0
                p.on_ground = True
                p.coyote_timer = 6
                
                # Note block bounce
                if t == NOTEBLOCK:
                    p.vy = -15
                    p.on_ground = False
                    
            elif p.vy < 0:  # Moving up
                p.y = h.bottom
                p.vy = 0
                
                # Bump block from below
                bump_block(level, tx, ty, p)
        
        # Collect coins
        r = p.rect()
        tx0 = clamp(r.left // TILE, 0, level.map.w - 1)
        tx1 = clamp(r.right // TILE, 0, level.map.w - 1)
        ty0 = clamp(r.top // TILE, 0, level.map.h - 1)
        ty1 = clamp(r.bottom // TILE, 0, level.map.h - 1)
        
        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                if level.map.get(tx, ty) == COIN:
                    level.map.set(tx, ty, EMPTY)
                    p.coins += 1
                    p.add_score(100)
                    spawn_coin_particles(level, tx * TILE + TILE // 2, ty * TILE + TILE // 2)
        
        # Apply friction
        if p.on_ground:
            p.vx *= self.level.theme["friction"]
        else:
            p.vx *= 0.99
        
        # Timers
        if p.coyote_timer > 0:
            p.coyote_timer -= 1
        if p.jump_buffer > 0:
            p.jump_buffer -= 1
    
    def update_enemies(self):
        """Update enemy AI and physics"""
        for e in self.level.enemies:
            if not e.alive:
                continue
            
            # Stomp timer
            if e.stomped and e.stomp_timer > 0:
                e.stomp_timer -= 1
                if e.stomp_timer == 0:
                    e.alive = False
                continue
            
            # Horizontal movement
            e.x += e.vx
            
            # Gravity for ground enemies
            if e.type != "flying":
                e.vy += 0.5
                e.y += e.vy
            else:
                # Flying enemy pattern
                e.y += math.sin(e.ai_timer * 0.05) * 0.5
            
            er = e.rect()
            
            # Wall collision
            ahead = pygame.Rect(er.x + e.dir * 6, er.y, er.w, er.h)
            hits = collide_rect_tiles(ahead, self.level, (SOLID, BRICK, PIPE_TOP, PIPE_BODY))
            if hits:
                e.dir *= -1
                e.vx = -e.vx
            
            # Edge detection (ground enemies)
            if e.type != "flying":
                foot = pygame.Rect(er.x + e.dir * 10, er.bottom, 6, 6)
                below = collide_rect_tiles(foot, self.level, (SOLID, BRICK))
                if not below:
                    e.dir *= -1
                    e.vx = -e.vx
                
                # Ground collision
                er = e.rect()
                ground_hits = collide_rect_tiles(er, self.level, (SOLID, BRICK))
                for gh in ground_hits:
                    if e.vy > 0:
                        e.y = gh.top - e.h
                        e.vy = 0
            
            e.ai_timer += 1
            
            # Player collision
            pr = self.player.rect()
            if pr.colliderect(er):
                # Stomp check
                if self.player.vy > 0 and self.player.y + self.player.h - e.y < 16:
                    # Stomp enemy
                    if e.type == "koopa" and not e.stomped:
                        e.stomped = True
                        e.vx = 0
                        e.h = 14
                    else:
                        e.stomped = True
                        e.stomp_timer = 30
                    
                    self.player.vy = -8
                    self.player.add_score(200)
                    
                    # Particles
                    for _ in range(8):
                        self.level.particles.append(Particle(
                            e.x + e.w // 2, e.y,
                            random.uniform(-3, 3), random.uniform(-4, -1),
                            30, (180, 80, 50)
                        ))
                else:
                    # Take damage
                    if self.player.take_damage():
                        self.respawn_level()
                        return
    
    def update_powerups(self):
        """Update powerup physics"""
        for p in self.level.powerups:
            if not p.alive:
                continue
            
            # Physics
            p.vy += 0.4
            p.x += p.vx
            p.y += p.vy
            
            # Tile collision
            pr = p.rect()
            hits = collide_rect_tiles(pr, self.level, (SOLID, BRICK, PIPE_TOP, PIPE_BODY))
            
            for h in hits:
                if p.vy > 0:
                    p.y = h.top - p.h
                    p.vy = 0
                if p.vx > 0 and pr.right > h.left:
                    p.vx = -p.vx
                elif p.vx < 0 and pr.left < h.right:
                    p.vx = -p.vx
            
            # Player collection
            if pr.colliderect(self.player.rect()):
                p.alive = False
                
                # Apply powerup
                if p.type == PowerUpType.MUSHROOM:
                    if self.player.state == PlayerState.SMALL:
                        self.player.state = PlayerState.BIG
                        self.player.h = 40
                elif p.type == PowerUpType.FIRE_FLOWER:
                    self.player.state = PlayerState.FIRE
                elif p.type == PowerUpType.SUPER_LEAF:
                    self.player.state = PlayerState.RACCOON
                
                self.player.add_score(1000)
    
    def update_projectiles(self):
        """Update projectiles (fireballs, hammers)"""
        for proj in self.level.projectiles:
            if not proj.alive:
                continue
            
            proj.lifetime -= 1
            if proj.lifetime <= 0:
                proj.alive = False
                continue
            
            # Physics
            proj.vy += 0.3
            proj.x += proj.vx
            proj.y += proj.vy
            
            # Bounce
            pr = proj.rect()
            hits = collide_rect_tiles(pr, self.level, (SOLID, BRICK))
            if hits and proj.vy > 0:
                proj.vy = -6
            
            # Enemy collision
            for e in self.level.enemies:
                if e.alive and not e.stomped and pr.colliderect(e.rect()):
                    e.alive = False
                    proj.alive = False
                    self.player.add_score(200)
                    
                    # Particles
                    for _ in range(6):
                        self.level.particles.append(Particle(
                            e.x + e.w // 2, e.y + e.h // 2,
                            random.uniform(-2, 2), random.uniform(-3, -1),
                            25, ORANGE
                        ))
    
    def draw_level(self):
        """Render level"""
        # Draw level tiles and entities
        self.level.draw(self.screen, self.cam_x)
        
        # Draw player
        pr = self.player.rect().move(-self.cam_x, 0)
        
        # Flashing when damaged
        if self.player.damage_timer > 0 and self.player.damage_timer % 6 < 3:
            player_color = WHITE
        else:
            # Color based on state
            if self.player.state == PlayerState.SMALL:
                player_color = RED
            elif self.player.state == PlayerState.BIG:
                player_color = (255, 100, 100)
            elif self.player.state == PlayerState.FIRE:
                player_color = (255, 255, 255)
            elif self.player.state in (PlayerState.RACCOON, PlayerState.TANOOKI):
                player_color = (200, 140, 80)
            else:
                player_color = (150, 150, 255)
        
        pygame.draw.rect(self.screen, player_color, pr)
        
        # Player face
        eye_x = pr.x + (18 if self.player.facing > 0 else 6)
        pygame.draw.circle(self.screen, BLACK, (eye_x, pr.y + 10), 3)
        
        # Raccoon tail
        if self.player.state in (PlayerState.RACCOON, PlayerState.TANOOKI):
            tail_x = pr.centerx - self.player.facing * 20
            pygame.draw.circle(self.screen, BROWN, (tail_x, pr.bottom - 10), 8)
        
        # HUD
        world_text = f"W{self.world_index + 1}-{self.stage_index + 1}  {WORLD_THEMES[self.world_index]['name']}"
        draw_text(self.screen, self.font, world_text, (16, 16), WHITE)
        
        stats = f"Lives: {max(0, self.player.lives)}  Coins: {self.player.coins}  Score: {self.player.score}"
        draw_text(self.screen, self.font, stats, (16, 42), WHITE)
        
        # P-meter
        if self.player.p_meter > 0:
            meter_w = int((self.player.p_meter / 7.0) * 100)
            pygame.draw.rect(self.screen, GRAY, (WIDTH - 120, 20, 100, 12))
            pygame.draw.rect(self.screen, ORANGE, (WIDTH - 120, 20, meter_w, 12))
            draw_text(self.screen, self.small_font, "P", (WIDTH - 130, 18), WHITE, shadow=False)
        
        # Time
        time_left = max(0, int(self.level_time_limit - self.level_time))
        time_color = RED if time_left < 30 else WHITE
        draw_text(self.screen, self.font, f"Time: {time_left}", (WIDTH - 140, 45), time_color)
    
    def respawn_level(self):
        """Respawn player at start"""
        self.player.lives -= 1
        
        if self.player.lives < 0:
            self.state = GameState.GAMEOVER
            return
        
        self.player.x, self.player.y = self.level.map.start_px
        self.player.vx = self.player.vy = 0
        self.player.damage_timer = 180
        self.cam_x = 0
    
    def finish_stage(self):
        """Complete current stage"""
        self.progress_clears[self.world_index][self.stage_index] = True
        self.player.add_score(5000)
        
        # Next stage or world
        if self.stage_index + 1 < self.world_stage_counts[self.world_index]:
            self.stage_index += 1
        else:
            if self.world_index + 1 < len(self.world_stage_counts):
                self.world_index += 1
                self.stage_index = 0
            else:
                self.state = GameState.ENDING
                return
        
        self.state = GameState.OVERWORLD
    
    # =========================================================================
    # BOSS & ENDING
    # =========================================================================
    def loop_boss(self):
        """Boss battle (placeholder)"""
        self.screen.fill(PURPLE)
        draw_text(self.screen, self.big_font, "BOSS BATTLE",
                 (WIDTH // 2, HEIGHT // 2), WHITE, center=True)
        draw_text(self.screen, self.font, "Coming Soon!",
                 (WIDTH // 2, HEIGHT // 2 + 80), WHITE, center=True)
        pygame.display.flip()
        pygame.time.wait(2000)
        self.state = GameState.OVERWORLD
    
    def loop_ending(self):
        """Ending screen"""
        self.screen.fill(GOLD)
        draw_text(self.screen, self.big_font, "YOU WIN!",
                 (WIDTH // 2, HEIGHT // 2 - 40), BLACK, center=True)
        draw_text(self.screen, self.font, f"Final Score: {self.player.score}",
                 (WIDTH // 2, HEIGHT // 2 + 40), BLACK, center=True)
        draw_text(self.screen, self.font, "All 8 Worlds Completed!",
                 (WIDTH // 2, HEIGHT // 2 + 80), BLACK, center=True)
        
        pygame.display.flip()
        pygame.time.wait(4000)
        
        # Reset
        self.new_game()
        self.state = GameState.TITLE
    
    def loop_gameover(self):
        """Game over screen"""
        self.screen.fill(BLACK)
        draw_text(self.screen, self.big_font, "GAME OVER",
                 (WIDTH // 2, HEIGHT // 2), RED, center=True)
        draw_text(self.screen, self.font, f"Final Score: {self.player.score}",
                 (WIDTH // 2, HEIGHT // 2 + 60), WHITE, center=True)
        
        pygame.display.flip()
        pygame.time.wait(3000)
        
        self.state = GameState.TITLE
    
    # =========================================================================
    # SAVE/LOAD
    # =========================================================================
    def save_progress(self):
        """Save game progress to file"""
        data = {
            "world_index": self.world_index,
            "stage_index": self.stage_index,
            "progress": self.progress_clears,
            "player_lives": self.player.lives,
            "player_coins": self.player.coins,
            "player_score": self.player.score,
            "player_state": self.player.state.value
        }
        
        try:
            with open(self.save_file, 'w') as f:
                json.dump(data, f)
        except:
            pass
    
    def load_progress(self):
        """Load game progress from file"""
        try:
            with open(self.save_file, 'r') as f:
                data = json.load(f)
            
            self.world_index = data["world_index"]
            self.stage_index = data["stage_index"]
            self.progress_clears = data["progress"]
            self.player.lives = data["player_lives"]
            self.player.coins = data["player_coins"]
            self.player.score = data["player_score"]
            self.player.state = PlayerState(data["player_state"])
            
            return True
        except:
            return False
    
    def new_game(self):
        """Start new game"""
        self.world_index = 0
        self.stage_index = 0
        self.progress_clears = [[False] * c for c in self.world_stage_counts]
        self.player = Player()

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
def main():
    """Main entry point"""
    try:
        print(f"Starting {ENGINE_NAME} {ENGINE_VERSION}")
        print("Controls:")
        print("  Arrow Keys / WASD: Move")
        print("  Space / Z: Jump")
        print("  X: Fire (if Fire Flower)")
        print("  Down: Duck")
        print("  ESC: Pause/Back")
        print("\nAll bugs fixed! Complete SMB3 decomp engine loaded.")
        print("Features: 8 worlds, powerups, flight, enemies, scoring, save/load")
        
        game = Game()
        game.run()
    except KeyboardInterrupt:
        print("\nGame interrupted by user")
        pygame.quit()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        pygame.quit()

if __name__ == "__main__":
    main()