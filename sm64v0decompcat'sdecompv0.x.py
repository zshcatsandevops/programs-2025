#!/usr/bin/env python3
"""
Ultra Mario 64 — SpaceWorld '95 Demo (single file)
Engine fixes + SpaceWorld-style main menu + playable 3D demo using Ursina.

Dependencies:
    pip install ursina

Run:
    python program.py
"""

from ursina import *
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import math
import random
import time as pytime


# ------------------------------
# Constants & Tunables
# ------------------------------
GRAVITY = 40
JUMP_HEIGHT = 12
MARIO_SPEED = 8
MARIO_RUN_SPEED = 14
LONG_JUMP_SPEED = 20
DIVE_SPEED = 18
GROUND_POUND_SPEED = 30
WALL_JUMP_HEIGHT = 14
CAMERA_DISTANCE = 8
CAMERA_HEIGHT = 4

GOLD = color.rgb(212, 175, 55)
UI_Y = 0.45


# ------------------------------
# Game & Mario States
# ------------------------------
class GameState(Enum):
    INTRO = 'intro'
    TITLE = 'title'
    FILE_SELECT = 'file_select'
    MARIO_FACE = 'mario_face'
    CASTLE = 'castle'
    LEVEL = 'level'
    PAUSE = 'pause'
    STAR_GET = 'star_get'
    ATTRACT = 'attract'
    GAME_OVER = 'game_over'


class MarioState(Enum):
    IDLE = 'idle'
    WALKING = 'walking'
    RUNNING = 'running'
    JUMPING = 'jumping'
    LONG_JUMPING = 'long_jumping'
    WALL_SLIDING = 'wall_sliding'
    WALL_JUMPING = 'wall_jumping'
    GROUND_POUND = 'ground_pound'
    DIVING = 'diving'


# ------------------------------
# Save Data
# ------------------------------
@dataclass
class SaveData:
    stars: int = 0
    coins: int = 0
    lives: int = 4
    collected_stars: List[str] = field(default_factory=list)


