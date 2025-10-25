#!/usr/bin/env python3
"""
SUPER MARIO BROS 1 ENGINE
Faithful recreation of SMB1 mechanics and physics

Controls:
  Left/Right  or  A/D  -> Move
  Up/Space/W            -> Jump
  Run button (Shift)     -> Run while moving
  Down/S                -> Crouch (when big)
  Enter                 -> Start game
  Esc                   -> Quit

Requires: pygame
"""

import math
import random
import sys

import pygame

# -----------------------------------------------------------------------------
# Window / Timing
# -----------------------------------------------------------------------------
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Super Mario Bros 1 Engine")
clock = pygame.time.Clock()
FPS = 60

# -----------------------------------------------------------------------------
# Colors (NES SMB1 Palette)
# -----------------------------------------------------------------------------
SKY_BLUE   = (107, 140, 255)
BROWN      = (165,  75,  55)  # SMB1 brown
DARK_BROWN = (101,  67,  33)
RED        = (228,  92,  16)  # Mario red
BLUE       = (  0, 128, 248)  # Overalls blue
GREEN      = (  0, 168,   0)
YELLOW     = (252, 216, 168)  # Skin tone
BLACK      = (  0,   0,   0)
WHITE      = (255, 255, 255)
COIN_GOLD  = (248, 184,   0)
BRICK      = (200,  76,  12)
PIPE_GREEN = (  0, 168,   0)

# -----------------------------------------------------------------------------
# SMB1 Physics Constants
# -----------------------------------------------------------------------------
GRAVITY = 0.35
MAX_FALL_SPEED = 8.0
JUMP_STRENGTH = -8.5
WALK_ACCEL = 0.12
RUN_ACCEL = 0.25
GROUND_FRICTION = 0.85
AIR_FRICTION = 0.98
MAX_WALK_SPEED = 3.0
MAX_RUN_SPEED = 6.0

# -----------------------------------------------------------------------------
# Utility
# -----------------------------------------------------------------------------
def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v

# -----------------------------------------------------------------------------
# HUD (SMB1 Style)
# -----------------------------------------------------------------------------
class SMB1HUD:
    def __init__(self):
        self.font = pygame.font.SysFont("Arial", 16, bold=True)
        self.score = 0
        self.coins = 0
        self.lives = 3
        self.world = "1-1"
        self.time = 400
        
    def tick_time(self):
        self.time = max(0, self.time - 1)
        
    def draw(self, surface):
        # Black bar at top
        pygame.draw.rect(surface, BLACK, (0, 0, SCREEN_WIDTH, 30))
        
        # MARIO text
        mario_text = self.font.render("MARIO", True, WHITE)
        surface.blit(mario_text, (20, 5))
        
        # Score
        score_text = self.font.render(f"{self.score:06d}", True, WHITE)
        surface.blit(score_text, (20, 20))
        
        # Coin icon and count
        pygame.draw.circle(surface, COIN_GOLD, (200, 20), 6)
        coin_text = self.font.render(f"x{self.coins:02d}", True, WHITE)
        surface.blit(coin_text, (210, 15))
        
        # World
        world_text = self.font.render("WORLD", True, WHITE)
        surface.blit(world_text, (300, 5))
        world_num = self.font.render(self.world, True, WHITE)
        surface.blit(world_num, (310, 20))
        
        # Time
        time_text = self.font.render("TIME", True, WHITE)
        surface.blit(time_text, (400, 5))
        time_num = self.font.render(str(self.time), True, WHITE)
        surface.blit(time_num, (410, 20))
        
        # Lives (in SMB1 style)
        lives_text = self.font.render(f"LIVES: {self.lives}", True, WHITE)
        surface.blit(lives_text, (500, 15))

