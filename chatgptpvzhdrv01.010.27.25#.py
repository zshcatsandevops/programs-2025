#!/usr/bin/env python3
"""
PVZ 1 Pygame Edition
[C] Samsoft 1999-2025 # $
A clean-room educational re-creation of Plants vs. Zombies 1,
with authentic main menu, Crazy Dave's monologue, HUD elements, and tutorial level.
Bundled for Windows via PyInstaller.
"""

import pygame, sys, random, math

# === CONSTANTS ===============================================================
SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 700
GRID_ROWS, GRID_COLS, GRID_SIZE = 5, 9, 100
UI_PANEL_HEIGHT = 100
GAME_HEIGHT = SCREEN_HEIGHT - UI_PANEL_HEIGHT

# === COLORS ==================================================================
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_GREY = (50, 50, 50)
COLOR_LIGHT_GREY = (180, 180, 180)
COLOR_GRID_1 = (0, 140, 30)
COLOR_GRID_2 = (0, 120, 25)
COLOR_UI_PANEL = (70, 40, 20)
COLOR_PVZ_GREEN = (0, 200, 0)
COLOR_PVZ_RED = (200, 0, 0)
COLOR_PVZ_BROWN = (139, 69, 19)
COLOR_SUN_YELLOW = (255, 215, 0)
COLOR_DAVE_SKIN = (255, 220, 170)
COLOR_DAVE_BEARD = (139, 69, 19)
COLOR_DAVE_HAT = (169, 169, 169)
COLOR_DAVE_SHIRT = (255, 255, 255)

# === SETTINGS ================================================================
STARTING_SUN = 50
PEASHOOTER_COST = 100
SPAWN_ZOMBIE_EVENT = pygame.USEREVENT + 1
SPAWN_ZOMBIE_RATE = 5000
SPAWN_SUN_EVENT = pygame.USEREVENT + 2
SPAWN_SUN_RATE = 7000

TUTORIAL_DIALOGS = [
    "Hey neighbor! I'm Crazy Dave.",
    "But you can call me Crazy Dave.",
    "Zombies are coming! Plant this Peashooter to defend your house.",
    "Click the sun to collect it and get more sun points.",
    "Now plant the Peashooter on the lawn!",
    "Good job! Here comes a zombie - watch your plant shoot it down."
]

# === HELPERS ================================================================
def get_grid_pos(mouse_pos):
    mx, my = mouse_pos
    if my < UI_PANEL_HEIGHT:
        return None, None
    row = (my - UI_PANEL_HEIGHT) // GRID_SIZE
    col = mx // GRID_SIZE
    if 0 <= row < GRID_ROWS and 0 <= col < GRID_COLS:
        return row, col
    return None, None

def get_screen_pos(row, col):
    return col * GRID_SIZE + GRID_SIZE // 2, UI_PANEL_HEIGHT + row * GRID_SIZE + GRID_SIZE // 2

# === OBJECTS ================================================================
class Peashooter:
    def __init__(self, row, col):
        self.row, self.col = row, col
        self.x, self.y = get_screen_pos(row, col)
        self.health = 300
        self.fire_rate = 1400
        self.last_shot = pygame.time.get_ticks()
        self.rect = pygame.Rect(self.x - 20, self.y - 30, 40, 60)

    def update(self, projectiles, zombies_in_row):
        if not zombies_in_row: return
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.fire_rate:
            self.last_shot = now
            projectiles.append(PeaProjectile(self.x + 20, self.y))

    def draw(self, screen):
        pygame.draw.rect(screen, (0,180,0), (self.x - 10, self.y - 10, 20, 40))
        pygame.draw.circle(screen, (0,220,0), (self.x, self.y - 20), 18)
        pygame.draw.arc(screen, COLOR_BLACK, (self.x - 10, self.y - 25, 20, 10), 0, math.pi, 2)