# ------------------------------
# Mario
# ------------------------------
class Mario(Entity):
    def __init__(self):
        super().__init__(
            name='Mario',
            model='cube',
            color=color.red,
            scale=(1, 2, 1),
            position=(0, 2, 0),
            collider='box'
        )
        self.velocity = Vec3(0, 0, 0)
        self.grounded = False
        self.state = MarioState.IDLE
        self.jump_cooldown = 0.0

        self.health = 8
        self.coins = 0
        self.stars = 0
        self.lives = 4

        # Simple blocky "Mario"
        self._build_body()

        # Camera
        self.camera_pivot = Entity()
        camera.parent = self.camera_pivot
        camera.position = (0, CAMERA_HEIGHT, -CAMERA_DISTANCE)
        camera.rotation_x = 20

    def _build_body(self):
        self.head = Entity(parent=self, model='sphere', color=color.rgb(255, 200, 150),
                           scale=(0.8, 0.8, 0.8), position=(0, 0.8, 0))
        self.hat = Entity(parent=self.head, model='cube', color=color.red, scale=(1.2, 0.4, 1.2), position=(0, 0.5, 0))
        self.body = Entity(parent=self, model='cube', color=color.red, scale=(0.8, 1, 0.6), position=(0, 0, 0))
        self.overalls = Entity(parent=self.body, model='cube', color=color.blue, scale=(1.1, 0.7, 1.1), position=(0, -0.3, 0))
        self.left_arm  = Entity(parent=self, model='cube', color=color.rgb(255, 200, 150), scale=(0.3, 0.8, 0.3), position=(-0.6, 0, 0))
        self.right_arm = Entity(parent=self, model='cube', color=color.rgb(255, 200, 150), scale=(0.3, 0.8, 0.3), position=(0.6, 0, 0))
        self.left_leg  = Entity(parent=self, model='cube', color=color.blue, scale=(0.35, 0.8, 0.35), position=(-0.25, -0.8, 0))
        self.right_leg = Entity(parent=self, model='cube', color=color.blue, scale=(0.35, 0.8, 0.35), position=(0.25, -0.8, 0))

    def input(self, key):
        if key == 'space' and self.grounded and self.jump_cooldown <= 0:
            self.velocity.y = JUMP_HEIGHT
            self.state = MarioState.JUMPING
            self.jump_cooldown = 0.2

        elif key == 'left ctrl' and not self.grounded:
            self.velocity.y = -GROUND_POUND_SPEED
            self.state = MarioState.GROUND_POUND

        elif key == 'q' and not self.grounded:
            forward = Vec3(0, 0, 1).rotated((0, self.rotation_y, 0))
            self.velocity = forward * DIVE_SPEED
            self.velocity.y = -5
            self.state = MarioState.DIVING

    def update(self):
        self._handle_move_input()
        self._physics()
        self._update_camera()

        if self.jump_cooldown > 0:
            self.jump_cooldown -= time.dt

    def _handle_move_input(self):
        move = Vec3(0, 0, 0)
        if held_keys['w'] or held_keys['up arrow']:
            move.z += 1
        if held_keys['s'] or held_keys['down arrow']:
            move.z -= 1
        if held_keys['a'] or held_keys['left arrow']:
            move.x -= 1
        if held_keys['d'] or held_keys['right arrow']:
            move.x += 1

        if move.length() > 0:
            move = move.normalized()
            speed = MARIO_RUN_SPEED if held_keys['left shift'] else MARIO_SPEED
            self.velocity.x = move.x * speed
            self.velocity.z = move.z * speed
            self.rotation_y = math.degrees(math.atan2(move.x, move.z))
            if self.grounded:
                self.state = MarioState.RUNNING if speed > MARIO_SPEED else MarioState.WALKING
        else:
            if self.grounded:
                self.state = MarioState.IDLE
            self.velocity.x *= 0.85
            self.velocity.z *= 0.85

    def _physics(self):
        if not self.grounded:
            self.velocity.y -= GRAVITY * time.dt

        # Apply
        self.position += self.velocity * time.dt

        # Ground raycast
        ray = raycast(self.position, Vec3(0, -1, 0), distance=1.1, ignore=[self])
        if ray.hit:
            self.grounded = True
            self.position = ray.world_point + Vec3(0, 1, 0)
            if self.velocity.y < 0:
                self.velocity.y = 0
        else:
            self.grounded = False

        # Wall slide detection
        for d in (Vec3(1,0,0), Vec3(-1,0,0), Vec3(0,0,1), Vec3(0,0,-1)):
            if raycast(self.position, d, distance=0.6, ignore=[self]).hit and not self.grounded:
                self.state = MarioState.WALL_SLIDING
                self.velocity.y = max(self.velocity.y, -2)
                break

    def _update_camera(self):
        # Smooth follow
        self.camera_pivot.position = lerp(self.camera_pivot.position, self.position, min(1, time.dt * 6))
        if held_keys['right mouse']:
            camera.rotation_y += mouse.velocity[0] * 100
            camera.rotation_x -= mouse.velocity[1] * 100
            camera.rotation_x = clamp(camera.rotation_x, -80, 80)

    # Interactions
    def collect_coin(self):
        self.coins += 1
        if self.coins >= 100:
            self.lives += 1
            self.coins -= 100

    def collect_star(self):
        self.stars += 1

    def take_damage(self, amount=1):
        self.health -= amount
        if self.health <= 0:
            self.lives -= 1
            self.respawn()

    def respawn(self):
        self.position = Vec3(0, 2, 0)
        self.velocity = Vec3(0, 0, 0)
        self.health = 8
        self.state = MarioState.IDLE


