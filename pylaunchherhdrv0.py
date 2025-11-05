#!/usr/bin/env python3
"""
🎮 PyLauncher - Minecraft Launcher (TLauncher Style)
A clean, safe Minecraft launcher with professional UI
Version: 1.0.0
Author: FlamesCo Labs
License: GPL-3.0
"""

import os
import sys
import json
import time
import hashlib
import platform
import subprocess
import threading
import webbrowser
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk, ImageDraw, ImageFont
import requests
from urllib.parse import urlparse
import zipfile
import shutil

# ==================== Configuration ====================

@dataclass
class LauncherConfig:
    """Main launcher configuration"""
    name: str = "PyLauncher"
    version: str = "1.0.0"
    author: str = "FlamesCo Labs"
    minecraft_dir: Path = field(default_factory=lambda: Path.home() / ".minecraft")
    launcher_dir: Path = field(default_factory=lambda: Path.home() / ".pylauncher")
    max_ram: int = 4096
    min_ram: int = 512
    default_ram: int = 2048
    java_args: str = "-XX:+UnlockExperimentalVMOptions -XX:+UseG1GC -XX:G1NewSizePercent=20"
    window_width: int = 950
    window_height: int = 550
    theme: str = "dark"

@dataclass
class ColorScheme:
    """TLauncher-style color scheme"""
    # Dark theme colors
    bg_primary: str = "#1e1e1e"
    bg_secondary: str = "#2d2d30"
    bg_tertiary: str = "#252526"
    bg_hover: str = "#3e3e42"
    
    # Accent colors (TLauncher green)
    accent_primary: str = "#4CAF50"
    accent_hover: str = "#66BB6A"
    accent_pressed: str = "#388E3C"
    
    # Text colors
    text_primary: str = "#ffffff"
    text_secondary: str = "#cccccc"
    text_disabled: str = "#808080"
    
    # Status colors
    success: str = "#4CAF50"
    warning: str = "#FFC107"
    error: str = "#F44336"
    info: str = "#2196F3"
    
    # UI elements
    border: str = "#3e3e42"
    input_bg: str = "#3c3c3c"
    scrollbar: str = "#4e4e52"

# ==================== Core Components ====================

class MinecraftVersion:
    """Minecraft version management"""
    
    MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest_v2.json"
    
    def __init__(self, launcher_dir: Path):
        self.launcher_dir = launcher_dir
        self.versions_dir = launcher_dir / "versions"
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_cache = None
        self.last_fetch = 0
        
    def get_versions(self, version_type: str = "all") -> List[Dict]:
        """Get available Minecraft versions"""
        try:
            # Cache manifest for 5 minutes
            if not self.manifest_cache or time.time() - self.last_fetch > 300:
                response = requests.get(self.MANIFEST_URL, timeout=10)
                self.manifest_cache = response.json()
                self.last_fetch = time.time()
            
            versions = self.manifest_cache.get("versions", [])
            
            if version_type == "release":
                return [v for v in versions if v["type"] == "release"]
            elif version_type == "snapshot":
                return [v for v in versions if v["type"] == "snapshot"]
            elif version_type == "old":
                return [v for v in versions if v["type"] in ["old_alpha", "old_beta"]]
            return versions
            
        except Exception as e:
            print(f"Error fetching versions: {e}")
            return []
    
    def download_version(self, version_id: str, progress_callback=None) -> bool:
        """Download Minecraft version files"""
        try:
            version_dir = self.versions_dir / version_id
            version_dir.mkdir(parents=True, exist_ok=True)
            
            # Download version JSON
            versions = self.get_versions()
            version_info = next((v for v in versions if v["id"] == version_id), None)
            
            if not version_info:
                return False
            
            # Download version manifest
            response = requests.get(version_info["url"])
            version_data = response.json()
            
            # Save version JSON
            with open(version_dir / f"{version_id}.json", "w") as f:
                json.dump(version_data, f, indent=2)
            
            # Download client JAR
            client_url = version_data["downloads"]["client"]["url"]
            client_path = version_dir / f"{version_id}.jar"
            
            if progress_callback:
                progress_callback("Downloading client JAR...", 0)
            
            self._download_file(client_url, client_path, progress_callback)
            
            # Download libraries
            self._download_libraries(version_data, progress_callback)
            
            # Download assets
            self._download_assets(version_data, progress_callback)
            
            return True
            
        except Exception as e:
            print(f"Error downloading version {version_id}: {e}")
            return False
    
    def _download_file(self, url: str, path: Path, progress_callback=None):
        """Download file with progress tracking"""
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total_size:
                        progress = (downloaded / total_size) * 100
                        progress_callback(f"Downloading: {path.name}", progress)
    
    def _download_libraries(self, version_data: Dict, progress_callback=None):
        """Download required libraries"""
        libraries_dir = self.launcher_dir / "libraries"
        
        for lib in version_data.get("libraries", []):
            if "downloads" in lib and "artifact" in lib["downloads"]:
                artifact = lib["downloads"]["artifact"]
                lib_path = libraries_dir / artifact["path"]
                
                if not lib_path.exists():
                    if progress_callback:
                        progress_callback(f"Downloading library: {lib_path.name}", 0)
                    
                    self._download_file(artifact["url"], lib_path, progress_callback)
    
    def _download_assets(self, version_data: Dict, progress_callback=None):
        """Download game assets"""
        assets_dir = self.launcher_dir / "assets"
        
        # Download asset index
        asset_index = version_data.get("assetIndex")
        if asset_index:
            index_path = assets_dir / "indexes" / f"{asset_index['id']}.json"
            
            if not index_path.exists():
                self._download_file(asset_index["url"], index_path, progress_callback)
            
            # Download asset objects
            with open(index_path) as f:
                assets = json.load(f)
            
            for asset_name, asset_info in assets.get("objects", {}).items():
                hash_val = asset_info["hash"]
                asset_path = assets_dir / "objects" / hash_val[:2] / hash_val
                
                if not asset_path.exists():
                    asset_url = f"https://resources.download.minecraft.net/{hash_val[:2]}/{hash_val}"
                    self._download_file(asset_url, asset_path, progress_callback)

