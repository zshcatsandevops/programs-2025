
import sys
import math
import random
import pygame

# ------------------------------
# Config
# ------------------------------
TITLE = "Ultra Mario 1"
DISPLAY_W, DISPLAY_H = 960, 540  # window size
SCALE = 1.0                      # render at native size
TILE = 24                        # tile size in pixels
ROWS, COLS = 15, 200             # tile rows * columns per level (camera shows ~40 cols)
FPS = 60

# World count: 8 worlds * 4 stages = 32
TOTAL_LEVELS = 32

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (120, 120, 120)
DARK_GRAY = (50, 50, 50)
RED = (200, 50, 50)
GREEN = (50, 200, 90)
BLUE = (60, 120, 220)
YELLOW = (250, 220, 70)
ORANGE = (255, 160, 80)
PURPLE = (160, 100, 230)
CYAN = (70, 220, 220)
BROWN = (160, 110, 60)

# Physics constants
GRAVITY = 0.45
JUMP_SPEED = 9.6
MAX_FALL = 16
WALK_SPEED = 3.0
RUN_SPEED = 5.0

# Gameplay
START_LIVES = 3
LEVEL_TIME = 400  # seconds per level

# Tiles and semantics (single-character map codes)
# Solids: Ground (X), Brick (B), Used (U), Pipe (P), Stone (S), Flagpole (F) is not solid
# Interactives: ? (Q), Coin (C) is pickup (not solid), Lava (L) kills, Spike (^)
SOLID_TILES = set('XBUPSH')
PASS_THROUGH = set('CFGL^-')  # not solid

# ------------------------------
# Utility
# ------------------------------
def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v

def world_to_screen(x, cam_x):
    return int(x - cam_x)

def aabb_overlap(ax, ay, aw, ah, bx, by, bw, bh):
    return (ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by)

# ------------------------------
# Entities
# ------------------------------
class Entity:
    def __init__(self, x, y, w, h, color=WHITE):
        self.rect = pygame.Rect(x, y, w, h)
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.dead = False
        self.color = color

    def update(self, dt, world):
        pass

    def draw(self, surf, cam_x):
        pygame.draw.rect(surf, self.color, (world_to_screen(self.rect.x, cam_x), self.rect.y, self.rect.w, self.rect.h))

class Fireball(Entity):
    def __init__(self, x, y, direction):
        super().__init__(x, y, 10, 10, ORANGE)
        self.vx = 6.0 * direction
        self.bounce = 7.0
        self.lifetime = 4.0

    def update(self, dt, world):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.dead = True
            return
        # Apply gravity-ish bounce behavior
        self.vy += 0.5
        if self.vy > 8:
            self.vy = 8

        self.rect.x += int(self.vx)
        # collide x
        if world.collide_solid_rect(self.rect):
            # explode
            self.dead = True
            return

        self.rect.y += int(self.vy)
        hit, side, tx, ty = world.collide_solid_rect_detail(self.rect)
        if hit:
            # bounce on ground only
            if side == 'bottom':  # hit ground
                self.rect.bottom = (ty * TILE)
                self.vy = -self.bounce
            else:
                self.dead = True

