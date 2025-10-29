import pygame, sys, random, math

# ====== INIT ======
pygame.init()
pygame.font.init()
WIDTH, HEIGHT = 1365, 768
FPS = 60
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Plants vs Zombies: Redone Volume AI")
clock = pygame.time.Clock()

# ====== COLORS ======
SKY_BLUE = (100, 200, 255)
PURPLE_NIGHT = (180, 80, 220)
LAWN_GREEN = (100, 190, 40)
PATH_GRAY = (80, 80, 80)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BROWN = (139, 69, 19)
GREEN = (0, 200, 0)
DARK_GREEN = (0, 100, 0)
YELLOW = (255, 230, 40)
RED = (220, 60, 60)
ORANGE = (255, 130, 0)
PURPLE = (130, 0, 200)

# ====== TEXT ======
title_font = pygame.font.SysFont("impact", 96)
sub_font = pygame.font.SysFont("arialblack", 36)
tiny_font = pygame.font.SysFont("arial", 20)

# ====== BACKGROUND PAINT ======
def draw_gradient(surf, color_top, color_bottom):
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = color_top[0]*(1-ratio) + color_bottom[0]*ratio
        g = color_top[1]*(1-ratio) + color_bottom[1]*ratio
        b = color_top[2]*(1-ratio) + color_bottom[2]*ratio
        pygame.draw.line(surf, (int(r), int(g), int(b)), (0, y), (WIDTH, y))

# ====== SIMPLE SHAPES ======
def draw_sunflower(x, y):
    # petals
    for i in range(12):
        angle = i * math.pi/6
        px = x + math.cos(angle)*45
        py = y + math.sin(angle)*45
        pygame.draw.circle(screen, ORANGE, (int(px), int(py)), 20)
    # face
    pygame.draw.circle(screen, (150,100,40), (x, y), 35)
    pygame.draw.circle(screen, BLACK, (x-10, y-10), 6)
    pygame.draw.circle(screen, BLACK, (x+10, y-10), 6)
    pygame.draw.arc(screen, BLACK, (x-20, y-10, 40, 40), 0, math.pi, 2)

def draw_peashooter(x, y):
    pygame.draw.rect(screen, DARK_GREEN, (x-15, y, 30, 60))
    pygame.draw.circle(screen, GREEN, (x, y-20), 30)
    pygame.draw.circle(screen, BLACK, (x+10, y-25), 5)

def draw_wallnut(x, y):
    pygame.draw.ellipse(screen, BROWN, (x-30, y, 60, 80))
    pygame.draw.circle(screen, BLACK, (x-10, y+25), 6)
    pygame.draw.circle(screen, BLACK, (x+10, y+25), 6)

def draw_cactus(x, y):
    pygame.draw.rect(screen, (0,150,0), (x-15, y, 30, 100), border_radius=8)
    for i in range(8):
        px = x + random.choice([-20,20])
        py = y + i*12
        pygame.draw.circle(screen, RED, (px, py), 4)

def draw_zombie(x, y, tone):
    body = pygame.Surface((50,100), pygame.SRCALPHA)
    pygame.draw.rect(body, (tone, tone//2, tone), (0,20,50,80))
    pygame.draw.circle(body, (tone+20, tone+20, tone+20), (25,10), 15)
    screen.blit(body, (x,y))

# ====== ANIM OBJECTS ======
zombies = [{"x":WIDTH - i*200, "y":random.randint(400,600), "tone":random.randint(60,120)} for i in range(6)]
clouds = [{"x":random.randint(0,WIDTH), "y":random.randint(0,200), "w":random.randint(100,200)} for _ in range(5)]

# ====== BUTTON ======
def draw_button(text, rect, hover=False):
    color = (255,255,180) if hover else (200,200,120)
    pygame.draw.rect(screen, color, rect, border_radius=12)
    label = sub_font.render(text, True, BLACK)
    screen.blit(label, label.get_rect(center=rect.center))

# ====== LOOP ======
running = True
while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if e.type == pygame.MOUSEBUTTONDOWN:
            if start_btn.collidepoint(e.pos):
                print("Game start!")  # hook to start actual game later

    # Background gradient
    draw_gradient(screen, SKY_BLUE, PURPLE_NIGHT)

    # Lawn & path
    pygame.draw.rect(screen, LAWN_GREEN, (0, 500, WIDTH, 268))
    pygame.draw.rect(screen, PATH_GRAY, (WIDTH//2, 500, WIDTH//2, 268))

    # Clouds
    for c in clouds:
        pygame.draw.ellipse(screen, WHITE, (c["x"], c["y"], c["w"], 60))
        c["x"] -= 0.5
        if c["x"] + c["w"] < 0: c["x"] = WIDTH

    # Plants
    draw_cactus(450, 500)
    draw_wallnut(350, 520)
    draw_peashooter(250, 520)
    draw_sunflower(150, 520)

    # Zombies
    for z in zombies:
        draw_zombie(int(z["x"]), int(z["y"]), z["tone"])
        z["x"] -= 0.7
        if z["x"] < -60: 
            z["x"] = WIDTH + random.randint(0,300)
            z["y"] = random.randint(400,600)
            z["tone"] = random.randint(60,120)

    # Title text
    title1 = title_font.render("PLANTS", True, (40,255,40))
    title2 = title_font.render("vs", True, WHITE)
    title3 = title_font.render("ZOMBIES", True, (160,80,40))
    screen.blit(title1, (WIDTH//2 - 480, 80))
    screen.blit(title2, (WIDTH//2 - 130, 120))
    screen.blit(title3, (WIDTH//2 - 50, 80))

    subtitle = sub_font.render("REDONE  •  VOLUME AI", True, YELLOW)
    screen.blit(subtitle, (WIDTH//2 - 250, 200))

    # Button
    start_btn = pygame.Rect(WIDTH//2 - 150, 650, 300, 60)
    draw_button("CLICK TO START!", start_btn, start_btn.collidepoint(pygame.mouse.get_pos()))

    # Footer
    footer = tiny_font.render("Pre-Release Build — Work in Progress (Procedural Title Screen, No PNGs)", True, WHITE)
    screen.blit(footer, (20, HEIGHT - 30))

    pygame.display.flip()
    clock.tick(FPS)
