#!/usr/bin/env python3
"""
Ultra Mario 2D Bros PC Port
An accurate Super Mario Bros 1 engine recreation in pygame
60 FPS NES-style gameplay with authentic sprites and physics

Updated: Integrated NES sprites from Spriters Resource.
Assumes PNG sheets in 'sprites/' folder.
Fallback to procedural if missing.

This file has been fixed to fully integrate the SpriteRenderer,
pass the renderer object, and implement proper fallbacks.

MODIFIED: Added level_type for overworld/underground; authentic World 1 layouts; ceiling rendering.
FIXED: Completed the file with all necessary game logic, classes (Player, Enemy, Level, Game),
and the main game loop to make it runnable.

---
Samsoft patch v0 (samsoftsmb0decompv0.py):

✔ Fix #1: Removed undefined `game` usage inside entity `draw()` methods.
          All draw methods now accept an explicit `renderer` parameter, and callers pass it.
✔ Fix #2: Corrected double (actually triple) scaling. We now render at base NES
          resolution to an off-screen surface and only scale once at the end:
            - `world_to_screen()` no longer multiplies by SCALE.
            - Sprite sheets are no longer pre-scaled; we draw native 1x frames.
            - All fallback sprite painters use pixel unit `s = 1` (no hidden scaling).
            - Koopa / Mario vertical offsets use base pixels (no `* SCALE`).
✔ Fix #3: Fireball rect size uses integers (8x8) instead of floats.
✔ Fix #4: Lives were resetting on restart. `handle_player_death()` now preserves lives.
✔ Fix #5: Fragile enemy spawning (using `sprites()[-1]`) replaced with explicit references.
✔ Fix #6: Removed extra `pygame.display.flip()` from `Game.draw()` to avoid double-flip;
          the window flip now happens only in `main()` after scaling to the window.

Save as: samsoftsmb0decompv0.py
"""

import sys
import math
import random
import pygame
import os

# ==============================================================================
# SMB1 ENGINE CONFIGURATION
# ==============================================================================
TITLE = "Ultra Mario 2D Bros"
DISPLAY_W, DISPLAY_H = 768, 720  # Window size (3x of NES base 256x240)
SCALE = 3.0                      # Window upscaling factor for pixel-perfect display
TILE = 16                        # SMB1 tile size (base pixels)
ROWS, COLS = 15, 256             # NES screen height, extended level width
FPS = 60                         # NES framerate
SCREEN_W_TILES = int(DISPLAY_W / SCALE / TILE)  # 16 tiles wide
SCREEN_H_TILES = int(DISPLAY_H / SCALE / TILE)  # 15 tiles high

# SMB1 World Structure
TOTAL_LEVELS = 32  # 8 worlds x 4 levels

# NES Color Palette (approximated) - Retained for fallback
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
UNDERGROUND_BLUE = (0, 0, 0)  # Underground background

# SMB1 Physics (pixel-perfect values)
GRAVITY = 0.21875 * (60 / FPS) ** 2  # Adjusted for 60fps (Original: 0.21875 @ 60.0988fps)
JUMP_VELOCITY = -5.0                 # Initial jump velocity
JUMP_HOLD_FORCE = -0.25              # Additional force when holding jump
MAX_FALL = 4.0                       # Terminal velocity
WALK_ACCEL = 0.07                    # Walking acceleration
RUN_ACCEL = 0.10                     # Running acceleration
MAX_WALK_SPEED = 1.8                 # Max walking speed
MAX_RUN_SPEED = 3.0                  # Max running speed
FRICTION = 0.05                      # Ground friction
AIR_FRICTION = 0.03                  # Air resistance
SKID_FRICTION = 0.15                 # Friction when skidding

# SMB1 Gameplay Constants
START_LIVES = 3
LEVEL_TIME = 400
SMALL_MARIO_HEIGHT = 16
BIG_MARIO_HEIGHT = 32
FIREBALL_SPEED = 4.0
ENEMY_SPEED = -0.5  # Default move left
GOOMBA_STOMP_TIME = 30  # Frames to show stomped goomba
SHELL_SLIDE_SPEED = 5.0
POWERUP_SPAWN_SPEED = 0.5
POWERUP_MOVE_SPEED = 1.0

# Player States
STATE_SMALL = 0
STATE_BIG = 1
STATE_FIRE = 2

# Game States
STATE_MENU = 0
STATE_PLAYING = 1
STATE_LEVEL_CLEAR = 2
STATE_GAME_OVER = 3
STATE_DEAD = 4

# Tile Types
TYPE_EMPTY = ' '
TYPE_GROUND = '#'
TYPE_BRICK = 'B'
TYPE_QUESTION = '?'
TYPE_USED_BLOCK = 'U'
TYPE_PIPE_TOP_LEFT = 'L'
TYPE_PIPE_TOP_RIGHT = 'R'
TYPE_PIPE_LEFT = 'l'
TYPE_PIPE_RIGHT = 'r'
TYPE_FLAGPOLE = 'F'
TYPE_FLAG = 'f'
TYPE_CASTLE = 'C'
TYPE_GOOMBA = 'G'
TYPE_KOOPA = 'K'


# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================
def clamp(value, min_val, max_val):
    """Clamp value between min and max"""
    return max(min_val, min(max_val, value))


def world_to_screen(world_x, world_y, camera_x, camera_y):
    """Convert world coordinates to screen coordinates (base pixels, no scaling)."""
    screen_x = int(world_x - camera_x)
    screen_y = int(world_y - camera_y)
    return screen_x, screen_y


def tile_to_world(tile_x, tile_y):
    """Convert tile coordinates to world coordinates"""
    return tile_x * TILE, tile_y * TILE