class Enemy(Entity):
    def __init__(self, x, y, kind='goober'):
        if kind == 'goober':
            w,h,color = 20, 20, BROWN
        elif kind == 'sheller':
            w,h,color = 22, 22, GREEN
        else:
            w,h,color = 20, 20, PURPLE
        super().__init__(x, y, w, h, color)
        self.kind = kind
        self.dir = -1
        self.walk_speed = 1.1 if kind=='goober' else 1.0
        self.shell = False
        self.shell_sliding = False
        self.stomp_timer = 0.0

    def stomped(self, world, player):
        if self.kind == 'goober':
            self.dead = True
            player.add_score(100)
        elif self.kind == 'sheller':
            if not self.shell:
                self.shell = True
                self.rect.h = 16
                self.rect.y += 6
                self.shell_sliding = False
                player.add_score(200)
            else:
                # kick shell
                self.shell_sliding = True
                self.dir = -1 if player.rect.centerx < self.rect.centerx else 1
                self.walk_speed = 5.0
                player.add_score(400)

    def update(self, dt, world):
        if self.dead:
            return
        # gravity
        self.vy += GRAVITY
        self.vy = clamp(self.vy, -MAX_FALL, MAX_FALL)

        # horizontal AI
        self.vx = (self.walk_speed * (0 if (self.kind=='sheller' and not self.shell_sliding and self.shell) else self.dir))

        # move x
        self.rect.x += int(self.vx)
        hit, side, tx, ty = world.collide_solid_rect_detail(self.rect)
        if hit:
            if side == 'right':
                self.rect.right = tx * TILE
                self.dir = -1
            elif side == 'left':
                self.rect.left = (tx+1) * TILE
                self.dir = 1

        # move y
        self.rect.y += int(self.vy)
        hit, side, tx, ty = world.collide_solid_rect_detail(self.rect)
        self.on_ground = False
        if hit:
            if side == 'bottom':
                self.rect.bottom = ty * TILE
                self.vy = 0
                self.on_ground = True
            elif side == 'top':
                self.rect.top = (ty+1) * TILE
                self.vy = 0

        # dead if fall below level
        if self.rect.top > ROWS * TILE + 200:
            self.dead = True

