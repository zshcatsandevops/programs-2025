#!/usr/bin/env python3
"""
PVZ DECOMP 1.0X [C] SAMSOFT LLC 2025-2026
Optimized PvZ-like tower defense with Crazy Dave tutorial
"""

import sys, math, random, pygame
from pygame.locals import *

pygame.init()
WIDTH, HEIGHT = 800, 520
FPS = 60
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("PVZ DECOMP 1.0X [C] SAMSOFT LLC 2025-2026")
clock = pygame.time.Clock()

# --- Colors ---
WHITE = (255,255,255); BLACK = (0,0,0)
GREEN = (86,200,86); DARKGREEN = (66,170,66)
BROWN = (124,84,50); RED = (230,70,70)
YELLOW = (255,230,90); BLUE = (80,200,255)
ORANGE = (255,165,0); GRAY = (140,140,140); SILVER = (185,185,185)

# --- Board ---
GRID_COLS, GRID_ROWS = 9, 5
UI_H = 80
LAWN_X, LAWN_Y = 80, UI_H
CELL_W = int((WIDTH - LAWN_X - 60) / GRID_COLS)
CELL_H = int((HEIGHT - UI_H - 30) / GRID_ROWS)
HOUSE_W = 52
SPAWN_X = LAWN_X + GRID_COLS*CELL_W + 12

# --- Fonts ---
FONT = pygame.font.SysFont(None, 20)
BIG = pygame.font.SysFont(None, 44)
HUGE = pygame.font.SysFont(None, 64)
MENU_FONT = pygame.font.SysFont(None, 36)
TITLE_FONT = pygame.font.SysFont(None, 48)

# --- Data ---
PLANT_DATA = {
    "sunflower": {"cost": 50, "recharge": 7000, "action_cd": 9000, "hp": 300, "action": "sun"},
    "shooter": {"cost": 100, "recharge": 7000, "action_cd": 1500, "hp": 300, "action": "shoot"},
    "wallnut": {"cost": 50, "recharge": 10000, "action_cd": 0, "hp": 1200, "action": "block"},
}
ZOMBIE_DATA = {
    "normal": {"hp": 220, "speed": 28, "dps": 12},
    "cone": {"hp": 420, "speed": 26, "dps": 12},
    "bucket": {"hp": 820, "speed": 24, "dps": 12}
}

# Pre-calculated surfaces for better performance
SUN_SURFACE = None
PLANT_SURFACES = {}

def init_surfaces():
    """Initialize cached surfaces for better performance"""
    global SUN_SURFACE, PLANT_SURFACES
    
    # Sun surface
    sun_surf = pygame.Surface((24, 24), pygame.SRCALPHA)
    pygame.draw.circle(sun_surf, YELLOW, (12, 12), 11)
    pygame.draw.circle(sun_surf, ORANGE, (12, 12), 11, 2)
    SUN_SURFACE = sun_surf
    
    # Plant surfaces
    PLANT_SURFACES["sunflower"] = pygame.Surface((40, 40), pygame.SRCALPHA)
    pygame.draw.circle(PLANT_SURFACES["sunflower"], YELLOW, (20, 20), 18)
    pygame.draw.circle(PLANT_SURFACES["sunflower"], ORANGE, (20, 20), 18, 2)
    
    PLANT_SURFACES["shooter"] = pygame.Surface((40, 40), pygame.SRCALPHA)
    pygame.draw.circle(PLANT_SURFACES["shooter"], GREEN, (20, 20), 18)
    pygame.draw.circle(PLANT_SURFACES["shooter"], BLUE, (32, 16), 6)
    
    PLANT_SURFACES["wallnut"] = pygame.Surface((44, 48), pygame.SRCALPHA)
    pygame.draw.rect(PLANT_SURFACES["wallnut"], BROWN, (2, 4, 40, 44), border_radius=8)

def grid_to_px(col, row): 
    return LAWN_X + col*CELL_W + CELL_W//2, LAWN_Y + row*CELL_H + CELL_H//2

