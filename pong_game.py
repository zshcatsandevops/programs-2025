#!/usr/bin/env python3
"""
Pong Game - Pygame Implementation
Left Paddle: Mouse Controlled
Right Paddle: AI Controlled
First to 5 wins!
"""

import pygame
import sys
import random

# Initialize Pygame
pygame.init()

# Constants
WIDTH = 600
HEIGHT = 400
PADDLE_WIDTH = 10
PADDLE_HEIGHT = 80
BALL_SIZE = 10
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)

# Paddle speed
AI_SPEED = 4


class Paddle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = PADDLE_WIDTH
        self.height = PADDLE_HEIGHT
        self.rect = pygame.Rect(x, y, self.width, self.height)

    def draw(self, screen):
        pygame.draw.rect(screen, WHITE, self.rect)

    def move_to(self, y):
        """Move paddle to specific y position (for mouse control)"""
        self.y = max(0, min(y - self.height // 2, HEIGHT - self.height))
        self.rect.y = self.y

    def move_ai(self, ball_y):
        """AI movement - follow the ball"""
        paddle_center = self.y + self.height // 2
        if paddle_center < ball_y - 10:
            self.y = min(self.y + AI_SPEED, HEIGHT - self.height)
        elif paddle_center > ball_y + 10:
            self.y = max(self.y - AI_SPEED, 0)
        self.rect.y = self.y


class Ball:
    def __init__(self):
        self.reset()

    def reset(self):
        """Reset ball to center with random direction"""
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        angle = random.choice([-1, 1])
        self.dx = 5 * angle
        self.dy = random.randint(-3, 3)
        self.rect = pygame.Rect(self.x, self.y, BALL_SIZE, BALL_SIZE)

    def move(self):
        self.x += self.dx
        self.y += self.dy

        # Bounce off top and bottom
        if self.y <= 0 or self.y >= HEIGHT - BALL_SIZE:
            self.dy = -self.dy
            self.y = max(0, min(self.y, HEIGHT - BALL_SIZE))

        self.rect.x = self.x
        self.rect.y = self.y

    def draw(self, screen):
        pygame.draw.rect(screen, WHITE, self.rect)

    def check_collision(self, left_paddle, right_paddle):
        """Check collision with paddles"""
        if self.rect.colliderect(left_paddle.rect):
            if self.dx < 0:  # Only bounce if moving towards paddle
                self.dx = -self.dx
                self.x = left_paddle.x + left_paddle.width
                # Add some variation based on where it hits the paddle
                offset = (self.y - left_paddle.y - left_paddle.height // 2) / (left_paddle.height // 2)
                self.dy += offset * 2

        if self.rect.colliderect(right_paddle.rect):
            if self.dx > 0:  # Only bounce if moving towards paddle
                self.dx = -self.dx
                self.x = right_paddle.x - BALL_SIZE
                # Add some variation based on where it hits the paddle
                offset = (self.y - right_paddle.y - right_paddle.height // 2) / (right_paddle.height // 2)
                self.dy += offset * 2


def draw_text(screen, text, size, x, y, color=WHITE):
    """Draw text on screen"""
    font = pygame.font.Font(None, size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.center = (x, y)
    screen.blit(text_surface, text_rect)


def game_over_screen(screen, winner):
    """Display game over screen with y/n prompt"""
    while True:
        screen.fill(BLACK)

        if winner == "player":
            draw_text(screen, "YOU WIN!", 74, WIDTH // 2, HEIGHT // 2 - 60)
        else:
            draw_text(screen, "AI WINS!", 74, WIDTH // 2, HEIGHT // 2 - 60)

        draw_text(screen, "GAME OVER", 50, WIDTH // 2, HEIGHT // 2)
        draw_text(screen, "Press Y to continue or N to restart", 30, WIDTH // 2, HEIGHT // 2 + 60)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_y:
                    # Show "You Win" message and exit
                    screen.fill(BLACK)
                    draw_text(screen, "Thanks for playing!", 50, WIDTH // 2, HEIGHT // 2)
                    pygame.display.flip()
                    pygame.time.wait(2000)
                    pygame.quit()
                    sys.exit()
                elif event.key == pygame.K_n:
                    # Restart game
                    return True

        pygame.time.Clock().tick(FPS)


def main():
    """Main game loop"""
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Pong - Mouse vs AI")
    clock = pygame.time.Clock()

    # Hide mouse cursor and track position
    pygame.mouse.set_visible(True)

    while True:
        # Initialize game objects
        left_paddle = Paddle(30, HEIGHT // 2 - PADDLE_HEIGHT // 2)
        right_paddle = Paddle(WIDTH - 30 - PADDLE_WIDTH, HEIGHT // 2 - PADDLE_HEIGHT // 2)
        ball = Ball()

        player_score = 0
        ai_score = 0

        # Game loop
        running = True
        while running:
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            # Get mouse position for left paddle
            mouse_y = pygame.mouse.get_pos()[1]
            left_paddle.move_to(mouse_y)

            # AI movement for right paddle
            right_paddle.move_ai(ball.y)

            # Move ball
            ball.move()

            # Check paddle collisions
            ball.check_collision(left_paddle, right_paddle)

            # Check scoring
            if ball.x <= 0:
                # AI scores
                ai_score += 1
                ball.reset()
            elif ball.x >= WIDTH - BALL_SIZE:
                # Player scores
                player_score += 1
                ball.reset()

            # Check for game over (first to 5)
            if player_score >= 5:
                if game_over_screen(screen, "player"):
                    break  # Restart
                else:
                    return
            elif ai_score >= 5:
                if game_over_screen(screen, "ai"):
                    break  # Restart
                else:
                    return

            # Drawing
            screen.fill(BLACK)

            # Draw center line
            for i in range(0, HEIGHT, 20):
                pygame.draw.rect(screen, GRAY, (WIDTH // 2 - 2, i, 4, 10))

            # Draw paddles and ball
            left_paddle.draw(screen)
            right_paddle.draw(screen)
            ball.draw(screen)

            # Draw scores
            draw_text(screen, str(player_score), 48, WIDTH // 4, 30)
            draw_text(screen, str(ai_score), 48, 3 * WIDTH // 4, 30)

            # Draw labels
            draw_text(screen, "MOUSE", 20, WIDTH // 4, 70)
            draw_text(screen, "AI", 20, 3 * WIDTH // 4, 70)

            pygame.display.flip()
            clock.tick(FPS)


if __name__ == "__main__":
    main()
