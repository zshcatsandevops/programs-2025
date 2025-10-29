#!/usr/bin/env python3
import pygame, sys, random, math
from pygame.locals import *
pygame.init()

# === CONFIG ===
WIDTH, HEIGHT, FPS = 1024, 768, 60
GRID_X, GRID_Y, CELL_W, CELL_H, ROWS, COLS = 100, 100, 80, 100, 5, 9
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("PVZ: Replanted - Full Remaster [C] Samsoft AI Edition (Procedural HD + Roguelike)")
clock = pygame.time.Clock()

# === COLORS ===
SKY = (135, 206, 235)
GRASS = (34, 139, 34)
BROWN = (139, 69, 19)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
DARK_GREEN = (0, 100, 0)
GRAY = (128, 128, 128)
BLACK = (0, 0, 0)
ZOMBIE_SKIN = (150, 100, 50)
PLANT_POT = (100, 50, 0)
SHADOW = (0, 0, 0, 64)
GOLD = (255, 215, 0)
NIGHT_SKY = (0, 0, 50)
WATER = (0, 100, 200)
PVZ3_PINK_ACCENT = (255, 182, 193)
PVZ3_PURPLE_HAZE = (147, 112, 219)
BLOOM_YELLOW = (255, 255, 200, 128)
GLOW_GREEN = (200, 255, 200, 64)
ROGUELIKE_HAZE = (255, 100, 100, 32)
UPSAMPLE_SCALE = 2
UPSAMPLE_W, UPSAMPLE_H = WIDTH * UPSAMPLE_SCALE, HEIGHT * UPSAMPLE_SCALE
upscale_surf = pygame.Surface((UPSAMPLE_W, UPSAMPLE_H))

# === FULL PLANT STATS ===
plant_stats = {
    'Peashooter': {'cost':100, 'cooldown':1.25, 'health':300, 'dmg':20, 'type':'shooter'},
    'Sunflower': {'cost':50, 'cooldown':24, 'health':300, 'sun':25, 'type':'sun'},
    'Cherry Bomb': {'cost':150, 'cooldown':50, 'health':300, 'dmg':1800, 'aoe':3, 'type':'bomb'},
    'Wall-nut': {'cost':50, 'cooldown':30, 'health':4000, 'type':'tank'},
    'Potato Mine': {'cost':25, 'cooldown':20, 'health':300, 'dmg':1800, 'delay':4, 'type':'mine'},
    'Snow Pea': {'cost':175, 'cooldown':1.25, 'health':300, 'dmg':20, 'slow':0.5, 'type':'shooter'},
    'Chomper': {'cost':150, 'cooldown':40, 'health':300, 'dmg':1800, 'chew':8, 'type':'chomp'},
    'Repeater': {'cost':200, 'cooldown':1.25, 'health':300, 'dmg':40, 'type':'shooter'},
    'Puff-shroom': {'cost':0, 'cooldown':1.25, 'health':300, 'dmg':20, 'range':3, 'type':'shroom'},
    'Sun-shroom': {'cost':25, 'cooldown':24, 'health':300, 'sun_small':15, 'sun_large':25, 'type':'sun'},
    'Fume-shroom': {'cost':75, 'cooldown':6, 'health':300, 'dmg':150, 'aoe':2, 'type':'shroom'},
    'Grave Buster': {'cost':75, 'cooldown':15, 'health':300, 'type':'utility'},
    'Hypno-shroom': {'cost':75, 'cooldown':30, 'health':300, 'type':'control'},
    'Scaredy-shroom': {'cost':25, 'cooldown':1.25, 'health':300, 'dmg':40, 'scare_range':3, 'type':'shroom'},
    'Ice-shroom': {'cost':75, 'cooldown':50, 'health':300, 'freeze':10, 'type':'shroom'},
    'Doom-shroom': {'cost':125, 'cooldown':50, 'health':300, 'dmg':2400, 'aoe':5, 'type':'bomb'},
    'Lily Pad': {'cost':0, 'cooldown':7.5, 'health':300, 'type':'aquatic'},
    'Squash': {'cost':50, 'cooldown':30, 'health':300, 'dmg':2400, 'type':'squash'},
    'Threepeater': {'cost':325, 'cooldown':1.25, 'health':300, 'dmg':60, 'type':'shooter'},
    'Tangle Kelp': {'cost':25, 'cooldown':20, 'health':300, 'dmg':1800, 'type':'aquatic'},
    'Jalapeno': {'cost':125, 'cooldown':50, 'health':300, 'dmg':1800, 'row_clear':True, 'type':'bomb'},
    'Spikeweed': {'cost':100, 'cooldown':7.5, 'health':300, 'dmg':40, 'crush':True, 'type':'ground'},
    'Torchwood': {'cost':175, 'cooldown':7.5, 'health':300, 'fire':True, 'type':'upgrade'},
    'Tall-nut': {'cost':125, 'cooldown':30, 'health':8000, 'type':'tank'},
    'Sea-shroom': {'cost':0, 'cooldown':1.25, 'health':300, 'dmg':75, 'range':3.5, 'type':'shroom'},
    'Plantern': {'cost':25, 'cooldown':7.5, 'health':300, 'reveal':True, 'type':'utility'},
    'Cactus': {'cost':125, 'cooldown':7.5, 'health':300, 'dmg':40, 'balloon':True, 'type':'shooter'},
    'Blover': {'cost':100, 'cooldown':7.5, 'health':300, 'fog_clear':True, 'type':'utility'},
    'Split Pea': {'cost':125, 'cooldown':1.25, 'health':300, 'dmg':40, 'dual':True, 'type':'shooter'},
    'Starfruit': {'cost':125, 'cooldown':1.25, 'health':300, 'dmg':20, 'pierce':5, 'type':'shooter'},
    'Pumpkin': {'cost':125, 'cooldown':30, 'health':4000, 'protect':True, 'type':'tank'},
    'Magnet-shroom': {'cost':100, 'cooldown':15, 'health':300, 'steal_metal':True, 'type':'utility'},
    'Cabbage-pult': {'cost':100, 'cooldown':1.5, 'health':300, 'dmg':35, 'lob':True, 'type':'lobber'},
    'Flower Pot': {'cost':25, 'cooldown':7.5, 'health':300, 'roof':True, 'type':'utility'},
    'Kernel-pult': {'cost':100, 'cooldown':1.5, 'health':300, 'dmg':40, 'stun':True, 'lob':True, 'type':'lobber'},
    'Coffee Bean': {'cost':75, 'cooldown':7.5, 'health':300, 'wake':True, 'type':'utility'},
    'Garlic': {'cost':50, 'cooldown':7.5, 'health':300, 'divert':True, 'type':'utility'},
    'Umbrella Leaf': {'cost':100, 'cooldown':7.5, 'health':300, 'block':True, 'type':'utility'},
    'Marigold': {'cost':50, 'cooldown':24, 'health':300, 'gold':10, 'type':'sun'},
    'Melon-pult': {'cost':300, 'cooldown':1.5, 'health':300, 'dmg':240, 'splash':True, 'lob':True, 'type':'lobber'},
}

