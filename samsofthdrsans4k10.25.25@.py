#!/usr/bin/env python3
"""
Inverted Fate – Sans Fight (Snowdin) — Undertale-accurate feel
--------------------------------------------------------------
• Fully self-contained: no external assets (“pr files = off”).
• Dialogue-only AU scene with snow effect.
• NO ambient static/white-noise; only subtle typewriter blips.
• Undertale-like 30 FPS fixed-step timing and input feel.
• Word-wrapped dialogue, 3-lines-per-page, typewriter with pauses,
  Z to speed/advance, R to restart. Integer-perfect drawing.
--------------------------------------------------------------
pip install pygame
"""

import pygame, sys, math, random
from textwrap import wrap

# ------------------------------------------------------------------
# Audio first (pre_init) to avoid crackle/pops; mono like classic GM
# ------------------------------------------------------------------
pygame.mixer.pre_init(44100, size=-16, channels=1, buffer=512)
pygame.init()

# ===============================================================
# SCREEN — Undertale runs at 640x480@30fps (4:3). Use vsync if avail.
# ===============================================================
WIDTH, HEIGHT = 640, 480
FLAGS = pygame.DOUBLEBUF
try:
    screen = pygame.display.set_mode((WIDTH, HEIGHT), FLAGS, vsync=1)  # pygame 2.x
except TypeError:
    screen = pygame.display.set_mode((WIDTH, HEIGHT), FLAGS)
pygame.display.set_caption("Inverted Fate – Sans Fight (Snowdin)")

# ===============================================================
# COLORS
# ===============================================================
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
SNOW = (240, 248, 255)
DARK_SNOW = (200, 220, 230)
BLUE = (100, 149, 237)
DARK_BLUE = (25, 25, 112)
STRIPE_WHITE = (220, 220, 220)

# ===============================================================
# FONTS — use built-in bold sans as placeholder (no external files)
# ===============================================================
try:
    font_dialogue = pygame.font.Font(None, 28)   # crisp-ish default
    font_small = pygame.font.Font(None, 20)
except Exception:
    font_dialogue = pygame.font.SysFont("Arial", 24, bold=True)
    font_small = pygame.font.SysFont("Arial", 18, bold=True)

# ===============================================================
# GAME STATE
# ===============================================================
STATE_DIALOGUE = 0
STATE_VICTORY = 1
game_state = STATE_DIALOGUE

# ===============================================================
# INPUT (GameMaker-like edge/held tracking)
# ===============================================================
z_pressed = False
z_just_pressed = False
r_pressed = False
r_just_pressed = False
esc_pressed = False
esc_just_pressed = False

def update_input():
    global z_pressed, z_just_pressed, r_pressed, r_just_pressed, esc_pressed, esc_just_pressed
    keys = pygame.key.get_pressed()

    prev_z = z_pressed
    prev_r = r_pressed
    prev_esc = esc_pressed

    z_pressed = keys[pygame.K_z] or keys[pygame.K_RETURN] or keys[pygame.K_SPACE]
    r_pressed = keys[pygame.K_r]
    esc_pressed = keys[pygame.K_ESCAPE]

    z_just_pressed = (not prev_z) and z_pressed
    r_just_pressed = (not prev_r) and r_pressed
    esc_just_pressed = (not prev_esc) and esc_pressed

# ===============================================================
# DIALOGUE
# ===============================================================
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

# ------- Word-wrap + pagination (3 lines/page, Undertale-like box) ---
BOX = pygame.Rect(24, HEIGHT - 150, WIDTH - 48, 126)  # inner text area
LINE_HEIGHT = 26
MAX_LINES_PER_PAGE = 3
TEXT_INNER_W = BOX.width - 20

def wrap_to_lines(text, font, max_width):
    words = text.split(' ')
    lines = []
    cur = ""
    for w in words:
        test = w if cur == "" else cur + " " + w
        if font.size(test)[0] <= max_width:
            cur = test
        else:
            if cur: lines.append(cur)
            # handle words longer than max width
            while font.size(w)[0] > max_width:
                # naive split by characters
                for i in range(len(w), 0, -1):
                    if font.size(w[:i])[0] <= max_width:
                        lines.append(w[:i])
                        w = w[i:]
                        break
            cur = w
    if cur:
        lines.append(cur)
    return lines if lines else [""]

def paginate_dialogues(dialogue_list):
    pages = []
    for t in dialogue_list:
        lines = wrap_to_lines(t, font_dialogue, TEXT_INNER_W)
        for i in range(0, len(lines), MAX_LINES_PER_PAGE):
            page_lines = lines[i:i+MAX_LINES_PER_PAGE]
            pages.append("\n".join(page_lines))
    return pages

PAGES = paginate_dialogues(dialogues)
page_idx = 0

