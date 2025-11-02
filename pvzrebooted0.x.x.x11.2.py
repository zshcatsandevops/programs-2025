import pygame, random, sys

# ───────── CONFIG ─────────
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 560
GRID_ROWS, GRID_COLS, CELL_SIZE = 5, 9, 80
GAMEOVER = False

WHITE, BLACK = (255,255,255), (0,0,0)
GREEN, RED, YELLOW, GOLD = (0,255,0), (255,0,0), (255,255,0), (255,215,0)

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Plants vs Zombies")

# ───────── CLASSES ─────────
class Plant(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
        self.hp, self.live = 200, True

class Sunflower(Plant):
    price = 50
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image = pygame.Surface((CELL_SIZE, CELL_SIZE))
        self.image.fill(YELLOW)
        self.sun_timer = 0
        self.ready_for_sun = False

    def update(self):
        self.sun_timer += 1
        self.ready_for_sun = False
        if self.sun_timer > 300:
            self.sun_timer = 0
            self.ready_for_sun = True

class PeaShooter(Plant):
    price = 100
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image = pygame.Surface((CELL_SIZE, CELL_SIZE))
        self.image.fill(GREEN)
        self.shot_count = 0
        self.ready_to_shoot = False
    def update(self):
        self.shot_count += 1
        self.ready_to_shoot = False
        if self.shot_count > 60:
            self.shot_count = 0
            self.ready_to_shoot = True

class PeaBullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((10, 10))
        self.image.fill((0,128,0))
        self.rect = self.image.get_rect(center=(x+CELL_SIZE//2, y+CELL_SIZE//2))
        self.speed, self.damage, self.live = 10, 50, True
    def update(self):
        self.rect.x += self.speed
        if self.rect.x > SCREEN_WIDTH: self.live = False

class Zombie(pygame.sprite.Sprite):
    def __init__(self, row):
        super().__init__()
        self.image = pygame.Surface((CELL_SIZE, CELL_SIZE))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.x = SCREEN_WIDTH
        self.rect.y = row * (SCREEN_HEIGHT // GRID_ROWS)
        self.hp, self.speed, self.live = 200, 1, True
    def update(self):
        self.rect.x -= self.speed
        if self.rect.x < 0:
            global GAMEOVER
            GAMEOVER = True

class Sun(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((20,20))
        self.image.fill(GOLD)
        self.rect = self.image.get_rect(center=(x+CELL_SIZE//2, y+CELL_SIZE//2))
        self.live = True

class MapCell:
    def __init__(self, position):
        self.position, self.can_grow, self.plant = position, True, None

# ───────── MAIN GAME ─────────
class MainGame:
    def __init__(self):
        self.window = screen
        self.plant_list = pygame.sprite.Group()
        self.zombie_list = pygame.sprite.Group()
        self.bullet_list = pygame.sprite.Group()
        self.sun_list = pygame.sprite.Group()
        self.money = 200
        self.selected_plant = None
        self.level = 1
        self.map_grid = [[MapCell((j * CELL_SIZE, i * (SCREEN_HEIGHT // GRID_ROWS)))
                          for j in range(GRID_COLS)] for i in range(GRID_ROWS)]
        self.zombie_spawn_timer = 0
        self.level_data = {1:{'zombies':5,'interval':300},2:{'zombies':10,'interval':240}}

    def draw_grid(self):
        for r in range(GRID_ROWS+1):
            pygame.draw.line(self.window, BLACK, (0,r*(SCREEN_HEIGHT//GRID_ROWS)),
                             (SCREEN_WIDTH,r*(SCREEN_HEIGHT//GRID_ROWS)))
        for c in range(GRID_COLS+1):
            pygame.draw.line(self.window, BLACK, (c*CELL_SIZE,0),(c*CELL_SIZE,SCREEN_HEIGHT))

    def spawn_zombie(self):
        row = random.randint(0, GRID_ROWS-1)
        self.zombie_list.add(Zombie(row))

    def deal_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1: self.selected_plant = Sunflower
                if event.key == pygame.K_2: self.selected_plant = PeaShooter
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                # click suns
                for sun in list(self.sun_list):
                    if sun.rect.collidepoint(x,y):
                        sun.kill()
                        self.money += 25
                # place plants
                col, row = x//CELL_SIZE, y//(SCREEN_HEIGHT//GRID_ROWS)
                if 0 <= row < GRID_ROWS and 0 <= col < GRID_COLS:
                    cell = self.map_grid[row][col]
                    if cell.can_grow and self.selected_plant and self.money >= self.selected_plant.price:
                        plant = self.selected_plant(cell.position[0], cell.position[1])
                        self.plant_list.add(plant)
                        cell.plant, cell.can_grow = plant, False
                        self.money -= self.selected_plant.price

    def update_game(self):
        for plant in list(self.plant_list):
            if plant.live:
                plant.update()
                if isinstance(plant, Sunflower) and plant.ready_for_sun:
                    self.sun_list.add(Sun(plant.rect.x, plant.rect.y))
                elif isinstance(plant, PeaShooter) and plant.ready_to_shoot:
                    self.bullet_list.add(PeaBullet(plant.rect.x, plant.rect.y))

        for bullet in list(self.bullet_list):
            if bullet.live:
                bullet.update()
                for zombie in list(self.zombie_list):
                    if pygame.sprite.collide_rect(bullet, zombie):
                        zombie.hp -= bullet.damage
                        bullet.live = False
                        bullet.kill()
                        if zombie.hp <= 0:
                            zombie.live = False
                            zombie.kill()
            else: bullet.kill()

        for zombie in list(self.zombie_list):
            if zombie.live:
                zombie.update()
                for plant in list(self.plant_list):
                    if pygame.sprite.collide_rect(zombie, plant):
                        plant.hp -= 10
                        if plant.hp <= 0:
                            plant.live = False
                            plant.kill()
                            r, c = zombie.rect.y // (SCREEN_HEIGHT//GRID_ROWS), zombie.rect.x // CELL_SIZE
                            if 0 <= r < GRID_ROWS and 0 <= c < GRID_COLS:
                                self.map_grid[r][c].can_grow = True

        self.zombie_spawn_timer += 1
        info = self.level_data.get(self.level, {'zombies':5,'interval':300})
        if self.zombie_spawn_timer > info['interval'] and len(self.zombie_list) < info['zombies']:
            self.zombie_spawn_timer = 0
            self.spawn_zombie()

    def draw(self):
        self.window.fill(WHITE)
        self.draw_grid()
        self.plant_list.draw(self.window)
        self.zombie_list.draw(self.window)
        self.bullet_list.draw(self.window)
        self.sun_list.draw(self.window)
        font = pygame.font.SysFont(None, 32)
        t1 = font.render(f"Sun: {self.money}", True, BLACK)
        t2 = font.render("Press 1: Sunflower ($50) | 2: Peashooter ($100)", True, BLACK)
        self.window.blit(t1, (10,10)); self.window.blit(t2, (10,40))

    def game_loop(self):
        clock = pygame.time.Clock()
        global GAMEOVER
        while not GAMEOVER:
            self.deal_events()
            self.update_game()
            self.draw()
            pygame.display.flip()
            clock.tick(60)

# ───────── MENU ─────────
def main_menu():
    font = pygame.font.SysFont(None, 48)
    start = font.render("Start", True, BLACK)
    quit_ = font.render("Exit", True, BLACK)
    start_rect = start.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
    quit_rect = quit_.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
    while True:
        screen.fill(WHITE)
        screen.blit(start, start_rect); screen.blit(quit_, quit_rect)
        pygame.display.update()
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN:
                if start_rect.collidepoint(e.pos): return True
                if quit_rect.collidepoint(e.pos): pygame.quit(); sys.exit()

# ───────── RUN ─────────
if __name__ == "__main__":
    if main_menu():
        game = MainGame()
        game.game_loop()
