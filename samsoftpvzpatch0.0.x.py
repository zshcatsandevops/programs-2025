#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ULTRA!PVZ 0.3 — Unified Engine + Procedural Main Menu + Intro Logos + Gameplay
# -----------------------------------------------------------------------------
# Adds EA, PopCap, and Samsoft intro sequences before the main menu.
# Each logo appears in sequence with fade transitions.
# -----------------------------------------------------------------------------

import pygame, math, random, sys
from dataclasses import dataclass

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ULTRA!PVZ 0.3 — Intro + Unified Engine")
clock = pygame.time.Clock()

# -----------------------------------------------------------------------------
# Colors
# -----------------------------------------------------------------------------
BLACK = (0,0,0)
WHITE = (255,255,255)
SKY_TOP = (120, 190, 255)
SKY_BOTTOM = (60, 160, 90)
GRASS = (60, 180, 90)
HOUSE = (210, 180, 160)
ENEMY = (180, 50, 50)
MOWER = (200, 200, 200)
PLANT = (80, 200, 80)
PROJECTILE = (255, 240, 120)
BUTTON_COLOR = (180, 180, 180)
BUTTON_HOVER = (230, 230, 230)
TEXT = (255,255,255)

font_big = pygame.font.SysFont(None, 90)
font_med = pygame.font.SysFont(None, 60)
font_small = pygame.font.SysFont(None, 36)