# ------------------------------
# Collectibles
# ------------------------------
class Star(Entity):
    def __init__(self, position, star_id):
        super().__init__(
            model='sphere',
            color=color.yellow,
            scale=0.8,
            position=position,
            collider='sphere'
        )
        self.star_id = star_id
        self._t0 = pytime.time()

        # Rays
        self.rays = []
        for i in range(5):
            angle = i * 72
            ray = Entity(parent=self, model='cube', color=color.yellow, scale=(2, 0.1, 0.1), rotation_z=angle)
            self.rays.append(ray)

    def update(self):
        t = pytime.time() - self._t0
        self.rotation_y += 100 * time.dt
        self.y = self.y + math.sin(t * 2) * 0.003
        if random.random() < 0.07:
            p = Entity(model='sphere', color=color.white, scale=0.08, position=self.position + Vec3(random.uniform(-1,1), random.uniform(-1,1), random.uniform(-1,1)))
            p.animate_scale(0, duration=0.4)
            destroy(p, delay=0.4)

    def collect(self):
        self.animate_scale(2, duration=0.4)
        self.animate_position(self.position + Vec3(0, 3, 0), duration=0.4)
        self.animate_rotation(Vec3(0, 720, 0), duration=0.4)
        destroy(self, delay=0.45)


class Coin(Entity):
    def __init__(self, position, color_=color.yellow, value=1):
        super().__init__(model='cylinder', color=color_, scale=(0.5, 0.1, 0.5), position=position, collider='box')
        self.rotation_speed = 200
        self.value = value

    def update(self):
        self.rotation_y += self.rotation_speed * time.dt

    def collect(self):
        for i in range(4):
            particle = Entity(model='sphere', color=color.yellow, scale=0.1, position=self.position)
            dir = Vec3(random.uniform(-1, 1), random.uniform(0, 2), random.uniform(-1, 1)).normalized()
            particle.animate_position(self.position + dir * 2, duration=0.3)
            particle.animate_scale(0, duration=0.3)
            destroy(particle, delay=0.3)
        destroy(self)


class RedCoin(Coin):
    def __init__(self, position):
        super().__init__(position, color_=color.red, value=2)


class BlueCoin(Coin):
    def __init__(self, position):
        super().__init__(position, color_=color.azure, value=5)


# ------------------------------
# Enemies (simple placeholders)
# ------------------------------
class Goomba(Entity):
    def __init__(self, position):
        super().__init__(model='cube', color=color.brown, scale=(0.8, 0.8, 0.8), position=position, collider='box')
        self.velocity = Vec3(random.choice([-1, 1]), 0, 0)
        self.grounded = False

    def update(self):
        self.position += self.velocity * time.dt
        if not self.grounded:
            self.velocity.y -= GRAVITY * time.dt

        # Ground
        ray = raycast(self.position, Vec3(0,-1,0), distance=0.6, ignore=[self])
        if ray.hit:
            self.grounded = True
            self.position = ray.world_point + Vec3(0, .4, 0)
            self.velocity.y = 0
        else:
            self.grounded = False

        # Walls
        front = raycast(self.position, self.velocity.normalized(), distance=0.5, ignore=[self])
        if front.hit:
            self.velocity.x *= -1


# ------------------------------
# Level System
# ------------------------------
class Level:
    def __init__(self, name):
        self.name = name
        self.root = Entity(name=f'{name}_root')
        self.stars: List[Star] = []
        self.coins: List[Entity] = []
        self.enemies: List[Entity] = []
        self.platforms: List[Entity] = []
        self.spawn_point = Vec3(0, 2, 0)

    def enable(self, enabled=True):
        self.root.enabled = enabled

    def destroy(self):
        destroy(self.root)

    def load(self):
        self.create_terrain()
        self.place_stars()
        self.place_coins()
        self.spawn_enemies()

    # Virtuals
    def create_terrain(self): ...
    def place_stars(self): ...
    def place_coins(self): ...
    def spawn_enemies(self): ...