# -----------------------------------------------------------------------------
# Blocks and Platforms
# -----------------------------------------------------------------------------
class Block:
    def __init__(self, x, y, block_type="brick"):
        self.x, self.y = float(x), float(y)
        self.w, self.h = 32, 32
        self.type = block_type
        self.bumped = False
        self.bump_offset = 0
        
    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y + self.bump_offset), self.w, self.h)
        
    def bump(self):
        if not self.bumped:
            self.bumped = True
            self.bump_offset = -4
            
    def update(self):
        if self.bumped:
            self.bump_offset += 0.5
            if self.bump_offset >= 0:
                self.bump_offset = 0
                self.bumped = False
                
    def draw(self, surface, cam_x):
        rx = int(self.x - cam_x)
        if self.type == "brick":
            pygame.draw.rect(surface, BRICK, (rx, int(self.y + self.bump_offset), self.w, self.h))
            # Brick pattern
            pygame.draw.line(surface, (150, 60, 30), (rx, int(self.y + self.bump_offset) + 8), 
                           (rx + self.w, int(self.y + self.bump_offset) + 8), 1)
            pygame.draw.line(surface, (150, 60, 30), (rx, int(self.y + self.bump_offset) + 16), 
                           (rx + self.w, int(self.y + self.bump_offset) + 16), 1)
            pygame.draw.line(surface, (150, 60, 30), (rx, int(self.y + self.bump_offset) + 24), 
                           (rx + self.w, int(self.y + self.bump_offset) + 24), 1)
        elif self.type == "question":
            # Question block - yellow with question mark
            pygame.draw.rect(surface, COIN_GOLD, (rx, int(self.y + self.bump_offset), self.w, self.h))
            pygame.draw.rect(surface, (200, 150, 0), (rx, int(self.y + self.bump_offset), self.w, self.h), 2)
            # Simple question mark
            q_font = pygame.font.SysFont("Arial", 20, bold=True)
            q_text = q_font.render("?", True, BLACK)
            surface.blit(q_text, (rx + 10, int(self.y + self.bump_offset) + 5))

class Platform:
    def __init__(self, x, y, w, h, platform_type="ground"):
        self.x, self.y, self.w, self.h = float(x), float(y), float(w), float(h)
        self.type = platform_type
        
    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), int(self.w), int(self.h))
        
    def draw(self, surface, cam_x):
        rx = int(self.x - cam_x)
        if self.type == "ground":
            pygame.draw.rect(surface, BROWN, (rx, int(self.y), int(self.w), int(self.h)))
            # Grass top
            pygame.draw.rect(surface, GREEN, (rx, int(self.y), int(self.w), 6))
        elif self.type == "pipe":
            pygame.draw.rect(surface, PIPE_GREEN, (rx, int(self.y), int(self.w), int(self.h)))
            # Pipe details
            pygame.draw.rect(surface, (0, 140, 0), (rx, int(self.y), int(self.w), 10))

class Coin:
    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.w, self.h = 16, 16
        self.collected = False
        self.anim_frame = 0
        
    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)
        
    def update(self):
        self.anim_frame = (self.anim_frame + 1) % 30
        
    def draw(self, surface, cam_x):
        if not self.collected:
            rx = int(self.x - cam_x)
            # Animated coin - changes size slightly
            size_mod = math.sin(self.anim_frame * 0.2) * 2
            pygame.draw.ellipse(surface, COIN_GOLD, 
                              (rx - size_mod/2, int(self.y) - size_mod/2, 
                               self.w + size_mod, self.h + size_mod))

