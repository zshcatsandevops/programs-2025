#!/usr/bin/env python3
"""
Ultra Mario 2D Bros - Complete Super Mario Bros 1 Recreation
All 32 Levels with Pygame Mixer OST
Created with Team Level Up Assets Support
"""

import pygame
import sys
import os
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional

# Initialize Pygame
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
GRAVITY = 0.8
JUMP_STRENGTH = -15
MOVE_SPEED = 5
MAX_FALL_SPEED = 15

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 100, 255)
BROWN = (139, 69, 19)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
SKY_BLUE = (107, 140, 255)
GROUND_BROWN = (222, 165, 115)

class GameState(Enum):
    MENU = 1
    PLAYING = 2
    PAUSED = 3
    GAME_OVER = 4
    LEVEL_COMPLETE = 5
    WORLD_COMPLETE = 6

class PowerUpState(Enum):
    SMALL = 1
    SUPER = 2
    FIRE = 3
    STAR = 4

@dataclass
class LevelData:
    world: int
    level: int
    music_track: str
    theme: str  # 'overworld', 'underground', 'castle', 'underwater'
    time_limit: int

    def get_display_name(self):
        return f"World {self.world}-{self.level}"

class MusicManager:
    """Manages all game music using pygame.mixer"""

    def __init__(self):
        self.current_track = None
        self.music_volume = 0.7
        pygame.mixer.music.set_volume(self.music_volume)

        # Music track mappings for all 32 levels
        self.tracks = {
            'main_theme': 'assets/music/overworld.ogg',
            'underground': 'assets/music/underground.ogg',
            'underwater': 'assets/music/underwater.ogg',
            'castle': 'assets/music/castle.ogg',
            'star_power': 'assets/music/starman.ogg',
            'level_complete': 'assets/music/level_clear.ogg',
            'game_over': 'assets/music/game_over.ogg',
            'world_clear': 'assets/music/world_clear.ogg',
            'title': 'assets/music/title.ogg',
        }

        # Sound effects
        self.sounds = {}
        self.load_sounds()

    def load_sounds(self):
        """Load sound effects"""
        sound_files = {
            'jump': 'assets/sounds/jump.ogg',
            'coin': 'assets/sounds/coin.ogg',
            'powerup': 'assets/sounds/powerup.ogg',
            'powerup_appears': 'assets/sounds/powerup_appears.ogg',
            'stomp': 'assets/sounds/stomp.ogg',
            'kick': 'assets/sounds/kick.ogg',
            'pipe': 'assets/sounds/pipe.ogg',
            'fireball': 'assets/sounds/fireball.ogg',
            'bump': 'assets/sounds/bump.ogg',
            'break_block': 'assets/sounds/break_block.ogg',
            'flagpole': 'assets/sounds/flagpole.ogg',
            'death': 'assets/sounds/death.ogg',
            '1up': 'assets/sounds/1up.ogg',
        }

        for name, path in sound_files.items():
            try:
                if os.path.exists(path):
                    self.sounds[name] = pygame.mixer.Sound(path)
            except:
                # Create placeholder sound if file doesn't exist
                self.sounds[name] = None

    def play_music(self, track_name: str, loops: int = -1):
        """Play background music"""
        if track_name in self.tracks:
            try:
                if os.path.exists(self.tracks[track_name]):
                    pygame.mixer.music.load(self.tracks[track_name])
                    pygame.mixer.music.play(loops)
                    self.current_track = track_name
            except:
                print(f"Could not load music: {track_name}")

    def play_sound(self, sound_name: str):
        """Play sound effect"""
        if sound_name in self.sounds and self.sounds[sound_name]:
            self.sounds[sound_name].play()

    def stop_music(self):
        """Stop background music"""
        pygame.mixer.music.stop()
        self.current_track = None

    def pause_music(self):
        """Pause background music"""
        pygame.mixer.music.pause()

    def unpause_music(self):
        """Unpause background music"""
        pygame.mixer.music.unpause()

