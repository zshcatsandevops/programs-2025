import pygame
import sys
import math
import random

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 600, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Goomba Adventure")

# Colors
BACKGROUND = (30, 30, 60)
GROUND = (80, 60, 40)
PATH = (120, 90, 60)
TREE_TRUNK = (90, 60, 30)
TREE_TOP = (30, 90, 40)
HOUSE_COLOR = (180, 120, 80)
ROOF_COLOR = (150, 60, 40)
GOOMBA_BROWN = (160, 120, 80)
GOOMBA_DARK = (120, 90, 60)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 60, 60)
YELLOW = (255, 220, 60)
BLUE = (80, 120, 220)

# Game clock
clock = pygame.time.Clock()
FPS = 60

# Player (Goomba) properties
player_x = WIDTH // 2
player_y = HEIGHT // 2
player_speed = 2
player_size = 30
animation_counter = 0
facing_right = True

# NPC properties
npcs = [
    {"x": 150, "y": 200, "color": RED, "name": "Luigi", "dialog": "It's-a me, Luigi! Help me find my brother!", "visible": True},
    {"x": 450, "y": 150, "color": YELLOW, "name": "Toad", "dialog": "The princess is in another castle!", "visible": True},
    {"x": 350, "y": 300, "color": BLUE, "name": "Sans", "dialog": "heh. you're a goomba now. how's that feel?", "visible": True}
]

# Game state
game_state = "exploring"  # "exploring", "dialog"
current_npc = None
dialog_timer = 0

# Font
font = pygame.font.SysFont("Arial", 16)
dialog_font = pygame.font.SysFont("Arial", 14)

def draw_background():
    # Draw sky
    screen.fill(BACKGROUND)
    
    # Draw ground
    pygame.draw.rect(screen, GROUND, (0, HEIGHT - 100, WIDTH, 100))
    
    # Draw path
    pygame.draw.rect(screen, PATH, (WIDTH // 2 - 50, HEIGHT - 100, 100, 100))
    
    # Draw trees
    for x, y in [(100, 150), (500, 120), (200, 80)]:
        pygame.draw.rect(screen, TREE_TRUNK, (x, y, 20, 60))
        pygame.draw.circle(screen, TREE_TOP, (x + 10, y - 20), 40)
    
    # Draw houses
    pygame.draw.rect(screen, HOUSE_COLOR, (50, HEIGHT - 180, 80, 80))
    pygame.draw.polygon(screen, ROOF_COLOR, [(30, HEIGHT - 180), (150, HEIGHT - 180), (90, HEIGHT - 220)])
    
    pygame.draw.rect(screen, HOUSE_COLOR, (470, HEIGHT - 160, 80, 60))
    pygame.draw.polygon(screen, ROOF_COLOR, [(450, HEIGHT - 160), (550, HEIGHT - 160), (500, HEIGHT - 200)])

def draw_goomba(x, y, frame, facing_right):
    # Body
    pygame.draw.circle(screen, GOOMBA_BROWN, (x, y), player_size // 2)
    
    # Eyes
    eye_offset = 5 if facing_right else -5
    pygame.draw.circle(screen, BLACK, (x + eye_offset, y - 5), 4)
    
    # Mouth
    mouth_y = y + 5
    if frame < 15:
        pygame.draw.arc(screen, BLACK, (x - 8, mouth_y - 3, 16, 8), 0, math.pi, 2)
    else:
        pygame.draw.arc(screen, BLACK, (x - 8, mouth_y, 16, 6), math.pi, 2 * math.pi, 2)
    
    # Feet - animate based on frame
    foot_offset = 3 if frame < 15 else -3
    pygame.draw.ellipse(screen, GOOMBA_DARK, (x - 12, y + 10, 8, 4))
    pygame.draw.ellipse(screen, GOOMBA_DARK, (x + 4 + foot_offset, y + 10, 8, 4))

def draw_npcs():
    for npc in npcs:
        if npc["visible"]:
            # Draw NPC body
            pygame.draw.circle(screen, npc["color"], (npc["x"], npc["y"]), 20)
            
            # Draw NPC face
            pygame.draw.circle(screen, WHITE, (npc["x"] - 5, npc["y"] - 3), 4)
            pygame.draw.circle(screen, WHITE, (npc["x"] + 5, npc["y"] - 3), 4)
            pygame.draw.circle(screen, BLACK, (npc["x"] - 5, npc["y"] - 3), 2)
            pygame.draw.circle(screen, BLACK, (npc["x"] + 5, npc["y"] - 3), 2)
            
            # Draw NPC name
            name_text = font.render(npc["name"], True, WHITE)
            screen.blit(name_text, (npc["x"] - name_text.get_width() // 2, npc["y"] - 35))

def draw_dialog_box(npc):
    # Draw dialog box
    pygame.draw.rect(screen, (50, 50, 80), (50, HEIGHT - 100, WIDTH - 100, 80))
    pygame.draw.rect(screen, WHITE, (50, HEIGHT - 100, WIDTH - 100, 80), 2)
    
    # Draw NPC name
    name_text = font.render(npc["name"], True, YELLOW)
    screen.blit(name_text, (70, HEIGHT - 90))
    
    # Draw dialog text
    dialog_text = dialog_font.render(npc["dialog"], True, WHITE)
    screen.blit(dialog_text, (70, HEIGHT - 60))
    
    # Draw prompt to continue
    prompt_text = dialog_font.render("Press SPACE to continue...", True, (200, 200, 200))
    screen.blit(prompt_text, (WIDTH - 200, HEIGHT - 30))

def check_npc_collision():
    global game_state, current_npc
    for npc in npcs:
        if npc["visible"]:
            distance = math.sqrt((player_x - npc["x"])**2 + (player_y - npc["y"])**2)
            if distance < player_size + 20:
                game_state = "dialog"
                current_npc = npc
                return

# Main game loop
running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and game_state == "dialog":
                game_state = "exploring"
                dialog_timer = 0
    
    # Get pressed keys for continuous movement
    keys = pygame.key.get_pressed()
    
    if game_state == "exploring":
        # Move player with arrow keys
        if keys[pygame.K_LEFT]:
            player_x -= player_speed
            facing_right = False
        if keys[pygame.K_RIGHT]:
            player_x += player_speed
            facing_right = True
        if keys[pygame.K_UP]:
            player_y -= player_speed
        if keys[pygame.K_DOWN]:
            player_y += player_speed
        
        # Keep player within screen bounds
        player_x = max(player_size // 2, min(WIDTH - player_size // 2, player_x))
        player_y = max(player_size // 2, min(HEIGHT - player_size // 2, player_y))
        
        # Update animation
        animation_counter = (animation_counter + 1) % 30
        
        # Check for NPC collisions
        check_npc_collision()
    
    # Draw everything
    draw_background()
    draw_npcs()
    draw_goomba(player_x, player_y, animation_counter, facing_right)
    
    # Draw UI
    pygame.draw.rect(screen, (40, 40, 70), (0, 0, WIDTH, 30))
    title_text = font.render("Goomba Adventure - Use arrow keys to move, talk to NPCs", True, WHITE)
    screen.blit(title_text, (10, 10))
    
    # Draw dialog if in dialog state
    if game_state == "dialog" and current_npc:
        draw_dialog_box(current_npc)
    
    # Update display
    pygame.display.flip()
    
    # Control game speed
    clock.tick(FPS)

pygame.quit()
sys.exit()