class Goomba:
    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.w, self.h = 32, 32
        self.vx = -1.0
        self.vy = 0.0
        self.alive = True
        self.squished = False
        self.squish_timer = 0
        
    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)
        
    def update(self, platforms):
        if self.squished:
            self.squish_timer += 1
            if self.squish_timer > 30:
                self.alive = False
            return
            
        self.vy += GRAVITY
        if self.vy > MAX_FALL_SPEED:
            self.vy = MAX_FALL_SPEED
            
        # Move horizontally
        self.x += self.vx
        
        # Check platform collisions
        on_ground = False
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vx > 0:
                    self.x = p.rect.left - self.w
                    self.vx = -self.vx
                elif self.vx < 0:
                    self.x = p.rect.right
                    self.vx = -self.vx
                    
                # Vertical collision
                if self.vy > 0 and self.rect.bottom > p.rect.top and self.y < p.rect.top:
                    self.y = p.rect.top - self.h
                    self.vy = 0
                    on_ground = True
                elif self.vy < 0:
                    self.y = p.rect.bottom
                    self.vy = 0
                    
        # Move vertically
        self.y += self.vy
        
        # Turn around at edges
        if not on_ground and self.vy > 0:
            # Check if there's ground ahead
            test_x = self.x + (10 if self.vx > 0 else -10)
            edge_found = False
            for p in platforms:
                if (p.rect.left <= test_x <= p.rect.right and 
                    p.rect.top >= self.y + self.h and p.rect.top <= self.y + self.h + 10):
                    edge_found = True
                    break
            if not edge_found:
                self.vx = -self.vx
                
    def draw(self, surface, cam_x):
        if not self.alive:
            return
            
        rx = int(self.x - cam_x)
        if self.squished:
            # Squished goomba
            pygame.draw.ellipse(surface, (139, 69, 19), (rx, int(self.y) + 20, self.w, 12))
        else:
            # Normal goomba - brown body
            pygame.draw.ellipse(surface, (139, 69, 19), (rx, int(self.y), self.w, self.h))
            # Feet
            pygame.draw.rect(surface, (101, 67, 33), (rx, int(self.y) + 25, 8, 6))
            pygame.draw.rect(surface, (101, 67, 33), (rx + 24, int(self.y) + 25, 8, 6))
            # Eyes
            pygame.draw.circle(surface, BLACK, (rx + 10, int(self.y) + 12), 3)
            pygame.draw.circle(surface, BLACK, (rx + 22, int(self.y) + 12), 3)