# ===============================================================
# AUDIO — Typewriter blip only (no ambient static)
# ===============================================================
def make_type_blip(freq=880, ms=35, volume=0.4):
    """Small sine blip with quick attack/release to avoid clicks."""
    sr = 44100
    n = int(sr * ms / 1000.0)
    if n <= 0: n = 1
    buf = bytearray()
    for i in range(n):
        t = i / sr
        # envelope: 2ms attack, 5ms release (linear)
        a = min(1.0, i / (0.002 * sr))
        r = max(0.0, (n - i) / (0.005 * sr))
        env = max(0.0, min(1.0, min(a, r)))
        s = math.sin(2 * math.pi * freq * t) * env
        val = int(s * 32767 * volume)
        buf += val.to_bytes(2, byteorder='little', signed=True)
    return pygame.mixer.Sound(buffer=bytes(buf))

type_blip = make_type_blip()

# ===============================================================
# SANS — simple sprite (integer-only positioning)
# ===============================================================
def create_sans_sprite():
    s = pygame.Surface((100, 120), pygame.SRCALPHA)
    # Skull
    pygame.draw.circle(s, WHITE, (50, 30), 25)
    # Eyes
    pygame.draw.circle(s, BLACK, (40, 28), 6)
    pygame.draw.circle(s, BLACK, (60, 28), 6)
    # Mouth
    pygame.draw.arc(s, BLACK, (38, 32, 24, 12), 0, math.pi, 2)
    # Scarf
    pygame.draw.rect(s, BLUE, (20, 35, 60, 25), border_radius=3)
    for y in [38, 43, 48]:
        pygame.draw.line(s, STRIPE_WHITE, (20, y), (80, y), 2)
    # Shirt
    pygame.draw.rect(s, WHITE, (30, 55, 40, 25), border_radius=2)
    for y in [60, 65, 70]:
        pygame.draw.line(s, BLACK, (30, y), (70, y), 1)
    # Jacket
    pygame.draw.rect(s, BLUE, (25, 50, 50, 35), border_radius=5)
    # Badge
    pygame.draw.circle(s, WHITE, (50, 65), 4)
    pygame.draw.line(s, WHITE, (46, 65), (42, 63), 2)
    pygame.draw.line(s, WHITE, (46, 65), (42, 67), 2)
    pygame.draw.line(s, WHITE, (54, 65), (58, 63), 2)
    pygame.draw.line(s, WHITE, (54, 65), (58, 67), 2)
    # Sleeves
    pygame.draw.rect(s, BLUE, (15, 55, 15, 15))
    pygame.draw.rect(s, BLUE, (70, 55, 15, 15))
    # Mittens
    pygame.draw.ellipse(s, BLUE, (10, 65, 12, 10))
    pygame.draw.ellipse(s, BLUE, (78, 65, 12, 10))
    # Pants
    pygame.draw.rect(s, BLUE, (30, 80, 40, 15))
    # Boots
    pygame.draw.rect(s, DARK_BLUE, (25, 95, 15, 15))
    pygame.draw.rect(s, DARK_BLUE, (60, 95, 15, 15))
    return s

sans_sprite = create_sans_sprite()

# ===============================================================
# SNOW — light, integer-stepped for pixel crispness
# ===============================================================
snowflakes = [{'x': random.randint(0, WIDTH),
               'y': random.randint(-HEIGHT, 0),
               'speed': random.choice([1, 2]),  # integer speed
               'size': random.randint(1, 2)} for _ in range(70)]

# ===============================================================
# TYPEWRITER ENGINE — fixed-step (30 FPS), Undertale-like pacing
# ===============================================================
# Pacing: ~15 cps base (1 char/2 frames), pauses after punctuation
BASE_INTERVAL_FRAMES = 2
PAUSE_FRAMES = {
    ',': 4, ';': 4, ':': 4, '-': 3,
    '.': 8, '!': 8, '?': 8, '…': 8
}
BEEP_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

# Per-page state
visible_chars = 0          # how many characters of the current page are revealed
frame_accum = 0            # counts frames to next char
punct_pause = 0            # additional frames to wait after punctuation
beep_cooldown = 0          # cooldown frames to avoid audio spam

def reset_typewriter():
    global visible_chars, frame_accum, punct_pause, beep_cooldown
    visible_chars = 0
    frame_accum = 0
    punct_pause = 0
    beep_cooldown = 0

reset_typewriter()

