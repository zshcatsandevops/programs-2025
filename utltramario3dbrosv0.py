import math
import random
import time as pytime
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sys
import os
import json

class UltraMarioLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Ultra Mario 3D Bros - Beta Build")
        self.root.geometry("800x600")
        self.root.configure(bg='#0a0a2a')
        self.root.resizable(False, False)
        self.center_window()
        self.settings = {
            "graphics_quality": "Medium",
            "music_enabled": True,
            "sound_volume": 50,
            "custom_level_path": "",
            "beta_mode": True,
            "debug_mode": False
        }
        self.load_settings()
        self.create_menu()

    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry('{}x{}+{}+{}'.format(width, height, x, y))

    def load_settings(self):
        try:
            if os.path.exists("ultra_mario_settings.json"):
                with open("ultra_mario_settings.json", "r") as f:
                    self.settings.update(json.load(f))
        except Exception as e:
            print(f"Error loading settings: {e}")

    def save_settings(self):
        try:
            with open("ultra_mario_settings.json", "w") as f:
                json.dump(self.settings, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False

    def create_menu(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        main_frame = tk.Frame(self.root, bg='#0a0a2a')
        main_frame.pack(expand=True, fill='both')
        title_label = tk.Label(main_frame, text="ULTRA MARIO 3D BROS", font=('Arial', 32, 'bold'), fg='#FFD700', bg='#0a0a2a')
        title_label.pack(pady=(60, 5))
        beta_label = tk.Label(main_frame, text="TECH DEMO", font=('Arial', 18, 'bold'), fg='#FF6600', bg='#0a0a2a')
        beta_label.pack(pady=(0, 20))
        file_frame = tk.Frame(main_frame, bg='#0a0a2a')
        file_frame.pack(pady=10)
        self.file_label = tk.Label(file_frame, text=f"FILE: {self.settings.get('save_file', 'MARIO')}", font=('Arial', 14), fg='#FFFFFF', bg='#0a0a2a')
        self.file_label.pack(side='left', padx=10)
        file_button = tk.Button(file_frame, text="CHANGE", command=self.change_file, font=('Arial', 12), width=8, bg='#444444', fg='white', relief='raised', bd=2, activebackground='#666666', activeforeground='white')
        file_button.pack(side='left')
        button_style = {'font': ('Arial', 16, 'bold'), 'width': 20, 'height': 2, 'bg': '#FF0000', 'fg': 'white', 'relief': 'raised', 'bd': 4, 'activebackground': '#CC0000', 'activeforeground': 'white'}
        self.start_button = tk.Button(main_frame, text="PLAY GAME", command=self.start_game, **button_style)
        self.start_button.pack(pady=10)
        self.files_button = tk.Button(main_frame, text="FILES", command=self.show_files, **button_style)
        self.files_button.pack(pady=10)
        self.copy_button = tk.Button(main_frame, text="COPY", command=self.copy_file, **button_style)
        self.copy_button.pack(pady=10)
        self.erase_button = tk.Button(main_frame, text="ERASE", command=self.erase_file, **button_style)
        self.erase_button.pack(pady=10)
        self.options_button = tk.Button(main_frame, text="OPTIONS", command=self.show_options, **button_style)
        self.options_button.pack(pady=10)
        score_frame = tk.Frame(main_frame, bg='#0a0a2a')
        score_frame.pack(pady=10)
        score_label = tk.Label(score_frame, text="HIGH SCORE", font=('Arial', 12), fg='#FFFFFF', bg='#0a0a2a')
        score_label.pack(side='left', padx=10)
        score_value = tk.Label(score_frame, text=f"{self.settings.get('high_score', '0000')}", font=('Arial', 12, 'bold'), fg='#FFD700', bg='#0a0a2a')
        score_value.pack(side='left')
        status_frame = tk.Frame(main_frame, bg='#0a0a2a')
        status_frame.pack(side='bottom', fill='x', pady=20)
        self.status_label = tk.Label(status_frame, text="Press PLAY GAME to begin your adventure!", font=('Arial', 10), fg='#00FF00', bg='#0a0a2a')
        self.status_label.pack()

    def change_file(self):
        files = ["MARIO", "LUIGI", "TOAD", "PEACH"]
        current = self.settings.get('save_file', 'MARIO')
        current_index = files.index(current) if current in files else 0
        new_index = (current_index + 1) % len(files)
        self.settings['save_file'] = files[new_index]
        self.save_settings()
        self.file_label.config(text=f"FILE: {self.settings['save_file']}")
        self.status_label.config(text=f"Switched to {self.settings['save_file']} file!")

    def copy_file(self):
        # This is a placeholder, as no file system logic exists yet
        self.status_label.config(text=f"Copying {self.settings.get('save_file', 'MARIO')} file...")
        self.root.update()
        self.root.after(1000, lambda: self.status_label.config(text="File copied successfully!"))

    def erase_file(self):
        # This is a placeholder, as no file system logic exists yet
        result = messagebox.askyesno("Erase File", f"Are you sure you want to erase {self.settings.get('save_file', 'MARIO')} file?")
        if result:
            self.status_label.config(text=f"Erasing {self.settings.get('save_file', 'MARIO')} file...")
            self.root.update()
            # Add actual file erase logic here
            self.root.after(1000, lambda: self.status_label.config(text="File erased successfully!"))

    def start_game(self):
        # Instead of launching, show the cutscene first
        self.show_cutscene()

    def show_cutscene(self):
        # 1. Clear the main menu
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # 2. Create a new frame for the cutscene
        cutscene_frame = tk.Frame(self.root, bg='#0a0a2a')
        cutscene_frame.pack(expand=True, fill='both')
        
        # 3. Create labels for the text (initially empty)
        # We use a handwriting-style font if available, otherwise default
        font_choice = ('Times New Roman', 24, 'italic')
        try:
            # Try a more stylized font, fallback to Times
            # 'Comic Sans MS' is widely available and looks more like handwriting
            font_choice = ('Comic Sans MS', 24, 'italic') 
        except tk.TclError:
            pass # Fallback to default Times New Roman

        self.line1 = tk.Label(cutscene_frame, text="", font=font_choice, fg='white', bg='#0a0a2a')
        self.line1.pack(pady=(150, 10))
        
        self.line2 = tk.Label(cutscene_frame, text="", font=font_choice, fg='white', bg='#0a0a2a')
        self.line2.pack(pady=10)
        
        self.line3 = tk.Label(cutscene_frame, text="", font=font_choice, fg='white', bg='#0a0a2a')
        self.line3.pack(pady=10)
        
        sign_font = (font_choice[0], 28, 'italic')
        
        self.line4 = tk.Label(cutscene_frame, text="", font=sign_font, fg='white', bg='#0a0a2a')
        self.line4.pack(pady=(30, 0))
        
        self.line5 = tk.Label(cutscene_frame, text="", font=sign_font, fg='white', bg='#0a0a2a')
        self.line5.pack(pady=(0, 10))
        
        # 4. Use root.after() to show text sequentially
        self.root.after(1000, lambda: self.line1.config(text="Dear Mario,"))
        self.root.after(2500, lambda: self.line2.config(text="Please come to the castle."))
        self.root.after(4000, lambda: self.line3.config(text="I have baked a cake for you."))
        self.root.after(6000, lambda: self.line4.config(text="Yours truly,"))
        self.root.after(7500, lambda: self.line5.config(text="— Princess Toadstool, Peach"))
        
        # 5. After the cutscene, launch the game
        self.root.after(9500, self.launch_game_after_cutscene)

    def launch_game_after_cutscene(self):
        # This contains the original logic from start_game
        print("Launching 3D Engine...") # Can't update status_label, it's destroyed
        threading.Thread(target=self.launch_ursina, daemon=True).start()
        self.root.after(1000, self.root.destroy)

    def launch_ursina(self):
        try:
            ursina_game = UrsinaGame(self.settings)
            ursina_game.run()
        except ImportError:
            print("FATAL ERROR: 'ursina' module not found. Install Ursina: pip install ursina")
            # In a real app, you might show this error in a tkinter popup
        except Exception as e:
            print(f"Error launching game: {e}")

    def show_files(self):
        try:
            self.files_window = tk.Toplevel(self.root)
            self.files_window.title("File Selection")
            self.files_window.geometry("600x500")
            self.files_window.configure(bg='#0a0a2a')
            self.files_window.resizable(False, False)
            self.root.update_idletasks()
            main_x = self.root.winfo_x()
            main_y = self.root.winfo_y()
            main_w = self.root.winfo_width()
            main_h = self.root.winfo_height()
            files_w = 600
            files_h = 500
            files_x = main_x + (main_w // 2) - (files_w // 2)
            files_y = main_y + (main_h // 2) - (files_h // 2)
            self.files_window.geometry(f'{files_w}x{files_h}+{files_x}+{files_y}')
            self.files_window.grab_set()
            self.files_window.transient(self.root)
            files_frame = tk.Frame(self.files_window, bg='#0a0a2a')
            files_frame.pack(expand=True, fill='both', padx=20, pady=20)
            files_title = tk.Label(files_frame, text="SELECT A FILE", font=('Arial', 16, 'bold'), fg='white', bg='#0a0a2a')
            files_title.pack(pady=(0, 20))
            file_slots_frame = tk.Frame(files_frame, bg='#0a0a2a')
            file_slots_frame.pack(fill='both', expand=True)
            self.file_slots = []
            for i in range(4):
                slot_frame = tk.Frame(file_slots_frame, bg='#333333', relief='raised', bd=2)
                slot_frame.pack(fill='x', pady=5)
                file_name = ["MARIO", "LUIGI", "TOAD", "PEACH"][i]
                stars = self.settings.get(f"{file_name.lower()}_stars", 0)
                icon_label = tk.Label(slot_frame, text="★" * min(stars, 5), font=('Arial', 14), fg='#FFD700', bg='#333333', width=5)
                icon_label.pack(side='left', padx=10, pady=5)
                name_label = tk.Label(slot_frame, text=file_name, font=('Arial', 14, 'bold'), fg='white', bg='#333333', width=10, anchor='w')
                name_label.pack(side='left', padx=10, pady=5)
                star_label = tk.Label(slot_frame, text=f"{stars} STAR{'S' if stars != 1 else ''}", font=('Arial', 12), fg='#CCCCCC', bg='#333333', anchor='w')
                star_label.pack(side='left', padx=10, pady=5)
                select_button = tk.Button(slot_frame, text="SELECT", command=lambda idx=i: self.select_file(idx), font=('Arial', 12), width=8, bg='#444444', fg='white', relief='raised', bd=2, activebackground='#666666', activeforeground='white')
                select_button.pack(side='right', padx=10, pady=5)
                self.file_slots.append({'frame': slot_frame, 'name': file_name, 'stars': stars})
            instructions = tk.Label(files_frame, text="Select a file to continue your adventure.", font=('Arial', 10), fg='#CCCCCC', bg='#0a0a2a', justify='center')
            instructions.pack(pady=10)
            close_button = tk.Button(files_frame, text="CLOSE", command=self.close_files, font=('Arial', 12, 'bold'), width=15, height=2, bg='#FF0000', fg='white', relief='raised', bd=4, activebackground='#CC0000', activeforeground='white')
            close_button.pack(pady=10, side='bottom')
        except Exception as e:
            self.status_label.config(text=f"Error opening files: {e}")
            print(f"Error opening files: {e}")

    def select_file(self, index):
        selected_file = self.file_slots[index]['name']
        self.settings['save_file'] = selected_file
        self.save_settings()
        self.status_label.config(text=f"Selected {selected_file} file!")
        self.file_label.config(text=f"FILE: {selected_file}")
        self.close_files()

    def close_files(self):
        self.files_window.grab_release()
        self.files_window.destroy()

    def show_options(self):
        try:
            self.options_window = tk.Toplevel(self.root)
            self.options_window.title("Options")
            self.options_window.geometry("400x500")
            self.options_window.configure(bg='#0a0a2a')
            self.options_window.resizable(False, False)
            self.root.update_idletasks()
            main_x = self.root.winfo_x()
            main_y = self.root.winfo_y()
            main_w = self.root.winfo_width()
            main_h = self.root.winfo_height()
            opt_w = 400
            opt_h = 500
            opt_x = main_x + (main_w // 2) - (opt_w // 2)
            opt_y = main_y + (main_h // 2) - (opt_h // 2)
            self.options_window.geometry(f'{opt_w}x{opt_h}+{opt_x}+{opt_y}')
            self.options_window.grab_set()
            self.options_window.transient(self.root)
            options_frame = tk.Frame(self.options_window, bg='#0a0a2a')
            options_frame.pack(expand=True, fill='both', padx=20, pady=20)
            options_title = tk.Label(options_frame, text="OPTIONS", font=('Arial', 16, 'bold'), fg='white', bg='#0a0a2a')
            options_title.pack(pady=(0, 20))
            graphics_frame = tk.Frame(options_frame, bg='#0a0a2a')
            graphics_frame.pack(pady=10, fill='x')
            graphics_label = tk.Label(graphics_frame, text="Graphics Quality:", font=('Arial', 12), fg='white', bg='#0a0a2a', width=15, anchor='w')
            graphics_label.pack(side='left', padx=(20, 10))
            style = ttk.Style()
            style.configure('TCombobox', fieldbackground='#333333', background='#555555', foreground='white', arrowcolor='white')
            style.map('TCombobox', fieldbackground=[('readonly', '#333333')], selectbackground=[('readonly', '#0078d7')], selectforeground=[('readonly', 'white')])
            self.graphics_var = tk.StringVar(value=self.settings.get("graphics_quality", "Medium"))
            graphics_options = ["Low", "Medium", "High", "Ultra"]
            graphics_dropdown = ttk.Combobox(graphics_frame, textvariable=self.graphics_var, values=graphics_options, state='readonly', width=15, font=('Arial', 12))
            graphics_dropdown.pack(side='left', padx=10)
            music_frame = tk.Frame(options_frame, bg='#0a0a2a')
            music_frame.pack(pady=10, fill='x')
            self.music_var = tk.BooleanVar(value=self.settings.get("music_enabled", True))
            music_check = tk.Checkbutton(music_frame, text="Enable Music", variable=self.music_var, font=('Arial', 12), fg='white', bg='#0a0a2a', selectcolor='#333333', activebackground='#0a0a2a', activeforeground='white', onvalue=True, offvalue=False, anchor='w')
            music_check.pack(side='left', padx=(20, 10))
            volume_frame = tk.Frame(options_frame, bg='#0a0a2a')
            volume_frame.pack(pady=10, fill='x', padx=20)
            volume_label = tk.Label(volume_frame, text="Sound Volume:", font=('Arial', 12), fg='white', bg='#0a0a2a', width=15, anchor='w')
            volume_label.pack(side='left', padx=(0, 10))
            self.volume_var = tk.IntVar(value=self.settings.get("sound_volume", 50))
            volume_scale = tk.Scale(volume_frame, from_=0, to=100, orient='horizontal', variable=self.volume_var, bg='#0a0a2a', fg='white', highlightbackground='#0a0a2a', troughcolor='#333333', activebackground='#FF0000')
            volume_scale.pack(side='left', fill='x', expand=True, padx=10)
            beta_frame = tk.Frame(options_frame, bg='#0a0a2a')
            beta_frame.pack(pady=10, fill='x')
            self.beta_var = tk.BooleanVar(value=self.settings.get("beta_mode", True))
            beta_check = tk.Checkbutton(beta_frame, text="Enable Beta Features", variable=self.beta_var, font=('Arial', 12), fg='white', bg='#0a0a2a', selectcolor='#333333', activebackground='#0a0a2a', activeforeground='white', onvalue=True, offvalue=False, anchor='w')
            beta_check.pack(side='left', padx=(20, 10))
            debug_frame = tk.Frame(options_frame, bg='#0a0a2a')
            debug_frame.pack(pady=10, fill='x')
            self.debug_var = tk.BooleanVar(value=self.settings.get("debug_mode", False))
            debug_check = tk.Checkbutton(debug_frame, text="Enable Debug Mode", variable=self.debug_var, font=('Arial', 12), fg='white', bg='#0a0a2a', selectcolor='#333333', activebackground='#0a0a2a', activeforeground='white', onvalue=True, offvalue=False, anchor='w')
            debug_check.pack(side='left', padx=(20, 10))
            reset_frame = tk.Frame(options_frame, bg='#0a0a2a')
            reset_frame.pack(pady=20)
            reset_button = tk.Button(reset_frame, text="Reset to Defaults", command=self.reset_options, font=('Arial', 12), width=15, height=1, bg='#555555', fg='white', relief='raised', bd=4, activebackground='#333333', activeforeground='white')
            reset_button.pack()
            close_button = tk.Button(options_frame, text="Save & Close", command=self.close_options, font=('Arial', 12, 'bold'), width=15, height=2, bg='#FF0000', fg='white', relief='raised', bd=4, activebackground='#CC0000', activeforeground='white')
            close_button.pack(pady=20, side='bottom')
        except Exception as e:
            self.status_label.config(text=f"Error opening options: {e}")
            print(f"Error opening options: {e}")

    def reset_options(self):
        self.graphics_var.set("Medium")
        self.music_var.set(True)
        self.volume_var.set(50)
        self.beta_var.set(True)
        self.debug_var.set(False)
        messagebox.showinfo("Reset", "Options have been reset to defaults.")

    def close_options(self):
        self.settings["graphics_quality"] = self.graphics_var.get()
        self.settings["music_enabled"] = self.music_var.get()
        self.settings["sound_volume"] = self.volume_var.get()
        self.settings["beta_mode"] = self.beta_var.get()
        self.settings["debug_mode"] = self.debug_var.get()
        if self.save_settings():
            self.status_label.config(text=f"Options saved! Graphics: {self.settings['graphics_quality']}")
        else:
            self.status_label.config(text="Error saving options!")
        self.options_window.grab_release()
        self.options_window.destroy()

class UrsinaGame:
    def __init__(self, settings=None):
        self.app = None
        self.settings = settings or {}
        self.beta_mode = self.settings.get("beta_mode", True)
        self.debug_mode = self.settings.get("debug_mode", False)

    def run(self):
        # Only import ursina when the game is launched
        from ursina import (
            Ursina, Entity, time, held_keys, Vec3, Vec2, color, camera, Sky, Text,
            application, destroy, scene, DirectionalLight, AmbientLight, raycast,
            distance, load_model, load_texture, collider, mouse, lerp,
            Sequence, Func, Audio, clamp, Wait, invoke
        )
        
        # --- Game Constants ---
        GRAVITY = 30
        TERMINAL_VELOCITY = -50
        PLAYER_SPEED = 8
        JUMP_HEIGHT = 10
        JUMP_DURATION = 0.3
        
        # --- Enemy Class ---
        class Goomba(Entity):
            def __init__(self, position=(0,0,0)):
                super().__init__(model='cube', color=color.brown, scale=(1, 0.8, 1), position=position, collider='box', texture='white_cube')
                self.direction = 1
                self.speed = 2
                self.patrol_range = 5
                self.start_x = position[0]
                self.health = 1
            
            def update(self):
                self.x += self.direction * self.speed * time.dt
                if abs(self.x - self.start_x) > self.patrol_range:
                    self.direction *= -1
                    self.rotation_y += 180
        
        # --- Player Class ---
        class BetaMario(Entity):
            def __init__(self):
                super().__init__(model='cube', color=color.clear, scale=(1, 2, 1), position=(0, 10, -15), collider='box')
                
                # Player Stats
                self.speed = PLAYER_SPEED
                self.jump_height = JUMP_HEIGHT
                self.jump_duration = JUMP_DURATION
                self.health = 100
                self.coins = 0
                self.red_coins = 0
                self.score = 0
                self.stars = 0
                self.lives = 4
                self.power_up = "normal"
                self.power_up_timer = 0
                
                # Movement State
                self.jumping = False
                self.air_time = 0
                self.grounded = False
                self.velocity_y = 0
                self.can_double_jump = False
                self.is_ground_pounding = False
                
                # Combat & Interaction State
                self.is_punching = False
                self.is_immune = False
                self.last_immune_time = 0
                self.cap_on = True # Placeholder
                
                # Create Model & Camera
                self.create_beta_mario_model()
                self.camera_pivot = Entity(parent=self, y=1)
                camera.parent = self.camera_pivot
                camera.position = (0, 2, -10)
                camera.rotation_x = 10
                camera.rotation_y = 0
                mouse.locked = True
                self.camera_sensitivity = 60
                
                # --- BUG FIX 1: Set 'enabled=False' ---
                # This hitbox will be enabled during the punch move
                self.punch_hitbox = Entity(parent=self, model='cube', color=color.rgba(0,0,0,0), scale=(1, 1, 1.5), position=(0, 0, 0.75), enabled=False)

            def create_beta_mario_model(self):
                # This creates a simple blocky Mario
                self.head = Entity(parent=self, model='sphere', color=color.rgb(255, 200, 150), scale=(0.8 / self.scale.x, 0.8 / self.scale.y, 0.8 / self.scale.z), position=(0, 0.8, 0))
                self.hat = Entity(parent=self.head, model='cube', color=color.red, scale=(1.2, 0.4, 1.2), position=(0, 0.5, 0))
                self.emblem = Entity(parent=self.hat, model='cube', color=color.white, scale=(0.5, 0.1, 0.5), position=(0, 0.2, 0.5))
                self.body_model = Entity(parent=self, model='cube', color=color.red, scale=(0.8 / self.scale.x, 1 / self.scale.y, 0.6 / self.scale.z), position=(0, 0, 0))
                self.overalls = Entity(parent=self.body_model, model='cube', color=color.blue, scale=(1.1, 0.7, 1.1), position=(0, -0.3, 0))
                self.left_arm = Entity(parent=self, model='cube', color=color.rgb(255, 200, 150), scale=(0.3 / self.scale.x, 0.8 / self.scale.y, 0.3 / self.scale.z), position=(-0.6, 0, 0))
                self.right_arm = Entity(parent=self, model='cube', color=color.rgb(255, 200, 150), scale=(0.3 / self.scale.x, 0.8 / self.scale.y, 0.3 / self.scale.z), position=(0.6, 0, 0))
                self.left_leg = Entity(parent=self, model='cube', color=color.blue, scale=(0.35 / self.scale.x, 0.8 / self.scale.y, 0.35 / self.scale.z), position=(-0.25, -0.8, 0))
                self.right_leg = Entity(parent=self, model='cube', color=color.blue, scale=(0.35 / self.scale.x, 0.8 / self.scale.y, 0.35 / self.scale.z), position=(0.25, -0.8, 0))
                self.left_glove = Entity(parent=self.left_arm, model='sphere', color=color.white, scale=(0.4, 0.4, 0.4), position=(0, -0.5, 0))
                self.right_glove = Entity(parent=self.right_arm, model='sphere', color=color.white, scale=(0.4, 0.4, 0.4), position=(0, -0.5, 0))

            def update_movement(self):
                if self.is_ground_pounding:
                    return
                
                # Camera
                self.rotation_y += mouse.velocity[0] * self.camera_sensitivity * time.dt
                self.camera_pivot.rotation_x -= mouse.velocity[1] * self.camera_sensitivity * time.dt
                self.camera_pivot.rotation_x = clamp(self.camera_pivot.rotation_x, -10, 45)
                
                # Movement
                direction = Vec3(0, 0, 0)
                move_speed = self.speed
                if self.power_up == "metal":
                    move_speed *= 0.7
                
                direction += self.forward * (held_keys['w'] or held_keys['up arrow'])
                direction -= self.forward * (held_keys['s'] or held_keys['down arrow'])
                direction += self.right * (held_keys['d'] or held_keys['right arrow'])
                direction -= self.right * (held_keys['a'] or held_keys['left arrow'])
                
                if direction.length() > 0:
                    direction = direction.normalized()
                    # Simple wall collision
                    move_ray = raycast(self.position + Vec3(0, 0.5, 0), direction, distance=0.6, ignore=[self])
                    if not move_ray.hit:
                        self.position += direction * move_speed * time.dt
                    
                    # Simple walk animation
                    self.left_leg.rotation_x = math.sin(pytime.time() * 10) * 30
                    self.right_leg.rotation_x = -math.sin(pytime.time() * 10) * 30
                    self.left_arm.rotation_x = -math.sin(pytime.time() * 10) * 20
                    self.right_arm.rotation_x = math.sin(pytime.time() * 10) * 20
                else:
                    # Idle
                    self.left_leg.rotation_x = 0
                    self.right_leg.rotation_x = 0
                    self.left_arm.rotation_x = 0
                    self.right_arm.rotation_x = 0

            def update_gravity(self):
                current_gravity = GRAVITY
                if self.power_up == "metal":
                    current_gravity *= 2
                elif self.power_up == "wing" and self.jumping:
                    current_gravity *= 0.5
                
                if self.is_ground_pounding:
                    self.velocity_y = -GRAVITY * 2
                
                if not self.grounded:
                    self.velocity_y -= current_gravity * time.dt
                    self.velocity_y = max(self.velocity_y, TERMINAL_VELOCITY)
                    self.y += self.velocity_y * time.dt
                
                # Ground check raycast
                ground_ray = raycast(self.position, Vec3(0, -1, 0), distance=1.1, ignore=[self])
                
                if ground_ray.hit:
                    if self.velocity_y < 0:
                        self.y = ground_ray.world_point.y + 1
                        if self.is_ground_pounding:
                            self.is_ground_pounding = False
                            camera.shake(duration=0.2, magnitude=1)
                        
                        self.velocity_y = 0
                        self.grounded = True
                        self.jumping = False
                        self.can_double_jump = True
                else:
                    self.grounded = False

            def update_powerup_timer(self):
                if self.power_up_timer > 0:
                    self.power_up_timer -= time.dt
                elif self.power_up != "normal":
                    self.power_up = "normal"
                    self.power_up_timer = 0
                    self.body_model.color = color.red
                    self.overalls.color = color.blue

            def take_damage(self, amount):
                if self.is_immune or self.power_up == "metal":
                    return
                
                self.health -= amount
                self.is_immune = True
                self.last_immune_time = pytime.time()
                self.body_model.blink(color.white, duration=0.5)
                
                if self.health <= 0:
                    self.die()

            def die(self):
                self.lives -= 1
                self.health = 100
                self.position = (0, 10, -15) # Respawn
                self.velocity_y = 0
                if self.lives <= 0:
                    print("GAME OVER")
                    application.quit()

            def update(self):
                if pytime.time() - self.last_immune_time > 1.5:
                    self.is_immune = False
                
                self.update_movement()
                self.update_gravity()
                self.update_powerup_timer()

            def jump(self):
                if self.grounded and not self.is_ground_pounding:
                    if self.power_up == "metal":
                        return # Too heavy
                    self.velocity_y = JUMP_HEIGHT
                    self.grounded = False
                    self.jumping = True
                    self.can_double_jump = True
                
                elif not self.grounded and self.can_double_jump and not self.is_ground_pounding:
                    self.velocity_y = JUMP_HEIGHT * 0.8 # Double jump
                    self.jumping = True
                    self.can_double_jump = False
                    if self.power_up == "wing":
                        self.velocity_y = JUMP_HEIGHT * 1.2 # Triple/Wing jump

            def ground_pound(self):
                if not self.grounded:
                    self.velocity_y = 5 # Small hop before slamming
                    self.is_ground_pounding = True
                    self.can_double_jump = False

            def punch(self):
                if self.is_punching:
                    return
                
                self.is_punching = True
                # --- BUG FIX 2: Use 'enabled' ---
                self.punch_hitbox.enabled = True
                self.punch_hitbox.world_position = self.world_position + self.forward * 1 + self.up * 0.5
                
                # Animate arm
                self.right_arm.animate_rotation_z(90, duration=0.1)
                self.right_arm.animate_rotation_z(0, duration=0.2, delay=0.1)
                
                def finish_punch():
                    self.is_punching = False
                    # --- BUG FIX 3: Use 'enabled' ---
                    self.punch_hitbox.enabled = False
                
                # Reset punch state after 0.3 seconds
                invoke(finish_punch, delay=0.3)

            def input(self, key):
                if key == 'escape':
                    mouse.locked = False
                    application.quit()
                if key == 'r':
                    self.die()
                if key == 'space':
                    self.jump()
                if key == 'left control' or key == 'c':
                    self.ground_pound()
                if key == 'f':
                    self.punch()
                
                # Debug keys
                if self.debug_mode:
                    if key == '1':
                        self.set_powerup("normal")
                    if key == '2':
                        self.set_powerup("metal")
                    if key == '3':
                        self.set_powerup("wing")
                    if key == '4':
                        self.set_powerup("vanish")
                    if key == 'l':
                        self.lives += 1
                    if key == 'k':
                        self.take_damage(20)

            def set_powerup(self, power_up_type):
                self.power_up = power_up_type
                self.power_up_timer = 20
                if self.power_up == "metal":
                    self.body_model.color = color.gray
                    self.overalls.color = color.dark_gray
                elif self.power_up == "wing":
                    # Add wing model logic here
                    pass
                elif self.power_up == "vanish":
                    self.body_model.color = color.rgba(200, 200, 255, 128)
                    self.overalls.color = color.rgba(100, 100, 255, 128)
                else: # normal
                    self.body_model.color = color.red
                    self.overalls.color = color.blue
        
        # --- HUD Class ---
        class BetaHUD:
            def __init__(self, player):
                self.player = player
                self.start_time = pytime.time()
                
                self.lives_bg = Entity(parent=camera.ui, model='quad', color=color.rgba(0,0,0,128), scale=(0.2, 0.05), position=Vec2(-0.8, 0.45))
                self.lives_text = Text(parent=camera.ui, text=f"MARIO x{self.player.lives}", position=Vec2(-0.88, 0.46), scale=1.5)
                
                self.health_bar_bg = Entity(parent=camera.ui, model='quad', color=color.rgba(0,0,0,128), scale=(0.2, 0.04), position=Vec2(-0.8, 0.4))
                self.health_bar = Entity(parent=camera.ui, model='quad', color=color.red, scale=(0.19, 0.03), position=Vec2(-0.8, 0.4))
                
                self.coin_bg = Entity(parent=camera.ui, model='quad', color=color.rgba(0,0,0,128), scale=(0.2, 0.05), position=Vec2(0.8, 0.45))
                self.coin_icon = Text(parent=camera.ui, text="¢", color=color.yellow, scale=1.5, position=Vec2(0.72, 0.46))
                self.coin_text = Text(parent=camera.ui, text=f"×{self.player.coins:02d}", color=color.yellow, scale=1.5, position=Vec2(0.75, 0.46))
                
                self.star_bg = Entity(parent=camera.ui, model='quad', color=color.rgba(0,0,0,128), scale=(0.2, 0.05), position=Vec2(0.8, 0.4))
                self.star_icon = Text(parent=camera.ui, text="★", color=color.yellow, scale=1.5, position=Vec2(0.72, 0.41))
                self.star_text = Text(parent=camera.ui, text=f"×{self.player.stars}", color=color.white, scale=1.5, position=Vec2(0.75, 0.41))
                
                self.red_coin_bg = Entity(parent=camera.ui, model='quad', color=color.rgba(0,0,0,128), scale=(0.2, 0.05), position=Vec2(0.8, 0.35))
                self.red_coin_icon = Text(parent=camera.ui, text="★", color=color.red, scale=1.5, position=Vec2(0.72, 0.36))
                self.red_coin_text = Text(parent=camera.ui, text=f"{self.player.red_coins}/8", color=color.white, scale=1.5, position=Vec2(0.75, 0.36))
                
                self.timer_bg = Entity(parent=camera.ui, model='quad', color=color.rgba(0,0,0,128), scale=(0.2, 0.05), position=Vec2(0.8, 0.3))
                self.timer_text = Text(parent=camera.ui, text="00:00", color=color.white, scale=1.5, position=Vec2(0.75, 0.31))
                
                self.power_bg = Entity(parent=camera.ui, model='quad', color=color.rgba(0,0,0,128), scale=(0.3, 0.05), position=Vec2(0.7, -0.45))
                self.power_text = Text(parent=camera.ui, text="POWER: NORMAL", scale=1.2, position=Vec2(0.6, -0.44))
                
                self.instructions = Text(text='WASD: Move | MOUSE: Look | SPACE: Jump | L-CTRL: Ground Pound | F: Punch', origin=(0, 0), position=(0, -0.45), scale=1)
                
                # Level Title Popup
                self.level_title = Text(text="BETA COURTYARD", origin=(0,0), position=(0,0.1), scale=3, color=color.white)
                self.level_title_bg = Entity(parent=camera.ui, model='quad', color=color.rgba(0,0,0,0.5), scale=(0.5, 0.1), position=(0, 0.1), z=1)
                self.level_title.enabled = True
                self.level_title_bg.enabled = True
                self.level_title.fade_out(duration=1, delay=3)
                self.level_title_bg.fade_out(duration=1, delay=3)
                
                if self.debug_mode:
                    self.debug_text = Text(text='DEBUG MODE', origin=(.5, .5), position=(0.5, -0.45), scale=1.5, color=color.red)

            def update(self):
                self.lives_text.text = f"MARIO x{self.player.lives}"
                self.coin_text.text = f"×{self.player.coins:02d}"
                self.star_text.text = f"×{self.player.stars}"
                self.red_coin_text.text = f"{self.player.red_coins}/8"
                
                power_str = f"POWER: {self.player.power_up.upper()}"
                if self.player.power_up_timer > 0:
                    power_str += f" ({int(self.player.power_up_timer)})"
                self.power_text.text = power_str
                
                elapsed = pytime.time() - self.start_time
                mins = int(elapsed // 60)
                secs = int(elapsed % 60)
                self.timer_text.text = f"{mins:02d}:{secs:02d}"
                
                health_percentage = self.player.health / 100
                self.health_bar.scale_x = 0.19 * health_percentage
                # This logic keeps the bar left-aligned
                self.health_bar.x = -0.8 - (0.19 * (1 - health_percentage) / 2)
                
                if self.player.health > 60: self.health_bar.color = color.green
                elif self.player.health > 30: self.health_bar.color = color.yellow
                else: self.health_bar.color = color.red
        
        # --- World Class ---
        class BetaWorld:
            def __init__(self, custom_level_path=None):
                self.custom_level_path = custom_level_path
                self.boos = []
                self.goombas = []
                self.coins = []
                self.red_coins = []
                self.power_ups = []
                self.exclamation_blocks = []
                self.moving_platforms = []
                self.spinning_platforms = []
                self.beta_star = None
                
                # Build level
                self.create_environment()
                self.coins.extend(self.create_coins())
                self.red_coins.extend(self.create_red_coins())
                self.goombas.extend(self.create_enemies())
                self.power_ups.extend(self.create_power_ups())
                self.exclamation_blocks.extend(self.create_exclamation_blocks())
                self.moving_platforms.extend(self.create_moving_platforms())
                self.spinning_platforms.extend(self.create_spinning_platforms())
                self.create_beta_portal()

            def create_environment(self):
                # Ground and Sky
                Entity(model='plane', texture='grass', texture_scale=(20,20), scale=(100, 1, 100), position=(0, 0, 0), collider='box')
                Sky()
                
                if self.custom_level_path and os.path.exists(self.custom_level_path):
                    try:
                        with open(self.custom_level_path, 'r') as f:
                            level_data = json.load(f)
                            self.load_custom_level(level_data)
                    except Exception as e:
                        print(f"Error loading custom level: {e}")
                        self.create_beta_level() # Fallback
                else:
                    self.create_beta_level()

            def create_beta_level(self):
                # Central Castle Wall
                Entity(model='cube', color=color.light_gray, scale=(20, 15, 2), position=(0, 7.5, 20), collider='box', texture='brick')
                Entity(model='cube', color=color.dark_gray, scale=(4, 6, 2.1), position=(0, 3, 19), collider='box', texture='brick') # Doorway
                
                # Fountain
                Entity(model='cube', color=color.blue, scale=(6, 0.2, 6), position=(0, 0.5, 10)) # Water
                fountain_walls = [
                    Entity(model='cube', color=color.gray, scale=(7, 1.5, 1), position=(0, 0.75, 13.5), collider='box'),
                    Entity(model='cube', color=color.gray, scale=(7, 1.5, 1), position=(0, 0.75, 6.5), collider='box'),
                    Entity(model='cube', color=color.gray, scale=(1, 1.5, 7), position=(3.5, 0.75, 10), collider='box'),
                    Entity(model='cube', color=color.gray, scale=(1, 1.5, 7), position=(-3.5, 0.75, 10), collider='box'),
                ]
                Entity(model='cylinder', color=color.gray, scale=(1, 3, 1), position=(0, 2, 10), collider='cylinder') # Spout
                
                # Boundary Walls
                Entity(model='cube', color=color.gray, scale=(1, 6, 50), position=(25, 3, 0), collider='box', texture='brick', texture_scale=(10,2))
                Entity(model='cube', color=color.gray, scale=(1, 6, 50), position=(-25, 3, 0), collider='box', texture='brick', texture_scale=(10,2))
                Entity(model='cube', color=color.gray, scale=(50, 6, 1), position=(0, 3, -25), collider='box', texture='brick', texture_scale=(10,2))
                
                # Trees
                tree_positions = [(8, 0, 5), (-8, 0, 5), (15, 0, -10)]
                for pos in tree_positions:
                    Entity(model='cylinder', color=color.brown, scale=(0.5, 3, 0.5), position=(pos[0], 1.5, pos[2]), collider='cylinder')
                    Entity(model='sphere', color=color.dark_green, scale=(3, 2, 3), position=(pos[0], 4, pos[2]), collider='sphere')
                
                # Boos
                boo_positions = [(5, 3, 8), (-5, 3, 12), (0, 3, 15)]
                for pos in boo_positions:
                    boo = Entity(model='sphere', color=color.rgba(255, 255, 255, 200), scale=(1.5, 1.5, 1.5), position=pos, collider='sphere')
                    boo.original_color = boo.color
                    boo.is_hiding = False
                    boo.start_y = pos[1]
                    self.boos.append(boo)

            def load_custom_level(self, level_data):
                if 'platforms' in level_data:
                    for platform in level_data['platforms']:
                        Entity(model=platform.get('model', 'cube'), color=color.rgba(*platform.get('color', [255, 165, 0, 255])), scale=platform.get('scale', [3, 0.5, 3]), position=platform.get('position', [0, 2, 0]), collider='box')

            def create_coins(self):
                coins_list = []
                # Line of coins
                for i in range(5):
                    coins_list.append(Entity(model='cylinder', color=color.gold, scale=(0.5, 0.1, 0.5), position=(-10 + i*1.5, 1, 5), collider='sphere'))
                # Ring of coins around fountain
                for i in range(8):
                    angle = (i / 8) * 2 * math.pi
                    x = math.sin(angle) * 3
                    z = math.cos(angle) * 3
                    coins_list.append(Entity(model='cylinder', color=color.gold, scale=(0.5, 0.1, 0.5), position=(x, 5, z + 10), collider='sphere'))
                return coins_list

            def create_red_coins(self):
                red_coin_positions = [(0, 4, 10), (15, 3, -10), (-8, 6, 5), (20, 1, 15), (-20, 1, -15), (0, 1, -20), (10, 8, 10), (-10, 12, -10)]
                rc_list = []
                for pos in red_coin_positions:
                    rc_list.append(Entity(model='cylinder', color=color.red, scale=(0.5, 0.1, 0.5), position=pos, collider='sphere'))
                return rc_list

            def spawn_beta_star(self):
                if self.beta_star: # Don't spawn if it already exists
                    return
                # Spawns on top of the fountain
                self.beta_star = Entity(model='sphere', color=color.yellow, scale=1.5, position=(0, 6, 10), collider='sphere', texture='white_cube')
                self.beta_star.animate_rotation((0, 360, 0), duration=2, loop=True)

            def create_enemies(self):
                enemies_list = []
                enemies_list.append(Goomba(position=(-10, 0.4, 0)))
                enemies_list.append(Goomba(position=(10, 0.4, 0)))
                enemies_list.append(Goomba(position=(0, 0.4, -10)))
                return enemies_list

            def create_power_ups(self):
                power_ups_list = []
                metal_cap = Entity(model='cube', color=color.gray, scale=(0.5, 0.5, 0.5), position=(20, 5, 20), collider='box', texture='white_cube')
                metal_cap.power_type = "metal"
                power_ups_list.append(metal_cap)
                
                wing_cap = Entity(model='cube', color=color.rgba(255, 255, 0, 255), scale=(0.5, 0.5, 0.5), position=(-20, 8, 10), collider='box', texture='white_cube')
                wing_cap.power_type = "wing"
                power_ups_list.append(wing_cap)
                return power_ups_list

            def create_exclamation_blocks(self):
                blocks = []
                block_pos = [(0, 3, 0), (5, 3, 5), (-5, 3, -5)]
                for pos in block_pos:
                    block = Entity(model='cube', color=color.yellow, scale=1, position=pos, collider='box', texture='white_cube') # Add ! texture later
                    block.hit = False
                    blocks.append(block)
                return blocks

            def create_moving_platforms(self):
                platforms = []
                pf = Entity(model='cube', color=color.blue, scale=(4, 0.5, 2), position=(10, 7, 10), collider='box')
                pf.start_pos = pf.position
                pf.direction = 1
                platforms.append(pf)
                return platforms

            def create_spinning_platforms(self):
                platforms = []
                pf = Entity(model='cylinder', color=color.green, scale=(3, 0.5, 3), position=(-10, 11, -10), collider='box')
                platforms.append(pf)
                return platforms

            def create_beta_portal(self):
                # Just a visual prop for now
                portal_frame = Entity(model='cube', color=color.gray, scale=(0.5, 5, 3), position=(-24.5, 2.5, 10), collider='box')
                portal_frame2 = Entity(model='cube', color=color.gray, scale=(0.5, 5, 3), position=(-24.5, 2.5, 13), collider='box')
                portal_frame3 = Entity(model='cube', color=color.gray, scale=(0.5, 0.5, 3), position=(-24.5, 5, 11.5), collider='box')
                portal_surface = Entity(model='quad', color=color.rgba(100, 0, 200, 150), scale=(2.9, 4.9), position=(-24.4, 2.5, 11.5))
                portal_surface.texture = 'noise'

            def update_platforms(self):
                for pf in self.moving_platforms:
                    pf.x += pf.direction * 2 * time.dt
                    if abs(pf.x - pf.start_pos.x) > 5:
                        pf.direction *= -1
                for pf in self.spinning_platforms:
                    pf.rotation_y += 30 * time.dt

            def update(self, player):
                self.update_platforms()
                
                # Boo logic
                for boo in self.boos:
                    boo.look_at(player, 'forward')
                    player_direction = player.forward
                    boo_direction = (boo.position - player.position).normalized()
                    dot_product = player_direction.dot(boo_direction)
                    
                    # If player is looking at boo
                    if dot_product > 0.3 and distance(player, boo) < 15:
                        if not boo.is_hiding:
                            boo.is_hiding = True
                            boo.animate_color(color.rgba(255,255,255,50), duration=0.2)
                            boo.collider = None # Can't touch
                    else: # Player is not looking
                        if boo.is_hiding:
                            boo.is_hiding = False
                            boo.animate_color(boo.original_color, duration=0.2)
                            boo.collider = 'sphere'
                        # Chase player
                        if distance(player, boo) < 15 and distance(player, boo) > 3:
                            boo.position = lerp(boo.position, player.position, time.dt * 0.5)
                    
                    # Bob up and down
                    boo.y = boo.start_y + math.sin(pytime.time() * 2 + boo.x) * 0.2
                
                # Update all Goombas
                for goomba in self.goombas:
                    goomba.update()

        # --- Game Setup and Main Loop ---
        app = Ursina(title="Ultra Mario 3D Bros - Beta Build", development_mode=False)
        
        graphics_quality = self.settings.get("graphics_quality", "Medium")
        if graphics_quality == "Low":
            application.render_mode = 'wireframe' # Simple way to reduce load
        
        player = BetaMario()
        world = BetaWorld(self.settings.get("custom_level_path", None))
        ui = BetaHUD(player)
        
        # Lighting
        DirectionalLight(parent=scene, y=10, z=5, shadows=True, rotation=(30, 30, 0))
        AmbientLight(color=color.rgba(100, 100, 100, 255))
        
        # --- Main Game Update Function ---
        def update():
            player.update()
            world.update(player)
            ui.update()
            
            # --- Collision Checks ---
            
            # Use [:] to create a copy, allowing us to remove items while iterating
            for coin in world.coins[:]:
                if player.intersects(coin).hit:
                    player.coins += 1
                    player.score += 100
                    world.coins.remove(coin)
                    destroy(coin)
            
            for coin in world.red_coins[:]:
                if player.intersects(coin).hit:
                    player.coins += 2
                    player.red_coins += 1
                    player.score += 200
                    world.red_coins.remove(coin)
                    destroy(coin)
                    if player.red_coins == 8:
                        world.spawn_beta_star()
            
            if world.beta_star and player.intersects(world.beta_star).hit:
                player.stars += 1
                player.score += 1000
                destroy(world.beta_star)
                world.beta_star = None
            
            for power_up in world.power_ups[:]:
                if player.intersects(power_up).hit:
                    player.set_powerup(power_up.power_type)
                    world.power_ups.remove(power_up)
                    destroy(power_up)
            
            for enemy in world.goombas[:]:
                if player.intersects(enemy).hit:
                    # Stomp
                    if player.is_ground_pounding or player.velocity_y < -0.1:
                        destroy(enemy)
                        world.goombas.remove(enemy)
                        player.score += 200
                        player.velocity_y = JUMP_HEIGHT * 0.5 # Bounce
                    else: # Took damage
                        player.take_damage(10)
            
            for enemy in world.boos[:]:
                if player.intersects(enemy).hit:
                    if player.is_ground_pounding:
                        destroy(enemy)
                        world.boos.remove(enemy)
                        player.score += 200
                        player.velocity_y = JUMP_HEIGHT * 0.5 # Bounce
                    else: # Took damage
                        player.take_damage(10)
            
            # Punch collision
            if player.is_punching:
                for block in world.exclamation_blocks:
                    if player.punch_hitbox.intersects(block).hit and not block.hit:
                        block.hit = True
                        block.color = color.gray
                        block.texture = None
                        # Block "bump" animation
                        s = Sequence(Func(setattr, block, 'y', block.y + 0.3), Wait(0.1), Func(setattr, block, 'y', block.y - 0.3))
                        s.start()
                        # Spawn a coin
                        world.coins.append(Entity(model='cylinder', color=color.gold, scale=(0.5, 0.1, 0.5), position=block.position + Vec3(0,1,0), collider='sphere'))

        # Pass input to player
        def input(key):
            player.input(key)
        
        # Start the game
        app.run()

# --- Main Entry Point ---
def main():
    # Allow skipping the launcher for quick testing
    if len(sys.argv) > 1 and sys.argv[1] == '--direct':
        game = UrsinaGame()
        game.run()
    else:
        root = tk.Tk()
        app = UltraMarioLauncher(root)
        root.mainloop()

if __name__ == "__main__":
    main()
