#!/usr/bin/env python3
"""
Ultra Mario 3D Bros — Beta Build (DirectX Stable Full Edition)
-------------------------------------------------------------
Full version with launcher, cutscene, complete Ursina SM64-like gameplay engine.
Stable on DirectX (ANGLE) backend.
"""

import os
# Force DirectX backend for Ursina stability
os.environ["PYGLET_SHADOW_WINDOW"] = "0"
os.environ["PYGLET_HEADLESS"] = "false"
os.environ["PYGLET_GL_BACKEND"] = "angle"

import math, random, time as pytime, tkinter as tk
from tkinter import ttk, messagebox
import subprocess, sys

# --------------------------------------------------------------
#  LAUNCHER SECTION
# --------------------------------------------------------------
class UltraMarioLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Ultra Mario 3D Bros - Beta Build")
        self.root.geometry("800x600")
        self.root.configure(bg='#0a0a2a')
        self.root.resizable(False, False)
        self.center_window()
        self.launch_after_close = False

        self.settings = {
            "graphics_quality": "Medium",
            "music_enabled": True,
            "sound_volume": 50,
            "beta_mode": True,
            "debug_mode": False,
            "save_file": "MARIO",
        }
        self.create_menu()

    def center_window(self):
        self.root.update_idletasks()
        width, height = 800, 600
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def create_menu(self):
        for w in self.root.winfo_children():
            w.destroy()
        main_frame = tk.Frame(self.root, bg="#0a0a2a")
        main_frame.pack(expand=True, fill="both")

        tk.Label(main_frame, text="ULTRA MARIO 3D BROS", font=('Arial', 32, 'bold'), fg='#FFD700', bg='#0a0a2a').pack(pady=(60, 5))
        tk.Label(main_frame, text="TECH DEMO", font=('Arial', 18, 'bold'), fg='#FF6600', bg='#0a0a2a').pack(pady=(0, 20))

        tk.Button(main_frame, text="PLAY GAME", font=('Arial', 16, 'bold'), width=20, height=2, bg='#FF0000', fg='white', relief='raised', bd=4, activebackground='#CC0000', command=self.start_game).pack(pady=20)
        tk.Button(main_frame, text="EXIT", font=('Arial', 16, 'bold'), width=20, height=2, bg='#444', fg='white', command=self.root.destroy).pack(pady=10)

        self.status_label = tk.Label(main_frame, text="Press PLAY GAME to begin your adventure!", font=('Arial', 10), fg='#00FF00', bg='#0a0a2a')
        self.status_label.pack(side='bottom', pady=20)

    def start_game(self):
        self.show_cutscene()

    def show_cutscene(self):
        for w in self.root.winfo_children():
            w.destroy()
        cut = tk.Frame(self.root, bg='#0a0a2a')
        cut.pack(expand=True, fill='both')
        lines = [("Dear Mario,", 1000), ("Please come to the castle.", 2500), ("I have baked a cake for you.", 4000), ("Yours truly,", 6000), ("— Princess Toadstool, Peach", 7500)]
        lbls = [tk.Label(cut, text="", font=('Comic Sans MS', 24, 'italic'), fg='white', bg='#0a0a2a') for _ in range(5)]
        for l in lbls: l.pack(pady=10)
        for i, (t, d) in enumerate(lines):
            self.root.after(d, lambda i=i, t=t: lbls[i].config(text=t))
        self.root.after(9500, self.launch_game_after_cutscene)

    def launch_game_after_cutscene(self):
        self.root.destroy()
        pytime.sleep(0.5)
        subprocess.Popen([sys.executable, os.path.abspath(__file__), 'play'])

