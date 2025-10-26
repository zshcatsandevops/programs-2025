import pygame
import sys
import math
import random

pygame.init()
pygame.mixer.init()

# Screen
WIDTH, HEIGHT = 600, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Inverted Fate - Sans Fight (Snowdin)")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
SNOW = (240, 248, 255)
DARK_SNOW = (200, 220, 230)
BONE_WHITE = (240, 240, 240)

# Fonts
font_dialogue = pygame.font.SysFont("Arial", 22, bold=True)
font_small = pygame.font.SysFont("Arial", 16)

# Game state
STATE_DIALOGUE = 0
STATE_VICTORY = 1
game_state = STATE_DIALOGUE
dialogue_idx = 0
typewriter_pos = 0
typewriter_timer = 0

# ----- EXACT DIALOGUE FROM INVERTED FATE SNOWDIN FIGHT -----
dialogues = [
    "Sans: heya.",
    "Sans: you've been... been busy, huh?",
    "Sans: ...",
    "Sans: so, i've got a question for ya.",
    "Sans: do you think even the worst person can change?",
    "Sans: that everybody can be a good person, if they just try?",
    "Sans: heh heh heh heh...",
    "Sans: alright.",
    "Sans: well, here's a better question.",
    "Sans: do you wanna have a bad time?",
    "Sans: 'cause if you take another step forward...",
    "Sans: ...you're really not gonna like what happens next.",
    "Sans: ...",
    "Sans: welp.",
    "Sans: sorry, old lady.",
    "Sans: this is why i never make promises.",
    "Sans: ...",
    "Sans: it's a beautiful day outside.",
    "Sans: birds are singing, flowers are blooming...",
    "Sans: on days like these, kids like you...",
    "Sans: ...Should be burning in hell.",
    "Sans: ...",
    "Sans: but you're not gonna fight, are ya?",
    "Sans: you're taking the pacifist route.",
    "Sans: ...guess i can't blame ya.",
    "Sans: heh.",
    "Sans: well, i'm not gonna waste my time.",
    "Sans: go ahead.",
    "Sans: spare me.",
    "Sans: i know you will."
]

# Sans sprite (same as original but slightly larger)
def create_sans_sprite():
    s = pygame.Surface((100, 120), pygame.SRCALPHA)
    # head
    pygame.draw.circle(s, WHITE, (50, 30), 25)
    # hood
    pygame.draw.rect(s, (0, 0, 0), (30, 5, 40, 20))
    pygame.draw.rect(s, (0, 0, 0), (25, 20, 50, 15))
    # body
    pygame.draw.rect(s, WHITE, (25, 55, 50, 50), border_radius=10)
    # eyes
    pygame.draw.circle(s, BLACK, (40, 28), 6)
    pygame.draw.circle(s, BLACK, (60, 28), 6)
    # mouth
    pygame.draw.arc(s, BLACK, (38, 32, 24, 12), 0, math.pi, 2)
    return s

sans_sprite = create_sans_sprite()

# Snow particles
snowflakes = []
for _ in range(80):
    snowflakes.append({
        'x': random.randint(0, WIDTH),
        'y': random.randint(-HEIGHT, 0),
        'speed': random.uniform(0.5, 1.5),
        'size': random.randint(1, 3)
    })

clock = pygame.time.Clock()
running = True

def draw_background():
    # Night sky gradient
    for y in range(HEIGHT // 2):
        ratio = y / (HEIGHT // 2)
        color = (
            int(10 * (1 - ratio) + 50 * ratio),
            int(10 * (1 - ratio) + 70 * ratio),
            int(30 * (1 - ratio) + 120 * ratio)
        )
        pygame.draw.line(screen, color, (0, y), (WIDTH, y))
    # Snow ground
    pygame.draw.rect(screen, SNOW, (0, HEIGHT // 2, WIDTH, HEIGHT // 2))
    pygame.draw.rect(screen, DARK_SNOW, (0, HEIGHT - 50, WIDTH, 50))

def update_snow():
    for f in snowflakes:
        f['y'] += f['speed']
        if f['y'] > HEIGHT:
            f['y'] = random.randint(-50, -5)
            f['x'] = random.randint(0, WIDTH)
    for f in snowflakes:
        pygame.draw.circle(screen, SNOW, (int(f['x']), int(f['y'])), f['size'])

def draw_dialogue():
    box = pygame.Rect(20, HEIGHT - 120, WIDTH - 40, 100)
    pygame.draw.rect(screen, (20, 20, 40), box, border_radius=8)
    pygame.draw.rect(screen, WHITE, box, 2, border_radius=8)

    text = dialogues[dialogue_idx]
    displayed = text[:typewriter_pos]
    rendered = font_dialogue.render(displayed, True, WHITE)
    screen.blit(rendered, (35, HEIGHT - 100))

    # Blinking cursor
    if pygame.time.get_ticks() % 1000 < 500:
        cursor_x = 35 + rendered.get_width()
        pygame.draw.line(screen, WHITE, (cursor_x, HEIGHT - 100), (cursor_x, HEIGHT - 80), 2)

    # Continue prompt
    cont = font_small.render("Press Z to continue", True, (255, 255, 100))
    screen.blit(cont, (WIDTH - cont.get_width() - 20, HEIGHT - 35))

def draw_victory():
    screen.fill(BLACK)
    lines = [
        "VICTORY ACHIEVED",
        "",
        "You showed mercy to Sans.",
        "",
        "Press R to play again"
    ]
    y = HEIGHT // 2 - len(lines) * 15
    for line in lines:
        color = (0, 255, 0) if "VICTORY" in line else WHITE
        txt = font_dialogue.render(line, True, color)
        screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, y))
        y += 30

while running:
    dt = clock.tick(60)
    typewriter_timer += dt

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if game_state == STATE_DIALOGUE:
                if event.key == pygame.K_z:
                    if typewriter_pos < len(dialogues[dialogue_idx]):
                        typewriter_pos = len(dialogues[dialogue_idx])
                    else:
                        dialogue_idx += 1
                        typewriter_pos = 0
                        if dialogue_idx >= len(dialogues):
                            game_state = STATE_VICTORY
            elif game_state == STATE_VICTORY:
                if event.key == pygame.K_r:
                    dialogue_idx = 0
                    typewriter_pos = 0
                    game_state = STATE_DIALOGUE

    # Typewriter effect
    if game_state == STATE_DIALOGUE and typewriter_pos < len(dialogues[dialogue_idx]):
        if typewriter_timer > 35:
            typewriter_pos += 1
            typewriter_timer = 0

    # --- DRAW ---
    draw_background()
    update_snow()

    # Sans (centered near top)
    screen.blit(sans_sprite, (WIDTH // 2 - 50, 60))

    if game_state == STATE_DIALOGUE:
        draw_dialogue()
    elif game_state == STATE_VICTORY:
        draw_victory()

    pygame.display.flip()

pygame.quit()
sys.exit()