# === FULL ZOMBIE STATS ===
zombie_stats = {
    'Zombie': {'health':100, 'speed':0.5, 'type':'basic'},
    'Flag Zombie': {'health':100, 'speed':0.5, 'wave_leader':True, 'type':'basic'},
    'Conehead Zombie': {'health':460, 'speed':0.5, 'shield':360, 'type':'shield'},
    'Pole Vaulting Zombie': {'health':200, 'speed':1.8, 'vault':True, 'type':'jumper'},
    'Buckethead Zombie': {'health':1100, 'speed':0.5, 'shield':1000, 'type':'shield'},
    'Newspaper Zombie': {'health':240, 'speed':0.5, 'rage_speed':2.0, 'type':'fast'},
    'Screen Door Zombie': {'health':1100, 'speed':0.5, 'shield':1000, 'type':'shield'},
    'Football Zombie': {'health':170, 'speed':1.2, 'crush':True, 'type':'tank'},
    'Dancing Zombie': {'health':120, 'speed':0.5, 'summon':True, 'type':'summoner'},
    'Backup Dancer': {'health':100, 'speed':0.5, 'type':'basic'},
    'Ducky Tube Zombie': {'health':100, 'speed':0.5, 'pool':True, 'type':'basic'},
    'Snorkel Zombie': {'health':240, 'speed':0.5, 'submerge':True, 'type':'pool'},
    'Zomboni': {'health':680, 'speed':0.5, 'crush':True, 'ice_trail':True, 'type':'vehicle'},
    'Zombie Bobsled Team': {'health':300, 'speed':1.0, 'ice':True, 'type':'group'},
    'Dolphin Rider Zombie': {'health':140, 'speed':1.8, 'jump':True, 'type':'jumper'},
    'Jack-in-the-Box Zombie': {'health':240, 'speed':0.8, 'explode':True, 'type':'bomb'},
    'Balloon Zombie': {'health':100, 'speed':1.0, 'fly':True, 'type':'flyer'},
    'Digger Zombie': {'health':240, 'speed':0.5, 'tunnel':True, 'type':'stealth'},
    'Pogo Zombie': {'health':240, 'speed':1.5, 'jump':True, 'type':'jumper'},
    'Bungee Zombie': {'health':300, 'speed':0, 'steal':True, 'type':'stealth'},
    'Ladder Zombie': {'health':460, 'speed':0.5, 'ladder':True, 'type':'shield'},
    'Catapult Zombie': {'health':1000, 'speed':0.5, 'lob_zombies':True, 'type':'lobber'},
    'Gargantuar': {'health':3000, 'speed':0.4, 'smash':True, 'imp':True, 'type':'boss'},
    'Imp': {'health':100, 'speed':1.5, 'type':'basic'},
    'Dr. Zomboss': {'health':10000, 'speed':0, 'phases':3, 'aoe':True, 'type':'boss'},
}