class BobOmbBattlefield(Level):
    def __init__(self):
        super().__init__('Bob-omb Battlefield')

    def create_terrain(self):
        ground = Entity(parent=self.root, model='cube', texture='white_cube', color=color.green,
                        scale=(100, 2, 100), position=(0, 0, 0), collider='box')
        self.platforms.append(ground)

        # Some hills
        for _ in range(6):
            x, z = random.uniform(-35, 35), random.uniform(-35, 35)
            hill = Entity(parent=self.root, model='sphere', color=color.green,
                          scale=(random.uniform(10, 20), random.uniform(5, 10), random.uniform(10, 20)),
                          position=(x, 2, z), collider='box')
            self.platforms.append(hill)

        # Simple bridge
        for i in range(10):
            plank = Entity(parent=self.root, model='cube', color=color.brown, scale=(2, 0.2, 8),
                           position=(-20 + i * 2, 5, 0), collider='box')
            self.platforms.append(plank)

        # A little path up a slope
        for i in range(15):
            seg = Entity(parent=self.root, model='cube', color=color.gray, scale=(4, 0.5, 4),
                         position=(30, 2 + i * 0.5, -30 + i * 2), collider='box')
            self.platforms.append(seg)

        self.spawn_point = Vec3(0, 3, -20)

    def place_stars(self):
        self.stars.append(Star(Vec3(30, 12, 10), 'bob_1'))
        self.stars.append(Star(Vec3(-30, 2, -30), 'bob_2'))
        self.stars.append(Star(Vec3(0, 15, 0), 'bob_3'))
        for s in self.stars:
            s.parent = self.root

    def place_coins(self):
        for _ in range(40):
            x, z = random.uniform(-45, 45), random.uniform(-45, 45)
            c = Coin(Vec3(x, 2, z))
            c.parent = self.root
            self.coins.append(c)
        red_positions = [Vec3(10,3,10), Vec3(-10,3,10), Vec3(10,3,-10), Vec3(-10,3,-10),
                         Vec3(20,6,0), Vec3(-20,6,0), Vec3(0,8,20), Vec3(0,8,-20)]
        for p in red_positions:
            rc = RedCoin(p)
            rc.parent = self.root
            self.coins.append(rc)

    def spawn_enemies(self):
        for _ in range(6):
            x, z = random.uniform(-25, 25), random.uniform(-25, 25)
            g = Goomba(Vec3(x, 2, z))
            g.parent = self.root
            self.enemies.append(g)


# ------------------------------
# Peach's Castle (hub)
# ------------------------------
class LevelPainting(Entity):
    def __init__(self, name, position, rotation, base_color, stars_required):
        super().__init__(
            parent=None,
            model='quad',
            color=base_color,
            scale=(4, 5, 1),
            position=position,
            rotation=rotation,
            collider='box'
        )
        self.level_name = name
        self.stars_required = stars_required

        # Frame
        Entity(parent=self, model='cube', color=GOLD, scale=(1.05, 1.05, 0.05), position=(0, 0, -0.06))

        # Title
        Text(parent=self, text=name, origin=(0,0), scale=1.6, position=(0, -0.6, -0.1), color=color.white)

        # Requirement
        Text(parent=self, text=f'{stars_required}★', origin=(0,0), scale=1.2, position=(0, -0.95, -0.1), color=color.yellow)


