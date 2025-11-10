#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cat's DS 0.1 – Nintendo DS Emulator GUI (Samsoft EmuCore 2025 style)
Core by Samsoft Studios / Cat-san
©2025 GPL-3.0-or-later — Educational Emulator Skeleton

GUI layout modified by Gemini to match user-provided screenshot.
Enhanced by Grok: Added basic ARMv4T instruction support for data processing and load/store.
"""

import sys, os, threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

# ────────────────────────────────────────────────────────────────
# Core Emulation (enhanced with basic ARM instructions)
# ────────────────────────────────────────────────────────────────

class MemoryController:
    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.data = bytearray(end - start)
    def read(self, addr, size):
        offset = addr - self.start
        if offset + size > len(self.data): return 0
        val = int.from_bytes(self.data[offset:offset+size], 'little')
        return val
    def write(self, addr, size, value):
        offset = addr - self.start
        if offset + size > len(self.data): return
        self.data[offset:offset+size] = value.to_bytes(size, 'little')

class ARMCPU:
    def __init__(self, emu, is_arm9):
        self.emu = emu
        self.is_arm9 = is_arm9
        self.registers = [0]*16
        self.cpsr = 0

    def ror(self, value, amount):
        """Rotate right for immediate encoding."""
        amount = amount % 32
        if amount == 0:
            return value
        value &= 0xFFFFFFFF
        return ((value >> amount) | (value << (32 - amount))) & 0xFFFFFFFF

    def step(self):
        pc = self.registers[15]
        instr = self.emu.read_memory(pc, 4)
        if instr == 0:
            self.registers[15] += 4
            return

        # Data Processing Instructions (bits 27-25 = 000)
        if (instr & 0x0E000000) == 0x00000000:
            i_bit = (instr >> 25) & 1
            opcode = (instr >> 21) & 0xF
            s_bit = (instr >> 20) & 1  # Ignored for now
            rn = (instr >> 16) & 0xF
            rd = (instr >> 12) & 0xF
            op1 = self.registers[rn]

            if i_bit == 1:
                # Immediate: 8-bit imm rotated right by 2 * rotate_amount
                rotate = (instr >> 8) & 0xF
                imm8 = instr & 0xFF
                op2 = self.ror(imm8, rotate * 2)
            else:
                # Register operand (simplified: use low 12 bits as immediate for now)
                op2 = instr & 0xFFF

            if opcode == 0b1101:  # MOV
                self.registers[rd] = op2
            elif opcode == 0b0100:  # ADD
                self.registers[rd] = op1 + op2
            elif opcode == 0b0010:  # SUB
                self.registers[rd] = op1 - op2
            elif opcode == 0b0000:  # AND
                self.registers[rd] = op1 & op2
            elif opcode == 0b1100:  # ORR
                self.registers[rd] = op1 | op2
            elif opcode == 0b1010:  # CMP
                diff = op1 - op2
                # Flags ignored for simplicity
                pass
            # TODO: Handle Rd == 15 (PC write: add pipeline flush)

        # Load/Store Instructions (bits 27-25 = 010, single word/byte transfer)
        elif (instr & 0x0E000000) == 0x04000000:
            i_bit = (instr >> 24) & 1
            p_bit = (instr >> 23) & 1  # Assume pre-index (1)
            u_bit = (instr >> 22) & 1  # Assume up/add (1)
            b_bit = (instr >> 21) & 1  # Assume word (0)
            l_bit = (instr >> 20) & 1  # Load (1) or Store (0)
            w_bit = 0  # Assume no writeback
            rn = (instr >> 16) & 0xF
            rd = (instr >> 12) & 0xF

            if i_bit == 1:
                offset = instr & 0xFFF
            else:
                offset = 0  # Simplified: skip register offset

            base = self.registers[rn]
            if p_bit:  # Pre-indexed
                address = base + offset if u_bit else base - offset
            else:  # Post-indexed (simplified)
                address = base

            if l_bit:  # Load
                self.registers[rd] = self.emu.read_memory(address, 4 if b_bit == 0 else 1)
                if b_bit:  # Zero-extend byte
                    self.registers[rd] &= 0xFF
            else:  # Store
                size = 4 if b_bit == 0 else 1
                value = self.registers[rd] & (0xFFFFFFFF if size == 4 else 0xFF)
                self.emu.write_memory(address, size, value)

            # TODO: Handle writeback if w_bit, PC as base/Rd

        # Branch Instructions (bits 27-25 = 101)
        elif (instr & 0x0E000000) == 0x0A000000:
            offset = instr & 0x00FFFFFF
            if offset & 0x00800000:
                offset |= 0xFF000000
            offset <<= 2
            self.registers[15] = pc + 8 + offset
            return

        # Default: NOP or unsupported
        pass

        self.registers[15] += 4

class LCD:
    def __init__(self, emu): self.emu = emu
    def update(self): pass

class CatsDS:
    def __init__(self):
        self.version = "0.1"
        self.memory_controllers = []
        self.add_memory(0x02000000, 0x02400000)
        self.add_memory(0x03000000, 0x03800000)
        self.add_memory(0x06000000, 0x06800000)
        self.arm9 = ARMCPU(self, True)
        self.arm7 = ARMCPU(self, False)
        self.lcd = LCD(self)
        self.running = False
    def add_memory(self, start, end):
        self.memory_controllers.append(MemoryController(start, end))
    def read_memory(self, addr, size):
        for mc in self.memory_controllers:
            if mc.start <= addr < mc.end:
                return mc.read(addr, size)
        return 0
    def write_memory(self, addr, size, value):
        for mc in self.memory_controllers:
            if mc.start <= addr < mc.end:
                mc.write(addr, size, value); return
    def load_rom(self, filename):
        with open(filename,'rb') as f: data=f.read()
        arm9_off=int.from_bytes(data[0x20:0x24],'little')
        arm9_entry=int.from_bytes(data[0x24:0x28],'little')
        arm9_load=int.from_bytes(data[0x28:0x2C],'little')
        arm9_size=int.from_bytes(data[0x2C:0x30],'little')
        arm7_off=int.from_bytes(data[0x30:0x34],'little')
        arm7_entry=int.from_bytes(data[0x34:0x38],'little')
        arm7_load=int.from_bytes(data[0x38:0x3C],'little')
        arm7_size=int.from_bytes(data[0x3C:0x40],'little')
        for i in range(arm9_size):
            self.write_memory(arm9_load+i,1,data[arm9_off+i])
        for i in range(arm7_size):
            self.write_memory(arm7_load+i,1,data[arm7_off+i])
        self.arm9.registers[15]=arm9_entry
        self.arm7.registers[15]=arm7_entry
    def run(self):
        self.running=True
        while self.running:
            self.arm9.step()
            self.arm7.step()
            self.lcd.update()

# ────────────────────────────────────────────────────────────────
# GUI (Samsoft EmuCore 2025 style, based on user image)
# ────────────────────────────────────────────────────────────────

class EmuGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cat's DS 0.1 – Samsoft EmuCore 2025")
        self.geometry("900x650") # Increased size
        self.configure(bg="#2E2E2E") # Dark grey background

        # --- Style Configuration ---
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        
        # Dark theme for frames and labels
        self.style.configure('.', background='#2E2E2E', foreground='white')
        self.style.configure('TFrame', background='#2E2E2E')
        self.style.configure('TLabel', background='#2E2E2E', foreground='white', font=('Arial', 10))
        self.style.configure('Header.TLabel', font=('Arial', 11, 'bold'))
        
        # Style for buttons in the left panel
        self.style.configure('Nav.TButton', 
            background='#3C3C3C', 
            foreground='white',
            font=('Arial', 10),
            bordercolor='#2E2E2E',
            lightcolor='#3C3C3C',
            darkcolor='#3C3C3C',
            padding=(10, 5)
        )
        self.style.map('Nav.TButton',
            background=[('active', '#505050'), ('disabled', '#303030')],
            foreground=[('disabled', '#777777')]
        )
        # Remove button borders for a flatter look
        self.style.layout('Nav.TButton', [
            ('Button.button', {'children': [
                ('Button.focus', {'children': [
                    ('Button.padding', {'children': [
                        ('Button.label', {'sticky': 'nswe'})
                    ], 'sticky': 'nswe'})
                ], 'sticky': 'nswe'})
            ], 'sticky': 'nswe'})
        ])

        self.emu = CatsDS()
        self.thread = None

        self.create_menu()
        self.create_layout()
        self.create_statusbar()

        self.log_message("[Samsoft EmuCore 2025]")
        self.log_message(f"Cat's DS Emulation initialized (Enhanced ARMv4T support).")
        self.log_message("Ready.")


    def create_menu(self):
        menubar = tk.Menu(self, bg="#3C3C3C", fg="white", relief="flat")

        # --- File Menu ---
        file_menu = tk.Menu(menubar, tearoff=0, bg="#3C3C3C", fg="white", relief="flat")
        file_menu.add_command(label="Open ROM...", command=self.load_rom_dialog)
        file_menu.add_command(label="Recent ROMs", state="disabled")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # --- Emulation Menu ---
        run_menu = tk.Menu(menubar, tearoff=0, bg="#3C3C3C", fg="white", relief="flat")
        run_menu.add_command(label="Run", command=self.start_emulation)
        run_menu.add_command(label="Stop", command=self.stop_emulation)
        menubar.add_cascade(label="Emulation", menu=run_menu)

        # --- Other Menus (as seen in image) ---
        menubar.add_cascade(label="Debug", menu=tk.Menu(menubar, tearoff=0, bg="#3C3C3C", fg="white"))
        menubar.add_cascade(label="Tools", menu=tk.Menu(menubar, tearoff=0, bg="#3C3C3C", fg="white"))
        menubar.add_cascade(label="Help", menu=tk.Menu(menubar, tearoff=0, bg="#3C3C3C", fg="white"))

        self.config(menu=menubar)

    def create_layout(self):
        # --- Main Container ---
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1, minsize=300) # Left panel
        main_frame.grid_columnconfigure(1, weight=3) # Right panel (console)

        # --- Left Panel (Navigation & Screens) ---
        left_panel = ttk.Frame(main_frame)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_panel.grid_rowconfigure(0, weight=0) # Nav
        left_panel.grid_rowconfigure(1, weight=1) # Top Screen
        left_panel.grid_rowconfigure(2, weight=1) # Bottom Screen

        # Navigation Frame
        nav_frame = ttk.Frame(left_panel, style='TFrame')
        nav_frame.grid(row=0, column=0, sticky="new")
        nav_frame.grid_columnconfigure(0, weight=1)
        
        ttk.Button(nav_frame, text="Open ROM...", command=self.load_rom_dialog, style='Nav.TButton').grid(row=0, column=0, sticky='ew')
        ttk.Button(nav_frame, text="Recent ROMs", state="disabled", style='Nav.TButton').grid(row=1, column=0, sticky='ew')
        ttk.Button(nav_frame, text="Exit", command=self.quit, style='Nav.TButton').grid(row=2, column=0, sticky='ew')

        # Top Screen Frame
        top_screen_frame = ttk.Frame(left_panel, padding=(0, 10, 0, 5))
        top_screen_frame.grid(row=1, column=0, sticky="nsew")
        top_screen_frame.grid_rowconfigure(1, weight=1)
        top_screen_frame.grid_columnconfigure(0, weight=1)

        ttk.Label(top_screen_frame, text="Top Screen (256x192)", style='Header.TLabel').grid(row=0, column=0, sticky="w", pady=5)
        self.top_canvas = tk.Canvas(top_screen_frame, bg="black", width=256, height=192, relief="sunken", borderwidth=2, highlightthickness=0)
        self.top_canvas.grid(row=1, column=0, sticky="nsew")

        # Bottom Screen Frame
        bottom_screen_frame = ttk.Frame(left_panel, padding=(0, 5, 0, 0))
        bottom_screen_frame.grid(row=2, column=0, sticky="nsew")
        bottom_screen_frame.grid_rowconfigure(1, weight=1)
        bottom_screen_frame.grid_columnconfigure(0, weight=1)

        ttk.Label(bottom_screen_frame, text="Bottom Screen (Touch Input)", style='Header.TLabel').grid(row=0, column=0, sticky="w", pady=5)
        self.bottom_canvas = tk.Canvas(bottom_screen_frame, bg="black", width=256, height=192, relief="sunken", borderwidth=2, highlightthickness=0)
        self.bottom_canvas.grid(row=1, column=0, sticky="nsew")

        # --- Right Panel (Debug Console) ---
        console_frame = ttk.Frame(main_frame)
        console_frame.grid(row=0, column=1, sticky="nsew")
        console_frame.grid_rowconfigure(1, weight=1)
        console_frame.grid_columnconfigure(0, weight=1)

        ttk.Label(console_frame, text="Debug Console", style='Header.TLabel').grid(row=0, column=0, sticky="w", pady=5)
        
        self.console_text = tk.Text(console_frame, 
            bg="#1E1E1E", 
            fg="#D4D4D4", 
            font=("Consolas", 10), 
            relief="sunken", 
            borderwidth=2, 
            highlightthickness=0,
            wrap="word",
            state="disabled"
        )
        self.console_text.grid(row=1, column=0, sticky="nsew")
        
        # Add a scrollbar to the console
        console_scrollbar = ttk.Scrollbar(console_frame, orient="vertical", command=self.console_text.yview)
        console_scrollbar.grid(row=1, column=1, sticky="ns")
        self.console_text['yscrollcommand'] = console_scrollbar.set

    def create_statusbar(self):
        self.status = tk.Label(self, text="Ready.", anchor="w", bg="#1E1E1E", fg="white", font=('Arial', 9), relief="sunken", borderwidth=1, padx=5)
        self.status.pack(fill="x", side="bottom")

    def log_message(self, msg):
        """Logs a message to the debug console with a timestamp."""
        now = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{now}] {msg}\n"
        
        self.console_text.config(state="normal")
        self.console_text.insert("end", formatted_msg)
        self.console_text.config(state="disabled")
        self.console_text.see("end") # Auto-scroll
        
        # Also update status bar with the latest message
        self.status.config(text=msg)

    # ───────── ROM and Emulation Control ─────────

    def load_rom_dialog(self):
        path = filedialog.askopenfilename(filetypes=[("NDS ROMs","*.nds")])
        if not path: 
            self.log_message("ROM loading cancelled.")
            return
        try:
            self.emu.load_rom(path)
            self.log_message(f"Loaded {os.path.basename(path)}")
        except Exception as e:
            self.log_message(f"Load Error: {e}")
            messagebox.showerror("Load Error", str(e))

    def start_emulation(self):
        if self.thread and self.thread.is_alive():
            self.log_message("Emulation is already running.")
            return
        
        self.log_message("Starting emulation...")
        self.thread = threading.Thread(target=self.emu.run, daemon=True)
        self.thread.start()
        # self.after(100, self.update_views) # Disabled as register views are removed

    def stop_emulation(self):
        self.emu.running = False
        self.log_message("Emulation stopped.")

    # def update_views(self):
    #     """
    #     This function is no longer called, but is kept
    #     as a reference for when you add register/memory views
    #     in new windows or debug tabs.
    #     """
    #     if self.emu.running:
    #         self.after(100, self.update_views)
    
    def quit(self):
        """Safely stops the emulation thread before quitting."""
        self.stop_emulation()
        if self.thread:
            self.thread.join(timeout=0.5) # Wait briefly for thread
        super().quit()

# ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = EmuGUI()
    app.mainloop()