class ProfileManager:
    """Manage user profiles and accounts"""
    
    def __init__(self, launcher_dir: Path):
        self.launcher_dir = launcher_dir
        self.profiles_file = launcher_dir / "profiles.json"
        self.profiles = self._load_profiles()
    
    def _load_profiles(self) -> Dict:
        """Load profiles from file"""
        if self.profiles_file.exists():
            try:
                with open(self.profiles_file) as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "profiles": {},
            "selected": None
        }
    
    def save_profiles(self):
        """Save profiles to file"""
        self.profiles_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.profiles_file, "w") as f:
            json.dump(self.profiles, f, indent=2)
    
    def add_profile(self, name: str, settings: Dict) -> bool:
        """Add new profile"""
        if name in self.profiles["profiles"]:
            return False
        
        self.profiles["profiles"][name] = {
            "created": datetime.now().isoformat(),
            "lastUsed": datetime.now().isoformat(),
            "type": "custom",
            "icon": "Grass",
            **settings
        }
        
        if not self.profiles["selected"]:
            self.profiles["selected"] = name
        
        self.save_profiles()
        return True
    
    def get_profile(self, name: str) -> Optional[Dict]:
        """Get profile by name"""
        return self.profiles["profiles"].get(name)
    
    def get_selected_profile(self) -> Optional[Tuple[str, Dict]]:
        """Get currently selected profile"""
        selected = self.profiles.get("selected")
        if selected and selected in self.profiles["profiles"]:
            return selected, self.profiles["profiles"][selected]
        return None
    
    def set_selected(self, name: str):
        """Set selected profile"""
        if name in self.profiles["profiles"]:
            self.profiles["selected"] = name
            self.save_profiles()

# ==================== UI Components ====================