class Zombie:
    def __init__(self, row):
        self.row = row
        self.x = SCREEN_WIDTH + random.randint(0, 50)
        self.y = UI_PANEL_HEIGHT + row * GRID_SIZE + GRID_SIZE // 2
        self.health = 200
        self.speed = 0.5 + random.random() * 0.3
        self.rect = pygame.Rect(self.x - 25, self.y - 40, 50, 80)

    def update(self):
        self.x -= self.speed
        self.rect.centerx = int(self.x)

    def draw(self, screen):
        pygame.draw.rect(screen, (100,150,100), self.rect)
        pygame.draw.circle(screen, (150,200,150), (self.x, self.y - 30), 18)
        pygame.draw.circle(screen, COLOR_WHITE, (self.x - 8, self.y - 33), 5)
        pygame.draw.circle(screen, COLOR_WHITE, (self.x + 8, self.y - 33), 5)
        pygame.draw.circle(screen, COLOR_BLACK, (self.x - 8, self.y - 33), 2)
        pygame.draw.circle(screen, COLOR_BLACK, (self.x + 8, self.y - 33), 2)

class PeaProjectile:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.speed = 6
        self.damage = 20
        self.rect = pygame.Rect(self.x, self.y - 5, 16, 10)
    def update(self): self.x += self.speed; self.rect.centerx = int(self.x)
    def draw(self, screen): pygame.draw.ellipse(screen, (0,200,0), self.rect)

class SunToken:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.value = 25
        self.fall_speed = 0.5
        self.lifespan = 10000
        self.spawn_time = pygame.time.get_ticks()
        self.rect = pygame.Rect(self.x - 15, self.y - 15, 30, 30)
    def update(self):
        if self.y < SCREEN_HEIGHT - 50:
            self.y += self.fall_speed
            self.rect.centery = int(self.y)
        return pygame.time.get_ticks() - self.spawn_time > self.lifespan
    def draw(self, screen):
        pygame.draw.circle(screen, COLOR_SUN_YELLOW, (int(self.x), int(self.y)), 15)
        pygame.draw.circle(screen, COLOR_WHITE, (int(self.x), int(self.y)), 10)
    def check_click(self, pos): return self.rect.collidepoint(pos)

