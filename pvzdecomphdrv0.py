import pygame
import sys
import random
import math
from pygame.locals import *

pygame.init()
pygame.mixer.init()

# === CONSTANTS ===
WIDTH, HEIGHT = 800, 600
LAWN_X, LAWN_Y = 250, 100
GRID_ROWS, GRID_COLS = 5, 9
CELL_W, CELL_H = 80, 100
UI_HEIGHT = 100
HOUSE_W = 200
SPAWN_X = WIDTH - HOUSE_W
FPS = 60

# === COLORS ===
SKY_BLUE = (113, 197, 207)
LIGHT_BLUE = (173, 216, 230)
LAWN_GREEN = (120, 190, 33)
LAWN_DARK = (100, 160, 30)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GOLD = (255, 215, 0)
DARK_GREEN = (60, 120, 30)
BUTTON_HOVER = (200, 230, 255)
ORANGE = (255, 165, 0)
DARK_RED = (139, 0, 0)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ULTRA Plants vs Zombies - PyGame Edition")
clock = pygame.time.Clock()

FONT_SMALL = pygame.font.SysFont("Arial", 16)
FONT_MEDIUM = pygame.font.SysFont("Arial", 24)
FONT_BIG = pygame.font.SysFont("Arial", 36)
FONT_TITLE = pygame.font.SysFont("Arial", 48, bold=True)

# === IMAGE PLACEHOLDERS ===
def load_surfaces():
    global SUN_SURF
    SUN_SURF = pygame.Surface((40, 40), pygame.SRCALPHA)
    pygame.draw.circle(SUN_SURF, (255, 220, 50), (20, 20), 20)
    pygame.draw.circle(SUN_SURF, (255, 255, 150), (20, 20), 15)

