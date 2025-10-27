import pygame
import sys
import math

# --- Constants ---
WIDTH, HEIGHT = 600, 400
FPS = 60

# Colors
SKY_BLUE = (135, 206, 235)
GRASS_GREEN = (34, 139, 34)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 0, 0)
BROWN = (139, 69, 19)
DARK_BROWN = (85, 45, 13)
BIRD_BLUE = (60, 60, 200)
SCARF_BLUE = (0, 0, 139)
BIRD_ORANGE = (255, 165, 0)
WHEEL_GRAY = (50, 50, 50)
UI_BAR_BG = (100, 100, 100)
UI_BAR_FILL = (50, 150, 255)

# --- Helper Function to draw pixel-style clouds ---
def draw_pixel_cloud(surface, x, y):
    """Draws a simple, blocky cloud."""
    pygame.draw.rect(surface, WHITE, (x, y, 25, 10))
    pygame.draw.rect(surface, WHITE, (x + 10, y - 10, 35, 10))
    pygame.draw.rect(surface, WHITE, (x + 25, y, 30, 10))

# --- Main Game Function ---
def main():
    pygame.init()

    # --- Setup Display ---
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Pygame: Melee Bicycle Mayhem")
    clock = pygame.time.Clock()

    # --- Fonts ---
    # We use the default pygame font as we can't load external files
    try:
        pixel_font_large = pygame.font.Font(None, 32)
        pixel_font_small = pygame.font.Font(None, 24)
    except Exception as e:
        print(f"Error loading font: {e}. Quitting.")
        pygame.quit()
        sys.exit()

    # --- Game State Variables ---
    cloud1_x = 100.0
    cloud2_x = 450.0
    wheel_angle = 0.0  # Angle in radians for wheel spokes

    running = True
    while running:
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # --- Game Logic / State Update ---
        # Animate clouds
        cloud1_x -= 0.8
        if cloud1_x < -100:
            cloud1_x = WIDTH + 20

        cloud2_x -= 0.5
        if cloud2_x < -100:
            cloud2_x = WIDTH + 20
        
        # Animate wheel spokes
        wheel_angle += 0.05
        if wheel_angle > 2 * math.pi:
            wheel_angle -= 2 * math.pi

        # --- Drawing ---
        
        # 1. Background
        screen.fill(SKY_BLUE)
        pygame.draw.rect(screen, GRASS_GREEN, (0, HEIGHT - 80, WIDTH, 80))

        # 2. Clouds (animated)
        draw_pixel_cloud(screen, int(cloud1_x), 50)
        draw_pixel_cloud(screen, int(cloud2_x), 100)

        # 3. Bicycle & Bird (Drawn with primitive shapes)
        # We'll center the character
        base_x = WIDTH // 2 - 50
        base_y = HEIGHT - 100
        wheel_radius = 30

        # Wheels
        wheel1_pos = (base_x, base_y)
        wheel2_pos = (base_x + 100, base_y)
        pygame.draw.circle(screen, WHEEL_GRAY, wheel1_pos, wheel_radius, 4)
        pygame.draw.circle(screen, WHEEL_GRAY, wheel2_pos, wheel_radius, 4)

        # Draw animated spokes
        for i in range(4): # 4 spokes per wheel
            angle = wheel_angle + (i * math.pi / 2)
            # Spoke for wheel 1
            spoke1_end = (wheel1_pos[0] + (wheel_radius - 2) * math.cos(angle), 
                           wheel1_pos[1] + (wheel_radius - 2) * math.sin(angle))
            pygame.draw.line(screen, WHEEL_GRAY, wheel1_pos, spoke1_end, 2)
            # Spoke for wheel 2
            spoke2_end = (wheel2_pos[0] + (wheel_radius - 2) * math.cos(angle), 
                           wheel2_pos[1] + (wheel_radius - 2) * math.sin(angle))
            pygame.draw.line(screen, WHEEL_GRAY, wheel2_pos, spoke2_end, 2)

        # Bike Frame (Red)
        seat_post_top = (base_x + 35, base_y - 50)
        handle_post_top = (base_x + 85, base_y - 60)
        crank_center = (base_x + 35, base_y - 5) # A bit above the wheel
        pygame.draw.line(screen, RED, wheel1_pos, seat_post_top, 4)
        pygame.draw.line(screen, RED, crank_center, seat_post_top, 4)
        pygame.draw.line(screen, RED, crank_center, handle_post_top, 4)
        pygame.draw.line(screen, RED, seat_post_top, handle_post_top, 4)
        pygame.draw.line(screen, RED, handle_post_top, wheel2_pos, 4)

        # Handlebars & Basket
        handlebar_pos = (base_x + 90, base_y - 70)
        pygame.draw.line(screen, WHEEL_GRAY, handle_post_top, handlebar_pos, 4)
        pygame.draw.line(screen, WHEEL_GRAY, handlebar_pos, (handlebar_pos[0] + 10, handlebar_pos[1] - 5), 6)
        pygame.draw.rect(screen, BROWN, (base_x + 95, base_y - 90, 30, 20), 0, 3)

        # Seat
        pygame.draw.rect(screen, DARK_BROWN, (base_x + 25, base_y - 60, 20, 10), 0, 2)

        # Bird
        bird_body_pos = (base_x + 45, base_y - 80)
        pygame.draw.ellipse(screen, BIRD_BLUE, (bird_body_pos[0] - 15, bird_body_pos[1] - 15, 30, 45))
        bird_head_pos = (bird_body_pos[0] + 5, bird_body_pos[1] - 25)
        pygame.draw.circle(screen, BIRD_BLUE, bird_head_pos, 18)

        # Bird Face
        beak_points = [(bird_head_pos[0] + 15, bird_head_pos[1] - 5),
                       (bird_head_pos[0] + 35, bird_head_pos[1]),
                       (bird_head_pos[0] + 15, bird_head_pos[1] + 5)]
        pygame.draw.polygon(screen, BIRD_ORANGE, beak_points)
        pygame.draw.circle(screen, WHITE, (bird_head_pos[0] + 10, bird_head_pos[1] - 5), 5)
        pygame.draw.circle(screen, BLACK, (bird_head_pos[0] + 11, bird_head_pos[1] - 5), 3)

        # Goggles
        pygame.draw.rect(screen, BROWN, (bird_head_pos[0] - 10, bird_head_pos[1] - 15, 25, 10), 2, 2)
        
        # Scarf
        scarf_points = [(bird_body_pos[0] - 5, bird_body_pos[1] - 10),
                        (bird_body_pos[0] - 20, bird_body_pos[1] - 5),
                        (bird_body_pos[0] - 15, bird_body_pos[1] + 10)]
        pygame.draw.polygon(screen, SCARF_BLUE, scarf_points)


        # 4. UI Text ("Falco: 67%")
        falco_text_str = "Falco: 67%"
        falco_surf = pixel_font_large.render(falco_text_str, True, BLACK)
        falco_rect = falco_surf.get_rect(center=(WIDTH // 2, 80))
        
        # Text Background (semi-transparent)
        text_bg_rect = falco_rect.inflate(10, 6)
        text_bg_surf = pygame.Surface(text_bg_rect.size, pygame.SRCALPHA)
        text_bg_surf.fill((255, 255, 255, 200)) # White with 200/255 alpha
        screen.blit(text_bg_surf, text_bg_rect)
        screen.blit(falco_surf, falco_rect) # Draw text on top

        # 5. Bottom UI Bar
        bar_rect_bg = (10, HEIGHT - 45, WIDTH - 20, 10)
        bar_rect_fg = (bar_rect_bg[0], bar_rect_bg[1], bar_rect_bg[2] * 0.8, bar_rect_bg[3])
        pygame.draw.rect(screen, UI_BAR_BG, bar_rect_bg, 0, 4)
        pygame.draw.rect(screen, UI_BAR_FILL, bar_rect_fg, 0, 4)

        # 6. Bottom UI Text
        fps_str = f"FPS: {int(clock.get_fps())}"
        fps_surf = pixel_font_small.render(fps_str, True, BLACK)
        screen.blit(fps_surf, (15, HEIGHT - 30))
        
        score_str = "Score: 1250 points"
        score_surf = pixel_font_small.render(score_str, True, BLACK)
        score_rect = score_surf.get_rect(topright=(WIDTH - 15, HEIGHT - 30))
        screen.blit(score_surf, score_rect)

        # --- Update Display ---
        pygame.display.flip()
        clock.tick(FPS)

    # --- Quit ---
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
