#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Samsoft OS Compiler 0.2 – Embedded WSL2 Libdragon Environment (Single-file)
©2025 Samsoft / Cat-san

This single-file desktop provides:
- HEX Editor (open/edit/save space-separated hex bytes)
- LEVEL Editor (grid painter with JSON save/load)
- WSL/UltraSim Terminal (streams output; supports batch "Setup Libdragon")

Notes:
- On Windows with WSL, commands are run via `wsl.exe bash -lc "<cmd>"`.
- On macOS/Linux or Windows without WSL, shell commands run locally (bash if available).
- No external dependencies beyond Python's standard library.
"""

import os
import sys
import json
import queue
import shutil
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, colorchooser

APP_TITLE = "Samsoft OS Compiler 0.2"
PIX_FONT = ("Courier", 12, "bold")
MONO_FONT = ("Consolas" if os.name == "nt" else "Menlo", 10)
BG_COLOR = "#002E5A"
BTN_BG = "#1E4A8F"
BTN_FG = "#CAD9ED"

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def is_windows() -> bool:
    return os.name == "nt"

def has_wsl() -> bool:
    """Detect whether wsl.exe exists and at least one distro is registered."""
    if not is_windows():
        return False
    wsl_path = shutil.which("wsl.exe") or shutil.which("wsl")
    if not wsl_path:
        return False
    try:
        # Quiet list of distros returns non-empty output when at least one exists
        r = subprocess.run([wsl_path, "-l", "-q"], capture_output=True, text=True, timeout=5)
        return r.returncode == 0 and r.stdout.strip() != ""
    except Exception:
        return False

def which_bash_local() -> str:
    """Best-effort local bash, otherwise return system shell."""
    bash = shutil.which("bash")
    if bash:
        return bash
    # Fallback to cmd on Windows or /bin/sh elsewhere
    return "cmd" if is_windows() else (shutil.which("sh") or "/bin/sh")

# ---------------------------------------------------------------------------
# Threaded command runner (streams output safely to Tk)
# ---------------------------------------------------------------------------

class CommandRunner(threading.Thread):
    def __init__(self, args, on_line, on_exit):
        super().__init__(daemon=True)
        self.args = args
        self.on_line = on_line
        self.on_exit = on_exit
        self.proc = None
        self._stop = threading.Event()

    def run(self):
        try:
            self.proc = subprocess.Popen(
                self.args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=True
            )
        except Exception as e:
            self.on_line(f"[launcher error] {e}")
            self.on_exit(1)
            return

        try:
            for line in self.proc.stdout:
                if self._stop.is_set():
                    break
                self.on_line(line.rstrip("\n"))
        except Exception as e:
            self.on_line(f"[read error] {e}")

        rc = 0
        try:
            rc = self.proc.wait()
        except Exception:
            rc = 1
        self.on_exit(rc)

    def stop(self):
        self._stop.set()
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.terminate()
            except Exception:
                pass

# ---------------------------------------------------------------------------
# Simple Hex Editor
# ---------------------------------------------------------------------------

class HexEditor(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Samsoft HEX Editor")
        self.geometry("900x640")
        self.configure(bg=BG_COLOR)
        self._path = None

        # Toolbar
        bar = tk.Frame(self, bg=BG_COLOR)
        bar.pack(fill="x")
        for label, cmd in [
            ("Open", self.open_file),
            ("Save", self.save_file),
            ("Save As", self.save_file_as),
            ("Validate", self.validate_hex),
            ("Clear", self.clear_text),
        ]:
            tk.Button(bar, text=label, font=("Arial", 10, "bold"),
                      bg=BTN_BG, fg=BTN_FG, command=cmd, padx=10, pady=4).pack(side="left", padx=4, pady=6)

        # Editor
        self.text = scrolledtext.ScrolledText(
            self, wrap="none", font=("Courier", 11),
            bg="#0D1B2A", fg="#00FFAA", insertbackground="white", undo=True
        )
        self.text.pack(fill="both", expand=True)

        # Status
        self.status = tk.Label(self, text="Open a file or paste hex bytes (e.g., '4E 45 53 1A')",
                               anchor="w", bg="#051C33", fg="#9BC2E6")
        self.status.pack(fill="x")

        # Menu
        menu = tk.Menu(self)
        m_file = tk.Menu(menu, tearoff=0)
        m_file.add_command(label="Open...", command=self.open_file, accelerator="Ctrl+O")
        m_file.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        m_file.add_command(label="Save As...", command=self.save_file_as)
        m_file.add_separator()
        m_file.add_command(label="Close", command=self.destroy, accelerator="Ctrl+W")
        menu.add_cascade(label="File", menu=m_file)
        self.config(menu=menu)

        # Shortcuts
        self.bind("<Control-o>", lambda e: self.open_file())
        self.bind("<Control-s>", lambda e: self.save_file())
        self.bind("<Control-w>", lambda e: self.destroy())

    def set_status(self, msg):
        self.status.config(text=msg)

    def clear_text(self):
        self.text.delete("1.0", tk.END)
        self._path = None
        self.set_status("Cleared editor.")

    def open_file(self):
        path = filedialog.askopenfilename(title="Open file")
        if not path:
            return
        try:
            with open(path, "rb") as f:
                data = f.read()
            # Show as space-separated hex bytes
            hex_str = " ".join(f"{b:02X}" for b in data)
            self.text.delete("1.0", tk.END)
            self.text.insert("1.0", hex_str)
            self._path = path
            self.set_status(f"Loaded {len(data)} bytes from {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Open failed", str(e))

    def _bytes_from_text(self):
        raw = self.text.get("1.0", tk.END).strip()
        if not raw:
            return b""
        tokens = raw.replace("\n", " ").replace("\t", " ").split()
        data = bytearray()
        for i, t in enumerate(tokens, 1):
            t = t.strip()
            if len(t) != 2:
                raise ValueError(f"Invalid token #{i}: '{t}' (must be 2 hex chars)")
            try:
                data.append(int(t, 16))
            except Exception:
                raise ValueError(f"Invalid hex token #{i}: '{t}'")
        return bytes(data)

    def validate_hex(self):
        try:
            data = self._bytes_from_text()
            self.set_status(f"Valid hex: {len(data)} bytes.")
        except Exception as e:
            messagebox.showerror("Validation error", str(e))

    def save_file(self):
        if not self._path:
            return self.save_file_as()
        try:
            data = self._bytes_from_text()
            with open(self._path, "wb") as f:
                f.write(data)
            self.set_status(f"Saved {len(data)} bytes to {os.path.basename(self._path)}")
            messagebox.showinfo("Saved", "File saved successfully.")
        except Exception as e:
            messagebox.showerror("Save failed", str(e))

    def save_file_as(self):
        path = filedialog.asksaveasfilename(defaultextension=".bin",
                                            filetypes=[("Binary", "*.bin"), ("All files", "*.*")])
        if not path:
            return
        self._path = path
        self.save_file()

# ---------------------------------------------------------------------------
# Level Editor (grid painter with JSON save/load)
# ---------------------------------------------------------------------------

class LevelEditor(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Samsoft LEVEL Editor")
        self.geometry("800x600")
        self.configure(bg="#101820")

        self.tile_size = 32
        self.color = "#00BFFF"
        self.tiles = {}   # (x, y) -> canvas rectangle id

        # Toolbar
        bar = tk.Frame(self, bg="#0C1218")
        bar.pack(fill="x")
        tk.Button(bar, text="New", bg=BTN_BG, fg=BTN_FG, command=self.clear, padx=10, pady=4).pack(side="left", padx=4, pady=6)
        tk.Button(bar, text="Save Map", bg=BTN_BG, fg=BTN_FG, command=self.save_map, padx=10, pady=4).pack(side="left", padx=4)
        tk.Button(bar, text="Load Map", bg=BTN_BG, fg=BTN_FG, command=self.load_map, padx=10, pady=4).pack(side="left", padx=4)
        tk.Button(bar, text="Pick Color", bg=BTN_BG, fg=BTN_FG, command=self.pick_color, padx=10, pady=4).pack(side="left", padx=4)
        self.info = tk.Label(bar, text="LMB: paint | RMB: erase | Tile: 32x32", bg="#0C1218", fg="#9BC2E6")
        self.info.pack(side="right", padx=10)

        # Canvas
        self.canvas = tk.Canvas(self, width=768, height=512, bg="#101820", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.paint_tile)
        self.canvas.bind("<B1-Motion>", self.paint_tile)
        self.canvas.bind("<Button-3>", self.erase_tile)
        self.canvas.bind("<B3-Motion>", self.erase_tile)
        self.canvas.bind("<Motion>", self._hover)
        self._hover_label = tk.Label(self, text="", anchor="w", bg="#0C1218", fg="#9BC2E6")
        self._hover_label.pack(fill="x")

        self._draw_grid()

    def _draw_grid(self):
        self.canvas.delete("grid")
        w = int(self.canvas.cget("width"))
        h = int(self.canvas.cget("height"))
        for x in range(0, w, self.tile_size):
            self.canvas.create_line(x, 0, x, h, fill="#243447", tags="grid")
        for y in range(0, h, self.tile_size):
            self.canvas.create_line(0, y, w, y, fill="#243447", tags="grid")

    def _tile_coords(self, event):
        x = (event.x // self.tile_size) * self.tile_size
        y = (event.y // self.tile_size) * self.tile_size
        return x, y

    def paint_tile(self, event):
        x, y = self._tile_coords(event)
        key = (x, y)
        if key in self.tiles:
            # recolor existing
            self.canvas.itemconfig(self.tiles[key], fill=self.color)
            return
        rect = self.canvas.create_rectangle(
            x, y, x+self.tile_size, y+self.tile_size,
            fill=self.color, outline="", tags="tile"
        )
        self.tiles[key] = rect

    def erase_tile(self, event):
        x, y = self._tile_coords(event)
        key = (x, y)
        if key in list(self.tiles.keys()):
            self.canvas.delete(self.tiles[key])
            del self.tiles[key]

    def pick_color(self):
        c = colorchooser.askcolor(initialcolor=self.color, title="Pick Tile Color")
        if c and c[1]:
            self.color = c[1]

    def clear(self):
        for rid in list(self.tiles.values()):
            self.canvas.delete(rid)
        self.tiles.clear()

    def save_map(self):
        path = filedialog.asksaveasfilename(defaultextension=".json",
                                            filetypes=[("Level JSON", "*.json"), ("All files", "*.*")])
        if not path:
            return
        data = {
            "tile_size": self.tile_size,
            "tiles": [{"x": x, "y": y, "color": self.canvas.itemcget(rid, "fill")}
                      for (x, y), rid in self.tiles.items()]
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            messagebox.showinfo("Saved", f"Saved {len(data['tiles'])} tiles.")
        except Exception as e:
            messagebox.showerror("Save failed", str(e))

    def load_map(self):
        path = filedialog.askopenfilename(filetypes=[("Level JSON", "*.json"), ("All files", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.clear()
            self.tile_size = int(data.get("tile_size", 32)) or 32
            for t in data.get("tiles", []):
                x, y = int(t["x"]), int(t["y"])
                color = t.get("color", "#00BFFF")
                rect = self.canvas.create_rectangle(
                    x, y, x+self.tile_size, y+self.tile_size,
                    fill=color, outline="", tags="tile"
                )
                self.tiles[(x, y)] = rect
            self._draw_grid()
            messagebox.showinfo("Loaded", f"Loaded {len(self.tiles)} tiles.")
        except Exception as e:
            messagebox.showerror("Load failed", str(e))

    def _hover(self, event):
        x, y = self._tile_coords(event)
        self._hover_label.config(text=f"Cursor tile: ({x//self.tile_size}, {y//self.tile_size})  px=({x},{y})")

# ---------------------------------------------------------------------------
# WSL / UltraSim Terminal
# ---------------------------------------------------------------------------

class WSLConsole(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Samsoft WSL2 / UltraSim Terminal")
        self.geometry("1000x650")
        self.configure(bg="#001830")

        self.output = scrolledtext.ScrolledText(
            self, bg="#001830", fg="#00FFAA",
            font=MONO_FONT, insertbackground="white"
        )
        self.output.pack(fill="both", expand=True)

        cmd_row = tk.Frame(self, bg="#001830")
        cmd_row.pack(fill="x")
        self.cmd_entry = tk.Entry(cmd_row, font=MONO_FONT, bg="#112244", fg="white")
        self.cmd_entry.pack(side="left", fill="x", expand=True, padx=4, pady=4)
        self.cmd_entry.bind("<Return>", self.run_command)

        tk.Button(cmd_row, text="Run", bg=BTN_BG, fg=BTN_FG, command=self.run_command, padx=12).pack(side="left", padx=4)
        tk.Button(cmd_row, text="Stop", bg="#6B2C2C", fg="#FFDCDC", command=self.stop_command, padx=12).pack(side="left", padx=4)
        tk.Button(cmd_row, text="Setup Libdragon", bg=BTN_BG, fg=BTN_FG, command=self.setup_libdragon).pack(side="left", padx=4)

        # Status bar
        self.status = tk.Label(self, text="", anchor="w", bg="#051C33", fg="#9BC2E6")
        self.status.pack(fill="x")

        self.runner = None
        self._print_banner()

    # --- helpers

    def append_line(self, text: str):
        """Thread-safe append to output."""
        self.output.after(0, lambda: (self.output.insert(tk.END, text + "\n"), self.output.see(tk.END)))

    def set_status(self, msg: str):
        self.status.config(text=msg)

    def _print_banner(self):
        if is_windows() and has_wsl():
            self.append_line("Detected Windows + WSL. Commands will run inside WSL (bash -lc).")
        elif is_windows():
            self.append_line("Windows detected, but WSL not found. Falling back to local shell.")
        else:
            self.append_line("Non-Windows OS detected. Using local shell (bash if available).")
        self.append_line("Tip: press Enter to run. 'Stop' terminates the running process.\n")

    def _shell_args_for(self, cmd: str):
        """Build subprocess args for target shell (WSL if present, else local)."""
        if is_windows() and has_wsl():
            wsl = shutil.which("wsl.exe") or "wsl"
            return [wsl, "bash", "-lc", cmd]
        # Local
        sh = which_bash_local()
        if os.path.basename(sh).lower() == "cmd":
            # cmd.exe /c "cmd"
            return [sh, "/c", cmd]
        else:
            return [sh, "-lc", cmd]

    # --- command lifecycle

    def run_command(self, event=None):
        cmd = self.cmd_entry.get().strip()
        if not cmd:
            return
        if self.runner and self.runner.is_alive():
            messagebox.showwarning("Busy", "A command is already running. Stop it before starting another.")
            return
        self.append_line(f"> {cmd}")
        args = self._shell_args_for(cmd)

        def on_line(line):  # from worker thread
            self.append_line(line)

        def on_exit(rc):
            self.append_line(f"[process exited with code {rc}]")
            self.set_status("Idle")

        self.set_status("Running...")
        self.runner = CommandRunner(args, on_line, on_exit)
        self.runner.start()
        self.cmd_entry.delete(0, tk.END)

    def stop_command(self):
        if self.runner and self.runner.is_alive():
            self.runner.stop()
            self.append_line("[termination requested]")

    # --- batch setup for libdragon (best-effort, non-interactive sudo first)

    def setup_libdragon(self):
        if not (is_windows() and has_wsl()):
            messagebox.showinfo("Unavailable", "Libdragon setup requires Windows + WSL.")
            return

        cmds = [
            # Show environment
            "uname -a",
            'echo "Home: $HOME  Distro: $(grep ^NAME= /etc/os-release | cut -d\\" -f2)"',
            # Non-interactive apt to avoid blocking if sudo prompts. If this fails, user should run manually.
            "if command -v sudo >/dev/null; then sudo -n apt-get update || echo '[sudo password required: run manually]'; else apt-get update; fi",
            "if command -v sudo >/dev/null; then sudo -n apt-get install -y build-essential git wget || echo '[sudo password required: run manually]'; else apt-get install -y build-essential git wget; fi",
            # Toolchain package (from libdragon releases)
            "mkdir -p /tmp && wget -O /tmp/toolchain.deb https://github.com/DragonMinded/libdragon/releases/download/toolchain-continuous-prerelease/gcc-toolchain-mips64-x86_64.deb || echo '[wget failed]'",
            "if command -v sudo >/dev/null; then sudo -n dpkg -i /tmp/toolchain.deb || echo '[sudo password required for dpkg: run manually]'; else dpkg -i /tmp/toolchain.deb; fi",
            "rm -f /tmp/toolchain.deb || true",
            # Clone and build libdragon
            "git clone https://github.com/DragonMinded/libdragon.git $HOME/libdragon || true",
            "cd $HOME/libdragon && ./build.sh || echo '[build.sh failed]'",
            # Presence check
            'test -d /opt/libdragon && echo "✅ /opt/libdragon present" || echo "⚠️  /opt/libdragon missing (requires sudo)"'
        ]
        batch = " && ".join(cmds)
        self.cmd_entry.delete(0, tk.END)
        self.cmd_entry.insert(0, batch)
        self.run_command()

# ---------------------------------------------------------------------------
# Main Samsoft OS Desktop
# ---------------------------------------------------------------------------

class SamsoftOSCompiler(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1100x750")
        self.configure(bg=BG_COLOR)
        self._build_menu()
        self._build_desktop()
        self._build_status()

        # DPI awareness hint (Windows)
        try:
            if is_windows():
                import ctypes
                ctypes.windll.shcore.SetProcessDpiAwareness(1)  # PER_MONITOR_AWARE
        except Exception:
            pass

    # --- UI construction

    def _build_menu(self):
        menu = tk.Menu(self)

        m_file = tk.Menu(menu, tearoff=0)
        m_file.add_command(label="Hex Editor", command=self.open_hex_editor, accelerator="Ctrl+H")
        m_file.add_command(label="Level Editor", command=self.open_level_editor, accelerator="Ctrl+L")
        m_file.add_command(label="Terminal (WSL/UltraSim)", command=self.launch_emulator, accelerator="Ctrl+T")
        m_file.add_separator()
        m_file.add_command(label="Exit", command=self.quit, accelerator="Ctrl+Q")
        menu.add_cascade(label="File", menu=m_file)

        m_help = tk.Menu(menu, tearoff=0)
        m_help.add_command(label="About", command=self.show_about)
        menu.add_cascade(label="Help", menu=m_help)

        self.config(menu=menu)

        # Shortcuts
        self.bind("<Control-h>", lambda e: self.open_hex_editor())
        self.bind("<Control-l>", lambda e: self.open_level_editor())
        self.bind("<Control-t>", lambda e: self.launch_emulator())
        self.bind("<Control-q>", lambda e: self.quit())

    def _build_desktop(self):
        # Left-side launcher buttons
        buttons = [
            ("HEX EDIT", self.open_hex_editor, 120),
            ("LEVEL EDIT", self.open_level_editor, 230),
            ("TERMINAL", self.launch_emulator, 340),
        ]
        for label, cmd, y in buttons:
            btn = tk.Button(
                self, text=label, font=PIX_FONT, bg=BTN_BG, fg=BTN_FG,
                width=12, height=3, command=cmd, relief="raised", bd=2, activebackground="#2C63B7"
            )
            btn.place(x=50, y=y)

        # Center welcome text
        title = tk.Label(self, text="SAMSOFT ULTRA DESKTOP", fg="#E8EFFA", bg=BG_COLOR, font=("Arial", 20, "bold"))
        title.place(relx=0.5, y=80, anchor="center")
        sub = tk.Label(self,
                       text="Hex Editing • Level Painting • WSL/UltraSim Terminal",
                       fg="#BFD4F2", bg=BG_COLOR, font=("Arial", 12))
        sub.place(relx=0.5, y=110, anchor="center")

        # Info panel
        panel = tk.Frame(self, bg="#012342", bd=1, relief="solid")
        panel.place(relx=0.5, rely=0.5, anchor="center", width=650, height=280)

        msg = (
            "• HEX Editor: Open a file → Edit as space-separated hex → Save.\n"
            "• LEVEL Editor: Paint tiles (LMB) / Erase (RMB). Save/Load as JSON.\n"
            "• TERMINAL: Run commands. On Windows+WSL, commands run inside WSL.\n"
            "  Use 'Setup Libdragon' for a best‑effort toolchain install.\n\n"
            "Tip: Ctrl+H / Ctrl+L / Ctrl+T to open tools quickly."
        )
        tk.Label(panel, text=msg, bg="#012342", fg="#9BC2E6",
                 font=("Arial", 11), justify="left").pack(padx=16, pady=16, anchor="w")

    def _build_status(self):
        self.status = tk.Label(self, text="Ready", anchor="w", bg="#051C33", fg="#9BC2E6")
        self.status.pack(side="bottom", fill="x")

    # --- commands

    def open_hex_editor(self):
        HexEditor(self)
        self.status.config(text="Opened HEX Editor")

    def open_level_editor(self):
        LevelEditor(self)
        self.status.config(text="Opened LEVEL Editor")

    def launch_emulator(self):
        WSLConsole(self)
        self.status.config(text="Opened WSL/UltraSim Terminal")

    def show_about(self):
        about = tk.Toplevel(self)
        about.title("About UltraSim")
        about.configure(bg="#012342")
        tk.Label(about, text="Samsoft Ultra Simulator (UltraSim)", font=("Arial", 14, "bold"),
                 bg="#012342", fg="#E8EFFA").pack(padx=16, pady=(16, 6))
        summary = (
            "UltraSim is a modern reconstruction of the 1995 SGI/N64 co‑simulation environment, "
            "rebuilt by Samsoft for archival preservation and education. It pairs a procedural "
            "debugging layer with real‑time visualization to approximate SGI prototype timing "
            "for legacy ROM validation and engine research."
        )
        tk.Label(about, text=summary, wraplength=520, justify="left", bg="#012342", fg="#BFD4F2").pack(padx=16, pady=8)

        feats = (
            "• Stop‑n‑Swap: switch memory/ROM states instantly\n"
            "• Multi‑language: C / ASM / MIPS / C++ hot‑swaps\n"
            "• Internal server: networked debugging & IPC\n"
            "• Procedural debugger: trace instructions/VRAM/co‑proc signals\n"
            "• Compatibility mode: SGI‑style timing for legacy validation"
        )
        tk.Label(about, text=feats, justify="left", bg="#012342", fg="#9BC2E6").pack(padx=16, pady=(0, 16))
        tk.Button(about, text="Close", command=about.destroy, bg=BTN_BG, fg=BTN_FG, padx=12, pady=4).pack(pady=(0, 16))

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    app = SamsoftOSCompiler()
    app.mainloop()

if __name__ == "__main__":
    main()