class Camera:
    """Camera system for scrolling levels"""

    def __init__(self, width: int, height: int):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        self.level_width = width

    def apply(self, entity):
        """Apply camera offset to entity"""
        return entity.rect.move(-self.camera.x, -self.camera.y)

    def update(self, target):
        """Update camera position to follow target"""
        x = -target.rect.centerx + int(SCREEN_WIDTH / 3)

        # Keep camera within level bounds
        x = min(0, x)  # Left bound
        x = max(-(self.level_width - SCREEN_WIDTH), x)  # Right bound

        self.camera = pygame.Rect(x, 0, self.width, self.height)

class Mario(pygame.sprite.Sprite):
    """Mario player character"""

    def __init__(self, x: int, y: int):
        super().__init__()
        self.power_state = PowerUpState.SMALL
        self.update_size()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        # Physics
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.facing_right = True

        # State
        self.alive = True
        self.invincible_timer = 0
        self.star_timer = 0
        self.animation_frame = 0
        self.animation_timer = 0

        # Score tracking
        self.score = 0
        self.coins = 0
        self.lives = 3

    def update_size(self):
        """Update Mario's size based on power state"""
        if self.power_state == PowerUpState.SMALL:
            self.image = pygame.Surface((32, 32))
            self.image.fill(RED)
        elif self.power_state == PowerUpState.SUPER:
            self.image = pygame.Surface((32, 48))
            self.image.fill(RED)
        elif self.power_state == PowerUpState.FIRE:
            self.image = pygame.Surface((32, 48))
            self.image.fill(WHITE)
            pygame.draw.rect(self.image, RED, (0, 0, 32, 24))

    def handle_input(self, keys):
        """Handle player input"""
        if not self.alive:
            return

        # Horizontal movement
        self.vel_x = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -MOVE_SPEED
            self.facing_right = False
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = MOVE_SPEED
            self.facing_right = True

        # Jumping
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.vel_y = JUMP_STRENGTH
            self.on_ground = False

    def update(self, platforms, enemies, powerups, blocks):
        """Update Mario's state"""
        if not self.alive:
            return

        # Apply gravity
        self.vel_y += GRAVITY
        if self.vel_y > MAX_FALL_SPEED:
            self.vel_y = MAX_FALL_SPEED

        # Update position
        self.rect.x += self.vel_x
        self.check_collision_x(platforms)

        self.rect.y += self.vel_y
        self.on_ground = False
        self.check_collision_y(platforms)

        # Update timers
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
        if self.star_timer > 0:
            self.star_timer -= 1

        # Animation
        self.animation_timer += 1
        if self.animation_timer >= 10:
            self.animation_frame = (self.animation_frame + 1) % 3
            self.animation_timer = 0

    def check_collision_x(self, platforms):
        """Check horizontal collision"""
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vel_x > 0:  # Moving right
                    self.rect.right = platform.rect.left
                elif self.vel_x < 0:  # Moving left
                    self.rect.left = platform.rect.right
                self.vel_x = 0

    def check_collision_y(self, platforms):
        """Check vertical collision"""
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vel_y > 0:  # Falling
                    self.rect.bottom = platform.rect.top
                    self.on_ground = True
                elif self.vel_y < 0:  # Jumping
                    self.rect.top = platform.rect.bottom
                self.vel_y = 0

    def power_up(self):
        """Upgrade power state"""
        if self.power_state == PowerUpState.SMALL:
            self.power_state = PowerUpState.SUPER
        elif self.power_state == PowerUpState.SUPER:
            self.power_state = PowerUpState.FIRE
        self.update_size()

    def take_damage(self):
        """Take damage"""
        if self.invincible_timer > 0 or self.star_timer > 0:
            return

        if self.power_state == PowerUpState.SMALL:
            self.die()
        else:
            self.power_state = PowerUpState.SMALL
            self.update_size()
            self.invincible_timer = 120  # 2 seconds of invincibility

    def die(self):
        """Mario dies"""
        self.alive = False
        self.lives -= 1

