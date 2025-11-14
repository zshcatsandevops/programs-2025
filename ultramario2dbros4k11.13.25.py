# program.py
# Ultra Mario 2D Bros — Main Menu (single-file, no external assets)
# Requires: Python 3.9+ and pygame 2.x
# Run:  python program.py
#
# Notes:
# - No files are read or written. All assets (sounds, visuals) are procedural.
# - Keyboard: ↑/↓ navigate, ←/→ adjust, Enter/Space confirm, Esc back/quit, F11 toggle fullscreen.
# - Gamepad (if connected): D-Pad/Left Stick navigate, A confirm, B back, Start toggle fullscreen.
# - Integer scaling keeps crisp pixel style; window can be resized.

import math
import sys
import time
import random
from array import array

try:
    import pygame
except Exception as e:
    print("This program needs pygame 2.x:\n    pip install pygame")
    sys.exit(1)

# ----------------------------
# Globals & Constants
# ----------------------------
VIRTUAL_W, VIRTUAL_H = 320, 180   # virtual resolution; scaled to window
FPS = 60

TITLE = "Ultra Mario 2D Bros"
BUILD = "v1.0"

# Palette (high-contrast, retro-leaning)
COL_BG_TOP      = (18,  18,  32)
COL_BG_BOTTOM   = (8,   8,   16)
COL_HILL_1      = (24,  96,  48)
COL_HILL_2      = (16,  72,  40)
COL_HILL_3      = (8,   56,  28)
COL_CLOUD       = (230, 240, 255)
COL_TITLE       = (255, 235, 95)
COL_TITLE_DARK  = (96,  60,  0)
COL_UI          = (245, 245, 245)
COL_UI_DIM      = (160, 160, 160)
COL_ACCENT      = (255, 120, 80)
COL_LOCK        = (130, 130, 130)
COL_HIGHLIGHT   = (255, 255, 255)

# ----------------------------
# Utility
# ----------------------------
def clamp(x, lo, hi): return lo if x < lo else hi if x > hi else x
def lerp(a, b, t):    return a + (b - a) * t

# ----------------------------
# Settings (in-memory only)
# ----------------------------
class Settings:
    def __init__(self):
        self.fullscreen = False
        self.music_vol = 0   # 0..100 (no music assets in this demo)
        self.sfx_vol = 60    # 0..100
        self.scanlines = True
        self.input_hints = True

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen

SETTINGS = Settings()

# ----------------------------
# Procedural SFX (no numpy)
# ----------------------------
class SFX:
    def __init__(self):
        # Initialize mixer with common settings; if already init, ignore
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.pre_init(44100, -16, 1, 256)
                pygame.mixer.init()
            except Exception:
                # Audio-less fallback
                pass

    @staticmethod
    def _tone(freq=880, ms=80, volume=0.2):
        if not pygame.mixer.get_init():  # no audio device
            return None
        sample_rate = 44100
        n_samples = int(sample_rate * (ms / 1000.0))
        buf = array('h')
        amp = int(32767 * volume * (SETTINGS.sfx_vol / 100.0))
        for i in range(n_samples):
            # simple sine + quick decay to avoid clicks
            t = i / sample_rate
            decay = max(0.0, 1.0 - (i / n_samples))
            s = int(amp * math.sin(2 * math.pi * freq * t) * (0.7 + 0.3 * decay))
            buf.append(s)
        return pygame.mixer.Sound(buffer=buf)

    def nav(self):
        snd = self._tone(1200, 40, 0.15)
        if snd: snd.play()

    def confirm(self):
        snd = self._tone(880, 80, 0.25)
        if snd: snd.play()

    def back(self):
        snd = self._tone(220, 90, 0.2)
        if snd: snd.play()

SFXSYS = SFX()

