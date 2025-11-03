# sm64_main_menu.py
# Super Mario 64-style main menu in a single Ursina file.
# Requires: pip install ursina
# Run:      python sm64_main_menu.py

from ursina import *
from math import sin, cos, pi
import random
import time as pytime


# ---------------------------
# Helpers
# ---------------------------
def is_descendant_of(node, ancestor):
    """Return True if 'node' is 'ancestor' or is inside its hierarchy."""
    e = node
    while e is not None:
        if e == ancestor:
            return True
        e = e.parent
    return False


# ---------------------------
# Interactive “head” (drag to rotate, blinks, pupils follow mouse, stretchable nose)
# ---------------------------
class InteractiveHead(Entity):
    def __init__(self, **kwargs):
        super().__init__(model='sphere',
                         color=color.rgb(244, 205, 170),
                         collider='sphere',
                         scale=1.45,
                         **kwargs)

        # Facial features (all primitives; no textures)
        self.eye_l = Entity(parent=self, model='sphere', color=color.white, scale=.25, position=Vec3(-.38, .22, .58), collider='sphere')
        self.eye_r = Entity(parent=self, model='sphere', color=color.white, scale=.25, position=Vec3(.38, .22, .58), collider='sphere')
        self.pupil_l = Entity(parent=self.eye_l, model='sphere', color=color.black, scale=.12, position=Vec3(0, 0, .11))
        self.pupil_r = Entity(parent=self.eye_r, model='sphere', color=color.black, scale=.12, position=Vec3(0, 0, .11))

        # Simple eyebrows and nose
        brow_color = color.rgb(110, 70, 35)
        self.brow_l = Entity(parent=self, model='cube', color=brow_color, scale=(.40, .05, .05), position=Vec3(-.38, .38, .48))
        self.brow_r = Entity(parent=self, model='cube', color=brow_color, scale=(.40, .05, .05), position=Vec3(.38, .38, .48))
        self.nose   = Entity(parent=self, model='sphere', color=color.rgb(255, 192, 187), scale=.3, position=Vec3(0, .05, .78), collider='sphere')

        # Simple mustache (two rotated cubes for authenticity)
        self.mustache_l = Entity(parent=self, model='cube', color=brow_color, scale=(.35, .12, .05), position=Vec3(-.25, -.12, .68), rotation=Vec3(0, 25, 10))
        self.mustache_r = Entity(parent=self, model='cube', color=brow_color, scale=(.35, .12, .05), position=Vec3(.25, -.12, .68), rotation=Vec3(0, -25, -10))

        # A simple cap (two stacked primitives)
        self.cap_brim = Entity(parent=self, model='cylinder', color=color.rgb(220, 40, 40),
                               scale=(1.25, .05, 1.25), position=Vec3(0, .58, 0), rotation=Vec3(90, 0, 0))
        self.cap_top  = Entity(parent=self, model='sphere', color=color.rgb(220, 40, 40),
                               scale=(1.15, .5, 1.15), position=Vec3(0, .78, -.05))

        # Interactivity / animation
        self.dragging = False
        self.current_dragged_part = None
        self.drag_start_pos = Vec3(0, 0, 0)
        self.drag_start_mouse = Vec2(0, 0)
        self._last_mouse_x = 0.0
        self._idle_rot_speed = 12.0
        self._blink_cooldown = random.uniform(1.8, 4.6)
        self._blink_open_scale = .25

    def input(self, key):
        # Begin dragging if clicking on the head (or any of its children)
        if key == 'left mouse down' and mouse.hovered_entity is not None:
            hovered = mouse.hovered_entity
            if is_descendant_of(hovered, self):
                if hovered == self.nose:  # Stretchable part
                    self.current_dragged_part = hovered
                    self.drag_start_pos = hovered.position
                    self.drag_start_mouse = mouse.position
                else:
                    self.dragging = True
                    self._last_mouse_x = mouse.x
        if key == 'left mouse up':
            self.dragging = False
            if self.current_dragged_part:
                # Snap back elastically
                self.current_dragged_part.animate_position(self.drag_start_pos, duration=0.3, curve=curve.out_elastic)
                self.current_dragged_part = None

    def _blink(self):
        # Quick squash + restore on eye spheres
        for eye in (self.eye_l, self.eye_r):
            eye.animate('scale_y', 0.02, duration=0.07, curve=curve.linear)
        # Re-open after a beat
        invoke(lambda: [setattr(eye, 'scale_y', self._blink_open_scale) for eye in (self.eye_l, self.eye_r)],
               delay=0.14)

    def update(self):
        # Rotate while dragging; slow idle spin otherwise
        if self.dragging:
            dx = mouse.x - self._last_mouse_x
            self.rotation_y += dx * 420  # degrees per normalized mouse unit
            self._last_mouse_x = mouse.x
        else:
            self.rotation_y += self._idle_rot_speed * time.dt

        # Pupils follow the pointer a bit (screen space → tiny local offsets)
        px = clamp(mouse.x * 0.12, -0.06, 0.06)
        py = clamp(mouse.y * 0.12, -0.06, 0.06)
        self.pupil_l.position = Vec3(px, py, self.pupil_l.position.z)
        self.pupil_r.position = Vec3(px, py, self.pupil_r.position.z)

        # Stretch dragged part
        if self.current_dragged_part:
            delta = mouse.position - self.drag_start_mouse
            # Simple stretch: move forward (z) based on drag distance, with some x/y
            stretch_amount = length(delta) * 3.0
            direction = normalize(Vec3(delta.x, delta.y, 1.0))  # Bias toward forward
            new_pos = self.drag_start_pos + direction * stretch_amount
            self.current_dragged_part.position = new_pos

        # Occasional blink
        self._blink_cooldown -= time.dt
        if self._blink_cooldown <= 0:
            self._blink()
            self._blink_cooldown = random.uniform(2.0, 5.0)


