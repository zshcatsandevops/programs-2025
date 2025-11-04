#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ULTRA!PVZ — Procedural Main Menu (800×600 Edition)
# ---------------------------------------------------------------------
# Each button now opens its own submenu:
#  - Adventure → mock level select
#  - Almanac → scrolling info entries
#  - Options → toggle dummy settings
#  - Quit → exits
# ---------------------------------------------------------------------

import pygame, math, random, sys
pygame.init()

# Screen setup
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ULTRA!PVZ — Procedural Main Menu")
clock = pygame.time.Clock()

# Fonts
font_big = pygame.font.SysFont(None, 90)
font_small = pygame.font.SysFont(None, 36)
font_tiny = pygame.font.SysFont(None, 22)

# Colors
SKY_TOP = (120, 190, 255)
SKY_BOTTOM = (60, 160, 90)
GRASS = (70, 160, 80)
BUTTON_COLOR = (180, 180, 180)
BUTTON_HOVER = (230, 230, 230)
TEXT = (20, 20, 20)

# ---------------------------------------------------------------------
# Cloud System
# ---------------------------------------------------------------------
class Cloud:
    def __init__(self):
        self.x = random.uniform(0, WIDTH)
        self.y = random.uniform(30, 160)
        self.s = random.uniform(0.6, 1.4)
        self.speed = random.uniform(10, 40)
    def update(self, dt):
        self.x += self.speed * dt
        if self.x > WIDTH + 200 * self.s:
            self.x = -200 * self.s
            self.y = random.uniform(20, 200)
    def draw(self, surf):
        for i in range(4):
            r = 45 * self.s * (0.7 + 0.3 * math.sin(pygame.time.get_ticks()/700 + i))
            pygame.draw.ellipse(surf, (255,255,255), (self.x + i*25*self.s, self.y, r, r/1.4))

clouds = [Cloud() for _ in range(6)]

def gradient(surf, top, bottom):
    for y in range(HEIGHT):
        t = y / HEIGHT
        c = [int(top[i] + (bottom[i]-top[i])*t) for i in range(3)]
        pygame.draw.line(surf, c, (0,y), (WIDTH,y))

