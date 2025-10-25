#!/usr/bin/env python3
"""
Ultra Mario 2D Bros — Somari PC Edition (SMB1 GFX Mod)
---------------------------------------
• 1990 id Software–style Carmack scrolling (tile-dirty buffer)
• SMB1-style 8x8 hardcoded tiles
• Somari-style hybrid physics (momentum + Mario jump + spin dash + jump slowdown)
• Synth APU (square + noise)
• No external files — pure Pygame 3.11+
• Tuned to 60 FPS with Master System-inspired speeds (top speed 12 px/frame, lighter accel/decel)
---------------------------------------
Controls:
  ←/→   Move   ↑/SPACE  Jump   ↓  Spin-dash (hold to charge, release to boost)
  R Restart   ESC Quit
"""

import math, random, sys, pygame
from array import array

# =========================================================
# CONFIG
# =========================================================
SCALE, BASE_TILE = 3, 8
TILE_PIX = BASE_TILE * SCALE
SCREEN_WIDTH, SCREEN_HEIGHT = 600, 400
FPS = 60

# physics (tuned for Somari: slow accel, hard to stop, jump slowdown, spin dash)
GRAVITY = 0.8
MOVE_ACCEL = 0.15  # Lower for longer buildup
GROUND_FRICTION = 0.95  # Closer to 1 for harder to stop
AIR_FRICTION = 0.99
JUMP_STRENGTH = -14
JUMP_SLOWDOWN = 0.6  # Multiplier on horizontal speed when jumping
MAX_SPEED_X = 12  # Master System top speed ~12 px/frame
MAX_FALL_SPEED = 15
SPIN_CHARGE_RATE = 0.5  # Boost per frame of charge

# colors
SKY_BLUE = (107, 140, 255)
# Palettes: [0=Transparent/Sky, 1=Color1, 2=Color2, 3=Color3/Black]
PALETTES = {
    'ground': [SKY_BLUE, (216, 120, 32), (172, 56, 0), (0, 0, 0)],
    'brick': [SKY_BLUE, (252, 152, 56), (139, 69, 19), (0, 0, 0)],
    'mario': [SKY_BLUE, (252, 216, 168), (255, 0, 0), (139, 69, 19)], # 1=Skin, 2=Red, 3=Brown
    'mario_spin': [SKY_BLUE, (255, 255, 0), (255, 0, 0), (252, 216, 168)], # 1=Yellow, 2=Red, 3=Skin
    'goomba': [SKY_BLUE, (252, 216, 168), (139, 69, 19), (0, 0, 0)] # 1=Skin, 2=Brown, 3=Black
}

# =========================================================
# GFX DATA (Hardcoded 8x8 tiles and 8x16 sprites)
# =========================================================
# 0=Sky, 1=Pal1, 2=Pal2, 3=Pal3
GFX_GROUND = [
    (3, 3, 3, 3, 3, 3, 3, 3),
    (3, 2, 2, 1, 1, 2, 2, 3),
    (3, 2, 1, 1, 1, 1, 2, 3),
    (3, 1, 1, 1, 1, 1, 1, 3),
    (3, 1, 1, 1, 1, 1, 1, 3),
    (3, 2, 1, 1, 1, 1, 2, 3),
    (3, 2, 2, 1, 1, 2, 2, 3),
    (3, 3, 3, 3, 3, 3, 3, 3),
]
GFX_BRICK = [
    (3, 3, 3, 3, 3, 3, 3, 3),
    (3, 1, 1, 3, 1, 1, 1, 3),
    (3, 1, 1, 3, 1, 1, 1, 3),
    (3, 3, 3, 3, 3, 3, 3, 3),
    (3, 1, 1, 1, 3, 1, 1, 3),
    (3, 1, 1, 1, 3, 1, 1, 3),
    (3, 3, 3, 3, 3, 3, 3, 3),
    (3, 2, 2, 2, 2, 2, 2, 3), # Shadow row
]
GFX_QBLOCK = [
    (3, 3, 3, 3, 3, 3, 3, 3),
    (3, 2, 1, 1, 1, 1, 2, 3),
    (3, 1, 2, 1, 1, 2, 1, 3),
    (3, 1, 1, 2, 2, 1, 1, 3),
    (3, 1, 1, 2, 1, 1, 2, 3),
    (3, 1, 2, 1, 1, 2, 1, 3),
    (3, 2, 1, 1, 2, 1, 1, 3),
    (3, 3, 3, 3, 3, 3, 3, 3),
]

