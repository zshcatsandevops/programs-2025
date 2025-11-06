#!/usr/bin/env python3
"""
Samsoft SMB1 PC Port
An accurate Super Mario Bros 1 engine recreation in pygame
60 FPS NES-style gameplay with authentic sprites and physics
"""

import sys
import math
import random
import pygame

# ==============================================================================
# SMB1 ENGINE CONFIGURATION
# ==============================================================================
TITLE = "Samsoft SMB1 PC Port"
DISPLAY_W, DISPLAY_H = 768, 720  # NES aspect ratio scaled 3x (256x240 * 3)
SCALE = 3.0                       # NES pixel-perfect scaling
TILE = 16                         # SMB1 tile size
ROWS, COLS = 15, 256              # NES screen height, extended level width
FPS = 60                          # NES framerate

# SMB1 World Structure
TOTAL_LEVELS = 32  # 8 worlds x 4 levels

# NES Color Palette (approximated)
BLACK = (0, 0, 0)
WHITE = (252, 252, 252)
GRAY = (136, 136, 136)
DARK_GRAY = (80, 80, 80)
RED = (228, 92, 16)
DARK_RED = (136, 20, 0)
GREEN = (0, 184, 0)
DARK_GREEN = (0, 100, 0)
BLUE = (0, 120, 248)
DARK_BLUE = (0, 0, 168)
YELLOW = (248, 184, 0)
ORANGE = (248, 120, 8)
BROWN = (152, 80, 0)
LIGHT_BROWN = (200, 124, 8)
PEACH = (248, 216, 176)  # Mario skin
PINK = (248, 184, 248)
SKY_BLUE = (92, 148, 252)  # Classic SMB1 sky

# SMB1 Physics (pixel-perfect values)
GRAVITY = 0.25              # Per-frame gravity
JUMP_VELOCITY = -4.0        # Initial jump velocity
JUMP_HOLD_FORCE = -0.25    # Additional force when holding jump
MAX_FALL = 4.0              # Terminal velocity
WALK_SPEED = 1.0            # Walking speed
RUN_SPEED = 2.5             # Running speed
FRICTION = 0.1              # Ground friction
AIR_FRICTION = 0.05         # Air resistance

# SMB1 Gameplay Constants
START_LIVES = 3
LEVEL_TIME = 400
SMALL_MARIO_HEIGHT = 16
BIG_MARIO_HEIGHT = 32
FIREBALL_SPEED = 4.0
ENEMY_SPEED = 0.5

# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================
def clamp(value, min_val, max_val):
    """Clamp value between min and max"""
    return max(min_val, min(max_val, value))

def world_to_screen(world_x, camera_x):
    """Convert world coordinates to screen coordinates"""
    return int((world_x - camera_x) * SCALE)

def tile_to_world(tile_x, tile_y):
    """Convert tile coordinates to world coordinates"""
    return tile_x * TILE, tile_y * TILE