# ---------------------------------------------------------------------
# Generic Button
# ---------------------------------------------------------------------
class Button:
    def __init__(self, text, y):
        self.text = text
        self.y = y
        self.rect = pygame.Rect(WIDTH//2 - 180, y, 360, 60)
    def draw(self, surf, hover):
        col = BUTTON_HOVER if hover else BUTTON_COLOR
        pygame.draw.rect(surf, col, self.rect, border_radius=20)
        pygame.draw.arc(surf, (150,150,150), self.rect.inflate(10,20), math.pi, 2*math.pi, 8)
        label = font_small.render(self.text, True, TEXT)
        surf.blit(label, (self.rect.centerx - label.get_width()//2,
                          self.rect.centery - label.get_height()//2))

# ---------------------------------------------------------------------
# Scene Drawing
# ---------------------------------------------------------------------
def draw_scene(t, dt):
    gradient(screen, SKY_TOP, SKY_BOTTOM)
    for c in clouds:
        c.update(dt)
        c.draw(screen)
    # Sine grass horizon
    points = [(x, 440 + 10 * math.sin(x*0.02 + t*1.5)) for x in range(0, WIDTH+20, 20)]
    pygame.draw.polygon(screen, GRASS, points + [(WIDTH,HEIGHT),(0,HEIGHT)])

    sway = math.sin(t*2)*4
    title = font_big.render("ULTRA!PVZ", True, (255,255,255))
    subtitle = font_tiny.render("Replanted Fusion Edition", True, (250,250,250))
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 140 + sway))
    screen.blit(subtitle, (WIDTH//2 - subtitle.get_width()//2, 210 + sway/2))

# ---------------------------------------------------------------------
# Submenus
# ---------------------------------------------------------------------
def adventure_menu():
    running, level = True, 1
    while running:
        dt = clock.tick(60)/1000
        for e in pygame.event.get():
            if e.type == pygame.QUIT: sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE: running = False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_LEFT: level = max(1, level-1)
                if e.key == pygame.K_RIGHT: level += 1
        draw_scene(pygame.time.get_ticks()/1000, dt)
        txt = font_small.render(f"Select Level {level}", True, (255,255,255))
        screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2-40))
        tip = font_tiny.render("← → to change level | ESC to return", True, (240,240,240))
        screen.blit(tip, (WIDTH//2 - tip.get_width()//2, HEIGHT - 40))
        pygame.display.flip()

def almanac_menu():
    running = True
    scroll = 0
    entries = [f"Entry {i}: Procedural test data." for i in range(1,11)]
    while running:
        dt = clock.tick(60)/1000
        for e in pygame.event.get():
            if e.type == pygame.QUIT: sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE: running = False
            if e.type == pygame.MOUSEWHEEL: scroll += e.y*30
        draw_scene(pygame.time.get_ticks()/1000, dt)
        base_y = 180 + scroll
        for i, text in enumerate(entries):
            y = base_y + i*40
            label = font_small.render(text, True, (250,250,250))
            screen.blit(label, (WIDTH//2 - label.get_width()//2, y))
        tip = font_tiny.render("Scroll or ESC to return", True, (240,240,240))
        screen.blit(tip, (WIDTH//2 - tip.get_width()//2, HEIGHT - 40))
        pygame.display.flip()

def options_menu():
    running = True
    setting = {"Fullscreen": False, "VSync": True}
    while running:
        dt = clock.tick(60)/1000
        for e in pygame.event.get():
            if e.type == pygame.QUIT: sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE: running = False
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mx,my = e.pos
                for i,key in enumerate(setting.keys()):
                    rect = pygame.Rect(WIDTH//2-150, 220+i*60, 300, 50)
                    if rect.collidepoint(mx,my):
                        setting[key] = not setting[key]
        draw_scene(pygame.time.get_ticks()/1000, dt)
        for i,(k,v) in enumerate(setting.items()):
            rect = pygame.Rect(WIDTH//2-150, 220+i*60, 300, 50)
            pygame.draw.rect(screen, BUTTON_COLOR, rect, border_radius=12)
            label = font_small.render(f"{k}: {'ON' if v else 'OFF'}", True, TEXT)
            screen.blit(label, (rect.centerx - label.get_width()//2,
                                rect.centery - label.get_height()//2))
        tip = font_tiny.render("Click to toggle | ESC to return", True, (240,240,240))
        screen.blit(tip, (WIDTH//2 - tip.get_width()//2, HEIGHT - 40))
        pygame.display.flip()

# ---------------------------------------------------------------------
# Main Menu
# ---------------------------------------------------------------------
def main():
    t = 0; running = True
    buttons = [
        Button("Adventure", 280),
        Button("Almanac", 350),
        Button("Options", 420),
        Button("Quit", 490)
    ]
    while running:
        dt = clock.tick(60)/1000
        t += dt
        for e in pygame.event.get():
            if e.type == pygame.QUIT: running = False
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for b in buttons:
                    if b.rect.collidepoint(e.pos):
                        if b.text == "Adventure": adventure_menu()
                        elif b.text == "Almanac": almanac_menu()
                        elif b.text == "Options": options_menu()
                        elif b.text == "Quit": running = False
        draw_scene(t, dt)
        mx,my = pygame.mouse.get_pos()
        for b in buttons:
            b.draw(screen, b.rect.collidepoint(mx,my))
        footer = font_tiny.render("© 2025 Samsoft | Click buttons to navigate", True, (230,230,230))
        screen.blit(footer, (WIDTH//2 - footer.get_width()//2, HEIGHT - 30))
        pygame.display.flip()
    pygame.quit()

if __name__ == "__main__":
    main()
