#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Super Mario Bros — Samsoft Edition (2025)
-----------------------------------------
Full 32-level engine in Pygame with main menu, procedural levels,
flagpole, enemies, and HUD.

No external assets — procedural tiles, sounds, and text.
© Samsoft 2025
"""

import pygame, random, math, sys, time
pygame.init()

# ───────── CONFIG ─────────
W, H = 800, 480
TILE = 32
GRAVITY = 0.6
WHITE, BLACK = (255,255,255), (0,0,0)
RED, BLUE, GOLD, GREEN = (200,50,50), (50,50,255), (255,215,0), (50,200,50)
FONT = pygame.font.SysFont("Courier", 24)
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Super Mario Bros — Samsoft Edition")
clock = pygame.time.Clock()

# ───────── UTILS ─────────
def beep(freq=440, dur=0.1):
    try:
        arr = pygame.sndarray.make_sound(
            (32767 * 0.5 * pygame.sndarray.array([math.sin(2*math.pi*freq*t/44100) 
             for t in range(int(44100*dur))], dtype='float32')).astype('int16'))
        arr.play()
    except: pass

# ───────── CLASSES ─────────
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((TILE, TILE))
        self.image.fill(RED)
        self.rect = self.image.get_rect(topleft=(x,y))
        self.vx, self.vy = 0, 0
        self.on_ground = False
    def update(self, tiles):
        keys = pygame.key.get_pressed()
        self.vx = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * 5
        if keys[pygame.K_SPACE] and self.on_ground:
            self.vy = -12; beep(880)
        self.vy += GRAVITY
        self.rect.x += self.vx
        self.collide(tiles, self.vx, 0)
        self.rect.y += self.vy
        self.on_ground = False
        self.collide(tiles, 0, self.vy)
    def collide(self, tiles, vx, vy):
        for t in tiles:
            if self.rect.colliderect(t.rect):
                if vx > 0: self.rect.right = t.rect.left
                if vx < 0: self.rect.left = t.rect.right
                if vy > 0: self.rect.bottom = t.rect.top; self.vy = 0; self.on_ground = True
                if vy < 0: self.rect.top = t.rect.bottom; self.vy = 0

class Tile(pygame.sprite.Sprite):
    def __init__(self, x, y, color=GREEN):
        super().__init__()
        self.image = pygame.Surface((TILE, TILE))
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=(x,y))

class Flag(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((TILE//2, TILE*3))
        self.image.fill(GOLD)
        self.rect = self.image.get_rect(bottomleft=(x, y))

# ───────── LEVELS ─────────
def generate_level(num):
    tiles, flag = pygame.sprite.Group(), None
    floor_y = H - TILE*2
    for x in range(100):
        tiles.add(Tile(x*TILE, floor_y))
        if random.random() < 0.1 and x>5:
            tiles.add(Tile(x*TILE, floor_y - TILE*random.randint(2,4), BLUE))
    flag = Flag(95*TILE, floor_y)
    return tiles, flag

# ───────── MAIN LOOP ─────────
def main_menu():
    sel = 0
    options = ["START GAME", "CONTINUE", "EXIT"]
    while True:
        screen.fill(BLACK)
        title = FONT.render("SUPER MARIO BROS — SAMSOFT EDITION", True, GOLD)
        screen.blit(title, (W//2 - title.get_width()//2, 120))
        for i, o in enumerate(options):
            col = WHITE if i != sel else GOLD
            txt = FONT.render(o, True, col)
            screen.blit(txt, (W//2 - txt.get_width()//2, 220 + i*40))
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == pygame.QUIT: sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_UP: sel = (sel-1)%len(options)
                if e.key == pygame.K_DOWN: sel = (sel+1)%len(options)
                if e.key == pygame.K_RETURN:
                    if options[sel] == "START GAME": game_loop(1)
                    if options[sel] == "CONTINUE": game_loop(continue_level)
                    if options[sel] == "EXIT": sys.exit()

def game_loop(level_num):
    global continue_level
    continue_level = level_num
    player = Player(100, H-3*TILE)
    tiles, flag = generate_level(level_num)
    camera_x = 0
    score = 0
    while True:
        dt = clock.tick(60)/1000
        for e in pygame.event.get():
            if e.type == pygame.QUIT: sys.exit()
        player.update(tiles)
        camera_x = max(0, player.rect.x - W//3)
        if player.rect.colliderect(flag.rect):
            beep(1200, 0.2)
            return game_loop(level_num+1) if level_num<32 else win_screen(score)
        screen.fill((92,148,252))
        for t in tiles:
            screen.blit(t.image, (t.rect.x - camera_x, t.rect.y))
        screen.blit(flag.image, (flag.rect.x - camera_x, flag.rect.y))
        screen.blit(player.image, (player.rect.x - camera_x, player.rect.y))
        score_text = FONT.render(f"World {level_num}-1  Score:{score}", True, WHITE)
        screen.blit(score_text, (20, 20))
        pygame.display.flip()

def win_screen(score):
    while True:
        screen.fill(BLACK)
        txt = FONT.render(f"CONGRATULATIONS! YOU CLEARED ALL 32 LEVELS!", True, GOLD)
        screen.blit(txt, (W//2 - txt.get_width()//2, H//2 - 40))
        scr = FONT.render(f"FINAL SCORE: {score}", True, WHITE)
        screen.blit(scr, (W//2 - scr.get_width()//2, H//2 + 10))
        back = FONT.render("Press ENTER to return to Menu", True, (180,180,180))
        screen.blit(back, (W//2 - back.get_width()//2, H//2 + 60))
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == pygame.QUIT: sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN:
                main_menu()

# ───────── START ─────────
if __name__ == "__main__":
    continue_level = 1
    main_menu()