def cell_at(mx, my):
    if not (LAWN_X <= mx < SPAWN_X and LAWN_Y <= my < LAWN_Y + GRID_ROWS*CELL_H): 
        return None
    col = (mx - LAWN_X)//CELL_W
    row = (my - LAWN_Y)//CELL_H
    return int(max(0,min(GRID_COLS-1,col))), int(max(0,min(GRID_ROWS-1,row)))

# === Intro Screen (SAMSOFT LLC PRESENTS) ===
class Intro:
    def __init__(self):
        self.timer = 0.0
        self.duration = 3.0  # 3 seconds
        self.state = "showing"  # showing, fading, done
        
    def update(self, dt):
        self.timer += dt
        if self.timer > self.duration:
            if self.state == "showing":
                self.state = "fading"
                self.timer = 0.0
            elif self.state == "fading":
                self.state = "done"
                
    def draw(self, surface):
        if self.state == "done":
            return
            
        alpha = 255 if self.state == "showing" else int(255 * (1 - self.timer / 1.0))
        if alpha < 0:
            alpha = 0
            
        # Background
        overlay = pygame.Surface((WIDTH, HEIGHT)).convert_alpha()
        overlay.fill((0, 0, 0))
        overlay.set_alpha(255 - alpha)  # Darken background during fade
        surface.blit(overlay, (0, 0))
        
        # SAMSOFT LLC PRESENTS text
        text = TITLE_FONT.render("[SAMSOFT LLC PRESENTS]", True, WHITE)
        text = pygame.transform.smoothscale(text, (text.get_width() * 1.2, text.get_height() * 1.2))
        text.set_alpha(alpha)
        tw, th = text.get_size()
        surface.blit(text, ((WIDTH - tw) // 2, (HEIGHT - th) // 2))

# === Main Menu ===
class MainMenu:
    def __init__(self):
        self.options = ["Start Adventure", "Options", "Quit"]
        self.selected = 0
        self.title = "Plants vs. Zombies"
        
    def handle_event(self, event):
        if event.type == KEYDOWN:
            if event.key == K_DOWN:
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key == K_UP:
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key == K_RETURN:
                return self.options[self.selected].lower()
        elif event.type == MOUSEBUTTONDOWN:
            mx, my = event.pos
            y_offset = HEIGHT // 2 - 50
            for i, option in enumerate(self.options):
                opt_surf = MENU_FONT.render(option, True, WHITE)
                opt_rect = opt_surf.get_rect(center=(WIDTH // 2, y_offset + i * 40))
                if opt_rect.collidepoint(mx, my):
                    return option.lower()
        return None
    
    def draw(self, surface):
        # Background gradient or simple fill
        surface.fill((135, 206, 235))  # Sky blue like PvZ
        
        # Title
        title_surf = TITLE_FONT.render(self.title, True, GREEN)
        surface.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, 100))
        
        # Options
        y_offset = HEIGHT // 2 - 50
        for i, option in enumerate(self.options):
            color = YELLOW if i == self.selected else WHITE
            opt_surf = MENU_FONT.render(option, True, color)
            opt_rect = opt_surf.get_rect(center=(WIDTH // 2, y_offset + i * 40))
            surface.blit(opt_surf, opt_rect)
            
            # Highlight selected
            if i == self.selected:
                pygame.draw.rect(surface, ORANGE, opt_rect.inflate(10, 10), 3, border_radius=5)

# === Entities ===
class Pea:
    __slots__ = ('x', 'y', 'row', 'spd', 'dmg', 'dead')
    
    def __init__(self, x, y, row, dmg=20):
        self.x = x; self.y = y; self.row = row
        self.spd = 320; self.dmg = dmg; self.dead = False
        
    def update(self, dt, zombies):
        self.x += self.spd * dt
        for z in zombies:
            if z.row == self.row and not z.dead and abs(z.x - self.x) < 14:
                z.hp -= self.dmg
                self.dead = True
                break
        if self.x > WIDTH:
            self.dead = True
            
    def draw(self, surface):
        pygame.draw.circle(surface, BLUE, (int(self.x), int(self.y)), 5)

class Sun:
    __slots__ = ('x', 'y', 'vy', 'target_y', 'dead', 'timer')
    
    def __init__(self, x, y, fall=True):
        self.x = x; self.y = y
        self.vy = 60 if fall else 0
        self.target_y = y + random.randint(40, 110) if fall else y
        self.dead = False; self.timer = 0.0
        
    def update(self, dt):
        if self.vy > 0 and self.y < self.target_y:
            self.y += self.vy * dt
        self.timer += dt
        if self.timer > 12.0:
            self.dead = True
            
    def hit(self, mx, my):
        return (self.x - mx)**2 + (self.y - my)**2 <= 144
        
    def draw(self, surface):
        surface.blit(SUN_SURFACE, (int(self.x) - 12, int(self.y) - 12))

class Plant:
    __slots__ = ('col', 'row', 'name', 'x', 'y', 'hp', 'action', 'action_cd', 'timer_ms', 'dead')
    
    def __init__(self, col, row, name):
        data = PLANT_DATA[name]
        self.col = col; self.row = row; self.name = name
        self.x, self.y = grid_to_px(col, row)
        self.hp = data["hp"]; self.action = data["action"]
        self.action_cd = data["action_cd"]; self.timer_ms = 0; self.dead = False
        
    def update(self, dt, world):
        if self.dead:
            return
            
        self.timer_ms += dt * 1000
        if self.action == "shoot" and self.timer_ms >= self.action_cd:
            self.timer_ms = 0
            world.peas.append(Pea(self.x + 22, self.y - 2, self.row))
        elif self.action == "sun" and self.timer_ms >= self.action_cd:
            self.timer_ms = 0
            world.suns.append(Sun(self.x, self.y - 22, fall=False))
            
    def damage(self, amount):
        self.hp -= amount
        self.dead = self.hp <= 0
        
    def draw(self, surface):
        # Use cached surface for plants
        if self.name in PLANT_SURFACES:
            if self.name == "wallnut":
                surface.blit(PLANT_SURFACES[self.name], (self.x - 22, self.y - 24))
            else:
                surface.blit(PLANT_SURFACES[self.name], (self.x - 20, self.y - 20))
        
        # Health bar
        max_hp = PLANT_DATA[self.name]["hp"]
        ratio = max(0, min(1, self.hp / max_hp))
        pygame.draw.rect(surface, RED, (self.x - 20, self.y + 22, 40, 5))
        pygame.draw.rect(surface, GREEN, (self.x - 20, self.y + 22, int(40 * ratio), 5))

class Zombie:
    __slots__ = ('name', 'row', 'hp', 'speed', 'dps', 'x', 'y', 'state', 'target', 'dead')
    
    def __init__(self, name, row):
        data = ZOMBIE_DATA[name]
        self.name = name; self.row = row
        self.hp = data["hp"]; self.speed = data["speed"]; self.dps = data["dps"]
        self.x = SPAWN_X; self.y = LAWN_Y + row * CELL_H + CELL_H // 2
        self.state = "walk"; self.target = None; self.dead = False
        
    def update(self, dt, world):
        if self.dead or self.hp <= 0:
            self.dead = True
            return
            
        # Check mowers
        for mower in world.mowers:
            if (mower.row == self.row and not mower.spent and 
                self.x < (LAWN_X + HOUSE_W + 8)):
                mower.trigger()
            if (mower.row == self.row and mower.active and not mower.spent and 
                abs(self.x - mower.x) < 20):
                self.dead = True
                return
                
        if self.state == "eat" and self.target and not self.target.dead:
            self.target.damage(self.dps * dt)
            if self.target.dead:
                self.state = "walk"
                self.target = None
        else:
            self.x -= self.speed * dt
            self.state = "walk"
            self.target = None
            
            for plant in world.plants_by_row[self.row]:
                if not plant.dead and abs(plant.x - self.x) < 24:
                    self.state = "eat"
                    self.target = plant
                    break
                    
            if self.x < LAWN_X + HOUSE_W:
                world.game_over = True
                
    def draw(self, surface):
        # Color based on zombie type
        if self.name == "normal":
            color = (200, 110, 60)
        elif self.name == "cone":
            color = (250, 140, 70)
        else:  # bucket
            color = SILVER
            
        pygame.draw.rect(surface, color, (int(self.x) - 16, int(self.y) - 26, 32, 52), border_radius=5)
        pygame.draw.circle(surface, BLACK, (int(self.x), int(self.y) - 28), 5)
        
        # Health bar
        max_hp = ZOMBIE_DATA[self.name]["hp"]
        ratio = max(0, min(1, self.hp / max_hp))
        pygame.draw.rect(surface, RED, (int(self.x) - 18, int(self.y) + 26, 36, 4))
        pygame.draw.rect(surface, GREEN, (int(self.x) - 18, int(self.y) + 26, int(36 * ratio), 4))

class Mower:
    __slots__ = ('row', 'x', 'y', 'active', 'spent', 'speed')
    
    def __init__(self, row):
        self.row = row
        self.x = LAWN_X + 8
        self.y = LAWN_Y + row * CELL_H + CELL_H // 2 + 10
        self.active = False; self.spent = False; self.speed = 520
        
    def trigger(self):
        if not self.active and not self.spent:
            self.active = True
            
    def update(self, dt):
        if self.active and not self.spent:
            self.x += self.speed * dt
            if self.x > WIDTH + 40:
                self.spent = True
                self.active = False
                
    def draw(self, surface):
        color = (180, 40, 40) if not self.spent else GRAY
        pygame.draw.rect(surface, color, (int(self.x) - 16, int(self.y) - 10, 32, 20), border_radius=4)
        pygame.draw.circle(surface, BLACK, (int(self.x) - 12, int(self.y) + 12), 6)
        pygame.draw.circle(surface, BLACK, (int(self.x) + 12, int(self.y) + 12), 6)

# === Crazy Dave Tutorial ===
class Tutorial:
    __slots__ = ('lines', 'index', 'done')
    
    def __init__(self):
        self.lines = [
            "Crazy Dave: Howdy neighbor! I'm CRAAAAZY DAVE!",
            "Crazy Dave: Those zombies are coming for your lawn!",
            "Crazy Dave: Click a seed packet, then click the grass to plant!",
            "Crazy Dave: Sunflowers make more sun—collect it when it drops!",
            "Crazy Dave: Keep an eye on your sun points up there.",
            "Crazy Dave: Don't let those zombies reach the house!",
            "Crazy Dave: Ready? Let's rock!"
        ]
        self.index = 0; self.done = False
        
    def next(self):
        self.index += 1
        if self.index >= len(self.lines):
            self.done = True
            
    def draw(self, surface):
        if self.done:
            return
            
        pygame.draw.rect(surface, (240, 240, 200), (60, HEIGHT - 100, WIDTH - 120, 80), border_radius=10)
        pygame.draw.circle(surface, (255, 180, 100), (100, HEIGHT - 60), 24)
        
        text = FONT.render(self.lines[self.index], True, BLACK)
        surface.blit(text, (140, HEIGHT - 75))
        
        prompt = FONT.render("[Press SPACE]", True, (100, 100, 100))
        surface.blit(prompt, (WIDTH - 180, HEIGHT - 40))

# === World ===
class World:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.plants = []
        self.plants_by_row = [[] for _ in range(GRID_ROWS)]
        self.zombies = []
        self.peas = []
        self.suns = []
        self.mowers = [Mower(r) for r in range(GRID_ROWS)]
        
        self.sun_total = 50
        self.seed_recharge = {k: 0.0 for k in PLANT_DATA}
        self.selected_name = None
        self.wave = 1
        self.wave_target = 5
        
        self.spawn_timer = 0
        self.spawn_cd = 4
        self.wave_spawned = 0
        
        self.game_over = False
        self.won = False
        
        self.tutorial = Tutorial()
        self.tutorial_active = True
        
    def plant_at(self, col, row):
        for plant in self.plants_by_row[row]:
            if plant.col == col:
                return plant
        return None
        
    def add_plant(self, name, col, row):
        plant = Plant(col, row, name)
        self.plants.append(plant)
        self.plants_by_row[row].append(plant)
        
    def remove_plant(self, plant):
        if plant in self.plants:
            self.plants.remove(plant)
        if plant in self.plants_by_row[plant.row]:
            self.plants_by_row[plant.row].remove(plant)
            
    def update(self, dt):
        if self.game_over or self.won or (self.tutorial_active and not self.tutorial.done):
            return
            
        # Update seed recharges
        for name in self.seed_recharge:
            self.seed_recharge[name] = max(0.0, self.seed_recharge[name] - dt * 1000)
            
        # Random sun generation
        if random.random() < 0.006:
            self.suns.append(Sun(
                random.randint(LAWN_X + 40, WIDTH - 60), 
                LAWN_Y + 8, 
                True
            ))
            
        # Zombie spawning
        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_cd:
            self.spawn_timer = 0
            if self.wave_spawned < self.wave * 5:
                z_type = random.choice(list(ZOMBIE_DATA.keys()))
                row = random.randint(0, GRID_ROWS - 1)
                self.zombies.append(Zombie(z_type, row))
                self.wave_spawned += 1
            elif not any(not z.dead for z in self.zombies):
                if self.wave >= self.wave_target:
                    self.won = True
                else:
                    self.wave += 1
                    self.wave_spawned = 0
                    self.spawn_cd = max(1.4, self.spawn_cd - 0.3)
                    
        # Update all entities
        for plant in list(self.plants):
            if plant.dead:
                self.remove_plant(plant)
                continue
            plant.update(dt, self)
            
        for zombie in list(self.zombies):
            zombie.update(dt, self)
        self.zombies = [z for z in self.zombies if not z.dead]
        
        for pea in list(self.peas):
            pea.update(dt, self.zombies)
        self.peas = [b for b in self.peas if not b.dead]
        
        for sun in list(self.suns):
            sun.update(dt)
        self.suns = [s for s in self.suns if not s.dead]
        
        for mower in self.mowers:
            mower.update(dt)
            
    def draw_board(self, surface):
        # Draw house
        pygame.draw.rect(surface, BROWN, (0, LAWN_Y, HOUSE_W, HEIGHT - LAWN_Y))
        
        # Draw lawn grid
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                x = LAWN_X + col * CELL_W
                y = LAWN_Y + row * CELL_H
                color = GREEN if (row + col) % 2 == 0 else DARKGREEN
                pygame.draw.rect(surface, color, (x, y, CELL_W, CELL_H))
                
        # Spawn line
        pygame.draw.line(surface, BLACK, (SPAWN_X, LAWN_Y), (SPAWN_X, LAWN_Y + GRID_ROWS * CELL_H), 2)
        
    def draw_ui(self, surface):
        pygame.draw.rect(surface, GRAY, (0, 0, WIDTH, UI_H))
        
        # Sun counter and wave info
        surface.blit(FONT.render(f"Sun: {int(self.sun_total)}", True, BLACK), (12, 10))
        surface.blit(FONT.render(f"Wave: {self.wave}/{self.wave_target}", True, BLACK), (12, 32))
        surface.blit(FONT.render("Tip: Right-click cancels selection • R to reset", True, BLACK), (12, 54))
        
        # Plant selection cards
        x_offset = 100
        for name in PLANT_DATA:
            rect = pygame.Rect(x_offset, 12, 62, 54)
            can_plant = self.seed_recharge[name] <= 0 and self.sun_total >= PLANT_DATA[name]["cost"]
            
            # Card background
            pygame.draw.rect(surface, (86, 180, 86) if can_plant else (110, 110, 110), rect, border_radius=6)
            
            # Plant icon
            center_x, center_y = rect.center
            if name in PLANT_SURFACES:
                if name == "wallnut":
                    surface.blit(PLANT_SURFACES[name], (center_x - 22, center_y - 24))
                else:
                    surface.blit(PLANT_SURFACES[name], (center_x - 20, center_y - 20))
            
            # Plant name and cost
            surface.blit(FONT.render(f"{name[:7]}", True, BLACK), (rect.x + 5, rect.y + 2))
            surface.blit(FONT.render(str(PLANT_DATA[name]['cost']), True, BLACK), (rect.x + 5, rect.y + 36))
            
            # Recharge overlay
            if self.seed_recharge[name] > 0:
                percent = min(1.0, self.seed_recharge[name] / max(1, PLANT_DATA[name]['recharge']))
                height = int(percent * rect.height)
                overlay = pygame.Surface((rect.width, height), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 120))
                surface.blit(overlay, (rect.x, rect.bottom - height))
                
            # Selection highlight
            if self.selected_name == name:
                pygame.draw.rect(surface, ORANGE, rect, 3, border_radius=6)
                
            x_offset += 76
            
    def draw(self, surface):
        self.draw_board(surface)
        
        # Draw entities in optimal order
        for sun in self.suns:
            sun.draw(surface)
        for plant in self.plants:
            plant.draw(surface)
        for zombie in self.zombies:
            zombie.draw(surface)
        for pea in self.peas:
            pea.draw(surface)
        for mower in self.mowers:
            mower.draw(surface)
            
        # Game state messages
        if self.game_over:
            text = HUGE.render("ZOMBIES BREACHED!", True, RED)
            surface.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 30))
            
        if self.won:
            text = HUGE.render("LEVEL COMPLETE!", True, (60, 210, 60))
            surface.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 30))
            
        # Tutorial
        if self.tutorial_active and not self.tutorial.done:
            self.tutorial.draw(surface)