# 8x16 "Mario-like" sprite
GFX_MARIO_STAND = [
    (0, 0, 2, 2, 2, 2, 0, 0), # Red Hat
    (0, 2, 2, 2, 2, 2, 2, 0),
    (0, 0, 3, 1, 1, 3, 0, 0), # Moustache + Skin
    (0, 0, 3, 1, 1, 3, 0, 0),
    (0, 0, 3, 3, 3, 3, 0, 0),
    (0, 0, 2, 2, 2, 2, 0, 0), # Red Torso
    (0, 2, 2, 3, 3, 2, 2, 0), # Overalls
    (0, 2, 2, 3, 3, 2, 2, 0),
    (0, 2, 2, 3, 3, 2, 2, 0),
    (0, 2, 2, 0, 0, 2, 2, 0),
    (0, 3, 3, 0, 0, 3, 3, 0), # Brown Boots
    (0, 3, 3, 0, 0, 3, 3, 0),
    (0, 3, 3, 0, 0, 3, 3, 0),
    (0, 3, 3, 0, 0, 3, 3, 0),
    (0, 0, 0, 0, 0, 0, 0, 0),
    (0, 0, 0, 0, 0, 0, 0, 0),
]
GFX_MARIO_JUMP = [
    (0, 0, 2, 2, 2, 2, 0, 0), # Red Hat
    (0, 2, 2, 2, 2, 2, 2, 0),
    (0, 0, 3, 1, 1, 3, 0, 0), # Moustache + Skin
    (0, 0, 3, 1, 1, 3, 0, 0),
    (0, 0, 3, 3, 3, 3, 0, 0),
    (0, 2, 2, 2, 2, 2, 0, 0), # Red Torso / Arm
    (2, 2, 3, 3, 2, 2, 2, 0), # Overalls
    (2, 2, 3, 3, 2, 2, 0, 0),
    (2, 2, 3, 3, 2, 2, 0, 0),
    (0, 0, 3, 3, 0, 0, 0, 0),
    (0, 0, 3, 3, 0, 3, 3, 0), # Brown Boots
    (0, 0, 3, 3, 0, 3, 3, 0),
    (0, 0, 3, 0, 0, 3, 3, 0),
    (0, 0, 3, 0, 0, 3, 3, 0),
    (0, 0, 0, 0, 0, 0, 0, 0),
    (0, 0, 0, 0, 0, 0, 0, 0),
]
GFX_MARIO_SKID = GFX_MARIO_JUMP # Reuse jump sprite for spin

# 8x8 "Goomba-like" sprite
GFX_GOOMBA = [
    (0, 0, 2, 2, 2, 2, 0, 0), # Brown head
    (0, 2, 2, 2, 2, 2, 2, 0),
    (0, 2, 3, 2, 2, 3, 2, 0), # Eyes
    (0, 2, 3, 2, 2, 3, 2, 0),
    (0, 2, 2, 2, 2, 2, 2, 0),
    (0, 0, 1, 1, 1, 1, 0, 0), # Skin body
    (0, 1, 1, 1, 1, 1, 1, 0),
    (3, 3, 0, 0, 0, 0, 3, 3), # Feet
]

# =========================================================
# INIT
# =========================================================
pygame.init()
AUDIO_ENABLED = True
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
except Exception:
    AUDIO_ENABLED = False

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Ultra Mario 2D Bros — Somari PC Edition")
clock = pygame.time.Clock()

