# program.py
# Ultra Mario 3D Bros — SM64-style File-Select → Title → Tech Demo (single file)
# © Samsoft 2025
# Requires: pip install ursina

from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from math import sin, cos, radians
import random
import time

# ─────────────────────────────────────────────
# Utility Functions
# ─────────────────────────────────────────────
def is_descendant_of(node, ancestor):
    """Check if node is a descendant of ancestor in the entity hierarchy."""
    while node:
        if node == ancestor:
            return True
        node = getattr(node, 'parent', None)
    return False

def clamp(value, min_val, max_val):
    """Clamp value between min and max."""
    return max(min_val, min(value, max_val))

# ─────────────────────────────────────────────
# SGI-style Interactive Head
# ─────────────────────────────────────────────
class InteractiveHead(Entity):
    def __init__(self, **kwargs):
        super().__init__(
            model='cube',
            color=color.rgb(244, 205, 170),
            collider='box',
            scale=(1.6, 1.8, 1.4),
            **kwargs
        )
        self.game_mode = False
        self.dragging = False
        self.current_dragged_part = None
        self._last_mouse_x = 0
        self._idle_rot_speed = 12
        self._blink_timer = random.uniform(2, 5)
        self.blinking = False

        # Create facial features
        self._create_face_parts()
        
    def _create_face_parts(self):
        """Create all facial components."""
        # Eyes
        self.eye_l = Entity(parent=self, model='cube', color=color.white, scale=(.3, .2, .1),
                           position=Vec3(-.35, .25, .65))
        self.eye_r = Entity(parent=self, model='cube', color=color.white, scale=(.3, .2, .1),
                           position=Vec3(.35, .25, .65))
        
        # Pupils
        self.pupil_l = Entity(parent=self.eye_l, model='cube', color=color.black,
                             scale=(.5, .5, 1.2), position=Vec3(0, 0, .06))
        self.pupil_r = Entity(parent=self.eye_r, model='cube', color=color.black,
                             scale=(.5, .5, 1.2), position=Vec3(0, 0, .06))
        
        # Eyebrows
        brow_color = color.rgb(80, 50, 20)
        self.brow_l = Entity(parent=self, model='cube', color=brow_color,
                           scale=(.45, .08, .08), position=Vec3(-.35, .4, .55), rotation_z=5)
        self.brow_r = Entity(parent=self, model='cube', color=brow_color,
                           scale=(.45, .08, .08), position=Vec3(.35, .4, .55), rotation_z=-5)
        
        # Nose
        self.nose = Entity(parent=self, model='cube', color=color.rgb(255, 180, 160),
                          scale=(.25, .3, .4), position=Vec3(0, .1, .8), rotation_x=10, collider='box')
        
        # Mustache
        self.mustache_l = Entity(parent=self, model='cube', color=brow_color,
                               scale=(.4, .15, .08), position=Vec3(-.25, -.1, .7), rotation=Vec3(0, 15, -5))
        self.mustache_r = Entity(parent=self, model='cube', color=brow_color,
                               scale=(.4, .15, .08), position=Vec3(.25, -.1, .7), rotation=Vec3(0, -15, 5))
        
        # Cap
        self.cap_brim = Entity(parent=self, model='cylinder', color=color.rgb(200, 30, 30),
                             scale=(1.4, .08, 1.4), position=Vec3(0, .65, 0), rotation_x=90)
        self.cap_top = Entity(parent=self, model='cube', color=color.rgb(200, 30, 30),
                            scale=(1.3, .5, 1.3), position=Vec3(0, .9, -.1))
        
        # Cap emblem (M)
        self.cap_emblem = Entity(parent=self.cap_top, model='circle', color=color.white,
                               scale=.3, position=Vec3(0, .3, .7), rotation_x=90)
        mcol = color.rgb(200, 30, 30)
        self.m_left = Entity(parent=self.cap_emblem, model='cube', color=mcol,
                           scale=(.08, .2, .02), position=Vec3(-.08, 0, -.01))
        self.m_middle1 = Entity(parent=self.cap_emblem, model='cube', color=mcol,
                              scale=(.08, .12, .02), position=Vec3(0, -.04, -.01), rotation_z=45)
        self.m_middle2 = Entity(parent=self.cap_emblem, model='cube', color=mcol,
                              scale=(.08, .12, .02), position=Vec3(0, .04, -.01), rotation_z=-45)
        self.m_right = Entity(parent=self.cap_emblem, model='cube', color=mcol,
                            scale=(.08, .2, .02), position=Vec3(.08, 0, -.01))

    def input(self, key):
        """Handle input events for the head."""
        if self.game_mode:
            return
            
        if key == 'left mouse down' and mouse.hovered_entity:
            hovered = mouse.hovered_entity
            if is_descendant_of(hovered, self):
                if hovered == self.nose:
                    self.current_dragged_part = hovered
                    self._drag_origin = hovered.world_position
                    self._mouse_origin = mouse.position
                else:
                    self.dragging = True
                    self._last_mouse_x = mouse.x
                    
        if key == 'left mouse up':
            self.dragging = False
            if self.current_dragged_part:
                self.current_dragged_part.animate_position(
                    self._drag_origin,
                    duration=.3,
                    curve=curve.out_elastic
                )
                self.current_dragged_part = None

    def _blink(self):
        """Perform blinking animation."""
        if self.blinking:
            return
            
        self.blinking = True
        for eye in (self.eye_l, self.eye_r):
            eye.animate_scale_y(0.02, duration=0.07)
        
        invoke(self._open_eyes, delay=0.14)
        
    def _open_eyes(self):
        """Open eyes after blinking."""
        for eye in (self.eye_l, self.eye_r):
            eye.scale_y = .2
        self.blinking = False

    def update(self):
        """Update head animations and interactions."""
        if not self.game_mode:
            if self.dragging and hasattr(self, '_last_mouse_x'):
                dx = mouse.x - self._last_mouse_x
                self.rotation_y += dx * 420 * time.dt
                self._last_mouse_x = mouse.x
            else:
                self.rotation_y += self._idle_rot_speed * time.dt
                
            # Eye tracking
            px = clamp(mouse.x * 0.08, -.12, .12)
            py = clamp(mouse.y * 0.08, -.08, .08)
            for pupil in (self.pupil_l, self.pupil_r):
                pupil.x, pupil.y = px, py
                
            # Nose dragging
            if self.current_dragged_part and hasattr(self, '_mouse_origin'):
                d = mouse.position - self._mouse_origin
                self.current_dragged_part.position = self._drag_origin + Vec3(d.x, d.y, abs(d.x + d.y)) * 3
        
        # Blinking logic
        self._blink_timer -= time.dt
        if self._blink_timer <= 0 and not self.blinking:
            self._blink()
            self._blink_timer = random.uniform(2, 5)