class TLauncherUI(tk.Tk):
    """Main launcher window with TLauncher-style UI"""
    
    def __init__(self):
        super().__init__()
        
        self.config = LauncherConfig()
        self.colors = ColorScheme()
        self.version_manager = MinecraftVersion(self.config.launcher_dir)
        self.profile_manager = ProfileManager(self.config.launcher_dir)
        
        self.setup_window()
        self.create_widgets()
        self.load_data()
    
    def setup_window(self):
        """Configure main window"""
        self.title(f"{self.config.name} v{self.config.version}")
        self.geometry(f"{self.config.window_width}x{self.config.window_height}")
        self.configure(bg=self.colors.bg_primary)
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.config.window_width // 2)
        y = (self.winfo_screenheight() // 2) - (self.config.window_height // 2)
        self.geometry(f"+{x}+{y}")
        
        # Prevent resizing
        self.resizable(False, False)
        
        # Set icon (if available)
        try:
            if platform.system() == "Windows":
                self.iconbitmap("icon.ico")
        except:
            pass
    
    def create_widgets(self):
        """Create all UI widgets"""
        self.create_header()
        self.create_sidebar()
        self.create_main_area()
        self.create_bottom_bar()
    
    def create_header(self):
        """Create header with logo and account info"""
        header = tk.Frame(self, bg=self.colors.bg_secondary, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        # Logo area
        logo_frame = tk.Frame(header, bg=self.colors.bg_secondary)
        logo_frame.pack(side="left", padx=20)
        
        logo_label = tk.Label(
            logo_frame,
            text="🎮 PyLauncher",
            font=("Arial", 18, "bold"),
            bg=self.colors.bg_secondary,
            fg=self.colors.accent_primary
        )
        logo_label.pack(side="left")
        
        version_label = tk.Label(
            logo_frame,
            text=f"v{self.config.version}",
            font=("Arial", 10),
            bg=self.colors.bg_secondary,
            fg=self.colors.text_secondary
        )
        version_label.pack(side="left", padx=(10, 0))
        
        # Account area
        account_frame = tk.Frame(header, bg=self.colors.bg_secondary)
        account_frame.pack(side="right", padx=20)
        
        self.username_var = tk.StringVar(value="Player")
        username_entry = tk.Entry(
            account_frame,
            textvariable=self.username_var,
            font=("Arial", 11),
            bg=self.colors.input_bg,
            fg=self.colors.text_primary,
            insertbackground=self.colors.text_primary,
            relief="flat",
            width=15
        )
        username_entry.pack(side="left", padx=5)
        
        account_btn = tk.Button(
            account_frame,
            text="👤 Account",
            font=("Arial", 10),
            bg=self.colors.accent_primary,
            fg="white",
            relief="flat",
            padx=15,
            pady=5,
            cursor="hand2",
            command=self.show_account_dialog
        )
        account_btn.pack(side="left", padx=5)
    
    def create_sidebar(self):
        """Create sidebar with navigation"""
        sidebar = tk.Frame(self, bg=self.colors.bg_tertiary, width=200)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        
        # Navigation buttons
        nav_items = [
            ("🏠 Home", self.show_home),
            ("🎯 Versions", self.show_versions),
            ("👥 Profiles", self.show_profiles),
            ("🔧 Settings", self.show_settings),
            ("📦 Mods", self.show_mods),
            ("🌍 Servers", self.show_servers),
            ("📰 News", self.show_news)
        ]
        
        for text, command in nav_items:
            btn = tk.Button(
                sidebar,
                text=text,
                font=("Arial", 11),
                bg=self.colors.bg_tertiary,
                fg=self.colors.text_primary,
                relief="flat",
                anchor="w",
                padx=20,
                pady=12,
                cursor="hand2",
                command=command
            )
            btn.pack(fill="x")
            
            # Hover effects
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.colors.bg_hover))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=self.colors.bg_tertiary))
    
    def create_main_area(self):
        """Create main content area"""
        self.main_frame = tk.Frame(self, bg=self.colors.bg_primary)
        self.main_frame.pack(side="left", fill="both", expand=True)
        
        # Create home page by default
        self.show_home()
    
    def create_bottom_bar(self):
        """Create bottom bar with play button and settings"""
        bottom = tk.Frame(self, bg=self.colors.bg_secondary, height=80)
        bottom.pack(side="bottom", fill="x")
        bottom.pack_propagate(False)
        
        # Settings area
        settings_frame = tk.Frame(bottom, bg=self.colors.bg_secondary)
        settings_frame.pack(side="left", padx=20, pady=15)
        
        # Version selector
        tk.Label(
            settings_frame,
            text="Version:",
            font=("Arial", 10),
            bg=self.colors.bg_secondary,
            fg=self.colors.text_secondary
        ).grid(row=0, column=0, padx=(0, 10), sticky="w")
        
        self.version_var = tk.StringVar()
        self.version_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.version_var,
            font=("Arial", 10),
            width=20,
            state="readonly"
        )
        self.version_combo.grid(row=0, column=1, padx=(0, 20))
        
        # RAM settings
        tk.Label(
            settings_frame,
            text="RAM:",
            font=("Arial", 10),
            bg=self.colors.bg_secondary,
            fg=self.colors.text_secondary
        ).grid(row=0, column=2, padx=(0, 10), sticky="w")
        
        self.ram_var = tk.StringVar(value="2G")
        ram_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.ram_var,
            font=("Arial", 10),
            width=10,
            values=["1G", "2G", "3G", "4G", "6G", "8G", "12G", "16G"],
            state="readonly"
        )
        ram_combo.grid(row=0, column=3)
        
        # Play button
        self.play_button = tk.Button(
            bottom,
            text="PLAY",
            font=("Arial", 16, "bold"),
            bg=self.colors.accent_primary,
            fg="white",
            relief="flat",
            padx=40,
            pady=15,
            cursor="hand2",
            command=self.launch_game
        )
        self.play_button.pack(side="right", padx=30)
        
        # Hover effect
        self.play_button.bind("<Enter>", lambda e: self.play_button.config(bg=self.colors.accent_hover))
        self.play_button.bind("<Leave>", lambda e: self.play_button.config(bg=self.colors.accent_primary))
        
        # Progress bar (hidden by default)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            bottom,
            variable=self.progress_var,
            maximum=100,
            length=300
        )
        self.progress_label = tk.Label(
            bottom,
            text="",
            font=("Arial", 9),
            bg=self.colors.bg_secondary,
            fg=self.colors.text_secondary
        )
    
    def show_home(self):
        """Show home page"""
        self.clear_main_frame()
        
        # Welcome message
        welcome = tk.Frame(self.main_frame, bg=self.colors.bg_primary)
        welcome.pack(expand=True)
        
        tk.Label(
            welcome,
            text="Welcome to PyLauncher",
            font=("Arial", 24, "bold"),
            bg=self.colors.bg_primary,
            fg=self.colors.text_primary
        ).pack(pady=(0, 10))
        
        tk.Label(
            welcome,
            text="A clean, fast Minecraft launcher",
            font=("Arial", 12),
            bg=self.colors.bg_primary,
            fg=self.colors.text_secondary
        ).pack(pady=(0, 30))
        
        # Quick actions
        actions_frame = tk.Frame(welcome, bg=self.colors.bg_primary)
        actions_frame.pack()
        
        quick_actions = [
            ("🚀 Quick Play", self.launch_game),
            ("📥 Install Version", self.show_versions),
            ("⚙️ Settings", self.show_settings)
        ]
        
        for text, command in quick_actions:
            btn = tk.Button(
                actions_frame,
                text=text,
                font=("Arial", 12),
                bg=self.colors.bg_secondary,
                fg=self.colors.text_primary,
                relief="flat",
                padx=20,
                pady=10,
                cursor="hand2",
                command=command
            )
            btn.pack(side="left", padx=10)
            
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.colors.bg_hover))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=self.colors.bg_secondary))
        
        # Stats
        stats_frame = tk.Frame(welcome, bg=self.colors.bg_primary)
        stats_frame.pack(pady=40)
        
        stats = [
            ("Installed Versions", len(os.listdir(self.version_manager.versions_dir)) if self.version_manager.versions_dir.exists() else 0),
            ("Profiles", len(self.profile_manager.profiles.get("profiles", {}))),
            ("Total Playtime", "0h 0m")
        ]
        
        for label, value in stats:
            stat_frame = tk.Frame(stats_frame, bg=self.colors.bg_secondary, padx=20, pady=15)
            stat_frame.pack(side="left", padx=10)
            
            tk.Label(
                stat_frame,
                text=str(value),
                font=("Arial", 20, "bold"),
                bg=self.colors.bg_secondary,
                fg=self.colors.accent_primary
            ).pack()
            
            tk.Label(
                stat_frame,
                text=label,
                font=("Arial", 10),
                bg=self.colors.bg_secondary,
                fg=self.colors.text_secondary
            ).pack()
    
    def show_versions(self):
        """Show versions management page"""
        self.clear_main_frame()
        
        # Header
        header = tk.Frame(self.main_frame, bg=self.colors.bg_primary)
        header.pack(fill="x", padx=20, pady=20)
        
        tk.Label(
            header,
            text="Minecraft Versions",
            font=("Arial", 18, "bold"),
            bg=self.colors.bg_primary,
            fg=self.colors.text_primary
        ).pack(side="left")
        
        # Filter buttons
        filter_frame = tk.Frame(header, bg=self.colors.bg_primary)
        filter_frame.pack(side="right")
        
        filters = ["All", "Release", "Snapshot", "Old"]
        for filter_type in filters:
            btn = tk.Button(
                filter_frame,
                text=filter_type,
                font=("Arial", 10),
                bg=self.colors.bg_secondary,
                fg=self.colors.text_primary,
                relief="flat",
                padx=15,
                pady=5,
                cursor="hand2",
                command=lambda t=filter_type.lower(): self.filter_versions(t)
            )
            btn.pack(side="left", padx=2)
        
        # Versions list
        list_frame = tk.Frame(self.main_frame, bg=self.colors.bg_primary)
        list_frame.pack(fill="both", expand=True, padx=20)
        
        # Scrollable frame
        canvas = tk.Canvas(list_frame, bg=self.colors.bg_primary, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors.bg_primary)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Load versions
        versions = self.version_manager.get_versions("release")[:20]  # Show first 20
        
        for version in versions:
            version_frame = tk.Frame(
                scrollable_frame,
                bg=self.colors.bg_secondary,
                relief="flat",
                bd=1
            )
            version_frame.pack(fill="x", pady=5, padx=5)
            
            # Version info
            info_frame = tk.Frame(version_frame, bg=self.colors.bg_secondary)
            info_frame.pack(side="left", padx=15, pady=10)
            
            tk.Label(
                info_frame,
                text=version["id"],
                font=("Arial", 12, "bold"),
                bg=self.colors.bg_secondary,
                fg=self.colors.text_primary
            ).pack(anchor="w")
            
            tk.Label(
                info_frame,
                text=f"Type: {version['type']} | Released: {version['releaseTime'][:10]}",
                font=("Arial", 9),
                bg=self.colors.bg_secondary,
                fg=self.colors.text_secondary
            ).pack(anchor="w")
            
            # Install button
            install_btn = tk.Button(
                version_frame,
                text="Install",
                font=("Arial", 10),
                bg=self.colors.accent_primary,
                fg="white",
                relief="flat",
                padx=20,
                pady=5,
                cursor="hand2",
                command=lambda v=version["id"]: self.install_version(v)
            )
            install_btn.pack(side="right", padx=15)
    
    def show_profiles(self):
        """Show profiles management page"""
        self.clear_main_frame()
        
        tk.Label(
            self.main_frame,
            text="Profiles Management",
            font=("Arial", 18, "bold"),
            bg=self.colors.bg_primary,
            fg=self.colors.text_primary
        ).pack(pady=20)
        
        # Add profile button
        tk.Button(
            self.main_frame,
            text="+ New Profile",
            font=("Arial", 11),
            bg=self.colors.accent_primary,
            fg="white",
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
            command=self.create_profile_dialog
        ).pack(pady=10)
        
        # Profiles list
        profiles_frame = tk.Frame(self.main_frame, bg=self.colors.bg_primary)
        profiles_frame.pack(fill="both", expand=True, padx=40, pady=20)
        
        for name, profile in self.profile_manager.profiles.get("profiles", {}).items():
            prof_frame = tk.Frame(
                profiles_frame,
                bg=self.colors.bg_secondary,
                relief="flat",
                bd=1
            )
            prof_frame.pack(fill="x", pady=5)
            
            tk.Label(
                prof_frame,
                text=f"📁 {name}",
                font=("Arial", 11, "bold"),
                bg=self.colors.bg_secondary,
                fg=self.colors.text_primary
            ).pack(side="left", padx=15, pady=10)
            
            if self.profile_manager.profiles.get("selected") == name:
                tk.Label(
                    prof_frame,
                    text="✓ Active",
                    font=("Arial", 10),
                    bg=self.colors.bg_secondary,
                    fg=self.colors.success
                ).pack(side="left", padx=10)
            
            tk.Button(
                prof_frame,
                text="Select",
                font=("Arial", 10),
                bg=self.colors.accent_primary,
                fg="white",
                relief="flat",
                padx=15,
                pady=5,
                cursor="hand2",
                command=lambda n=name: self.select_profile(n)
            ).pack(side="right", padx=10, pady=10)
    
    def show_settings(self):
        """Show settings page"""
        self.clear_main_frame()
        
        tk.Label(
            self.main_frame,
            text="Settings",
            font=("Arial", 18, "bold"),
            bg=self.colors.bg_primary,
            fg=self.colors.text_primary
        ).pack(pady=20)
        
        settings_frame = tk.Frame(self.main_frame, bg=self.colors.bg_primary)
        settings_frame.pack(padx=40, pady=20)
        
        # Game directory
        tk.Label(
            settings_frame,
            text="Game Directory:",
            font=("Arial", 11),
            bg=self.colors.bg_primary,
            fg=self.colors.text_primary
        ).grid(row=0, column=0, sticky="w", pady=10)
        
        dir_frame = tk.Frame(settings_frame, bg=self.colors.bg_primary)
        dir_frame.grid(row=0, column=1, padx=20)
        
        self.dir_var = tk.StringVar(value=str(self.config.minecraft_dir))
        dir_entry = tk.Entry(
            dir_frame,
            textvariable=self.dir_var,
            font=("Arial", 10),
            bg=self.colors.input_bg,
            fg=self.colors.text_primary,
            width=40
        )
        dir_entry.pack(side="left")
        
        tk.Button(
            dir_frame,
            text="Browse",
            font=("Arial", 10),
            bg=self.colors.bg_secondary,
            fg=self.colors.text_primary,
            relief="flat",
            padx=10,
            command=self.browse_directory
        ).pack(side="left", padx=5)
        
        # Java arguments
        tk.Label(
            settings_frame,
            text="JVM Arguments:",
            font=("Arial", 11),
            bg=self.colors.bg_primary,
            fg=self.colors.text_primary
        ).grid(row=1, column=0, sticky="w", pady=10)
        
        self.java_args_text = tk.Text(
            settings_frame,
            font=("Arial", 10),
            bg=self.colors.input_bg,
            fg=self.colors.text_primary,
            height=3,
            width=50
        )
        self.java_args_text.grid(row=1, column=1, padx=20)
        self.java_args_text.insert("1.0", self.config.java_args)
        
        # Save button
        tk.Button(
            settings_frame,
            text="Save Settings",
            font=("Arial", 11),
            bg=self.colors.accent_primary,
            fg="white",
            relief="flat",
            padx=25,
            pady=8,
            cursor="hand2",
            command=self.save_settings
        ).grid(row=2, column=1, pady=20)
    
    def show_mods(self):
        """Show mods page"""
        self.clear_main_frame()
        
        tk.Label(
            self.main_frame,
            text="Mods Manager",
            font=("Arial", 18, "bold"),
            bg=self.colors.bg_primary,
            fg=self.colors.text_primary
        ).pack(pady=20)
        
        tk.Label(
            self.main_frame,
            text="Manage your Minecraft mods here",
            font=("Arial", 11),
            bg=self.colors.bg_primary,
            fg=self.colors.text_secondary
        ).pack(pady=10)
        
        # Mods directory button
        tk.Button(
            self.main_frame,
            text="📁 Open Mods Folder",
            font=("Arial", 11),
            bg=self.colors.bg_secondary,
            fg=self.colors.text_primary,
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2",
            command=lambda: self.open_folder(self.config.minecraft_dir / "mods")
        ).pack(pady=20)
    
    def show_servers(self):
        """Show servers page"""
        self.clear_main_frame()
        
        tk.Label(
            self.main_frame,
            text="Server List",
            font=("Arial", 18, "bold"),
            bg=self.colors.bg_primary,
            fg=self.colors.text_primary
        ).pack(pady=20)
        
        # Popular servers
        servers = [
            ("Hypixel", "mc.hypixel.net"),
            ("Mineplex", "mineplex.com"),
            ("2b2t", "2b2t.org"),
            ("Cubecraft", "play.cubecraft.net"),
            ("Minehut", "minehut.com")
        ]
        
        servers_frame = tk.Frame(self.main_frame, bg=self.colors.bg_primary)
        servers_frame.pack(padx=40, pady=20)
        
        for name, ip in servers:
            server_frame = tk.Frame(
                servers_frame,
                bg=self.colors.bg_secondary,
                relief="flat",
                bd=1
            )
            server_frame.pack(fill="x", pady=5)
            
            tk.Label(
                server_frame,
                text=f"🌐 {name}",
                font=("Arial", 12, "bold"),
                bg=self.colors.bg_secondary,
                fg=self.colors.text_primary
            ).pack(side="left", padx=15, pady=10)
            
            tk.Label(
                server_frame,
                text=ip,
                font=("Arial", 10),
                bg=self.colors.bg_secondary,
                fg=self.colors.text_secondary
            ).pack(side="left", padx=10)
            
            tk.Button(
                server_frame,
                text="Copy IP",
                font=("Arial", 10),
                bg=self.colors.accent_primary,
                fg="white",
                relief="flat",
                padx=15,
                pady=5,
                cursor="hand2",
                command=lambda i=ip: self.copy_to_clipboard(i)
            ).pack(side="right", padx=10, pady=10)
    
    def show_news(self):
        """Show news page"""
        self.clear_main_frame()
        
        tk.Label(
            self.main_frame,
            text="Minecraft News",
            font=("Arial", 18, "bold"),
            bg=self.colors.bg_primary,
            fg=self.colors.text_primary
        ).pack(pady=20)
        
        # Sample news
        news_items = [
            {
                "title": "Minecraft 1.20.4 Released!",
                "date": "2024-01-15",
                "content": "New features including armadillos and wolf armor!"
            },
            {
                "title": "Minecraft Live 2024 Announced",
                "date": "2024-01-10",
                "content": "Join us for the biggest Minecraft event of the year"
            },
            {
                "title": "New Snapshot Available",
                "date": "2024-01-08",
                "content": "Test the latest features in snapshot 24w02a"
            }
        ]
        
        news_frame = tk.Frame(self.main_frame, bg=self.colors.bg_primary)
        news_frame.pack(fill="both", expand=True, padx=40, pady=20)
        
        for item in news_items:
            article = tk.Frame(
                news_frame,
                bg=self.colors.bg_secondary,
                relief="flat",
                bd=1
            )
            article.pack(fill="x", pady=10)
            
            tk.Label(
                article,
                text=item["title"],
                font=("Arial", 13, "bold"),
                bg=self.colors.bg_secondary,
                fg=self.colors.text_primary
            ).pack(anchor="w", padx=15, pady=(10, 5))
            
            tk.Label(
                article,
                text=item["date"],
                font=("Arial", 9),
                bg=self.colors.bg_secondary,
                fg=self.colors.text_secondary
            ).pack(anchor="w", padx=15)
            
            tk.Label(
                article,
                text=item["content"],
                font=("Arial", 10),
                bg=self.colors.bg_secondary,
                fg=self.colors.text_primary
            ).pack(anchor="w", padx=15, pady=(5, 10))
    
    def clear_main_frame(self):
        """Clear main frame content"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()
    
    def load_data(self):
        """Load initial data"""
        # Load available versions
        versions = self.version_manager.get_versions("release")
        version_ids = [v["id"] for v in versions[:50]]  # Show first 50
        self.version_combo['values'] = version_ids
        
        if version_ids:
            self.version_combo.set(version_ids[0])
    
    def launch_game(self):
        """Launch Minecraft"""
        version = self.version_var.get()
        username = self.username_var.get() or "Player"
        ram = self.ram_var.get()
        
        if not version:
            messagebox.showwarning("Warning", "Please select a Minecraft version")
            return
        
        # Check if version is installed
        version_dir = self.version_manager.versions_dir / version
        if not version_dir.exists():
            response = messagebox.askyesno(
                "Version Not Installed",
                f"Version {version} is not installed. Download it now?"
            )
            if response:
                self.install_version(version)
            return
        
        # Show progress
        self.play_button.pack_forget()
        self.progress_bar.pack(side="right", padx=30, pady=25)
        self.progress_label.pack(side="right", padx=10)
        
        # Launch in thread
        thread = threading.Thread(
            target=self._launch_minecraft,
            args=(version, username, ram)
        )
        thread.daemon = True
        thread.start()
    
    def _launch_minecraft(self, version: str, username: str, ram: str):
        """Internal method to launch Minecraft"""
        try:
            self.update_progress("Preparing launch...", 20)
            
            # Build launch command
            java_path = "java"  # Assume Java is in PATH
            version_jar = self.version_manager.versions_dir / version / f"{version}.jar"
            
            # Basic launch command (simplified)
            command = [
                java_path,
                f"-Xmx{ram}",
                f"-Xms{self.config.min_ram}M",
                "-jar",
                str(version_jar),
                "--username", username,
                "--version", version,
                "--gameDir", str(self.config.minecraft_dir)
            ]
            
            self.update_progress("Launching Minecraft...", 80)
            
            # Launch the game
            subprocess.Popen(command)
            
            self.update_progress("Minecraft launched!", 100)
            time.sleep(2)
            
            # Reset UI
            self.after(0, self.reset_launch_ui)
            
        except Exception as e:
            messagebox.showerror("Launch Error", f"Failed to launch Minecraft:\n{e}")
            self.after(0, self.reset_launch_ui)
    
    def reset_launch_ui(self):
        """Reset launch UI after game starts"""
        self.progress_bar.pack_forget()
        self.progress_label.pack_forget()
        self.play_button.pack(side="right", padx=30)
        self.progress_var.set(0)
    
    def update_progress(self, message: str, value: float):
        """Update progress bar and label"""
        self.after(0, lambda: self.progress_label.config(text=message))
        self.after(0, lambda: self.progress_var.set(value))
    
    def install_version(self, version_id: str):
        """Install a Minecraft version"""
        # Show progress dialog
        dialog = tk.Toplevel(self)
        dialog.title(f"Installing {version_id}")
        dialog.geometry("400x150")
        dialog.configure(bg=self.colors.bg_secondary)
        dialog.transient(self)
        dialog.grab_set()
        
        tk.Label(
            dialog,
            text=f"Installing Minecraft {version_id}",
            font=("Arial", 12, "bold"),
            bg=self.colors.bg_secondary,
            fg=self.colors.text_primary
        ).pack(pady=20)
        
        progress_label = tk.Label(
            dialog,
            text="Preparing...",
            font=("Arial", 10),
            bg=self.colors.bg_secondary,
            fg=self.colors.text_secondary
        )
        progress_label.pack()
        
        progress = ttk.Progressbar(
            dialog,
            length=300,
            mode="indeterminate"
        )
        progress.pack(pady=20)
        progress.start()
        
        def download():
            def update_status(msg, prog):
                progress_label.config(text=msg)
            
            success = self.version_manager.download_version(version_id, update_status)
            
            if success:
                messagebox.showinfo("Success", f"Version {version_id} installed successfully!")
            else:
                messagebox.showerror("Error", f"Failed to install version {version_id}")
            
            dialog.destroy()
        
        thread = threading.Thread(target=download)
        thread.daemon = True
        thread.start()
    
    def show_account_dialog(self):
        """Show account management dialog"""
        dialog = tk.Toplevel(self)
        dialog.title("Account Settings")
        dialog.geometry("400x300")
        dialog.configure(bg=self.colors.bg_secondary)
        dialog.transient(self)
        
        tk.Label(
            dialog,
            text="Account Management",
            font=("Arial", 14, "bold"),
            bg=self.colors.bg_secondary,
            fg=self.colors.text_primary
        ).pack(pady=20)
        
        # Account type selection
        tk.Label(
            dialog,
            text="Account Type:",
            font=("Arial", 11),
            bg=self.colors.bg_secondary,
            fg=self.colors.text_primary
        ).pack(pady=10)
        
        account_types = ["Offline", "Microsoft", "Mojang (Legacy)"]
        account_var = tk.StringVar(value="Offline")
        
        for acc_type in account_types:
            tk.Radiobutton(
                dialog,
                text=acc_type,
                variable=account_var,
                value=acc_type,
                font=("Arial", 10),
                bg=self.colors.bg_secondary,
                fg=self.colors.text_primary,
                selectcolor=self.colors.bg_secondary
            ).pack()
        
        tk.Button(
            dialog,
            text="Save",
            font=("Arial", 11),
            bg=self.colors.accent_primary,
            fg="white",
            relief="flat",
            padx=30,
            pady=8,
            command=dialog.destroy
        ).pack(pady=30)
    
    def create_profile_dialog(self):
        """Create new profile dialog"""
        dialog = tk.Toplevel(self)
        dialog.title("Create Profile")
        dialog.geometry("400x250")
        dialog.configure(bg=self.colors.bg_secondary)
        dialog.transient(self)
        
        tk.Label(
            dialog,
            text="Create New Profile",
            font=("Arial", 14, "bold"),
            bg=self.colors.bg_secondary,
            fg=self.colors.text_primary
        ).pack(pady=20)
        
        # Profile name
        tk.Label(
            dialog,
            text="Profile Name:",
            font=("Arial", 11),
            bg=self.colors.bg_secondary,
            fg=self.colors.text_primary
        ).pack()
        
        name_var = tk.StringVar()
        tk.Entry(
            dialog,
            textvariable=name_var,
            font=("Arial", 11),
            bg=self.colors.input_bg,
            fg=self.colors.text_primary,
            width=30
        ).pack(pady=10)
        
        # Version selection
        tk.Label(
            dialog,
            text="Game Version:",
            font=("Arial", 11),
            bg=self.colors.bg_secondary,
            fg=self.colors.text_primary
        ).pack()
        
        version_var = tk.StringVar()
        version_combo = ttk.Combobox(
            dialog,
            textvariable=version_var,
            font=("Arial", 10),
            width=28,
            state="readonly"
        )
        version_combo['values'] = self.version_combo['values']
        version_combo.pack(pady=10)
        
        def create():
            name = name_var.get().strip()
            version = version_var.get()
            
            if name and version:
                self.profile_manager.add_profile(name, {"version": version})
                messagebox.showinfo("Success", f"Profile '{name}' created!")
                dialog.destroy()
                self.show_profiles()
            else:
                messagebox.showwarning("Warning", "Please fill all fields")
        
        tk.Button(
            dialog,
            text="Create Profile",
            font=("Arial", 11),
            bg=self.colors.accent_primary,
            fg="white",
            relief="flat",
            padx=30,
            pady=8,
            command=create
        ).pack(pady=30)
    
    def select_profile(self, name: str):
        """Select a profile"""
        self.profile_manager.set_selected(name)
        self.show_profiles()
    
    def filter_versions(self, filter_type: str):
        """Filter versions list"""
        versions = self.version_manager.get_versions(filter_type)
        # Update the versions display
        self.show_versions()
    
    def browse_directory(self):
        """Browse for game directory"""
        directory = filedialog.askdirectory(
            title="Select Minecraft Directory",
            initialdir=self.config.minecraft_dir
        )
        if directory:
            self.dir_var.set(directory)
    
    def save_settings(self):
        """Save launcher settings"""
        self.config.minecraft_dir = Path(self.dir_var.get())
        self.config.java_args = self.java_args_text.get("1.0", "end-1c")
        messagebox.showinfo("Success", "Settings saved successfully!")
    
    def open_folder(self, path: Path):
        """Open folder in file explorer"""
        path.mkdir(parents=True, exist_ok=True)
        
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    
    def copy_to_clipboard(self, text: str):
        """Copy text to clipboard"""
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("Copied", f"'{text}' copied to clipboard!")

# ==================== Main Entry Point ====================

def main():
    """Main entry point"""
    try:
        # Check for required packages
        required = ["tkinter", "PIL", "requests"]
        missing = []
        
        for package in required:
            try:
                __import__(package)
            except ImportError:
                missing.append(package)
        
        if missing:
            print(f"⚠️  Missing required packages: {', '.join(missing)}")
            print("📦 Install with: pip install pillow requests")
            return
        
        # Create and run launcher
        app = TLauncherUI()
        
        # Set window icon if available
        try:
            if platform.system() == "Windows":
                app.iconbitmap("icon.ico")
        except:
            pass
        
        # Start main loop
        app.mainloop()
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("🎮 PyLauncher - Minecraft Launcher (TLauncher Style)")
    print("=" * 60)
    print("Version: 1.0.0")
    print("Author: FlamesCo Labs")
    print("License: GPL-3.0")
    print("=" * 60)
    print()
    main()