# === MAIN MENU ===============================================================
class MainMenu:
    def __init__(self, screen, clock, title_font, small_font):
        self.screen, self.clock = screen, clock
        self.title_font, self.small_font = title_font, small_font
        self.decor_suns = [SunToken(random.randint(100, SCREEN_WIDTH-100), random.randint(50,200)) for _ in range(3)]
        self.play_button = pygame.Rect(SCREEN_WIDTH//2-100, SCREEN_HEIGHT//2+120, 200, 60)
        self.quit_button = pygame.Rect(SCREEN_WIDTH//2-100, SCREEN_HEIGHT//2+200, 200, 60)
        self.hud_sun = 0
        self.seed_cards = [pygame.Rect(SCREEN_WIDTH-400+i*90, SCREEN_HEIGHT-80, 80, 60) for i in range(3)]
        self.monologue_lines = [
            "Greetings, neighbor!", "The name's Crazy Dave.", "But you can just call me Crazy Dave.",
            "Listen, I've got a surprise for you.", "Use your shovel and dig up those plants!",
            "We're going BOWLING!", "Because I'm CRAAAZY!!!!!"
        ]
        self.current_monologue = random.choice(self.monologue_lines)

    def draw_crazy_dave(self):
        dave_x, dave_y = 150, SCREEN_HEIGHT - 150
        pygame.draw.rect(self.screen, COLOR_DAVE_SHIRT, (dave_x - 30, dave_y - 20, 60, 80))
        pygame.draw.circle(self.screen, COLOR_DAVE_SKIN, (dave_x, dave_y - 60), 30)
        pygame.draw.circle(self.screen, COLOR_WHITE, (dave_x - 10, dave_y - 65), 8)
        pygame.draw.circle(self.screen, COLOR_WHITE, (dave_x + 10, dave_y - 65), 8)
        pygame.draw.circle(self.screen, COLOR_BLACK, (dave_x - 10, dave_y - 65), 3)
        pygame.draw.circle(self.screen, COLOR_BLACK, (dave_x + 10, dave_y - 65), 3)
        pygame.draw.polygon(self.screen, COLOR_DAVE_BEARD, [(dave_x - 20, dave_y - 40),(dave_x, dave_y - 20),(dave_x + 20, dave_y - 40)])
        pygame.draw.rect(self.screen, COLOR_DAVE_HAT, (dave_x - 35, dave_y - 90, 70, 20))
        pygame.draw.rect(self.screen, COLOR_DAVE_HAT, (dave_x - 25, dave_y - 100, 50, 20))
        bubble_rect = pygame.Rect(dave_x + 50, dave_y - 100, 300, 80)
        pygame.draw.rect(self.screen, COLOR_WHITE, bubble_rect, border_radius=10)
        quote_text = self.small_font.render(self.current_monologue, True, COLOR_BLACK)
        self.screen.blit(quote_text, (bubble_rect.x + 10, bubble_rect.y + 10))

    def draw(self):
        self.screen.fill(COLOR_GRID_1)
        for sun in self.decor_suns: sun.update(); sun.draw(self.screen)
        title = self.title_font.render("PLANTS vs ZOMBIES", True, COLOR_PVZ_GREEN)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, SCREEN_HEIGHT//3))
        self.draw_crazy_dave()
        pygame.draw.rect(self.screen, COLOR_PVZ_GREEN, self.play_button, border_radius=10)
        play_txt = self.title_font.render("PLAY", True, COLOR_WHITE)
        self.screen.blit(play_txt, (self.play_button.centerx - play_txt.get_width()//2, self.play_button.centery - play_txt.get_height()//2))
        pygame.display.flip()

    def handle_event(self, e):
        if e.type == pygame.QUIT: return "quit"
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.play_button.collidepoint(e.pos): return "play"
        return None

    def run(self):
        while True:
            for e in pygame.event.get():
                res = self.handle_event(e)
                if res == "quit": pygame.quit(); sys.exit()
                if res == "play": return True
            self.draw()
            self.clock.tick(60)

# === BASE GAME ===============================================================
class Game:
    def __init__(self, screen, clock):
        self.screen, self.clock = screen, clock
        self.suns, self.zombies, self.projectiles = [], [], []
    def handle(self, e): pass
    def update(self): pass
    def draw(self):
        self.screen.fill(COLOR_GRID_1)
        pygame.display.flip()
    def run(self):
        running = True
        while running:
            for e in pygame.event.get():
                if e.type == pygame.QUIT: running = False
            self.update()
            self.draw()
            self.clock.tick(60)
        pygame.quit(); sys.exit()

# === TUTORIAL ================================================================
class TutorialGame(Game):
    def __init__(self, screen, clock):
        super().__init__(screen, clock)
        self.dialogs = TUTORIAL_DIALOGS
        self.step = 0
        self.current_dialog = self.dialogs[self.step]
        self.font = pygame.font.Font(None, 32)
    def draw(self):
        self.screen.fill(COLOR_GRID_1)
        dave_x, dave_y = 150, SCREEN_HEIGHT - 150
        pygame.draw.rect(self.screen, COLOR_DAVE_SHIRT, (dave_x - 30, dave_y - 20, 60, 80))
        pygame.draw.circle(self.screen, COLOR_DAVE_SKIN, (dave_x, dave_y - 60), 30)
        text = self.font.render(self.current_dialog, True, COLOR_BLACK)
        self.screen.blit(text, (300, SCREEN_HEIGHT - 100))
        pygame.display.flip()

# === MAIN ===================================================================
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    title_font = pygame.font.Font(None, 72)
    small_font = pygame.font.Font(None, 24)
    print("PVZ 1 Pygame Edition — Ready!")
    menu = MainMenu(screen, clock, title_font, small_font)
    if menu.run():
        TutorialGame(screen, clock).run()