class PowerUp(Entity):
    def __init__(self, x, y, kind='mushroom'):
        color = YELLOW if kind=='star' else RED if kind=='mushroom' else ORANGE
        super().__init__(x, y, 18, 18, color)
        self.kind = kind
        self.vx = 0.8 if kind!='star' else 2.0
        self.dir = 1

    def update(self, dt, world):
        # star bouncy motion
        if self.kind == 'star':
            self.vy += GRAVITY*0.8
            if self.on_ground:
                self.vy = -8.0
                self.on_ground = False
        else:
            self.vy += GRAVITY
        self.vy = clamp(self.vy, -MAX_FALL, MAX_FALL)
        self.rect.x += int(self.vx * self.dir)
        hit, side, tx, ty = world.collide_solid_rect_detail(self.rect)
        if hit:
            if side in ('left','right'):
                if side=='left':
                    self.rect.left = (tx+1)*TILE
                else:
                    self.rect.right = tx*TILE
                self.dir *= -1
        self.rect.y += int(self.vy)
        hit, side, tx, ty = world.collide_solid_rect_detail(self.rect)
        self.on_ground = False
        if hit:
            if side == 'bottom':
                self.rect.bottom = ty*TILE
                self.vy = 0
                self.on_ground = True
            elif side == 'top':
                self.rect.top = (ty+1)*TILE
                self.vy = 0

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 18, 26, BLUE)
        self.small_h = 26
        self.big_h = 34
        self.is_big = False
        self.has_fire = False
        self.inv_timer = 0.0
        self.star_timer = 0.0
        self.fire_cooldown = 0.0
        self.score = 0
        self.coins = 0
        self.lives = START_LIVES
        self.holding_jump = False
        self.spawn_x = x
        self.spawn_y = y

    def add_score(self, pts):
        self.score += pts

    def add_coin(self, n=1):
        self.coins += n
        self.score += 200 * n
        if self.coins >= 100:
            self.coins -= 100
            self.lives += 1

    def damage(self):
        if self.inv_timer > 0 or self.star_timer > 0:
            return
        if self.has_fire:
            self.has_fire = False
            self.inv_timer = 2.0
        elif self.is_big:
            self.is_big = False
            self.rect.h = self.small_h
            self.rect.y += (self.big_h - self.small_h)
            self.inv_timer = 2.0
        else:
            self.lives -= 1
            return 'dead'

    def powerup(self, kind):
        if kind == 'mushroom':
            if not self.is_big:
                self.is_big = True
                self.rect.y -= (self.big_h - self.small_h)
                self.rect.h = self.big_h
                self.add_score(1000)
            else:
                self.add_score(100)  # extra points if already big
        elif kind == 'flower':
            if not self.is_big:
                # mushroom effect first
                self.is_big = True
                self.rect.y -= (self.big_h - self.small_h)
                self.rect.h = self.big_h
            self.has_fire = True
            self.add_score(1000)
        elif kind == 'star':
            self.star_timer = 10.0
            self.add_score(1000)

    def handle_input(self, keys):
        run = (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] or keys[pygame.K_x])
        speed = RUN_SPEED if run else WALK_SPEED
        self.vx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vx -= speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vx += speed

    def try_jump(self, keys):
        if (keys[pygame.K_z] or keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.vy = -JUMP_SPEED
            self.on_ground = False
            self.holding_jump = True

    def variable_jump(self, keys):
        if not (keys[pygame.K_z] or keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]):
            self.holding_jump = False
        # If holding jump while moving up, reduce gravity slightly for a bit
        if self.holding_jump and self.vy < 0:
            self.vy += GRAVITY * 0.3

    def shoot(self, projectiles):
        if not self.has_fire:
            return
        if self.fire_cooldown > 0:
            return
        direction = 1 if self.vx >= 0 else -1
        fb = Fireball(self.rect.centerx, self.rect.centery, direction)
        projectiles.append(fb)
        self.fire_cooldown = 0.35

    def teleport_to_spawn(self):
        self.rect.x = self.spawn_x
        self.rect.y = self.spawn_y
        self.vx = self.vy = 0

    def update(self, dt, world, keys, projectiles):
        if self.inv_timer > 0:
            self.inv_timer -= dt
        if self.star_timer > 0:
            self.star_timer -= dt
        if self.fire_cooldown > 0:
            self.fire_cooldown -= dt

        # Input
        self.handle_input(keys)
        self.try_jump(keys)
        self.variable_jump(keys)

        # Gravity
        self.vy += GRAVITY
        self.vy = clamp(self.vy, -MAX_FALL, MAX_FALL)

        # Move X
        self.rect.x += int(self.vx)
        hit, side, tx, ty = world.collide_solid_rect_detail(self.rect)
        if hit:
            if side == 'right':
                self.rect.right = tx * TILE
            elif side == 'left':
                self.rect.left = (tx + 1) * TILE

        # Move Y
        self.rect.y += int(self.vy)
        hit, side, tx, ty = world.collide_solid_rect_detail(self.rect)
        self.on_ground = False
        if hit:
            if side == 'bottom':
                self.rect.bottom = ty * TILE
                self.vy = 0
                self.on_ground = True
            elif side == 'top':
                # Bonk block
                self.rect.top = (ty + 1) * TILE
                self.vy = 0
                world.hit_block(tx, ty, self)

        # Fireball key
        if pygame.key.get_pressed()[pygame.K_c]:
            self.shoot(projectiles)

        # Interactions: Coins, flagpole, hazards
        # Coins as pickups placed in map
        for cx, cy in world.coins[:]:
            coin_rect = pygame.Rect(cx*TILE+4, cy*TILE+4, TILE-8, TILE-8)
            if self.rect.colliderect(coin_rect):
                world.coins.remove((cx, cy))
                self.add_coin(1)
        # Flagpole
        if world.flagpole_rect and self.rect.colliderect(world.flagpole_rect):
            world.level_complete = True
        # Hazards: Lava or spikes
        for hx, hy in world.hazards:
            hz_rect = pygame.Rect(hx*TILE, hy*TILE, TILE, TILE)
            if self.rect.colliderect(hz_rect):
                if self.star_timer <= 0:
                    if self.damage() == 'dead':
                        self.dead = True

        # Death by falling
        if self.rect.top > ROWS * TILE + 200:
            if self.damage() == 'dead':
                self.dead = True

