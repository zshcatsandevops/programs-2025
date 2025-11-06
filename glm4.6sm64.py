#!/usr/bin/env python3
"""
Ultra Mario 3D Bros — Beta Build
Based on Super Mario 64 Beta Elements
Tkinter main menu + Ursina 3D engine
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import sys
import os
import json
import threading
import math
import random
import time as pytime

# ------------------------------
# Tkinter Main Menu
# ------------------------------
class UltraMarioLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Ultra Mario 3D Bros - Beta Build")
        self.root.geometry("800x600")
        self.root.configure(bg='#0a0a2a')
        
        # Make window not resizable
        self.root.resizable(False, False)
        
        # Center the window
        self.center_window()
        
        # Game settings
        self.settings = {
            "graphics_quality": "Medium",
            "music_enabled": True,
            "sound_volume": 50,
            "custom_level_path": "",
            "beta_mode": True,
            "debug_mode": False
        }
        
        # Load settings if available
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
                    self.settings = json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")

    def save_settings(self):
        try:
            with open("ultra_mario_settings.json", "w") as f:
                json.dump(self.settings, f)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False

    def create_menu(self):
        # Main frame
        main_frame = tk.Frame(self.root, bg='#0a0a2a')
        main_frame.pack(expand=True, fill='both')
        
        # Title with beta indicator
        title_label = tk.Label(
            main_frame,
            text="ULTRA MARIO 3D BROS",
            font=('Arial', 32, 'bold'),
            fg='#FFD700',
            bg='#0a0a2a'
        )
        title_label.pack(pady=(60, 5))
        
        beta_label = tk.Label(
            main_frame,
            text="BETA DEMO",
            font=('Arial', 18, 'bold'),
            fg='#FF6600',
            bg='#0a0a2a'
        )
        beta_label.pack(pady=(0, 20))
        
        # File select (like in SM64 beta)
        file_frame = tk.Frame(main_frame, bg='#0a0a2a')
        file_frame.pack(pady=10)
        
        file_label = tk.Label(
            file_frame,
            text=f"FILE: {self.settings.get('save_file', 'MARIO')}",
            font=('Arial', 14),
            fg='#FFFFFF',
            bg='#0a0a2a'
        )
        file_label.pack(side='left', padx=10)
        
        file_button = tk.Button(
            file_frame,
            text="CHANGE",
            command=self.change_file,
            font=('Arial', 12),
            width=8,
            bg='#444444',
            fg='white',
            relief='raised',
            bd=2,
            activebackground='#666666',
            activeforeground='white'
        )
        file_button.pack(side='left')
        
        # Menu buttons with SM64 beta style
        button_style = {
            'font': ('Arial', 16, 'bold'),
            'width': 20,
            'height': 2,
            'bg': '#FF0000',
            'fg': 'white',
            'relief': 'raised',
            'bd': 4,
            'activebackground': '#CC0000',
            'activeforeground': 'white'
        }
        
        self.start_button = tk.Button(
            main_frame,
            text="PLAY GAME",
            command=self.start_game,
            **button_style
        )
        self.start_button.pack(pady=10)
        
        self.files_button = tk.Button(
            main_frame,
            text="FILES",
            command=self.show_files,
            **button_style
        )
        self.files_button.pack(pady=10)
        
        self.copy_button = tk.Button(
            main_frame,
            text="COPY",
            command=self.copy_file,
            **button_style
        )
        self.copy_button.pack(pady=10)
        
        self.erase_button = tk.Button(
            main_frame,
            text="ERASE",
            command=self.erase_file,
            **button_style
        )
        self.erase_button.pack(pady=10)
        
        self.options_button = tk.Button(
            main_frame,
            text="OPTIONS",
            command=self.show_options,
            **button_style
        )
        self.options_button.pack(pady=10)
        
        # Score display (beta feature)
        score_frame = tk.Frame(main_frame, bg='#0a0a2a')
        score_frame.pack(pady=10)
        
        score_label = tk.Label(
            score_frame,
            text="HIGH SCORE",
            font=('Arial', 12),
            fg='#FFFFFF',
            bg='#0a0a2a'
        )
        score_label.pack(side='left', padx=10)
        
        score_value = tk.Label(
            score_frame,
            text=f"{self.settings.get('high_score', '0000')}",
            font=('Arial', 12, 'bold'),
            fg='#FFD700',
            bg='#0a0a2a'
        )
        score_value.pack(side='left')
        
        # Status bar
        status_frame = tk.Frame(main_frame, bg='#0a0a2a')
        status_frame.pack(side='bottom', fill='x', pady=20)
        
        self.status_label = tk.Label(
            status_frame,
            text="Press START to begin your adventure!",
            font=('Arial', 10),
            fg='#00FF00',
            bg='#0a0a2a'
        )
        self.status_label.pack()

    def change_file(self):
        # Simple file name change dialog
        files = ["MARIO", "LUIGI", "TOAD", "PEACH"]
        current = self.settings.get('save_file', 'MARIO')
        current_index = files.index(current) if current in files else 0
        new_index = (current_index + 1) % len(files)
        self.settings['save_file'] = files[new_index]
        self.save_settings()
        self.create_menu()  # Refresh menu

    def copy_file(self):
        self.status_label.config(text=f"Copying {self.settings.get('save_file', 'MARIO')} file...")
        self.root.update()
        # Simulate copying
        self.root.after(1000, lambda: self.status_label.config(text="File copied successfully!"))

    def erase_file(self):
        result = messagebox.askyesno("Erase File", f"Are you sure you want to erase {self.settings.get('save_file', 'MARIO')} file?")
        if result:
            self.status_label.config(text=f"Erasing {self.settings.get('save_file', 'MARIO')} file...")
            self.root.update()
            # Simulate erasing
            self.root.after(1000, lambda: self.status_label.config(text="File erased successfully!"))

    def start_game(self):
        self.status_label.config(text="Launching 3D Engine...")
        self.root.update()
        
        # Launch Ursina game in a separate thread
        threading.Thread(target=self.launch_ursina, daemon=True).start()
        
        # Close Tkinter window after a short delay
        self.root.after(1000, self.root.destroy)

    def launch_ursina(self):
        try:
            # Import and run the Ursina game
            ursina_game = UrsinaGame(self.settings)
            ursina_game.run()
        except ImportError:
            print("--------------------------------------------------")
            print("FATAL ERROR: 'ursina' module not found.")
            print("Please install Ursina to play this game:")
            print("  pip install ursina")
            print("--------------------------------------------------")
        except Exception as e:
            print(f"Error launching game: {e}")

    def show_files(self):
        # Create a new Toplevel window for file selection
        try:
            self.files_window = tk.Toplevel(self.root)
            self.files_window.title("File Selection")
            self.files_window.geometry("600x500")
            self.files_window.configure(bg='#0a0a2a')
            self.files_window.resizable(False, False)

            # Center the files window relative to the main window
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

            # Make the files window modal (grabs focus)
            self.files_window.grab_set()
            self.files_window.transient(self.root)

            files_frame = tk.Frame(self.files_window, bg='#0a0a2a')
            files_frame.pack(expand=True, fill='both', padx=20, pady=20)

            # Title
            files_title = tk.Label(
                files_frame,
                text="SELECT A FILE",
                font=('Arial', 16, 'bold'),
                fg='white',
                bg='#0a0a2a'
            )
            files_title.pack(pady=(0, 20))
            
            # File slots (like in SM64)
            file_slots_frame = tk.Frame(files_frame, bg='#0a0a2a')
            file_slots_frame.pack(fill='both', expand=True)
            
            self.file_slots = []
            for i in range(4):
                slot_frame = tk.Frame(file_slots_frame, bg='#333333', relief='raised', bd=2)
                slot_frame.pack(fill='x', pady=5)
                
                file_name = ["MARIO", "LUIGI", "TOAD", "PEACH"][i]
                stars = self.settings.get(f"{file_name.lower()}_stars", 0)
                
                # File icon
                icon_label = tk.Label(
                    slot_frame,
                    text="★" * min(stars, 5),
                    font=('Arial', 14),
                    fg='#FFD700',
                    bg='#333333',
                    width=5
                )
                icon_label.pack(side='left', padx=10, pady=5)
                
                # File name
                name_label = tk.Label(
                    slot_frame,
                    text=file_name,
                    font=('Arial', 14, 'bold'),
                    fg='white',
                    bg='#333333',
                    width=10,
                    anchor='w'
                )
                name_label.pack(side='left', padx=10, pady=5)
                
                # Star count
                star_label = tk.Label(
                    slot_frame,
                    text=f"{stars} STAR{'S' if stars != 1 else ''}",
                    font=('Arial', 12),
                    fg='#CCCCCC',
                    bg='#333333',
                    anchor='w'
                )
                star_label.pack(side='left', padx=10, pady=5)
                
                # Select button
                select_button = tk.Button(
                    slot_frame,
                    text="SELECT",
                    command=lambda idx=i: self.select_file(idx),
                    font=('Arial', 12),
                    width=8,
                    bg='#444444',
                    fg='white',
                    relief='raised',
                    bd=2,
                    activebackground='#666666',
                    activeforeground='white'
                )
                select_button.pack(side='right', padx=10, pady=5)
                
                self.file_slots.append({
                    'frame': slot_frame,
                    'name': file_name,
                    'stars': stars
                })
            
            # Instructions
            instructions = tk.Label(
                files_frame,
                text="Select a file to continue your adventure.",
                font=('Arial', 10),
                fg='#CCCCCC',
                bg='#0a0a2a',
                justify='center'
            )
            instructions.pack(pady=10)
            
            # Close Button
            close_button = tk.Button(
                files_frame,
                text="CLOSE",
                command=self.close_files,
                font=('Arial', 12, 'bold'),
                width=15,
                height=2,
                bg='#FF0000',
                fg='white',
                relief='raised',
                bd=4,
                activebackground='#CC0000',
                activeforeground='white'
            )
            close_button.pack(pady=10, side='bottom')
        
        except Exception as e:
            self.status_label.config(text=f"Error opening files: {e}")
            print(f"Error opening files: {e}")

    def select_file(self, index):
        selected_file = self.file_slots[index]['name']
        self.settings['save_file'] = selected_file
        self.save_settings()
        self.status_label.config(text=f"Selected {selected_file} file!")
        self.close_files()
        self.create_menu()  # Refresh main menu

    def close_files(self):
        # Release grab and destroy the window
        self.files_window.grab_release()
        self.files_window.destroy()

    def show_options(self):
        # Create a new Toplevel window for options
        try:
            self.options_window = tk.Toplevel(self.root)
            self.options_window.title("Options")
            self.options_window.geometry("400x500")
            self.options_window.configure(bg='#0a0a2a')
            self.options_window.resizable(False, False)

            # Center the options window relative to the main window
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

            # Make the options window modal (grabs focus)
            self.options_window.grab_set()
            self.options_window.transient(self.root)

            options_frame = tk.Frame(self.options_window, bg='#0a0a2a')
            options_frame.pack(expand=True, fill='both', padx=20, pady=20)

            # Title
            options_title = tk.Label(
                options_frame,
                text="OPTIONS",
                font=('Arial', 16, 'bold'),
                fg='white',
                bg='#0a0a2a'
            )
            options_title.pack(pady=(0, 20))

            # --- Graphics Quality ---
            graphics_frame = tk.Frame(options_frame, bg='#0a0a2a')
            graphics_frame.pack(pady=10, fill='x')

            graphics_label = tk.Label(
                graphics_frame,
                text="Graphics Quality:",
                font=('Arial', 12),
                fg='white',
                bg='#0a0a2a',
                width=15,
                anchor='w'
            )
            graphics_label.pack(side='left', padx=(20, 10))

            # We need a style for the Combobox
            style = ttk.Style()
            
            # Configure TCombobox style
            style.configure('TCombobox', 
                            fieldbackground='#333333', 
                            background='#555555', 
                            foreground='white',
                            arrowcolor='white')
            style.map('TCombobox',
                      fieldbackground=[('readonly', '#333333')],
                      selectbackground=[('readonly', '#0078d7')],
                      selectforeground=[('readonly', 'white')])

            self.graphics_var = tk.StringVar(value=self.settings.get("graphics_quality", "Medium"))
            graphics_options = ["Low", "Medium", "High", "Ultra"]
            graphics_dropdown = ttk.Combobox(
                graphics_frame,
                textvariable=self.graphics_var,
                values=graphics_options,
                state='readonly',
                width=15,
                font=('Arial', 12)
            )
            graphics_dropdown.pack(side='left', padx=10)

            # --- Enable Music ---
            music_frame = tk.Frame(options_frame, bg='#0a0a2a')
            music_frame.pack(pady=10, fill='x')

            self.music_var = tk.BooleanVar(value=self.settings.get("music_enabled", True))
            music_check = tk.Checkbutton(
                music_frame,
                text="Enable Music",
                variable=self.music_var,
                font=('Arial', 12),
                fg='white',
                bg='#0a0a2a',
                selectcolor='#333333',
                activebackground='#0a0a2a',
                activeforeground='white',
                onvalue=True,
                offvalue=False,
                anchor='w'
            )
            music_check.pack(side='left', padx=(20, 10))

            # --- Sound Volume ---
            volume_frame = tk.Frame(options_frame, bg='#0a0a2a')
            volume_frame.pack(pady=10, fill='x', padx=20)

            volume_label = tk.Label(
                volume_frame,
                text="Sound Volume:",
                font=('Arial', 12),
                fg='white',
                bg='#0a0a2a',
                width=15,
                anchor='w'
            )
            volume_label.pack(side='left', padx=(20, 10))

            self.volume_var = tk.IntVar(value=self.settings.get("sound_volume", 50))
            volume_scale = tk.Scale(
                volume_frame,
                from_=0,
                to=100,
                orient='horizontal',
                variable=self.volume_var,
                bg='#0a0a2a',
                fg='white',
                highlightbackground='#0a0a2a',
                troughcolor='#333333',
                activebackground='#FF0000'
            )
            volume_scale.pack(side='left', fill='x', expand=True, padx=10)

            # --- Beta Mode ---
            beta_frame = tk.Frame(options_frame, bg='#0a0a2a')
            beta_frame.pack(pady=10, fill='x')

            self.beta_var = tk.BooleanVar(value=self.settings.get("beta_mode", True))
            beta_check = tk.Checkbutton(
                beta_frame,
                text="Enable Beta Features",
                variable=self.beta_var,
                font=('Arial', 12),
                fg='white',
                bg='#0a0a2a',
                selectcolor='#333333',
                activebackground='#0a0a2a',
                activeforeground='white',
                onvalue=True,
                offvalue=False,
                anchor='w'
            )
            beta_check.pack(side='left', padx=(20, 10))

            # --- Debug Mode ---
            debug_frame = tk.Frame(options_frame, bg='#0a0a2a')
            debug_frame.pack(pady=10, fill='x')

            self.debug_var = tk.BooleanVar(value=self.settings.get("debug_mode", False))
            debug_check = tk.Checkbutton(
                debug_frame,
                text="Enable Debug Mode",
                variable=self.debug_var,
                font=('Arial', 12),
                fg='white',
                bg='#0a0a2a',
                selectcolor='#333333',
                activebackground='#0a0a2a',
                activeforeground='white',
                onvalue=True,
                offvalue=False,
                anchor='w'
            )
            debug_check.pack(side='left', padx=(20, 10))

            # --- Reset to Defaults ---
            reset_frame = tk.Frame(options_frame, bg='#0a0a2a')
            reset_frame.pack(pady=20)

            reset_button = tk.Button(
                reset_frame,
                text="Reset to Defaults",
                command=self.reset_options,
                font=('Arial', 12),
                width=15,
                height=1,
                bg='#555555',
                fg='white',
                relief='raised',
                bd=4,
                activebackground='#333333',
                activeforeground='white'
            )
            reset_button.pack()

            # --- Close Button ---
            close_button = tk.Button(
                options_frame,
                text="Save & Close",
                command=self.close_options,
                font=('Arial', 12, 'bold'),
                width=15,
                height=2,
                bg='#FF0000',
                fg='white',
                relief='raised',
                bd=4,
                activebackground='#CC0000',
                activeforeground='white'
            )
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
        # Update settings with new values
        self.settings["graphics_quality"] = self.graphics_var.get()
        self.settings["music_enabled"] = self.music_var.get()
        self.settings["sound_volume"] = self.volume_var.get()
        self.settings["beta_mode"] = self.beta_var.get()
        self.settings["debug_mode"] = self.debug_var.get()
        
        # Save the settings
        if self.save_settings():
            self.status_label.config(text=f"Options saved! Graphics: {self.settings['graphics_quality']}")
        else:
            self.status_label.config(text="Error saving options!")
        
        # Release grab and destroy the window
        self.options_window.grab_release()
        self.options_window.destroy()

    def quit_game(self):
        self.status_label.config(text="Thanks for playing!")
        self.root.after(1000, self.root.destroy)


# ------------------------------
# Ursina 3D Game Engine
# ------------------------------
class UrsinaGame:
    def __init__(self, settings=None):
        self.app = None
        self.settings = settings or {}
        self.beta_mode = self.settings.get("beta_mode", True)
        self.debug_mode = self.settings.get("debug_mode", False)
        
    def run(self):
        # Import Ursina here to avoid Tkinter conflicts
        try:
            from ursina import (
                Ursina, Entity, time, held_keys, Vec3, color, 
                camera, Sky, Text, application, destroy, scene, 
                DirectionalLight, AmbientLight, raycast, math, 
                load_model, load_texture, collider
            )
            from ursina.prefabs.first_person_controller import FirstPersonController
        except ImportError:
            print("--------------------------------------------------")
            print("FATAL ERROR: 'ursina' module not found.")
            print("Please install Ursina to play this game:")
            print("  pip install ursina")
            print("--------------------------------------------------")
            return # Exit the run method if ursina is not found
        
        # Game constants
        GRAVITY = 1
        JUMP_HEIGHT = 0.5
        PLAYER_SPEED = 6
        JUMP_DURATION = 0.3
        
        class BetaMario(Entity):
            def __init__(self):
                super().__init__(
                    model='cube',
                    color=color.clear, # Make the root entity invisible
                    scale=(1, 2, 1),
                    position=(0, 10, 0),
                    collider='box'
                )
                self.speed = PLAYER_SPEED
                self.jump_height = JUMP_HEIGHT
                self.jump_duration = JUMP_DURATION
                self.jumping = False
                self.air_time = 0
                
                self.grounded = False
                self.health = 100
                self.coins = 0
                self.score = 0
                self.stars = 0
                self.lives = 4
                self.velocity_y = 0
                self.power_up = "normal"  # normal, metal, wing, vanish
                self.cap_on = True

                # Create beta Mario model
                self.create_beta_mario_model()
                
                # Camera setup
                camera.parent = self
                camera.position = (0, 5, -8)
                camera.rotation_x = 20
                camera.rotation_y = 0
            
            def create_beta_mario_model(self):
                # Beta Mario had a different model with more polygons
                # Head
                self.head = Entity(
                    parent=self,
                    model='sphere',
                    color=color.rgb(255, 200, 150),
                    scale=(0.8 / self.scale_x, 0.8 / self.scale_y, 0.8 / self.scale_z),
                    position=(0, 0.8, 0)
                )
                
                # Beta hat was different
                self.hat = Entity(
                    parent=self.head,
                    model='cube',
                    color=color.red,
                    scale=(1.2, 0.4, 1.2),
                    position=(0, 0.5, 0)
                )
                
                # Beta emblem on hat
                self.emblem = Entity(
                    parent=self.hat,
                    model='cube',
                    color=color.white,
                    scale=(0.5, 0.1, 0.5),
                    position=(0, 0.2, 0.5)
                )
                
                # Body
                self.body_model = Entity(
                    parent=self,
                    model='cube',
                    color=color.red,
                    scale=(0.8 / self.scale_x, 1 / self.scale_y, 0.6 / self.scale_z),
                    position=(0, 0, 0)
                )
                
                # Overalls
                self.overalls = Entity(
                    parent=self.body_model,
                    model='cube',
                    color=color.blue,
                    scale=(1.1, 0.7, 1.1),
                    position=(0, -0.3, 0)
                )
                
                # Arms
                self.left_arm = Entity(
                    parent=self,
                    model='cube',
                    color=color.rgb(255, 200, 150),
                    scale=(0.3 / self.scale_x, 0.8 / self.scale_y, 0.3 / self.scale_z),
                    position=(-0.6, 0, 0)
                )
                self.right_arm = Entity(
                    parent=self,
                    model='cube',
                    color=color.rgb(255, 200, 150),
                    scale=(0.3 / self.scale_x, 0.8 / self.scale_y, 0.3 / self.scale_z),
                    position=(0.6, 0, 0)
                )
                
                # Legs
                self.left_leg = Entity(
                    parent=self,
                    model='cube',
                    color=color.blue,
                    scale=(0.35 / self.scale_x, 0.8 / self.scale_y, 0.35 / self.scale_z),
                    position=(-0.25, -0.8, 0)
                )
                self.right_leg = Entity(
                    parent=self,
                    model='cube',
                    color=color.blue,
                    scale=(0.35 / self.scale_x, 0.8 / self.scale_y, 0.35 / self.scale_z),
                    position=(0.25, -0.8, 0)
                )
                
                # Beta Mario had gloves
                self.left_glove = Entity(
                    parent=self.left_arm,
                    model='sphere',
                    color=color.white,
                    scale=(0.4, 0.4, 0.4),
                    position=(0, -0.5, 0)
                )
                self.right_glove = Entity(
                    parent=self.right_arm,
                    model='sphere',
                    color=color.white,
                    scale=(0.4, 0.4, 0.4),
                    position=(0, -0.5, 0)
                )
            
            def update_movement(self):
                # Movement
                direction = Vec3(0, 0, 0)
                if held_keys['w'] or held_keys['up arrow']:
                    direction += self.forward
                if held_keys['s'] or held_keys['down arrow']:
                    direction -= self.forward
                if held_keys['a'] or held_keys['left arrow']:
                    direction -= self.right
                if held_keys['d'] or held_keys['right arrow']:
                    direction += self.right
                
                # Rotation
                self.rotation_y += held_keys['right arrow'] * time.dt * 100
                self.rotation_y -= held_keys['left arrow'] * time.dt * 100

                if direction.length() > 0:
                    direction = direction.normalized()
                    
                    # Prevent moving through walls
                    move_ray = raycast(self.position + Vec3(0, 0.5, 0), direction, distance=0.6, ignore=[self])
                    if not move_ray.hit:
                        self.position += direction * self.speed * time.dt
                    
                    # Simple animation
                    self.left_leg.rotation_x = math.sin(pytime.time() * 10) * 30
                    self.right_leg.rotation_x = -math.sin(pytime.time() * 10) * 30
                    self.left_arm.rotation_x = -math.sin(pytime.time() * 10) * 20
                    self.right_arm.rotation_x = math.sin(pytime.time() * 10) * 20
                else:
                    self.left_leg.rotation_x = 0
                    self.right_leg.rotation_x = 0
                    self.left_arm.rotation_x = 0
                    self.right_arm.rotation_x = 0

            def update_gravity(self):
                # Gravity
                if not self.grounded:
                    self.velocity_y -= GRAVITY * time.dt
                    self.y += self.velocity_y
                
                # Check for ground
                ground_ray = raycast(self.position, Vec3(0, -1, 0), distance=1.1, ignore=[self])
                
                if ground_ray.hit:
                    if self.velocity_y < 0:
                        self.y = ground_ray.world_point.y + 1
                        self.velocity_y = 0
                        self.grounded = True
                        self.jumping = False
                else:
                    self.grounded = False

            def update(self):
                self.update_movement()
                self.update_gravity()

            def jump(self):
                if self.grounded:
                    self.velocity_y = 0.2 # Adjust this value for jump height
                    self.grounded = False
                    self.jumping = True

            def input(self, key):
                if key == 'escape':
                    application.quit()
                if key == 'r':
                    self.position = (0, 10, 0)
                    self.velocity_y = 0
                if key == 'space':
                    self.jump()
                # Beta debug controls
                if self.debug_mode:
                    if key == '1':
                        self.power_up = "normal"
                        print("Power-up: Normal")
                    if key == '2':
                        self.power_up = "metal"
                        print("Power-up: Metal")
                    if key == '3':
                        self.power_up = "wing"
                        print("Power-up: Wing")
                    if key == '4':
                        self.power_up = "vanish"
                        print("Power-up: Vanish")
                    if key == 'c':
                        self.cap_on = not self.cap_on
                        self.hat.enabled = self.cap_on
                        print(f"Cap: {'On' if self.cap_on else 'Off'}")
        
        class BetaHUD:
            def __init__(self, player):
                self.player = player
                
                # Beta HUD had a different layout
                # Lives display
                self.lives_text = Text(
                    text=f"MARIO x{self.player.lives}",
                    origin=(-.85, .85),
                    position=(-0.85, 0.45),
                    scale=2,
                    color=color.white
                )
                
                # Coin display
                self.coin_text = Text(
                    text=f"×{self.player.coins:02d}",
                    origin=(-.5, .5),
                    position=(-0.5, 0.45),
                    scale=2,
                    color=color.yellow
                )
                
                # Coin icon
                self.coin_icon = Text(
                    text="¢",
                    origin=(-.5, .5),
                    position=(-0.6, 0.45),
                    scale=2,
                    color=color.yellow
                )
                
                # Star display
                self.star_text = Text(
                    text=f"×{self.player.stars}",
                    origin=(-.5, .5),
                    position=(-0.2, 0.45),
                    scale=2,
                    color=color.rgba(255, 255, 0, 255)
                )
                
                # Star icon
                self.star_icon = Text(
                    text="★",
                    origin=(-.5, .5),
                    position=(-0.3, 0.45),
                    scale=2,
                    color=color.rgba(255, 255, 0, 255)
                )
                
                # Power-up display (beta feature)
                self.power_text = Text(
                    text=f"POWER: {self.player.power_up.upper()}",
                    origin=(-.5, .5),
                    position=(0.2, 0.45),
                    scale=1.5,
                    color=color.white
                )
                
                # Camera position (beta debug feature)
                self.camera_text = Text(
                    text="CAM: POS",
                    origin=(-.5, .5),
                    position=(0.5, 0.45),
                    scale=1.5,
                    color=color.white
                )
                
                # Health bar (beta feature that was removed)
                self.health_bar_bg = Entity(
                    parent=camera.ui,
                    model='quad',
                    color=color.rgba(0, 0, 0, 128),
                    scale=(0.2, 0.02),
                    position=(-0.65, -0.45)
                )
                
                self.health_bar = Entity(
                    parent=camera.ui,
                    model='quad',
                    color=color.red,
                    scale=(0.2, 0.02),
                    position=(-0.65, -0.45)
                )
                
                # Instructions
                self.instructions = Text(
                    text='WASD: Move | SPACE: Jump | R: Reset | ESC: Quit',
                    origin=(0, 0),
                    position=(0, -0.45),
                    scale=1.5,
                    color=color.white
                )
                
                # Beta debug info
                if self.debug_mode:
                    self.debug_text = Text(
                        text='DEBUG MODE',
                        origin=(.5, .5),
                        position=(0.5, -0.45),
                        scale=1.5,
                        color=color.red
                    )
            
            def update(self):
                self.lives_text.text = f"MARIO x{self.player.lives}"
                self.coin_text.text = f"×{self.player.coins:02d}"
                self.star_text.text = f"×{self.player.stars}"
                self.power_text.text = f"POWER: {self.player.power_up.upper()}"
                
                # Update camera position
                self.camera_text.text = f"CAM: {int(camera.position.x)},{int(camera.position.y)},{int(camera.position.z)}"
                
                # Update health bar
                health_percentage = self.player.health / 100
                self.health_bar.scale_x = 0.2 * health_percentage
                
                # Change health bar color based on health
                if self.player.health > 60:
                    self.health_bar.color = color.green
                elif self.player.health > 30:
                    self.health_bar.color = color.yellow
                else:
                    self.health_bar.color = color.red
        
        class BetaWorld:
            def __init__(self, custom_level_path=None):
                self.custom_level_path = custom_level_path
                self.create_environment()
                self.coins = self.create_coins()
                self.enemies = self.create_enemies()
                self.power_ups = self.create_power_ups()
                self.create_platforms()
                
            def create_environment(self):
                # Ground
                Entity(
                    model='plane',
                    texture='white_cube',
                    color=color.green,
                    scale=(100, 1, 100),
                    position=(0, 0, 0),
                    collider='box'
                )
                
                # Sky
                Sky()
                
                # Load custom level if available
                if self.custom_level_path and os.path.exists(self.custom_level_path):
                    try:
                        with open(self.custom_level_path, 'r') as f:
                            level_data = json.load(f)
                            self.load_custom_level(level_data)
                    except Exception as e:
                        print(f"Error loading custom level: {e}")
                        self.create_beta_level()
                else:
                    self.create_beta_level()
            
            def create_beta_level(self):
                # Beta level design - different from final
                # Beta had more platforms and different layouts
                
                # Beta castle (different design)
                for i in range(10):
                    size = 10 - i
                    Entity(
                        model='cube',
                        color=color.rgba(200, 150, 100, 255),
                        scale=(size*2, 1, size*2),
                        position=(0, i, 0),
                        collider='box'
                    )
                
                # Beta platforms (different layout)
                platform_positions = [
                    (5, 2, 5),
                    (10, 4, 10),
                    (15, 6, 15),
                    (20, 8, 20),
                    (-5, 3, -5),
                    (-10, 5, -10),
                    (-15, 7, -15),
                    (-20, 9, -20),
                    (0, 10, 25),
                    (0, 12, -25),
                    (25, 5, 0),
                    (-25, 7, 0)
                ]
                
                for pos in platform_positions:
                    Entity(
                        model='cube',
                        color=color.rgba(100, 100, 200, 255),
                        scale=(3, 0.5, 3),
                        position=pos,
                        collider='box'
                    )
                
                # Beta moving platforms (feature from beta)
                self.moving_platforms = []
                for i in range(3):
                    platform = Entity(
                        model='cube',
                        color=color.rgba(200, 100, 100, 255),
                        scale=(3, 0.5, 3),
                        position=(i*10-10, 5, 0),
                        collider='box'
                    )
                    self.moving_platforms.append(platform)
            
            def load_custom_level(self, level_data):
                # Load platforms from custom level data
                if 'platforms' in level_data:
                    for platform in level_data['platforms']:
                        Entity(
                            model=platform.get('model', 'cube'),
                            color=color.rgba(*platform.get('color', [255, 165, 0, 255])),
                            scale=platform.get('scale', [3, 0.5, 3]),
                            position=platform.get('position', [0, 2, 0]),
                            collider='box'
                        )
                
                # Load other level elements as needed
                # This is a basic implementation, can be expanded
            
            def create_coins(self):
                coins_list = []
                for i in range(30):  # More coins in beta
                    x = random.uniform(-20, 20)
                    z = random.uniform(-20, 20)
                    y = random.uniform(2, 15)
                    
                    coin = Entity(
                        model='cylinder',
                        color=color.gold,
                        scale=(0.5, 0.1, 0.5),
                        position=(x, y, z),
                        collider='sphere'
                    )
                    coins_list.append(coin)
                return coins_list
            
            def create_enemies(self):
                enemies_list = []
                
                # Beta had different enemies
                # Goombas
                for i in range(5):
                    x = random.uniform(-10, 10)
                    z = random.uniform(-10, 10)
                    
                    goomba = Entity(
                        model='cube',
                        color=color.brown,
                        scale=(1, 0.8, 1),
                        position=(x, 0.4, z),
                        collider='box'
                    )
                    enemies_list.append(goomba)
                
                # Koopas (beta had different design)
                for i in range(3):
                    x = random.uniform(-15, 15)
                    z = random.uniform(-15, 15)
                    
                    koopa = Entity(
                        model='cube',
                        color=color.green,
                        scale=(1, 1.2, 1),
                        position=(x, 0.6, z),
                        collider='box'
                    )
                    enemies_list.append(koopa)
                
                return enemies_list
            
            def create_power_ups(self):
                power_ups_list = []
                
                # Beta had different power-ups
                # Metal cap
                metal_cap = Entity(
                    model='cube',
                    color=color.gray,
                    scale=(0.5, 0.5, 0.5),
                    position=(10, 3, 10),
                    collider='box'
                )
                power_ups_list.append(metal_cap)
                
                # Wing cap
                wing_cap = Entity(
                    model='cube',
                    color=color.rgba(255, 255, 0, 255),
                    scale=(0.5, 0.5, 0.5),
                    position=(-10, 3, -10),
                    collider='box'
                )
                power_ups_list.append(wing_cap)
                
                # Vanish cap
                vanish_cap = Entity(
                    model='cube',
                    color=color.rgba(100, 100, 255, 128),
                    scale=(0.5, 0.5, 0.5),
                    position=(0, 3, 15),
                    collider='box'
                )
                power_ups_list.append(vanish_cap)
                
                return power_ups_list
            
            def create_platforms(self):
                # Create some floating platforms
                positions = [
                    (0, 5, 5),
                    (8, 8, 8),
                    (-8, 12, -8),
                    (12, 15, -12),
                    (-12, 18, 12)
                ]
                
                for pos in positions:
                    Entity(
                        model='cube',
                        color=color.blue,
                        scale=(3, 0.5, 3),
                        position=pos,
                        collider='box'
                    )
            
            def update(self):
                # Update moving platforms
                for i, platform in enumerate(self.moving_platforms):
                    platform.x += math.sin(time.time() + i) * 0.05
                    platform.z += math.cos(time.time() + i) * 0.05
        
        # Create the Ursina application
        app = Ursina(title="Ultra Mario 3D Bros - Beta Build", development_mode=False)
        
        # Apply graphics settings
        graphics_quality = self.settings.get("graphics_quality", "Medium")
        if graphics_quality == "Low":
            application.render_mode = 'wireframe'
        elif graphics_quality == "High":
            application.render_mode = 'default'
        elif graphics_quality == "Ultra":
            application.render_mode = 'default'
            # Additional high-quality settings could be applied here
        
        # Create game objects
        player = BetaMario()
        world = BetaWorld(self.settings.get("custom_level_path", None))
        ui = BetaHUD(player)
        
        # Add lighting
        DirectionalLight(parent=scene, y=10, z=5, shadows=True, rotation=(30, 30, 0))
        AmbientLight(color=color.rgba(100, 100, 100, 255))
        
        def update():
            player.update()
            world.update()
            ui.update()
            
            # Check coin collection
            for coin in world.coins[:]:
                if player.intersects(coin).hit:
                    player.coins += 1
                    player.score += 100
                    world.coins.remove(coin)
                    
                    # Create collection effect
                    for i in range(5):
                        particle = Entity(
                            model='sphere',
                            color=color.yellow,
                            scale=0.1,
                            position=coin.position
                        )
                        particle.animate_position(
                            particle.position + Vec3(random.uniform(-2, 2), random.uniform(0, 3), random.uniform(-2, 2)),
                            duration=0.5
                        )
                        particle.animate_scale(0, duration=0.5)
                        destroy(particle, delay=0.5)
                    
                    destroy(coin)
            
            # Check power-up collection
            for power_up in world.power_ups[:]:
                if player.intersects(power_up).hit:
                    # Determine which power-up was collected
                    if power_up.color == color.gray:
                        player.power_up = "metal"
                    elif power_up.color == color.rgba(255, 255, 0, 255):
                        player.power_up = "wing"
                    elif power_up.color == color.rgba(100, 100, 255, 128):
                        player.power_up = "vanish"
                    
                    world.power_ups.remove(power_up)
                    destroy(power_up)
            
            # Check enemy collision
            for enemy in world.enemies:
                if player.intersects(enemy).hit:
                    # Simple check: reset player if not jumping on top
                    if not player.jumping and player.y < (enemy.y + 1.1):
                        player.position = (0, 10, 0)
                        player.health -= 10
                        player.lives -= 1
                    elif player.velocity_y < -0.05: # Jumping on top
                        destroy(enemy)
                        world.enemies.remove(enemy)
                        player.score += 200
                        player.jump() # bounce
        
        def input(key):
            player.input(key)
        
        # Run the game
        app.run()


# ------------------------------
# Main Execution
# ------------------------------
def main():
    # Check if we should launch Tkinter menu or go directly to game
    if len(sys.argv) > 1 and sys.argv[1] == '--direct':
        # Launch Ursina directly
        game = UrsinaGame()
        game.run()
    else:
        # Launch Tkinter menu
        root = tk.Tk()
        app = UltraMarioLauncher(root)
        root.mainloop()

if __name__ == "__main__":
    main()
