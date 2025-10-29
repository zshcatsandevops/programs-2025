import pygame
import sys
import math
import random
from enum import Enum
from pygame.locals import *

# ============== INITIALIZE ==============
pygame.init()
pygame.mixer.init()

# ============== CONSTANTS ==============
WIDTH, HEIGHT = 600, 400
FPS = 60
GRID_ROWS = 5
GRID_COLS = 9
CELL_W = 50
CELL_H = 60
GRID_X = 80
GRID_Y = 80

# Colors
SKY_BLUE = (135, 206, 235)
LAWN_GREEN = (34, 139, 34)
DARK_GREEN = (0, 100, 0)
BROWN = (139, 69, 19)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GRAY = (128, 128, 128)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
BLUE = (0, 0, 255)
DARK_RED = (139, 0, 0)  # <-- fixed missing color

# Game states
class GameState(Enum):
    MENU = 1
    GAME = 2
    PAUSED = 3
    VICTORY = 4
    DEFEAT = 5
    LEVEL_SELECT = 6

# ============== WINDOW SETUP ==============
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Plants vs Zombies - Complete Edition")
clock = pygame.time.Clock()

# Fonts
pygame.font.init()
FONT_TINY = pygame.font.Font(None, 12)
FONT_SMALL = pygame.font.Font(None, 16)
FONT_MEDIUM = pygame.font.Font(None, 24)
FONT_LARGE = pygame.font.Font(None, 32)
FONT_HUGE = pygame.font.Font(None, 48)

# ============== PARTICLES ==============
class Particle:
    def __init__(self, x, y, vx, vy, color, lifetime=1.0, size=3):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = size
    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 200 * dt
        self.lifetime -= dt
        return self.lifetime > 0
    def draw(self, surface):
        alpha = self.lifetime / self.max_lifetime
        size = int(self.size * alpha)
        if size > 0:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), size)