# ===============================================================
# DRAW HELPERS
# ===============================================================
def draw_background():
    # Sky gradient (top half)
    for y in range(HEIGHT // 2):
        r = y / (HEIGHT // 2)
        color = (int(10 + 40*r), int(10 + 60*r), int(30 + 90*r))
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
        pygame.draw.circle(screen, SNOW, (int(f['x']), int(f['y'])), f['size'])

def draw_dialogue_box():
    # Box
    pygame.draw.rect(screen, (20, 20, 40), BOX, border_radius=6)
    pygame.draw.rect(screen, WHITE, BOX, 2, border_radius=6)

def draw_page_text(page_text):
    # Render only the visible substring (typewriter effect)
    visible = page_text[:visible_chars]
    lines = visible.split('\n')
    x = BOX.left + 10
    y = BOX.top + 10
    for line in lines:
        if line == "":
            y += LINE_HEIGHT
            continue
        surf = font_dialogue.render(line, True, WHITE)
        screen.blit(surf, (x, y))
        y += LINE_HEIGHT

def draw_continue_arrow(page_text_fully_revealed):
    # Undertale-like little ▼ caret (blink)
    if not page_text_fully_revealed:
        return
    if (pygame.time.get_ticks() // 400) % 2 == 0:
        cx = BOX.right - 20
        cy = BOX.bottom - 16
        pygame.draw.polygon(screen, WHITE, [(cx-6, cy-4), (cx+6, cy-4), (cx, cy+6)])

def draw_cursor_after_text(page_text):
    # Draw small block at the end of currently revealed text (blink)
    if (pygame.time.get_ticks() // 300) % 2 == 0:
        # compute end position
        before = page_text[:visible_chars]
        lines = before.split('\n')
        last_line = lines[-1] if lines else ""
        x = BOX.left + 10 + font_dialogue.size(last_line)[0] + 2
        y = BOX.top + 10 + LINE_HEIGHT * (len(lines)-1)
        pygame.draw.rect(screen, WHITE, (x, y, 8, 2))

def draw_victory():
    screen.fill(BLACK)
    lines = ["VICTORY ACHIEVED", "", "You showed mercy to Sans.", "", "Press R to play again"]
    y = HEIGHT // 2 - len(lines)*15
    for line in lines:
        color = (0,255,0) if "VICTORY" in line else WHITE
        txt = font_dialogue.render(line, True, color)
        screen.blit(txt, (WIDTH//2 - txt.get_width()//2, y))
        y += 30

# ===============================================================
# MAIN LOOP — strict 30 FPS fixed-step
# ===============================================================
clock = pygame.time.Clock()
running = True

while running:
    dt_ms = clock.tick(30)  # lock to 30 to match Undertale
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

    update_input()
    if esc_just_pressed:
        running = False

    # STATE: DIALOGUE
    if game_state == STATE_DIALOGUE:
        page_text = PAGES[page_idx]

        # ---- Typewriter update (fixed frames) ----
        # if Z is held and text is printing, go fast (≈ 3 chars per frame)
        fast = z_pressed and visible_chars < len(page_text)

        # decrement timers
        global_frame_advance = 1  # always 1 per frame (fixed step)
        if beep_cooldown > 0: beep_cooldown -= global_frame_advance
        if punct_pause > 0:
            punct_pause -= global_frame_advance
        else:
            frame_accum += global_frame_advance
            interval = 0 if fast else BASE_INTERVAL_FRAMES
            # reveal characters if interval reached
            if frame_accum >= max(1, interval):
                step = 3 if fast else 1
                # reveal up to 'step' characters this frame
                for _ in range(step):
                    if visible_chars < len(page_text):
                        ch = page_text[visible_chars]
                        visible_chars += 1
                        # punctuation pauses (ignored if fast)
                        if not fast and ch in PAUSE_FRAMES:
                            punct_pause = PAUSE_FRAMES[ch]
                            break  # pause immediately after showing this char
                        # beep on "voice" chars, throttle a little
                        if ch in BEEP_CHARS and beep_cooldown <= 0:
                            type_blip.play()
                            beep_cooldown = 2
                    else:
                        break
                frame_accum = 0

        # Z interactions
        if z_just_pressed:
            if visible_chars < len(page_text):
                # first press while printing => jump to end (classic feel)
                visible_chars = len(page_text)
                punct_pause = 0
            else:
                # advance to next page
                page_idx += 1
                if page_idx >= len(PAGES):
                    game_state = STATE_VICTORY
                else:
                    reset_typewriter()

        # R restart
        if r_just_pressed:
            page_idx = 0
            reset_typewriter()

    elif game_state == STATE_VICTORY:
        if r_just_pressed:
            page_idx = 0
            reset_typewriter()
            game_state = STATE_DIALOGUE

    # ---------------- DRAW ----------------
    draw_background()
    update_snow()

    # Sans sprite with tiny integer sway
    sway = int(round(math.sin(pygame.time.get_ticks() / 500.0) * 2))
    screen.blit(sans_sprite, (WIDTH//2 - 50 + sway, 60))

    if game_state == STATE_DIALOGUE:
        draw_dialogue_box()
        current_text = PAGES[page_idx]
        draw_page_text(current_text)
        draw_cursor_after_text(current_text)
        draw_continue_arrow(visible_chars >= len(current_text))
    else:
        draw_victory()

    pygame.display.flip()

pygame.quit()