# =========================================================
# PPU — Renders hardcoded GFX data
# =========================================================
class PPU:
    def __init__(self, scale=SCALE):
        self.scale = scale
        self.tile_pix = BASE_TILE * scale
        self._cache = {}
        # Link Tile IDs to GFX data
        self.tile_data = { 1: GFX_GROUND, 2: GFX_BRICK, 3: GFX_QBLOCK, 4: GFX_GOOMBA }
        # Link Sprite names to GFX data
        self.sprite_data = {
            'stand': GFX_MARIO_STAND,
            'jump': GFX_MARIO_JUMP,
            'skid': GFX_MARIO_SKID
        }

    def tile_surface(self, tid):
        """Creates a scaled 8x8 tile surface from GFX data"""
        key = tid
        if key in self._cache:
            return self._cache[key]

        if tid == 1:
            gfx, pal_name = self.tile_data[1], 'ground'
        elif tid == 2:
            gfx, pal_name = self.tile_data[2], 'brick'
        elif tid == 3:
            gfx, pal_name = self.tile_data[3], 'brick' # Q-block uses brick palette
        elif tid == 4:
            gfx, pal_name = self.tile_data[4], 'goomba'
        else: # tid == 0 (Sky)
            surf = pygame.Surface((self.tile_pix, self.tile_pix))
            surf.fill(SKY_BLUE)
            self._cache[key] = surf
            return surf

        # Create base 8x8 surface
        base_surf = pygame.Surface((BASE_TILE, BASE_TILE))
        palette = PALETTES[pal_name]
        for y, row in enumerate(gfx):
            for x, c in enumerate(row):
                base_surf.set_at((x, y), palette[c])
        
        # Scale up
        scaled_surf = pygame.transform.scale(base_surf, (self.tile_pix, self.tile_pix))
        scaled_surf.set_colorkey(SKY_BLUE) # Use sky for transparency
        self._cache[key] = scaled_surf
        return scaled_surf

    def sprite_surface(self, name, palette_name, facing_right=True):
        """Creates a scaled 8x16 sprite surface from GFX data"""
        key = (name, palette_name, facing_right)
        if key in self._cache:
            return self._cache[key]

        if name not in self.sprite_data:
            return self.tile_surface(0) # Return blank sky tile

        gfx = self.sprite_data[name]
        palette = PALETTES[palette_name]
        
        # Create base 8x16 surface
        base_surf = pygame.Surface((BASE_TILE, BASE_TILE * 2), pygame.SRCALPHA)
        base_surf.fill(SKY_BLUE) # Transparent background
        
        for y, row in enumerate(gfx):
            for x, c in enumerate(row):
                if c != 0: # 0 is transparent
                    base_surf.set_at((x, y), palette[c])
        
        # Flip if needed
        if not facing_right:
            base_surf = pygame.transform.flip(base_surf, True, False)
            
        # Scale up
        scaled_surf = pygame.transform.scale(base_surf, (self.tile_pix, self.tile_pix * 2))
        scaled_surf.set_colorkey(SKY_BLUE)
        self._cache[key] = scaled_surf
        return scaled_surf

# =========================================================
# APU Synth (Unchanged)
# =========================================================
class APU:
    def __init__(self):
        self.enabled = AUDIO_ENABLED
        if not self.enabled: return
        self.ch = pygame.mixer.Channel(0)
        self.jump = self._tone(220,440,0.12)
        self.spin = self._noise(100)

    def _tone(self,f1,f2,dur):
        sr=22050; buf=array('h')
        for i in range(int(sr*dur)):
            f=f1+(f2-f1)*(1-i/(sr*dur))
            s=int(math.sin(2*math.pi*f*i/sr)*16000)
            buf.extend((s,s))
        return pygame.mixer.Sound(buffer=buf.tobytes())

    def _noise(self,ms,vol=0.3):
        n=int(22050*ms/1000); buf=array('h'); amp=int(32767*vol); reg=1
        for _ in range(n):
            bit=(reg^(reg>>1))&1; reg=(reg>>1)|(bit<<14)
            v=amp if reg&1 else -amp; buf.extend((v,v))
        return pygame.mixer.Sound(buffer=buf.tobytes())

    def play_jump(self): 
        if self.enabled: self.ch.play(self.jump)
    def play_spin(self): 
        if self.enabled: self.ch.play(self.spin)