# -----------------------------------------------------------------------------
# Fade Utility
# -----------------------------------------------------------------------------
def fade_text(text, duration=2.0, font=font_med, color=WHITE):
    surf = font.render(text, True, color)
    alpha = 0
    timer = 0
    while timer < duration:
        dt = clock.tick(60)/1000
        timer += dt
        alpha = min(255, (timer/duration)*255)
        screen.fill(BLACK)
        temp = surf.copy()
        temp.set_alpha(alpha)
        screen.blit(temp, (WIDTH//2 - surf.get_width()//2, HEIGHT//2 - surf.get_height()//2))
        pygame.display.flip()
    pygame.time.wait(800)

# -----------------------------------------------------------------------------
# Gradient Utility
# -----------------------------------------------------------------------------
def gradient(surf, top, bottom):
    for y in range(HEIGHT):
        t = y / HEIGHT
        c = [int(top[i] + (bottom[i]-top[i])*t) for i in range(3)]
        pygame.draw.line(surf, c, (0,y), (WIDTH,y))

# -----------------------------------------------------------------------------
# Button Class
# -----------------------------------------------------------------------------
class Button:
    def __init__(self, text, pos, callback):
        self.text = text
        self.pos = pos
        self.callback = callback
        self.rect = pygame.Rect(pos[0]-100, pos[1]-25, 200, 50)

    def draw(self, surf):
        mx, my = pygame.mouse.get_pos()
        hover = self.rect.collidepoint(mx, my)
        color = BUTTON_HOVER if hover else BUTTON_COLOR
        pygame.draw.rect(surf, color, self.rect, border_radius=8)
        label = font_small.render(self.text, True, (0,0,0))
        surf.blit(label, (self.rect.centerx - label.get_width()//2, self.rect.centery - label.get_height()//2))

    def click(self):
        if self.rect.collidepoint(pygame.mouse.get_pos()):
            self.callback()

# -----------------------------------------------------------------------------
# Gameplay Entities
# -----------------------------------------------------------------------------
@dataclass
class Projectile:
    x: float
    y: float
    speed: float = 180
    active: bool = True
    def update(self, dt, enemies):
        self.x += self.speed * dt
        for e in enemies:
            if e.active and abs(e.y - self.y) < 20 and abs(e.x - self.x) < 20:
                e.health -= 1
                self.active = False
        if self.x > WIDTH:
            self.active = False
    def draw(self, surf):
        if self.active:
            pygame.draw.circle(surf, PROJECTILE, (int(self.x), int(self.y)), 6)

class Plant:
    def __init__(self, grid_pos):
        self.grid_x, self.grid_y = grid_pos
        self.x = 160 + self.grid_x * 80
        self.y = 140 + self.grid_y * 80
        self.shoot_timer = 0
    def update(self, dt, projectiles):
        self.shoot_timer += dt
        if self.shoot_timer > 1.8:
            self.shoot_timer = 0
            projectiles.append(Projectile(self.x + 25, self.y + 20))
    def draw(self, surf):
        pygame.draw.rect(surf, PLANT, (self.x, self.y, 40, 40), border_radius=8)

class Enemy:
    def __init__(self, lane, speed):
        self.lane = lane
        self.x = WIDTH + random.randint(0, 200)
        self.y = 140 + lane * 80
        self.speed = speed
        self.health = 3
        self.active = True
    def update(self, dt):
        if self.active:
            self.x -= self.speed * dt
            if self.x < 100 or self.health <= 0:
                self.active = False
    def draw(self, surf):
        if self.active:
            pygame.draw.rect(surf, ENEMY, (self.x, self.y, 30, 40))

class Mower:
    def __init__(self, lane):
        self.lane = lane
        self.x = 120
        self.y = 140 + lane * 80
        self.active = False
        self.used = False
    def update(self, dt, enemies):
        if self.active:
            self.x += 250 * dt
            for e in enemies:
                if e.lane == self.lane and e.active and abs(e.x - self.x) < 30:
                    e.active = False
            if self.x > WIDTH + 60:
                self.active = False
                self.used = True
        else:
            for e in enemies:
                if not self.used and e.active and e.x < self.x + 20 and e.lane == self.lane:
                    self.active = True
    def draw(self, surf):
        col = (240,240,240) if self.active else MOWER
        pygame.draw.rect(surf, col, (self.x, self.y+10, 50, 30), border_radius=8)

# -----------------------------------------------------------------------------
# Stage Simulation
# -----------------------------------------------------------------------------
def play_stage(stage_num):
    grid = [[None for _ in range(9)] for _ in range(5)]
    mowers = [Mower(i) for i in range(5)]
    enemies, projectiles, plants = [], [], []
    spawn_timer, wave_count, max_waves = 0, 0, 4 + stage_num
    running = True

    while running:
        dt = clock.tick(60) / 1000
        spawn_timer += dt

        for e in pygame.event.get():
            if e.type == pygame.QUIT: sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                running = False
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mx, my = e.pos
                if mx > 160 and my > 140 and my < 540:
                    gx = (mx - 160)//80
                    gy = (my - 140)//80
                    if 0 <= gx < 9 and 0 <= gy < 5 and grid[gy][gx] is None:
                        p = Plant((gx, gy))
                        plants.append(p)
                        grid[gy][gx] = p

        if spawn_timer > 2.0 and wave_count < max_waves:
            spawn_timer = 0
            lane = random.randint(0,4)
            enemies.append(Enemy(lane, random.uniform(30, 60)))
            wave_count += 1

        for e in enemies: e.update(dt)
        for p in plants: p.update(dt, projectiles)
        for m in mowers: m.update(dt, enemies)
        for proj in projectiles: proj.update(dt, enemies)

        projectiles = [p for p in projectiles if p.active]

        gradient(screen, SKY_TOP, SKY_BOTTOM)
        pygame.draw.rect(screen, GRASS, (0, HEIGHT-160, WIDTH, 160))
        pygame.draw.rect(screen, HOUSE, (0, 120, 120, 300))

        for i in range(5):
            pygame.draw.line(screen, (50,130,60), (120, 180+i*80), (WIDTH, 180+i*80), 2)

        for p in plants: p.draw(screen)
        for m in mowers: m.draw(screen)
        for e in enemies: e.draw(screen)
        for proj in projectiles: proj.draw(screen)

        txt = font_small.render(f"Stage {stage_num} — Enemies left: {len([e for e in enemies if e.active])}", True, TEXT)
        screen.blit(txt, (WIDTH//2 - txt.get_width()//2, 40))

        pygame.display.flip()

# -----------------------------------------------------------------------------
# Intro Sequences
# -----------------------------------------------------------------------------
def show_intros():
    screen.fill(BLACK)
    fade_text("ELECTRONIC ARTS PRESENTS", duration=2.0)
    screen.fill(BLACK)
    fade_text("POPCAP GAMES", duration=2.0)
    screen.fill(BLACK)
    fade_text("SAMSOFT STUDIOS", duration=2.5, font=font_big, color=(200,255,200))
    pygame.time.wait(1000)

# -----------------------------------------------------------------------------
# Menu System
# -----------------------------------------------------------------------------
def main_menu():
    def start_game():
        for stage in range(1, 4):
            play_stage(stage)

    def quit_game():
        pygame.quit()
        sys.exit()

    buttons = [
        Button("Adventure", (WIDTH//2, 320), start_game),
        Button("Quit", (WIDTH//2, 400), quit_game)
    ]

    t = 0
    while True:
        dt = clock.tick(60) / 1000
        t += dt

        for e in pygame.event.get():
            if e.type == pygame.QUIT: sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for b in buttons: b.click()

        gradient(screen, SKY_TOP, SKY_BOTTOM)
        pygame.draw.rect(screen, GRASS, (0, HEIGHT-160, WIDTH, 160))

        title = font_big.render("ULTRA!PVZ", True, (255,255,255))
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 160 + math.sin(t*2)*4))

        for b in buttons: b.draw(screen)
        pygame.display.flip()

# -----------------------------------------------------------------------------
# Main Entry
# -----------------------------------------------------------------------------
def main():
    show_intros()
    main_menu()

if __name__ == "__main__":
    main()