# ----------------------------
# Input Abstraction
# ----------------------------
class Input:
    def __init__(self):
        pygame.joystick.init()
        self.joys = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
        for j in self.joys:
            j.init()
        self._repeat_time = 0
        self._repeat_dir = None

    def any_start(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE):
                return True
            if e.type == pygame.JOYBUTTONDOWN and e.button in (0, 7):  # A or START
                return True
        return False

    def navigate(self, events, dt):
        up = down = left = right = confirm = back = toggle_full = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_F11]: toggle_full = True

        # Keyboard edges
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_UP, pygame.K_w):    up = True
                if e.key in (pygame.K_DOWN, pygame.K_s):  down = True
                if e.key in (pygame.K_LEFT, pygame.K_a):  left = True
                if e.key in (pygame.K_RIGHT, pygame.K_d): right = True
                if e.key in (pygame.K_RETURN, pygame.K_SPACE): confirm = True
                if e.key == pygame.K_ESCAPE: back = True
            elif e.type == pygame.JOYBUTTONDOWN:
                if e.button == 0: confirm = True   # A
                if e.button == 1: back = True      # B
                if e.button == 7: toggle_full = True  # START

        # Gamepad axes / hats (with small deadzone and rate limiting)
        axis_y = axis_x = 0.0
        hat_x = hat_y = 0
        for j in self.joys:
            try:
                axis_y = j.get_axis(1)
                axis_x = j.get_axis(0)
                if j.get_numhats() > 0:
                    hx, hy = j.get_hat(0)
                    hat_x, hat_y = hx, hy
            except Exception:
                pass

        DEAD = 0.35
        raw_up = (axis_y < -DEAD) or (hat_y == 1)
        raw_down = (axis_y > DEAD) or (hat_y == -1)
        raw_left = (axis_x < -DEAD) or (hat_x == -1)
        raw_right = (axis_x > DEAD) or (hat_x == 1)

        # Simple edge-detection for stick to avoid endless repeats
        # (we also allow keyboard edges immediately)
        # We'll implement a manual repeat cooldown.
        if not hasattr(self, "_cool"):
            self._cool = 0

        self._cool -= dt
        if self._cool < 0:
            if raw_up:
                up = True; self._cool = 0.18
            elif raw_down:
                down = True; self._cool = 0.18
            elif raw_left:
                left = True; self._cool = 0.18
            elif raw_right:
                right = True; self._cool = 0.18

        return up, down, left, right, confirm, back, toggle_full

# ----------------------------
# Simple Scene System
# ----------------------------
class Scene:
    def __init__(self, app): self.app = app
    def update(self, dt, events): pass
    def draw(self, surf): pass
    def on_enter(self): pass
    def on_exit(self): pass

# ----------------------------
# Background: gradient, parallax hills, clouds, stars, scanlines
# ----------------------------
class Cloud:
    def __init__(self, y, speed, scale):
        self.x = random.uniform(-40, VIRTUAL_W + 20)
        self.y = y
        self.speed = speed
        self.scale = scale

    def update(self, dt):
        self.x += self.speed * dt
        if self.x > VIRTUAL_W + 40:
            self.x = -60
            self.y = random.uniform(10, 70) * self.scale

    def draw(self, surf):
        x = int(self.x)
        y = int(self.y)
        s = int(20 * self.scale)
        pygame.draw.ellipse(surf, COL_CLOUD, pygame.Rect(x, y, s*3, s))
        pygame.draw.ellipse(surf, COL_CLOUD, pygame.Rect(x + s*2, y-5, s*2, s))
        pygame.draw.ellipse(surf, COL_CLOUD, pygame.Rect(x + s, y-8, s*2, s))