class PeachsCastle:
    def __init__(self):
        self.root = Entity(name='castle_root')
        self.paintings: List[LevelPainting] = []
        self._build()

    def _build(self):
        # Main floor
        Entity(parent=self.root, model='cube', texture='white_cube', color=color.rgb(200, 150, 100),
               scale=(40, 1, 60), position=(0, 0, 0), collider='box')
        # Walls
        for x in [-20, 20]:
            Entity(parent=self.root, model='cube', texture='white_cube', color=color.rgb(230, 200, 170),
                   scale=(1, 20, 60), position=(x, 10, 0), collider='box')
        Entity(parent=self.root, model='cube', texture='white_cube', color=color.rgb(230, 200, 170),
               scale=(40, 20, 1), position=(0, 10, 30), collider='box')

        # A few pillars
        for x, z in [(-10,-10),(10,-10),(-10,10),(10,10)]:
            Entity(parent=self.root, model='cylinder', texture='white_cube', color=color.white,
                   scale=(2, 10, 2), position=(x, 5, z), collider='box')

        # Paintings (hub entries)
        cfgs = [
            {"name": "Bob-omb Battlefield", "position": (-19, 5, -10), "rotation": (0, 90, 0), "base_color": color.green, "stars_required": 0},
            {"name": "Whomp's Fortress", "position": (-19, 5, 0), "rotation": (0, 90, 0), "base_color": color.gray, "stars_required": 1},
            {"name": "Jolly Roger Bay", "position": (-19, 5, 10), "rotation": (0, 90, 0), "base_color": color.azure, "stars_required": 3},
        ]
        for c in cfgs:
            p = LevelPainting(c["name"], c["position"], c["rotation"], c["base_color"], c["stars_required"])
            p.parent = self.root
            self.paintings.append(p)


# ------------------------------
# Mario Face Screen (stretchy face toy)
# ------------------------------
class MarioFace(Entity):
    def __init__(self):
        super().__init__(model='sphere', texture='white_cube', scale=3, position=(0, 0, 5))
        self.face_parts = {}
        self._make_face()
        self.dragging = False

    def _make_face(self):
        self.face_parts['left_eye'] = Entity(parent=self, model='sphere', color=color.black, scale=(0.15, 0.2, 0.1), position=(-0.3, 0.3, -1))
        self.face_parts['right_eye'] = Entity(parent=self, model='sphere', color=color.black, scale=(0.15, 0.2, 0.1), position=(0.3, 0.3, -1))
        self.face_parts['nose'] = Entity(parent=self, model='sphere', color=color.rgb(255, 200, 150), scale=(0.3, 0.4, 0.5), position=(0, 0, -1.2))
        self.face_parts['mustache'] = Entity(parent=self, model='cube', color=color.black, scale=(0.8, 0.1, 0.2), position=(0, -0.2, -1.1))
        self.face_parts['hat'] = Entity(parent=self, model='cube', color=color.red, scale=(2, 0.8, 0.1), position=(0, 1.2, 0))

    def input(self, key):
        if key == 'left mouse down':
            self.dragging = True
        elif key == 'left mouse up':
            self.dragging = False

    def update(self):
        if self.dragging and mouse.point:
            stretch = 1 + distance(mouse.position, Vec3(0, 0, 0)) * 2
            for name, part in self.face_parts.items():
                if name != 'hat':
                    offset = part.position - self.position
                    part.position = self.position + offset * stretch


# ------------------------------
# UI
# ------------------------------
class GameUI:
    def __init__(self, game):
        self.game = game
        self._build()

    def _build(self):
        self.lives_text = Text(parent=camera.ui, text=f'MARIO × 4', position=(-0.85, UI_Y), scale=2, color=color.white)
        self.coin_text  = Text(parent=camera.ui, text=f'× 00', position=(-0.85, UI_Y-0.05), scale=2, color=color.yellow)
        self.star_text  = Text(parent=camera.ui, text=f'★ × 00', position=(0.68, UI_Y), scale=2, color=color.yellow)
        self.health_bar = Entity(parent=camera.ui, model='quad', color=color.red, scale=(0.2, 0.05), position=(0, UI_Y, -0.1))
        self.hide()

    def show(self):
        for e in (self.lives_text, self.coin_text, self.star_text, self.health_bar):
            e.enabled = True

    def hide(self):
        for e in (self.lives_text, self.coin_text, self.star_text, self.health_bar):
            e.enabled = False

    def update(self):
        if not self.game.mario:
            return
        self.lives_text.text = f'MARIO × {self.game.mario.lives}'
        self.coin_text.text  = f'× {self.game.mario.coins:02d}'
        self.star_text.text  = f'★ × {max(self.game.save.stars, self.game.mario.stars):02d}'
        hp = clamp(self.game.mario.health / 8, 0, 1)
        self.health_bar.scale_x = 0.2 * hp