# === Main Loop ===
def main():
    # Initialize cached surfaces
    init_surfaces()
    
    # Game states
    state = "intro"  # intro, menu, game
    intro = Intro()
    menu = MainMenu()
    world = World()
    
    running = True
    
    while running:
        dt = clock.tick(FPS) / 1000.0
        
        # Event handling
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    if state == "game":
                        state = "menu"
                    else:
                        running = False
                        
        # State-specific handling
        if state == "intro":
            intro.update(dt)
            if intro.state == "done":
                state = "menu"
        elif state == "menu":
            action = menu.handle_event(event)
            if action == "start adventure" or action == "play":
                state = "game"
                world.reset()
            elif action == "quit":
                running = False
        elif state == "game":
            mx, my = pygame.mouse.get_pos()
            
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    state = "menu"
                elif event.key == K_r:
                    world.reset()
                elif event.key == K_SPACE:
                    if world.tutorial_active and not world.tutorial.done:
                        world.tutorial.next()
                    else:
                        world.selected_name = None
            elif event.type == MOUSEBUTTONDOWN:
                if world.tutorial_active and not world.tutorial.done:
                    continue
                    
                # Collect suns
                for sun in list(world.suns):
                    if sun.hit(mx, my):
                        world.sun_total += 25
                        sun.dead = True
                        
                # Plant selection
                x_offset = 100
                for name in PLANT_DATA:
                    rect = pygame.Rect(x_offset, 12, 62, 54)
                    if rect.collidepoint(mx, my) and world.seed_recharge[name] <= 0:
                        world.selected_name = name
                    x_offset += 76
                    
                # Plant placement
                if world.selected_name:
                    cell = cell_at(mx, my)
                    if cell:
                        col, row = cell
                        if not world.plant_at(col, row):
                            cost = PLANT_DATA[world.selected_name]["cost"]
                            if world.sun_total >= cost:
                                world.add_plant(world.selected_name, col, row)
                                world.sun_total -= cost
                                world.seed_recharge[world.selected_name] = PLANT_DATA[world.selected_name]["recharge"]
                                world.selected_name = None
                                
                # Reset on game over/win
                if world.game_over or world.won:
                    if event.button == 1:  # Left click to restart
                        world.reset()
                    
                # Right-click cancel
                if event.button == 3:
                    world.selected_name = None
        
        # Update game state
        if state == "game":
            world.update(dt)
            if world.tutorial.done:
                world.tutorial_active = False
        
        # Rendering
        screen.fill(WHITE)
        
        if state == "intro":
            intro.draw(screen)
        elif state == "menu":
            menu.draw(screen)
        elif state == "game":
            world.draw_ui(screen)
            world.draw(screen)
            
        pygame.display.flip()
        
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
