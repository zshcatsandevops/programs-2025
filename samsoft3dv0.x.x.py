#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Space 3D Pinball (Ursina, single-file prototype)
Window: 600x400
No external assets required.
Controls:
  - Left Arrow / A  : Left flipper
  - Right Arrow / D : Right flipper
  - R               : Reset ball (if lost) / Restart
  - ESC             : Quit
"""
from ursina import *
import math
import random


# -------------------------------
# Helpers
# -------------------------------
def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def vec2_len(x, z):
    return math.sqrt(x*x + z*z)


def reflect(v: Vec3, n: Vec3) -> Vec3:
    """Reflect vector v against unit normal n (3D, but we only use x,z)."""
    d = v.x * n.x + v.y * n.y + v.z * n.z
    return Vec3(v.x - 2*d*n.x, v.y - 2*d*n.y, v.z - 2*d*n.z)


# -------------------------------
# App / Window
# -------------------------------
app = Ursina()
window.title = 'Space 3D Pinball'
window.borderless = False
window.fullscreen = False
window.size = (600, 400)
window.color = color.black


# -------------------------------
# Playfield parameters
# -------------------------------
WIDTH = 12.0     # x span of table (left/right)
DEPTH = 18.0     # z span of table (top/bottom)
WALL_THICK = 0.5
DRAIN_GAP = 3.0

# "Gravity" along -Z (toward the camera) to emulate a sloped pinball table.
SLOPE_ACC = -6.0

# Ball tuning
FRICTION = 0.04        # energy loss per second
BOUNCE = 0.9           # wall restitution
BUMPER_BOOST = 5.0
MAX_SPEED = 18.0
MIN_SPEED = 1.3

# Flipper tuning
FLIPPER_SWING_SPEED = 480.0  # deg/sec
LEFT_REST = -26.0
LEFT_HIT = 32.0
RIGHT_REST = 26.0
RIGHT_HIT = -32.0
FLIP_IMPULSE = 11.0   # impulse added to the ball on 'strike'

# UI / scoring
score = 0
balls_left = 3


# -------------------------------
# Scene & Lighting
# -------------------------------
# Table plane (x-z)
table = Entity(model='plane',
               scale=(WIDTH, DEPTH),
               color=color.rgba(20, 20, 35, 255),
               texture='white_cube',
               texture_scale=(int(WIDTH), int(DEPTH)),
               y=0)

# Subtle rim glow rails
glow_rim = Entity(model=Mesh(vertices=[
                    Vec3(-WIDTH/2, 0.02,  DEPTH/2),
                    Vec3( WIDTH/2, 0.02,  DEPTH/2),
                    Vec3( WIDTH/2, 0.02, -DEPTH/2),
                    Vec3(-WIDTH/2, 0.02, -DEPTH/2),
                ],
                triangles=[(0,1,2), (0,2,3)]),
                color=color.rgba(60, 70, 160, 40))

# Walls
walls = []
left_wall = Entity(model='cube', color=color.rgba(160, 160, 200, 255),
                   scale=(WALL_THICK, 1, DEPTH), x=-WIDTH/2, y=0.5, collider='box')
right_wall = Entity(model='cube', color=color.rgba(160, 160, 200, 255),
                    scale=(WALL_THICK, 1, DEPTH), x=WIDTH/2, y=0.5, collider='box')
top_wall = Entity(model='cube', color=color.rgba(160, 160, 200, 255),
                  scale=(WIDTH, 1, WALL_THICK), z=DEPTH/2, y=0.5, collider='box')

# Bottom split walls (leave a drain gap in the middle)
bottom_segment_width = (WIDTH - DRAIN_GAP) / 2.0
bottom_left = Entity(model='cube', color=color.rgba(160, 160, 200, 255),
                     scale=(bottom_segment_width, 1, WALL_THICK),
                     x = -WIDTH/2 + bottom_segment_width/2,
                     z = -DEPTH/2,
                     y=0.5, collider='box')
bottom_right = Entity(model='cube', color=color.rgba(160, 160, 200, 255),
                      scale=(bottom_segment_width, 1, WALL_THICK),
                      x = WIDTH/2 - bottom_segment_width/2,
                      z = -DEPTH/2,
                      y=0.5, collider='box')
walls.extend([left_wall, right_wall, top_wall, bottom_left, bottom_right])

# Spacey starfield (simple billboard quads; no textures required)
star_group = Entity()
for _ in range(120):
    sx = random.uniform(-WIDTH*1.2, WIDTH*1.2)
    sz = random.uniform(-DEPTH*1.2, DEPTH*1.2)
    sy = random.uniform(3.0, 8.0)
    s = random.uniform(0.04, 0.1)
    Entity(parent=star_group, model='quad', scale=s, position=(sx, sy, sz),
           color=color.rgba(250, 250, 255, random.randint(140, 220)),
           billboard=True, unlit=True)

# A faint ambient + rim light
ambient = Entity(light=AmbientLight(color=color.rgba(80, 80, 120, 255)))
rimlight = Entity(light=DirectionalLight(shadows=False),
                  rotation=(60, 30, 0),
                  color=color.rgba(200, 200, 220, 255))


# -------------------------------
# Ball
# -------------------------------
class Ball(Entity):
    def __init__(self):
        super().__init__(model='sphere', scale=0.6, color=color.white,
                         y=0.3, collider='sphere')
        self.radius = 0.3
        self.velocity = Vec3(0, 0, 0)
        self.in_play = True

    def reset(self):
        self.position = Vec3(0, 0.3, DEPTH/2 - 2.0)
        # slight random x, gentle initial roll
        self.velocity = Vec3(random.uniform(-0.5, 0.5), 0, -2.0)
        self.in_play = True

    def speed_clamp(self):
        vx, vz = self.velocity.x, self.velocity.z
        s = vec2_len(vx, vz)
        if s > MAX_SPEED:
            k = MAX_SPEED / (s + 1e-6)
            self.velocity.x *= k
            self.velocity.z *= k
        elif s < MIN_SPEED:
            # Nudge so it doesn't stall forever
            if s < 1e-3:
                self.velocity.z -= 0.4
            else:
                k = (MIN_SPEED + 0.01) / (s + 1e-6)
                self.velocity.x *= k * 0.5
                self.velocity.z *= k * 0.5

    def update_motion(self, dt: float):
        # Slope "gravity"
        self.velocity.z += SLOPE_ACC * dt
        # Friction
        self.velocity.x *= max(0.0, 1.0 - FRICTION * dt)
        self.velocity.z *= max(0.0, 1.0 - FRICTION * dt)
        self.speed_clamp()
        # Integrate (confine to x-z plane)
        self.position += Vec3(self.velocity.x * dt, 0, self.velocity.z * dt)


ball = Ball()
ball.reset()


# -------------------------------
# Bumpers
# -------------------------------
class Bumper(Entity):
    def __init__(self, pos: Vec3, radius=0.6, boost=BUMPER_BOOST):
        super().__init__(model='sphere', color=color.azure, scale=radius*2.0,
                         position=pos, collider='sphere')
        self.radius = radius
        self.boost = boost
        # a base ring for looks
        Entity(parent=self, model='cylinder', scale=(radius*2.2, 0.1, radius*2.2),
               y=-self.scale_y/2, color=color.rgba(120, 140, 240, 200))

    def collide_ball(self, ball: Ball):
        dx = ball.x - self.x
        dz = ball.z - self.z
        rsum = ball.radius + self.radius
        dist = vec2_len(dx, dz)
        if dist <= rsum:
            # Push ball out
            nx, nz = (dx / (dist + 1e-6)), (dz / (dist + 1e-6))
            # Snap outside bumper to avoid sticking
            ball.x = self.x + nx * (rsum + 0.005)
            ball.z = self.z + nz * (rsum + 0.005)
            # Reflect and boost
            n = Vec3(nx, 0, nz)
            ball.velocity = reflect(ball.velocity, n)
            ball.velocity += n * self.boost
            return True
        return False


bumpers = [
    Bumper(Vec3(0, 0.3, 6.0), radius=0.7, boost=6.5),
    Bumper(Vec3(-3.0, 0.3, 3.5), radius=0.6),
    Bumper(Vec3(3.0, 0.3, 3.5), radius=0.6),
    Bumper(Vec3(0.0, 0.3, 1.0), radius=0.55),
]


# -------------------------------
# Flippers (visual + strike zones)
# -------------------------------
class Flipper(Entity):
    def __init__(self, side='left'):
        if side not in ('left', 'right'):
            raise ValueError('Flipper side must be "left" or "right".')
        self.side = side
        pivot_pos = Vec3(-2.4, 0.25, -6.5) if side == 'left' else Vec3(2.4, 0.25, -6.5)
        # Parent pivot so rotation occurs about inner end
        pivot = Entity(position=pivot_pos)
        origin_x = -0.5 if side == 'left' else 0.5
        super().__init__(parent=pivot, model='cube', collider='box',
                         scale=(3.0, 0.3, 0.8), origin=(origin_x, 0, 0),
                         color=color.rgba(240, 120, 120, 255) if side == 'left' else color.rgba(120, 240, 120, 255))
        # Angles
        self.rest = LEFT_REST if side == 'left' else RIGHT_REST
        self.hit = LEFT_HIT if side == 'left' else RIGHT_HIT
        self.rotation_y = self.rest
        self.target = self.rest

        # A simple invisible strike zone (approximate)
        zone_x = -1.5 if side == 'left' else 1.5
        self.strike_zone = Entity(model='sphere', scale=(1.8, 0.2, 1.8),
                                  position=(zone_x, 0.25, -6.2),
                                  color=color.clear, collider=None)

    def set_pressed(self, pressed: bool):
        self.target = self.hit if pressed else self.rest

    def strike(self):
        # If ball is inside the zone when we trigger, kick it.
        dx = ball.x - self.strike_zone.x
        dz = ball.z - self.strike_zone.z
        if vec2_len(dx, dz) < 1.1:
            # Aim mostly up the table and a bit to the side
            side_push = 1.0 if self.side == 'left' else -1.0
            impulse = Vec3(FLIP_IMPULSE * 0.35 * side_push, 0, FLIP_IMPULSE)
            ball.velocity += impulse


left_flipper = Flipper('left')
right_flipper = Flipper('right')


# Decorative drains / lanes
Entity(model='cube', scale=(DRAIN_GAP, 0.05, 0.3),
       position=(0, 0.26, -DEPTH/2 + 0.2),
       color=color.rgba(80, 80, 90, 255))


# -------------------------------
# UI
# -------------------------------
score_text = Text(text='SCORE: 0', origin=(-.5, .5), position=(-0.88, 0.46), scale=1.1, color=color.azure)
balls_text = Text(text='BALLS: 3', origin=(-.5, .5), position=(-0.88, 0.40), scale=1.0, color=color.lime)
hint_text = Text(text='A/Left = Left Flipper  |  D/Right = Right Flipper  |  R = Reset  |  ESC = Quit',
                 origin=(0, 0), position=(0, -0.47), scale=.8, color=color.rgba(200, 200, 200, 200))


def add_score(points):
    global score
    score += points
    score_text.text = f'SCORE: {score}'


def set_balls(n):
    global balls_left
    balls_left = n
    balls_text.text = f'BALLS: {balls_left}'


# -------------------------------
# Camera
# -------------------------------
camera.position = Vec3(0, 18, -18)
camera.rotation_x = 45
camera.fov = 60


# -------------------------------
# Game state & logic
# -------------------------------
pressed_left = False
pressed_right = False


def input(key):
    global pressed_left, pressed_right, score, balls_left
    # Left flipper
    if key in ('a', 'left arrow'):
        pressed_left = True
        left_flipper.set_pressed(True)
        left_flipper.strike()
        add_score(1)  # tiny "hit" point for timing
    if key in ('a up', 'left arrow up'):
        pressed_left = False
        left_flipper.set_pressed(False)

    # Right flipper
    if key in ('d', 'right arrow'):
        pressed_right = True
        right_flipper.set_pressed(True)
        right_flipper.strike()
        add_score(1)
    if key in ('d up', 'right arrow up'):
        pressed_right = False
        right_flipper.set_pressed(False)

    # Reset
    if key == 'r':
        if balls_left <= 0:
            set_balls(3)
            score = 0
            score_text.text = 'SCORE: 0'
        ball.reset()


def update():
    dt = time.dt

    # Animate flippers toward their targets
    for fl, target in ((left_flipper, left_flipper.target),
                       (right_flipper, right_flipper.target)):
        cur = fl.rotation_y
        if abs(cur - target) > 0.1:
            dir_sign = 1.0 if target > cur else -1.0
            step = FLIPPER_SWING_SPEED * dt * dir_sign
            # clamp
            if (dir_sign > 0 and cur + step > target) or (dir_sign < 0 and cur + step < target):
                fl.rotation_y = target
            else:
                fl.rotation_y = cur + step

    # Ball physics / movement
    if ball.in_play:
        ball.update_motion(dt)

        # ----- Wall collisions (AABB of playfield) -----
        min_x = -WIDTH/2 + WALL_THICK/2 + ball.radius
        max_x = WIDTH/2 - WALL_THICK/2 - ball.radius
        if ball.x < min_x:
            ball.x = min_x
            ball.velocity.x = abs(ball.velocity.x) * BOUNCE
        elif ball.x > max_x:
            ball.x = max_x
            ball.velocity.x = -abs(ball.velocity.x) * BOUNCE

        # Top
        z_top = DEPTH/2 - WALL_THICK/2 - ball.radius
        if ball.z > z_top:
            ball.z = z_top
            ball.velocity.z = -abs(ball.velocity.z) * BOUNCE

        # Bottom with drain gap
        z_bottom = -DEPTH/2 + WALL_THICK/2 + ball.radius
        if ball.z < z_bottom:
            # If not inside drain gap, bounce; otherwise drain (ball lost)
            if abs(ball.x) >= (DRAIN_GAP/2 + 0.05):
                ball.z = z_bottom
                ball.velocity.z = abs(ball.velocity.z) * BOUNCE
            else:
                # Drain
                ball.in_play = False

        # ----- Bumper collisions -----
        for b in bumpers:
            if b.collide_ball(ball):
                add_score(100)

    else:
        # Ball drained: lose a ball and show prompt
        global balls_left
        if balls_left > 0:
            set_balls(balls_left - 1)
        if balls_left <= 0:
            hint_text.text = 'GAME OVER – Press R to restart'
            hint_text.color = color.rgba(255, 120, 120, 230)
        else:
            hint_text.text = 'Ball Lost – Press R to launch again'
            hint_text.color = color.rgba(200, 200, 200, 200)


if __name__ == '__main__':
    app.run()