# ------------------------------
# SpaceWorld '95 Title Screen
# ------------------------------
class StarField(Entity):
    def __init__(self, count=120):
        super().__init__(parent=scene)
        self.stars = []
        for _ in range(count):
            s = Entity(parent=self, model='quad', texture='white_cube', color=color.rgba(255,255,255,200),
                       scale=random.uniform(0.002, 0.01),
                       position=(random.uniform(-6,6), random.uniform(-3.5,3.5), random.uniform(2,6)))
            self.stars.append(s)

    def update(self):
        for s in self.stars:
            s.z -= time.dt * 0.3
            if s.z < 1.5:
                s.z = random.uniform(3, 6)
                s.x = random.uniform(-6, 6)
                s.y = random.uniform(-3.5, 3.5)


class TitleScreen:
    def __init__(self, game):
        self.game = game
        self.root = Entity(name='title_root')
        self.starfield = StarField()
        self.starfield.parent = self.root

        # Rotating demo star
        self.big_star = Entity(parent=self.root, model='sphere', color=color.yellow, scale=1.2, position=(0, 0.25, 2.5))
        self.big_star_pulse_t0 = pytime.time()

        # Title text
        self.title = Text(parent=camera.ui, text='ULTRA MARIO 64', scale=3, origin=(0,0), position=(0, 0.3))
        self.subtitle = Text(parent=camera.ui, text="SpaceWorld '95 Demo", scale=1.5, origin=(0,0), position=(0, 0.2), color=color.azure)
        self.prompt = Text(parent=camera.ui, text='PRESS ENTER', scale=2, origin=(0,0), position=(0, -0.2), color=color.white)
        self.hint = Text(parent=camera.ui, text='F: MARIO FACE   •   D: DEMO PLAY   •   ESC: QUIT', scale=1.2, origin=(0,0), position=(0, -0.35), color=color.rgba(255,255,255,180))

        # Demo diorama (tiny level + rotating camera)
        self.diorama_root = Entity(parent=self.root)
        ground = Entity(parent=self.diorama_root, model='cube', color=color.green, scale=(14, 1, 14), position=(0,-3,6))
        pillar = Entity(parent=self.diorama_root, model='cube', color=color.gray, scale=(2, 5, 2), position=(0,-0.5,6))
        self.cam_orbit = Entity(parent=self.diorama_root, position=(0, -1.5, 6))
        self.cam = EditorCamera(enabled=False, parent=self.cam_orbit, rotation=(10, 0, 0), position=(0, 0, -12))
        self._blink_t = 0

        # Auto-start attract demo after timeout
        invoke(self._auto_attract, delay=12)

    def _auto_attract(self):
        if self.root.enabled and self.game.state == GameState.TITLE:
            self.game.start_attract_demo()

    def enable(self, enabled=True):
        self.root.enabled = enabled
        self.title.enabled = enabled
        self.subtitle.enabled = enabled
        self.prompt.enabled = enabled
        self.hint.enabled = enabled

    def destroy(self):
        destroy(self.root)
        for w in (self.title, self.subtitle, self.prompt, self.hint):
            destroy(w)

    def update(self):
        # Spin & pulse star
        self.big_star.rotation_y += 60 * time.dt
        t = pytime.time() - self.big_star_pulse_t0
        self.big_star.scale = 1.2 + math.sin(t * 2) * 0.1

        # Orbit camera around diorama
        self.cam_orbit.rotation_y += 10 * time.dt

        # Blink prompt
        self._blink_t += time.dt
        self.prompt.alpha = 0.3 + 0.7 * abs(math.sin(self._blink_t * 3))


