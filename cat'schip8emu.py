#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Cat's CHIP-8 Emu 0.2.3 — Full Featured Edition
# (C) 2025 Samsoft Studios / Cat-san
#
# Tkinter CHIP-8 emulator with full opcode support and standard 90s emulator features:
#  - Menu system for file operations, options, and help
#  - Pause/resume, reset, single-step execution
#  - Adjustable CPU speed via slider
#  - Save/load states with compression
#  - Color chooser for on/off pixels
#  - Screen scale adjustment
#  - Quirk toggles for shift and memory behaviors
#  - Completed all CHIP-8 opcodes
#  - Retained previous canvas rendering fixes
#
# Licensed under GPL-3.0-or-later.
# Nintendo trademark notice: not affiliated or endorsed.

import sys, os, random, argparse, time, pickle, zlib
from tkinter import (
    Tk, Canvas, Frame, BOTH, LEFT, RIGHT, X, Y, BOTTOM, TOP, StringVar,
    Label, Button, Scale, HORIZONTAL, filedialog, messagebox, Menu,
    colorchooser, BooleanVar, IntVar, simpledialog
)

# -------------------------------------------------------
# Complete CHIP-8 core with all opcodes
# -------------------------------------------------------

class Chip8:
    WIDTH, HEIGHT = 64, 32
    MEM_SIZE = 4096
    ROM_LOAD_ADDR = 0x200
    FONT_ADDR = 0x50
    FONTSET = [
        0xF0,0x90,0x90,0x90,0xF0, 0x20,0x60,0x20,0x20,0x70,
        0xF0,0x10,0xF0,0x80,0xF0, 0xF0,0x10,0xF0,0x10,0xF0,
        0x90,0x90,0xF0,0x10,0x10, 0xF0,0x80,0xF0,0x10,0xF0,
        0xF0,0x80,0xF0,0x90,0xF0, 0xF0,0x10,0x20,0x40,0x40,
        0xF0,0x90,0xF0,0x90,0xF0, 0xF0,0x90,0xF0,0x10,0xF0,
        0xF0,0x90,0xF0,0x90,0x90, 0xE0,0x90,0xE0,0x90,0xE0,
        0xF0,0x80,0x80,0x80,0xF0, 0xE0,0x90,0x90,0x90,0xE0,
        0xF0,0x80,0xF0,0x80,0xF0, 0xF0,0x80,0xF0,0x80,0x80
    ]
    def __init__(self, shift_quirk=False, mem_quirk=False):
        self.shift_quirk = shift_quirk
        self.mem_quirk = mem_quirk
        self.reset(True)
    def reset(self, hard=False):
        self.memory = [0]*self.MEM_SIZE
        self.V = [0]*16; self.I=0; self.pc=self.ROM_LOAD_ADDR
        self.stack=[]; self.delay_timer=0; self.sound_timer=0
        self.gfx=[0]*(self.WIDTH*self.HEIGHT); self.keypad=[0]*16
        self.draw_flag=True; self.wait_key_reg=None
        for i,b in enumerate(self.FONTSET):
            self.memory[self.FONT_ADDR+i]=b
        if not hard and hasattr(self,"_rom_bytes"):
            self.load_rom_bytes(self._rom_bytes)
    def load_rom_bytes(self, data:bytes):
        for i in range(self.ROM_LOAD_ADDR,self.MEM_SIZE):
            self.memory[i]=0
        for i,b in enumerate(data):
            self.memory[self.ROM_LOAD_ADDR+i]=b
        self.pc=self.ROM_LOAD_ADDR
        self.V=[0]*16; self.I=0; self.stack=[]
        self.delay_timer=self.sound_timer=0
        self.gfx=[0]*(self.WIDTH*self.HEIGHT)
        self.draw_flag=True; self.wait_key_reg=None
        self._rom_bytes=data
    def _xor_pixel(self,x,y,val):
        if 0<=x<self.WIDTH and 0<=y<self.HEIGHT:
            idx=y*self.WIDTH+x; before=self.gfx[idx]
            self.gfx[idx]^=val
            if before and not self.gfx[idx]:
                self.V[0xF]=1
    def cycle(self):
        if self.wait_key_reg is not None:
            pressed = False
            for i in range(16):
                if self.keypad[i]:
                    self.V[self.wait_key_reg] = i
                    pressed = True
                    break
            if not pressed:
                return
            self.wait_key_reg = None
        if self.pc + 1 >= self.MEM_SIZE:
            return
        op = (self.memory[self.pc] << 8) | self.memory[self.pc + 1]
        self.pc = (self.pc + 2) & 0xFFF
        nnn = op & 0x0FFF
        n = op & 0xF
        x = (op >> 8) & 0xF
        y = (op >> 4) & 0xF
        kk = op & 0xFF
        if op == 0x00E0:
            self.gfx = [0] * (self.WIDTH * self.HEIGHT)
            self.draw_flag = True
            return
        if op == 0x00EE and self.stack:
            self.pc = self.stack.pop()
            return
        if op & 0xF000 == 0x1000:
            self.pc = nnn
            return
        if op & 0xF000 == 0x2000:
            self.stack.append(self.pc)
            self.pc = nnn
            return
        if op & 0xF000 == 0x3000:
            if self.V[x] == kk:
                self.pc = (self.pc + 2) & 0xFFF
            return
        if op & 0xF000 == 0x4000:
            if self.V[x] != kk:
                self.pc = (self.pc + 2) & 0xFFF
            return
        if op & 0xF000 == 0x5000:
            if self.V[x] == self.V[y]:
                self.pc = (self.pc + 2) & 0xFFF
            return
        if op & 0xF000 == 0x6000:
            self.V[x] = kk
            return
        if op & 0xF000 == 0x7000:
            self.V[x] = (self.V[x] + kk) & 0xFF
            return
        if op & 0xF000 == 0x8000:
            if n == 0:
                self.V[x] = self.V[y]
            elif n == 1:
                self.V[x] |= self.V[y]
            elif n == 2:
                self.V[x] &= self.V[y]
            elif n == 3:
                self.V[x] ^= self.V[y]
            elif n == 4:
                total = self.V[x] + self.V[y]
                self.V[0xF] = 1 if total > 0xFF else 0
                self.V[x] = total & 0xFF
            elif n == 5:
                total = self.V[x] - self.V[y]
                self.V[0xF] = 0 if total < 0 else 1
                self.V[x] = total & 0xFF
            elif n == 6:
                if not self.shift_quirk:
                    val = self.V[y]
                else:
                    val = self.V[x]
                self.V[0xF] = val & 0x1
                self.V[x] = val >> 1
            elif n == 7:
                total = self.V[y] - self.V[x]
                self.V[0xF] = 0 if total < 0 else 1
                self.V[x] = total & 0xFF
            elif n == 0xE:
                if not self.shift_quirk:
                    val = self.V[y]
                else:
                    val = self.V[x]
                self.V[0xF] = (val >> 7) & 0x1
                self.V[x] = (val << 1) & 0xFF
            return
        if op & 0xF000 == 0x9000:
            if self.V[x] != self.V[y]:
                self.pc = (self.pc + 2) & 0xFFF
            return
        if op & 0xF000 == 0xA000:
            self.I = nnn
            return
        if op & 0xF000 == 0xB000:
            self.pc = nnn + self.V[0]
            return
        if op & 0xF000 == 0xC000:
            self.V[x] = random.randint(0, 255) & kk
            return
        if op & 0xF000 == 0xD000:
            self.V[0xF] = 0
            for row in range(n):
                sprite = self.memory[(self.I + row) & 0xFFF]
                for bit in range(8):
                    if sprite & (0x80 >> bit):
                        self._xor_pixel((self.V[x] + bit) % self.WIDTH, (self.V[y] + row) % self.HEIGHT, 1)
            self.draw_flag = True
            return
        if op & 0xF000 == 0xE000:
            if kk == 0x9E:
                if self.keypad[self.V[x]]:
                    self.pc = (self.pc + 2) & 0xFFF
            elif kk == 0xA1:
                if not self.keypad[self.V[x]]:
                    self.pc = (self.pc + 2) & 0xFFF
            return
        if op & 0xF000 == 0xF000:
            if kk == 0x07:
                self.V[x] = self.delay_timer
            elif kk == 0x0A:
                self.wait_key_reg = x
            elif kk == 0x15:
                self.delay_timer = self.V[x]
            elif kk == 0x18:
                self.sound_timer = self.V[x]
            elif kk == 0x1E:
                self.I = (self.I + self.V[x]) & 0xFFF
            elif kk == 0x29:
                self.I = self.FONT_ADDR + (self.V[x] & 0xF) * 5
            elif kk == 0x33:
                val = self.V[x]
                self.memory[(self.I + 2) & 0xFFF] = val % 10
                val //= 10
                self.memory[(self.I + 1) & 0xFFF] = val % 10
                val //= 10
                self.memory[self.I & 0xFFF] = val % 10
            elif kk == 0x55:
                for i in range(x + 1):
                    self.memory[(self.I + i) & 0xFFF] = self.V[i]
                if self.mem_quirk:
                    self.I = (self.I + x + 1) & 0xFFF
            elif kk == 0x65:
                for i in range(x + 1):
                    self.V[i] = self.memory[(self.I + i) & 0xFFF]
                if self.mem_quirk:
                    self.I = (self.I + x + 1) & 0xFFF
            return