# ─────────────────────────────────────────────
# File-Select Menu (session only)
# ─────────────────────────────────────────────
class FileSelectMenu(Entity):
    def __init__(self, on_select, **kwargs):
        super().__init__(parent=camera.ui, **kwargs)
        self.on_select = on_select
        self.erase = False
        self.slots = [{'exists': False, 'stars': 0} for _ in range(4)]
        
        self._create_ui_elements()
        self._refresh()
        
    def _create_ui_elements(self):
        """Create all UI elements for the file select menu."""
        # Background
        self.bg = Entity(parent=self, model='quad', color=color.rgba(0, 0, 0, .6), scale=(.98, .86), z=1)
        
        # Title
        Text("FILE SELECT", parent=self, y=.34, scale=1.6, color=color.gold)
        
        # File slots
        self.buttons = []
        coords = [(-.32, .12), (.32, .12), (-.32, -.18), (.32, -.18)]
        names = ['FILE A', 'FILE B', 'FILE C', 'FILE D']
        
        for i, (pos, name) in enumerate(zip(coords, names)):
            btn = Button(
                parent=self,
                scale=(.37, .16),
                position=Vec3(pos[0], pos[1], 0),
                color=color.rgba(50, 50, 50, 200),
                highlight_color=color.rgba(80, 80, 200, 220)
            )
            btn.text_entity = Text(parent=btn, text=name, scale=.9, y=.01, origin=(0, 0))
            btn.info = Text(parent=btn, text="Empty", scale=.7, y=-.045, color=color.rgba(255, 255, 255, .8))
            btn.slot_index = i
            btn.on_click = self._create_click_handler(i)
            self.buttons.append(btn)
        
        # Control buttons
        self.erase_btn = Button(text='Erase: OFF', parent=self, y=-.38, x=-.22, scale=(.23, .08),
                              color=color.rgba(150, 50, 50, 200))
        self.quit_btn = Button(text='Quit', parent=self, y=-.38, x=.22, scale=(.23, .08),
                             color=color.rgba(150, 50, 50, 200))
        
        self.erase_btn.on_click = self._toggle_erase
        self.quit_btn.on_click = application.quit
        
        # Footer text
        Text("Session-only (no saves)", parent=self, y=-.46, scale=.6, color=color.rgba(255, 255, 255, .7))
        
        # Animate buttons in
        for i, btn in enumerate(self.buttons):
            btn.scale = (.001, .001)
            btn.animate_scale((.37, .16), duration=.12 + i * .05, curve=curve.out_back)
    
    def _create_click_handler(self, index):
        """Create a click handler for a specific file slot."""
        def handler():
            self._click(index)
        return handler
    
    def _toggle_erase(self):
        """Toggle erase mode."""
        self.erase = not self.erase
        self.erase_btn.text = f"Erase: {'ON' if self.erase else 'OFF'}"
        self.erase_btn.color = color.rgba(200, 50, 50, 220) if self.erase else color.rgba(150, 50, 50, 200)
        
    def _refresh(self):
        """Refresh the display of file slots."""
        for i, btn in enumerate(self.buttons):
            slot = self.slots[i]
            btn.text_entity.text = f"FILE {'ABCD'[i]}"
            btn.info.text = "Empty" if not slot['exists'] else f"{slot['stars']} ★"
            btn.color = color.rgba(50, 100, 50, 200) if slot['exists'] else color.rgba(50, 50, 50, 200)
            
    def _click(self, i):
        """Handle file slot click."""
        slot = self.slots[i]
        if self.erase and slot['exists']:
            slot.update({'exists': False, 'stars': 0})
            self._refresh()
            return
            
        if not slot['exists']:
            slot['exists'] = True
            slot['stars'] = 0
            
        if self.on_select:
            self.on_select(i, slot.copy())