# ------------------------------
# Game Manager
# ------------------------------
class GameManager:
    def __init__(self):
        self.state = GameState.INTRO
        self.mario: Optional[Mario] = None
        self.save = SaveData()
        self.ui = GameUI(self)

        self.castle: Optional[PeachsCastle] = None
        self.level: Optional[Level] = None

        self.title: Optional[TitleScreen] = None
        self.mario_face: Optional[MarioFace] = None

        self._build_intro()

    # ---------- Intro & Title ----------
    def _build_intro(self):
        self.state = GameState.INTRO
        self.logo = Entity(model='cube', texture='white_cube', scale=3, position=(0, 0, 4), color=color.azure)
        self.logo.animate_rotation(Vec3(360, 360, 360), duration=2)
        invoke(self.show_title, delay=2.8)

    def show_title(self):
        if hasattr(self, 'logo'):
            destroy(self.logo)
        self.state = GameState.TITLE
        self.title = TitleScreen(self)
        self.ui.hide()

    def show_file_select(self):
        # Keep it simple: one slot — immediately start castle.
        self.start_castle()

    def show_mario_face(self):
        self.state = GameState.MARIO_FACE
        if self.title:
            self.title.enable(False)
        self.mario_face = MarioFace()
        self.face_text = Text(parent=camera.ui, text="Drag to stretch!  (ENTER: Back)",
                              scale=1.5, origin=(0,0), position=(0, -0.4))

    def hide_mario_face(self):
        if self.mario_face:
            destroy(self.mario_face)
            destroy(self.face_text)
            self.mario_face = None
        self.show_title()

    # ---------- Castle & Level ----------
    def start_castle(self):
        self.state = GameState.CASTLE
        if self.title:
            self.title.destroy()
            self.title = None

        if not self.castle:
            self.castle = PeachsCastle()

        if not self.mario:
            self.mario = Mario()
        self.mario.position = Vec3(0, 2, -10)

        self.ui.show()

    def start_level(self, name):
        if self.level:
            self.level.destroy()
            self.level = None
        if name == 'Bob-omb Battlefield':
            self.level = BobOmbBattlefield()
        else:
            # For the demo, all paintings link to Bob-omb Battlefield
            self.level = BobOmbBattlefield()

        self.level.load()
        self.level.enable(True)
        self.mario.position = self.level.spawn_point
        self.state = GameState.LEVEL

        # Level banner
        self.level_banner = Text(parent=camera.ui, text=name, origin=(0,0), position=(0, 0.32), scale=2, color=color.white)
        self.level_banner.fade_out(duration=2, delay=1)

    def exit_level_to_castle(self):
        if self.level:
            self.level.destroy()
            self.level = None
        self.start_castle()

    # ---------- Attract Demo ----------
    def start_attract_demo(self):
        self.state = GameState.ATTRACT
        if self.title:
            self.title.enable(False)
        if not self.level:
            self.level = BobOmbBattlefield()
            self.level.load()
        if not self.mario:
            self.mario = Mario()
        self.mario.position = Vec3(-25, 3, -10)
        self.ui.hide()
        self._autopilot = AutoPilot(self.mario, loop=True)

        self.attract_hint = Text(parent=camera.ui, text="Attract Mode — press ENTER to start", origin=(0,0),
                                 position=(0, -0.42), scale=1.4, color=color.rgba(255,255,255,180))

    def stop_attract_demo(self):
        if hasattr(self, '_autopilot') and self._autopilot:
            self._autopilot.stop()
        if hasattr(self, 'attract_hint') and self.attract_hint:
            destroy(self.attract_hint)
        self.start_castle()

    # ---------- Star & Coin ----------
    def on_star_collected(self, star: Star):
        self.save.stars += 1
        self.mario.collect_star()
        star.collect()
        # Simple "star get" text
        t = Text(parent=camera.ui, text="YOU GOT A STAR!", origin=(0,0), position=(0, 0.1), scale=2, color=color.yellow)
        t.fade_out(duration=1.5, delay=0.5)
        destroy(t, delay=2)

    # ---------- Per-frame Update ----------
    def update(self):
        # Title screen anim
        if self.state == GameState.TITLE and self.title:
            self.title.update()

        # Interactions in castle
        if self.state == GameState.CASTLE and self.castle and self.mario:
            for p in self.castle.paintings:
                if self.mario.intersects(p).hit:
                    if self.save.stars >= p.stars_required:
                        self.start_level(p.level_name)

        # Interactions in level
        if self.state in (GameState.LEVEL, GameState.ATTRACT) and self.level and self.mario:
            # Coins
            to_remove = []
            for c in self.level.coins:
                if not c.alive:
                    to_remove.append(c)
                    continue
                if self.mario.intersects(c).hit:
                    self.mario.collect_coin()
                    c.collect()
                    to_remove.append(c)
            for c in to_remove:
                try:
                    self.level.coins.remove(c)
                except ValueError:
                    pass

            # Stars
            to_remove = []
            for s in self.level.stars:
                if not s.alive:
                    to_remove.append(s)
                    continue
                if self.mario.intersects(s).hit:
                    self.on_star_collected(s)
                    to_remove.append(s)
            for s in to_remove:
                try:
                    self.level.stars.remove(s)
                except ValueError:
                    pass

        # UI
        self.ui.update()