# ------------------------------
# World / Level
# ------------------------------
class World:
    def __init__(self, level_index):
        # level_index: 0..31
        self.level_index = level_index
        self.world = level_index // 4 + 1
        self.stage = level_index % 4 + 1
        self.map = [['-' for _ in range(COLS)] for __ in range(ROWS)]
        self.coins = []    # list of (tx, ty)
        self.hazards = []  # list of (tx, ty)
        self.enemies = []
        self.powerups = []
        self.projectiles = []
        self.flagpole_rect = None
        self.level_complete = False
        self.time_left = LEVEL_TIME
        self.start_x = 2 * TILE
        self.start_y = (ROWS-3)*TILE - 10

        self.generate_level()

    # ------------- Map helpers -------------
    def in_bounds(self, tx, ty):
        return 0 <= tx < COLS and 0 <= ty < ROWS

    def get(self, tx, ty):
        if not self.in_bounds(tx, ty):
            return 'X' if ty >= ROWS else '-'  # treat off-bottom as solid
        return self.map[ty][tx]

    def set(self, tx, ty, ch):
        if self.in_bounds(tx, ty):
            self.map[ty][tx] = ch

    def tile_rect(self, tx, ty):
        return pygame.Rect(tx*TILE, ty*TILE, TILE, TILE)

    def is_solid(self, ch):
        return ch in SOLID_TILES

    # ------------- Collision -------------
    def collide_solid_rect(self, rect):
        # Broad-phase: check tiles overlapped by rect
        min_tx = max(0, rect.left // TILE - 2)
        max_tx = min(COLS-1, rect.right // TILE + 2)
        min_ty = max(0, rect.top // TILE - 2)
        max_ty = min(ROWS-1, rect.bottom // TILE + 2)
        for ty in range(min_ty, max_ty+1):
            for tx in range(min_tx, max_tx+1):
                ch = self.get(tx, ty)
                if self.is_solid(ch):
                    if rect.colliderect(self.tile_rect(tx, ty)):
                        return True
        return False

    def collide_solid_rect_detail(self, rect):
        # Return (hit, side, tx, ty)
        # Determine which side by probing
        # We'll check immediate overlapping tiles to resolve
        min_tx = max(0, rect.left // TILE - 2)
        max_tx = min(COLS-1, rect.right // TILE + 2)
        min_ty = max(0, rect.top // TILE - 2)
        max_ty = min(ROWS-1, rect.bottom // TILE + 2)
        for ty in range(min_ty, max_ty+1):
            for tx in range(min_tx, max_tx+1):
                ch = self.get(tx, ty)
                if not self.is_solid(ch):
                    continue
                tile_r = self.tile_rect(tx, ty)
                if rect.colliderect(tile_r):
                    # Determine side by overlap depths
                    dx1 = rect.right - tile_r.left
                    dx2 = tile_r.right - rect.left
                    dy1 = rect.bottom - tile_r.top
                    dy2 = tile_r.bottom - rect.top
                    min_dx = min(dx1, dx2)
                    min_dy = min(dy1, dy2)
                    if min_dx < min_dy:
                        # horizontal collision
                        side = 'right' if dx1 < dx2 else 'left'
                        return True, side, tx, ty
                    else:
                        side = 'bottom' if dy1 < dy2 else 'top'
                        return True, side, tx, ty
        return False, None, -1, -1

    # ------------- Blocks -------------
    def hit_block(self, tx, ty, player):
        ch = self.get(tx, ty)
        if ch == 'B':
            # Brick: break if big
            if player.is_big:
                self.set(tx, ty, '-')
                player.add_score(50)
            else:
                # bounce only
                pass
        elif ch == 'Q':
            # Question: spawn item/coin; convert to Used
            self.set(tx, ty, 'U')
            rng = random.Random(self.level_index*1234 + tx*31 + ty*17)
            roll = rng.random()
            item_kind = None
            if roll < 0.50:
                # coin
                self.coins.append((tx, ty-1))
                player.add_score(200)
            elif roll < 0.80:
                item_kind = 'mushroom'
            elif roll < 0.95:
                item_kind = 'flower'
            else:
                item_kind = 'star'
            if item_kind:
                pu = PowerUp(tx*TILE+3, (ty-1)*TILE+4, item_kind)
                self.powerups.append(pu)

    # ------------- Level Generation -------------
    def generate_level(self):
        # Deterministic RNG per level
        seed = 1000 + self.level_index*4242
        rng = random.Random(seed)

        # Base: ground
        ground_y = ROWS - 2  # last two rows are ground + bedrock
        for x in range(COLS):
            self.set(x, ground_y, 'X')
            self.set(x, ROWS-1, 'S')  # bedrock

        # A few holes (increase with difficulty)
        holes = self.world + self.stage - 1
        holes = clamp(holes, 1, 10)
        for _ in range(holes):
            start = rng.randint(8, COLS-20)
            width = rng.randint(2, 5 + self.world)
            for x in range(start, min(COLS-1, start+width)):
                self.set(x, ground_y, '-')
                self.set(x, ROWS-1, '-')

        # Pipes
        pipe_count = clamp(2 + self.world, 2, 10)
        for _ in range(pipe_count):
            x = rng.randint(10, COLS-12)
            h = rng.randint(2, 4 + (self.world//2))
            # only place if ground present
            if self.get(x, ground_y) == 'X' and self.get(x+1, ground_y) == 'X':
                for y in range(ground_y - h + 1, ground_y+1):
                    self.set(x, y, 'P')
                    self.set(x+1, y, 'P')

        # Platforms, bricks, question blocks
        plat_count = 35 + self.level_index // 2
        for _ in range(plat_count):
            x = rng.randint(6, COLS-6)
            y = rng.randint(5, ground_y-3)
            length = rng.randint(2, 6)
            tile = 'B' if rng.random() < 0.6 else 'Q'
            for i in range(length):
                self.set(x+i, y, tile)
                if tile == 'Q' and rng.random() < 0.3:
                    # sometimes stack a coin above
                    self.coins.append((x+i, y-1))

        # Random floating coins
        for _ in range(60):
            x = rng.randint(5, COLS-5)
            y = rng.randint(3, ground_y-2)
            if self.get(x, y) == '-':
                self.coins.append((x, y))

        # Hazards (lava pools)
        for _ in range(2 + self.world//2):
            start = rng.randint(12, COLS-18)
            w = rng.randint(2, 5)
            for x in range(start, start+w):
                self.set(x, ground_y, 'L')
                self.hazards.append((x, ground_y))

        # Enemies
        enemy_count = 18 + self.level_index // 2
        for _ in range(enemy_count):
            kind = 'goober' if rng.random() < 0.6 else 'sheller'
            # try place on ground tiles (X) with space above
            for _try in range(5):
                x = rng.randint(4, COLS-4)
                if self.get(x, ground_y) in ('X','P') and self.get(x, ground_y-1) == '-':
                    e = Enemy(x*TILE+2, (ground_y-1)*TILE+8, kind)
                    self.enemies.append(e)
                    break

        # Start position (ensure free space)
        self.start_x = 2*TILE
        self.start_y = (ground_y-1)*TILE - 6

        # Flagpole near end
        flag_x = COLS - 6
        self.set(flag_x, ground_y, 'X')
        self.set(flag_x, ground_y-1, '-')
        self.flagpole_rect = pygame.Rect(flag_x*TILE+TILE//2-2, (ground_y-8)*TILE, 4, 8*TILE)

        # Castle (solid facade)
        for y in range(ground_y-5, ground_y+1):
            for x in range(COLS-10, COLS-3):
                if y >= ground_y-2:
                    self.set(x, y, 'S')
                else:
                    self.set(x, y, 'H')  # decorative solid

    # ------------- Draw -------------
    def draw(self, surf, cam_x):
        # Background
        surf.fill((120, 190, 255))

        # Parallax "hills"
        for i in range(8):
            hill_x = ((i*500) - cam_x*0.5) % (COLS*TILE)
            pygame.draw.ellipse(surf, (90, 180, 120), (hill_x, DISPLAY_H-160, 260, 120))

        # Tiles
        min_tx = max(0, int(cam_x // TILE) - 2)
        max_tx = min(COLS-1, int((cam_x + DISPLAY_W) // TILE) + 2)
        for ty in range(ROWS):
            for tx in range(min_tx, max_tx+1):
                ch = self.get(tx, ty)
                if ch == '-':
                    continue
                r = self.tile_rect(tx, ty)
                sx = world_to_screen(r.x, cam_x)
                rr = pygame.Rect(sx, r.y, r.w, r.h)
                if ch == 'X':
                    pygame.draw.rect(surf, (200,160,110), rr)  # ground
                elif ch == 'S' or ch == 'H':
                    pygame.draw.rect(surf, (110,110,110), rr)  # stone/castle
                elif ch == 'B':
                    pygame.draw.rect(surf, (150, 75, 0), rr)   # brick
                elif ch == 'Q':
                    pygame.draw.rect(surf, YELLOW, rr)        # question
                    pygame.draw.rect(surf, (160,130,0), rr, 2)
                elif ch == 'U':
                    pygame.draw.rect(surf, (200,200,80), rr)  # used
                    pygame.draw.rect(surf, (160,130,0), rr, 2)
                elif ch == 'P':
                    pygame.draw.rect(surf, (60,150,60), rr)   # pipe
                    pygame.draw.rect(surf, (40,110,40), rr, 3)
                elif ch == 'L':
                    pygame.draw.rect(surf, (255, 90, 60), rr) # lava
        # Coins
        for (cx, cy) in self.coins:
            r = pygame.Rect(world_to_screen(cx*TILE+6, cam_x), cy*TILE+6, TILE-12, TILE-12)
            pygame.draw.ellipse(surf, YELLOW, r)

        # Flagpole
        if self.flagpole_rect:
            base = self.flagpole_rect.copy()
            base.x = world_to_screen(base.x, cam_x)
            pygame.draw.rect(surf, WHITE, base)
            flag = pygame.Rect(base.x-16, base.y+20, 16, 12)
            pygame.draw.rect(surf, RED, flag)

# ------------------------------
# Game
# ------------------------------
STATE_MENU = 0
STATE_PLAYING = 1
STATE_PAUSED = 2
STATE_GAMEOVER = 3
STATE_VICTORY = 4
STATE_LEVELCLEAR = 5

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((DISPLAY_W, DISPLAY_H))
        self.clock = pygame.time.Clock()
        self.font_big = pygame.font.Font(None, 72)
        self.font = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)

        self.state = STATE_MENU
        self.level_index = 0
        self.world = None
        self.player = None
        self.cam_x = 0
        self.level_entry_timer = 0.5

        self.menu_level_buffer = ""  # for typing "1..32" to start

    def start_level(self, level_index):
        self.level_index = max(0, min(TOTAL_LEVELS-1, level_index))
        self.world = World(self.level_index)
        self.player = Player(self.world.start_x, self.world.start_y)
        self.player.spawn_x = self.world.start_x
        self.player.spawn_y = self.world.start_y
        self.cam_x = 0
        self.level_entry_timer = 0.6
        self.state = STATE_PLAYING

    def next_level(self):
        if self.level_index + 1 >= TOTAL_LEVELS:
            self.state = STATE_VICTORY
        else:
            self.start_level(self.level_index + 1)

    def update_camera(self):
        target = self.player.rect.centerx - DISPLAY_W//2
        # clamp within level
        max_x = COLS*TILE - DISPLAY_W
        self.cam_x = clamp(target, 0, max_x)

    def draw_hud(self):
        # HUD: SCORE, COINS, WORLD, LIVES, TIME
        s_score = self.font_small.render(f"SCORE {self.player.score:06d}", True, WHITE)
        s_coins = self.font_small.render(f"COINS x{self.player.coins:02d}", True, WHITE)
        world_str = f"{(self.level_index//4)+1}-{(self.level_index%4)+1}"
        s_world = self.font_small.render(f"WORLD {world_str}", True, WHITE)
        s_lives = self.font_small.render(f"LIVES {self.player.lives}", True, WHITE)
        s_time = self.font_small.render(f"TIME {int(self.world.time_left):03d}", True, WHITE)
        self.screen.blit(s_score, (20, 12))
        self.screen.blit(s_coins, (220, 12))
        self.screen.blit(s_world, (420, 12))
        self.screen.blit(s_lives, (620, 12))
        self.screen.blit(s_time, (800, 12))

    def handle_menu_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                # Start from typed level if provided
                if self.menu_level_buffer.strip():
                    try:
                        n = int(self.menu_level_buffer.strip())
                        if 1 <= n <= TOTAL_LEVELS:
                            self.start_level(n-1)
                            self.menu_level_buffer = ""
                            return
                    except ValueError:
                        pass
                self.start_level(0)
            elif event.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit(0)
            elif event.key == pygame.K_BACKSPACE:
                self.menu_level_buffer = self.menu_level_buffer[:-1]
            else:
                ch = event.unicode
                if ch.isdigit():
                    if len(self.menu_level_buffer) < 2:
                        self.menu_level_buffer += ch

    def draw_menu(self):
        self.screen.fill((25, 35, 60))
        title = self.font_big.render(TITLE, True, YELLOW)
        self.screen.blit(title, (DISPLAY_W//2 - title.get_width()//2, 100))
        msg1 = self.font.render("Press ENTER to Start", True, WHITE)
        self.screen.blit(msg1, (DISPLAY_W//2 - msg1.get_width()//2, 220))
        msg2 = self.font_small.render("Type 1..32 then ENTER to start from a specific level", True, GRAY)
        self.screen.blit(msg2, (DISPLAY_W//2 - msg2.get_width()//2, 260))
        if self.menu_level_buffer:
            msg3 = self.font.render(f"Level: {self.menu_level_buffer}", True, CYAN)
            self.screen.blit(msg3, (DISPLAY_W//2 - msg3.get_width()//2, 300))

        foot = self.font_small.render("Asset-free 2D engine • Pygame • © You", True, GRAY)
        self.screen.blit(foot, (DISPLAY_W//2 - foot.get_width()//2, 480))

    def draw_pause(self):
        overlay = pygame.Surface((DISPLAY_W, DISPLAY_H), pygame.SRCALPHA)
        overlay.fill((0,0,0,140))
        self.screen.blit(overlay, (0,0))
        t = self.font_big.render("PAUSED", True, WHITE)
        self.screen.blit(t, (DISPLAY_W//2 - t.get_width()//2, DISPLAY_H//2 - 80))
        s = self.font.render("Press P to resume • ESC to quit", True, WHITE)
        self.screen.blit(s, (DISPLAY_W//2 - s.get_width()//2, DISPLAY_H//2))

    def draw_center_message(self, title, subtitle):
        self.screen.fill(BLACK)
        t = self.font_big.render(title, True, WHITE)
        self.screen.blit(t, (DISPLAY_W//2 - t.get_width()//2, DISPLAY_H//2 - 60))
        s = self.font.render(subtitle, True, GRAY)
        self.screen.blit(s, (DISPLAY_W//2 - s.get_width()//2, DISPLAY_H//2 + 10))

    def update_playing(self, dt):
        keys = pygame.key.get_pressed()
        if self.level_entry_timer > 0:
            self.level_entry_timer -= dt
        # Pause
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Quick exit to menu
                    self.state = STATE_MENU
                    return
                if event.key == pygame.K_p:
                    self.state = STATE_PAUSED
                if event.key == pygame.K_c:
                    self.player.shoot(self.world.projectiles)

        # Update player
        self.player.update(dt, self.world, keys, self.world.projectiles)

        # Powerups
        for pu in self.world.powerups[:]:
            pu.update(dt, self.world)
            if pu.rect.colliderect(self.player.rect):
                self.player.powerup(pu.kind)
                self.world.powerups.remove(pu)

        # Enemies
        for e in self.world.enemies[:]:
            e.update(dt, self.world)
            # Collide with player
            if not e.dead and self.player.rect.colliderect(e.rect):
                # Check stomp
                if self.player.vy > 1.0 and self.player.rect.bottom - e.rect.top < 16:
                    e.stomped(self.world, self.player)
                    self.player.vy = -7.0
                    self.player.on_ground = False
                else:
                    if self.player.star_timer > 0:
                        e.dead = True
                        self.player.add_score(200)
                    else:
                        if self.player.damage() == 'dead':
                            self.state = STATE_GAMEOVER
                        else:
                            # knockback
                            self.player.vx = -4.0 if (self.player.rect.centerx < e.rect.centerx) else 4.0

        # Fireballs vs enemies
        for fb in self.world.projectiles[:]:
            fb.update(dt, self.world)
            for e in self.world.enemies[:]:
                if not e.dead and fb.rect.colliderect(e.rect):
                    e.dead = True
                    self.player.add_score(200)
                    fb.dead = True
            if fb.dead:
                self.world.projectiles.remove(fb)

        # Reduce time
        if self.world.time_left > 0:
            self.world.time_left -= dt
            if self.world.time_left <= 0:
                # time out
                if self.player.damage() == 'dead':
                    self.state = STATE_GAMEOVER

        # Level complete?
        if self.world.level_complete:
            self.state = STATE_LEVELCLEAR

        # Update camera
        self.update_camera()

        # Draw
        self.world.draw(self.screen, self.cam_x)
        # Draw entities
        for pu in self.world.powerups:
            pu.draw(self.screen, self.cam_x)
        for e in self.world.enemies:
            if not e.dead:
                e.draw(self.screen, self.cam_x)
        for fb in self.world.projectiles:
            fb.draw(self.screen, self.cam_x)
        # Player (blink during invincibility)
        if int(self.player.inv_timer*10) % 2 == 0 or self.player.inv_timer <= 0 or self.player.star_timer > 0:
            self.player.draw(self.screen, self.cam_x)

        self.draw_hud()

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1_000.0

            if self.state == STATE_MENU:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit(); sys.exit(0)
                    self.handle_menu_input(event)
                self.draw_menu()

            elif self.state == STATE_PLAYING:
                self.update_playing(dt)

            elif self.state == STATE_PAUSED:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit(); sys.exit(0)
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_p:
                            self.state = STATE_PLAYING
                        if event.key == pygame.K_ESCAPE:
                            self.state = STATE_MENU
                # draw paused overlay over current frame
                self.draw_pause()

            elif self.state == STATE_LEVELCLEAR:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit(); sys.exit(0)
                    if event.type == pygame.KEYDOWN:
                        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            self.next_level()
                self.draw_center_message("COURSE CLEAR!", "Press ENTER to continue")

            elif self.state == STATE_GAMEOVER:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit(); sys.exit(0)
                    if event.type == pygame.KEYDOWN:
                        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            self.state = STATE_MENU
                self.draw_center_message("GAME OVER", "Press ENTER to return to menu")

            elif self.state == STATE_VICTORY:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit(); sys.exit(0)
                    if event.type == pygame.KEYDOWN:
                        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            self.state = STATE_MENU
                self.draw_center_message("YOU WIN!", "All 32 stages cleared")

            pygame.display.flip()

if __name__ == "__main__":
    Game().run()