class Star:
    def __init__(self):
        self.x = random.randint(0, VIRTUAL_W-1)
        self.y = random.randint(0, VIRTUAL_H//2)
        self.t = random.random() * 2*math.pi

    def update(self, dt):
        self.t += dt * 4

    def draw(self, surf):
        a = 150 + int(105 * (0.5 + 0.5*math.sin(self.t)))
        surf.set_at((self.x, self.y), (a,a,a))

class Background:
    def __init__(self):
        self.clouds = [Cloud(random.uniform(10, 70), random.uniform(8, 18), random.uniform(0.6, 1.2)) for _ in range(8)]
        self.stars  = [Star() for _ in range(60)]

        self.t = 0

    def update(self, dt):
        self.t += dt
        for c in self.clouds: c.update(dt * 60/60.0)
        for s in self.stars:  s.update(dt)

    def draw_gradient(self, surf):
        # vertical gradient
        for y in range(VIRTUAL_H):
            t = y / (VIRTUAL_H-1)
            r = int(lerp(COL_BG_TOP[0], COL_BG_BOTTOM[0], t))
            g = int(lerp(COL_BG_TOP[1], COL_BG_BOTTOM[1], t))
            b = int(lerp(COL_BG_TOP[2], COL_BG_BOTTOM[2], t))
            pygame.draw.line(surf, (r,g,b), (0,y), (VIRTUAL_W,y))

    def draw_hills(self, surf):
        # 3 parallax layers
        def hill(ybase, amp, color, speed):
            points = []
            off = (self.t * speed) % VIRTUAL_W
            for x in range(0, VIRTUAL_W+1, 2):
                # rolling sine hills
                y = ybase + math.sin((x + off) * 0.02) * amp + math.sin((x + off) * 0.05) * (amp*0.4)
                points.append((x, int(y)))
            points += [(VIRTUAL_W, VIRTUAL_H), (0, VIRTUAL_H)]
            pygame.draw.polygon(surf, color, points)

        hill(VIRTUAL_H*0.88, 6, COL_HILL_3, 6)
        hill(VIRTUAL_H*0.92, 8, COL_HILL_2, 10)
        hill(VIRTUAL_H*0.96, 10, COL_HILL_1, 14)

    def draw(self, surf):
        self.draw_gradient(surf)
        # Stars first (upper sky)
        for s in self.stars: s.draw(surf)
        # Clouds
        for c in self.clouds: c.draw(surf)
        # Hills
        self.draw_hills(surf)
        # Ground line
        pygame.draw.line(surf, (12,22,12), (0, int(VIRTUAL_H*0.965)), (VIRTUAL_W, int(VIRTUAL_H*0.965)))

    def draw_scanlines(self, surf):
        if not SETTINGS.scanlines: return
        for y in range(0, VIRTUAL_H, 2):
            pygame.draw.line(surf, (0, 0, 0, 48), (0,y), (VIRTUAL_W, y))

# ----------------------------
# Menu Framework
# ----------------------------
class MenuItem:
    def __init__(self, text, action=None, enabled=True, value_getter=None, value_setter=None):
        self.text = text
        self.action = action          # callable or None
        self.enabled = enabled
        self.value_getter = value_getter
        self.value_setter = value_setter

    def is_adjustable(self):
        return self.value_getter is not None and self.value_setter is not None

class Menu:
    def __init__(self, title, items):
        self.title = title
        self.items = items
        self.index = 0
        # Move selection to first enabled item
        self._ensure_enabled_index(forward=True)

    def _ensure_enabled_index(self, forward=True):
        if any(i.enabled for i in self.items):
            attempts = 0
            while not self.items[self.index].enabled and attempts < len(self.items)+1:
                self.index = (self.index + (1 if forward else -1)) % len(self.items)
                attempts += 1

    def navigate(self, dir_y, dir_x):
        changed = False
        if dir_y != 0:
            prev = self.index
            self.index = (self.index + dir_y) % len(self.items)
            self._ensure_enabled_index(forward=(dir_y>0))
            changed = (self.index != prev)
        if dir_x != 0 and self.items[self.index].is_adjustable():
            # Adjust numeric/toggle values via setter
            self.items[self.index].value_setter(dir_x)
            changed = True
        return changed

    def activate(self):
        item = self.items[self.index]
        if item.enabled and item.action:
            item.action()

# ----------------------------
# Scenes
# ----------------------------
class MainMenu(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.bg = Background()
        self.pulse_t = 0.0
        self.title_wobble_t = 0.0

        self.menu = Menu("MAIN MENU", [
            MenuItem("Start Game", action=self.start_game),
            MenuItem("Level Select", enabled=False),  # Locked in this demo
            MenuItem("Options", action=self.goto_options),
            MenuItem("Credits", action=self.goto_credits),
            MenuItem("Quit", action=self.app.quit),
        ])

        self.fade = 1.0  # fade-in from black

    def on_enter(self):
        self.fade = 1.0

    def start_game(self):
        SFXSYS.confirm()
        self.app.push_scene(StartGamePlaceholder(self.app))

    def goto_options(self):
        SFXSYS.confirm()
        self.app.push_scene(OptionsMenu(self.app))

    def goto_credits(self):
        SFXSYS.confirm()
        self.app.push_scene(Credits(self.app))

    def update(self, dt, events):
        self.bg.update(dt)
        self.pulse_t += dt
        self.title_wobble_t += dt * 2
        self.fade = max(0.0, self.fade - dt * 1.5)

        up, down, left, right, ok, back, toggle_full = self.app.input.navigate(events, dt)
        if toggle_full:
            SETTINGS.toggle_fullscreen()
            self.app.apply_display_mode()
        moved = 0
        if up:   moved -= 1
        if down: moved += 1
        if moved != 0:
            if self.menu.navigate(moved, 0):
                SFXSYS.nav()
        if ok:
            self.menu.activate()
        if back:
            SFXSYS.back()
            self.app.quit()

    def draw_title(self, surf, font_big, font_small):
        # Wobble title with shadow
        t = self.title_wobble_t
        wobx = int(math.sin(t*1.3) * 1)
        woby = int(math.cos(t*0.9) * 1)
        title_text = TITLE
        shadow = font_big.render(title_text, True, COL_TITLE_DARK)
        text   = font_big.render(title_text, True, COL_TITLE)
        x = VIRTUAL_W//2
        y = 28 + woby
        surf.blit(shadow, shadow.get_rect(center=(x+2+wobx, y+2)))
        surf.blit(text, text.get_rect(center=(x+wobx, y)))
        # Build tag
        tag = font_small.render(BUILD, True, COL_UI_DIM)
        surf.blit(tag, tag.get_rect(center=(x, y+22)))

    def draw_menu(self, surf, font, font_small):
        # Menu items
        base_y = 78
        for i, item in enumerate(self.menu.items):
            is_sel = (i == self.menu.index)
            col = COL_HIGHLIGHT if (is_sel and item.enabled) else (COL_UI if item.enabled else COL_LOCK)

            label = item.text
            if not item.enabled:
                label += "  (locked)"
            text = font.render(label, True, col)
            rect = text.get_rect(center=(VIRTUAL_W//2, base_y + i*16))
            if is_sel:
                # Selection arrow
                t = self.pulse_t
                offs = int((math.sin(t*6)+1)*0.5*2)
                pygame.draw.polygon(surf, COL_ACCENT, [(rect.left-20, rect.centery),
                                                       (rect.left-12, rect.centery-4),
                                                       (rect.left-12, rect.centery+4)])
                pygame.draw.circle(surf, COL_ACCENT, (rect.right+10+offs, rect.centery), 2)
            surf.blit(text, rect)

        # Footer hint
        if SETTINGS.input_hints:
            s = font_small.render("Enter/A: Select    Esc/B: Back    \u2190/\u2192: Adjust", True, COL_UI_DIM)
            surf.blit(s, (VIRTUAL_W//2 - s.get_width()//2, VIRTUAL_H - 16))

        # Press Start pulse (only when nothing selected yet — but we always show for style)
        a = 0.6 + 0.4 * math.sin(self.pulse_t*4)
        press = font_small.render("Press Start", True, (int(200*a), int(200*a), 255))
        surf.blit(press, (8, 8))

    def draw(self, surf):
        self.bg.draw(surf)
        # Fonts
        font_big   = self.app.font_big
        font       = self.app.font
        font_small = self.app.font_small

        self.draw_title(surf, font_big, font_small)
        self.draw_menu(surf, font, font_small)

        # Scanlines overlay
        self.bg.draw_scanlines(surf)

        # Fade-in
        if self.fade > 0:
            f = int(self.fade * 255)
            overlay = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
            overlay.fill((0,0,0,f))
            surf.blit(overlay, (0,0))

class OptionsMenu(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.bg = Background()
        def vol_setter(name):
            def _set(delta):
                v = getattr(SETTINGS, name)
                v = clamp(v + delta*10, 0, 100)
                setattr(SETTINGS, name, v)
                SFXSYS.nav()
            return _set
        def toggle(name):
            def _act():
                setattr(SETTINGS, name, not getattr(SETTINGS, name))
                SFXSYS.confirm()
            return _act
        self.menu = Menu("OPTIONS", [
            MenuItem("Fullscreen", action=self.toggle_fullscreen),
            MenuItem("SFX Volume", value_getter=lambda: SETTINGS.sfx_vol, value_setter=vol_setter("sfx_vol")),
            MenuItem("Music Volume", value_getter=lambda: SETTINGS.music_vol, value_setter=vol_setter("music_vol")),
            MenuItem("Scanlines", action=toggle("scanlines")),
            MenuItem("Input Hints", action=toggle("input_hints")),
            MenuItem("Back", action=self.back)
        ])
        self.fade = 1.0

    def toggle_fullscreen(self):
        SETTINGS.toggle_fullscreen()
        self.app.apply_display_mode()
        SFXSYS.confirm()

    def back(self):
        SFXSYS.back()
        self.app.pop_scene()

    def update(self, dt, events):
        self.bg.update(dt)
        self.fade = max(0.0, self.fade - dt * 2.0)
        up, down, left, right, ok, back, toggle_full = self.app.input.navigate(events, dt)
        if toggle_full:
            SETTINGS.toggle_fullscreen()
            self.app.apply_display_mode()

        moved = 0
        if up:   moved -= 1
        if down: moved += 1
        if moved != 0:
            if self.menu.navigate(moved, 0):
                SFXSYS.nav()
        # Adjust or activate
        if left:  self.menu.navigate(0, -1)
        if right: self.menu.navigate(0, +1)
        if ok:
            it = self.menu.items[self.menu.index]
            if it.is_adjustable():
                self.menu.navigate(0, +1)
            elif it.action:
                it.action()
        if back:
            self.back()

    def draw(self, surf):
        self.bg.draw(surf)
        font_big, font, font_small = self.app.font_big, self.app.font, self.app.font_small

        # Title
        title = font_big.render("Options", True, COL_TITLE)
        surf.blit(title, title.get_rect(center=(VIRTUAL_W//2, 26)))

        # Items
        base_y = 64
        for i, item in enumerate(self.menu.items):
            is_sel = (i == self.menu.index)
            col = COL_HIGHLIGHT if is_sel else COL_UI
            label = item.text
            text = font.render(label, True, col)
            rect = text.get_rect(topleft=(36, base_y + i*16))
            surf.blit(text, rect)
            # Values / toggles
            if item.is_adjustable():
                val = item.value_getter()
                val_text = font.render(str(val), True, COL_ACCENT if is_sel else COL_UI_DIM)
                surf.blit(val_text, (VIRTUAL_W - 36 - val_text.get_width(), rect.y))
            elif item.action and ("Scanlines" in item.text or "Input Hints" in item.text or "Fullscreen" in item.text):
                state = "On" if (SETTINGS.scanlines if "Scanlines" in item.text else SETTINGS.input_hints if "Input Hints" in item.text else SETTINGS.fullscreen) else "Off"
                val_text = font.render(state, True, COL_ACCENT if is_sel else COL_UI_DIM)
                surf.blit(val_text, (VIRTUAL_W - 36 - val_text.get_width(), rect.y))

        # Footer
        hint = font_small.render("\u2190/\u2192 adjust • Enter/A toggle • Esc/B back", True, COL_UI_DIM)
        surf.blit(hint, hint.get_rect(center=(VIRTUAL_W//2, VIRTUAL_H-12)))

        # Scanlines
        self.bg.draw_scanlines(surf)

        # Fade-in
        if self.fade > 0:
            f = int(self.fade * 255)
            overlay = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
            overlay.fill((0,0,0,f))
            surf.blit(overlay, (0,0))

class Credits(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.bg = Background()
        self.scroll_y = VIRTUAL_H + 20
        self.lines = [
            "Ultra Mario 2D Bros",
            "",
            "Main Menu Demo",
            "",
            "Design & Code",
            "— You",
            "",
            "Audio",
            "— Procedural SFX",
            "",
            "Special Thanks",
            "— Pygame Community",
            "",
            "© 2025 Ultra Fan Project (Non-Commercial)",
        ]
        self.fade = 1.0

    def update(self, dt, events):
        self.bg.update(dt)
        self.fade = max(0.0, self.fade - dt * 2.0)
        self.scroll_y -= dt * 22

        _, _, _, _, ok, back, toggle_full = self.app.input.navigate(events, dt)
        if toggle_full:
            SETTINGS.toggle_fullscreen()
            self.app.apply_display_mode()
        if ok or back or self.scroll_y < -len(self.lines)*14 - 20:
            SFXSYS.back()
            self.app.pop_scene()

    def draw(self, surf):
        self.bg.draw(surf)
        font_big, font, font_small = self.app.font_big, self.app.font, self.app.font_small

        title = font_big.render("Credits", True, COL_TITLE)
        surf.blit(title, title.get_rect(center=(VIRTUAL_W//2, 24)))

        y = int(self.scroll_y)
        for i, line in enumerate(self.lines):
            f = font if line and not line.startswith("—") and not line.endswith("Demo") else font_small
            col = COL_UI if line and not line.startswith("©") else COL_UI_DIM
            txt = f.render(line, True, col)
            surf.blit(txt, txt.get_rect(center=(VIRTUAL_W//2, y + i*14)))

        self.bg.draw_scanlines(surf)

        if self.fade > 0:
            f = int(self.fade * 255)
            overlay = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
            overlay.fill((0,0,0,f))
            surf.blit(overlay, (0,0))

class StartGamePlaceholder(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.bg = Background()
        self.timer = 0
        self.fade = 1.0

    def update(self, dt, events):
        self.bg.update(dt)
        self.timer += dt
        self.fade = max(0.0, self.fade - dt * 2.0)
        _, _, _, _, ok, back, toggle_full = self.app.input.navigate(events, dt)
        if toggle_full:
            SETTINGS.toggle_fullscreen()
            self.app.apply_display_mode()
        if ok or back or self.timer > 2.0:
            self.app.pop_scene()  # Return to main menu for this demo

    def draw(self, surf):
        self.bg.draw(surf)
        font_big, font, font_small = self.app.font_big, self.app.font, self.app.font_small
        t1 = font_big.render("Loading...", True, COL_TITLE)
        t2 = font.render("Game bootstrap placeholder", True, COL_UI)
        surf.blit(t1, t1.get_rect(center=(VIRTUAL_W//2, VIRTUAL_H//2 - 8)))
        surf.blit(t2, t2.get_rect(center=(VIRTUAL_W//2, VIRTUAL_H//2 + 10)))
        self.bg.draw_scanlines(surf)
        if self.fade > 0:
            f = int(self.fade * 255)
            overlay = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
            overlay.fill((0,0,0,f))
            surf.blit(overlay, (0,0))

# ----------------------------
# App
# ----------------------------
class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.input = Input()

        # Fonts (use default; scale for crisp pixel look)
        self.font_small = pygame.font.Font(None, 16)
        self.font       = pygame.font.Font(None, 20)
        self.font_big   = pygame.font.Font(None, 36)

        # Display surfaces
        self.window = None
        self.screen = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)

        self.apply_display_mode()
        self._set_window_icon()

        # Scene stack
        self.scenes = []
        self.push_scene(MainMenu(self))

    # Create a simple, distinctive window icon programmatically
    def _set_window_icon(self):
        icon = pygame.Surface((32,32), pygame.SRCALPHA)
        icon.fill((0,0,0,0))
        pygame.draw.rect(icon, (255, 200, 0), (2, 18, 28, 12))
        pygame.draw.circle(icon, (255, 240, 120), (16, 10), 8)
        pygame.draw.rect(icon, (180, 60, 0), (6, 22, 6, 6))
        pygame.draw.rect(icon, (0, 120, 40), (20, 22, 6, 6))
        pygame.display.set_icon(icon)

    def apply_display_mode(self):
        flags = pygame.RESIZABLE
        if SETTINGS.fullscreen:
            flags |= pygame.FULLSCREEN
        # Try enabling vsync if available
        try:
            self.window = pygame.display.set_mode((VIRTUAL_W*3, VIRTUAL_H*3), flags, vsync=1)
        except TypeError:
            self.window = pygame.display.set_mode((VIRTUAL_W*3, VIRTUAL_H*3), flags)

    def push_scene(self, scene):
        if self.scenes:
            self.scenes[-1].on_exit()
        self.scenes.append(scene)
        scene.on_enter()

    def pop_scene(self):
        if self.scenes:
            self.scenes[-1].on_exit()
            self.scenes.pop()
        if self.scenes:
            self.scenes[-1].on_enter()
        else:
            self.quit()

    def quit(self):
        pygame.quit()
        sys.exit(0)

    # Letterboxed integer scaling for crisp pixels
    def _blit_scaled(self):
        win_w, win_h = self.window.get_size()
        scale = max(1, min(win_w // VIRTUAL_W, win_h // VIRTUAL_H))
        surf_w = VIRTUAL_W * scale
        surf_h = VIRTUAL_H * scale
        x = (win_w - surf_w) // 2
        y = (win_h - surf_h) // 2
        scaled = pygame.transform.scale(self.screen, (surf_w, surf_h))
        self.window.fill((0,0,0))
        self.window.blit(scaled, (x, y))

    def run(self):
        prev = time.perf_counter()
        while True:
            now = time.perf_counter()
            dt = clamp(now - prev, 0.0, 1/20)
            prev = now

            events = [e for e in pygame.event.get()]
            for e in events:
                if e.type == pygame.QUIT:
                    self.quit()
                if e.type == pygame.KEYDOWN and e.key == pygame.K_F11:
                    SETTINGS.toggle_fullscreen()
                    self.apply_display_mode()

            # Update current scene
            if not self.scenes:
                self.quit()
            scene = self.scenes[-1]
            scene.update(dt, events)

            # Draw
            self.screen.fill((0,0,0))
            scene.draw(self.screen)

            # Present
            self._blit_scaled()
            pygame.display.flip()
            self.clock.tick(FPS)

# ----------------------------
# Entry Point
# ----------------------------
if __name__ == "__main__":
    App().run()