# --------------------------------------------------------------
#  GAME SECTION
# --------------------------------------------------------------
def run_game():
    # Removed redundant 'import ursina' line
    from ursina import Ursina, Entity, Vec3, camera, color, window, raycast, held_keys, time, Sky, DirectionalLight, AmbientLight, scene

    app = Ursina(title='Ultra Mario 3D Bros – DX Stable Full Edition', development_mode=False)
    window.color = color.rgb(70, 120, 180)

    GRAVITY = 28.0
    WALK_SPEED = 6.5
    RUN_MULT = 1.6
    JUMP_V0 = 11.0

    class Player(Entity):
        def __init__(self):
            super().__init__(model='cube', color=color.clear, scale=(0.9, 1.8, 0.9), position=(0, 2, 5), collider='box')
            self.body = Entity(parent=self, model='cube', color=color.red, scale=(0.8, 1.0, 0.6), y=0)
            self.overalls = Entity(parent=self.body, model='cube', color=color.blue, scale=(1.05, 0.7, 1.05), y=-0.3)
            self.head = Entity(parent=self, model='sphere', color=color.rgb(255, 200, 150), scale=0.7, y=0.95)
            self.hat = Entity(parent=self.head, model='cube', color=color.red, scale=(0.9, 0.25, 0.9), y=0.45)
            camera.parent = self; camera.position = (0, 1.6, -10); camera.rotation_x = 10; self.rotation_y = 180
            self.vel_y = 0; self.grounded = False

        def update(self):
            dt = time.dt
            move = Vec3(0, 0, 0)
            move += self.forward * (held_keys['w'] or held_keys['up arrow'])
            move -= self.forward * (held_keys['s'] or held_keys['down arrow'])
            move += self.right * (held_keys['d'] or held_keys['right arrow'])
            move -= self.right * (held_keys['a'] or held_keys['left arrow'])
            speed = WALK_SPEED * (RUN_MULT if held_keys['shift'] else 1)
            if move.length() > 0:
                move = move.normalized()
                hit = raycast(self.position + Vec3(0, 0.6, 0), move, distance=0.7, ignore=[self])
                if not hit.hit:
                    self.position += move * speed * dt
            self.vel_y -= GRAVITY * dt
            self.y += self.vel_y * dt
            
            # --- BUG FIX ---
            # Changed raycast start position from `self.position + Vec3(0, 0.5, 0)` to `self.position`.
            # The old start point was too high, causing the ray to check *above* the player's feet.
            # The player would then fall through the ground.
            # This new start point (player's center) correctly checks past the player's feet.
            hit_ground = raycast(self.position, Vec3(0, -1, 0), distance=1.1, ignore=[self])
            
            if hit_ground.hit:
                self.y = hit_ground.world_point.y + 0.9
                self.vel_y = 0; self.grounded = True
            else:
                self.grounded = False

        def input(self, key):
            if key == 'space' and self.grounded:
                self.vel_y = JUMP_V0

    class World:
        def __init__(self, player):
            Sky()
            DirectionalLight(parent=scene, y=12, z=8, rotation=(35, 35, 0))
            AmbientLight(color=color.rgba(150, 150, 150, 255))
            Entity(model='plane', color=color.rgb(80, 150, 80), scale=(100, 1, 100), position=(0, 0, 0), collider='box') # Added collider to ground
            Entity(model='cube', color=color.light_gray, scale=(20, 10, 2), position=(0, 5, 24), collider='box')
            Entity(model='cube', color=color.dark_gray, scale=(4, 5, 2.1), position=(0, 2.5, 23), collider='box')
            for x in [-12, 12]:
                Entity(model='cube', color=color.light_gray, scale=(4, 15, 4), position=(x, 7.5, 24), collider='box')
                Entity(model='cone', color=color.red, scale=(4.8, 3, 4.8), position=(x, 16.5, 24)) # Roofs don't need colliders
            for x in [-8, -4, 4, 8]:
                for y in [7, 10]:
                    Entity(model='cube', color=color.dark_blue, scale=(1.5, 1.5, 0.5), position=(x, y, 23)) # Windows don't need colliders
            Entity(model='cylinder', color=color.gray, scale=(1, 3, 1), position=(0, 1.8, 5), collider='box')
            for i in range(8):
                ang = i / 8 * 2 * math.pi; x = math.sin(ang) * 3; z = math.cos(ang) * 3 + 5
                Entity(model='cube', color=color.gray, scale=(1, 0.2, 1), position=(x, 0.5, z), collider='box')

    player = Player(); World(player)
    print("✅ Ultra Mario 3D Bros launched with DirectX backend.")
    app.run()

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'play':
        run_game()
    else:
        root = tk.Tk(); UltraMarioLauncher(root); root.mainloop()