# === PLACEHOLDER WORLD ===
class World:
    def __init__(self):
        self.game_over = False
        self.victory = False
    def update(self, dt): pass
    def draw_game(self, surf):
        surf.fill(SKY_BLUE)
        text = FONT_BIG.render("Adventure Mode Active!", True, BLACK)
        surf.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 20))
        note = FONT_SMALL.render("Press ESC to return to Menu", True, BLACK)
        surf.blit(note, (WIDTH//2 - note.get_width()//2, HEIGHT//2 + 40))

# === OPTIONS PLACEHOLDER ===
class OptionsMenu:
    def __init__(self):
        self.buttons = [
            {"text": "Back", "rect": pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 80, 200, 50), "action": "back"}
        ]
        self.hovered = None
    def handle_event(self, e):
        if e.type == MOUSEMOTION:
            self.hovered = None
            for b in self.buttons:
                if b["rect"].collidepoint(e.pos):
                    self.hovered = b
        elif e.type == MOUSEBUTTONDOWN:
            for b in self.buttons:
                if b["rect"].collidepoint(e.pos):
                    return b["action"]
        return None
    def draw(self, surf):
        surf.fill(LIGHT_BLUE)
        title = FONT_BIG.render("Options Menu", True, BLACK)
        surf.blit(title, (WIDTH//2 - title.get_width()//2, 100))
        for b in self.buttons:
            col = BUTTON_HOVER if b == self.hovered else LAWN_GREEN
            pygame.draw.rect(surf, col, b["rect"], border_radius=12)
            pygame.draw.rect(surf, DARK_GREEN, b["rect"], 3, border_radius=12)
            txt = FONT_MEDIUM.render(b["text"], True, BLACK)
            surf.blit(txt, (b["rect"].centerx - txt.get_width()//2, b["rect"].centery - txt.get_height()//2))

# === MENU ===
class MainMenu:
    def __init__(self):
        bw, bh = 250, 50
        bx = WIDTH//2 - bw//2
        sy = HEIGHT//2 - 120
        self.buttons = [
            {"text": "Adventure", "rect": pygame.Rect(bx, sy, bw, bh), "action": "adventure"},
            {"text": "Survival", "rect": pygame.Rect(bx, sy + 70, bw, bh), "action": "survival"},
            {"text": "Mini-Games", "rect": pygame.Rect(bx, sy + 140, bw, bh), "action": "minigames"},
            {"text": "Zombatar", "rect": pygame.Rect(bx, sy + 210, bw, bh), "action": "zombatar"},
            {"text": "Options", "rect": pygame.Rect(bx, sy + 280, bw, bh), "action": "options"},
            {"text": "Quit", "rect": pygame.Rect(bx, sy + 350, bw, bh), "action": "quit"}
        ]
        self.hovered = None
    def handle_event(self, e):
        if e.type == MOUSEMOTION:
            self.hovered = None
            for b in self.buttons:
                if b["rect"].collidepoint(e.pos):
                    self.hovered = b
        elif e.type == MOUSEBUTTONDOWN:
            for b in self.buttons:
                if b["rect"].collidepoint(e.pos):
                    return b["action"]
        return None
    def draw(self, surf):
        for y in range(HEIGHT):
            ratio = y / HEIGHT
            c = (
                int(SKY_BLUE[0] * (1 - ratio) + LIGHT_BLUE[0] * ratio),
                int(SKY_BLUE[1] * (1 - ratio) + LIGHT_BLUE[1] * ratio),
                int(SKY_BLUE[2] * (1 - ratio) + LIGHT_BLUE[2] * ratio)
            )
            pygame.draw.line(surf, c, (0, y), (WIDTH, y))
        title_shadow = FONT_TITLE.render("ULTRA Plants vs Zombies", True, DARK_GREEN)
        title_text = FONT_TITLE.render("ULTRA Plants vs Zombies", True, GOLD)
        surf.blit(title_shadow, (WIDTH//2 - title_shadow.get_width()//2 + 3, 83))
        surf.blit(title_text, (WIDTH//2 - title_text.get_width()//2, 80))
        subtitle = FONT_MEDIUM.render("PyGame Edition", True, WHITE)
        surf.blit(subtitle, (WIDTH//2 - subtitle.get_width()//2, 140))
        for b in self.buttons:
            col = BUTTON_HOVER if b == self.hovered else LAWN_GREEN
            pygame.draw.rect(surf, col, b["rect"], border_radius=15)
            pygame.draw.rect(surf, DARK_GREEN, b["rect"], 3, border_radius=15)
            txt = FONT_MEDIUM.render(b["text"], True, BLACK)
            surf.blit(txt, (b["rect"].centerx - txt.get_width()//2, b["rect"].centery - txt.get_height()//2))
        footer = FONT_SMALL.render("[C] Samsoft Computing [C] 1999-2025", True, WHITE)
        surf.blit(footer, (WIDTH//2 - footer.get_width()//2, HEIGHT - 40))
        # NEW PROMPT MESSAGE
        prompt = FONT_SMALL.render("Press ENTER or click 'Adventure' to begin!", True, WHITE)
        surf.blit(prompt, (WIDTH//2 - prompt.get_width()//2, HEIGHT - 70))

# === INTRO ===
class Intro:
    def __init__(self):
        self.state = "fade_in"
        self.alpha = 0
        self.timer = 0
    def update(self, dt):
        self.timer += dt
        if self.state == "fade_in":
            self.alpha = min(255, self.alpha + 2)
            if self.alpha >= 255:
                self.state = "show"; self.timer = 0
        elif self.state == "show":
            if self.timer > 2.5: self.state = "fade_out"
        elif self.state == "fade_out":
            self.alpha = max(0, self.alpha - 2)
            if self.alpha <= 0: self.state = "done"
    def draw(self, surf):
        surf.fill(BLACK)
        t = FONT_BIG.render("ULTRA Plants vs Zombies", True, GOLD)
        t.set_alpha(self.alpha)
        surf.blit(t, (WIDTH//2 - t.get_width()//2, HEIGHT//2 - t.get_height()//2))
        s = FONT_MEDIUM.render("PyGame Edition", True, WHITE)
        s.set_alpha(self.alpha)
        surf.blit(s, (WIDTH//2 - s.get_width()//2, HEIGHT//2 + 50))

# === MAIN LOOP ===
def main():
    load_surfaces()
    intro = Intro()
    menu = MainMenu()
    options = OptionsMenu()
    world = None
    state = "intro"
    running = True

    while running:
        dt = clock.tick(FPS) / 1000
        for e in pygame.event.get():
            if e.type == QUIT:
                running = False

            # === INTRO ===
            if state == "intro":
                if e.type in (KEYDOWN, MOUSEBUTTONDOWN):
                    state = "menu"

            # === MENU ===
            elif state == "menu":
                res = menu.handle_event(e)
                if e.type == KEYDOWN and e.key == K_RETURN:
                    world = World(); state = "game"
                elif res == "adventure":
                    world = World(); state = "game"
                elif res == "options":
                    state = "options"
                elif res == "quit":
                    running = False
                elif res in ("survival", "minigames", "zombatar"):
                    state = res  # placeholder modes

            # === OPTIONS ===
            elif state == "options":
                res = options.handle_event(e)
                if res == "back" or (e.type == KEYDOWN and e.key == K_ESCAPE):
                    state = "menu"

            # === GAME ===
            elif state == "game":
                if e.type == KEYDOWN and e.key == K_ESCAPE:
                    state = "menu"

            # === PLACEHOLDER MODES ===
            elif state in ("survival", "minigames", "zombatar"):
                if e.type == KEYDOWN and e.key == K_ESCAPE:
                    state = "menu"

        # === UPDATE / DRAW ===
        if state == "intro":
            intro.update(dt)
            intro.draw(screen)
        elif state == "menu":
            menu.draw(screen)
        elif state == "options":
            options.draw(screen)
        elif state == "game" and world:
            world.update(dt)
            world.draw_game(screen)
        elif state in ("survival", "minigames", "zombatar"):
            screen.fill(SKY_BLUE)
            msg = FONT_BIG.render(f"{state.title()} Mode Placeholder", True, BLACK)
            screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 - 20))
            esc = FONT_SMALL.render("Press ESC to return to Menu", True, BLACK)
            screen.blit(esc, (WIDTH//2 - esc.get_width()//2, HEIGHT//2 + 40))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
