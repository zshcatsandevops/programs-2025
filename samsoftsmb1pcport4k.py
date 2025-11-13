import pygame, sys, math, random
pygame.init()

SCREEN_W, SCREEN_H = 800, 480
TILE = 32
FPS = 60

# COLORS
SKY = (92,148,252)
GROUND = (188,148,92)
BRICK = (200,76,12)
BLOCK = (252,156,0)
PIPE_GREEN = (80,200,80)
ENEMY_RED = (220,40,40)
COIN_GOLD = (255,210,80)
MARIO_COLOR = (240,80,40)

screen = pygame.display.set_mode((SCREEN_W,SCREEN_H))
clock = pygame.time.Clock()
pygame.display.set_caption("Ultra SMB1 – Samsoft Engine")

# --------------------------------------------------
# PLAYER
# --------------------------------------------------
class Player:
    def __init__(self,x,y):
        self.x = x; self.y = y
        self.vx = 0; self.vy = 0
        self.on_ground = False
        self.width = TILE; self.height = TILE

    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self, tiles):
        keys = pygame.key.get_pressed()
        speed = 4.2

        if keys[pygame.K_LEFT]: self.vx -= 0.5
        if keys[pygame.K_RIGHT]: self.vx += 0.5
        if not(keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]): self.vx *= 0.8
        self.vx = max(-speed, min(speed, self.vx))

        if keys[pygame.K_SPACE] and self.on_ground:
            self.vy = -11

        self.vy += 0.5
        self.vy = min(self.vy, 15)

        self.x += self.vx
        self.collide(self.vx,0,tiles)

        self.y += self.vy
        self.on_ground = False
        self.collide(0,self.vy,tiles)

    def collide(self, vx, vy, tiles):
        r = self.rect()
        for t in tiles:
            if r.colliderect(t):
                if vx > 0:
                    self.x = t.left - self.width
                    self.vx = 0
                if vx < 0:
                    self.x = t.right
                    self.vx = 0
                if vy > 0:
                    self.y = t.top - self.height
                    self.vy = 0
                    self.on_ground = True
                if vy < 0:
                    self.y = t.bottom
                    self.vy = 0

    def draw(self, camx):
        pygame.draw.rect(screen, MARIO_COLOR, (self.x - camx, self.y, self.width, self.height))

# --------------------------------------------------
# MAIN MENU
# --------------------------------------------------
class MainMenu:
    def __init__(self):
        self.title_font = pygame.font.SysFont("arial", 48)
        self.sub_font = pygame.font.SysFont("arial", 32)
        self.blink = 0

    def update(self):
        self.blink = (self.blink + 1) % 60

    def draw(self):
        screen.fill((0,0,0))
        title = self.title_font.render("ULTRA SMB1 – SAMSOFT", True, (255,255,255))
        screen.blit(title,(SCREEN_W//2 - title.get_width()//2, 150))
        if self.blink < 30:
            press = self.sub_font.render("PRESS ENTER", True, (255,255,0))
            screen.blit(press,(SCREEN_W//2 - press.get_width()//2, 260))

# --------------------------------------------------
# LEVEL
# --------------------------------------------------
class Level:
    def __init__(self, layout):
        self.layout = layout
        self.tiles = []
        self.player = Player(64, 64)
        self.camx = 0
        self.parse()

    def parse(self):
        self.tiles.clear()
        for y,row in enumerate(self.layout):
            for x,ch in enumerate(row):
                if ch == "X":
                    self.tiles.append(pygame.Rect(x*TILE, y*TILE, TILE, TILE))

    def update(self):
        self.player.update(self.tiles)
        self.camx = max(0, self.player.x - SCREEN_W//2)

    def draw(self):
        screen.fill(SKY)
        for t in self.tiles:
            pygame.draw.rect(screen, GROUND, (t.x - self.camx, t.y, TILE, TILE))
        self.player.draw(self.camx)

# --------------------------------------------------
# SAMPLE TEST LEVEL
# --------------------------------------------------
TEST_LEVEL = [
    "P             C         G                 ",
    "                                                ",
    "                                                ",
    "                                                ",
    "                                                ",
    "                                                ",
    "      B B B                                     ",
    "                                                ",
    "                                                ",
    "XXXXXXXXXXXX                XXXXXXXX           ",
    "                                                ",
    "                                                ",
    "                                                ",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
]

# Fix player spawn from 'P'
spawn_x = 64
spawn_y = 64
for y,row in enumerate(TEST_LEVEL):
    for x,ch in enumerate(row):
        if ch == 'P':
            spawn_x, spawn_y = x*TILE, y*TILE

level = Level(TEST_LEVEL)
level.player.x = spawn_x
level.player.y = spawn_y

# --------------------------------------------------
# MAIN LOOP
# --------------------------------------------------
MENU = MainMenu()
STATE = "MENU"

while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit(); sys.exit()

    keys = pygame.key.get_pressed()

    if STATE == "MENU":
        MENU.update()
        if keys[pygame.K_RETURN]:
            STATE = "GAME"
        MENU.draw()

    elif STATE == "GAME":
        level.update()
        level.draw()

    pygame.display.flip()
    clock.tick(FPS)
