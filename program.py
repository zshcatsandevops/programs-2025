import os
import pygame
import sys
import random

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400
FPS = 60
GRAVITY = 0.6
PLAYER_SPEED = 4
JUMP_STRENGTH = -12
MAX_FALL_SPEED = 15

# Colors
SKY_BLUE = (107, 140, 255)
BROWN = (139, 69, 19)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
ORANGE = (255, 140, 0)
DARK_GREEN = (34, 139, 34)
BRICK_RED = (178, 34, 34)

# Game States
STATE_MENU = 0
STATE_PLAYING = 1
STATE_GAME_OVER = 2
STATE_LEVEL_COMPLETE = 3

class Mario(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.state = "small"  # small, big, fire
        self.width = 16
        self.height = 16
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.velocity_y = 0
        self.velocity_x = 0
        self.on_ground = False
        self.facing_right = True
        self.invincible = False
        self.invincible_timer = 0
        self.alive = True

    def update(self, platforms, enemies, blocks, powerups, game):
        if not self.alive:
            return

        # Handle invincibility
        if self.invincible:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.invincible = False

        # Horizontal movement
        keys = pygame.key.get_pressed()
        self.velocity_x = 0

        if keys[pygame.K_LEFT]:
            self.velocity_x = -PLAYER_SPEED
            self.facing_right = False
        if keys[pygame.K_RIGHT]:
            self.velocity_x = PLAYER_SPEED
            self.facing_right = True

        self.rect.x += self.velocity_x

        # Apply gravity
        self.velocity_y += GRAVITY
        if self.velocity_y > MAX_FALL_SPEED:
            self.velocity_y = MAX_FALL_SPEED
        self.rect.y += self.velocity_y

        # Check for collisions with platforms
        self.on_ground = False
        for platform in platforms:
            if pygame.sprite.collide_rect(self, platform):
                # Land on top of platform
                if self.velocity_y > 0 and self.rect.bottom <= platform.rect.bottom:
                    self.rect.bottom = platform.rect.top
                    self.velocity_y = 0
                    self.on_ground = True
                # Hit from below
                elif self.velocity_y < 0 and self.rect.top >= platform.rect.top:
                    self.rect.top = platform.rect.bottom
                    self.velocity_y = 0

        # Check collisions with blocks
        for block in blocks:
            if pygame.sprite.collide_rect(self, block):
                # Hit from below
                if self.velocity_y < 0 and self.rect.top >= block.rect.top:
                    self.rect.top = block.rect.bottom
                    self.velocity_y = 0
                    block.hit(game, self)
                # Land on top
                elif self.velocity_y > 0 and self.rect.bottom <= block.rect.bottom:
                    self.rect.bottom = block.rect.top
                    self.velocity_y = 0
                    self.on_ground = True

        # Check collisions with enemies
        if not self.invincible:
            for enemy in enemies:
                if pygame.sprite.collide_rect(self, enemy) and enemy.alive:
                    # Jump on enemy
                    if self.velocity_y > 0 and self.rect.bottom <= enemy.rect.centery:
                        enemy.stomp()
                        self.velocity_y = -8
                        game.score += 100
                    else:
                        # Get hurt
                        self.get_hurt(game)

        # Check collisions with powerups
        for powerup in powerups:
            if pygame.sprite.collide_rect(self, powerup):
                powerup.collect(self, game)

        # Death if fall off screen
        if self.rect.y > SCREEN_HEIGHT:
            self.alive = False
            game.lives -= 1

    def jump(self):
        if self.on_ground:
            self.velocity_y = JUMP_STRENGTH

    def get_hurt(self, game):
        if self.state == "small":
            self.alive = False
            game.lives -= 1
        else:
            self.state = "small"
            self.height = 16
            self.invincible = True
            self.invincible_timer = 120  # 2 seconds of invincibility

    def grow(self):
        if self.state == "small":
            self.state = "big"
            self.height = 32
            self.rect.y -= 16

    def get_fire_power(self):
        self.state = "fire"
        self.height = 32
        if self.height == 16:
            self.rect.y -= 16

    def draw(self, screen, camera_x):
        # Draw Mario with blinking effect when invincible
        if self.invincible and (self.invincible_timer // 5) % 2 == 0:
            return

        color = RED
        if self.state == "fire":
            color = WHITE

        draw_rect = pygame.Rect(self.rect.x - camera_x, self.rect.y, self.width, self.height)
        pygame.draw.rect(screen, color, draw_rect)

        # Draw eyes
        eye_color = BLACK
        if self.facing_right:
            pygame.draw.circle(screen, eye_color, (draw_rect.x + 10, draw_rect.y + 5), 2)
        else:
            pygame.draw.circle(screen, eye_color, (draw_rect.x + 6, draw_rect.y + 5), 2)

class Goomba(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.width = 16
        self.height = 16
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(BROWN)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.velocity_x = -1
        self.velocity_y = 0
        self.alive = True
        self.stomped = False
        self.stomp_timer = 0

    def update(self, platforms):
        if self.stomped:
            self.stomp_timer += 1
            if self.stomp_timer > 30:
                self.kill()
            return

        if not self.alive:
            return

        # Move
        self.rect.x += self.velocity_x

        # Apply gravity
        self.velocity_y += GRAVITY
        if self.velocity_y > MAX_FALL_SPEED:
            self.velocity_y = MAX_FALL_SPEED
        self.rect.y += self.velocity_y

        # Platform collisions
        for platform in platforms:
            if pygame.sprite.collide_rect(self, platform):
                if self.velocity_y > 0:
                    self.rect.bottom = platform.rect.top
                    self.velocity_y = 0

        # Turn around at edges or walls
        if self.rect.x < 0 or self.rect.x > 3000:
            self.velocity_x *= -1

    def stomp(self):
        self.stomped = True
        self.height = 8
        self.velocity_x = 0

    def draw(self, screen, camera_x):
        if not self.alive and not self.stomped:
            return

        draw_rect = pygame.Rect(self.rect.x - camera_x, self.rect.y, self.width, self.height)
        pygame.draw.rect(screen, BROWN, draw_rect)

        # Draw eyes if not stomped
        if not self.stomped:
            pygame.draw.circle(screen, WHITE, (draw_rect.x + 5, draw_rect.y + 5), 2)
            pygame.draw.circle(screen, WHITE, (draw_rect.x + 11, draw_rect.y + 5), 2)
            pygame.draw.circle(screen, BLACK, (draw_rect.x + 5, draw_rect.y + 5), 1)
            pygame.draw.circle(screen, BLACK, (draw_rect.x + 11, draw_rect.y + 5), 1)

class Koopa(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.width = 16
        self.height = 24
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.velocity_x = -1
        self.velocity_y = 0
        self.alive = True
        self.in_shell = False
        self.shell_timer = 0

    def update(self, platforms):
        if not self.alive:
            return

        # Shell behavior
        if self.in_shell:
            self.shell_timer += 1
            if self.shell_timer > 300:  # Come out of shell after 5 seconds
                self.in_shell = False
                self.height = 24
                self.shell_timer = 0
            return

        # Move
        self.rect.x += self.velocity_x

        # Apply gravity
        self.velocity_y += GRAVITY
        if self.velocity_y > MAX_FALL_SPEED:
            self.velocity_y = MAX_FALL_SPEED
        self.rect.y += self.velocity_y

        # Platform collisions
        for platform in platforms:
            if pygame.sprite.collide_rect(self, platform):
                if self.velocity_y > 0:
                    self.rect.bottom = platform.rect.top
                    self.velocity_y = 0

    def stomp(self):
        if not self.in_shell:
            self.in_shell = True
            self.height = 16
            self.velocity_x = 0
            self.shell_timer = 0

    def draw(self, screen, camera_x):
        if not self.alive:
            return

        color = GREEN if not self.in_shell else DARK_GREEN
        draw_rect = pygame.Rect(self.rect.x - camera_x, self.rect.y, self.width, self.height)
        pygame.draw.rect(screen, color, draw_rect)

        # Shell pattern
        if self.in_shell:
            pygame.draw.rect(screen, WHITE, (draw_rect.x + 2, draw_rect.y + 2, 12, 12), 2)

class QuestionBlock(pygame.sprite.Sprite):
    def __init__(self, x, y, contains="coin"):
        super().__init__()
        self.width = 16
        self.height = 16
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.contains = contains  # "coin", "mushroom", "fireflower"
        self.hit_count = 0
        self.bump_offset = 0

    def hit(self, game, player):
        if self.hit_count > 0:
            return

        self.hit_count += 1
        self.bump_offset = -10

        if self.contains == "coin":
            game.score += 100
            game.coins += 1
        elif self.contains == "mushroom":
            powerup = Mushroom(self.rect.x, self.rect.y - 16)
            game.powerups.add(powerup)
        elif self.contains == "fireflower":
            powerup = FireFlower(self.rect.x, self.rect.y - 16)
            game.powerups.add(powerup)

    def update(self):
        if self.bump_offset < 0:
            self.bump_offset += 1

    def draw(self, screen, camera_x):
        color = YELLOW if self.hit_count == 0 else BROWN
        draw_rect = pygame.Rect(self.rect.x - camera_x, self.rect.y + self.bump_offset,
                               self.width, self.height)
        pygame.draw.rect(screen, color, draw_rect)

        # Question mark
        if self.hit_count == 0:
            font = pygame.font.Font(None, 20)
            text = font.render("?", True, BLACK)
            screen.blit(text, (draw_rect.x + 4, draw_rect.y))

class BrickBlock(pygame.sprite.Sprite):
    def __init__(self, x, y, breakable=True):
        super().__init__()
        self.width = 16
        self.height = 16
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(BRICK_RED)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.breakable = breakable
        self.bump_offset = 0

    def hit(self, game, player):
        if self.breakable and player.state != "small":
            self.kill()
            game.score += 50
        else:
            self.bump_offset = -10

    def update(self):
        if self.bump_offset < 0:
            self.bump_offset += 1

    def draw(self, screen, camera_x):
        draw_rect = pygame.Rect(self.rect.x - camera_x, self.rect.y + self.bump_offset,
                               self.width, self.height)
        pygame.draw.rect(screen, BRICK_RED, draw_rect)
        # Brick pattern
        pygame.draw.line(screen, BLACK, (draw_rect.x, draw_rect.y + 8),
                        (draw_rect.x + 16, draw_rect.y + 8), 1)
        pygame.draw.line(screen, BLACK, (draw_rect.x + 8, draw_rect.y),
                        (draw_rect.x + 8, draw_rect.y + 8), 1)

class Pipe(pygame.sprite.Sprite):
    def __init__(self, x, y, height):
        super().__init__()
        self.width = 32
        self.height = height
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(DARK_GREEN)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def draw(self, screen, camera_x):
        draw_rect = pygame.Rect(self.rect.x - camera_x, self.rect.y, self.width, self.height)
        pygame.draw.rect(screen, DARK_GREEN, draw_rect)
        # Pipe rim
        rim_rect = pygame.Rect(self.rect.x - camera_x - 2, self.rect.y - 4,
                              self.width + 4, 8)
        pygame.draw.rect(screen, DARK_GREEN, rim_rect)
        pygame.draw.rect(screen, BLACK, rim_rect, 2)

class Mushroom(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.width = 16
        self.height = 16
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.velocity_x = 2
        self.velocity_y = 0
        self.collected = False

    def update(self, platforms):
        if self.collected:
            return

        self.rect.x += self.velocity_x

        # Apply gravity
        self.velocity_y += GRAVITY
        if self.velocity_y > MAX_FALL_SPEED:
            self.velocity_y = MAX_FALL_SPEED
        self.rect.y += self.velocity_y

        # Platform collisions
        for platform in platforms:
            if pygame.sprite.collide_rect(self, platform):
                if self.velocity_y > 0:
                    self.rect.bottom = platform.rect.top
                    self.velocity_y = 0

    def collect(self, player, game):
        if not self.collected:
            self.collected = True
            player.grow()
            game.score += 1000
            self.kill()

    def draw(self, screen, camera_x):
        if self.collected:
            return
        draw_rect = pygame.Rect(self.rect.x - camera_x, self.rect.y, self.width, self.height)
        pygame.draw.rect(screen, RED, draw_rect)
        pygame.draw.circle(screen, WHITE, (draw_rect.x + 4, draw_rect.y + 6), 2)
        pygame.draw.circle(screen, WHITE, (draw_rect.x + 12, draw_rect.y + 6), 2)

class FireFlower(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.width = 16
        self.height = 16
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(ORANGE)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.collected = False

    def update(self, platforms):
        pass

    def collect(self, player, game):
        if not self.collected:
            self.collected = True
            player.get_fire_power()
            game.score += 1000
            self.kill()

    def draw(self, screen, camera_x):
        if self.collected:
            return
        draw_rect = pygame.Rect(self.rect.x - camera_x, self.rect.y, self.width, self.height)
        pygame.draw.rect(screen, ORANGE, draw_rect)
        # Flower petals
        pygame.draw.circle(screen, RED, (draw_rect.x + 8, draw_rect.y + 4), 3)
        pygame.draw.circle(screen, YELLOW, (draw_rect.x + 8, draw_rect.y + 12), 3)

class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.width = 12
        self.height = 16
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.collected = False

    def update(self, player, game):
        if pygame.sprite.collide_rect(self, player) and not self.collected:
            self.collected = True
            game.score += 100
            game.coins += 1
            self.kill()

    def draw(self, screen, camera_x):
        if self.collected:
            return
        draw_rect = pygame.Rect(self.rect.x - camera_x, self.rect.y, self.width, self.height)
        pygame.draw.ellipse(screen, YELLOW, draw_rect)
        pygame.draw.ellipse(screen, ORANGE, draw_rect, 2)

class Flag(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.width = 16
        self.height = 160
        self.pole_x = x
        self.image = pygame.Surface((self.width, self.height))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def draw(self, screen, camera_x):
        # Pole
        pygame.draw.rect(screen, WHITE, (self.pole_x - camera_x, self.rect.y, 4, self.height))
        # Flag
        flag_points = [
            (self.pole_x - camera_x + 4, self.rect.y + 10),
            (self.pole_x - camera_x + 24, self.rect.y + 20),
            (self.pole_x - camera_x + 4, self.rect.y + 30)
        ]
        pygame.draw.polygon(screen, GREEN, flag_points)

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(BROWN)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Super Mario Bros")
        self.clock = pygame.time.Clock()
        self.state = STATE_MENU
        self.font = pygame.font.Font(None, 24)
        self.large_font = pygame.font.Font(None, 48)

        # Game variables
        self.score = 0
        self.coins = 0
        self.lives = 3
        self.time = 400
        self.timer_count = 0
        self.camera_x = 0
        self.level_width = 3400

        # Sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.blocks = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.coins_group = pygame.sprite.Group()

        # Create player
        self.player = None

        # Level complete flag
        self.flag = None

    def reset_level(self):
        """Reset the level"""
        self.all_sprites.empty()
        self.platforms.empty()
        self.enemies.empty()
        self.blocks.empty()
        self.powerups.empty()
        self.coins_group.empty()

        self.camera_x = 0
        self.time = 400
        self.timer_count = 0

        # Create player
        self.player = Mario(100, SCREEN_HEIGHT - 100)

        # Create level
        self.create_world_1_1()

    def create_world_1_1(self):
        """Create World 1-1 level layout"""
        # Ground
        for x in range(0, self.level_width, 16):
            ground = Platform(x, SCREEN_HEIGHT - 32, 16, 32)
            self.platforms.add(ground)

        # Starting area platforms
        for i in range(3):
            platform = Platform(200 + i * 16, 280, 16, 16)
            self.platforms.add(platform)

        # Question blocks and bricks
        question_blocks_positions = [
            (256, 200, "coin"),
            (272, 200, "mushroom"),
            (288, 200, "coin"),
            (352, 200, "coin"),
            (368, 200, "coin"),
            (512, 200, "coin"),
            (528, 136, "coin"),
            (672, 200, "fireflower"),
            (1056, 200, "coin"),
            (1488, 200, "mushroom"),
            (1504, 200, "coin"),
        ]

        for x, y, contains in question_blocks_positions:
            block = QuestionBlock(x, y, contains)
            self.blocks.add(block)

        # Brick blocks
        brick_positions = [
            (304, 200), (320, 200), (336, 200),
            (384, 200), (400, 200),
            (544, 136), (560, 136),
            (688, 200), (704, 200), (720, 200), (736, 200), (752, 200),
            (768, 200), (784, 200), (800, 200),
            (1200, 200), (1216, 200), (1232, 200),
            (1456, 136), (1472, 136),
            (1520, 200), (1536, 200),
        ]

        for x, y in brick_positions:
            block = BrickBlock(x, y)
            self.blocks.add(block)

        # Pipes
        pipes_data = [
            (448, SCREEN_HEIGHT - 64, 32),
            (608, SCREEN_HEIGHT - 80, 48),
            (736, SCREEN_HEIGHT - 96, 64),
            (912, SCREEN_HEIGHT - 96, 64),
            (1808, SCREEN_HEIGHT - 64, 32),
            (2400, SCREEN_HEIGHT - 64, 32),
        ]

        for x, y, height in pipes_data:
            pipe = Pipe(x, y, height)
            self.platforms.add(pipe)

        # Enemies - Goombas
        goomba_positions = [400, 550, 800, 950, 1100, 1300, 1500, 1700, 1900, 2100, 2300]
        for x in goomba_positions:
            goomba = Goomba(x, SCREEN_HEIGHT - 100)
            self.enemies.add(goomba)

        # Enemies - Koopas
        koopa_positions = [650, 1000, 1400, 1800, 2200]
        for x in koopa_positions:
            koopa = Koopa(x, SCREEN_HEIGHT - 100)
            self.enemies.add(koopa)

        # Coins in the air
        coin_positions = [
            (300, 150), (316, 150), (332, 150),
            (500, 180),
            (700, 160), (716, 160), (732, 160),
            (1100, 180), (1116, 180),
        ]

        for x, y in coin_positions:
            coin = Coin(x, y)
            self.coins_group.add(coin)

        # Stairs at the end
        for i in range(9):
            height = (i + 1) * 16
            platform = Platform(2800 + i * 16, SCREEN_HEIGHT - 32 - height, 16, height)
            self.platforms.add(platform)

        # Descending stairs
        for i in range(9):
            height = (9 - i) * 16
            platform = Platform(2944 + i * 16, SCREEN_HEIGHT - 32 - height, 16, height)
            self.platforms.add(platform)

        # Flag
        self.flag = Flag(3232, SCREEN_HEIGHT - 192)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False

                if self.state == STATE_MENU:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                        self.state = STATE_PLAYING
                        self.reset_level()

                elif self.state == STATE_PLAYING:
                    if event.key == pygame.K_SPACE:
                        self.player.jump()

                elif self.state == STATE_GAME_OVER:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                        self.state = STATE_MENU
                        self.score = 0
                        self.coins = 0
                        self.lives = 3

                elif self.state == STATE_LEVEL_COMPLETE:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                        self.state = STATE_MENU

        return True

    def update(self):
        if self.state != STATE_PLAYING:
            return

        # Update timer
        self.timer_count += 1
        if self.timer_count >= 60:  # 1 second
            self.timer_count = 0
            self.time -= 1
            if self.time <= 0:
                self.player.alive = False
                self.lives -= 1

        # Update player
        self.player.update(self.platforms, self.enemies, self.blocks, self.powerups, self)

        # Update enemies
        for enemy in self.enemies:
            enemy.update(self.platforms)

        # Update blocks
        for block in self.blocks:
            block.update()

        # Update powerups
        for powerup in self.powerups:
            powerup.update(self.platforms)

        # Update coins
        for coin in self.coins_group:
            coin.update(self.player, self)

        # Update camera to follow player
        target_camera_x = self.player.rect.x - SCREEN_WIDTH // 3
        if target_camera_x < 0:
            target_camera_x = 0
        if target_camera_x > self.level_width - SCREEN_WIDTH:
            target_camera_x = self.level_width - SCREEN_WIDTH
        self.camera_x = target_camera_x

        # Check if player reached flag
        if self.flag and self.player.rect.x >= self.flag.pole_x:
            self.state = STATE_LEVEL_COMPLETE
            self.score += self.time * 10  # Bonus for remaining time

        # Check game over
        if not self.player.alive:
            if self.lives <= 0:
                self.state = STATE_GAME_OVER
            else:
                self.reset_level()

    def draw_menu(self):
        self.screen.fill(BLACK)

        title = self.large_font.render("SUPER MARIO BROS", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)

        start_text = self.font.render("Press SPACE to Start", True, WHITE)
        start_rect = start_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(start_text, start_rect)

        controls_text = [
            "Controls:",
            "Arrow Keys - Move",
            "Space - Jump",
            "ESC - Quit"
        ]

        y_offset = 260
        for text in controls_text:
            rendered = self.font.render(text, True, WHITE)
            rect = rendered.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
            self.screen.blit(rendered, rect)
            y_offset += 30

    def draw_game_over(self):
        self.screen.fill(BLACK)

        game_over_text = self.large_font.render("GAME OVER", True, RED)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(game_over_text, game_over_rect)

        score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 220))
        self.screen.blit(score_text, score_rect)

        restart_text = self.font.render("Press SPACE to Return to Menu", True, WHITE)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, 280))
        self.screen.blit(restart_text, restart_rect)

    def draw_level_complete(self):
        self.screen.fill(BLACK)

        complete_text = self.large_font.render("LEVEL COMPLETE!", True, GREEN)
        complete_rect = complete_text.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(complete_text, complete_rect)

        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 220))
        self.screen.blit(score_text, score_rect)

        continue_text = self.font.render("Press SPACE to Return to Menu", True, WHITE)
        continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH // 2, 280))
        self.screen.blit(continue_text, continue_rect)

    def draw(self):
        if self.state == STATE_MENU:
            self.draw_menu()
        elif self.state == STATE_GAME_OVER:
            self.draw_game_over()
        elif self.state == STATE_LEVEL_COMPLETE:
            self.draw_level_complete()
        else:
            # Draw game
            self.screen.fill(SKY_BLUE)

            # Draw platforms
            for platform in self.platforms:
                if hasattr(platform, 'draw'):
                    platform.draw(self.screen, self.camera_x)
                else:
                    draw_rect = pygame.Rect(platform.rect.x - self.camera_x, platform.rect.y,
                                          platform.rect.width, platform.rect.height)
                    pygame.draw.rect(self.screen, BROWN, draw_rect)

            # Draw blocks
            for block in self.blocks:
                block.draw(self.screen, self.camera_x)

            # Draw coins
            for coin in self.coins_group:
                coin.draw(self.screen, self.camera_x)

            # Draw powerups
            for powerup in self.powerups:
                powerup.draw(self.screen, self.camera_x)

            # Draw enemies
            for enemy in self.enemies:
                enemy.draw(self.screen, self.camera_x)

            # Draw player
            if self.player:
                self.player.draw(self.screen, self.camera_x)

            # Draw flag
            if self.flag:
                self.flag.draw(self.screen, self.camera_x)

            # Draw HUD
            self.draw_hud()

        pygame.display.flip()

    def draw_hud(self):
        # Score
        score_text = self.font.render(f"SCORE: {self.score:06d}", True, WHITE)
        self.screen.blit(score_text, (10, 10))

        # Coins
        coins_text = self.font.render(f"COINS: {self.coins:02d}", True, WHITE)
        self.screen.blit(coins_text, (180, 10))

        # Lives
        lives_text = self.font.render(f"LIVES: {self.lives}", True, WHITE)
        self.screen.blit(lives_text, (340, 10))

        # Time
        time_text = self.font.render(f"TIME: {self.time:03d}", True, WHITE)
        self.screen.blit(time_text, (470, 10))

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