# ------------------------------
# Autopilot / Attract Mode
# ------------------------------
class AutoPilot:
    def __init__(self, mario: Mario, loop=True):
        self.mario = mario
        self.loop = loop
        # Simple path
        self.path = [
            Vec3(-25, 3, -10),
            Vec3(-10, 3, 5),
            Vec3(15, 3, -5),
            Vec3(0, 3, -15),
        ]
        self._i = 0
        self._active = True
        self._tick = 0

    def stop(self):
        self._active = False

    def update(self):
        if not self._active:
            return
        target = self.path[self._i]
        delta = target - self.mario.position
        if delta.length() < 1.2:
            self._i += 1
            if self._i >= len(self.path):
                self._i = 0 if self.loop else len(self.path)-1
            return
        dir = delta.normalized()
        self.mario.velocity.x = dir.x * MARIO_RUN_SPEED
        self.mario.velocity.z = dir.z * MARIO_RUN_SPEED


# ------------------------------
# Global Input
# ------------------------------
def global_input(key):
    # Quit anytime
    if key == 'escape':
        application.quit()

    if game.state == GameState.TITLE:
        if key == 'enter':
            game.show_file_select()
        elif key == 'f':
            game.show_mario_face()
        elif key == 'd':
            game.start_attract_demo()

    elif game.state == GameState.MARIO_FACE:
        if key == 'enter':
            game.hide_mario_face()

    elif game.state == GameState.CASTLE or game.state == GameState.LEVEL:
        if key == 'tab':
            # Toggle free camera view
            if isinstance(camera, EditorCamera):
                camera.disable()
            else:
                EditorCamera()
        if key == 'escape':
            application.quit()

    elif game.state == GameState.ATTRACT:
        if key == 'enter':
            game.stop_attract_demo()


# ------------------------------
# Per-frame Update Hook
# ------------------------------
def global_update():
    # Autopilot ticker
    if hasattr(game, '_autopilot') and game.state == GameState.ATTRACT and game._autopilot:
        game._autopilot.update()

    game.update()

    # Debug overlay
    if held_keys['f3'] and game.mario:
        print(f'FPS: {1/max(time.dt, 1e-6):.0f}  Pos: {game.mario.position}  State: {game.state.name}  Stars: {game.save.stars}')


# ------------------------------
# App bootstrap
# ------------------------------
if __name__ == '__main__':
    app = Ursina(title="Ultra Mario 64 — SpaceWorld '95 Demo", borderless=False, fullscreen=False)

    window.exit_button.enabled = False if hasattr(window, 'exit_button') else False
    window.fps_counter.enabled = True

    # Lights & sky
    Sky()  # use default sky to avoid external textures
    DirectionalLight(parent=scene, y=10, rotation=(45, 45, 45))
    AmbientLight(color=color.rgba(100, 100, 100, 255))

    # Game manager
    game = GameManager()

    # Bind hooks
    input = global_input
    update = global_update

    app.run()
