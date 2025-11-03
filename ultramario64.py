# program.py
# Super Mario 64-style File Select FIRST, then title/attract (ULTRA MARIO 3D BROS).
# Requires: pip install ursina
# Run:      python program.py

from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from math import sin
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
# Interactive head (drag to rotate; blinks; pupils follow mouse; stretchable nose)
# ---------------------------
class InteractiveHead(Entity):
    def __init__(self, **kwargs):
        super().__init__(model='sphere',
                         color=color.rgb(244, 205, 170),
                         collider='sphere',
                         scale=1.45,
                         **kwargs)

        self.game_mode = False

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

        # Simple mustache (two rotated cubes)
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
        if self.game_mode:
            return

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
        if not self.game_mode:
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
                stretch_amount = delta.length() * 3.0
                direction = Vec3(delta.x, delta.y, 1.0).normalized()
                new_pos = self.drag_start_pos + direction * stretch_amount
                self.current_dragged_part.position = new_pos

        # Occasional blink (always active)
        self._blink_cooldown -= time.dt
        if self._blink_cooldown <= 0:
            self._blink()
            self._blink_cooldown = random.uniform(2.0, 5.0)


# ---------------------------
# File Select UI (session-only; no disk/files)
# ---------------------------
class FileSelectMenu(Entity):
    def __init__(self, on_select_slot, **kwargs):
        super().__init__(parent=camera.ui, **kwargs)
        self.on_select_slot = on_select_slot
        self.erase_mode = False
        self.slots = [{'exists': False, 'stars': 0} for _ in range(4)]
        # Backdrop
        self.bg = Entity(parent=self, model='quad', color=color.rgba(0, 0, 0, .65),
                         scale=(.98, .86), z=1)
        # Title
        self.title = Text("FILE SELECT", parent=self, y=.34, origin=(0, 0), scale=1.6)

        # Slot buttons (2x2 grid)
        self.buttons = []
        coords = [(-.32, .12), (.32, .12), (-.32, -.18), (.32, -.18)]
        names  = ['FILE A', 'FILE B', 'FILE C', 'FILE D']
        for i, ((x, y), nm) in enumerate(zip(coords, names)):
            btn = Button(parent=self, scale=(.37, .16), position=Vec2(x, y))
            btn.text_entity = Text(parent=btn, text="", origin=(0, 0), scale=.9, y=.01)
            btn.info = Text(parent=btn, text="", origin=(0, 0), scale=.7, y=-.045, color=color.rgba(255,255,255,.85))
            def _mk(i=i):
                self._click_slot(i)
            btn.on_click = _mk
            self.buttons.append(btn)

        # Bottom row controls
        self.erase_btn = Button(text='Erase: OFF', parent=self, y=-.38, x=-.22, scale=(.23, .08))
        self.erase_btn.on_click = self._toggle_erase
        self.quit_btn  = Button(text='Quit', parent=self, y=-.38, x=.22, scale=(.23, .08))
        self.quit_btn.on_click = application.quit

        self.note = Text("Session-only (no saves written)", parent=self, y=-.46, origin=(0,0),
                         scale=.6, color=color.rgba(255,255,255,.7))

        # Enter animation
        for i, b in enumerate(self.buttons):
            b.scale = (0.001, 0.001)
            b.animate_scale((.37, .16), duration=.12 + i*.05, curve=curve.out_back)
        self._refresh_labels()

    def _toggle_erase(self):
        self.erase_mode = not self.erase_mode
        self.erase_btn.text = f"Erase: {'ON' if self.erase_mode else 'OFF'}"

    def _refresh_labels(self):
        names  = ['FILE A', 'FILE B', 'FILE C', 'FILE D']
        for i, b in enumerate(self.buttons):
            slot = self.slots[i]
            if slot['exists']:
                b.text_entity.text = f"{names[i]}"
                b.info.text = f"{slot['stars']} ★"
            else:
                b.text_entity.text = f"{names[i]}"
                b.info.text = "Empty"

    def _click_slot(self, i):
        slot = self.slots[i]
        if self.erase_mode and slot['exists']:
            # Erase slot
            slot['exists'] = False
            slot['stars'] = 0
            self._refresh_labels()
            self.buttons[i].animate_scale(self.buttons[i].scale * 1.05, duration=.06, curve=curve.out_quart)
            self.buttons[i].animate_scale((.37, .16), duration=.08, delay=.06, curve=curve.in_out_quart)
            return

        # Ensure slot exists if picked empty
        if not slot['exists']:
            slot['exists'] = True
            slot['stars'] = 0
            self._refresh_labels()

        # Hand off to controller
        if self.on_select_slot:
            self.on_select_slot(i, slot)