# =========================================================
# ENTITIES
# =========================================================
class Goomba:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TILE_PIX, TILE_PIX) # 8x8 base sprite
        self.vel_x = -1 # Start moving left
        self.vel_y = 0
        self.on_ground = False

    def update(self, level):
        # --- Physics ---
        self.vel_y += GRAVITY
        if self.vel_y > MAX_FALL_SPEED: self.vel_y = MAX_FALL_SPEED
        
        self.rect.x += self.vel_x
        self.collide_level(level, dx=True)
        self.rect.y += int(self.vel_y)
        self.on_ground = False
        self.collide_level(level, dx=False)
        
    def collide_level(self, level, dx):
        """Collision with the level tiles"""
        for y, row in enumerate(level.tiles):
            for x, t in enumerate(row):
                if t > 0:
                    r = pygame.Rect(x*TILE_PIX, y*TILE_PIX, TILE_PIX, TILE_PIX)
                    if self.rect.colliderect(r):
                        if dx:
                            if self.vel_x > 0: self.rect.right = r.left
                            elif self.vel_x < 0: self.rect.left = r.right
                            self.vel_x *= -1 # Turn around
                        else:
                            if self.vel_y > 0:
                                self.rect.bottom = r.top
                                self.on_ground = True
                                self.vel_y = 0
                            elif self.vel_y < 0:
                                self.rect.top = r.bottom
                                self.vel_y = 0
                                

    def on_stomp(self, level):
        """Called when player stomps this goomba"""
        level.entities.remove(self)
        # TODO: Add a stomp sound

    def draw(self, surf, ppu, screen_rect):
        sprite_surf = ppu.tile_surface(4) # Tile ID 4 is Goomba
        surf.blit(sprite_surf, screen_rect)

# =========================================================
# SOMARI PLAYER (Updated with spin dash charging and jump slowdown)
# =========================================================
class Somari:
    def __init__(self,x,y):
        self.rect = pygame.Rect(x,y,TILE_PIX,TILE_PIX*2) # 8x16 base sprite
        self.vel_x=self.vel_y=0
        self.on_ground=False
        self.spin_mode=False
        self.charge=0
        self.facing_right=True
        self.jumping=False  # Track if just jumped this frame

    def handle_input(self,keys,apu):
        ax=0
        down_pressed = keys[pygame.K_DOWN]
        
        if down_pressed and self.on_ground:
            # Spin dash charging
            if self.charge == 0:
                apu.play_spin()
            self.charge += 1
            self.spin_mode = True
            ax = 0  # No horizontal movement while charging
            self.facing_right = self.vel_x >= 0  # Face current direction
        else:
            if self.spin_mode and self.charge > 0:
                # Release spin dash
                boost = min(self.charge * SPIN_CHARGE_RATE, MAX_SPEED_X)
                self.vel_x += boost if self.facing_right else -boost
                self.charge = 0
                self.spin_mode = False
            else:
                self.spin_mode = False
            
            # Normal movement if not spinning
            if not self.spin_mode:
                if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    ax=-MOVE_ACCEL
                    self.facing_right=False
                if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    ax= MOVE_ACCEL
                    self.facing_right=True
                
                # Jump
                if (keys[pygame.K_UP] or keys[pygame.K_SPACE]) and self.on_ground:
                    self.vel_y=JUMP_STRENGTH
                    self.on_ground=False
                    self.jumping = True  # Flag for slowdown
                    apu.play_jump()
                else:
                    self.jumping = False
        
        # Apply acceleration
        self.vel_x += ax
        
        # Friction
        friction = GROUND_FRICTION if self.on_ground else AIR_FRICTION
        self.vel_x *= friction
        
        # Cap speed
        self.vel_x = max(-MAX_SPEED_X, min(MAX_SPEED_X, self.vel_x))

    def update(self,level):
        # Apply jump slowdown if just jumped
        if self.jumping:
            self.vel_x *= JUMP_SLOWDOWN
            self.jumping = False
        
        self.vel_y += GRAVITY
        if self.vel_y>MAX_FALL_SPEED: self.vel_y=MAX_FALL_SPEED
        self.rect.x += int(self.vel_x)
        self.collide(level,dx=True)
        self.rect.y += int(self.vel_y)
        self.on_ground=False
        self.collide(level,dx=False)

        self.collide_entities(level) # Check for entity collisions

    def collide(self,level,dx):
        for y,row in enumerate(level.tiles):
            for x,t in enumerate(row):
                if t > 0: # Any tile ID > 0 is solid
                    r=pygame.Rect(x*TILE_PIX,y*TILE_PIX,TILE_PIX,TILE_PIX)
                    if self.rect.colliderect(r):
                        if dx:
                            if self.vel_x>0:self.rect.right=r.left
                            elif self.vel_x<0:self.rect.left=r.right
                            self.vel_x=0
                        else:
                            if self.vel_y>0:self.rect.bottom=r.top; self.on_ground=True
                            elif self.vel_y<0:self.rect.top=r.bottom
                            self.vel_y=0

    def collide_entities(self, level):
        """Handle collisions with entities"""
        for e in level.entities[:]: # Iterate on a copy
            if self.rect.colliderect(e.rect):
                # Check for stomp
                # Player is falling (vel_y > 0)
                # Player's feet are just above the goomba's center
                is_stomp = self.vel_y > 0 and self.rect.bottom < e.rect.centery + TILE_PIX/2
                
                if is_stomp:
                    e.on_stomp(level)
                    self.vel_y = JUMP_STRENGTH * 0.6 # Small bounce
                # X-axis collision (hurt)
                else:
                    self.on_hurt(level)
                    
    def on_hurt(self, level):
        """Called when player is hurt"""
        # For simplicity, just reset position
        self.rect.x = 4 * TILE_PIX
        self.rect.y = SCREEN_HEIGHT - 5 * TILE_PIX
        self.vel_x = 0
        self.vel_y = 0
        self.charge = 0
        self.spin_mode = False

    def draw(self, surf, ppu, screen_rect):
        """Draws the player sprite relative to the screen"""
        if self.spin_mode:
            pal = 'mario_spin'
            sprite_name = 'skid'
        elif not self.on_ground:
            pal = 'mario'
            sprite_name = 'jump'
        else:
            pal = 'mario'
            sprite_name = 'stand'
        
        # Get the correct sprite surface from the PPU
        sprite_surf = ppu.sprite_surface(sprite_name, pal, self.facing_right)
        surf.blit(sprite_surf, screen_rect)

