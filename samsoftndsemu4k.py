#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cat's DS 0.1 – Nintendo DS Emulator GUI (Samsoft EmuCore 2025 style)
Fixed edition – 12-bug patchset
Extended with fuller ARM interpreter
"""
import os, sys, time, threading, subprocess, platform, tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
IS_WINDOWS = platform.system().lower() == "windows"
# ──────────────────────────────────────────────
# Optional Win32 helpers
# ──────────────────────────────────────────────
if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes
    class RECT(ctypes.Structure):
        _fields_ = [("left", wintypes.LONG),
                    ("top", wintypes.LONG),
                    ("right", wintypes.LONG),
                    ("bottom", wintypes.LONG)]
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    GWL_STYLE = -16
    WS_CHILD, WS_VISIBLE = 0x40000000, 0x10000000
    WS_CLIPSIBLINGS, WS_CLIPCHILDREN = 0x04000000, 0x02000000
    SWP_NOSIZE, SWP_NOMOVE, SWP_NOZORDER, SWP_FRAMECHANGED = 0x0001,0x0002,0x0004,0x0020
    WM_CLOSE = 0x0010
    def _get_pid_for_hwnd(hwnd):
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return pid.value
    def _is_window_visible(hwnd): return bool(user32.IsWindowVisible(hwnd))
    def _get_window_text(hwnd):
        length = user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value
    def _enum_windows_for_pid(pid):
        res = []
        def _cb(hwnd, lp):
            if _get_pid_for_hwnd(hwnd) == pid and _is_window_visible(hwnd):
                res.append(hwnd)
            return True
        user32.EnumWindows(EnumWindowsProc(_cb), 0)
        return res
    def _set_parent(child, parent):
        try: return bool(user32.SetParent(child, parent))
        except Exception: return False
    def _get_style(hwnd): return user32.GetWindowLongW(hwnd, GWL_STYLE)
    def _set_style(hwnd, style):
        try:
            user32.SetWindowLongW(hwnd, GWL_STYLE, ctypes.c_long(style))
            user32.SetWindowPos(hwnd, 0,0,0,0,0,
                SWP_NOMOVE|SWP_NOSIZE|SWP_NOZORDER|SWP_FRAMECHANGED)
        except Exception: pass
    def _move_window(hwnd,x,y,w,h):
        try: user32.MoveWindow(hwnd,x,y,w,h,True)
        except Exception: pass
# ──────────────────────────────────────────────
# Minimal Core
# ──────────────────────────────────────────────
class MemoryController:
    def __init__(self,start,end):
        self.start,self.end=start,end
        self.data=bytearray(end-start)
    def read(self,addr,size):
        o=addr-self.start
        if o<0 or o+size>len(self.data): return 0
        return int.from_bytes(self.data[o:o+size],'little')
    def write(self,addr,size,val):
        o=addr-self.start
        if o<0 or o+size>len(self.data): return
        self.data[o:o+size]=val.to_bytes(size,'little')
class ARMCPU:
    def __init__(self,emu,is_arm9):
        self.emu,self.is_arm9=emu,is_arm9
        self.registers=[0]*16; self.cpsr=0x1F  # System mode, T=0
    def ror(self,v,a): a%=32; return ((v>>a)|(v<<(32-a)))&0xFFFFFFFF if a else v&0xFFFFFFFF
    def check_cond(self,cond):
        N = (self.cpsr >> 31) & 1
        Z = (self.cpsr >> 30) & 1
        C = (self.cpsr >> 29) & 1
        V = (self.cpsr >> 28) & 1
        if cond == 0: return Z == 1
        if cond == 1: return Z == 0
        if cond == 2: return C == 1
        if cond == 3: return C == 0
        if cond == 4: return N == 1
        if cond == 5: return N == 0
        if cond == 6: return V == 1
        if cond == 7: return V == 0
        if cond == 8: return C == 1 and Z == 0
        if cond == 9: return C == 0 or Z == 1
        if cond == 10: return N == V
        if cond == 11: return N != V
        if cond == 12: return Z == 0 and N == V
        if cond == 13: return Z == 1 or N != V
        if cond == 14: return True
        if cond == 15: return False
        return False
    def step(self):
        pc = self.registers[15]
        if self.cpsr & 0x20:
            instr = self.emu.read_memory(pc,2)
            self.registers[15] = (pc + 2) & 0xFFFFFFFF
            # Basic Thumb support - extend with more ops as needed
            # For example, simple MOV immediate (Thumb: MOV Rd, #imm8)
            if (instr >> 8) & 0x1F == 0x4:  # MOV Rd, #imm8 (00100 ddd iiiiiiii)
                rd = (instr >> 8) & 7
                imm = instr & 0xFF
                self.registers[rd] = imm
                N = (imm >> 31) & 1
                Z = 1 if imm == 0 else 0
                self.cpsr = (self.cpsr & ~0xC0000000) | (N << 31) | (Z << 30)
            # Add more Thumb ops here for fuller support
            return
        instr = self.emu.read_memory(pc,4)
        cond = (instr >> 28) & 0xF
        if not self.check_cond(cond):
            self.registers[15] = (pc + 4) & 0xFFFFFFFF
            return
        if (instr >> 26) & 3 == 0:  # Data processing
            I = (instr >> 25) & 1
            if I == 0:  # Register operand (basic support skipped for now)
                self.registers[15] = (pc + 4) & 0xFFFFFFFF
                return
            opcd = (instr >> 21) & 0xF
            S = (instr >> 20) & 1
            rn = (instr >> 16) & 0xF
            rd = (instr >> 12) & 0xF
            op1 = self.registers[rn]
            imm = instr & 0xFF
            rot = (instr >> 8) & 0xF
            op2 = self.ror(imm, rot * 2)
            carry_out = (op2 >> 31) & 1 if rot else (self.cpsr >> 29) & 1
            if opcd == 0b1101:  # MOV
                result = op2
                if S:
                    N = (result >> 31) & 1
                    Z = 1 if result == 0 else 0
                    V = (self.cpsr >> 28) & 1
                    self.cpsr = (self.cpsr & ~0xF0000000) | (N << 31) | (Z << 30) | (carry_out << 29) | (V << 28)
            elif opcd == 0b0100:  # ADD
                full = op1 + op2
                result = full & 0xFFFFFFFF
                C = 1 if full > 0xFFFFFFFF else 0
                V = 1 if ((op1 >> 31) == (op2 >> 31)) and ((result >> 31) != (op1 >> 31)) else 0
                N = (result >> 31) & 1
                Z = 1 if result == 0 else 0
                if S:
                    self.cpsr = (self.cpsr & ~0xF0000000) | (N << 31) | (Z << 30) | (C << 29) | (V << 28)
            elif opcd == 0b0010:  # SUB
                full = op1 - op2
                result = full & 0xFFFFFFFF
                C = 0 if full < 0 else 1
                V = 1 if ((op1 >> 31) != (op2 >> 31)) and ((result >> 31) != (op1 >> 31)) else 0
                N = (result >> 31) & 1
                Z = 1 if result == 0 else 0
                if S:
                    self.cpsr = (self.cpsr & ~0xF0000000) | (N << 31) | (Z << 30) | (C << 29) | (V << 28)
            elif opcd == 0b0000:  # AND
                result = op1 & op2
                if S:
                    N = (result >> 31) & 1
                    Z = 1 if result == 0 else 0
                    V = (self.cpsr >> 28) & 1
                    self.cpsr = (self.cpsr & ~0xF0000000) | (N << 31) | (Z << 30) | (carry_out << 29) | (V << 28)
            elif opcd == 0b1100:  # ORR
                result = op1 | op2
                if S:
                    N = (result >> 31) & 1
                    Z = 1 if result == 0 else 0
                    V = (self.cpsr >> 28) & 1
                    self.cpsr = (self.cpsr & ~0xF0000000) | (N << 31) | (Z << 30) | (carry_out << 29) | (V << 28)
            self.registers[rd] = result
        elif (instr >> 26) & 3 == 1:  # Single data transfer (basic immediate)
            I = (instr >> 25) & 1
            if I:  # Shifted register offset (skipped for simplicity)
                self.registers[15] = (pc + 4) & 0xFFFFFFFF
                return
            P = (instr >> 24) & 1
            U = (instr >> 23) & 1
            B = (instr >> 22) & 1
            W = (instr >> 21) & 1
            L = (instr >> 20) & 1
            rn = (instr >> 16) & 0xF
            rd = (instr >> 12) & 0xF
            offset = instr & 0xFFF
            addr = self.registers[rn]
            if P:
                if U:
                    addr += offset
                else:
                    addr -= offset
            if L:
                val = self.emu.read_memory(addr, 1 if B else 4)
                self.registers[rd] = val
            else:
                val = self.registers[rd]
                self.emu.write_memory(addr, 1 if B else 4, val)
            if not P or W:
                new_base = self.registers[rn]
                if U:
                    new_base += offset
                else:
                    new_base -= offset
                self.registers[rn] = new_base
        elif (instr >> 25) & 7 == 5:  # Branch
            L = (instr >> 24) & 1
            offset = instr & 0xFFFFFF
            if (instr & 0x800000):
                offset -= 0x1000000
            offset <<= 2
            target = pc + 8 + offset
            if L:
                self.registers[14] = pc + 4
            self.registers[15] = target
            return
        self.registers[15] = (pc + 4) & 0xFFFFFFFF
class CatsDS:
    def __init__(self):
        self.memory_controllers=[]
        self.add_memory(0x02000000,0x02400000)  # Main RAM 4MB
        self.add_memory(0x03000000,0x03010000)  # Shared WRAM 64KB
        self.add_memory(0x03800000,0x03810000)  # ARM7 private WRAM 64KB
        self.add_memory(0x04000000,0x05000000)  # IO registers (dummy)
        self.add_memory(0x06000000,0x06800000)  # VRAM (oversized dummy)
        self.arm9,self.arm7=ARMCPU(self,True),ARMCPU(self,False)
        self.running=False
    def add_memory(self,s,e): self.memory_controllers.append(MemoryController(s,e))
    def read_memory(self,a,s):
        for m in self.memory_controllers:
            if m.start<=a<m.end: return m.read(a,s)
        return 0
    def write_memory(self,a,s,v):
        for m in self.memory_controllers:
            if m.start<=a<m.end:m.write(a,s,v);return
    def load_rom(self,path):
        with open(path,'rb') as f: d=f.read()
        def u32(o):return int.from_bytes(d[o:o+4],'little')
        a9o,a9e,a9l,a9s=u32(0x20),u32(0x24),u32(0x28),u32(0x2C)
        for i in range(a9s):self.write_memory(a9l+i,1,d[a9o+i])
        self.arm9.registers[15]=a9e
        a7o,a7e,a7l,a7s=u32(0x30),u32(0x34),u32(0x38),u32(0x3C)
        for i in range(a7s):self.write_memory(a7l+i,1,d[a7o+i])
        self.arm7.registers[15]=a7e
    def run(self):
        self.running=True
        while self.running: 
            self.arm9.step()
            self.arm7.step()
            # No sleep for better performance; add cycle limiting if needed
    def stop(self): self.running=False
# ──────────────────────────────────────────────
# External Engine Bridge
# ──────────────────────────────────────────────
class NoCashBridge:
    def __init__(self,exe=None):
        self.exe_path=exe; self.proc=None; self._embedded_hwnd=None
        self._embed_target_frame=None; self._embed_keep=False
    def set_exe_path(self,p): self.exe_path=p
    def load_rom(self,p): self.rom_path=p
    def is_running(self): return self.proc and self.proc.poll() is None
    def run(self,frame,on_log):
        if self.is_running(): return  # Fix: prevent multiple launches
        if not self.exe_path or not os.path.exists(self.exe_path):
            raise FileNotFoundError("NO$GBA.exe path invalid")
        if not getattr(self,"rom_path",None): raise RuntimeError("No ROM")
        self._embed_target_frame=frame
        def _launch():
            try:
                args=[self.exe_path,self.rom_path]; cwd=os.path.dirname(self.exe_path)
                startup=None
                if IS_WINDOWS:
                    startup=subprocess.STARTUPINFO(); startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW
                self.proc=subprocess.Popen(args,cwd=cwd,startupinfo=startup)
                on_log(f"no$gba started PID {self.proc.pid}")
                if IS_WINDOWS: threading.Thread(target=self._embed_loop,args=(on_log,),daemon=True).start()
                threading.Thread(target=self._wait,args=(on_log,),daemon=True).start()
            except Exception as e: on_log(f"Launch error: {e}")
        threading.Thread(target=_launch,daemon=True).start()
    def _wait(self,on_log):
        if not self.proc: return
        self.proc.wait(); self._embedded_hwnd=None; self._embed_keep=False
        on_log("no$gba exited.")
    def _embed_loop(self,on_log):
        if not IS_WINDOWS or not self.proc: return
        pid=self.proc.pid; deadline=time.time()+8
        hwnd=None
        while time.time()<deadline and self.is_running():
            wins=_enum_windows_for_pid(pid)
            for w in wins:
                if "no$gba" in _get_window_text(w).lower(): hwnd=w; break
            if hwnd: break; time.sleep(0.25)
        if not hwnd: on_log("Embed: window not found."); return
        try:
            par=int(self._embed_target_frame.winfo_id())
            st=_get_style(hwnd)|(WS_CHILD|WS_CLIPSIBLINGS|WS_CLIPCHILDREN)
            _set_style(hwnd,st); _set_parent(hwnd,par)
            self._embedded_hwnd=hwnd; self._embed_keep=True
            on_log("Embed success.")
            self._resize_loop()
        except Exception as e: on_log(f"Embed err {e}")
    def _resize_loop(self):
        if not (IS_WINDOWS and self._embedded_hwnd and self._embed_keep): return
        if not self._embed_target_frame.winfo_exists(): return
        w,h=max(100,self._embed_target_frame.winfo_width()),max(100,self._embed_target_frame.winfo_height())
        _move_window(self._embedded_hwnd,0,0,w,h)
        self._embed_target_frame.after(100,self._resize_loop)
    def stop(self,on_log):
        self._embed_keep=False
        if IS_WINDOWS and self._embedded_hwnd:
            try: user32.PostMessageW(self._embedded_hwnd,WM_CLOSE,0,0)
            except Exception: pass
        if self.proc and self.is_running():
            try: self.proc.terminate(); self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired: self.proc.kill()
        self.proc=None; self._embedded_hwnd=None
        on_log("no$gba stopped.")
# ──────────────────────────────────────────────
# GUI
# ──────────────────────────────────────────────
ENGINE_OPTS=("Internal (CatsDS)","External (no$gba 2025)")
class EmuGUI(tk.Tk):
    def __init__(self):
        super().__init__(); self.title("Cat's DS 0.1 – Samsoft EmuCore 2025"); self.geometry("980x680")
        self.configure(bg="#2E2E2E")
        s=ttk.Style(self); s.theme_use('clam')
        s.configure('.',background='#2E2E2E',foreground='white')
        s.configure('TFrame',background='#2E2E2E')
        s.configure('TLabel',background='#2E2E2E',foreground='white')
        self.core_i=CatsDS(); self.core_x=NoCashBridge()
        self.backend=tk.StringVar(value=ENGINE_OPTS[0])
        self.thread=None; self.current_rom=None
        self._build(); self.log("[Samsoft EmuCore Ready]")
    def _build(self):
        bar=tk.Menu(self); self.config(menu=bar)
        f=tk.Menu(bar,tearoff=0,bg="#3C3C3C",fg="white")
        f.add_command(label="Open ROM...",command=self.load_rom)
        f.add_separator(); f.add_command(label="Exit",command=self.quit)
        bar.add_cascade(label="File",menu=f)
        r=tk.Menu(bar,tearoff=0,bg="#3C3C3C",fg="white")
        r.add_command(label="Run",command=self.start); r.add_command(label="Stop",command=self.stop)
        bar.add_cascade(label="Run",menu=r)
        # layout
        main=ttk.Frame(self,padding=10); main.pack(fill="both",expand=True)
        main.grid_rowconfigure(0,weight=1); main.grid_columnconfigure(1,weight=1)
        left=ttk.Frame(main); left.grid(row=0,column=0,sticky="ns")
        ttk.Label(left,text="Core:").pack(anchor="w")
        ttk.Combobox(left,values=ENGINE_OPTS,textvariable=self.backend,state='readonly').pack(fill="x")
        ttk.Button(left,text="Open ROM...",command=self.load_rom).pack(fill="x")
        self.top=tk.Canvas(left,bg="black",width=256,height=192); self.top.pack(pady=10)
        self.bot=tk.Canvas(left,bg="black",width=256,height=192); self.bot.pack()
        self.ext=ttk.Frame(left)
        right=ttk.Frame(main); right.grid(row=0,column=1,sticky="nsew")
        ttk.Label(right,text="Console").pack(anchor="w")
        self.txt=tk.Text(right,bg="#1E1E1E",fg="#D4D4D4",state="disabled"); self.txt.pack(fill="both",expand=True)
        sb=ttk.Scrollbar(right,orient="vertical",command=self.txt.yview)
        sb.pack(side="right",fill="y"); self.txt.config(yscrollcommand=sb.set)
    def log(self,msg):
        t=datetime.now().strftime("%H:%M:%S")
        self.txt.config(state="normal"); self.txt.insert("end",f"[{t}] {msg}\n"); self.txt.config(state="disabled")
        self.txt.see("end")
    def load_rom(self):
        p=filedialog.askopenfilename(filetypes=[("NDS ROM","*.nds")])
        if not p:return
        self.current_rom=p; b=self.backend.get()
        try:
            if b==ENGINE_OPTS[0]: self.core_i.load_rom(p); self.log(f"ROM loaded internal: {os.path.basename(p)}")
            else: self.core_x.load_rom(p); self.log(f"ROM prepared external: {os.path.basename(p)}")
        except Exception as e: messagebox.showerror("Load",str(e))
    def start(self):
        b=self.backend.get()
        if b==ENGINE_OPTS[0]:
            if self.thread and self.thread.is_alive(): return
            self.thread=threading.Thread(target=self.core_i.run,daemon=True); self.thread.start()
            self.log("Internal emu started.")
        else:
            self.top.pack_forget(); self.bot.pack_forget(); self.ext.pack(fill="both",expand=True)
            self.core_x.run(self.ext,self.log)
    def stop(self):
        b=self.backend.get()
        if b==ENGINE_OPTS[0]: self.core_i.stop()
        else: self.core_x.stop(self.log); self.ext.pack_forget(); self.top.pack(pady=10); self.bot.pack()
        if self.thread and self.thread.is_alive(): self.thread=None
        self.log("Stopped.")
    def quit(self):
        self.stop(); super().quit()
if __name__=="__main__":
    EmuGUI().mainloop()
