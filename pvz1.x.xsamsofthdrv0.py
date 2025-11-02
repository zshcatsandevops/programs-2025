#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plants vs. Zombies: Rebooted InfDev 0.1
---------------------------------------
Stylized ULTRA!PVZ main menu inspired by PopCap's original,
with animated sky gradient, waving grass, glowing logo,
and smooth fade transitions.

© Samsoft 2025
© 2000s PopCap Games
"""

import pygame
import math
import sys

pygame.init()

# ───────── CONFIG ─────────
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
BLACK, WHITE = (0, 0, 0), (255, 255, 255)
GOLD, YELLOW, GRAY = (255, 215, 0), (255, 255, 0), (128, 128, 128)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Plants vs. Zombies: Rebooted InfDev 0.1")

# ───────── TRANSITION ─────────
def fade_transition():
    fade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    fade.fill(BLACK)
    for alpha in range(0, 255, 8):
        fade.set_alpha(alpha)
        screen.blit(fade, (0, 0))
        pygame.display.flip()
        pygame.time.delay(12)

# ───────── MAIN MENU ─────────
def main_menu():
    clock = pygame.time.Clock()
    pygame.mouse.set_visible(True)

    # Fonts
    font_big = pygame.font.SysFont("arial", 96, bold=True)
    font_mid = pygame.font.SysFont("arial", 38, bold=True)
    font_small = pygame.font.SysFont("arial", 22, bold=True)
    font_tiny = pygame.font.SysFont("arial", 16, bold=True)

    # Texts
    title_surface = font_big.render("ULTRA!PVZ", True, GOLD)
    subtitle_surface = font_mid.render("Rebooted InfDev 0.1", True, YELLOW)
    credit1 = font_tiny.render("© Samsoft 2025", True, GRAY)
    credit2 = font_tiny.render("© 2000s PopCap Games", True, GRAY)

    # Buttons
    buttons = [
        {"label": "ADVENTURE", "rect": pygame.Rect(SCREEN_WIDTH//2-120, 300, 240, 50)},
        {"label": "MINI-GAMES", "rect": pygame.Rect(SCREEN_WIDTH//2-120, 360, 240, 50)},
        {"label": "PUZZLE", "rect": pygame.Rect(SCREEN_WIDTH//2-120, 420, 240, 50)},
        {"label": "SURVIVAL", "rect": pygame.Rect(SCREEN_WIDTH//2-120, 480, 240, 50)},
    ]

    angle, grass_scroll, selected = 0, 0, -1
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and selected == 0:
                fade_transition(); return
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_a, pygame.K_RETURN, pygame.K_SPACE):
                    fade_transition(); return
                if event.key == pygame.K_ESCAPE:
                    running = False

        # Animate
        angle = (angle + 1) % 360
        grass_scroll = (grass_scroll + 1.5) % 40

        # --- Background sky gradient (fixed clamp) ---
        for y in range(0, SCREEN_HEIGHT // 2, 2):
            c = min(255, 120 + y // 3)
            r = c
            g = min(255, c + 40)
            b = 255
            pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        # Ground
        pygame.draw.rect(screen, (70, 150, 70), (0, SCREEN_HEIGHT - 180, SCREEN_WIDTH, 180))
        pygame.draw.rect(screen, (30, 100, 30), (0, SCREEN_HEIGHT - 150, SCREEN_WIDTH, 150))

        # Grass
        for gx in range(-1, SCREEN_WIDTH // 40 + 2):
            pygame.draw.rect(screen, (0, 80, 0), (gx * 40 - grass_scroll, SCREEN_HEIGHT - 150, 20, 150))

        # Title wobble & glow
        wobble_y = 8 * math.sin(math.radians(angle))
        glow_val = 200 + int(55 * math.sin(math.radians(angle * 2)))
        glow_surface = font_big.render("ULTRA!PVZ", True, (glow_val, glow_val, 0))
        screen.blit(glow_surface, (SCREEN_WIDTH//2 - glow_surface.get_width()//2, 100 + wobble_y))
        screen.blit(title_surface, (SCREEN_WIDTH//2 - title_surface.get_width()//2, 100 + wobble_y))

        # Subtitle
        screen.blit(subtitle_surface, (SCREEN_WIDTH//2 - subtitle_surface.get_width()//2, 190 + wobble_y / 2))

        # Buttons
        mx, my = pygame.mouse.get_pos()
        selected = -1
        for i, btn in enumerate(buttons):
            r = btn["rect"]
            hovered = r.collidepoint(mx, my)
            fill_color = (200, 140, 60) if hovered else (181, 107, 41)
            border_color = (100, 60, 20)
            pygame.draw.rect(screen, fill_color, r, border_radius=10)
            pygame.draw.rect(screen, border_color, r, 4, border_radius=10)
            label = font_small.render(btn["label"], True, BLACK)
            screen.blit(label, (r.centerx - label.get_width()//2, r.centery - label.get_height()//2))
            if hovered: selected = i

        # Footer
        info = font_tiny.render("Press A for Almanac anytime", True, WHITE)
        screen.blit(info, (SCREEN_WIDTH//2 - info.get_width()//2, SCREEN_HEIGHT - 70))
        screen.blit(credit1, (SCREEN_WIDTH - credit1.get_width() - 15, SCREEN_HEIGHT - 30))
        screen.blit(credit2, (15, SCREEN_HEIGHT - 30))

        pygame.display.flip()
        clock.tick(60)

# ───────── RUN ─────────
if __name__ == "__main__":
    main_menu()
    pygame.quit()