# =========================================================
# CARMACK SCROLLER (Render method updated)
# =========================================================
class CarmackScroller:
    def __init__(self,ppu,level):
        self.ppu=ppu; self.level=level
        # Buffer is wider to hold tiles that are partially scrolled in
        self.buffer=pygame.Surface((SCREEN_WIDTH+TILE_PIX,SCREEN_HEIGHT))
        self.buffer.set_colorkey(SKY_BLUE)
        self.buffer.fill(SKY_BLUE)
        self.prev_x=0

    def render(self,surf,cam_x):
        dx=int(cam_x-self.prev_x)
        if dx==0:
            surf.blit(self.buffer,(0,0)); return
            
        self.buffer.scroll(-dx,0)
        
        new_cols_rect = None
        
        # right scroll: draw new columns on the right edge
        if dx>0:
            cols=(dx+TILE_PIX-1)//TILE_PIX
            start_col = int((cam_x + SCREEN_WIDTH) // TILE_PIX)
            # Area to draw new columns
            new_cols_rect = pygame.Rect(self.buffer.get_width() - cols * TILE_PIX, 0, cols * TILE_PIX, SCREEN_HEIGHT)
            
            for i in range(cols + 1):
                x = start_col + i
                for y,row in enumerate(self.level.tiles):
                    if 0<=x<len(row) and row[x] > 0: # 0 is sky
                        t=self.ppu.tile_surface(row[x])
                        # Calculate blit position in the buffer
                        buf_x = x * TILE_PIX - cam_x
                        self.buffer.blit(t, (buf_x, y*TILE_PIX))

        # left scroll: draw new columns on the left edge
        elif dx<0:
            cols = (-dx + TILE_PIX - 1) // TILE_PIX
            start_col = int(cam_x // TILE_PIX)
            # Area to draw new columns
            new_cols_rect = pygame.Rect(0, 0, cols * TILE_PIX, SCREEN_HEIGHT)

            for i in range(cols + 1):
                x = start_col + i
                for y,row in enumerate(self.level.tiles):
                    if 0<=x<len(row) and row[x] > 0: # 0 is sky
                        t=self.ppu.tile_surface(row[x])
                        # Calculate blit position in the buffer
                        buf_x = x * TILE_PIX - cam_x
                        self.buffer.blit(t, (buf_x, y*TILE_PIX))
        
        self.prev_x=cam_x
        surf.blit(self.buffer,(0,0))

# =========================================================
# LEVEL (Build method updated)
# =========================================================
class Level:
    def __init__(self,ppu):
        self.ppu=ppu; self.tiles=[]; self.entities = []
        self._build()

    def _build(self):
        cols,rows=200,15
        self.tiles=[[0 for _ in range(cols)] for _ in range(rows)]
        g=rows-2 # Ground level
        
        for x in range(cols):
            # Two-tile thick floor
            self.tiles[g][x]=1
            self.tiles[g+1][x]=1
            
            # Add some brick/q-blocks
            if 10 < x < 18:
                self.tiles[g-3][x] = 2 # Bricks
            if x == 14:
                 self.tiles[g-3][x] = 3 # Q-Block
            
            if x in (25, 27):
                self.tiles[g-4][x] = 3 # Floating Q-Blocks
            if x == 26:
                self.tiles[g-4][x] = 2 # Floating brick
                
            if 35 < x < 40:
                self.tiles[g-5][x] = 2

        # --- Spawn Entities ---
        self.entities.append(Goomba(16 * TILE_PIX, (g - 1) * TILE_PIX))
        self.entities.append(Goomba(19 * TILE_PIX, (g - 1) * TILE_PIX))
        self.entities.append(Goomba(29 * TILE_PIX, (g - 1) * TILE_PIX))
        self.entities.append(Goomba(30 * TILE_PIX, (g - 1) * TILE_PIX))

# =========================================================
# GAME LOOP (Render logic updated)
# =========================================================
def main():
    ppu=PPU(); apu=APU(); lvl=Level(ppu)
    hero=Somari(4*TILE_PIX,SCREEN_HEIGHT-5*TILE_PIX)
    cam_x=0; scroller=CarmackScroller(ppu,lvl)
    running=True
    
    while running:
        clock.tick(FPS)
        
        for e in pygame.event.get():
            if e.type==pygame.QUIT or (e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE): running=False
            if e.type==pygame.KEYDOWN and e.key==pygame.K_r: 
                hero = Somari(4*TILE_PIX,SCREEN_HEIGHT-5*TILE_PIX)
                cam_x = 0
                scroller = CarmackScroller(ppu, lvl)
                
        keys=pygame.key.get_pressed()
        hero.handle_input(keys,apu)
        hero.update(lvl)
        
        # Update all entities
        for e in lvl.entities[:]: # Iterate on a copy
            e.update(lvl)
        
        # Center camera on player
        cam_x=hero.rect.centerx-SCREEN_WIDTH//2
        # Don't let camera scroll past level start
        if cam_x < 0: cam_x = 0
        
        # --- RENDER ---
        
        # 1. Fill screen with sky color (replaces draw_parallax)
        screen.fill(SKY_BLUE)
        
        # 2. Draw the scrolling tilemap
        scroller.render(screen,cam_x)
        
        # 3. Draw all entities
        for e in lvl.entities:
            e_screen_rect = e.rect.copy()
            e_screen_rect.x -= int(cam_x)
            if e_screen_rect.colliderect(screen.get_rect()): # Only draw if on screen
                e.draw(screen, ppu, e_screen_rect)
        
        # 4. Draw the player at screen-relative coordinates
        hero_screen_rect = hero.rect.copy()
        hero_screen_rect.x -= int(cam_x)
        hero.draw(screen, ppu, hero_screen_rect)
        
        # 5. Flip display
        pygame.display.flip()
        
    pygame.quit()

if __name__=="__main__":
    main()