# === LEVEL DATA (Stubbed for demo) ===
level_data = {
    "1-1": {"flags": 1, "zombies": ['Zombie'], "special": None},
    "5-10": {"flags": 3, "zombies": ['Gargantuar', 'Imp', 'Dr. Zomboss'], "special": 'boss', "phases":3, "roof": True},
    "endless": {"flags": float('inf'), "zombies": list(zombie_stats.keys()), "special": "roguelike"},
}

# === GAME STATE ===
plants = []
zombies = []
projectiles = []
suns = []
sun_bank = 50
lives = 3
wave_current = 0
waves_total = 1
game_active = True
menu_active = False
paused = False
zen_mode = False
time_elapsed = 0
selected_plant = None

# === HELPER: Quit Game ===
def quit_game():
    pygame.quit()
    sys.exit()

# === CLASSES ===
class Plant:
    def __init__(self, col, row, plant_type):
        self.col = col
        self.row = row
        self.type = plant_type
        stats = plant_stats.get(plant_type, {'health':300})
        self.health = stats['health']
        self.max_health = stats['health']
        self.anim_frame = 0
        self.recoil = 0
        self.target_zombie = None
        self.shoot_timer = stats.get('cooldown', 7.5) * FPS if 'shooter' in stats.get('type', '') else 0
        self.sun_timer = stats.get('cooldown', 24) * FPS if 'sun' in stats.get('type', '') else 0
        self.explode_timer = stats.get('delay', 0) * FPS if 'mine' in stats.get('type', '') else 0
        self.chew_timer = 0

    def update(self):
        self.anim_frame += 0.1
        center_x = GRID_X + self.col * CELL_W + CELL_W // 2
        center_y = GRID_Y + self.row * CELL_H + CELL_H // 2
        stats = plant_stats[self.type]

        # Target acquisition
        self.target_zombie = None
        for z in zombies:
            if z.row == self.row and z.x > center_x:
                if self.target_zombie is None or z.x < self.target_zombie.x:
                    self.target_zombie = z

        if 'shooter' in stats.get('type', ''):
            self.shoot_timer -= 1
            if self.shoot_timer <= 0 and self.target_zombie:
                dmg = stats['dmg']
                if stats.get('dual'): dmg //= 2
                projectiles.append(Projectile(center_x + 20, center_y, self.row, dmg,
                                            stats.get('slow', 0), stats.get('fire', False), stats.get('pierce', 1)))
                self.recoil = 5
                self.shoot_timer = stats['cooldown'] * FPS

        elif 'lobber' in stats.get('type', ''):
            self.shoot_timer -= 1
            if self.shoot_timer <= 0 and self.target_zombie:
                projectiles.append(Lobber(center_x, center_y, self.row, stats['dmg'],
                                        stats.get('splash', False), stats.get('stun', False)))
                self.shoot_timer = stats['cooldown'] * FPS

        elif 'chomp' in stats.get('type', ''):
            if self.target_zombie and abs(self.target_zombie.x - center_x) < 30:
                self.chew_timer += 1
                if self.chew_timer >= stats['chew'] * FPS:
                    self.target_zombie.health -= stats['dmg']
                    self.chew_timer = 0

        elif 'mine' in stats.get('type', ''):
            self.explode_timer -= 1
            if self.explode_timer <= 0:
                for z in zombies[:]:
                    if z.row == self.row and abs(z.x - center_x) < stats['aoe'] * CELL_W:
                        z.health -= stats['dmg']
                        if z.health <= 0:
                            zombies.remove(z)
                plants.remove(self)

        elif 'sun' in stats.get('type', ''):
            self.sun_timer -= 1
            if self.sun_timer <= 0:
                suns.append(Sun(center_x, center_y, from_plant=True))
                self.sun_timer = stats['cooldown'] * FPS

        self.recoil = max(0, self.recoil - 1)

    def draw(self, target_surf=screen, scale=1):
        center_x = (GRID_X + self.col * CELL_W + CELL_W // 2) * scale
        center_y = (GRID_Y + self.row * CELL_H + CELL_H // 2 - self.recoil) * scale
        sway = math.sin(self.anim_frame) * 2 * scale

        # Shadow
        shadow = pygame.Surface((40 * scale, 20 * scale), SRCALPHA)
        pygame.draw.ellipse(shadow, SHADOW, (0, 0, 40 * scale, 20 * scale))
        target_surf.blit(shadow, (center_x - 20 * scale, center_y + 15 * scale))

        # Type-specific
        if self.type == 'Cherry Bomb':
            pygame.draw.circle(target_surf, RED, (int(center_x - 5 * scale), int(center_y)), int(8 * scale))
            pygame.draw.circle(target_surf, RED, (int(center_x + 5 * scale), int(center_y)), int(8 * scale))
            spark_ang = self.anim_frame * 10
            spark_x = center_x + math.cos(spark_ang) * 10 * scale
            spark_y = center_y + math.sin(spark_ang) * 10 * scale
            pygame.draw.circle(target_surf, YELLOW, (int(spark_x), int(spark_y)), int(2 * scale))
        else:
            pygame.draw.rect(target_surf, GREEN, (center_x - 15 * scale, center_y - 20 * scale, 30 * scale, 40 * scale))

        # Glow
        glow = pygame.Surface((50 * scale, 50 * scale), SRCALPHA)
        pygame.draw.circle(glow, GLOW_GREEN, (25 * scale, 25 * scale), 25 * scale)
        target_surf.blit(glow, (center_x - 25 * scale, center_y - 25 * scale), special_flags=BLEND_ADD)

class Zombie:
    def __init__(self, row, zombie_type):
        self.row = row
        self.type = zombie_type
        self.x = WIDTH + random.randint(0, 100)
        stats = zombie_stats[zombie_type]
        self.health = stats['health']
        self.max_health = stats['health']
        self.speed = stats['speed']
        self.eat_timer = 30
        self.walk_frame = 0
        self.state = 'walk'
        self.phase = 1

    def update(self):
        self.walk_frame += self.speed * 0.2
        center_x = GRID_X + 5 * CELL_W + CELL_W // 2  # Example lawn start

        colliding_plant = None
        for p in plants:
            p_x = GRID_X + p.col * CELL_W + CELL_W // 2
            if p.row == self.row and abs(self.x - p_x) < 30:
                colliding_plant = p
                break

        if colliding_plant:
            self.state = 'eat'
            self.eat_timer -= 1
            if self.eat_timer <= 0:
                colliding_plant.health -= 10
                self.eat_timer = 30
                if colliding_plant.health <= 0:
                    plants.remove(colliding_plant)
                    self.state = 'walk'
        else:
            self.state = 'walk'
            self.x -= self.speed

        if self.x < 50:
            global lives
            lives -= 1
            zombies.remove(self)
            if lives <= 0:
                global game_active, menu_active
                game_active = False
                menu_active = True

    def draw(self, target_surf=screen, scale=1):
        x = int(self.x * scale)
        y = int((GRID_Y + self.row * CELL_H + CELL_H // 2) * scale)
        pygame.draw.rect(target_surf, ZOMBIE_SKIN, (x - 15 * scale, y - 30 * scale, 30 * scale, 50 * scale))
        # Health bar
        bar_w = 40 * scale * (self.health / self.max_health)
        pygame.draw.rect(target_surf, RED, (x - 20 * scale, y - 40 * scale, 40 * scale, 4 * scale))
        pygame.draw.rect(target_surf, GREEN, (x - 20 * scale, y - 40 * scale, bar_w, 4 * scale))

class Projectile:
    def __init__(self, x, y, row, dmg=20, slow=0, fire=False, pierce=1):
        self.x = x
        self.y = y
        self.row = row
        self.speed = 6
        self.dmg = dmg
        self.slow = slow
        self.fire = fire
        self.pierce = pierce
        self.hit_count = 0

    def update(self):
        self.x += self.speed
        if self.x > WIDTH + 50:
            projectiles.remove(self)
            return
        for z in zombies[:]:
            if z.row == self.row and abs(z.x - self.x) < 20:
                z.health -= self.dmg
                if self.slow: z.speed *= (1 - self.slow)
                self.hit_count += 1
                if self.hit_count >= self.pierce:
                    projectiles.remove(self)
                    break
                if z.health <= 0:
                    zombies.remove(z)

    def draw(self, target_surf=screen, scale=1):
        color = (0, 255, 0) if not self.fire else (255, 100, 0)
        pygame.draw.circle(target_surf, color, (int(self.x * scale), int(self.y * scale)), int(5 * scale))

class Lobber(Projectile):
    def __init__(self, x, y, row, dmg, splash=False, stun=False):
        super().__init__(x, y, row, dmg)
        self.arc = 0
        self.target_x = WIDTH

    def update(self):
        progress = (self.x - GRID_X) / (WIDTH - GRID_X)
        self.y = GRID_Y + self.row * CELL_H + CELL_H // 2 - math.sin(progress * math.pi) * 100
        self.x += 4
        if self.x > self.target_x:
            for z in zombies[:]:
                if z.row == self.row and abs(z.x - self.x) < 50:
                    z.health -= self.dmg
                    if z.health <= 0:
                        zombies.remove(z)
            projectiles.remove(self)

class Sun:
    def __init__(self, x, y, from_plant=False):
        self.x = x
        self.y = y
        self.from_plant = from_plant
        self.lifetime = 600 if from_plant else 300

    def update(self):
        self.lifetime -= 1
        if self.lifetime <= 0:
            suns.remove(self)

    def draw(self, surf, scale=1):
        pygame.draw.circle(surf, YELLOW, (int(self.x * scale), int(self.y * scale)), int(15 * scale))

# === MAIN LOOP ===
current_level = "1-1"
config = level_data[current_level]

while True:
    dt = clock.tick(FPS)
    time_elapsed += 1

    for event in pygame.event.get():
        if event.type == QUIT:
            quit_game()
        elif event.type == KEYDOWN:
            if event.key == K_p:
                paused = not paused
            if event.key == K_z and game_active:
                zen_mode = not zen_mode
        elif event.type == MOUSEBUTTONDOWN and game_active and not paused:
            mx, my = pygame.mouse.get_pos()
            col = (mx - GRID_X) // CELL_W
            row = (my - GRID_Y) // CELL_H
            if 0 <= col < COLS and 0 <= row < ROWS and selected_plant:
                cost = plant_stats[selected_plant]['cost']
                if sun_bank >= cost:
                    plants.append(Plant(col, row, selected_plant))
                    sun_bank -= cost
                    selected_plant = None

    if not game_active or paused or zen_mode:
        screen.fill(BLACK)
        font = pygame.font.SysFont(None, 55)
        text = font.render("PAUSED" if paused else "GAME OVER" if not game_active else "ZEN MODE", 1, WHITE)
        screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2))
        pygame.display.flip()
        continue

    # Spawn zombies
    if time_elapsed % (5 * FPS) == 0 and wave_current < config["flags"]:
        z_type = random.choice(config["zombies"])
        row = random.randint(0, ROWS-1)
        zombies.append(Zombie(row, z_type))

    # Update
    for p in plants[:]: p.update()
    for z in zombies[:]: z.update()
    for proj in projectiles[:]: proj.update()
    for s in suns[:]: s.update()

    # Rendering: HD Upscale
    upscale_surf.fill(SKY)
    for row in range(ROWS):
        y = (GRID_Y + row * CELL_H) * UPSAMPLE_SCALE
        color = GRASS if row % 2 == 0 else DARK_GREEN
        pygame.draw.rect(upscale_surf, color, (GRID_X * UPSAMPLE_SCALE, y, COLS * CELL_W * UPSAMPLE_SCALE, CELL_H * UPSAMPLE_SCALE))

    for p in plants: p.draw(upscale_surf, UPSAMPLE_SCALE)
    for z in zombies: z.draw(upscale_surf, UPSAMPLE_SCALE)
    for proj in projectiles: proj.draw(upscale_surf, UPSAMPLE_SCALE)
    for s in suns: s.draw(upscale_surf, UPSAMPLE_SCALE)

    # Downsample
    pygame.transform.smoothscale(upscale_surf, (WIDTH, HEIGHT), screen)

    # HUD
    font = pygame.font.SysFont(None, 36)
    sun_text = font.render(f"Sun: {sun_bank}", 1, GOLD)
    screen.blit(sun_text, (10, 10))
    lives_text = font.render(f"Lives: {lives}", 1, RED)
    screen.blit(lives_text, (10, 50))

    pygame.display.flip()