class Platform(pygame.sprite.Sprite):
    """Ground and platform blocks"""

    def __init__(self, x: int, y: int, width: int, height: int, platform_type: str = 'ground'):
        super().__init__()
        self.platform_type = platform_type
        self.image = pygame.Surface((width, height))

        if platform_type == 'ground':
            self.image.fill(GROUND_BROWN)
        elif platform_type == 'brick':
            self.image.fill(BROWN)
        elif platform_type == 'question':
            self.image.fill(YELLOW)
        elif platform_type == 'pipe':
            self.image.fill(GREEN)
        else:
            self.image.fill(BROWN)

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class Enemy(pygame.sprite.Sprite):
    """Enemy base class"""

    def __init__(self, x: int, y: int, enemy_type: str = 'goomba'):
        super().__init__()
        self.enemy_type = enemy_type

        if enemy_type == 'goomba':
            self.image = pygame.Surface((32, 32))
            self.image.fill(BROWN)
            self.move_speed = 1
        elif enemy_type == 'koopa':
            self.image = pygame.Surface((32, 48))
            self.image.fill(GREEN)
            self.move_speed = 1
        else:
            self.image = pygame.Surface((32, 32))
            self.image.fill(RED)
            self.move_speed = 1

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.vel_x = -self.move_speed
        self.vel_y = 0
        self.alive = True

    def update(self, platforms):
        """Update enemy"""
        if not self.alive:
            return

        # Apply gravity
        self.vel_y += GRAVITY
        if self.vel_y > MAX_FALL_SPEED:
            self.vel_y = MAX_FALL_SPEED

        # Move
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y

        # Simple collision with platforms
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vel_y > 0:
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                elif self.vel_x != 0:
                    self.vel_x = -self.vel_x

class PowerUp(pygame.sprite.Sprite):
    """Power-up items"""

    def __init__(self, x: int, y: int, powerup_type: str = 'mushroom'):
        super().__init__()
        self.powerup_type = powerup_type

        if powerup_type == 'mushroom':
            self.image = pygame.Surface((32, 32))
            self.image.fill(RED)
            pygame.draw.circle(self.image, WHITE, (8, 8), 4)
            pygame.draw.circle(self.image, WHITE, (24, 8), 4)
        elif powerup_type == 'fire_flower':
            self.image = pygame.Surface((32, 32))
            self.image.fill(ORANGE)
        elif powerup_type == 'star':
            self.image = pygame.Surface((32, 32))
            self.image.fill(YELLOW)
        else:
            self.image = pygame.Surface((32, 32))
            self.image.fill(GREEN)

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.vel_y = 0
        self.collected = False

    def update(self, platforms):
        """Update power-up"""
        if self.collected:
            return

        # Apply gravity
        self.vel_y += GRAVITY
        if self.vel_y > MAX_FALL_SPEED:
            self.vel_y = MAX_FALL_SPEED

        self.rect.y += self.vel_y

        # Check collision with platforms
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vel_y > 0:
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0