# ---------------------------
# Menu Controller / Scenes
# ---------------------------
class MainMenuController(Entity):
    def __init__(self, game_title="SUPER MARIO 64", **kwargs):
        super().__init__(**kwargs)

        # Lighting & sky
        self.sky = Sky()
        self.amb = AmbientLight(color=color.rgba(255, 255, 255, .25))
        self.dir = DirectionalLight(shadows=True)
        self.dir.look_at(Vec3(1, -1.5, -1))

        # Camera framing
        camera.position = Vec3(0, 0.55, -7.5)
        camera.look_at(Vec3(0, 0.4, 0))

        # Title (2D UI)
        self.title = Text(text=game_title,
                          parent=camera.ui,
                          y=.41,
                          x=0,
                          origin=(0, 0),
                          scale=2,
                          color=color.rgb(255, 240, 180),
                          background=False)

        # Subtle rotating ring behind the title (3D)
        self.title_ring = Entity(model='torus', color=color.rgba(255, 220, 80, 60),
                                 scale=2.6, y=1.45, z=1.0)

        # 3D “head” (no orbiting star for SM64 authenticity)
        self.head = InteractiveHead(y=.15, z=0)

        # “PRESS START” (blink)
        self.press_start = Text("PRESS START",
                                parent=camera.ui,
                                origin=(0, 0),
                                y=-.42,
                                z=0,
                                scale=1.35,
                                color=color.white)

        # Buttons (hidden until after Start, adjusted for SM64-like options)
        self.buttons_root = Entity(parent=camera.ui, enabled=False)
        self.btn_start  = Button(text='Start Game', parent=self.buttons_root, scale=(.25, .09), y=.05)
        self.btn_score  = Button(text='Score',      parent=self.buttons_root, scale=(.25, .09), y=-.05)
        self.btn_sound  = Button(text='Sound',      parent=self.buttons_root, scale=(.25, .09), y=-.15)
        self.btn_quit   = Button(text='Quit',       parent=self.buttons_root, scale=(.25, .09), y=-.25)

        self.btn_start.on_click = self._start_game
        self.btn_score.on_click = Func(print, 'Score placeholder')  # Placeholder
        self.btn_sound.on_click = self._toggle_sound
        self.btn_quit.on_click  = application.quit

        # Sound panel (SM64-like: stereo/mono/headset)
        self.sound_root = Entity(parent=camera.ui, enabled=False)
        self.sound_bg   = Entity(parent=self.sound_root, model='quad',
                                 color=color.rgba(0, 0, 0, .7), scale=(.9, .6), z=0)
        self.sound_title = Text("SOUND", parent=self.sound_root, y=.20, origin=(0, 0), scale=1.2)
        self.stereo_btn = Button(text='Stereo', parent=self.sound_root, y=.05, scale=(.22, .08))
        self.mono_btn   = Button(text='Mono',   parent=self.sound_root, y=-.05, scale=(.22, .08))
        self.headset_btn= Button(text='Headset',parent=self.sound_root, y=-.15, scale=(.22, .08))
        self.back_btn   = Button(text='Back',   parent=self.sound_root, y=-.25, scale=(.22, .08))
        self.back_btn.on_click = self._toggle_sound
        # Placeholder actions
        self.stereo_btn.on_click = Func(print, 'Set to Stereo')
        self.mono_btn.on_click   = Func(print, 'Set to Mono')
        self.headset_btn.on_click= Func(print, 'Set to Headset')

        # Fade overlay for transitions
        self.fader = Entity(parent=camera.ui, model='quad', color=color.rgba(0, 0, 0, 0), scale=2, z=-100)

        # Simple state machine
        self.state = 'ATTRACT'  # ATTRACT -> MAIN -> SOUND -> PLAY
        self._just_started = True

    # ------------- State changes -------------
    def goto_main(self):
        if self.state != 'ATTRACT':
            return
        self.state = 'MAIN'
        self.press_start.enabled = False
        self.buttons_root.enabled = True
        # Fun pop on the buttons
        for i, b in enumerate((self.btn_start, self.btn_score, self.btn_sound, self.btn_quit)):
            b.scale = (0.001, 0.001)
            b.animate_scale((.25, .09), duration=.12 + i*.05, curve=curve.out_back)

    def _toggle_sound(self):
        if self.state == 'MAIN':
            self.state = 'SOUND'
            self.buttons_root.enabled = False
            self.sound_root.enabled = True
        elif self.state == 'SOUND':
            self.state = 'MAIN'
            self.sound_root.enabled = False
            self.buttons_root.enabled = True

    def _start_game(self):
        # Placeholder: fade out, then show a “Loading...” splash
        self.state = 'PLAY'
        self.buttons_root.enabled = False
        self.sound_root.enabled = False
        self.press_start.enabled = False
        self.title.text = "LOADING..."
        self.title.color = color.azure
        self._fade_to(1.0, duration=.8, then=lambda: invoke(self._show_loading, delay=.2))

    def _show_loading(self):
        # Swap scene feel a bit (still just a placeholder)
        self.head.enabled = False
        self.title_ring.enabled = False
        # Replace sky color to suggest change of scene
        destroy(self.sky)
        self.sky = Sky()
        self.sky.color = color.rgb(20, 22, 35)
        self._fade_to(0.0, duration=.8)

    # ------------- Visual helpers -------------
    def _fade_to(self, target_alpha, duration=.6, then=None):
        self.fader.animate('color', color.rgba(0, 0, 0, target_alpha), duration=duration, curve=curve.linear)
        if then:
            invoke(then, delay=duration)

    # ------------- Global event hooks -------------
    def input(self, key):
        # Global input behaviors
        if key == 'f11':
            window.fullscreen = not window.fullscreen

        if self.state == 'ATTRACT':
            if key in ('enter', 'space', 'start', 'left mouse down'):
                self.goto_main()
        elif self.state == 'SOUND':
            if key == 'escape':
                self._toggle_sound()
        elif self.state == 'MAIN':
            if key == 'escape':
                application.quit()

    def update(self):
        # Title ring slow spin
        self.title_ring.rotation_y += 15 * time.dt

        # Blink "PRESS START"
        if self.state == 'ATTRACT':
            t = pytime.time()
            self.press_start.alpha = .42 + .42 * (0.5 + 0.5*sin(t*3.2))
        else:
            self.press_start.alpha = 0.0


# ---------------------------
# App bootstrap
# ---------------------------
app = Ursina()
window.title = 'Super Mario 64'
window.color = color.rgb(14, 22, 40)
window.fps_counter.enabled = False

controller = MainMenuController(game_title='SUPER MARIO 64')

# Tip text (small corner hint)
hint = Text("F11: fullscreen  |  ESC: quit/back",
            parent=camera.ui, origin=(.5, -.5), x=.48, y=-.48, scale=.65, color=color.rgba(255,255,255,.75))

app.run()