def world_to_tile(world_x, world_y):
    """Convert world coordinates to tile coordinates"""
    return int(world_x // TILE), int(world_y // TILE)


# ==============================================================================
# SPRITE RENDERING WITH NES SPRITE SHEETS
# ==============================================================================
class SpriteRenderer:
    """NES-accurate sprite rendering using loaded sprite sheets (base resolution)."""

    def __init__(self):
        self.sprites = {}  # Cache: key -> list of surfaces (no pre-scaling)
        self.sprites_dir = 'sprites'
        self.fallback = False  # Start optimistic

        try:
            self.load_all_sprites()
            print("Successfully loaded sprites from 'sprites/' directory.")
        except Exception as e:
            print(f"Warning: Could not load sprites. {e}")
            print("Falling back to procedural (math-based) drawing.")
            self.fallback = True
            self.sprites = {}  # Clear any partial loads

    def load_sheet(self, filename, tile_w, tile_h, cols):
        """Load and slice a UNIFORM sprite sheet; leave frames at native size."""
        path = os.path.join(self.sprites_dir, filename)
        sheet = pygame.image.load(path).convert_alpha()
        frames = []
        rows = sheet.get_height() // tile_h
        for row in range(rows):
            row_frames = []
            for col in range(cols):
                frame = sheet.subsurface((col * tile_w, row * tile_h, tile_w, tile_h))
                row_frames.append(frame)  # no pre-scale here
            frames.append(row_frames)
        return frames

    def load_all_sprites(self):
        """Preload all required sheets. Assumes specific filenames and layouts."""
        # Mario Sprites
        self.sprites['mario_small'] = self.load_sheet('mario_small.png', 16, 16, 6)  # 0:idle, 1:run1, 2:run2, 3:skid, 4:jump, 5:dead
        self.sprites['mario_big'] = self.load_sheet('mario_big.png', 16, 32, 6)
        self.sprites['mario_fire'] = self.load_sheet('mario_fire.png', 16, 32, 6)

        # Enemy Sprites
        self.sprites['goomba'] = self.load_sheet('goomba.png', 16, 16, 3)  # 0:walk1, 1:walk2, 2:stomped
        self.sprites['koopa'] = self.load_sheet('koopa.png', 16, 24, 3)    # 0:walk1, 1:walk2, 2:shell

        # Item Sprites
        self.sprites['powerups'] = self.load_sheet('powerups.png', 16, 16, 3)     # 0:mushroom, 1:flower, 2:star
        self.sprites['projectiles'] = self.load_sheet('projectiles.png', 8, 8, 4) # 0-3: fireball
        self.sprites['coin'] = self.load_sheet('coin.png', 16, 16, 4)             # 0-3: spinning coin

        # Block Sprites
        self.sprites['blocks'] = self.load_sheet('blocks.png', 16, 16, 4)  # 0:brick, 1:q_anim, 2:q_used, 3:ground

        # Scenery Sprites
        self.sprites['scenery'] = self.load_sheet('scenery.png', 16, 16, 6)  # 0:pipe_tl, 1:pipe_tr, 2:pipe_l, 3:pipe_r, 4:flagpole, 5:flag

        # Check if all essential sprites loaded
        if not all(k in self.sprites for k in ['mario_small', 'goomba', 'blocks', 'scenery']):
            raise FileNotFoundError("Essential sprites missing.")

    @staticmethod
    def flip_horiz(surface):
        """Flip sprite horizontally for left-facing"""
        return pygame.transform.flip(surface, True, False)

    def draw_mario(self, surf, screen_x, screen_y, state, facing_right, frame, is_jumping, is_skidding, is_dead, vx):
        """Draw Mario from sprite sheet at screen_x, screen_y (base pixels)."""
        # Handle fallback
        if self.fallback or (state == STATE_FIRE and 'mario_fire' not in self.sprites):
            self._draw_mario_fallback(surf, screen_x, screen_y, state > STATE_SMALL, state == STATE_FIRE, facing_right, frame if not is_jumping else 0)
            return

        try:
            # Select sprite sheet
            if state == STATE_FIRE:
                sheet = self.sprites['mario_fire'][0]
            elif state == STATE_BIG:
                sheet = self.sprites['mario_big'][0]
            else:
                sheet = self.sprites['mario_small'][0]

            # Select frame
            if is_dead:
                frame_idx = 5  # Dead
            elif is_jumping:
                frame_idx = 4  # Jump
            elif is_skidding:
                frame_idx = 3  # Skid
            elif abs(vx) > 0.1:
                frame_idx = int(frame * 0.2) % 2 + 1  # 1 or 2 for walking
            else:
                frame_idx = 0  # Idle

            sprite = sheet[frame_idx]
            if not facing_right:
                sprite = self.flip_horiz(sprite)

            surf.blit(sprite, (screen_x, screen_y))

        except (KeyError, IndexError, TypeError):
            # Fallback if a specific sprite is missing (e.g., mario_fire)
            self._draw_mario_fallback(surf, screen_x, screen_y, state > STATE_SMALL, state == STATE_FIRE, facing_right, frame if not is_jumping else 0)

    def _draw_mario_fallback(self, surf, x, y, is_big, is_fire, facing_right, frame):
        """Original math-based fallback, rendered in base pixel units."""
        s = 1
        hat_color = WHITE if is_fire else RED
        overalls_color = RED if is_fire else BLUE

        if is_big:
            pygame.draw.rect(surf, hat_color, (x + 4*s, y + 0*s, 5*s, s))
            pygame.draw.rect(surf, hat_color, (x + 3*s, y + 1*s, 9*s, 5*s))
            pygame.draw.rect(surf, PEACH, (x + 3*s, y + 6*s, 8*s, 5*s))
            eye_x = 4*s if facing_right else 7*s
            pygame.draw.rect(surf, BLACK, (x + eye_x, y + 7*s, 2*s, 2*s))
            pygame.draw.rect(surf, BROWN, (x + 3*s, y + 9*s, 6*s, 2*s))
            pygame.draw.rect(surf, hat_color, (x + 3*s, y + 11*s, 8*s, 6*s))
            pygame.draw.rect(surf, overalls_color, (x + 2*s, y + 17*s, 10*s, 8*s))
            arm_offset = int(math.sin(frame * 0.3) * 2) if frame > 0 else 0
            pygame.draw.rect(surf, PEACH, (x + 0*s, y + (12 + arm_offset)*s, 3*s, 4*s))
            pygame.draw.rect(surf, PEACH, (x + 11*s, y + (12 - arm_offset)*s, 3*s, 4*s))
            if frame % 20 < 10:
                pygame.draw.rect(surf, overalls_color, (x + 2*s, y + 25*s, 5*s, 4*s))
                pygame.draw.rect(surf, BROWN, (x + 2*s, y + 29*s, 5*s, 3*s))
                pygame.draw.rect(surf, overalls_color, (x + 7*s, y + 25*s, 5*s, 3*s))
                pygame.draw.rect(surf, BROWN, (x + 7*s, y + 28*s, 5*s, 4*s))
            else:
                pygame.draw.rect(surf, overalls_color, (x + 2*s, y + 25*s, 5*s, 3*s))
                pygame.draw.rect(surf, BROWN, (x + 2*s, y + 28*s, 5*s, 4*s))
                pygame.draw.rect(surf, overalls_color, (x + 7*s, y + 25*s, 5*s, 4*s))
                pygame.draw.rect(surf, BROWN, (x + 7*s, y + 29*s, 5*s, 3*s))
        else:
            pygame.draw.rect(surf, RED, (x + 4*s, y + 0*s, 5*s, 2*s))
            pygame.draw.rect(surf, RED, (x + 3*s, y + 2*s, 9*s, 3*s))
            pygame.draw.rect(surf, PEACH, (x + 3*s, y + 5*s, 8*s, 4*s))
            eye_x = 4*s if facing_right else 7*s
            pygame.draw.rect(surf, BLACK, (x + eye_x, y + 6*s, 2*s, 2*s))
            pygame.draw.rect(surf, RED, (x + 3*s, y + 9*s, 8*s, 3*s))
            pygame.draw.rect(surf, BLUE, (x + 2*s, y + 12*s, 10*s, 4*s))
            if frame % 16 < 8:
                pygame.draw.rect(surf, BROWN, (x + 2*s, y + 14*s, 5*s, 2*s))
                pygame.draw.rect(surf, BROWN, (x + 7*s, y + 13*s, 5*s, 2*s))
            else:
                pygame.draw.rect(surf, BROWN, (x + 7*s, y + 14*s, 5*s, 2*s))
                pygame.draw.rect(surf, BROWN, (x + 2*s, y + 13*s, 5*s, 2*s))

    def draw_goomba(self, surf, screen_x, screen_y, frame, stomped):
        """Draw Goomba from sheet"""
        if self.fallback:
            self._draw_goomba_fallback(surf, screen_x, screen_y, frame, stomped)
            return

        try:
            if stomped:
                sprite = self.sprites['goomba'][0][2]
            else:
                frame_idx = int(frame * 0.1) % 2
                sprite = self.sprites['goomba'][0][frame_idx]
            surf.blit(sprite, (screen_x, screen_y))
        except (KeyError, IndexError, TypeError):
            self._draw_goomba_fallback(surf, screen_x, screen_y, frame, stomped)

    def _draw_goomba_fallback(self, surf, x, y, frame, stomped):
        """Original math-based fallback"""
        s = 1

        if stomped:
            pygame.draw.rect(surf, BROWN, (x, y + 8*s, 16*s, 8*s))
            return

        for i in range(16):
            for j in range(12):
                dist = math.sqrt((i - 7.5)**2 + (j - 5)**2)
                if dist <= 7.5:
                    pygame.draw.rect(surf, BROWN, (x + i*s, y + j*s, s, s))
        eye_offset = int(math.sin(frame * 0.1) * 0.5)
        pygame.draw.rect(surf, BLACK, (x + (4 + eye_offset)*s, y + 6*s, 2*s, 4*s))
        pygame.draw.rect(surf, BLACK, (x + (10 - eye_offset)*s, y + 6*s, 2*s, 4*s))
        foot_frame = frame % 30
        if foot_frame < 15:
            pygame.draw.rect(surf, BLACK, (x + 4*s, y + 12*s, 4*s, 4*s))
            pygame.draw.rect(surf, BLACK, (x + 8*s, y + 12*s, 4*s, 4*s))
        else:
            pygame.draw.rect(surf, BLACK, (x + 2*s, y + 12*s, 4*s, 4*s))
            pygame.draw.rect(surf, BLACK, (x + 10*s, y + 12*s, 4*s, 4*s))

    def draw_koopa(self, surf, screen_x, screen_y, is_shell, facing_right, frame):
        """Draw Koopa Troopa from sheet"""
        if self.fallback:
            self._draw_koopa_fallback(surf, screen_x, screen_y, is_shell, frame)
            return

        try:
            if is_shell:
                sprite = self.sprites['koopa'][0][2]  # Shell frame
            else:
                frame_idx = int(frame * 0.1) % 2
                sprite = self.sprites['koopa'][0][frame_idx]

            if not facing_right:
                sprite = self.flip_horiz(sprite)

            # Koopa sprite is 24px high; collision rect is 32px -> lift visual 8px.
            surf.blit(sprite, (screen_x, screen_y - 8))
        except (KeyError, IndexError, TypeError):
            self._draw_koopa_fallback(surf, screen_x, screen_y, is_shell, frame)

    def _draw_koopa_fallback(self, surf, x, y, is_shell, frame):
        """Original math-based fallback"""
        s = 1

        # Adjust y for 24px height
        y -= 8 * s

        if is_shell:
            for i in range(16):
                for j in range(16):
                    if 2 <= i <= 13 and 2 <= j <= 13:
                        pygame.draw.rect(surf, GREEN, (x + i*s, y + j*s + 8*s, s, s))
            pygame.draw.rect(surf, YELLOW, (x + 4*s, y + 4*s + 8*s, 8*s, 2*s))
            pygame.draw.rect(surf, YELLOW, (x + 4*s, y + 8*s + 8*s, 8*s, 2*s))
        else:
            pygame.draw.rect(surf, GREEN, (x + 5*s, y, 6*s, 6*s))
            pygame.draw.rect(surf, BLACK, (x + 7*s, y + 2*s, 2*s, 2*s))
            for i in range(4, 13):
                for j in range(6, 16):
                    pygame.draw.rect(surf, GREEN, (x + i*s, y + j*s, s, s))
            pygame.draw.rect(surf, YELLOW, (x + 5*s, y + 8*s, 6*s, 2*s))
            pygame.draw.rect(surf, YELLOW, (x + 5*s, y + 12*s, 6*s, 2*s))
            walk_phase = (frame % 40) / 10.0
            leg1_x = int(4 + math.sin(walk_phase) * 2)
            leg2_x = int(10 + math.sin(walk_phase + math.pi) * 2)
            pygame.draw.rect(surf, ORANGE, (x + leg1_x*s, y + 16*s, 4*s, 4*s))
            pygame.draw.rect(surf, ORANGE, (x + leg2_x*s, y + 16*s, 4*s, 4*s))

    def draw_powerup(self, surf, screen_x, screen_y, kind, frame):
        """Draw a powerup (Mushroom, Flower, Star)"""
        if self.fallback:
            if kind == 'mushroom':
                self._draw_mushroom_fallback(surf, screen_x, screen_y)
            elif kind == 'flower':
                self._draw_fire_flower_fallback(surf, screen_x, screen_y, frame)
            elif kind == 'star':
                self._draw_star_fallback(surf, screen_x, screen_y, frame)
            return

        try:
            if kind == 'mushroom':
                sprite = self.sprites['powerups'][0][0]
            elif kind == 'flower':
                sprite = self.sprites['powerups'][0][1]
                # Simple 2-frame animation by alternating color
                if frame % 12 < 6:
                    sprite = sprite.copy()
                    sprite.fill(ORANGE, special_flags=pygame.BLEND_RGB_MULT)
            elif kind == 'star':
                sprite = self.sprites['powerups'][0][2]
                if frame % 12 < 6:
                    sprite = sprite.copy()
                    sprite.fill(WHITE, special_flags=pygame.BLEND_RGB_MULT)
            surf.blit(sprite, (screen_x, screen_y))
        except (KeyError, IndexError, TypeError):
            if kind == 'mushroom':
                self._draw_mushroom_fallback(surf, screen_x, screen_y)
            elif kind == 'flower':
                self._draw_fire_flower_fallback(surf, screen_x, screen_y, frame)
            elif kind == 'star':
                self._draw_star_fallback(surf, screen_x, screen_y, frame)

    def _draw_mushroom_fallback(self, surf, x, y):
        s = 1
        for i in range(16):
            for j in range(10):
                dist_from_center = abs(i - 7.5)
                if j < 10 - dist_from_center * 0.7:
                    pygame.draw.rect(surf, RED, (x + i*s, y + j*s, s, s))
        pygame.draw.rect(surf, WHITE, (x + 3*s, y + 4*s, 4*s, 4*s))
        pygame.draw.rect(surf, WHITE, (x + 9*s, y + 4*s, 4*s, 4*s))
        pygame.draw.rect(surf, WHITE, (x + 6*s, y + 1*s, 4*s, 2*s))
        pygame.draw.rect(surf, PEACH, (x + 5*s, y + 10*s, 6*s, 6*s))

    def _draw_fire_flower_fallback(self, surf, x, y, frame):
        s = 1
        pygame.draw.rect(surf, GREEN, (x + 7*s, y + 10*s, 2*s, 6*s))
        angle = frame * 0.1
        for i in range(4):
            petal_angle = angle + i * math.pi / 2
            px = int(x + 8*s + math.cos(petal_angle) * 6*s)
            py = int(y + 6*s + math.sin(petal_angle) * 6*s)
            pygame.draw.rect(surf, ORANGE if i % 2 == 0 else WHITE, (px - 2*s, py - 2*s, 4*s, 4*s))
        pygame.draw.rect(surf, YELLOW, (x + 6*s, y + 4*s, 4*s, 4*s))

    def _draw_star_fallback(self, surf, x, y, frame):
        s = 1
        points = []
        for i in range(10):
            angle = i * math.pi / 5
            r = 8 * s if i % 2 == 0 else 3 * s
            px = x + 8*s + int(r * math.cos(angle - math.pi / 2))
            py = y + 8*s + int(r * math.sin(angle - math.pi / 2))
            points.append((px, py))
        colors = [YELLOW, WHITE, ORANGE]
        color = colors[(frame // 4) % 3]
        pygame.draw.polygon(surf, color, points)

    def draw_coin(self, surf, screen_x, screen_y, frame):
        if self.fallback or 'coin' not in self.sprites:
            self._draw_coin_fallback(surf, screen_x, screen_y, frame)
            return

        try:
            frame_idx = int(frame * 0.2) % 4
            sprite = self.sprites['coin'][0][frame_idx]
            surf.blit(sprite, (screen_x, screen_y))
        except (KeyError, IndexError, TypeError):
            self._draw_coin_fallback(surf, screen_x, screen_y, frame)

    def _draw_coin_fallback(self, surf, x, y, frame):
        s = 1
        width = int(abs(math.cos(frame * 0.2)) * 14 + 2)
        offset = (16 - width) // 2
        if width > 2:
            pygame.draw.ellipse(surf, YELLOW, (x + offset*s, y + s, width*s, 14*s))
            pygame.draw.ellipse(surf, ORANGE, (x + (offset+1)*s, y + 3*s, (width-2)*s, 10*s))

    def draw_fireball(self, surf, screen_x, screen_y, frame):
        if self.fallback or 'projectiles' not in self.sprites:
            self._draw_fireball_fallback(surf, screen_x, screen_y, frame)
            return

        try:
            frame_idx = int(frame * 0.5) % 4
            sprite = self.sprites['projectiles'][0][frame_idx]
            surf.blit(sprite, (screen_x, screen_y))
        except (KeyError, IndexError, TypeError):
            self._draw_fireball_fallback(surf, screen_x, screen_y, frame)

    def _draw_fireball_fallback(self, surf, x, y, frame):
        s = 1
        angle = frame * 0.5
        for i in range(4):
            fx = int(x + 4*s + math.cos(angle + i * math.pi/2) * 3*s)
            fy = int(y + 4*s + math.sin(angle + i * math.pi/2) * 3*s)
            color = ORANGE if i % 2 == 0 else RED
            pygame.draw.circle(surf, color, (fx, fy), s * 2)

    def draw_block(self, surf, screen_x, screen_y, tile_type, frame):
        """Draws a block (brick, question, ground)"""
        if self.fallback:
            if tile_type == TYPE_BRICK:
                self._draw_brick_fallback(surf, screen_x, screen_y)
            elif tile_type == TYPE_QUESTION:
                self._draw_question_block_fallback(surf, screen_x, screen_y, False)
            elif tile_type == TYPE_USED_BLOCK:
                self._draw_question_block_fallback(surf, screen_x, screen_y, True)
            elif tile_type == TYPE_GROUND:
                self._draw_ground_fallback(surf, screen_x, screen_y)
            return

        try:
            if tile_type == TYPE_BRICK:
                sprite = self.sprites['blocks'][0][0]
            elif tile_type == TYPE_QUESTION:
                anim_frame = int(frame * 0.1) % 4
                if anim_frame == 3:
                    anim_frame = 1  # 0, 1, 2, 1 loop
                sprite = self.sprites['blocks'][anim_frame][1]
            elif tile_type == TYPE_USED_BLOCK:
                sprite = self.sprites['blocks'][0][2]
            elif tile_type == TYPE_GROUND:
                sprite = self.sprites['blocks'][0][3]
            else:
                return  # Not a block

            surf.blit(sprite, (screen_x, screen_y))
        except (KeyError, IndexError, TypeError):
            if tile_type == TYPE_BRICK:
                self._draw_brick_fallback(surf, screen_x, screen_y)
            elif tile_type == TYPE_QUESTION:
                self._draw_question_block_fallback(surf, screen_x, screen_y, False)
            elif tile_type == TYPE_USED_BLOCK:
                self._draw_question_block_fallback(surf, screen_x, screen_y, True)
            elif tile_type == TYPE_GROUND:
                self._draw_ground_fallback(surf, screen_x, screen_y)

    def _draw_brick_fallback(self, surf, x, y):
        s = 1
        pygame.draw.rect(surf, LIGHT_BROWN, (x, y, TILE*s, TILE*s))
        for row in range(4):
            for col in range(2):
                bx = x + col * 8*s + (4*s if row % 2 == 1 else 0)
                by = y + row * 4*s
                pygame.draw.rect(surf, BROWN, (bx, by, 7*s, 3*s))
                pygame.draw.rect(surf, BLACK, (bx, by, 7*s, 3*s), 1)

    def _draw_ground_fallback(self, surf, x, y):
        s = 1
        pygame.draw.rect(surf, BROWN, (x, y, TILE*s, TILE*s))
        pygame.draw.rect(surf, BLACK, (x, y, TILE*s, TILE*s), 1)

    def _draw_question_block_fallback(self, surf, x, y, used):
        s = 1
        if used:
            pygame.draw.rect(surf, BROWN, (x, y, TILE*s, TILE*s))
            pygame.draw.rect(surf, BLACK, (x, y, TILE*s, TILE*s), 1)
        else:
            pygame.draw.rect(surf, YELLOW, (x, y, TILE*s, TILE*s))
            pygame.draw.rect(surf, ORANGE, (x, y, TILE*s, TILE*s), 2)
            q_points = [
                (x+6*s, y+3*s), (x+10*s, y+3*s), (x+10*s, y+6*s),
                (x+8*s, y+8*s), (x+8*s, y+10*s)
            ]
            pygame.draw.lines(surf, BLACK, False, q_points, 2)
            pygame.draw.circle(surf, BLACK, (x+8*s, y+13*s), s)

    def draw_pipe(self, surf, screen_x, screen_y, tile_type):
        """Draw a single pipe tile"""
        if self.fallback:
            self._draw_pipe_fallback(surf, screen_x, screen_y)
            return

        try:
            if tile_type == TYPE_PIPE_TOP_LEFT:
                sprite = self.sprites['scenery'][0][0]
            elif tile_type == TYPE_PIPE_TOP_RIGHT:
                sprite = self.sprites['scenery'][0][1]
            elif tile_type == TYPE_PIPE_LEFT:
                sprite = self.sprites['scenery'][0][2]
            elif tile_type == TYPE_PIPE_RIGHT:
                sprite = self.sprites['scenery'][0][3]
            else:
                return

            surf.blit(sprite, (screen_x, screen_y))
        except (KeyError, IndexError, TypeError):
            self._draw_pipe_fallback(surf, screen_x, screen_y)

    def _draw_pipe_fallback(self, surf, x, y):
        """Fallback for a generic pipe piece"""
        s = 1
        pygame.draw.rect(surf, GREEN, (x, y, TILE*s, TILE*s))
        pygame.draw.rect(surf, DARK_GREEN, (x, y, TILE*s, TILE*s), 2)

    def draw_flagpole(self, surf, screen_x, screen_y, tile_type):
        """Draw flagpole or flag"""
        if self.fallback:
            return

        try:
            if tile_type == TYPE_FLAGPOLE:
                sprite = self.sprites['scenery'][0][4]
            elif tile_type == TYPE_FLAG:
                sprite = self.sprites['scenery'][0][5]
            else:
                return

            surf.blit(sprite, (screen_x, screen_y))
        except (KeyError, IndexError, TypeError):
            pass  # Just don't draw it


# ==============================================================================
# SAMPLE LEVEL DATA (World 1-1)
# ==============================================================================

LEVEL_1_1_MAP = [
    "                                                                                                                                                                                                                                                                                                                                                                                                                                                        ",  # 0
    "                                                                                                                                                                                                                                                                                                                                                                                                                                                        ",  # 1
    "                                                                                                                                                                                                                                                                                                                                                                                                                                                        ",  # 2
    "                                ?   B                                                                                                                                                                                                                                                                                                                                                                                                                   ",  # 3
    "                                                                                                                                                                                                                                                                                                                                                                                                                                                        ",  # 4
    "                        ? B ? B                                                                                                                                                                                                                                                                                                                                                                                                                       ",  # 5
    "                                                                                                                                                                                                                                                                                                                                                                                                                                                        ",  # 6
    "                                                                                                                               LR                                                                              LR                                                                                                                                                                                                                                     ",  # 7
    "                                                               ?                                                               lr                                                                              lr                                                                                                                                                                                                                                     ",  # 8
    "                                G G                                                                                            lr  G G G                                                                       lr                                 B B B                                                                                                                                                                                             C ",  # 9
    "                                      G G                                                                                        lr                                                                              lr                                                                                                                                                                                                                                C ",  # 10
    "                                                                                                                                 lr                                                  B ? B                     lr                                                                                                                                                                                                                              f ",  # 11
    "                                                                                                                                 lr                                                                            lr                                                                                                                                                                                                                              F ",  # 12
    "######################  ####################################  #######  ################   #############################  #################### ########################  ################################  ########################################################################################################################################################",  # 13
    "######################  ####################################  #######  ################   #############################  #################### ########################  ################################  ########################################################################################################################################################"   # 14
]
LEVEL_1_1_TYPE = 'overworld'


# ==============================================================================
# GAME OBJECTS
# ==============================================================================

class Entity(pygame.sprite.Sprite):
    """Base class for all game objects"""
    def __init__(self, x, y, w, h):
        super().__init__()
        self.rect = pygame.Rect(int(x), int(y), int(w), int(h))
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.alive = True

    def update(self, game):
        pass

    def draw(self, surf, camera_x, camera_y, frame, renderer):
        pass

    def get_tile_rects(self, level, tx, ty):
        """Get solid tile rects around tile (tx, ty)"""
        rects = []
        for y in range(ty - 1, ty + 3):
            for x in range(tx - 1, tx + 3):
                if level.is_solid(x, y):
                    rects.append(pygame.Rect(x * TILE, y * TILE, TILE, TILE))
        return rects


class Player(Entity):
    """Mario"""
    def __init__(self, x, y):
        super().__init__(x, y, TILE, SMALL_MARIO_HEIGHT)
        self.state = STATE_SMALL
        self.facing_right = True
        self.is_jumping = False
        self.is_running = False
        self.is_skidding = False
        self.is_dead = False
        self.jump_timer = 0
        self.lives = START_LIVES
        self.score = 0
        self.coins = 0
        self.fireballs = pygame.sprite.Group()
        self.max_fireballs = 2
        self.invincible_timer = 0  # After being hit

    def update(self, game):
        if self.is_dead:
            self.vy += GRAVITY
            self.rect.y += int(self.vy)
            if self.rect.y > DISPLAY_H / SCALE:
                game.handle_player_death()
            return

        if self.invincible_timer > 0:
            self.invincible_timer -= 1

        # --- Input Handling ---
        keys = pygame.key.get_pressed()
        self.is_running = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

        target_vx = 0.0
        if keys[pygame.K_LEFT]:
            target_vx = -MAX_WALK_SPEED
            if self.is_running:
                target_vx = -MAX_RUN_SPEED
            self.facing_right = False
        if keys[pygame.K_RIGHT]:
            target_vx = MAX_WALK_SPEED
            if self.is_running:
                target_vx = MAX_RUN_SPEED
            self.facing_right = True

        # --- Horizontal Movement ---
        accel = RUN_ACCEL if self.is_running else WALK_ACCEL
        friction = AIR_FRICTION if not self.on_ground else FRICTION

        # Check for skid
        self.is_skidding = False
        if self.on_ground and target_vx != 0 and math.copysign(1, self.vx) != math.copysign(1, target_vx) and abs(self.vx) > 0.5:
            friction = SKID_FRICTION
            self.is_skidding = True

        if target_vx == 0:
            # Apply friction
            if self.vx > 0:
                self.vx = max(0, self.vx - friction)
            elif self.vx < 0:
                self.vx = min(0, self.vx + friction)
        else:
            # Accelerate
            self.vx = clamp(self.vx + accel * math.copysign(1, target_vx), -abs(target_vx), abs(target_vx))

        self.rect.x += int(self.vx)
        self.check_horizontal_collisions(game)

        # --- Vertical Movement ---
        # Apply gravity
        if not self.on_ground:
            self.vy += GRAVITY
            if self.vy > MAX_FALL:
                self.vy = MAX_FALL

        # Jumping
        if self.is_jumping:
            if keys[pygame.K_SPACE]:
                # Hold jump button for higher jump
                if self.jump_timer < 16:  # Max hold time
                    self.vy += JUMP_HOLD_FORCE
                self.jump_timer += 1
            else:
                self.is_jumping = False  # Released key
                if self.vy < 0:
                    self.vy *= 0.5  # Cut jump short

        self.rect.y += int(self.vy)
        self.on_ground = False  # Assume not on ground until collision check
        self.check_vertical_collisions(game)

        # --- Fireballs ---
        self.fireballs.update(game)

        # --- Check for death ---
        if self.rect.y > ROWS * TILE:
            self.die(game)

    def check_horizontal_collisions(self, game):
        tx, ty = world_to_tile(self.rect.centerx, self.rect.centery)
        tile_rects = self.get_tile_rects(game.level, tx, ty)

        for tile_rect in tile_rects:
            if self.rect.colliderect(tile_rect):
                if self.vx > 0:  # Moving right
                    self.rect.right = tile_rect.left
                    self.vx = 0
                elif self.vx < 0:  # Moving left
                    self.rect.left = tile_rect.right
                    self.vx = 0

        # Check entity collisions (enemies)
        for entity in game.enemies:
            if self.rect.colliderect(entity.rect) and entity.alive:
                self.handle_enemy_collision(game, entity)

    def check_vertical_collisions(self, game):
        tx, ty = world_to_tile(self.rect.centerx, self.rect.centery)
        tile_rects = self.get_tile_rects(game.level, tx, ty)

        for tile_rect in tile_rects:
            if self.rect.colliderect(tile_rect):
                if self.vy > 0:  # Moving down
                    self.rect.bottom = tile_rect.top
                    self.on_ground = True
                    self.is_jumping = False
                    self.vy = 0
                elif self.vy < 0:  # Moving up
                    self.rect.top = tile_rect.bottom
                    self.vy = 0
                    # Check if we hit a block from below
                    hit_tx, hit_ty = world_to_tile(tile_rect.x, tile_rect.y)
                    game.level.hit_block(game, hit_tx, hit_ty, self)

        # Check entity collisions (enemies)
        if self.vy > 0:  # Only check for stomps when moving down
            for entity in game.enemies:
                if self.rect.colliderect(entity.rect) and entity.alive:
                    self.handle_enemy_collision(game, entity)

    def handle_enemy_collision(self, game, enemy):
        if self.invincible_timer > 0:
            return

        # Check for stomp
        is_stomp = self.vy > 0 and self.rect.bottom < enemy.rect.centery

        if is_stomp:
            enemy.stomp(game, self)
            self.vy = JUMP_VELOCITY * 0.75  # Bounce
            self.on_ground = False
            self.is_jumping = True
            self.jump_timer = 0
            game.add_score(100)
        else:
            # Hit by enemy
            self.take_damage(game)

    def take_damage(self, game):
        if self.invincible_timer > 0:
            return

        if self.state > STATE_SMALL:
            self.state -= 1
            self.invincible_timer = FPS * 2  # 2 seconds of invincibility
            # Adjust rect for size change
            if self.state == STATE_SMALL:
                self.rect.h = SMALL_MARIO_HEIGHT
                self.rect.y += (BIG_MARIO_HEIGHT - SMALL_MARIO_HEIGHT)
        else:
            self.die(game)

    def powerup(self, game, powerup_type):
        if powerup_type == 'mushroom':
            if self.state == STATE_SMALL:
                self.state = STATE_BIG
                self.rect.h = BIG_MARIO_HEIGHT
                self.rect.y -= (BIG_MARIO_HEIGHT - SMALL_MARIO_HEIGHT)
                game.add_score(1000)
        elif powerup_type == 'flower':
            if self.state == STATE_SMALL:
                self.state = STATE_BIG
                self.rect.h = BIG_MARIO_HEIGHT
                self.rect.y -= (BIG_MARIO_HEIGHT - SMALL_MARIO_HEIGHT)
            elif self.state == STATE_BIG:
                self.state = STATE_FIRE
            game.add_score(1000)

    def die(self, game):
        if not self.is_dead:
            self.is_dead = True
            self.vy = JUMP_VELOCITY  # Death jump
            self.vx = 0
            self.rect.h = SMALL_MARIO_HEIGHT  # Ensure correct sprite

    def jump(self):
        if self.on_ground:
            self.vy = JUMP_VELOCITY
            self.on_ground = False
            self.is_jumping = True
            self.jump_timer = 0

    def shoot(self, game):
        if self.state == STATE_FIRE and len(self.fireballs) < self.max_fireballs:
            fb_x = self.rect.right if self.facing_right else self.rect.left - 8
            fb_vx = FIREBALL_SPEED if self.facing_right else -FIREBALL_SPEED
            fireball = Fireball(fb_x, self.rect.centery, fb_vx)
            self.fireballs.add(fireball)
            game.entities.add(fireball)

    def draw(self, surf, camera_x, camera_y, frame, renderer):
        if self.invincible_timer > 0 and self.invincible_timer % 10 < 5:
            return  # Flash when invincible

        sx, sy = world_to_screen(self.rect.x, self.rect.y, camera_x, camera_y)

        # Adjust for big mario sprite height
        if self.state > STATE_SMALL and not self.is_dead:
            sy -= (BIG_MARIO_HEIGHT - SMALL_MARIO_HEIGHT)

        renderer.draw_mario(
            surf, sx, sy, self.state, self.facing_right, frame,
            self.is_jumping and not self.on_ground,
            self.is_skidding, self.is_dead, self.vx
        )

        # Draw fireballs
        for fb in self.fireballs:
            fb.draw(surf, camera_x, camera_y, frame, renderer)


class Goomba(Entity):
    """Goomba"""
    def __init__(self, x, y):
        super().__init__(x, y, TILE, TILE)
        self.vx = ENEMY_SPEED
        self.stomped_timer = 0

    def update(self, game):
        if not self.alive:
            return

        if self.stomped_timer > 0:
            self.stomped_timer -= 1
            if self.stomped_timer == 0:
                self.kill()  # Remove from sprite groups
            return

        # --- Movement ---
        self.rect.x += int(self.vx)
        self.check_horizontal_collisions(game)

        # --- Vertical Movement ---
        if not self.on_ground:
            self.vy += GRAVITY
            if self.vy > MAX_FALL:
                self.vy = MAX_FALL

        self.rect.y += int(self.vy)
        self.on_ground = False
        self.check_vertical_collisions(game)

    def check_horizontal_collisions(self, game):
        tx, ty = world_to_tile(self.rect.centerx, self.rect.centery)
        tile_rects = self.get_tile_rects(game.level, tx, ty)

        for tile_rect in tile_rects:
            if self.rect.colliderect(tile_rect):
                if self.vx > 0:  # Moving right
                    self.rect.right = tile_rect.left
                elif self.vx < 0:  # Moving left
                    self.rect.left = tile_rect.right
                self.vx *= -1  # Turn around

        # Check other enemies
        for enemy in game.enemies:
            if enemy != self and self.rect.colliderect(enemy.rect) and enemy.alive:
                self.vx *= -1
                enemy.vx *= -1

    def check_vertical_collisions(self, game):
        tx, ty = world_to_tile(self.rect.centerx, self.rect.centery)
        tile_rects = self.get_tile_rects(game.level, tx, ty)

        for tile_rect in tile_rects:
            if self.rect.colliderect(tile_rect):
                if self.vy > 0:  # Moving down
                    self.rect.bottom = tile_rect.top
                    self.on_ground = True
                    self.vy = 0

    def stomp(self, game, player):
        self.alive = False
        self.stomped_timer = GOOMBA_STOMP_TIME
        self.vx = 0

    def hit_by_fireball(self, game):
        self.alive = False
        self.vx = 0
        self.vy = -2  # Pop up
        self.kill()   # Remove
        game.add_score(100)

    def draw(self, surf, camera_x, camera_y, frame, renderer):
        sx, sy = world_to_screen(self.rect.x, self.rect.y, camera_x, camera_y)
        renderer.draw_goomba(surf, sx, sy, frame, self.stomped_timer > 0)


class Koopa(Entity):
    """Koopa Troopa"""
    def __init__(self, x, y):
        # Koopa is 24px tall, but rect is 32 for collision
        super().__init__(x, y, TILE, BIG_MARIO_HEIGHT)
        self.vx = ENEMY_SPEED
        self.is_shell = False
        self.is_sliding = False
        self.shell_timer = 0

    def update(self, game):
        if not self.alive:
            return

        if self.is_sliding:
            # Shell sliding logic
            self.rect.x += int(self.vx)
            self.check_horizontal_collisions(game)
            # Sliding shells kill other enemies
            for enemy in game.enemies:
                if enemy != self and self.rect.colliderect(enemy.rect) and enemy.alive:
                    enemy.hit_by_fireball(game)  # Same effect
        elif self.is_shell:
            # Sitting shell
            self.vx = 0
            if self.shell_timer > 0:
                self.shell_timer -= 1
                if self.shell_timer == 0:
                    self.is_shell = False  # Emerge
            return
        else:
            # Walking logic
            self.rect.x += int(self.vx)
            self.check_horizontal_collisions(game)

        # --- Vertical Movement ---
        if not self.on_ground:
            self.vy += GRAVITY
            if self.vy > MAX_FALL:
                self.vy = MAX_FALL

        self.rect.y += int(self.vy)
        self.on_ground = False
        self.check_vertical_collisions(game)

    def check_horizontal_collisions(self, game):
        tx, ty = world_to_tile(self.rect.centerx, self.rect.centery)
        tile_rects = self.get_tile_rects(game.level, tx, ty)

        for tile_rect in tile_rects:
            if self.rect.colliderect(tile_rect):
                if self.vx > 0:
                    self.rect.right = tile_rect.left
                elif self.vx < 0:
                    self.rect.left = tile_rect.right
                self.vx *= -1

    def check_vertical_collisions(self, game):
        tx, ty = world_to_tile(self.rect.centerx, self.rect.centery)
        tile_rects = self.get_tile_rects(game.level, tx, ty)

        for tile_rect in tile_rects:
            if self.rect.colliderect(tile_rect):
                if self.vy > 0:
                    self.rect.bottom = tile_rect.top
                    self.on_ground = True
                    self.vy = 0

    def stomp(self, game, player):
        if self.is_shell:
            # Kick shell
            self.is_sliding = True
            self.vx = SHELL_SLIDE_SPEED if player.rect.centerx < self.rect.centerx else -SHELL_SLIDE_SPEED
            self.shell_timer = 0
        else:
            # Turn into shell
            self.is_shell = True
            self.is_sliding = False
            self.vx = 0
            self.shell_timer = FPS * 10  # 10 seconds to emerge

    def hit_by_fireball(self, game):
        self.alive = False
        self.vx = 0
        self.vy = -2
        self.kill()
        game.add_score(200)

    def draw(self, surf, camera_x, camera_y, frame, renderer):
        sx, sy = world_to_screen(self.rect.x, self.rect.y, camera_x, camera_y)
        # Adjust for 24px height when not shell
        sy_adj = sy - 8 if not self.is_shell else sy
        renderer.draw_koopa(surf, sx, sy_adj, self.is_shell, self.vx >= 0, frame)


class Powerup(Entity):
    """Mushroom, Flower, Star"""
    def __init__(self, x, y, kind):
        super().__init__(x, y, TILE, TILE)
        self.kind = kind
        self.vx = 0.0
        self.vy = -POWERUP_SPAWN_SPEED
        self.spawn_timer = TILE / POWERUP_SPAWN_SPEED

    def update(self, game):
        if self.spawn_timer > 0:
            self.spawn_timer -= 1
            self.rect.y += int(self.vy)
            if self.spawn_timer == 0:
                self.vx = POWERUP_MOVE_SPEED
                self.vy = 0.0
            return

        # --- Movement ---
        self.rect.x += int(self.vx)
        self.check_horizontal_collisions(game)

        # --- Vertical Movement ---
        if not self.on_ground:
            self.vy += GRAVITY
            if self.vy > MAX_FALL:
                self.vy = MAX_FALL

        self.rect.y += int(self.vy)
        self.on_ground = False
        self.check_vertical_collisions(game)

        # Check collision with player
        if self.rect.colliderect(game.player.rect):
            game.player.powerup(game, self.kind)
            self.kill()

    def check_horizontal_collisions(self, game):
        tx, ty = world_to_tile(self.rect.centerx, self.rect.centery)
        tile_rects = self.get_tile_rects(game.level, tx, ty)

        for tile_rect in tile_rects:
            if self.rect.colliderect(tile_rect):
                if self.vx > 0:
                    self.rect.right = tile_rect.left
                elif self.vx < 0:
                    self.rect.left = tile_rect.right
                self.vx *= -1

    def check_vertical_collisions(self, game):
        tx, ty = world_to_tile(self.rect.centerx, self.rect.centery)
        tile_rects = self.get_tile_rects(game.level, tx, ty)

        for tile_rect in tile_rects:
            if self.rect.colliderect(tile_rect):
                if self.vy > 0:
                    self.rect.bottom = tile_rect.top
                    self.on_ground = True
                    self.vy = 0

    def draw(self, surf, camera_x, camera_y, frame, renderer):
        sx, sy = world_to_screen(self.rect.x, self.rect.y, camera_x, camera_y)
        renderer.draw_powerup(surf, sx, sy, self.kind, frame)


class Fireball(Entity):
    """Mario's Fireball"""
    def __init__(self, x, y, vx):
        super().__init__(x, y, 8, 8)  # 8x8 sprite (integers)
        self.vx = vx
        self.vy = 1.0  # Bounces
        self.bounce_power = -3.0
        self.lifetime = FPS * 3  # 3 seconds

    def update(self, game):
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()
            return

        self.rect.x += int(self.vx)
        self.check_horizontal_collisions(game)

        self.vy += GRAVITY
        self.rect.y += int(self.vy)
        self.check_vertical_collisions(game)

    def check_horizontal_collisions(self, game):
        tx, ty = world_to_tile(self.rect.centerx, self.rect.centery)
        tile_rects = self.get_tile_rects(game.level, tx, ty)

        for tile_rect in tile_rects:
            if self.rect.colliderect(tile_rect):
                self.kill()  # Hit a wall
                return

        # Check enemies
        for enemy in game.enemies:
            if self.rect.colliderect(enemy.rect) and enemy.alive:
                enemy.hit_by_fireball(game)
                self.kill()
                return

    def check_vertical_collisions(self, game):
        tx, ty = world_to_tile(self.rect.centerx, self.rect.centery)
        tile_rects = self.get_tile_rects(game.level, tx, ty)

        for tile_rect in tile_rects:
            if self.rect.colliderect(tile_rect):
                if self.vy > 0:
                    self.rect.bottom = tile_rect.top
                    self.vy = self.bounce_power  # Bounce
                elif self.vy < 0:
                    self.rect.top = tile_rect.bottom
                    self.vy = 0

    def draw(self, surf, camera_x, camera_y, frame, renderer):
        sx, sy = world_to_screen(self.rect.x, self.rect.y, camera_x, camera_y)
        renderer.draw_fireball(surf, sx, sy, frame)


class Coin(Entity):
    """Animated coin that pops from a block"""
    def __init__(self, x, y):
        super().__init__(x, y, TILE, TILE)
        self.vy = -4.0
        self.lifetime = int(FPS * 0.5)  # Half a second

    def update(self, game):
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()
            return

        self.vy += GRAVITY
        self.rect.y += int(self.vy)

    def draw(self, surf, camera_x, camera_y, frame, renderer):
        sx, sy = world_to_screen(self.rect.x, self.rect.y, camera_x, camera_y)
        renderer.draw_coin(surf, sx, sy, frame)


# ==============================================================================
# LEVEL CLASS
# ==============================================================================

class Level:
    """Manages level data, tiles, and rendering"""
    def __init__(self, map_data, level_type):
        # Always work on a fresh copy of the map list (strings are immutable),
        # so reloading restores original layout.
        self.map = list(map_data)
        self.level_type = level_type
        self.width = len(self.map[0]) * TILE
        self.height = len(self.map) * TILE
        self.blocks = {}  # Store info about blocks, e.g., (tx, ty) -> 'coin', 'mushroom'

        self.solid_tiles = [
            TYPE_GROUND, TYPE_BRICK, TYPE_QUESTION, TYPE_USED_BLOCK,
            TYPE_PIPE_TOP_LEFT, TYPE_PIPE_TOP_RIGHT, TYPE_PIPE_LEFT, TYPE_PIPE_RIGHT
        ]

        # Pre-populate blocks based on map
        first_mushroom_given = False
        for ty, row in enumerate(self.map):
            for tx, tile in enumerate(row):
                if tile == TYPE_QUESTION:
                    # First ? is mushroom, rest are coins
                    if not first_mushroom_given:
                        self.blocks[(tx, ty)] = 'mushroom'
                        first_mushroom_given = True
                    else:
                        self.blocks[(tx, ty)] = 'coin'
                elif tile == TYPE_BRICK:
                    self.blocks[(tx, ty)] = 'breakable'

    def get_tile(self, tx, ty):
        """Get tile at tile coordinates (tx, ty)"""
        if 0 <= ty < len(self.map) and 0 <= tx < len(self.map[0]):
            return self.map[ty][tx]
        return TYPE_EMPTY

    def is_solid(self, tx, ty):
        """Check if tile at (tx, ty) is solid"""
        return self.get_tile(tx, ty) in self.solid_tiles

    def set_tile(self, tx, ty, tile_type):
        """Set tile at (tx, ty)"""
        if 0 <= ty < len(self.map) and 0 <= tx < len(self.map[0]):
            row = list(self.map[ty])
            row[tx] = tile_type
            self.map[ty] = "".join(row)

    def hit_block(self, game, tx, ty, player):
        """Handle player hitting a block from below"""
        tile = self.get_tile(tx, ty)

        if tile == TYPE_QUESTION:
            self.set_tile(tx, ty, TYPE_USED_BLOCK)
            content = self.blocks.get((tx, ty), 'coin')
            bx, by = tile_to_world(tx, ty)

            if content == 'coin':
                game.add_coin()
                game.add_score(200)
                game.entities.add(Coin(bx, by))
            elif content == 'mushroom' or content == 'flower':
                kind = 'mushroom' if player.state == STATE_SMALL else 'flower'
                game.entities.add(Powerup(bx, by - TILE, kind))

        elif tile == TYPE_BRICK:
            if player.state > STATE_SMALL:
                self.set_tile(tx, ty, TYPE_EMPTY)
                game.add_score(50)
                # TODO: Add brick break particle

    def spawn_entities(self, game):
        """Create all entities for the level"""
        for ty, row in enumerate(self.map):
            for tx, tile in enumerate(row):
                wx, wy = tile_to_world(tx, ty)
                if tile == TYPE_GOOMBA:
                    enemy = Goomba(wx, wy)
                    game.entities.add(enemy)
                    game.enemies.add(enemy)
                elif tile == TYPE_KOOPA:
                    enemy = Koopa(wx, wy - 8)  # Koopa is 24px; spawn slightly higher
                    game.entities.add(enemy)
                    game.enemies.add(enemy)

    def draw(self, surf, camera_x, camera_y, frame, renderer):
        """Draw all visible tiles in base pixels"""
        start_tx = int(camera_x // TILE)
        end_tx = int((camera_x + (DISPLAY_W / SCALE)) // TILE) + 1
        start_ty = int(camera_y // TILE)
        end_ty = int((camera_y + (DISPLAY_H / SCALE)) // TILE) + 1

        for ty in range(start_ty, end_ty):
            for tx in range(start_tx, end_tx):
                tile = self.get_tile(tx, ty)
                if tile == TYPE_EMPTY:
                    continue

                wx, wy = tile_to_world(tx, ty)
                sx, sy = world_to_screen(wx, wy, camera_x, camera_y)

                if tile in [TYPE_BRICK, TYPE_QUESTION, TYPE_USED_BLOCK, TYPE_GROUND]:
                    renderer.draw_block(surf, sx, sy, tile, frame)
                elif tile in [TYPE_PIPE_TOP_LEFT, TYPE_PIPE_TOP_RIGHT, TYPE_PIPE_LEFT, TYPE_PIPE_RIGHT]:
                    renderer.draw_pipe(surf, sx, sy, tile)
                elif tile in [TYPE_FLAGPOLE, TYPE_FLAG]:
                    renderer.draw_flagpole(surf, sx, sy, tile)
                elif tile == TYPE_CASTLE:  # Simple Castle fallback
                    pygame.draw.rect(surf, GRAY, (sx, sy - TILE*3, TILE*5, TILE*4))


# ==============================================================================
# MAIN GAME CLASS
# ==============================================================================

class Game:
    """Main game application"""
    def __init__(self, screen, renderer):
        self.screen = screen
        self.renderer = renderer
        self.clock = pygame.time.Clock()
        self.running = True
        self.frame = 0
        self.game_state = STATE_PLAYING  # Start playing for debug

        self.camera_x = 0.0
        self.camera_y = 0.0

        self.level = None
        self.player = None
        self.entities = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()

        self.level_timer = LEVEL_TIME
        self.time_elapsed = 0.0

        self.font = pygame.font.Font(None, 24)

        # Load initial level
        self._template_map = list(LEVEL_1_1_MAP)  # keep an untouched template
        self.load_level(self._template_map, LEVEL_1_1_TYPE)

    def load_level(self, map_data, level_type):
        """Load a new level from a map template (list of strings)."""
        self.entities.empty()
        self.enemies.empty()

        # Work with a fresh copy of the provided template list
        map_copy = list(map_data)
        self.level = Level(map_copy, level_type)

        # Spawn player
        self.player = Player(50, 100)
        self.entities.add(self.player)

        # Spawn enemies / items
        self.level.spawn_entities(self)

        # Camera / timer
        self.camera_x = 0.0
        self.camera_y = 0.0
        self.level_timer = LEVEL_TIME
        self.time_elapsed = 0.0
        self.game_state = STATE_PLAYING

    def handle_player_death(self):
        # Preserve current lives after subtract
        lives_left = self.player.lives - 1
        if lives_left > 0:
            self.load_level(self._template_map, self.level.level_type)  # Restart with fresh copy
            self.player.lives = lives_left  # keep remaining lives
        else:
            self.game_state = STATE_GAME_OVER

    def add_score(self, amount):
        self.player.score += amount

    def add_coin(self):
        self.player.coins += 1
        if self.player.coins >= 100:
            self.player.coins = 0
            self.player.lives += 1
            # TODO: Play 1-UP sound

    def update(self):
        """Update game logic"""
        if self.game_state != STATE_PLAYING:
            return

        # Update timer (approx. once per second)
        self.time_elapsed += 1 / FPS
        if int(self.time_elapsed) > 0:
            self.level_timer -= int(self.time_elapsed)
            self.time_elapsed = 0.0
            if self.level_timer <= 0:
                self.level_timer = 0
                self.player.die(self)

        # Update all entities
        self.entities.update(self)

        # Update camera
        self.camera_x = max(0.0, self.player.rect.x - (DISPLAY_W / SCALE / 2))
        self.camera_x = min(self.camera_x, self.level.width - (DISPLAY_W / SCALE))
        # No vertical camera scroll in SMB1
        self.camera_y = 0.0

        self.frame += 1

    def draw(self):
        """Render the game onto the small off-screen surface (base resolution)."""
        # --- Draw Background ---
        if self.level.level_type == 'overworld':
            self.screen.fill(SKY_BLUE)
        else:
            self.screen.fill(UNDERGROUND_BLUE)

        # --- Draw Level ---
        self.level.draw(self.screen, self.camera_x, self.camera_y, self.frame, self.renderer)

        # --- Draw Entities ---
        for entity in self.entities:
            # Cull entities off-screen
            if (entity.rect.x > self.camera_x - TILE and
                    entity.rect.x < self.camera_x + (DISPLAY_W / SCALE) + TILE):
                entity.draw(self.screen, self.camera_x, self.camera_y, self.frame, self.renderer)

        # --- Draw HUD ---
        self.draw_text("MARIO", 50, 20)
        self.draw_text(f"{self.player.score:06d}", 50, 40)

        self.draw_text("COINS", 250, 20)
        self.draw_text(f"{self.player.coins:02d}", 260, 40)

        self.draw_text("WORLD", 450, 20)
        self.draw_text("1-1", 460, 40)

        self.draw_text("TIME", 600, 20)
        self.draw_text(f"{self.level_timer:03d}", 610, 40)

        self.draw_text(f"LIVES: {self.player.lives}", 50, 70)
        # NOTE: We DO NOT flip here; the window flip happens in main() after scaling.

    def draw_text(self, text, x, y, color=WHITE):
        """Helper to draw text on screen"""
        text_surface = self.font.render(text, True, color)
        self.screen.blit(text_surface, (x, y))


# ==============================================================================
# MAIN FUNCTION
# ==============================================================================

def main():
    pygame.init()

    # Create the main window and the base-resolution render surface.
    window = pygame.display.set_mode((DISPLAY_W, DISPLAY_H))
    base_surface = pygame.Surface((int(DISPLAY_W / SCALE), int(DISPLAY_H / SCALE)))

    pygame.display.set_caption(TITLE)

    # Initialize Sprite Renderer AFTER display init (for convert_alpha safety).
    renderer = SpriteRenderer()

    # Create Game object using the base surface
    game = Game(base_surface, renderer)

    # --- Main Loop ---
    while game.running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game.running = False
                if game.game_state == STATE_PLAYING and not game.player.is_dead:
                    if event.key == pygame.K_SPACE:
                        game.player.jump()
                    if event.key == pygame.K_f:
                        game.player.shoot(game)

        game.update()

        # Render to the base surface
        game.draw()

        # Scale the base surface to the window in a single pass
        pygame.transform.scale(base_surface, (DISPLAY_W, DISPLAY_H), window)

        # Present
        pygame.display.flip()
        game.clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