# ─────────────────────────────────────────────
# Simple Tech Demo Level
# ─────────────────────────────────────────────
class TechDemo(Entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._create_environment()
        self._create_platforms()
        self._create_interactive_objects()
        
        self.collected = 0
        self.create_ui()
        
    def _create_environment(self):
        """Create the basic environment."""
        self.ground = Entity(
            model='plane',
            scale=(50, 1, 50),
            texture='white_cube',
            texture_scale=(5, 5),
            color=color.rgb(100, 150, 200),
            collider='mesh'
        )
        
        # Add some ambient objects
        for i in range(10):
            x = random.uniform(-20, 20)
            z = random.uniform(-20, 20)
            size = random.uniform(1, 3)
            Entity(
                model='cube',
                position=(x, size/2, z),
                scale=(size, size, size),
                color=color.random_color(),
                collider='box'
            )
        
    def _create_platforms(self):
        """Create platforms and moving elements."""
        self.platforms = []
        platform_data = [
            ((0, 2, 0), (8, .5, 8), color.green),
            ((10, 4, 5), (4, .5, 4), color.yellow),
            ((-8, 6, -5), (3, .5, 3), color.orange)
        ]
        
        for pos, scale, col in platform_data:
            platform = Entity(
                model='cube',
                position=pos,
                scale=scale,
                color=col,
                collider='box'
            )
            self.platforms.append(platform)
        
        # Moving platform
        self.mover = Entity(
            model='cube',
            scale=(3, .5, 3),
            color=color.cyan,
            position=(-5, 3, 10),
            collider='box'
        )
        self.mover_target_positions = [Vec3(-5, 3, 10), Vec3(-5, 3, 15)]
        self.mover_current_target = 0
        
        # Spinning platform
        self.spin = Entity(
            model='cube',
            scale=(2, 2, 2),
            color=color.magenta,
            position=(15, 1, 0),
            collider='box'
        )
    
    def _create_interactive_objects(self):
        """Create collectible stars and other interactive objects."""
        self.stars = []
        star_positions = [(0, 3, 0), (10, 5, 5), (-8, 7, -5)]
        
        for pos in star_positions:
            star = Entity(
                model='sphere',
                scale=.5,
                color=color.yellow,
                position=pos,
                collider='sphere',
                name='star'
            )
            self.stars.append(star)
    
    def create_ui(self):
        """Create the user interface elements."""
        self.stars_text = Text(
            f"Stars: {self.collected}/3",
            position=(-.8, .4),
            parent=camera.ui,
            scale=1.5,
            color=color.yellow
        )
        
        # Instructions
        Text(
            "Collect all stars!\nWASD: Move | Space: Jump\nF5: Toggle Fly Mode | F8: Toggle God Mode",
            parent=camera.ui,
            position=(0, -.45),
            scale=.7,
            color=color.white,
            origin=(0, 0),
            background=True,
            enabled=True
        )
    
    def update(self):
        """Update game logic."""
        if not hasattr(self, 'player') or not self.player:
            return
            
        # Move platform
        target = self.mover_target_positions[self.mover_current_target]
        self.mover.position = lerp(self.mover.position, target, time.dt * 2)
        
        if distance(self.mover.position, target) < .3:
            self.mover_current_target = 1 - self.mover_current_target
        
        # Spin the rotating platform
        self.spin.rotation_y += 50 * time.dt
        self.spin.rotation_x += 30 * time.dt
        
        # Check for star collection
        for star in self.stars[:]:
            if star.enabled and distance(star.position, self.player.position) < 1.3:
                star.disable()
                self.collected += 1
                self.stars_text.text = f"Stars: {self.collected}/3"
                
                # Win condition
                if self.collected >= 3:
                    Text(
                        "LEVEL COMPLETE!",
                        parent=camera.ui,
                        origin=(0, 0),
                        scale=3,
                        color=color.green,
                        background=True
                    )

# ─────────────────────────────────────────────
# Enhanced First-Person Controller
# ─────────────────────────────────────────────
class DebugFPC(FirstPersonController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._fly = False
        self._god = False
        self.fly_speed = 15
        self.sprint_speed = 16
        self.normal_speed = 8
        self.god_speed = 20
        self.normal_jump = 2
        self.god_jump = 10
        
        # Visual indicator
        self.mode_text = Text(
            "",
            parent=camera.ui,
            position=(-.85, .45),
            scale=1.2,
            color=color.white
        )
        
    def input(self, key):
        """Handle input events."""
        super().input(key)
        
        if key == 'f5':
            self._fly = not self._fly
            self.gravity = 0 if self._fly else 1
            self.mode_text.text = "FLY MODE" if self._fly else ""
            self.mode_text.color = color.blue if self._fly else color.white
            
        if key == 'f8':
            self._god = not self._god
            self.speed = self.god_speed if self._god else self.normal_speed
            self.jump_height = self.god_jump if self._god else self.normal_jump
            self.mode_text.text = "GOD MODE" if self._god else ("FLY MODE" if self._fly else "")
            self.mode_text.color = color.red if self._god else (color.blue if self._fly else color.white)
    
    def update(self):
        """Update player movement."""
        super().update()
        
        # Fly mode controls
        if self._fly:
            direction = Vec3(
                (self.forward.x * (held_keys['w'] - held_keys['s']) +
                 self.right.x * (held_keys['d'] - held_keys['a'])),
                0,
                (self.forward.z * (held_keys['w'] - held_keys['s']) +
                 self.right.z * (held_keys['d'] - held_keys['a']))
            ).normalized()
            
            if direction.magnitude() > 0.1:
                self.position += direction * self.fly_speed * time.dt
            
            # Vertical movement
            if held_keys['e']:
                self.y += self.fly_speed * time.dt
            if held_keys['q']:
                self.y -= self.fly_speed * time.dt
        
        # Speed adjustments
        if held_keys['shift'] and not self._fly:
            self.speed = self.sprint_speed
        else:
            self.speed = self.god_speed if self._god else self.normal_speed

# ─────────────────────────────────────────────
# Main Game Controller
# ─────────────────────────────────────────────
class Main(Entity):
    def __init__(self):
        super().__init__()
        self._setup_scene()
        self._create_title_screen()
        self._setup_game_states()
        
    def _setup_scene(self):
        """Setup the basic scene elements."""
        self.sky = Sky()
        DirectionalLight(
            parent=self,
            y=2,
            z=3,
            shadows=True,
            rotation=(45, -45, 45),
            color=color.white
        )
        
        # Camera setup
        camera.position = (0, .55, -7.5)
        camera.look_at(Vec3(0, .4, 0))
        
        # Fader for transitions
        self.fader = Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgba(0, 0, 0, 0),
            scale=2,
            z=-10
        )
        
    def _create_title_screen(self):
        """Create title screen elements."""
        # Title text
        self.title = Text(
            "ULTRA MARIO 3D BROS",
            parent=camera.ui,
            y=.41,
            scale=2,
            color=color.rgb(255, 240, 180),
            enabled=False
        )
        
        # Decorative ring
        self.ring = Entity(
            model='torus',
            color=color.rgba(255, 220, 80, 60),
            scale=2.6,
            y=1.45,
            z=1,
            enabled=False
        )
        
        # Interactive head
        self.head = InteractiveHead(y=.15, enabled=False)
        
        # Press start text
        self.press = Text(
            "PRESS ANY KEY",
            parent=camera.ui,
            y=-.42,
            scale=1.35,
            color=color.white,
            enabled=False
        )
        
        # Menu buttons
        self.buttons = Entity(parent=camera.ui, enabled=False)
        self.btn_start = Button(
            "Start Game",
            parent=self.buttons,
            scale=(.25, .09),
            y=.05,
            color=color.rgba(100, 200, 100, 220)
        )
        self.btn_quit = Button(
            "Quit",
            parent=self.buttons,
            scale=(.25, .09),
            y=-.25,
            color=color.rgba(200, 100, 100, 220)
        )
        
        self.btn_start.on_click = self.start_game
        self.btn_quit.on_click = application.quit
        
        # File select menu
        self.file_menu = FileSelectMenu(self._file_chosen, enabled=True)
        
    def _setup_game_states(self):
        """Initialize game state variables."""
        self.state = 'FILE'  # FILE, ATTRACT, MAIN, PLAY
        self.selected_file = None
        self.level = None
        self.player = None
        
    def _file_chosen(self, file_index, file_data):
        """Handle file selection."""
        self.selected_file = file_index
        self.fade(1, .5, lambda: invoke(self._show_title, delay=.5))
        
    def _show_title(self):
        """Show title screen after file selection."""
        self.file_menu.enabled = False
        self.state = 'ATTRACT'
        
        # Enable title screen elements
        self.title.enabled = True
        self.ring.enabled = True
        self.head.enabled = True
        self.press.enabled = True
        
        self.fade(0, .5)
        
    def fade(self, alpha, duration, callback=None):
        """Perform screen fade transition."""
        self.fader.animate_color(color.rgba(0, 0, 0, alpha), duration=duration)
        if callback:
            invoke(callback, delay=duration)
            
    def goto_main_menu(self):
        """Go to main menu from attract mode."""
        if self.state != 'ATTRACT':
            return
            
        self.press.enabled = False
        self.buttons.enabled = True
        self.state = 'MAIN'
        
        # Animate buttons in
        for i, btn in enumerate([self.btn_start, self.btn_quit]):
            btn.scale = (.001, .001)
            btn.animate_scale((.25, .09), duration=.1 + i * .05, curve=curve.out_back)
            
    def start_game(self):
        """Start the game."""
        self.state = 'PLAY'
        self.fade(1, .8, lambda: invoke(self.enter_game, delay=.2))
        
    def enter_game(self):
        """Enter the game level."""
        # Hide title screen elements
        self.title.enabled = False
        self.ring.enabled = False
        self.press.enabled = False
        self.buttons.enabled = False
        
        # Setup game environment
        destroy(self.sky)
        self.sky = Sky(color=color.rgb(100, 150, 255))
        
        # Create level
        self.level = TechDemo()
        
        # Create player
        self.player = DebugFPC(position=(0, 3, 0))
        self.level.player = self.player
        
        # Attach head to player
        self.head.parent = self.player
        self.head.position = (0, 1.8, 0)
        self.head.game_mode = True
        self.head.enabled = True
        
        # Level title
        Text(
            "TECH DEMO - DS TEST STAGE",
            parent=camera.ui,
            position=(0, .4),
            scale=2,
            color=color.yellow,
            background=True,
            origin=(0, 0)
        )
        
        # Fade out
        self.fade(0, .8)
        
        # Add win condition check
        self.win_text = None
        
    def input(self, key):
        """Handle global input events."""
        if key == 'f11':
            window.fullscreen = not window.fullscreen
            
        if self.state == 'FILE' and key == 'escape':
            application.quit()
            
        if self.state == 'ATTRACT' and key in ('enter', 'space', 'left mouse down', 'right mouse down'):
            self.goto_main_menu()
            
        if self.state == 'MAIN' and key == 'escape':
            self.buttons.enabled = False
            self.press.enabled = True
            self.state = 'ATTRACT'
            
    def update(self):
        """Update game state."""
        if self.ring.enabled:
            self.ring.rotation_y += 15 * time.dt
            
        if self.state == 'ATTRACT':
            # Pulse the press text
            pulse = sin(time.time() * 3.2) * 0.5 + 0.5
            self.press.color = color.rgba(255, 255, 255, 128 + int(127 * pulse))
            
            # Subtle head bobbing
            self.head.y = 0.15 + sin(time.time() * 2) * 0.02
        else:
            self.press.color = color.white

# ─────────────────────────────────────────────
# Application Boot
# ─────────────────────────────────────────────
if __name__ == '__main__':
    app = Ursina(
        title='Ultra Mario 3D Bros – Tech Demo',
        borderless=False,
        fullscreen=False,
        vsync=True
    )
    
    window.color = color.rgb(14, 22, 40)
    window.fps_counter.enabled = True  # Enable for debugging
    
    # Create main game controller
    main_game = Main()
    
    # Controls hint
    Text(
        "CONTROLS: F11 - Toggle Fullscreen | ESC - Main Menu/Quit | F5 - Fly Mode | F8 - God Mode",
        parent=camera.ui,
        origin=(.5, -.5),
        x=.48,
        y=-.48,
        scale=.65,
        color=color.rgba(255, 255, 255, .75)
    )
    
    print("Game initialized successfully!")
    print("Press F11 to toggle fullscreen")
    print("Press ESC to quit from file select or return to title from main menu")
    print("In game: F5 for fly mode, F8 for god mode")
    
    app.run()
