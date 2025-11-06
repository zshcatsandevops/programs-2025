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
PEACH = (240, 200, 160)  # Skin tone
BEIGE = (210, 180, 140)  # Mushroom stem
SKY = (132, 208, 255)

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
# Solids: Ground (X), Brick (B), Used (U), Pipe (P), Stone (S), Hidden (H)
# Interactives: ? (Q), Coin (C) pickup (not solid), Flagpole (F) not solid, Lava (L) kills, Spike (^)
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

    def draw(self, surf, cam_x):
        x = world_to_screen(self.rect.x, cam_x)
        y = self.rect.y
        # Fiery orb
        pygame.draw.circle(surf, ORANGE, (int(x + 5), int(y + 5)), 5)
        pygame.draw.circle(surf, YELLOW, (int(x + 5), int(y + 5)), 2)  # Glow

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

    def draw(self, surf, cam_x):
        x = world_to_screen(self.rect.x, cam_x)
        y = self.rect.y
        w = self.rect.w
        h = self.rect.h
        if self.kind == 'goober':
            # Goomba: mushroom body
            pygame.draw.ellipse(surf, BROWN, (x, y + 8, w, h - 8))  # Body
            pygame.draw.circle(surf, BROWN, (x + w // 2, y + 6), w // 2 - 1)  # Head
            pygame.draw.circle(surf, BLACK, (x + 4, y + 4), 2)  # Eye
            pygame.draw.circle(surf, BLACK, (x + w - 4, y + 4), 2)  # Eye
            pygame.draw.rect(surf, BROWN, (x + 2, y + h - 4, 3, 4))  # Foot
            pygame.draw.rect(surf, BROWN, (x + w - 5, y + h - 4, 3, 4))  # Foot
        elif self.kind == 'sheller':
            if self.shell:
                # Shelled Koopa: static shell
                pygame.draw.rect(surf, GREEN, (x, y, w, h))
                pygame.draw.rect(surf, DARK_GRAY, (x + 2, y + 2, w - 4, h - 4), 2)  # Outline
                # Shell bands
                pygame.draw.line(surf, BLACK, (x + 4, y + h // 2), (x + w - 4, y + h // 2), 2)
            else:
                # Walking Koopa: shell + legs/head
                pygame.draw.rect(surf, GREEN, (x + 2, y, w - 4, h - 6))  # Shell
                pygame.draw.rect(surf, DARK_GRAY, (x + 4, y + 2, w - 8, h - 8), 2)
                pygame.draw.rect(surf, GREEN, (x, y + h - 6, 6, 6))  # Leg
                pygame.draw.rect(surf, GREEN, (x + w - 6, y + h - 6, 6, 6))  # Leg
                pygame.draw.circle(surf, GREEN, (x + w // 2, y + 4), 4)  # Head
                pygame.draw.circle(surf, BLACK, (x + w // 2 - 1, y + 3), 1)  # Eye
        else:
            # Flyer: simple winged
            pygame.draw.ellipse(surf, PURPLE, (x, y, w, h))
            # Wings
            pygame.draw.polygon(surf, DARK_GRAY, [(x - 2, y + 4), (x + 4, y + 4), (x, y + 8)])
            pygame.draw.polygon(surf, DARK_GRAY, [(x + w - 2, y + 4), (x + w + 4, y + 4), (x + w, y + 8)])

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

    def draw(self, surf, cam_x):
        x = world_to_screen(self.rect.x, cam_x)
        y = self.rect.y
        w = self.rect.w
        h = self.rect.h
        if self.kind == 'mushroom':
            # Cap
            pygame.draw.ellipse(surf, RED, (x, y, w, 12))
            # Stem
            pygame.draw.rect(surf, BEIGE, (x + 5, y + 10, w - 10, h - 10))
            # Spots
            pygame.draw.circle(surf, WHITE, (x + 6, y + 6), 2)
            pygame.draw.circle(surf, WHITE, (x + 12, y + 8), 2)
        elif self.kind == 'flower':
            # Center
            pygame.draw.circle(surf, ORANGE, (x + w // 2, y + h // 2), w // 2 - 2)
            # Petals (simple)
            petal_w = 4
            for i in range(4):
                px = x + w // 2 + (w // 2 - petal_w) * (0.7 * math.cos(math.radians(i * 90)))
                py = y + h // 2 + (h // 2 - petal_w) * (0.7 * math.sin(math.radians(i * 90)))
                pygame.draw.ellipse(surf, ORANGE, (px - petal_w // 2, py - petal_w // 2, petal_w, petal_w * 2))
        elif self.kind == 'star':
            # Procedural star using math
            outer_r = 9
            inner_r = 4
            points = []
            for i in range(10):
                r = outer_r if i % 2 == 0 else inner_r
                angle = math.radians(i * 36)  # 360/10
                px = x + w // 2 + r * math.cos(angle)
                py = y + h // 2 + r * math.sin(angle)
                points.append((px, py))
            pygame.draw.polygon(surf, YELLOW, points)
            # Twinkle outline
            pygame.draw.polygon(surf, WHITE, points, 1)

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

    def draw(self, surf, cam_x):
        x = world_to_screen(self.rect.x, cam_x)
        y = self.rect.y
        w = self.rect.w
        h = self.rect.h
        # Flash when invulnerable
        if self.inv_timer > 0 and int(self.inv_timer * 20) % 2 == 0:
            return
        if self.is_big:
            # Big Mario
            # Hat
            pygame.draw.rect(surf, RED, (x + 2, y, w - 4, 8))
            pygame.draw.rect(surf, RED, (x + w // 2 - 2, y - 2, 4, 4))  # Brim
            # Head
            pygame.draw.circle(surf, PEACH, (x + w // 2, y + 12), 8)
            # Eyes
            pygame.draw.circle(surf, BLACK, (x + w // 2 - 3, y + 10), 2)
            pygame.draw.circle(surf, BLACK, (x + w // 2 + 3, y + 10), 2)
            # Mustache
            pygame.draw.rect(surf, BLACK, (x + 5, y + 14, 8, 3))
            # Shirt
            pygame.draw.rect(surf, RED, (x + 4, y + 16, w - 8, 6))
            # Overalls
            pygame.draw.rect(surf, BLUE, (x, y + 22, w, h - 22))
            # Arms
            pygame.draw.rect(surf, RED, (x - 2, y + 16, 4, 8))
            pygame.draw.rect(surf, RED, (x + w - 2, y + 16, 4, 8))
            # Shoes
            pygame.draw.rect(surf, BROWN, (x + 2, y + h - 4, 6, 4))
            pygame.draw.rect(surf, BROWN, (x + w - 8, y + h - 4, 6, 4))
        else:
            # Small Mario
            # Hat
            pygame.draw.rect(surf, RED, (x + 2, y, w - 4, 6))
            pygame.draw.rect(surf, RED, (x + w // 2 - 1, y - 1, 2, 2))  # Brim
            # Head
            pygame.draw.circle(surf, PEACH, (x + w // 2, y + 8), 6)
            # Eyes
            pygame.draw.circle(surf, BLACK, (x + w // 2 - 2, y + 6), 1)
            pygame.draw.circle(surf, BLACK, (x + w // 2 + 2, y + 6), 1)
            # Overalls
            pygame.draw.rect(surf, BLUE, (x, y + 12, w, h - 12))
            # Shoes
            pygame.draw.rect(surf, BROWN, (x + 1, y + h - 3, 4, 3))
            pygame.draw.rect(surf, BROWN, (x + w - 5, y + h - 3, 4, 3))

# ------------------------------
# World / Level
# ------------------------------
class PipeEntry:
    def __init__(self, x, y, w, h, dest_level, glitch_dest=None, label=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.dest_level = dest_level
        self.glitch_dest = glitch_dest  # optional alternate destination if "glitch" condition detected
        self.label = label

class World:
    def __init__(self, level_index):
        # level_index: -1 for Minus World, else 0..31
        self.level_index = level_index
        if level_index < 0:
            self.world = None
            self.stage = None
            self.world_label = "-1"
        else:
            self.world = level_index // 4 + 1
            self.stage = level_index % 4 + 1
            self.world_label = f"{self.world}-{self.stage}"

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
        self.pipes = []    # list of PipeEntry

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

    def rect_to_tile_range(self, rect):
        x0 = max(0, rect.left // TILE)
        x1 = min(COLS - 1, (rect.right - 1) // TILE)
        y0 = max(0, rect.top // TILE)
        y1 = min(ROWS - 1, (rect.bottom - 1) // TILE)
        return x0, x1, y0, y1

    def collide_solid_rect(self, rect):
        x0, x1, y0, y1 = self.rect_to_tile_range(rect)
        for ty in range(y0, y1 + 1):
            for tx in range(x0, x1 + 1):
                if self.get(tx, ty) in SOLID_TILES:
                    tile_rect = pygame.Rect(tx*TILE, ty*TILE, TILE, TILE)
                    if rect.colliderect(tile_rect):
                        return True
        return False

    def collide_solid_rect_detail(self, rect):
        """
        Returns (hit, side, tx, ty)
        side in {'left','right','top','bottom'} relative to the moving rect.
        Chooses side by minimal penetration depth.
        """
        x0, x1, y0, y1 = self.rect_to_tile_range(rect)
        best = None  # (overlap_val, side, tx, ty)
        for ty in range(y0, y1 + 1):
            for tx in range(x0, x1 + 1):
                if self.get(tx, ty) in SOLID_TILES:
                    tile_rect = pygame.Rect(tx*TILE, ty*TILE, TILE, TILE)
                    if rect.colliderect(tile_rect):
                        # compute overlaps
                        dx_left = rect.right - tile_rect.left     # our right overlapping their left (we moved right) -> side 'right'
                        dx_right = tile_rect.right - rect.left     # our left overlapping their right (we moved left) -> side 'left'
                        dy_top = rect.bottom - tile_rect.top       # our bottom overlapping their top (we moved down) -> side 'bottom'
                        dy_bottom = tile_rect.bottom - rect.top    # our top overlapping their bottom (we moved up) -> side 'top'

                        overlaps = [
                            (dx_left, 'right'),
                            (dx_right, 'left'),
                            (dy_top, 'bottom'),
                            (dy_bottom, 'top'),
                        ]
                        # choose smallest positive overlap
                        for val, side in overlaps:
                            if val >= 0:
                                if best is None or val < best[0]:
                                    best = (val, side, tx, ty)
        if best is None:
            return False, None, -1, -1
        return True, best[1], best[2], best[3]

    # ------------- Block interactions -------------
    def hit_block(self, tx, ty, player):
        ch = self.get(tx, ty)
        above_y = (ty - 1) * TILE
        spawn_x = tx * TILE + TILE // 2 - 9
        if ch == 'Q':
            # Question: powerup if small -> mushroom, if big -> flower (first), else coin
            self.set(tx, ty, 'U')
            kind = 'mushroom' if not player.is_big else 'flower'
            self.powerups.append(PowerUp(spawn_x, above_y, kind))
        elif ch == 'B':
            if player.is_big:
                # break brick
                self.set(tx, ty, '-')
                player.add_score(50)
            else:
                # "bump": 50 points
                player.add_score(10)
        elif ch == 'H':
            # Hidden becomes coin block
            self.set(tx, ty, 'U')
            self.coins.append((tx, ty - 1))
            player.add_score(200)
        # coins in map are pickup, no block bump needed

    # ------------- Warps -------------
    def try_pipe_warp(self, player, keys):
        if not (keys[pygame.K_DOWN] or keys[pygame.K_s]):
            return None
        for entry in self.pipes:
            # Player feet slightly inside the pipe top and horizontally overlapping
            p = player.rect
            r = entry.rect
            horizontally_overlaps = (p.centerx >= r.left and p.centerx <= r.right)
            feet_near_top = (0 <= p.bottom - r.top <= 6)
            if horizontally_overlaps and feet_near_top:
                # "Glitch" heuristic: holding LEFT and entering near the left lip of the pipe
                glitch = False
                if entry.glitch_dest is not None:
                    near_left_lip = abs(p.right - r.left) <= 4
                    if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and near_left_lip:
                        glitch = True
                return entry.glitch_dest if glitch and entry.glitch_dest is not None else entry.dest_level
        return None

    # ------------- Level generation -------------
    def fill_ground(self, start_col=0, end_col=COLS, top_row=13):
        for tx in range(start_col, end_col):
            for ty in range(top_row, ROWS):
                self.set(tx, ty, 'X')

    def place_pipe(self, base_col, height=3):
        # height in tiles above ground
        ground_top = 13
        top_row = ground_top - height
        for ty in range(top_row, ground_top):
            self.set(base_col, ty, 'P')
            self.set(base_col+1, ty, 'P')
        # Add an entry rectangle on the top opening
        entry_rect = pygame.Rect(base_col*TILE, top_row*TILE, 2*TILE, TILE)
        return entry_rect

    def staircase(self, start_col, width, height):
        ground_top = 13
        for i in range(width):
            h = min(height, i+1)
            for j in range(h):
                self.set(start_col + i, ground_top - 1 - j, 'S')

    def column_brick(self, tx, ty0, ty1, ch='B'):
        for ty in range(ty0, ty1+1):
            self.set(tx, ty, ch)

    def place_flagpole(self, pole_col):
        ground_top = 13
        pole_h_tiles = 10
        pole_top = ground_top - pole_h_tiles
        # Draw a "pole" with F tiles (non-solid, we use rect for collision)
        for ty in range(pole_top, ground_top):
            self.set(pole_col, ty, 'F')
        self.flagpole_rect = pygame.Rect(pole_col*TILE + TILE//2 - 4, pole_top*TILE, 8, pole_h_tiles*TILE)

    def scatter_coins(self, positions):
        for (tx, ty) in positions:
            if self.in_bounds(tx, ty):
                self.coins.append((tx, ty))

    def add_enemy(self, tx, ty, kind='goober'):
        x = tx * TILE + 2
        y = ty * TILE
        self.enemies.append(Enemy(x, y, kind))

    def create_world_1_1(self):
        # Ground baseline
        self.fill_ground()

        # Start plateau & early pipes
        # Some bricks and question blocks near start
        for tx in range(8, 13):
            self.set(tx, 9, 'B')
        self.set(10, 8, 'Q')  # powerup
        self.set(12, 9, 'Q')
        self.scatter_coins([(15, 7), (16,7), (17,7), (18,7)])

        # Pipes
        e1 = self.place_pipe(28, height=3)  # small
        e2 = self.place_pipe(45, height=4)  # taller
        e3 = self.place_pipe(70, height=4)
        e4 = self.place_pipe(95, height=5)  # special pipe with glitch alt

        # Register pipe warps (press Down on top). The last pipe offers a glitch path.
        # Normal path: go to World 2-1 (level_index 4)
        # Glitchy "minus" entry: hold Left+Down hugging the left lip -> -1
        self.pipes.append(PipeEntry(e1.x, e1.y, e1.w, e1.h, dest_level=4))
        self.pipes.append(PipeEntry(e2.x, e2.y, e2.w, e2.h, dest_level=8))
        self.pipes.append(PipeEntry(e3.x, e3.y, e3.w, e3.h, dest_level=12))
        self.pipes.append(PipeEntry(e4.x, e4.y, e4.w, e4.h, dest_level=4, glitch_dest=-1, label="GLITCH PIPE"))

        # Mid-section platforms
        for tx in range(60, 66):
            self.set(tx, 8, 'S')
        for tx in range(66, 72):
            self.set(tx, 10, 'S')
        for tx in range(72, 78):
            self.set(tx, 7, 'S')
        self.scatter_coins([(61,7),(62,7),(63,7),(69,9),(75,6)])

        # Enemies
        self.add_enemy(18, 12, 'goober')
        self.add_enemy(22, 12, 'goober')
        self.add_enemy(38, 12, 'sheller')
        self.add_enemy(64, 7, 'goober')
        self.add_enemy(73, 6, 'goober')

        # Late staircase and flag
        self.staircase(120, width=7, height=6)
        self.place_flagpole(130)

        # Hidden block example (becomes coin on hit)
        self.set(20, 8, 'H')

        # Start position
        self.start_x = 2 * TILE
        self.start_y = (ROWS-4) * TILE

    def create_minus_world(self):
        # A looping, water-adjacent vibe (no swimming physics; just a quirky loop)
        # Blue "stone" platforms, coins, hazards, and flag that loops back here
        for tx in range(COLS):
            if tx % 7 in (0,1,2):
                self.set(tx, 12, 'S')  # low platforms sprinkled
        self.fill_ground(top_row=14)  # lower ground so gaps exist

        # Spikes and lava pockets
        for tx in range(10, 20, 2):
            self.set(tx, 13, '^'); self.hazards.append((tx, 13))
        for tx in range(40, 50, 2):
            self.set(tx, 14, 'L'); self.hazards.append((tx, 14))

        # Coins clouds
        self.scatter_coins([(12, 6), (14, 6), (16, 6), (42, 9), (44, 9), (46, 9), (90, 7), (92, 7)])

        # A few enemies
        self.add_enemy(30, 11, 'goober')
        self.add_enemy(32, 11, 'goober')
        self.add_enemy(80, 11, 'sheller')

        # Flag that loops (on completion, reload -1)
        self.place_flagpole(150)

        # Pipes that bounce you around inside -1
        e = self.place_pipe(20, height=4)
        self.pipes.append(PipeEntry(e.x, e.y, e.w, e.h, dest_level=-1))
        e = self.place_pipe(100, height=5)
        self.pipes.append(PipeEntry(e.x, e.y, e.w, e.h, dest_level=-1))

        self.world_label = "-1"
        self.start_x = 3 * TILE
        self.start_y = (ROWS-5) * TILE

    def create_placeholder_world(self):
        """Simple generator so non-1-1 and non--1 are still playable."""
        self.fill_ground()
        # A few random bricks and coins
        rng = random.Random(42 + (self.level_index if self.level_index >= 0 else 0))
        for _ in range(40):
            tx = rng.randrange(6, COLS-10)
            ty = rng.randrange(5, 11)
            self.set(tx, ty, 'B' if rng.random() < 0.6 else 'Q')
        for _ in range(30):
            tx = rng.randrange(6, COLS-10)
            ty = rng.randrange(5, 10)
            self.coins.append((tx, ty))
        # Some pipes that hop to subsequent stages
        for base in (28, 60, 92):
            e = self.place_pipe(base, height=rng.choice([3,4,5]))
            dest = min(self.level_index + 4, TOTAL_LEVELS - 1) if self.level_index >= 0 else -1
            self.pipes.append(PipeEntry(e.x, e.y, e.w, e.h, dest))
        # Enemies
        for x in (20, 24, 44, 48, 64, 90, 110):
            self.add_enemy(x, 12, rng.choice(['goober','sheller']))
        # Flag
        self.place_flagpole(COLS-10)
        # Start
        self.start_x = 2 * TILE
        self.start_y = (ROWS-4) * TILE

    def generate_level(self):
        if self.level_index == -1:
            self.create_minus_world()
            return
        if self.world == 1 and self.stage == 1:
            self.create_world_1_1()
        else:
            self.create_placeholder_world()

    # ------------- Rendering -------------
    def draw_tile(self, surf, tx, ty, cam_x):
        ch = self.get(tx, ty)
        x = world_to_screen(tx * TILE, cam_x)
        y = ty * TILE
        r = pygame.Rect(x, y, TILE, TILE)

        if ch == '-':
            return
        if ch == 'X':  # ground
            pygame.draw.rect(surf, BROWN, r)
            pygame.draw.rect(surf, DARK_GRAY, r, 1)
        elif ch == 'S':  # stone
            pygame.draw.rect(surf, GRAY, r)
            pygame.draw.rect(surf, DARK_GRAY, r, 1)
        elif ch == 'B':  # brick
            pygame.draw.rect(surf, (180, 100, 60), r)
            pygame.draw.rect(surf, BLACK, r, 1)
            pygame.draw.line(surf, BLACK, (r.left, r.centery), (r.right, r.centery), 1)
            pygame.draw.line(surf, BLACK, (r.centerx, r.top), (r.centerx, r.bottom), 1)
        elif ch == 'Q':  # question
            pygame.draw.rect(surf, ORANGE, r)
            pygame.draw.rect(surf, BLACK, r, 1)
            pygame.draw.circle(surf, YELLOW, r.center, 5, 2)
        elif ch == 'U':  # used
            pygame.draw.rect(surf, (150, 150, 150), r)
            pygame.draw.rect(surf, DARK_GRAY, r, 1)
        elif ch == 'P':  # pipe
            pygame.draw.rect(surf, GREEN, r)
            pygame.draw.rect(surf, DARK_GRAY, r, 2)
        elif ch == 'C':
            # draw coin (map coins drawn from self.coins; this path is rarely used)
            pygame.draw.circle(surf, YELLOW, r.center, 6)
        elif ch == 'F':
            # flagpole visual
            pygame.draw.rect(surf, WHITE, (r.centerx-2, r.top, 4, TILE))
        elif ch == 'L':
            pygame.draw.rect(surf, (255, 64, 32), r)
        elif ch == '^':
            # spike
            pygame.draw.polygon(surf, GRAY, [(r.left, r.bottom), (r.centerx, r.top), (r.right, r.bottom)])
        elif ch == 'H':
            # hidden block (invisible): draw nothing
            pass

    def draw(self, surf, cam_x):
        # background
        surf.fill(SKY)

        # visible range
        c0 = max(0, int(cam_x // TILE) - 2)
        c1 = min(COLS-1, int((cam_x + DISPLAY_W) // TILE) + 2)

        # tiles
        for ty in range(ROWS):
            for tx in range(c0, c1+1):
                self.draw_tile(surf, tx, ty, cam_x)

        # coins
        for (tx, ty) in self.coins:
            x = world_to_screen(tx*TILE + TILE//2, cam_x)
            y = ty*TILE + TILE//2
            pygame.draw.circle(surf, YELLOW, (x, y), 6)
            pygame.draw.circle(surf, WHITE, (x, y), 6, 1)

        # hazards drawn by tiles already

        # flagpole (collision rect)
        if self.flagpole_rect:
            fr = self.flagpole_rect
            x = world_to_screen(fr.x, cam_x)
            pygame.draw.rect(surf, WHITE, (x, fr.y, fr.w, fr.h), 2)

# ------------------------------
# Game orchestration
# ------------------------------
def next_level_index(curr):
    if curr == -1:
        return -1  # minus world loops on itself
    if curr + 1 >= TOTAL_LEVELS:
        return 0
    return curr + 1

def prev_level_index(curr):
    if curr == -1:
        return -1
    if curr - 1 < 0:
        return TOTAL_LEVELS - 1
    return curr - 1

def run():
    pygame.init()
    pygame.display.set_caption(TITLE)
    render_w = int(DISPLAY_W / SCALE)
    render_h = int(DISPLAY_H / SCALE)
    window = pygame.display.set_mode((DISPLAY_W, DISPLAY_H))
    canvas = pygame.Surface((render_w, render_h))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Consolas", 18)

    level_index = 0  # start at 1-1
    world = World(level_index)
    player = Player(world.start_x, world.start_y)

    cam_x = 0.0
    running = True

    def draw_hud(surface):
        def text(s): return font.render(s, True, BLACK)
        surface.blit(text(f"Score {player.score:06d}"), (16, 10))
        surface.blit(text(f"Coins {player.coins:02d}"), (16, 32))
        world_label = world.world_label if world.level_index == -1 else f"{world.world}-{world.stage}"
        surface.blit(text(f"World {world_label}"), (DISPLAY_W//2 - 60, 10))
        surface.blit(text(f"Time {int(world.time_left):03d}"), (DISPLAY_W - 140, 10))
        surface.blit(text(f"Lives {player.lives}"), (DISPLAY_W - 140, 32))

    # main loop
    while running:
        dt_ms = clock.tick(FPS)
        dt = dt_ms / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            running = False
        if keys[pygame.K_r]:
            # reset current level
            world = World(level_index)
            player = Player(world.start_x, world.start_y)
        if keys[pygame.K_n]:
            level_index = next_level_index(level_index)
            world = World(level_index)
            player = Player(world.start_x, world.start_y)
        if keys[pygame.K_p]:
            level_index = prev_level_index(level_index)
            world = World(level_index)
            player = Player(world.start_x, world.start_y)

        # Time
        world.time_left -= dt
        if world.time_left <= 0 and not player.dead:
            if player.damage() == 'dead':
                player.dead = True

        # Update player and entities
        if not player.dead:
            player.update(dt, world, keys, world.projectiles)

        # Warp via pipe (Down)
        dest = world.try_pipe_warp(player, keys)
        if dest is not None:
            level_index = dest
            world = World(level_index)
            # keep stats
            player.teleport_to_spawn()
            player.rect.x = world.start_x
            player.rect.y = world.start_y

        # Projectiles
        for fb in world.projectiles[:]:
            fb.update(dt, world)
            if fb.dead:
                world.projectiles.remove(fb)

        # Enemies
        for e in world.enemies[:]:
            e.update(dt, world)
            if e.dead:
                world.enemies.remove(e)

        # Powerups
        for p in world.powerups[:]:
            p.update(dt, world)
            if p.dead:
                world.powerups.remove(p)

        # Collisions: player vs enemies
        if not player.dead:
            for e in world.enemies[:]:
                if player.rect.colliderect(e.rect):
                    if player.star_timer > 0:
                        e.dead = True
                        player.add_score(200)
                        continue
                    # stomp?
                    falling = player.vy > 0
                    above = player.rect.bottom - e.rect.top <= 10
                    if falling and above:
                        e.stomped(world, player)
                        player.vy = -6.0
                        player.on_ground = False
                    else:
                        if e.kind == 'sheller' and e.shell and e.shell_sliding:
                            # treat as hazard
                            if player.damage() == 'dead':
                                player.dead = True
                        else:
                            if player.damage() == 'dead':
                                player.dead = True

        # Fireballs vs enemies
        for fb in world.projectiles[:]:
            for e in world.enemies[:]:
                if fb.rect.colliderect(e.rect):
                    e.dead = True
                    fb.dead = True
                    player.add_score(200)

        # Powerup pickup
        for p in world.powerups[:]:
            if player.rect.colliderect(p.rect):
                player.powerup(p.kind)
                p.dead = True

        # On level complete
        if world.level_complete:
            if level_index == -1:
                # loop forever
                world = World(-1)
                player.rect.x, player.rect.y = world.start_x, world.start_y
                world.level_complete = False
            else:
                level_index = next_level_index(level_index)
                world = World(level_index)
                player.rect.x, player.rect.y = world.start_x, world.start_y
                world.level_complete = False

        # Camera follows player, clamped to level bounds
        cam_x = player.rect.centerx - DISPLAY_W * 0.45
        cam_x = clamp(cam_x, 0, COLS*TILE - DISPLAY_W)

        # --- Render ---
        canvas.fill(SKY)
        world.draw(canvas, cam_x)

        # Draw entities
        for e in world.enemies:
            e.draw(canvas, cam_x)
        for p in world.powerups:
            p.draw(canvas, cam_x)
        for fb in world.projectiles:
            fb.draw(canvas, cam_x)
        player.draw(canvas, cam_x)

        # HUD on top of the window surface (post-scale)
        if SCALE != 1.0:
            pygame.transform.smoothscale(canvas, (DISPLAY_W, DISPLAY_H), window)
        else:
            window.blit(canvas, (0, 0))
        draw_hud(window)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    run()