# -----------------------------------------------------------------------------
# Player (Mario)
# -----------------------------------------------------------------------------
class Player:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.w, self.h = 32, 32  # Small Mario size
        self.x, self.y = 64.0, 0.0
        self.vx, self.vy = 0.0, 0.0
        self.facing_right = True
        self.on_ground = False
        self.jump_pressed = False
        self.running = False
        self.crouching = False
        self.powerup_state = 0  # 0=small, 1=big, 2=fire
        self.invincible = 0
        self.dead = False
        self.death_timer = 0
        
    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)
        
    def handle_input(self, keys):
        if self.dead:
            return
            
        ax = 0.0
        self.running = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        self.crouching = (keys[pygame.K_DOWN] or keys[pygame.K_s]) and self.powerup_state > 0
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            ax -= RUN_ACCEL if self.running else WALK_ACCEL
            self.facing_right = False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            ax += RUN_ACCEL if self.running else WALK_ACCEL
            self.facing_right = True
            
        # Apply acceleration
        self.vx += ax
        
        # Apply friction
        if self.on_ground:
            self.vx *= GROUND_FRICTION
        else:
            self.vx *= AIR_FRICTION
            
        # Clamp speed
        max_speed = MAX_RUN_SPEED if self.running else MAX_WALK_SPEED
        self.vx = clamp(self.vx, -max_speed, max_speed)
        
        # Jumping
        jump_pressed = keys[pygame.K_UP] or keys[pygame.K_SPACE] or keys[pygame.K_w]
        if jump_pressed and self.on_ground and not self.jump_pressed:
            self.vy = JUMP_STRENGTH
            self.on_ground = False
        self.jump_pressed = jump_pressed
        
        # Adjust height when crouching
        if self.crouching and self.powerup_state > 0:
            self.h = 32
        elif self.powerup_state > 0:
            self.h = 64
            
    def update(self, platforms, blocks, coins, enemies):
        if self.dead:
            self.death_timer += 1
            if self.death_timer > 120:
                return "respawn"
            # Death animation
            self.y += self.vy
            self.vy += GRAVITY
            return None
            
        # Apply gravity
        self.vy += GRAVITY
        if self.vy > MAX_FALL_SPEED:
            self.vy = MAX_FALL_SPEED
            
        # Move horizontally
        self.x += self.vx
        
        # Horizontal collisions
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vx > 0:
                    self.x = p.rect.left - self.w
                elif self.vx < 0:
                    self.x = p.rect.right
                self.vx = 0
                
        # Block collisions (horizontal)
        for block in blocks:
            if self.rect.colliderect(block.rect):
                if self.vx > 0:
                    self.x = block.rect.left - self.w
                elif self.vx < 0:
                    self.x = block.rect.right
                self.vx = 0
                
        # Move vertically
        self.on_ground = False
        self.y += self.vy
        
        # Vertical collisions
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vy > 0:
                    self.y = p.rect.top - self.h
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0:
                    self.y = p.rect.bottom
                    self.vy = 0
                    
        # Block collisions from below
        for block in blocks:
            if self.rect.colliderect(block.rect):
                if self.vy < 0:  # Hitting block from below
                    block.bump()
                    self.vy = 0
                elif self.vy > 0:  # Landing on block
                    self.y = block.rect.top - self.h
                    self.vy = 0
                    self.on_ground = True
                    
        # Coin collection
        for coin in coins:
            if not coin.collected and self.rect.colliderect(coin.rect):
                coin.collected = True
                return "coin"
                
        # Enemy collisions
        for enemy in enemies:
            if enemy.alive and self.rect.colliderect(enemy.rect):
                if self.vy > 0 and self.rect.bottom < enemy.rect.top + 10:  # Jumping on enemy
                    enemy.squished = True
                    self.vy = JUMP_STRENGTH * 0.7  # Bounce
                    return "stomp"
                else:  # Hit by enemy
                    if self.powerup_state > 0:
                        self.powerup_state = 0
                        self.h = 32
                        self.invincible = 120
                        return "hit"
                    else:
                        self.die()
                        return "dead"
                        
        if self.invincible > 0:
            self.invincible -= 1
            
        return None
        
    def die(self):
        self.dead = True
        self.vy = JUMP_STRENGTH * 1.5  # Jump up when dead
        
    def draw(self, surface, cam_x):
        if self.invincible > 0 and (self.invincible // 4) % 2 == 0:
            return  # Flicker when invincible
            
        rx = int(self.x - cam_x)
        
        if self.dead:
            # Simple death animation - just draw a shrinking Mario
            size = max(0, 32 - self.death_timer // 4)
            pygame.draw.rect(surface, RED, (rx, int(self.y), size, size))
            return
            
        # Body color based on powerup state
        body_color = RED if self.powerup_state < 2 else WHITE
        
        if self.powerup_state == 0:  # Small Mario
            # Cap
            pygame.draw.rect(surface, body_color, (rx, int(self.y), self.w, 12))
            pygame.draw.rect(surface, body_color, (rx - 3, int(self.y) + 12, self.w + 6, 6))
            # Face
            pygame.draw.rect(surface, YELLOW, (rx + 6, int(self.y), self.w - 12, 20))
            # Overalls
            pygame.draw.rect(surface, BLUE, (rx, int(self.y) + 18, self.w, 14))
            # Arms
            pygame.draw.rect(surface, YELLOW, (rx - 3, int(self.y) + 18, 3, 8))
            pygame.draw.rect(surface, YELLOW, (rx + self.w, int(self.y) + 18, 3, 8))
            # Legs
            pygame.draw.rect(surface, BLUE, (rx + 4, int(self.y) + 32 - 6, 8, 6))
            pygame.draw.rect(surface, BLUE, (rx + self.w - 12, int(self.y) + 32 - 6, 8, 6))
            
        else:  # Big Mario
            # Adjust for crouching
            draw_y = self.y if not self.crouching else self.y + 32
            
            # Cap
            pygame.draw.rect(surface, body_color, (rx, int(draw_y), self.w, 16))
            pygame.draw.rect(surface, body_color, (rx - 4, int(draw_y) + 16, self.w + 8, 8))
            # Face
            pygame.draw.rect(surface, YELLOW, (rx + 8, int(draw_y), self.w - 16, 32))
            # Overalls
            pygame.draw.rect(surface, BLUE, (rx, int(draw_y) + 24, self.w, 24 if not self.crouching else 8))
            # Arms
            pygame.draw.rect(surface, YELLOW, (rx - 4, int(draw_y) + 24, 4, 16))
            pygame.draw.rect(surface, YELLOW, (rx + self.w, int(draw_y) + 24, 4, 16))
            # Legs (only show if not crouching)
            if not self.crouching:
                pygame.draw.rect(surface, BLUE, (rx + 8, int(draw_y) + 48, 8, 16))
                pygame.draw.rect(surface, BLUE, (rx + self.w - 16, int(draw_y) + 48, 8, 16))

# -----------------------------------------------------------------------------
# Level Design (SMB1 1-1 inspired)
# -----------------------------------------------------------------------------
class Level:
    def __init__(self):
        self.platforms = []
        self.blocks = []
        self.coins = []
        self.enemies = []
        self.length = 3000
        self.goal_x = 2800
        
        self._generate_level()
        
    def _generate_level(self):
        # Ground platform
        self.platforms.append(Platform(0, SCREEN_HEIGHT - 50, self.length, 50))
        
        # Platforms
        self.platforms.append(Platform(400, 400, 200, 20))
        self.platforms.append(Platform(700, 350, 150, 20))
        self.platforms.append(Platform(1000, 300, 200, 20))
        self.platforms.append(Platform(1300, 400, 200, 20))
        
        # Pipes
        self.platforms.append(Platform(600, SCREEN_HEIGHT - 130, 80, 80, "pipe"))
        self.platforms.append(Platform(1200, SCREEN_HEIGHT - 130, 80, 80, "pipe"))
        
        # Brick blocks
        for i in range(5):
            self.blocks.append(Block(500 + i * 32, 350))
            
        # Question blocks with coins
        self.blocks.append(Block(550, 250, "question"))
        self.coins.append(Coin(555, 255))
        
        self.blocks.append(Block(582, 250, "question"))
        self.coins.append(Coin(587, 255))
        
        # Floating coins
        for i in range(3):
            self.coins.append(Coin(800 + i * 40, 300))
            
        # Enemies
        self.enemies.append(Goomba(300, SCREEN_HEIGHT - 82))
        self.enemies.append(Goomba(900, SCREEN_HEIGHT - 82))
        self.enemies.append(Goomba(1100, 250))
        
    def update(self):
        for block in self.blocks:
            block.update()
        for coin in self.coins:
            coin.update()
        for enemy in self.enemies:
            enemy.update(self.platforms)
        # Remove dead enemies
        self.enemies = [e for e in self.enemies if e.alive]
        
    def draw(self, surface, cam_x):
        # Draw sky
        surface.fill(SKY_BLUE)
        
        # Draw clouds (simple)
        for i in range(5):
            cloud_x = (i * 400 + cam_x * 0.5) % (self.length + 400) - 100
            if 0 <= cloud_x <= SCREEN_WIDTH:
                pygame.draw.ellipse(surface, WHITE, (cloud_x, 50, 120, 40))
                pygame.draw.ellipse(surface, WHITE, (cloud_x + 30, 40, 100, 40))
                pygame.draw.ellipse(surface, WHITE, (cloud_x + 60, 50, 80, 40))
        
        # Draw platforms
        for p in self.platforms:
            p.draw(surface, cam_x)
            
        # Draw blocks
        for b in self.blocks:
            b.draw(surface, cam_x)
            
        # Draw coins
        for c in self.coins:
            c.draw(surface, cam_x)
            
        # Draw enemies
        for e in self.enemies:
            e.draw(surface, cam_x)
            
        # Draw goal flag
        flag_x = self.goal_x - cam_x
        if 0 <= flag_x <= SCREEN_WIDTH:
            # Pole
            pygame.draw.rect(surface, (200, 200, 200), (flag_x, 200, 8, 200))
            # Flag
            pygame.draw.polygon(surface, RED, [
                (flag_x + 8, 220),
                (flag_x + 8 + 40, 240),
                (flag_x + 8, 260)
            ])

# -----------------------------------------------------------------------------
# Main Game
# -----------------------------------------------------------------------------
def main():
    hud = SMB1HUD()
    player = Player()
    level = Level()
    
    cam_x = 0.0
    state = "menu"
    tick_accum = 0
    
    title_font = pygame.font.SysFont("Arial", 48, bold=True)
    ui_font = pygame.font.SysFont("Arial", 24, bold=True)
    
    running = True
    while running:
        dt_ms = clock.tick(FPS)
        tick_accum += dt_ms
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            running = False
            
        # Menu state
        if state == "menu":
            if keys[pygame.K_RETURN]:
                state = "playing"
                player.reset()
                hud.score = 0
                hud.coins = 0
                hud.lives = 3
                hud.time = 400
                hud.world = "1-1"
                
            # Draw menu
            screen.fill(SKY_BLUE)
            title = title_font.render("SUPER MARIO BROS", True, RED)
            screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 150))
            
            start_text = ui_font.render("PRESS ENTER TO START", True, WHITE)
            screen.blit(start_text, (SCREEN_WIDTH//2 - start_text.get_width()//2, 250))
            
            controls = [
                "CONTROLS:",
                "Arrow Keys/WASD - Move",
                "Shift - Run",
                "Space/Up - Jump",
                "Down - Crouch (when big)"
            ]
            
            for i, text in enumerate(controls):
                control_text = ui_font.render(text, True, WHITE)
                screen.blit(control_text, (SCREEN_WIDTH//2 - control_text.get_width()//2, 300 + i * 30))
                
            pygame.display.flip()
            continue
            
        # Playing state
        elif state == "playing":
            # Update timer
            if tick_accum >= 1000:
                tick_accum -= 1000
                hud.tick_time()
                if hud.time == 0:
                    player.die()
                    
            # Handle input and update
            player.handle_input(keys)
            result = player.update(level.platforms, level.blocks, level.coins, level.enemies)
            
            # Handle update results
            if result == "coin":
                hud.coins += 1
                hud.score += 200
                if hud.coins >= 100:
                    hud.coins = 0
                    hud.lives += 1
            elif result == "stomp":
                hud.score += 100
            elif result == "dead":
                hud.lives -= 1
                if hud.lives <= 0:
                    state = "gameover"
            elif result == "respawn":
                if hud.lives > 0:
                    player.reset()
                    cam_x = 0
                else:
                    state = "gameover"
                    
            # Check if reached goal
            if player.x >= level.goal_x:
                state = "level_clear"
                
            # Update level objects
            level.update()
            
            # Update camera
            cam_x = clamp(player.x - SCREEN_WIDTH * 0.4, 0, level.length - SCREEN_WIDTH)
            
            # Draw everything
            level.draw(screen, cam_x)
            player.draw(screen, cam_x)
            hud.draw(screen)
            
        # Level clear state
        elif state == "level_clear":
            screen.fill(SKY_BLUE)
            clear_text = title_font.render("LEVEL CLEAR!", True, WHITE)
            screen.blit(clear_text, (SCREEN_WIDTH//2 - clear_text.get_width()//2, 250))
            
            score_text = ui_font.render(f"SCORE: {hud.score}", True, WHITE)
            screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, 320))
            
            continue_text = ui_font.render("PRESS ENTER TO CONTINUE", True, WHITE)
            screen.blit(continue_text, (SCREEN_WIDTH//2 - continue_text.get_width()//2, 370))
            
            if keys[pygame.K_RETURN]:
                state = "menu"
                
        # Game over state
        elif state == "gameover":
            screen.fill(BLACK)
            over_text = title_font.render("GAME OVER", True, RED)
            screen.blit(over_text, (SCREEN_WIDTH//2 - over_text.get_width()//2, 250))
            
            score_text = ui_font.render(f"FINAL SCORE: {hud.score}", True, WHITE)
            screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, 320))
            
            restart_text = ui_font.render("PRESS ENTER TO RESTART", True, WHITE)
            screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, 370))
            
            if keys[pygame.K_RETURN]:
                state = "menu"
                
        pygame.display.flip()
        
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