# ============== PROJECTILES ==============
class Projectile:
    def __init__(self, x, y, damage=20, speed=200):
        self.x, self.y = x, y
        self.damage = damage
        self.speed = speed
        self.radius = 4
        self.active = True
    def update(self, dt):
        self.x += self.speed * dt
        if self.x > WIDTH:
            self.active = False
    def draw(self, surface):
        pygame.draw.circle(surface, (0, 255, 0), (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, (0, 200, 0), (int(self.x), int(self.y)), self.radius, 1)

class SnowPea(Projectile):
    def __init__(self, x, y):
        super().__init__(x, y, 20, 200)
        self.freeze_duration = 2.0
    def draw(self, surface):
        pygame.draw.circle(surface, (100, 200, 255), (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.radius, 1)

# ============== ZOMBIE ==============
class Zombie:
    def __init__(self, row, game):
        self.row = row
        self.game = game
        self.x = WIDTH
        self.y = GRID_Y + row * CELL_H + CELL_H//2
        self.hp = 200
        self.max_hp = 200
        self.speed = 15
        self.damage = 100
        self.eating = False
        self.freeze_timer = 0
        self.frozen = False
        self.radius = 12
        self.color = (100, 50, 0)
    def update(self, dt):
        if self.frozen:
            self.freeze_timer -= dt
            if self.freeze_timer <= 0:
                self.frozen = False
        speed_mult = 0.5 if self.frozen else 1.0
        if not self.eating:
            self.x -= self.speed * speed_mult * dt
            if self.x < GRID_X - 20:
                self.game.game_over()
            plant = self.game.get_plant_at_position(self.row, self.x)
            if plant:
                self.eating = True
                self.target_plant = plant
        else:
            if hasattr(self, "target_plant"):
                self.target_plant.take_damage(self.damage * dt)
                if self.target_plant.hp <= 0:
                    self.eating = False
    def take_damage(self, dmg):
        self.hp -= dmg
        if self.hp <= 0:
            if self in self.game.zombies:
                self.game.zombies.remove(self)
                for _ in range(5):
                    self.game.particles.append(Particle(self.x, self.y, random.uniform(-50,50), random.uniform(-80,-30), self.color, 0.5))
    def freeze(self, t):
        self.frozen = True
        self.freeze_timer = t
    def draw(self, s):
        c = (100, 150, 200) if self.frozen else self.color
        pygame.draw.circle(s, c, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(s, BLACK, (int(self.x), int(self.y)), self.radius, 2)
        if self.hp < self.max_hp:
            bw, bh = 25, 3
            pygame.draw.rect(s, RED, (self.x - bw//2, self.y - 20, bw, bh))
            pygame.draw.rect(s, (0,255,0), (self.x - bw//2, self.y - 20, bw*(self.hp/self.max_hp), bh))

# ============== PLANT (simplified for fix demo) ==============
class Plant:
    def __init__(self, row, col, game):
        self.row, self.col = row, col
        self.game = game
        self.x = GRID_X + col*CELL_W + CELL_W//2
        self.y = GRID_Y + row*CELL_H + CELL_H//2
        self.hp = 100
        self.color = DARK_GREEN
        self.radius = 15
        self.shoot_timer = 0
        self.shoot_interval = 1.5
    def update(self, dt):
        self.shoot_timer += dt
    def take_damage(self, dmg):
        self.hp -= dmg
        if self.hp <= 0:
            self.game.remove_plant(self.row, self.col)
    def draw(self, s):
        pygame.draw.circle(s, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(s, BLACK, (int(self.x), int(self.y)), self.radius, 2)

class Peashooter(Plant):
    def __init__(self, row, col, game):
        super().__init__(row, col, game)
        self.color = (0,200,0)
        self.cost = 100
    def update(self, dt):
        super().update(dt)
        if self.shoot_timer >= self.shoot_interval:
            if self.game.has_zombie_in_row(self.row):
                self.game.projectiles.append(Projectile(self.x+10, self.y))
                self.shoot_timer = 0

# ============== SUN ==============
class Sun:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.radius = 15
        self.value = 25
        self.collected = False
        self.lifetime = 10
    def update(self, dt):
        self.lifetime -= dt
        return self.lifetime > 0 and not self.collected
    def collect(self): self.collected = True; return self.value
    def draw(self, s):
        pygame.draw.circle(s, YELLOW, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(s, ORANGE, (int(self.x), int(self.y)), self.radius, 2)

# ============== GAME CORE ==============
class PvZGame:
    def __init__(self):
        self.state = GameState.MENU
        self.score = 0
        self.sun = 50
        self.plants = []
        self.zombies = []
        self.projectiles = []
        self.suns = []
        self.particles = []
        self.selected_plant = None
        self.plant_classes = [Peashooter]
        self.plant_cooldowns = [0]
        self.wave_timer = 0
        self.wave_interval = 10
        self.wave_count = 0
        self.max_waves = 3
        self.menu_selection = 0
        self.menu_options = ["Start Game","Quit"]
    def start_level(self):
        self.state = GameState.GAME
        self.zombies.clear(); self.plants.clear()
        self.projectiles.clear(); self.particles.clear()
        self.suns.clear(); self.wave_count = 0
    def game_over(self): self.state = GameState.DEFEAT
    def has_zombie_in_row(self,row): return any(z.row==row for z in self.zombies)
    def remove_plant(self,row,col):
        for p in self.plants[:]:
            if p.row==row and p.col==col:
                self.plants.remove(p)
    def spawn_wave(self):
        self.wave_count+=1
        for _ in range(3): self.zombies.append(Zombie(random.randint(0,GRID_ROWS-1), self))
    def update(self,dt):
        if self.state!=GameState.GAME: return
        self.wave_timer+=dt
        if self.wave_timer>=self.wave_interval and self.wave_count<self.max_waves:
            self.spawn_wave(); self.wave_timer=0
        for p in self.plants[:]: p.update(dt)
        for z in self.zombies[:]: z.update(dt)
        for pr in self.projectiles[:]:
            pr.update(dt)
            if not pr.active: self.projectiles.remove(pr); continue
            for z in self.zombies:
                if z.row ==  self.row_from_y(pr.y) and abs(z.x - pr.x) < z.radius + pr.radius:
                    z.take_damage(pr.damage)
                    if isinstance(pr, SnowPea): z.freeze(pr.freeze_duration)
                    pr.active=False; break
        for s in self.suns[:]:
            if not s.update(dt): self.suns.remove(s)
        for p in self.particles[:]:
            if not p.update(dt): self.particles.remove(p)
        if self.wave_count>=self.max_waves and not self.zombies:
            self.state=GameState.VICTORY
    def row_from_y(self,y): return max(0,min(GRID_ROWS-1,int((y-GRID_Y)/CELL_H)))
    def handle_click(self,mx,my):
        for sun in self.suns:
            if math.dist((mx,my),(sun.x,sun.y))<sun.radius and not sun.collected:
                self.sun+=sun.collect(); return
        if self.selected_plant:
            col=int((mx-GRID_X)/CELL_W); row=int((my-GRID_Y)/CELL_H)
            if 0<=row<GRID_ROWS and 0<=col<GRID_COLS:
                self.plants.append(self.selected_plant(row,col,self))
                self.sun-=self.selected_plant(0,0,self).cost
                self.selected_plant=None
    def draw(self,s):
        if self.state==GameState.MENU: self.draw_menu(s)
        elif self.state==GameState.GAME: self.draw_game(s)
        elif self.state==GameState.VICTORY: self.draw_victory(s)
        elif self.state==GameState.DEFEAT: self.draw_defeat(s)
    def draw_menu(self,s):
        s.fill(SKY_BLUE)
        title=FONT_HUGE.render("PLANTS vs ZOMBIES",True,DARK_GREEN)
        s.blit(title,(WIDTH//2-title.get_width()//2,60))
        for i,opt in enumerate(self.menu_options):
            color=WHITE if i==self.menu_selection else GRAY
            if i==self.menu_selection:
                pygame.draw.rect(s,LAWN_GREEN,(WIDTH//2-80,150+i*40,160,35))
            t=FONT_MEDIUM.render(opt,True,color)
            s.blit(t,(WIDTH//2-t.get_width()//2,155+i*40))
    def draw_game(self,s):
        s.fill(SKY_BLUE)
        for r in range(GRID_ROWS):
            pygame.draw.rect(s,LAWN_GREEN if r%2==0 else (40,150,40),(GRID_X,GRID_Y+r*CELL_H,GRID_COLS*CELL_W,CELL_H))
        for p in self.plants: p.draw(s)
        for z in self.zombies: z.draw(s)
        for pr in self.projectiles: pr.draw(s)
        for sun in self.suns: sun.draw(s)
        for pt in self.particles: pt.draw(s)
        txt=FONT_SMALL.render(f"Sun: {self.sun}",True,BLACK); s.blit(txt,(10,10))
    def draw_victory(self,s):
        s.fill(LAWN_GREEN)
        t=FONT_HUGE.render("VICTORY!",True,YELLOW)
        s.blit(t,(WIDTH//2-t.get_width()//2,HEIGHT//2-40))
        cont=FONT_SMALL.render("Press SPACE for menu",True,BLACK)
        s.blit(cont,(WIDTH//2-cont.get_width()//2,HEIGHT//2+20))
    def draw_defeat(self,s):
        s.fill(DARK_RED)
        t=FONT_HUGE.render("ZOMBIES ATE YOUR BRAINS!",True,RED)
        s.blit(t,(WIDTH//2-t.get_width()//2,HEIGHT//2-40))
        cont=FONT_SMALL.render("Press SPACE to retry",True,WHITE)
        s.blit(cont,(WIDTH//2-cont.get_width()//2,HEIGHT//2+20))

# ============== MAIN LOOP ==============
def main():
    game=PvZGame()
    run=True
    while run:
        dt=clock.tick(FPS)/1000
        for e in pygame.event.get():
            if e.type==QUIT:
                run=False
            elif e.type==KEYDOWN:
                if game.state==GameState.MENU:
                    if e.key==K_UP: game.menu_selection=(game.menu_selection-1)%len(game.menu_options)
                    elif e.key==K_DOWN: game.menu_selection=(game.menu_selection+1)%len(game.menu_options)
                    elif e.key in (K_RETURN,K_SPACE):
                        if game.menu_selection==0: game.start_level()
                        elif game.menu_selection==1: run=False
                elif game.state==GameState.VICTORY:
                    if e.key==K_SPACE: game.state=GameState.MENU
                elif game.state==GameState.DEFEAT:
                    if e.key==K_SPACE: game.start_level()
            elif e.type==MOUSEBUTTONDOWN and game.state==GameState.GAME:
                game.handle_click(*e.pos)
        game.update(dt)
        game.draw(screen)
        pygame.display.flip()
    pygame.quit(); sys.exit(0)

if __name__=="__main__":
    main()