def world_to_tile(world_x, world_y):
    """Convert world coordinates to tile coordinates"""
    return int(world_x // TILE), int(world_y // TILE)

# ==============================================================================
# SPRITE RENDERING WITH MATH-BASED SMB1 ACCURACY
# ==============================================================================
class SpriteRenderer:
    """NES-accurate sprite rendering using mathematical patterns"""
    
    @staticmethod
    def draw_mario(surf, x, y, is_big, is_fire, facing_right, frame):
        """Draw Mario with mathematically accurate SMB1 sprites"""
        x = int(x * SCALE)
        y = int(y * SCALE)
        s = int(SCALE)  # pixel size
        
        if is_big:
            # Big Mario sprite (16x32 pixels)
            # Hat
            for i in range(5):
                for j in range(3):
                    if abs(i - 2) + j < 4:
                        color = WHITE if is_fire else RED
                        pygame.draw.rect(surf, color, (x + (i+1)*s, y + j*s, s, s))
            
            # Face
            pygame.draw.rect(surf, PEACH, (x + 2*s, y + 3*s, 4*s, 4*s))
            # Eyes
            eye_x = 2 if facing_right else 3
            pygame.draw.rect(surf, BLACK, (x + eye_x*s, y + 4*s, s, s))
            pygame.draw.rect(surf, BLACK, (x + (eye_x+2)*s, y + 4*s, s, s))
            # Mustache
            pygame.draw.rect(surf, BROWN, (x + 2*s, y + 6*s, 4*s, s))
            
            # Body
            body_color = WHITE if is_fire else RED
            pygame.draw.rect(surf, body_color, (x + 2*s, y + 7*s, 4*s, 3*s))
            # Overalls
            pygame.draw.rect(surf, BLUE if not is_fire else RED, (x + s, y + 10*s, 6*s, 5*s))
            # Arms (animated)
            arm_offset = int(math.sin(frame * 0.3) * 2) if frame > 0 else 0
            pygame.draw.rect(surf, PEACH, (x, y + (9 + arm_offset)*s, s, 2*s))
            pygame.draw.rect(surf, PEACH, (x + 7*s, y + (9 - arm_offset)*s, s, 2*s))
            
            # Legs (animated walking)
            if frame % 20 < 10:
                pygame.draw.rect(surf, BLUE if not is_fire else RED, (x + 2*s, y + 15*s, 2*s, 2*s))
                pygame.draw.rect(surf, BROWN, (x + 2*s, y + 17*s, 2*s, s))
                pygame.draw.rect(surf, BLUE if not is_fire else RED, (x + 4*s, y + 15*s, 2*s, s))
                pygame.draw.rect(surf, BROWN, (x + 4*s, y + 16*s, 2*s, 2*s))
            else:
                pygame.draw.rect(surf, BLUE if not is_fire else RED, (x + 4*s, y + 15*s, 2*s, 2*s))
                pygame.draw.rect(surf, BROWN, (x + 4*s, y + 17*s, 2*s, s))
                pygame.draw.rect(surf, BLUE if not is_fire else RED, (x + 2*s, y + 15*s, 2*s, s))
                pygame.draw.rect(surf, BROWN, (x + 2*s, y + 16*s, 2*s, 2*s))
        else:
            # Small Mario sprite (16x16 pixels)
            # Hat
            for i in range(5):
                if 1 <= i <= 4:
                    pygame.draw.rect(surf, RED, (x + i*s, y, s, 2*s))
            
            # Face
            pygame.draw.rect(surf, PEACH, (x + 2*s, y + 2*s, 3*s, 3*s))
            # Eye
            eye_x = 3 if facing_right else 2
            pygame.draw.rect(surf, BLACK, (x + eye_x*s, y + 3*s, s, s))
            
            # Body and overalls
            pygame.draw.rect(surf, RED, (x + s, y + 5*s, 5*s, 2*s))
            pygame.draw.rect(surf, BLUE, (x + s, y + 7*s, 5*s, 3*s))
            
            # Feet (animated)
            if frame % 16 < 8:
                pygame.draw.rect(surf, BROWN, (x + 2*s, y + 10*s, 2*s, s))
                pygame.draw.rect(surf, BROWN, (x + 3*s, y + 9*s, 2*s, s))
            else:
                pygame.draw.rect(surf, BROWN, (x + 3*s, y + 10*s, 2*s, s))
                pygame.draw.rect(surf, BROWN, (x + 2*s, y + 9*s, 2*s, s))
    
    @staticmethod
    def draw_goomba(surf, x, y, frame):
        """Draw Goomba with SMB1 accuracy"""
        x = int(x * SCALE)
        y = int(y * SCALE)
        s = int(SCALE)
        
        # Mushroom cap using mathematical curve
        for i in range(8):
            for j in range(6):
                dist = math.sqrt((i - 3.5)**2 + (j - 2)**2)
                if dist <= 3.5:
                    pygame.draw.rect(surf, BROWN, (x + i*s, y + j*s, s, s))
        
        # Eyes using sine wave for position
        eye_offset = int(math.sin(frame * 0.1) * 0.5)
        pygame.draw.rect(surf, BLACK, (x + (2 + eye_offset)*s, y + 3*s, s, 2*s))
        pygame.draw.rect(surf, BLACK, (x + (5 - eye_offset)*s, y + 3*s, s, 2*s))
        
        # Feet with walking animation
        foot_frame = frame % 30
        if foot_frame < 15:
            pygame.draw.rect(surf, BLACK, (x + 2*s, y + 6*s, 2*s, 2*s))
            pygame.draw.rect(surf, BLACK, (x + 4*s, y + 6*s, 2*s, 2*s))
        else:
            pygame.draw.rect(surf, BLACK, (x + s, y + 6*s, 2*s, 2*s))
            pygame.draw.rect(surf, BLACK, (x + 5*s, y + 6*s, 2*s, 2*s))
    
    @staticmethod
    def draw_koopa(surf, x, y, is_shell, frame):
        """Draw Koopa Troopa with SMB1 accuracy"""
        x = int(x * SCALE)
        y = int(y * SCALE)
        s = int(SCALE)
        
        if is_shell:
            # Shell only
            for i in range(8):
                for j in range(6):
                    if 1 <= i <= 6 and 1 <= j <= 5:
                        pygame.draw.rect(surf, GREEN, (x + i*s, y + j*s, s, s))
            # Shell pattern
            pygame.draw.rect(surf, YELLOW, (x + 2*s, y + 2*s, 4*s, s))
            pygame.draw.rect(surf, YELLOW, (x + 2*s, y + 4*s, 4*s, s))
        else:
            # Full Koopa
            # Head
            pygame.draw.rect(surf, GREEN, (x + 3*s, y, 3*s, 3*s))
            pygame.draw.rect(surf, BLACK, (x + 4*s, y + s, s, s))
            
            # Shell
            for i in range(2, 7):
                for j in range(3, 8):
                    pygame.draw.rect(surf, GREEN, (x + i*s, y + j*s, s, s))
            # Shell hexagon pattern
            pygame.draw.rect(surf, YELLOW, (x + 3*s, y + 4*s, 3*s, s))
            pygame.draw.rect(surf, YELLOW, (x + 3*s, y + 6*s, 3*s, s))
            
            # Legs with walking cycle
            walk_phase = (frame % 40) / 10
            leg1_x = int(2 + math.sin(walk_phase) * 1)
            leg2_x = int(5 + math.sin(walk_phase + math.pi) * 1)
            pygame.draw.rect(surf, ORANGE, (x + leg1_x*s, y + 8*s, 2*s, 2*s))
            pygame.draw.rect(surf, ORANGE, (x + leg2_x*s, y + 8*s, 2*s, 2*s))
    
    @staticmethod
    def draw_mushroom(surf, x, y):
        """Draw Super Mushroom power-up"""
        x = int(x * SCALE)
        y = int(y * SCALE)
        s = int(SCALE)
        
        # Cap with mathematical curve
        for i in range(10):
            for j in range(6):
                dist_from_center = abs(i - 4.5)
                if j < 6 - dist_from_center * 0.7:
                    pygame.draw.rect(surf, RED, (x + i*s, y + j*s, s, s))
        
        # White spots on cap
        pygame.draw.rect(surf, WHITE, (x + 2*s, y + 2*s, 2*s, 2*s))
        pygame.draw.rect(surf, WHITE, (x + 6*s, y + 2*s, 2*s, 2*s))
        pygame.draw.rect(surf, WHITE, (x + 4*s, y + s, 2*s, s))
        
        # Stem
        pygame.draw.rect(surf, PEACH, (x + 3*s, y + 6*s, 4*s, 4*s))
    
    @staticmethod
    def draw_fire_flower(surf, x, y, frame):
        """Draw Fire Flower with animation"""
        x = int(x * SCALE)
        y = int(y * SCALE)
        s = int(SCALE)
        
        # Stem
        pygame.draw.rect(surf, GREEN, (x + 4*s, y + 6*s, 2*s, 4*s))
        
        # Flower petals with rotation
        angle = frame * 0.1
        for i in range(4):
            petal_angle = angle + i * math.pi / 2
            px = int(x + 5*s + math.cos(petal_angle) * 3*s)
            py = int(y + 3*s + math.sin(petal_angle) * 3*s)
            pygame.draw.rect(surf, ORANGE if i % 2 == 0 else WHITE, (px, py, 2*s, 2*s))
        
        # Center
        pygame.draw.rect(surf, YELLOW, (x + 4*s, y + 2*s, 2*s, 2*s))
    
    @staticmethod
    def draw_star(surf, x, y, frame):
        """Draw invincibility star with sparkle animation"""
        x = int(x * SCALE)
        y = int(y * SCALE)
        s = int(SCALE)
        
        # Star shape using mathematical formula
        points = []
        for i in range(10):
            angle = i * math.pi / 5
            if i % 2 == 0:
                r = 5 * s
            else:
                r = 2 * s
            px = x + 5*s + int(r * math.cos(angle - math.pi / 2))
            py = y + 5*s + int(r * math.sin(angle - math.pi / 2))
            points.append((px, py))
        
        # Flashing colors
        colors = [YELLOW, WHITE, ORANGE]
        color = colors[(frame // 4) % 3]
        pygame.draw.polygon(surf, color, points)
    
    @staticmethod
    def draw_coin(surf, x, y, frame):
        """Draw spinning coin"""
        x = int(x * SCALE)
        y = int(y * SCALE)
        s = int(SCALE)
        
        # Spinning animation using cosine
        width = int(abs(math.cos(frame * 0.2)) * 6 + 1)
        offset = (8 - width) // 2
        
        if width > 1:
            pygame.draw.ellipse(surf, YELLOW, (x + offset*s, y + s, width*s, 6*s))
            pygame.draw.ellipse(surf, ORANGE, (x + (offset+1)*s, y + 2*s, (width-2)*s, 4*s))
    
    @staticmethod
    def draw_fireball(surf, x, y, frame):
        """Draw Mario's fireball"""
        x = int(x * SCALE)
        y = int(y * SCALE)
        s = int(SCALE)
        
        # Rotating fireball
        angle = frame * 0.5
        for i in range(4):
            fx = int(x + 2*s + math.cos(angle + i * math.pi/2) * 2*s)
            fy = int(y + 2*s + math.sin(angle + i * math.pi/2) * 2*s)
            color = ORANGE if i % 2 == 0 else RED
            pygame.draw.circle(surf, color, (fx, fy), s)
    
    @staticmethod
    def draw_brick(surf, x, y):
        """Draw brick block with SMB1 pattern"""
        x = int(x * SCALE)
        y = int(y * SCALE)
        s = int(SCALE)
        
        pygame.draw.rect(surf, LIGHT_BROWN, (x, y, TILE*s, TILE*s))
        # Brick pattern
        for row in range(4):
            for col in range(2):
                bx = x + col * 8*s + (4*s if row % 2 == 1 else 0)
                by = y + row * 4*s
                pygame.draw.rect(surf, BROWN, (bx, by, 7*s, 3*s))
                pygame.draw.rect(surf, BLACK, (bx, by, 7*s, 3*s), 1)
    
    @staticmethod
    def draw_question_block(surf, x, y, used):
        """Draw question mark block"""
        x = int(x * SCALE)
        y = int(y * SCALE)
        s = int(SCALE)
        
        if used:
            pygame.draw.rect(surf, BROWN, (x, y, TILE*s, TILE*s))
            pygame.draw.rect(surf, BLACK, (x, y, TILE*s, TILE*s), 1)
        else:
            pygame.draw.rect(surf, YELLOW, (x, y, TILE*s, TILE*s))
            pygame.draw.rect(surf, ORANGE, (x, y, TILE*s, TILE*s), 2)
            # Question mark
            q_points = [(x+7*s, y+3*s), (x+9*s, y+3*s), (x+9*s, y+5*s), 
                       (x+8*s, y+6*s), (x+8*s, y+8*s), (x+7*s, y+9*s)]
            pygame.draw.lines(surf, BLACK, False, q_points, 2)
            pygame.draw.circle(surf, BLACK, (x+8*s, y+11*s), s)
    
    @staticmethod
    def draw_pipe(surf, x, y, height):
        """Draw a pipe segment"""
        x = int(x * SCALE)
        y = int(y * SCALE)
        s = int(SCALE)
        
        # Main pipe body
        pygame.draw.rect(surf, GREEN, (x, y, TILE*2*s, TILE*height*s))
        pygame.draw.rect(surf, DARK_GREEN, (x, y, TILE*2*s, TILE*height*s), 2)
        
        # Pipe cap
        if y <= TILE * SCALE:  # Only draw cap at top of screen
            pygame.draw.rect(surf, GREEN, (x-2*s, y, TILE*2*s+4*s, TILE*s))
            pygame.draw.rect(surf, DARK_GREEN, (x-2*s, y, TILE*2*s+4*s, TILE*s), 2)

# ==============================================================================
# ENTITY CLASSES
# ==============================================================================
class Entity:
    """Base entity class for all game objects"""
    
    def __init__(self, x, y, w, h):
        self.x = float(x)
        self.y = float(y)
        self.w = w
        self.h = h
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.facing_right = True
        self.alive = True
        self.frame = 0
    
    def get_rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)
    
    def update(self, world, dt):
        self.frame += 1
    
    def draw(self, surf, cam_x):
        pass

class Mario(Entity):
    """Mario player character with SMB1 physics"""
    
    def __init__(self, x, y):
        super().__init__(x, y, 12, SMALL_MARIO_HEIGHT)
        self.is_big = False
        self.has_fire = False
        self.star_timer = 0
        self.invincible_timer = 0
        self.lives = START_LIVES
        self.coins = 0
        self.score = 0
        self.jump_held = False
        self.fire_cooldown = 0
        self.spawn_x = x
        self.spawn_y = y
    
    def make_big(self):
        if not self.is_big:
            self.is_big = True
            self.h = BIG_MARIO_HEIGHT
            self.y -= (BIG_MARIO_HEIGHT - SMALL_MARIO_HEIGHT)
    
    def make_small(self):
        if self.is_big:
            self.is_big = False
            self.h = SMALL_MARIO_HEIGHT
            self.has_fire = False
            self.invincible_timer = 90  # 1.5 seconds at 60fps
    
    def take_damage(self):
        if self.invincible_timer > 0 or self.star_timer > 0:
            return False
        
        if self.has_fire:
            self.has_fire = False
            self.invincible_timer = 90
        elif self.is_big:
            self.make_small()
        else:
            self.die()
            return True
        return False
    
    def die(self):
        self.alive = False
        self.lives -= 1
        self.vy = JUMP_VELOCITY * 2  # Death bounce
    
    def handle_input(self, keys):
        # Horizontal movement
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            if self.vx > -RUN_SPEED:
                self.vx -= WALK_SPEED * 0.2
            self.facing_right = False
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            if self.vx < RUN_SPEED:
                self.vx += WALK_SPEED * 0.2
            self.facing_right = True
        else:
            # Apply friction
            if self.on_ground:
                self.vx *= (1 - FRICTION)
            else:
                self.vx *= (1 - AIR_FRICTION)
        
        # Jumping
        jump = keys[pygame.K_SPACE] or keys[pygame.K_z] or keys[pygame.K_UP] or keys[pygame.K_w]
        if jump and self.on_ground and not self.jump_held:
            self.vy = JUMP_VELOCITY
            self.jump_held = True
            self.on_ground = False
        elif jump and self.jump_held and self.vy < 0:
            # Variable jump height
            self.vy += JUMP_HOLD_FORCE
        elif not jump:
            self.jump_held = False
        
        # Run button
        run = keys[pygame.K_LSHIFT] or keys[pygame.K_x]
        if run:
            self.vx *= 1.5
        
        # Fire button
        if (keys[pygame.K_c] or keys[pygame.K_LCTRL]) and self.has_fire and self.fire_cooldown <= 0:
            self.shoot_fireball()
            self.fire_cooldown = 20
    
    def shoot_fireball(self):
        # Fireball creation handled by world
        pass
    
    def update(self, world, dt):
        super().update(world, dt)
        
        # Timers
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
        if self.star_timer > 0:
            self.star_timer -= 1
        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1
        
        # Apply gravity
        if not self.on_ground:
            self.vy += GRAVITY
            self.vy = min(self.vy, MAX_FALL)
        
        # Horizontal movement
        self.x += self.vx
        
        # Check horizontal collisions
        if world.check_collision(self.get_rect()):
            if self.vx > 0:
                self.x = int(self.x) - (int(self.x) % TILE)
                self.vx = 0
            else:
                self.x = int(self.x) + (TILE - int(self.x) % TILE)
                self.vx = 0
        
        # Vertical movement
        self.y += self.vy
        self.on_ground = False
        
        # Check vertical collisions
        if world.check_collision(self.get_rect()):
            if self.vy > 0:
                self.y = int(self.y) - (int(self.y) % TILE)
                self.vy = 0
                self.on_ground = True
            else:
                # Hit block above
                self.y = int(self.y) + (TILE - int(self.y) % TILE)
                self.vy = 0
                # Trigger block hit
                block_x = int(self.x + self.w/2) // TILE
                block_y = int(self.y - 1) // TILE
                world.hit_block(block_x, block_y, self)
        
        # Death by falling
        if self.y > ROWS * TILE:
            self.die()
    
    def draw(self, surf, cam_x):
        if self.invincible_timer > 0 and self.invincible_timer % 4 < 2:
            return  # Flashing effect
        
        screen_x = world_to_screen(self.x, cam_x)
        SpriteRenderer.draw_mario(surf, screen_x / SCALE, self.y, 
                                self.is_big, self.has_fire, 
                                self.facing_right, self.frame)

class Goomba(Entity):
    """Goomba enemy with simple AI"""
    
    def __init__(self, x, y):
        super().__init__(x, y, 16, 16)
        self.vx = -ENEMY_SPEED
        self.stomped = False
    
    def update(self, world, dt):
        super().update(world, dt)
        
        if self.stomped:
            self.alive = False
            return
        
        # Gravity
        self.vy += GRAVITY
        self.vy = min(self.vy, MAX_FALL)
        
        # Movement
        self.x += self.vx
        
        # Check wall collision - reverse direction
        if world.check_collision(self.get_rect()):
            self.vx = -self.vx
            self.x += self.vx * 2
        
        # Vertical movement
        self.y += self.vy
        if world.check_collision(self.get_rect()):
            if self.vy > 0:
                self.y = int(self.y) - (int(self.y) % TILE)
                self.vy = 0
                self.on_ground = True
        
        # Death by falling
        if self.y > ROWS * TILE:
            self.alive = False
    
    def draw(self, surf, cam_x):
        screen_x = world_to_screen(self.x, cam_x)
        SpriteRenderer.draw_goomba(surf, screen_x / SCALE, self.y, self.frame)

class KoopaTroopa(Entity):
    """Koopa Troopa enemy that becomes a shell when stomped"""
    
    def __init__(self, x, y):
        super().__init__(x, y, 16, 24)
        self.vx = -ENEMY_SPEED
        self.is_shell = False
        self.shell_moving = False
    
    def stomp(self):
        if not self.is_shell:
            self.is_shell = True
            self.h = 16
            self.y += 8
            self.vx = 0
            self.shell_moving = False
        else:
            # Kick shell
            self.shell_moving = True
            self.vx = FIREBALL_SPEED * (1 if self.facing_right else -1)
    
    def update(self, world, dt):
        super().update(world, dt)
        
        # Gravity
        self.vy += GRAVITY
        self.vy = min(self.vy, MAX_FALL)
        
        # Movement
        if not self.is_shell or self.shell_moving:
            self.x += self.vx
            
            # Check wall collision
            if world.check_collision(self.get_rect()):
                self.vx = -self.vx
                self.facing_right = not self.facing_right
                self.x += self.vx * 2
        
        # Vertical movement
        self.y += self.vy
        if world.check_collision(self.get_rect()):
            if self.vy > 0:
                self.y = int(self.y) - (int(self.y) % TILE)
                self.vy = 0
                self.on_ground = True
        
        # Death by falling
        if self.y > ROWS * TILE:
            self.alive = False
    
    def draw(self, surf, cam_x):
        screen_x = world_to_screen(self.x, cam_x)
        SpriteRenderer.draw_koopa(surf, screen_x / SCALE, self.y, 
                                 self.is_shell, self.frame)

class PowerUp(Entity):
    """Base class for power-ups"""
    
    def __init__(self, x, y, kind):
        super().__init__(x, y, 16, 16)
        self.kind = kind
        self.vx = ENEMY_SPEED if kind == 'mushroom' else 0
        self.emerged = False
        self.emerge_y = y
    
    def update(self, world, dt):
        super().update(world, dt)
        
        # Emerging animation
        if not self.emerged:
            self.y -= 0.5
            if self.y <= self.emerge_y - TILE:
                self.emerged = True
            return
        
        # Gravity (except star bounces)
        if self.kind == 'star':
            self.vy += GRAVITY * 0.7
            if self.on_ground:
                self.vy = -3.0  # Bounce
        else:
            self.vy += GRAVITY
            self.vy = min(self.vy, MAX_FALL)
        
        # Horizontal movement (mushroom only)
        if self.kind == 'mushroom':
            self.x += self.vx
            if world.check_collision(self.get_rect()):
                self.vx = -self.vx
                self.x += self.vx * 2
        
        # Vertical movement
        self.y += self.vy
        if world.check_collision(self.get_rect()):
            if self.vy > 0:
                self.y = int(self.y) - (int(self.y) % TILE)
                self.vy = 0
                self.on_ground = True
    
    def draw(self, surf, cam_x):
        screen_x = world_to_screen(self.x, cam_x)
        
        if self.kind == 'mushroom':
            SpriteRenderer.draw_mushroom(surf, screen_x / SCALE, self.y)
        elif self.kind == 'flower':
            SpriteRenderer.draw_fire_flower(surf, screen_x / SCALE, self.y, self.frame)
        elif self.kind == 'star':
            SpriteRenderer.draw_star(surf, screen_x / SCALE, self.y, self.frame)

class Fireball(Entity):
    """Mario's fireball projectile"""
    
    def __init__(self, x, y, direction):
        super().__init__(x, y, 8, 8)
        self.vx = FIREBALL_SPEED * direction
        self.vy = 0
        self.bounce_count = 0
    
    def update(self, world, dt):
        super().update(world, dt)
        
        # Gravity
        self.vy += GRAVITY * 0.8
        self.vy = min(self.vy, MAX_FALL)
        
        # Movement
        self.x += self.vx
        self.y += self.vy
        
        # Check collisions
        if world.check_collision(self.get_rect()):
            if self.vy > 0:
                # Bounce
                self.vy = -2.5
                self.bounce_count += 1
                if self.bounce_count > 3:
                    self.alive = False
            else:
                self.alive = False
        
        # Off screen
        if self.y > ROWS * TILE:
            self.alive = False
    
    def draw(self, surf, cam_x):
        screen_x = world_to_screen(self.x, cam_x)
        SpriteRenderer.draw_fireball(surf, screen_x / SCALE, self.y, self.frame)

# ==============================================================================
# WORLD CLASS
# ==============================================================================
class World:
    """SMB1 World/Level management"""
    
    def __init__(self, world_num, level_num):
        self.world = world_num
        self.level = level_num
        self.map = [[' ' for _ in range(COLS)] for _ in range(ROWS)]
        self.entities = []
        self.powerups = []
        self.fireballs = []
        self.coins = []
        self.time = LEVEL_TIME
        self.complete = False
        
        # Build level
        self.build_level()
    
    def build_level(self):
        """Build the level geometry"""
        # Ground
        for x in range(COLS):
            for y in range(ROWS - 2, ROWS):
                self.map[y][x] = 'X'
        
        # Add some gaps
        for gap_start in [40, 65, 120, 180]:
            for x in range(gap_start, gap_start + 3):
                if x < COLS:
                    for y in range(ROWS - 2, ROWS):
                        self.map[y][x] = ' '
        
        # Pipes
        pipe_positions = [30, 55, 85, 140, 200]
        for pipe_x in pipe_positions:
            if pipe_x < COLS - 1:
                height = 3 + (pipe_x // 50)
                for y in range(ROWS - 2 - height, ROWS - 2):
                    self.map[y][pipe_x] = 'P'
                    self.map[y][pipe_x + 1] = 'P'
        
        # Platforms and blocks
        for platform in range(10, 200, 25):
            if platform < COLS:
                y = ROWS - 6 - (platform % 3) * 2
                for x in range(platform, min(platform + 8, COLS)):
                    if x % 3 == 0:
                        self.map[y][x] = '?'  # Question block
                    else:
                        self.map[y][x] = 'B'  # Brick
        
        # Add coins
        for coin_x in range(20, 200, 15):
            if coin_x < COLS:
                self.coins.append((coin_x * TILE, (ROWS - 8) * TILE))
        
        # Add enemies
        for enemy_x in range(25, 200, 20):
            if enemy_x < COLS:
                if enemy_x % 40 < 20:
                    self.entities.append(Goomba(enemy_x * TILE, (ROWS - 3) * TILE))
                else:
                    self.entities.append(KoopaTroopa(enemy_x * TILE, (ROWS - 3) * TILE))
        
        # Flag pole at end
        self.map[ROWS - 12][COLS - 10] = 'F'
        for y in range(ROWS - 12, ROWS - 2):
            self.map[y][COLS - 10] = '|'
    
    def check_collision(self, rect):
        """Check if a rect collides with solid tiles"""
        x1 = max(0, rect.left // TILE)
        x2 = min(COLS - 1, rect.right // TILE)
        y1 = max(0, rect.top // TILE)
        y2 = min(ROWS - 1, rect.bottom // TILE)
        
        for y in range(y1, y2 + 1):
            for x in range(x1, x2 + 1):
                tile = self.map[y][x]
                if tile in 'XBP?US':  # Solid tiles
                    tile_rect = pygame.Rect(x * TILE, y * TILE, TILE, TILE)
                    if rect.colliderect(tile_rect):
                        return True
        return False
    
    def hit_block(self, x, y, mario):
        """Handle block being hit by Mario"""
        if 0 <= x < COLS and 0 <= y < ROWS:
            tile = self.map[y][x]
            
            if tile == '?':
                # Question block - spawn power-up
                self.map[y][x] = 'U'  # Used block
                if mario.is_big:
                    powerup = PowerUp(x * TILE, y * TILE, 'flower')
                else:
                    powerup = PowerUp(x * TILE, y * TILE, 'mushroom')
                self.powerups.append(powerup)
                mario.score += 200
            
            elif tile == 'B' and mario.is_big:
                # Break brick if big
                self.map[y][x] = ' '
                mario.score += 50
    
    def update(self, mario, dt):
        """Update all world elements"""
        # Update entities
        for entity in self.entities[:]:
            entity.update(self, dt)
            if not entity.alive:
                self.entities.remove(entity)
        
        # Update power-ups
        for powerup in self.powerups[:]:
            powerup.update(self, dt)
            # Check collection
            if mario.get_rect().colliderect(powerup.get_rect()):
                if powerup.kind == 'mushroom':
                    mario.make_big()
                    mario.score += 1000
                elif powerup.kind == 'flower':
                    mario.make_big()
                    mario.has_fire = True
                    mario.score += 1000
                elif powerup.kind == 'star':
                    mario.star_timer = 600  # 10 seconds
                    mario.score += 1000
                self.powerups.remove(powerup)
        
        # Update fireballs
        for fireball in self.fireballs[:]:
            fireball.update(self, dt)
            if not fireball.alive:
                self.fireballs.remove(fireball)
            # Check enemy hits
            for enemy in self.entities:
                if fireball.get_rect().colliderect(enemy.get_rect()):
                    enemy.alive = False
                    fireball.alive = False
                    mario.score += 200
        
        # Check enemy collisions
        mario_rect = mario.get_rect()
        for enemy in self.entities:
            if mario_rect.colliderect(enemy.get_rect()):
                if mario.star_timer > 0:
                    enemy.alive = False
                    mario.score += 200
                elif mario.vy > 0 and mario_rect.bottom - enemy.get_rect().top < 10:
                    # Stomp enemy
                    if isinstance(enemy, Goomba):
                        enemy.stomped = True
                        mario.score += 100
                    elif isinstance(enemy, KoopaTroopa):
                        enemy.stomp()
                        mario.score += 200
                    mario.vy = -3.0  # Bounce
                else:
                    # Take damage
                    mario.take_damage()
        
        # Check coin collection
        for coin in self.coins[:]:
            coin_rect = pygame.Rect(coin[0], coin[1], 10, 10)
            if mario_rect.colliderect(coin_rect):
                self.coins.remove(coin)
                mario.coins += 1
                mario.score += 200
                if mario.coins >= 100:
                    mario.coins -= 100
                    mario.lives += 1
        
        # Check flag (level complete)
        if mario.x > (COLS - 15) * TILE:
            self.complete = True
        
        # Create fireball if requested
        if mario.has_fire and mario.fire_cooldown == 20:  # Just fired
            direction = 1 if mario.facing_right else -1
            fireball = Fireball(mario.x + mario.w/2, mario.y + mario.h/2, direction)
            self.fireballs.append(fireball)
    
    def draw(self, surf, cam_x):
        """Draw the world"""
        # Clear with sky color
        surf.fill(SKY_BLUE)
        
        # Calculate visible tile range
        start_x = max(0, int(cam_x // TILE))
        end_x = min(COLS, int((cam_x + DISPLAY_W / SCALE) // TILE) + 2)
        
        # Draw tiles
        for y in range(ROWS):
            for x in range(start_x, end_x):
                tile = self.map[y][x]
                screen_x = world_to_screen(x * TILE, cam_x)
                
                if tile == 'X':  # Ground
                    SpriteRenderer.draw_brick(surf, screen_x / SCALE, y * TILE)
                elif tile == 'B':  # Brick
                    SpriteRenderer.draw_brick(surf, screen_x / SCALE, y * TILE)
                elif tile == '?':  # Question block
                    SpriteRenderer.draw_question_block(surf, screen_x / SCALE, y * TILE, False)
                elif tile == 'U':  # Used block
                    SpriteRenderer.draw_question_block(surf, screen_x / SCALE, y * TILE, True)
                elif tile == 'P':  # Pipe
                    SpriteRenderer.draw_pipe(surf, (x // 2) * 2 * TILE, y * TILE, 1)
                elif tile == '|':  # Flag pole
                    pygame.draw.rect(surf, WHITE, (screen_x, y * TILE * SCALE, 
                                                  2 * SCALE, TILE * SCALE))
                elif tile == 'F':  # Flag
                    points = [(screen_x, y * TILE * SCALE),
                            (screen_x + 20 * SCALE, y * TILE * SCALE + 10 * SCALE),
                            (screen_x, y * TILE * SCALE + 20 * SCALE)]
                    pygame.draw.polygon(surf, RED, points)
        
        # Draw coins
        for coin in self.coins:
            screen_x = world_to_screen(coin[0], cam_x)
            SpriteRenderer.draw_coin(surf, screen_x / SCALE, coin[1], pygame.time.get_ticks() // 10)
        
        # Draw entities
        for entity in self.entities:
            entity.draw(surf, cam_x)
        
        # Draw power-ups
        for powerup in self.powerups:
            powerup.draw(surf, cam_x)
        
        # Draw fireballs
        for fireball in self.fireballs:
            fireball.draw(surf, cam_x)

# ==============================================================================
# MAIN GAME CLASS
# ==============================================================================
class Game:
    """Main game controller"""
    
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((DISPLAY_W, DISPLAY_H))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.running = True
        
        # Game state
        self.world = World(1, 1)
        self.mario = Mario(32, ROWS * TILE - 64)
        self.camera_x = 0
        self.game_over = False
        self.paused = False
    
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_p:
                    self.paused = not self.paused
    
    def update(self, dt):
        """Update game state"""
        if self.paused or self.game_over:
            return
        
        # Handle input
        keys = pygame.key.get_pressed()
        self.mario.handle_input(keys)
        
        # Update Mario
        self.mario.update(self.world, dt)
        
        # Update world
        self.world.update(self.mario, dt)
        
        # Update camera (follow Mario)
        target_x = self.mario.x - DISPLAY_W / SCALE / 2
        self.camera_x = max(0, min(target_x, COLS * TILE - DISPLAY_W / SCALE))
        
        # Check game over
        if self.mario.lives <= 0:
            self.game_over = True
        
        # Check level complete
        if self.world.complete:
            # Next level
            self.world.level += 1
            if self.world.level > 4:
                self.world.level = 1
                self.world.world += 1
            self.world = World(self.world.world, self.world.level)
            self.mario.x = 32
            self.mario.y = ROWS * TILE - 64
    
    def draw(self):
        """Draw everything"""
        # Draw world
        self.world.draw(self.screen, self.camera_x)
        
        # Draw Mario
        self.mario.draw(self.screen, self.camera_x)
        
        # Draw HUD
        self.draw_hud()
        
        # Game over overlay
        if self.game_over:
            overlay = pygame.Surface((DISPLAY_W, DISPLAY_H))
            overlay.set_alpha(128)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))
            
            text = self.font.render("GAME OVER", True, WHITE)
            rect = text.get_rect(center=(DISPLAY_W // 2, DISPLAY_H // 2))
            self.screen.blit(text, rect)
        
        # Paused overlay
        if self.paused:
            text = self.font.render("PAUSED", True, WHITE)
            rect = text.get_rect(center=(DISPLAY_W // 2, DISPLAY_H // 2))
            self.screen.blit(text, rect)
        
        pygame.display.flip()
    
    def draw_hud(self):
        """Draw the HUD"""
        # Score
        score_text = f"MARIO    WORLD   TIME"
        text = self.font.render(score_text, True, WHITE)
        self.screen.blit(text, (50, 20))
        
        values_text = f"{self.mario.score:06d}    {self.world.world}-{self.world.level}    {int(self.world.time):03d}"
        text = self.font.render(values_text, True, WHITE)
        self.screen.blit(text, (50, 45))
        
        # Coins and lives
        coin_text = f"x{self.mario.coins:02d}"
        text = self.font.render(coin_text, True, WHITE)
        self.screen.blit(text, (150, 70))
        
        lives_text = f"x{self.mario.lives}"
        text = self.font.render(lives_text, True, WHITE)
        self.screen.blit(text, (250, 70))
    
    def run(self):
        """Main game loop"""
        print(f"Starting {TITLE}")
        print("Controls:")
        print("  Arrow Keys / WASD - Move")
        print("  Space / Z / Up - Jump")
        print("  Shift / X - Run")
        print("  C / Ctrl - Fireball")
        print("  P - Pause")
        print("  ESC - Quit")
        
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            
            self.handle_events()
            self.update(dt)
            self.draw()
        
        pygame.quit()
        sys.exit()

# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    game = Game()
    game.run()
