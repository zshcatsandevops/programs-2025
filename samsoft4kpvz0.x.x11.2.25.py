#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ULTRA!PVZ — Full Intro Chain + Game Foundation with Levels
Procedural text animation, main menu with level selection, and multi-level game loop.
© Samsoft 2025 (Modified for levels and gameplay)
"""

import pygame, math, sys, random
pygame.init()
pygame.font.init()  # Initialize the font module explicitly

# --- Constants ---
W, H = 800, 600
GRID_ROWS = 5
GRID_COLS = 9
CELL_SIZE = 80  # Approximate size, we'll calculate positions
TOP_BAR_HEIGHT = 100
GRID_START_X = 50
GRID_START_Y = TOP_BAR_HEIGHT + 20

# --- Colors ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GOLD = (255, 215, 0)
RED = (255, 80, 80)
BLUE = (80, 160, 255)
LAWN_GREEN = (34, 139, 34)
DARK_GREEN = (20, 80, 20)
GREEN_BLUE = (34, 100, 100)
GRAY_GREEN = (50, 100, 50)
BROWN_GREEN = (60, 100, 40)
SOIL_BROWN = (139, 69, 19)
TOP_BAR_GREY = (100, 100, 100)
PEASHOOTER_GREEN = (0, 200, 0)
SUNFLOWER_YELLOW = (255, 200, 0)
ZOMBIE_GREY = (150, 150, 150)
SUN_YELLOW = (255, 255, 0)
SEED_PACKET_GREY = (50, 50, 50)
SEED_PACKET_SELECTED = (0, 255, 255)

# --- Setup ---
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("ULTRA!PVZ")
clock = pygame.time.Clock()
def _init_game_font():
    """Initialize and return a font object, with fallbacks."""
    try:
        return pygame.font.SysFont("arial", 24, bold=True)
    except Exception as e:
        print(f"Warning: Arial not found ({e}). Using default font.")
        try:
            return pygame.font.SysFont(None, 30, bold=True)
        except Exception as e2:
            print(f"Warning: Default font failed ({e2}). Using Font constructor.")
            return pygame.font.Font(None, 30)

GAME_FONT = _init_game_font()

# --- Intro Functions (from original) ---

def fade_text(text, font, color, dur=1200):
    start = pygame.time.get_ticks()
    if not font:
        print(f"Error: Font for '{text}' is not loaded.")
        return
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(W // 2, H // 2))
    
    while pygame.time.get_ticks() - start < dur:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        t = (pygame.time.get_ticks() - start) / dur
        alpha = int(255 * math.sin(t * math.pi))
        
        screen.fill(BLACK)
        surf.set_alpha(alpha)
        screen.blit(surf, rect)
        pygame.display.flip()
        clock.tick(60)

def ea_swirl(dur=2000):
    start = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start < dur:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        t = (pygame.time.get_ticks() - start) / dur
        
        bg_col = (int(40 + 215 * t), int(40 + 215 * (1 - t)), int(120 + 80 * math.sin(t * 6)))
        screen.fill(bg_col)
        
        for i in range(60):
            ang = i / 60 * math.tau + t * 6 * math.pi
            r = 200 * (1 - t)
            x = W // 2 + math.cos(ang) * r
            y = H // 2 + math.sin(ang) * r
            size = max(1, int(6 * (1 - t)))
            pygame.draw.circle(screen, WHITE, (int(x), int(y)), size)
            
        pygame.display.flip()
        clock.tick(60)

def popcap_logo(dur=1500):
    start = pygame.time.get_ticks()
    font = None
    try:
        font = pygame.font.SysFont("arialblack", 96, bold=True)
    except:
        print("Arial Black not found, using default font.")
        font = pygame.font.SysFont(None, 100, bold=True)

    while pygame.time.get_ticks() - start < dur:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
        t = (pygame.time.get_ticks() - start) / dur
        
        c = (int(200 + 55 * math.sin(t * 4)), int(100 + 100 * math.sin(t * 5 + 2)), 255)
        txt = font.render("PopCap", True, c)
        rect = txt.get_rect(center=(W // 2, H // 2))
        
        screen.fill(BLACK)
        screen.blit(txt, rect)
        pygame.display.flip()
        clock.tick(60)

# --- Main Menu with Level Selection ---

def main_menu():
    font_big = None
    font_mid = None
    try:
        font_big = pygame.font.SysFont("arialblack", 96, bold=True)
        font_mid = pygame.font.SysFont("arial", 36, bold=True)
    except:
        print("Arial/Arial Black not found, using default font.")
        font_big = pygame.font.SysFont(None, 100, bold=True)
        font_mid = pygame.font.SysFont(None, 40, bold=True)

    # Level buttons
    level_names = ["Level 1: Day", "Level 2: Night", "Level 3: Pool", "Level 4: Fog", "Level 5: Roof"]
    buttons = []
    for i in range(5):
        rect = pygame.Rect(W // 2 - 150, H // 2 - 100 + i * 60, 300, 50)
        buttons.append({"level": i + 1, "name": level_names[i], "rect": rect})

    t = 0
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return 0  # Quit signal
            if e.type == pygame.MOUSEBUTTONDOWN:
                for btn in buttons:
                    if btn["rect"].collidepoint(mouse_pos):
                        return btn["level"]  # Return selected level

        t += 0.01
        
        # Animated sky gradient background
        for y in range(H):
            col = (int(60 + 60 * math.sin(t + y * 0.01)),
                   int(120 + 60 * math.sin(t * 1.2 + y * 0.015)),
                   int(180 + 60 * math.sin(t * 0.8 + y * 0.02)))
            pygame.draw.line(screen, col, (0, y), (W, y))
            
        # Draw title
        title = font_big.render("ULTRA!PVZ", True, GOLD)
        screen.blit(title, title.get_rect(center=(W // 2, H // 2 - 200)))
        
        # Draw buttons
        for btn in buttons:
            pygame.draw.rect(screen, BLUE, btn["rect"])
            text = font_mid.render(btn["name"], True, WHITE)
            text_rect = text.get_rect(center=btn["rect"].center)
            screen.blit(text, text_rect)
        
        pygame.display.flip()
        clock.tick(60)
    
    return 0  # Default quit

# --- Game Entities ---

class Peashooter:
    def __init__(self, x, y, row):
        self.x = x
        self.y = y
        self.row = row
        self.size = 20
        self.health = 100
        self.last_shot = pygame.time.get_ticks()

    def update(self, projectiles, zombies_in_row):
        if not zombies_in_row:
            return
        current = pygame.time.get_ticks()
        if current - self.last_shot > 1500:
            projectiles.append(Pea(self.x + self.size, self.y, self.row))
            self.last_shot = current

    def draw(self, surface):
        pygame.draw.circle(surface, PEASHOOTER_GREEN, (self.x, self.y), self.size)

class Sunflower:
    def __init__(self, x, y, row):
        self.x = x
        self.y = y
        self.row = row
        self.size = 20
        self.health = 100
        self.last_sun = pygame.time.get_ticks()

    def update(self, sun):
        current = pygame.time.get_ticks()
        if current - self.last_sun > 10000:
            sun += 25
            self.last_sun = current
        return sun

    def draw(self, surface):
        pygame.draw.circle(surface, SUNFLOWER_YELLOW, (self.x, self.y), self.size)

class Zombie:
    def __init__(self, row):
        self.row = row
        self.x = W + 30
        self.y = 0  # Set later
        self.speed = 0.5
        self.health = 100
        self.width = 30
        self.height = 50

    def update(self):
        self.x -= self.speed

    def draw(self, surface):
        pygame.draw.rect(surface, ZOMBIE_GREY, (self.x - self.width//2, self.y - self.height//2, self.width, self.height))

class Pea:
    def __init__(self, x, y, row):
        self.x = x
        self.y = y
        self.row = row
        self.speed = 3

    def update(self):
        self.x += self.speed

    def draw(self, surface):
        pygame.draw.circle(surface, BLUE, (int(self.x), int(self.y)), 5)

# --- Game Loop ---

def game_loop(level):
    # Level-specific settings
    bg_colors = [LAWN_GREEN, DARK_GREEN, GREEN_BLUE, GRAY_GREEN, BROWN_GREEN]
    bg_color = bg_colors[level - 1]
    total_zombies = 3 + level * 3
    zombie_spawn_interval = max(1000, 5000 // level)
    
    # Grid setup
    grid_width = W - GRID_START_X - 50
    grid_height = H - GRID_START_Y - 20
    cell_width = grid_width / GRID_COLS
    cell_height = grid_height / GRID_ROWS

    # Game state
    sun = 50
    plants = []
    zombies = []
    projectiles = []
    spawned_zombies = 0
    last_zombie_spawn = pygame.time.get_ticks()
    last_auto_sun = pygame.time.get_ticks()
    
    # Seed packets
    seed_packets = [
        {"name": "Peashooter", "cost": 100, "rect": pygame.Rect(10, 10, 60, 80), "color": PEASHOOTER_GREEN},
        {"name": "Sunflower", "cost": 50, "rect": pygame.Rect(80, 10, 60, 80), "color": SUNFLOWER_YELLOW}
    ]
    selected_plant = None

    def get_cell_center(row, col):
        x = GRID_START_X + col * cell_width + cell_width / 2
        y = GRID_START_Y + row * cell_height + cell_height / 2
        return int(x), int(y)

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        mx, my = mouse_pos
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    clicked_packet = False
                    for packet in seed_packets:
                        if packet["rect"].collidepoint(mx, my):
                            if sun >= packet["cost"]:
                                selected_plant = packet["name"]
                                clicked_packet = True
                            break
                    if clicked_packet:
                        continue

                    if selected_plant and mx > GRID_START_X and mx < GRID_START_X + grid_width and my > GRID_START_Y and my < GRID_START_Y + grid_height:
                        col = int((mx - GRID_START_X) / cell_width)
                        row = int((my - GRID_START_Y) / cell_height)
                        plant_x, plant_y = get_cell_center(row, col)
                        if selected_plant == "Peashooter":
                            plants.append(Peashooter(plant_x, plant_y, row))
                            sun -= 100
                        elif selected_plant == "Sunflower":
                            plants.append(Sunflower(plant_x, plant_y, row))
                            sun -= 50
                        selected_plant = None
                if event.button == 3:  # Right click
                    selected_plant = None

        # Auto sun every 15 seconds
        if current_time - last_auto_sun > 15000:
            sun += 10
            last_auto_sun = current_time

        # Spawn zombies if not all spawned
        if spawned_zombies < total_zombies and current_time - last_zombie_spawn > zombie_spawn_interval:
            spawn_row = random.randint(0, GRID_ROWS - 1)
            new_zombie = Zombie(spawn_row)
            new_zombie.y = int(GRID_START_Y + spawn_row * cell_height + cell_height / 2)
            zombies.append(new_zombie)
            spawned_zombies += 1
            last_zombie_spawn = current_time

        # Update zombies
        for zombie in zombies[:]:
            zombie.update()
            if zombie.x < GRID_START_X - zombie.width:
                # Lose condition
                if GAME_FONT is not None:
                    lose_text = GAME_FONT.render("Game Over! Zombie reached the house.", True, RED)
                    screen.blit(lose_text, (W // 2 - 200, H // 2))
                else:
                    print("Game Over! Zombie reached the house.")
                pygame.display.flip()
                pygame.time.wait(2000)
                return False

            # Zombie eating plants
            for plant in plants[:]:
                if plant.row == zombie.row and abs(zombie.x - plant.x) < 20:
                    plant.health -= 0.5  # Gradual damage
                    if plant.health <= 0:
                        plants.remove(plant)
                    break

        # Update plants
        for plant in plants:
            zombies_in_row = [z for z in zombies if z.row == plant.row]
            if isinstance(plant, Peashooter):
                plant.update(projectiles, zombies_in_row)
            elif isinstance(plant, Sunflower):
                sun = plant.update(sun)

        # Update projectiles
        for proj in projectiles[:]:
            proj.update()
            if proj.x > W:
                projectiles.remove(proj)
                continue
            for zombie in zombies[:]:
                if zombie.row == proj.row and abs(zombie.x - proj.x) < 15 and abs(zombie.y - proj.y) < 15:
                    zombie.health -= 20
                    projectiles.remove(proj)
                    if zombie.health <= 0:
                        zombies.remove(zombie)
                    break

        # Win condition
        if spawned_zombies >= total_zombies and not zombies:
            win_text = GAME_FONT.render(f"Level {level} Complete!", True, GOLD)
            screen.blit(win_text, (W // 2 - 150, H // 2))
            pygame.display.flip()
            pygame.time.wait(2000)
            return True

        # --- Drawing ---
        screen.fill(bg_color)  # Level-specific background
        
        pygame.draw.rect(screen, TOP_BAR_GREY, (0, 0, W, TOP_BAR_HEIGHT))
        
        # Seed packets
        for packet in seed_packets:
            color = SEED_PACKET_SELECTED if selected_plant == packet["name"] else SEED_PACKET_GREY
            pygame.draw.rect(screen, color, packet["rect"])
            pygame.draw.rect(screen, packet["color"], packet["rect"].inflate(-10, -10))
            cost_text = GAME_FONT.render(str(packet["cost"]), True, SUN_YELLOW)
            screen.blit(cost_text, (packet["rect"].x + 5, packet["rect"].bottom - 25))

        # Sun count
        sun_text = GAME_FONT.render(f"SUN: {int(sun)}", True, SUN_YELLOW)
        screen.blit(sun_text, (seed_packets[-1]["rect"].right + 20, TOP_BAR_HEIGHT // 2 - 15))

        # Grid cells
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                x = GRID_START_X + c * cell_width
                y = GRID_START_Y + r * cell_height
                cell_rect = pygame.Rect(x + 2, y + 2, cell_width - 4, cell_height - 4)
                pygame.draw.rect(screen, SOIL_BROWN, cell_rect, border_radius=5)
        
        # Plants
        for plant in plants:
            plant.draw(screen)
        
        # Zombies
        for zombie in zombies:
            zombie.draw(screen)
        
        # Projectiles
        for proj in projectiles:
            proj.draw(screen)
        
        # Selected plant ghost
        if selected_plant:
            ghost_color = PEASHOOTER_GREEN if selected_plant == "Peashooter" else SUNFLOWER_YELLOW
            pygame.draw.circle(screen, ghost_color, mouse_pos, 20, 2)

        pygame.display.flip()
        clock.tick(60)

# --- Main Execution ---

def main():
    main_font = None
    try:
        main_font = pygame.font.SysFont("arialblack", 72, bold=True)
    except Exception as e:
        print(f"Warning: Arial Black not found ({e}). Using default font.")
        main_font = pygame.font.SysFont(None, 80, bold=True)

    # Intro sequence
    fade_text("SAMSOFT PRESENTS", main_font, GOLD, 1500)
    ea_swirl()
    popcap_logo()
    
    # Main loop for menu and levels
    while True:
        selected_level = main_menu()
        if selected_level == 0:
            break
        game_loop(selected_level)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