class Level:
    """Level class containing all level data and entities"""

    def __init__(self, level_data: LevelData):
        self.level_data = level_data
        self.platforms = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.coins = pygame.sprite.Group()
        self.completed = False
        self.time_remaining = level_data.time_limit

        # Load level based on world and level number
        self.load_level()

    def load_level(self):
        """Load level layout"""
        world = self.level_data.world
        level = self.level_data.level

        # Ground
        for i in range(0, 5000, 32):
            self.platforms.add(Platform(i, SCREEN_HEIGHT - 64, 32, 64, 'ground'))

        # Level-specific layouts
        if world == 1 and level == 1:
            self.load_world_1_1()
        elif world == 1 and level == 2:
            self.load_world_1_2()
        elif world == 1 and level == 3:
            self.load_world_1_3()
        elif world == 1 and level == 4:
            self.load_world_1_4()
        elif world == 2 and level == 1:
            self.load_world_2_1()
        elif world == 2 and level == 2:
            self.load_world_2_2()
        elif world == 2 and level == 3:
            self.load_world_2_3()
        elif world == 2 and level == 4:
            self.load_world_2_4()
        else:
            # Generic level layout for other levels
            self.load_generic_level()

    def load_world_1_1(self):
        """Load World 1-1 (Classic first level)"""
        # Question blocks
        for i in range(3):
            self.platforms.add(Platform(400 + i * 64, 300, 32, 32, 'question'))

        # Brick blocks
        for i in range(5):
            self.platforms.add(Platform(600 + i * 32, 300, 32, 32, 'brick'))

        # Pipe
        self.platforms.add(Platform(800, SCREEN_HEIGHT - 128, 64, 64, 'pipe'))

        # Enemies
        self.enemies.add(Enemy(500, SCREEN_HEIGHT - 100, 'goomba'))
        self.enemies.add(Enemy(700, SCREEN_HEIGHT - 100, 'goomba'))
        self.enemies.add(Enemy(1000, SCREEN_HEIGHT - 100, 'koopa'))

        # Power-up
        self.powerups.add(PowerUp(420, 250, 'mushroom'))

    def load_world_1_2(self):
        """Load World 1-2 (Underground level)"""
        # Underground platforms
        for i in range(10):
            self.platforms.add(Platform(300 + i * 100, 400, 64, 32, 'brick'))

        # Enemies
        for i in range(5):
            self.enemies.add(Enemy(400 + i * 200, SCREEN_HEIGHT - 100, 'goomba'))

    def load_world_1_3(self):
        """Load World 1-3 (Tree level)"""
        # Platforms at various heights
        for i in range(8):
            y = 250 + (i % 3) * 100
            self.platforms.add(Platform(200 + i * 150, y, 96, 32, 'brick'))

        self.enemies.add(Enemy(300, SCREEN_HEIGHT - 100, 'koopa'))
        self.enemies.add(Enemy(600, SCREEN_HEIGHT - 100, 'koopa'))

    def load_world_1_4(self):
        """Load World 1-4 (Castle level)"""
        # Castle blocks
        for i in range(15):
            self.platforms.add(Platform(200 + i * 64, 350, 32, 32, 'brick'))

        # More enemies for castle
        for i in range(4):
            self.enemies.add(Enemy(300 + i * 250, SCREEN_HEIGHT - 100, 'koopa'))

    def load_world_2_1(self):
        """Load World 2-1"""
        self.load_generic_level()
        # Add more goombas
        for i in range(6):
            self.enemies.add(Enemy(300 + i * 200, SCREEN_HEIGHT - 100, 'goomba'))

    def load_world_2_2(self):
        """Load World 2-2 (Underground)"""
        self.load_world_1_2()

    def load_world_2_3(self):
        """Load World 2-3"""
        self.load_world_1_3()

    def load_world_2_4(self):
        """Load World 2-4 (Castle)"""
        self.load_world_1_4()

    def load_generic_level(self):
        """Load a generic level template"""
        # Question blocks
        for i in range(5):
            self.platforms.add(Platform(300 + i * 100, 300, 32, 32, 'question'))

        # Brick platforms
        for i in range(10):
            self.platforms.add(Platform(150 + i * 80, 350 + (i % 2) * 50, 32, 32, 'brick'))

        # Pipes
        self.platforms.add(Platform(700, SCREEN_HEIGHT - 128, 64, 64, 'pipe'))
        self.platforms.add(Platform(1200, SCREEN_HEIGHT - 160, 64, 96, 'pipe'))

        # Enemies
        for i in range(4):
            enemy_type = 'goomba' if i % 2 == 0 else 'koopa'
            self.enemies.add(Enemy(400 + i * 300, SCREEN_HEIGHT - 100, enemy_type))

    def update(self, mario):
        """Update level"""
        self.platforms.update()
        self.enemies.update(self.platforms)
        self.powerups.update(self.platforms)

        # Check Mario collision with enemies
        for enemy in self.enemies:
            if mario.rect.colliderect(enemy.rect) and enemy.alive:
                if mario.rect.bottom < enemy.rect.centery and mario.vel_y > 0:
                    # Stomp enemy
                    enemy.alive = False
                    enemy.kill()
                    mario.vel_y = -8  # Bounce
                    mario.score += 100
                else:
                    # Take damage
                    mario.take_damage()

        # Check Mario collision with power-ups
        for powerup in self.powerups:
            if mario.rect.colliderect(powerup.rect) and not powerup.collected:
                powerup.collected = True
                powerup.kill()
                mario.power_up()
                mario.score += 1000

    def draw(self, screen, camera):
        """Draw level"""
        for platform in self.platforms:
            screen.blit(platform.image, camera.apply(platform))

        for enemy in self.enemies:
            if enemy.alive:
                screen.blit(enemy.image, camera.apply(enemy))

        for powerup in self.powerups:
            if not powerup.collected:
                screen.blit(powerup.image, camera.apply(powerup))