# ---------------------------
# Menu Controller / Scenes
# ---------------------------
class MainMenuController(Entity):
    def __init__(self, game_title="ULTRA MARIO 3D BROS", **kwargs):
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
                          background=False,
                          enabled=False)

        # Subtle rotating ring behind the title (3D)
        self.title_ring = Entity(model='torus', color=color.rgba(255, 220, 80, 60),
                                 scale=2.6, y=1.45, z=1.0, enabled=False)

        # 3D "head"
        self.head = InteractiveHead(y=.15, z=0, enabled=False)

        # "PRESS START" (blink)
        self.press_start = Text("PRESS START",
                                parent=camera.ui,
                                origin=(0, 0),
                                y=-.42,
                                z=0,
                                scale=1.35,
                                color=color.white,
                                enabled=False)

        # Buttons (hidden until after Start)
        self.buttons_root = Entity(parent=camera.ui, enabled=False)
        self.btn_start  = Button(text='Start Game', parent=self.buttons_root, scale=(.25, .09), y=.05)
        self.btn_score  = Button(text='Score',      parent=self.buttons_root, scale=(.25, .09), y=-.05)
        self.btn_sound  = Button(text='Sound',      parent=self.buttons_root, scale=(.25, .09), y=-.15)
        self.btn_quit   = Button(text='Quit',       parent=self.buttons_root, scale=(.25, .09), y=-.25)

        self.btn_start.on_click = self._start_game
        self.btn_score.on_click = self._show_score
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
        self.stereo_btn.on_click = Func(print, 'Set to Stereo')
        self.mono_btn.on_click   = Func(print, 'Set to Mono')
        self.headset_btn.on_click= Func(print, 'Set to Headset')

        # Score panel (Mario 64-style Player Records)
        self.score_root = Entity(parent=camera.ui, enabled=False)
        self.score_bg   = Entity(parent=self.score_root, model='quad',
                                 color=color.rgba(0, 0, 0, .7), scale=(.9, .6), z=0)
        self.score_title = Text("PLAYER RECORDS", parent=self.score_root, y=.20, origin=(0, 0), scale=1.2)
        self.score_text = Text("FILES ARE OFF", parent=self.score_root, y=0, origin=(0, 0), scale=1.0, color=color.yellow)
        self.score_note = Text("Please select a file first", parent=self.score_root, y=-.10, origin=(0, 0), scale=.7, color=color.white)
        self.score_back_btn = Button(text='Back', parent=self.score_root, y=-.25, scale=(.22, .08))
        self.score_back_btn.on_click = self._hide_score

        # Fade overlay for transitions
        self.fader = Entity(parent=camera.ui, model='quad', color=color.rgba(0, 0, 0, 0), scale=2, z=-100)

        # File Select (first thing shown)
        self.file_menu = FileSelectMenu(on_select_slot=self._on_file_selected, enabled=True)

        # Small "current file" tag once past file select
        self.file_tag = Text("", parent=camera.ui, origin=(.5, -.5), x=.48, y=.42,
                             scale=.8, color=color.rgba(255,255,255,.85), enabled=False)

        # Simple state machine
        # Order: FILE_SELECT -> ATTRACT (title) -> MAIN -> SOUND -> SCORE -> PLAY
        self.state = 'FILE_SELECT'
        self.selected_slot_index = None

    # ------------- File select flow -------------
    def _on_file_selected(self, index, slot_data):
        self.selected_slot_index = index
        # Fade to title/attract
        self._fade_to(1.0, duration=.6, then=lambda: invoke(self._enter_attract_from_file, delay=.05))

    def _enter_attract_from_file(self):
        self.file_menu.enabled = False

        # Enable title scene bits
        self.title.enabled = True
        self.title_ring.enabled = True
        self.head.enabled = True
        self.press_start.enabled = True
        self.file_tag.enabled = True
        self.file_tag.text = f"Slot: {'ABCD'[self.selected_slot_index]}"

        self.state = 'ATTRACT'
        self._fade_to(0.0, duration=.6)

    def _goto_file_select(self):
        if self.state == 'FILE_SELECT':
            return
        # Hide title/main UI
        self.buttons_root.enabled = False
        self.sound_root.enabled = False
        self.score_root.enabled = False
        self.head.enabled = False
        self.title_ring.enabled = False
        self.press_start.enabled = False
        self.title.enabled = False
        self.file_tag.enabled = False
        self.state = 'FILE_SELECT'
        self._fade_to(1.0, duration=.4, then=lambda: invoke(self._show_file_menu, delay=.05))

    def _show_file_menu(self):
        self.file_menu.enabled = True
        self._fade_to(0.0, duration=.4)

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

    def _show_score(self):
        if self.state == 'MAIN':
            self.state = 'SCORE'
            self.buttons_root.enabled = False
            self.score_root.enabled = True

    def _hide_score(self):
        if self.state == 'SCORE':
            self.state = 'MAIN'
            self.score_root.enabled = False
            self.buttons_root.enabled = True

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
        self.state = 'PLAY'
        self.buttons_root.enabled = False
        self.sound_root.enabled = False
        self.score_root.enabled = False
        self.press_start.enabled = False
        self.title.enabled = False
        self.title_ring.enabled = False
        self.file_tag.enabled = False
        self.head.enabled = False
        self._fade_to(1.0, duration=.8, then=lambda: invoke(self._enter_game, delay=.2))

    def _enter_game(self):
        destroy(self.sky)
        self.sky = Sky()

        self.ground = Entity(model='plane', scale=64, texture='grass', collider='box')

        self.player = FirstPersonController(model=None, collider='sphere', position=(0, 5, 0), speed=8, jump_height=2)

        self.head.parent = self.player
        self.head.position = Vec3(0, 0, 0)
        self.head.rotation = Vec3(0, 0, 0)
        self.head.enabled = True
        self.head.game_mode = True
        self.head._idle_rot_speed = 0

        self.player.camera_pivot.y = 1
        self.player.camera_pivot.z = -4

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
        if key == 'f2' and self.state != 'FILE_SELECT':
            self._goto_file_select()

        if self.state == 'FILE_SELECT':
            if key == 'escape':
                application.quit()

        elif self.state == 'ATTRACT':
            if key in ('enter', 'space', 'start', 'left mouse down'):
                self.goto_main()

        elif self.state == 'SOUND':
            if key == 'escape':
                self._toggle_sound()

        elif self.state == 'SCORE':
            if key == 'escape':
                self._hide_score()

        elif self.state == 'MAIN':
            if key == 'escape':
                application.quit()

    def update(self):
        # Title ring slow spin
        if self.title_ring.enabled:
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
window.title = 'Ultra Mario 3D Bros'
window.color = color.rgb(14, 22, 40)
window.fps_counter.enabled = False

controller = MainMenuController(game_title='ULTRA MARIO 3D BROS')

# Tip text (small corner hint)
hint = Text("F11: fullscreen  |  ESC: quit/back  |  F2: file select",
            parent=camera.ui, origin=(.5, -.5), x=.48, y=-.48,
            scale=.65, color=color.rgba(255,255,255,.75))

app.run()
