import os
import pygame
import tkinter

# Initialize Pygame
pygame.init()

# Window dimensions
WIDTH = 600
HEIGHT = 400

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Game settings
FPS = 60
PADDLE_WIDTH = 10
PADDLE_HEIGHT = 80
BALL_SIZE = 10
PADDLE_SPEED = 5
BALL_SPEED_X = 4
BALL_SPEED_Y = 4

# Create window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pong")
clock = pygame.time.Clock()

# Paddle class
class Paddle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = PADDLE_WIDTH
        self.height = PADDLE_HEIGHT
        self.speed = PADDLE_SPEED
        self.rect = pygame.Rect(x, y, self.width, self.height)

    def move(self, up=True):
        if up:
            self.y -= self.speed
        else:
            self.y += self.speed

        # Keep paddle within screen bounds
        if self.y < 0:
            self.y = 0
        if self.y > HEIGHT - self.height:
            self.y = HEIGHT - self.height

        self.rect.y = self.y

    def draw(self, screen):
        pygame.draw.rect(screen, WHITE, self.rect)

# Ball class
class Ball:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.size = BALL_SIZE
        self.speed_x = BALL_SPEED_X
        self.speed_y = BALL_SPEED_Y
        self.rect = pygame.Rect(self.x, self.y, self.size, self.size)

    def move(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.rect.x = self.x
        self.rect.y = self.y

        # Bounce off top and bottom
        if self.y <= 0 or self.y >= HEIGHT - self.size:
            self.speed_y *= -1

    def reset(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.speed_x *= -1
        self.rect.x = self.x
        self.rect.y = self.y

    def draw(self, screen):
        pygame.draw.rect(screen, WHITE, self.rect)

# Initialize game objects
paddle1 = Paddle(20, HEIGHT // 2 - PADDLE_HEIGHT // 2)
paddle2 = Paddle(WIDTH - 30, HEIGHT // 2 - PADDLE_HEIGHT // 2)
ball = Ball()

# Scores
score1 = 0
score2 = 0
font = pygame.font.Font(None, 50)

# Game loop
running = True
while running:
    clock.tick(FPS)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Get keys
    keys = pygame.key.get_pressed()

    # Player 1 controls (W/S)
    if keys[pygame.K_w]:
        paddle1.move(up=True)
    if keys[pygame.K_s]:
        paddle1.move(up=False)

    # Player 2 controls (UP/DOWN)
    if keys[pygame.K_UP]:
        paddle2.move(up=True)
    if keys[pygame.K_DOWN]:
        paddle2.move(up=False)

    # Move ball
    ball.move()

    # Ball collision with paddles
    if ball.rect.colliderect(paddle1.rect) or ball.rect.colliderect(paddle2.rect):
        ball.speed_x *= -1

    # Score points
    if ball.x <= 0:
        score2 += 1
        ball.reset()
    if ball.x >= WIDTH:
        score1 += 1
        ball.reset()

    # Draw everything
    screen.fill(BLACK)

    # Draw center line
    for i in range(0, HEIGHT, 20):
        pygame.draw.rect(screen, WHITE, (WIDTH // 2 - 2, i, 4, 10))

    # Draw paddles and ball
    paddle1.draw(screen)
    paddle2.draw(screen)
    ball.draw(screen)

    # Draw scores
    score1_text = font.render(str(score1), True, WHITE)
    score2_text = font.render(str(score2), True, WHITE)
    screen.blit(score1_text, (WIDTH // 4, 20))
    screen.blit(score2_text, (WIDTH * 3 // 4, 20))

    pygame.display.flip()

pygame.quit()