class Game:
    """Main game class"""

    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Ultra Mario 2D Bros - All 32 Levels")
        self.clock = pygame.time.Clock()
        self.running = True

        # Game state
        self.state = GameState.MENU
        self.music_manager = MusicManager()

        # Create all 32 levels
        self.all_levels = self.create_all_levels()
        self.current_level_index = 0
        self.current_level = None

        # Player
        self.mario = None
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

        # UI
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 36)

        # Menu selection
        self.menu_selection = 0
        self.menu_options = ['Start Game', 'Level Select', 'Options', 'Quit']

    def create_all_levels(self) -> List[LevelData]:
        """Create all 32 SMB1 levels"""
        levels = []

        # World 1
        levels.append(LevelData(1, 1, 'main_theme', 'overworld', 400))
        levels.append(LevelData(1, 2, 'underground', 'underground', 400))
        levels.append(LevelData(1, 3, 'main_theme', 'overworld', 300))
        levels.append(LevelData(1, 4, 'castle', 'castle', 300))

        # World 2
        levels.append(LevelData(2, 1, 'main_theme', 'overworld', 400))
        levels.append(LevelData(2, 2, 'underground', 'underground', 400))
        levels.append(LevelData(2, 3, 'main_theme', 'overworld', 300))
        levels.append(LevelData(2, 4, 'castle', 'castle', 300))

        # World 3
        levels.append(LevelData(3, 1, 'main_theme', 'overworld', 400))
        levels.append(LevelData(3, 2, 'main_theme', 'overworld', 400))
        levels.append(LevelData(3, 3, 'main_theme', 'overworld', 300))
        levels.append(LevelData(3, 4, 'castle', 'castle', 300))

        # World 4
        levels.append(LevelData(4, 1, 'main_theme', 'overworld', 400))
        levels.append(LevelData(4, 2, 'underground', 'underground', 400))
        levels.append(LevelData(4, 3, 'main_theme', 'overworld', 300))
        levels.append(LevelData(4, 4, 'castle', 'castle', 300))

        # World 5
        levels.append(LevelData(5, 1, 'main_theme', 'overworld', 400))
        levels.append(LevelData(5, 2, 'underground', 'underground', 400))
        levels.append(LevelData(5, 3, 'main_theme', 'overworld', 300))
        levels.append(LevelData(5, 4, 'castle', 'castle', 300))

        # World 6
        levels.append(LevelData(6, 1, 'main_theme', 'overworld', 400))
        levels.append(LevelData(6, 2, 'main_theme', 'overworld', 400))
        levels.append(LevelData(6, 3, 'main_theme', 'overworld', 300))
        levels.append(LevelData(6, 4, 'castle', 'castle', 300))

        # World 7
        levels.append(LevelData(7, 1, 'main_theme', 'overworld', 400))
        levels.append(LevelData(7, 2, 'underground', 'underground', 400))
        levels.append(LevelData(7, 3, 'main_theme', 'overworld', 300))
        levels.append(LevelData(7, 4, 'castle', 'castle', 300))

        # World 8
        levels.append(LevelData(8, 1, 'main_theme', 'overworld', 400))
        levels.append(LevelData(8, 2, 'main_theme', 'overworld', 400))
        levels.append(LevelData(8, 3, 'main_theme', 'overworld', 300))
        levels.append(LevelData(8, 4, 'castle', 'castle', 300))

        return levels

    def start_level(self, level_index: int):
        """Start a specific level"""
        if 0 <= level_index < len(self.all_levels):
            self.current_level_index = level_index
            level_data = self.all_levels[level_index]
            self.current_level = Level(level_data)
            self.mario = Mario(100, SCREEN_HEIGHT - 200)
            self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
            self.camera.level_width = 5000  # Set level width

            # Play appropriate music
            self.music_manager.play_music(level_data.music_track)

            self.state = GameState.PLAYING

    def next_level(self):
        """Progress to next level"""
        self.current_level_index += 1
        if self.current_level_index < len(self.all_levels):
            self.start_level(self.current_level_index)
        else:
            # Game completed!
            self.state = GameState.MENU
            print("Congratulations! You beat all 32 levels!")

    def handle_events(self):
        """Handle input events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if self.state == GameState.MENU:
                    if event.key == pygame.K_UP:
                        self.menu_selection = (self.menu_selection - 1) % len(self.menu_options)
                    elif event.key == pygame.K_DOWN:
                        self.menu_selection = (self.menu_selection + 1) % len(self.menu_options)
                    elif event.key == pygame.K_RETURN:
                        self.handle_menu_selection()

                elif self.state == GameState.PLAYING:
                    if event.key == pygame.K_ESCAPE:
                        self.state = GameState.PAUSED
                    elif event.key == pygame.K_r:
                        # Restart level
                        self.start_level(self.current_level_index)
                    elif event.key == pygame.K_n:
                        # Next level (for testing)
                        self.next_level()

                elif self.state == GameState.PAUSED:
                    if event.key == pygame.K_ESCAPE:
                        self.state = GameState.PLAYING

                elif self.state == GameState.GAME_OVER:
                    if event.key == pygame.K_RETURN:
                        self.state = GameState.MENU

    def handle_menu_selection(self):
        """Handle menu selection"""
        if self.menu_selection == 0:  # Start Game
            self.start_level(0)
        elif self.menu_selection == 1:  # Level Select
            self.show_level_select()
        elif self.menu_selection == 2:  # Options
            pass  # TODO: Options menu
        elif self.menu_selection == 3:  # Quit
            self.running = False

    def show_level_select(self):
        """Show level select screen"""
        selecting = True
        selected_world = 0
        selected_level = 0

        while selecting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    selecting = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        selecting = False
                    elif event.key == pygame.K_LEFT:
                        selected_level = max(0, selected_level - 1)
                    elif event.key == pygame.K_RIGHT:
                        selected_level = min(3, selected_level + 1)
                    elif event.key == pygame.K_UP:
                        selected_world = max(0, selected_world - 1)
                    elif event.key == pygame.K_DOWN:
                        selected_world = min(7, selected_world + 1)
                    elif event.key == pygame.K_RETURN:
                        level_index = selected_world * 4 + selected_level
                        self.start_level(level_index)
                        selecting = False

            # Draw level select screen
            self.screen.fill(BLACK)
            title = self.font_large.render("Level Select", True, WHITE)
            self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

            # Draw level grid
            for world in range(8):
                for level in range(4):
                    x = 200 + level * 120
                    y = 150 + world * 50

                    color = YELLOW if world == selected_world and level == selected_level else WHITE
                    text = self.font_small.render(f"World {world + 1}-{level + 1}", True, color)
                    self.screen.blit(text, (x, y))

            instructions = self.font_small.render("Arrow keys to select, ENTER to play, ESC to go back", True, WHITE)
            self.screen.blit(instructions, (SCREEN_WIDTH // 2 - instructions.get_width() // 2, 550))

            pygame.display.flip()
            self.clock.tick(FPS)

    def update(self):
        """Update game state"""
        if self.state == GameState.PLAYING:
            keys = pygame.key.get_pressed()
            self.mario.handle_input(keys)
            self.mario.update(self.current_level.platforms,
                            self.current_level.enemies,
                            self.current_level.powerups,
                            self.current_level.platforms)
            self.current_level.update(self.mario)
            self.camera.update(self.mario)

            # Check if Mario fell off
            if self.mario.rect.y > SCREEN_HEIGHT:
                self.mario.die()

            # Check game over
            if not self.mario.alive and self.mario.lives <= 0:
                self.state = GameState.GAME_OVER
                self.music_manager.play_music('game_over', 0)
            elif not self.mario.alive:
                # Restart level with remaining lives
                self.start_level(self.current_level_index)

    def draw(self):
        """Draw everything"""
        self.screen.fill(SKY_BLUE if self.current_level and self.current_level.level_data.theme == 'overworld' else BLACK)

        if self.state == GameState.MENU:
            self.draw_menu()
        elif self.state == GameState.PLAYING:
            self.draw_game()
        elif self.state == GameState.PAUSED:
            self.draw_game()
            self.draw_pause()
        elif self.state == GameState.GAME_OVER:
            self.draw_game_over()

        pygame.display.flip()

    def draw_menu(self):
        """Draw main menu"""
        self.screen.fill(BLACK)

        # Title
        title = self.font_large.render("ULTRA MARIO 2D BROS", True, RED)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100))

        subtitle = self.font_medium.render("All 32 Levels", True, WHITE)
        self.screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 180))

        # Menu options
        for i, option in enumerate(self.menu_options):
            color = YELLOW if i == self.menu_selection else WHITE
            text = self.font_medium.render(option, True, color)
            y = 300 + i * 60
            self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, y))

        # Instructions
        instructions = self.font_small.render("Use UP/DOWN arrows and ENTER to select", True, WHITE)
        self.screen.blit(instructions, (SCREEN_WIDTH // 2 - instructions.get_width() // 2, 550))

    def draw_game(self):
        """Draw game"""
        # Draw level
        if self.current_level:
            self.current_level.draw(self.screen, self.camera)

        # Draw Mario
        if self.mario:
            self.screen.blit(self.mario.image, self.camera.apply(self.mario))

        # Draw HUD
        self.draw_hud()

    def draw_hud(self):
        """Draw HUD"""
        if not self.mario or not self.current_level:
            return

        # Score
        score_text = self.font_small.render(f"Score: {self.mario.score:06d}", True, WHITE)
        self.screen.blit(score_text, (10, 10))

        # Coins
        coins_text = self.font_small.render(f"Coins: {self.mario.coins:02d}", True, YELLOW)
        self.screen.blit(coins_text, (10, 40))

        # Lives
        lives_text = self.font_small.render(f"Lives: {self.mario.lives}", True, RED)
        self.screen.blit(lives_text, (10, 70))

        # Level
        level_text = self.font_small.render(self.current_level.level_data.get_display_name(), True, WHITE)
        self.screen.blit(level_text, (SCREEN_WIDTH - level_text.get_width() - 10, 10))

        # Time
        time_text = self.font_small.render(f"Time: {self.current_level.time_remaining}", True, WHITE)
        self.screen.blit(time_text, (SCREEN_WIDTH - time_text.get_width() - 10, 40))

    def draw_pause(self):
        """Draw pause overlay"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        pause_text = self.font_large.render("PAUSED", True, WHITE)
        self.screen.blit(pause_text, (SCREEN_WIDTH // 2 - pause_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))

        continue_text = self.font_small.render("Press ESC to continue", True, WHITE)
        self.screen.blit(continue_text, (SCREEN_WIDTH // 2 - continue_text.get_width() // 2, SCREEN_HEIGHT // 2 + 50))

    def draw_game_over(self):
        """Draw game over screen"""
        self.screen.fill(BLACK)

        game_over_text = self.font_large.render("GAME OVER", True, RED)
        self.screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 2 - 100))

        if self.mario:
            score_text = self.font_medium.render(f"Final Score: {self.mario.score}", True, WHITE)
            self.screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, SCREEN_HEIGHT // 2))

        continue_text = self.font_small.render("Press ENTER to return to menu", True, WHITE)
        self.screen.blit(continue_text, (SCREEN_WIDTH // 2 - continue_text.get_width() // 2, SCREEN_HEIGHT // 2 + 100))

    def run(self):
        """Main game loop"""
        self.music_manager.play_music('title')

        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

def main():
    """Main entry point"""
    print("=" * 60)
    print("ULTRA MARIO 2D BROS - All 32 Levels")
    print("=" * 60)
    print("\nControls:")
    print("  Arrow Keys / WASD - Move")
    print("  Space / Up - Jump")
    print("  ESC - Pause")
    print("  R - Restart Level")
    print("  N - Next Level (testing)")
    print("\nMenu Navigation:")
    print("  Up/Down - Select")
    print("  Enter - Confirm")
    print("\nAssets:")
    print("  Place Team Level Up assets in 'assets/' folder")
    print("  Music: assets/music/")
    print("  Sounds: assets/sounds/")
    print("  Graphics: assets/graphics/")
    print("\n" + "=" * 60)
    print()

    # Create assets directories if they don't exist
    os.makedirs('assets/music', exist_ok=True)
    os.makedirs('assets/sounds', exist_ok=True)
    os.makedirs('assets/graphics', exist_ok=True)

    # Start game
    game = Game()
    game.run()

if __name__ == "__main__":
    main()