# -------------------------------------------------------
# Tkinter Frontend with enhanced features
# -------------------------------------------------------

KEYMAP={'1':1,'2':2,'3':3,'4':0xC,'q':4,'w':5,'e':6,'r':0xD,
        'a':7,'s':8,'d':9,'f':0xE,'z':0xA,'x':0,'c':0xB,'v':0xF}

class Chip8App:
    def __init__(self,root,rom=None,scale=12,cpu_hz=700):
        self.root=root; self.scale=int(scale); self.cpu_hz=cpu_hz
        self.chip=Chip8(); self.paused=False; self.cycles_accum=0
        self.frame_ms=int(1000/60)
        self.color_on="#FFFFFF"; self.color_off="#000000"
        self._render_busy=False
        self.canvas=Canvas(root,width=Chip8.WIDTH*self.scale,
                           height=Chip8.HEIGHT*self.scale,
                           highlightthickness=0,bg=self.color_off,bd=0)
        self.canvas.pack(side=TOP)
        self.pixel_ids=[]; self._init_pixels()
        self.status=StringVar(value="Ready.")
        Label(root,textvariable=self.status,anchor='w').pack(side=BOTTOM,fill=X)
        control_frame = Frame(root)
        control_frame.pack(side=BOTTOM, fill=X)
        self.pause_btn = Button(control_frame, text="Pause", command=self._toggle_pause)
        self.pause_btn.pack(side=LEFT)
        Button(control_frame, text="Reset", command=self.reset_soft).pack(side=LEFT)
        Button(control_frame, text="Step", command=self._step).pack(side=LEFT)
        self.speed_var = IntVar(value=self.cpu_hz)
        Scale(control_frame, from_=100, to=2000, resolution=50, orient=HORIZONTAL, label="CPU Hz",
              variable=self.speed_var, command=self._update_speed).pack(side=LEFT)
        menubar = Menu(root)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="Load ROM...", command=self._load_rom_dialog)
        filemenu.add_separator()
        filemenu.add_command(label="Save State...", command=self._save_state_dialog)
        filemenu.add_command(label="Load State...", command=self._load_state_dialog)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        optionsmenu = Menu(menubar, tearoff=0)
        optionsmenu.add_command(label="Colors...", command=self._set_colors)
        optionsmenu.add_command(label="Screen Scale...", command=self._set_scale)
        self.shift_var = BooleanVar(value=self.chip.shift_quirk)
        optionsmenu.add_checkbutton(label="Shift Quirk (ignore Vy)", variable=self.shift_var, command=self._toggle_shift_quirk)
        self.mem_var = BooleanVar(value=self.chip.mem_quirk)
        optionsmenu.add_checkbutton(label="Memory Quirk (I += x+1)", variable=self.mem_var, command=self._toggle_mem_quirk)
        menubar.add_cascade(label="Options", menu=optionsmenu)
        helpmenu = Menu(menubar, tearoff=0)
        helpmenu.add_command(label="About", command=self._about)
        menubar.add_cascade(label="Help", menu=helpmenu)
        root.config(menu=menubar)
        self.root.bind("<KeyPress>",self._on_keydown)
        self.root.bind("<KeyRelease>",self._on_keyup)
        if rom and os.path.exists(rom): self.load_rom(rom)
        self.root.resizable(False,False)
        self._schedule()

    # ---------------- Rendering fixes ----------------
    def _init_pixels(self):
        self.canvas.delete("all"); self.pixel_ids=[]
        for y in range(Chip8.HEIGHT):
            row=[]
            for x in range(Chip8.WIDTH):
                x0=int(x*self.scale); y0=int(y*self.scale)
                x1=int(x0+self.scale); y1=int(y0+self.scale)
                rid=self.canvas.create_rectangle(x0,y0,x1,y1,outline="",fill=self.color_off)
                row.append(rid)
            self.pixel_ids.append(row)

    def render(self):
        if self._render_busy: return
        self._render_busy=True
        try:
            on,off=self.color_on,self.color_off
            idx=0; self.canvas.configure(state="disabled")
            for y in range(Chip8.HEIGHT):
                row=self.pixel_ids[y]
                for x in range(Chip8.WIDTH):
                    self.canvas.itemconfig(row[x],fill=on if self.chip.gfx[idx] else off)
                    idx+=1
            self.canvas.configure(state="normal")
            self.canvas.update_idletasks()  # ensure frame flush
        finally:
            self._render_busy=False

    # ---------------- Logic ----------------
    def _schedule(self):
        self.root.after(self.frame_ms,self._tick)
    def _tick(self):
        if not self.paused:
            self.cycles_accum += self.cpu_hz / 60.0
            n = int(self.cycles_accum)
            self.cycles_accum -= n
            for _ in range(n):
                self.chip.cycle()
            if self.chip.delay_timer > 0:
                self.chip.delay_timer -= 1
            if self.chip.sound_timer > 0:
                self.chip.sound_timer -= 1
                self.root.bell()
        if self.chip.draw_flag:
            self.root.after_idle(self.render)  # macOS-safe
            self.chip.draw_flag = False
        self._schedule()
    def _step(self):
        if self.paused:
            self.chip.cycle()
            if self.chip.draw_flag:
                self.render()
                self.chip.draw_flag = False

    # ---------------- Input ----------------
    def _on_keydown(self,e):
        k=(e.keysym or "").lower()
        if k in KEYMAP: self.chip.keypad[KEYMAP[k]]=1
    def _on_keyup(self,e):
        k=(e.keysym or "").lower()
        if k in KEYMAP: self.chip.keypad[KEYMAP[k]]=0

    # ---------------- Controls ----------------
    def _toggle_pause(self):
        self.paused = not self.paused
        self.pause_btn['text'] = "Resume" if self.paused else "Pause"
    def _update_speed(self, v):
        self.cpu_hz = int(v)
    def _toggle_shift_quirk(self):
        self.chip.shift_quirk = self.shift_var.get()
        messagebox.showinfo("Quirk Changed", "Shift quirk updated. Resetting emulator.")
        self.reset_soft()
    def _toggle_mem_quirk(self):
        self.chip.mem_quirk = self.mem_var.get()
        messagebox.showinfo("Quirk Changed", "Memory quirk updated. Resetting emulator.")
        self.reset_soft()

    # ---------------- ROMs / State ----------------
    def load_rom(self,path):
        with open(path,"rb") as f: data=f.read()
        self.chip.load_rom_bytes(data)
        self.status.set(f"Loaded {os.path.basename(path)} ({len(data)} bytes)")
        self.render()
    def _load_rom_dialog(self):
        path = filedialog.askopenfilename(title="Load CHIP-8 ROM", filetypes=[("CHIP-8 files", "*.ch8 *.rom *.bin"), ("All files", "*.*")])
        if path:
            self.load_rom(path)
    def save_state(self, path):
        state = {
            'memory': self.chip.memory[:],
            'V': self.chip.V[:],
            'I': self.chip.I,
            'pc': self.chip.pc,
            'stack': self.chip.stack[:],
            'delay_timer': self.chip.delay_timer,
            'sound_timer': self.chip.sound_timer,
            'gfx': self.chip.gfx[:],
            'keypad': self.chip.keypad[:],
            'draw_flag': self.chip.draw_flag,
            'wait_key_reg': self.chip.wait_key_reg,
            'shift_quirk': self.chip.shift_quirk,
            'mem_quirk': self.chip.mem_quirk,
            '_rom_bytes': self.chip._rom_bytes,
        }
        compressed = zlib.compress(pickle.dumps(state))
        with open(path, 'wb') as f:
            f.write(compressed)
        self.status.set(f"Saved state to {os.path.basename(path)}")
    def _save_state_dialog(self):
        path = filedialog.asksaveasfilename(title="Save State", defaultextension=".c8s", filetypes=[("CHIP-8 State", "*.c8s")])
        if path:
            self.save_state(path)
    def load_state(self, path):
        with open(path, 'rb') as f:
            compressed = f.read()
        state = pickle.loads(zlib.decompress(compressed))
        for k, v in state.items():
            setattr(self.chip, k, v)
        self.render()
        self.status.set(f"Loaded state from {os.path.basename(path)}")
    def _load_state_dialog(self):
        path = filedialog.askopenfilename(title="Load State", filetypes=[("CHIP-8 State", "*.c8s")])
        if path:
            self.load_state(path)
    def reset_soft(self):
        self.chip.reset(False)
        for r in self.pixel_ids:
            for pid in r: self.canvas.itemconfig(pid,fill=self.color_off)
        self.render()
    def _set_colors(self):
        col = colorchooser.askcolor(self.color_on, title="Choose ON color")
        if col[1]: self.color_on = col[1]
        col = colorchooser.askcolor(self.color_off, title="Choose OFF color")
        if col[1]:
            self.color_off = col[1]
            self.canvas.config(bg=self.color_off)
        self.render()
    def _set_scale(self):
        new = simpledialog.askinteger("Screen Scale", "Enter pixel scale (1-20):", initialvalue=self.scale, minvalue=1, maxvalue=20)
        if new:
            self.scale = new
            self.canvas.config(width=Chip8.WIDTH * new, height=Chip8.HEIGHT * new)
            self._init_pixels()
            self.render()
            self.root.resizable(False, False)
    def _about(self):
        messagebox.showinfo("About", "Cat's CHIP-8 Emu 0.2.3 — Full Featured Edition\n(C) 2025 Samsoft Studios / Cat-san\nLicensed under GPL-3.0-or-later.\n\nFeatures standard 90s emulator capabilities like save states, configurable speed, and more.")

# -------------------------------------------------------
# Entry
# -------------------------------------------------------

def main():
    p=argparse.ArgumentParser()
    p.add_argument("rom",nargs="?",help="Path to CHIP-8 ROM")
    p.add_argument("--hz",type=float,default=700)
    p.add_argument("--scale",type=int,default=12)
    a=p.parse_args()
    root=Tk(); root.title("Cat's CHIP-8 Emu 0.2.3")
    app=Chip8App(root,rom=a.rom,scale=a.scale,cpu_hz=a.hz)
    root.mainloop()

if __name__=="__main__":
    main()