#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CAT'S CLICKTEAM ENGINE v2.5 — Tkinter Edition (single file, files = off)
Educational, homebrew-friendly micro engine inspired by "event-sheet" style tools.
No external assets required.

Features (core subset):
- Object types: ACTIVE, BACKDROP, STRING, COUNTER, ARRAY
- Event types: ALWAYS, KEY_PRESS/RELEASE, TIMER, COLLISION, CREATE/DESTROY, FRAME_CHANGE
- Actions: spawn/destroy, set/add counters, set strings, move/bounce, change frame
- Safe expression evaluator (limited builtins)
- Simple frames system + overlay inspector (F1), pause (P), quit (Esc)
- Optional exporters:
    * Windows EXE via PyInstaller
    * macOS .app + .dmg via PyInstaller + hdiutil
    * HTML preview (Canvas + JS) — supports a practical subset of events/actions

CLI:
    python program.py                      # run
    python program.py --export exe  --name MyGame
    python program.py --export dmg  --name MyGame
    python program.py --export html --name MyGame

Note: "HTML export" generates a single .html with embedded JS runtime that mirrors a subset
      of this engine (always-friction, timer spawns, key spawns, movement + edge bounce, strings).
"""

import tkinter as tk
import random, json, math, sys, os, subprocess, platform, time, argparse, textwrap
from enum import Enum
from typing import Dict, List, Any, Callable, Optional, Tuple

# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------
WIDTH, HEIGHT = 600, 400
BG = "#000000"
FG = "#FFFFFF"
FPS = 60

# -------------------------------------------------------------------
# ENUMS
# -------------------------------------------------------------------
class ObjectType(Enum):
    ACTIVE = "active"
    BACKDROP = "backdrop"
    COUNTER = "counter"
    STRING = "string"
    ARRAY = "array"

class EventType(Enum):
    ALWAYS = "always"
    ON_KEY_PRESS = "key_press"
    ON_KEY_RELEASE = "key_release"
    ON_TIMER = "timer"
    ON_COLLISION = "collision"
    ON_CREATE = "create"
    ON_DESTROY = "destroy"
    ON_FRAME_CHANGE = "frame_change"

# -------------------------------------------------------------------
# UTILS
# -------------------------------------------------------------------
def clamp(v, lo, hi): return lo if v < lo else hi if v > hi else v
def now_ms(): return int(time.time() * 1000)

# -------------------------------------------------------------------
# GAME OBJECT
# -------------------------------------------------------------------
class GameObject:
    def __init__(self, engine, obj_type: ObjectType, x=0, y=0, w=32, h=32, color=FG, **data):
        self.engine = engine
        self.type = obj_type
        self.x, self.y, self.w, self.h = float(x), float(y), float(w), float(h)
        self.vel_x = float(data.get("vel_x", 0.0))
        self.vel_y = float(data.get("vel_y", 0.0))
        self.color = data.get("color", color)
        self.visible = bool(data.get("visible", True))
        self.opacity = float(data.get("opacity", 1.0))   # 0..1 (not fully used on Tk canvas)
        self.angle = float(data.get("angle", 0.0))       # stored only; Tk canvas has no rotation
        self.z = int(data.get("z", 0))
        self.qualifiers = set(data.get("qualifiers", []))  # groups
        self.data = dict(data)
        self.data.setdefault("id", data.get("id"))
        self.canvas_id: Optional[int] = None  # main shape/text id
        self.outline_id: Optional[int] = None # outline for actives
        self._text_cache = ""                 # for STRING

    # AABB for collisions
    def rect(self) -> Tuple[float,float,float,float]:
        return (self.x, self.y, self.x + self.w, self.y + self.h)

    def center(self) -> Tuple[float,float]:
        return (self.x + self.w/2.0, self.y + self.h/2.0)

    def update(self, dt: float):
        # integrate
        self.x += self.vel_x * dt
        self.y += self.vel_y * dt
        # edge bounce for actives
        if self.type in (ObjectType.ACTIVE,):
            if self.x < 0 or self.x + self.w > self.engine.width:
                self.vel_x *= -1
                self.x = clamp(self.x, 0, self.engine.width - self.w)
            if self.y < 0 or self.y + self.h > self.engine.height:
                self.vel_y *= -1
                self.y = clamp(self.y, 0, self.engine.height - self.h)

    def destroy(self):
        if self.canvas_id:
            try:
                self.engine.canvas.delete(self.canvas_id)
            except tk.TclError:
                pass
            self.canvas_id = None
        if self.outline_id:
            try:
                self.engine.canvas.delete(self.outline_id)
            except tk.TclError:
                pass
            self.outline_id = None

    def render(self, canvas: tk.Canvas):
        if not self.visible: return
        if self.type == ObjectType.STRING:
            # draw/update text
            txt = str(self.data.get("text", ""))
            fs = int(self.data.get("font_size", 18))
            if self.canvas_id is None:
                self.canvas_id = canvas.create_text(self.x, self.y, text=txt,
                                                    fill=self.color, anchor="nw",
                                                    font=("TkDefaultFont", fs),
                                                    tags=("layer_string",))
            else:
                if txt != self._text_cache:
                    canvas.itemconfigure(self.canvas_id, text=txt, fill=self.color)
                canvas.coords(self.canvas_id, self.x, self.y)
            self._text_cache = txt
        elif self.type in (ObjectType.COUNTER, ObjectType.ARRAY):
            # non-visual
            return
        else:
            # ACTIVE/BACKDROP rectangles
            if self.canvas_id is None:
                layer = "layer_backdrop" if self.type == ObjectType.BACKDROP else "layer_active"
                self.canvas_id = canvas.create_rectangle(self.x, self.y, self.x+self.w, self.y+self.h,
                                                         outline="", fill=self.color, tags=(layer,))
                if self.type == ObjectType.ACTIVE:
                    self.outline_id = canvas.create_rectangle(self.x, self.y, self.x+self.w, self.y+self.h,
                                                              outline="#111111", width=1, tags=(layer,))
            else:
                canvas.coords(self.canvas_id, self.x, self.y, self.x+self.w, self.y+self.h)
                if self.outline_id:
                    canvas.coords(self.outline_id, self.x, self.y, self.x+self.w, self.y+self.h)

# -------------------------------------------------------------------
# EVENT
# -------------------------------------------------------------------
class Event:
    def __init__(self, event_type: EventType, condition: Optional[Callable[[Dict[str, Any]], bool]] = None,
                 actions: Optional[List[Callable[[Dict[str, Any]], None]]] = None,
                 target: Optional[str] = None, meta: Optional[Dict[str, Any]] = None):
        self.type = event_type
        self.condition = condition or (lambda ctx: True)
        self.actions = actions or []
        self.target = target
        self.meta = meta or {}
        # timer bookkeeping (for ON_TIMER)
        self._acc = 0.0

    def tick_and_trigger(self, ctx: Dict[str, Any]):
        """Handles timers internally and triggers actions when condition matches."""
        if self.type == EventType.ON_TIMER:
            # fixed-interval evaluation
            interval = float(self.meta.get("interval", 1.0))
            self._acc += ctx["dt"]
            if self._acc + 1e-9 >= interval:
                self._acc -= interval
                match = self.condition(ctx)
                if match:
                    for a in self.actions: a(ctx)
        else:
            if self.condition(ctx):
                for a in self.actions: a(ctx)

# -------------------------------------------------------------------
# SAFE EXPRESSION EVALUATOR
# -------------------------------------------------------------------
class ExpressionEvaluator:
    SAFE_GLOBALS = {
        "__builtins__": {},
        "abs": abs, "min": min, "max": max, "round": round, "int": int, "float": float,
        "rand": random.random, "uniform": random.uniform, "randint": random.randint,
        "pi": math.pi, "sin": math.sin, "cos": math.cos, "sqrt": math.sqrt
    }

    @staticmethod
    def safe_eval(expr: str, ctx: Dict[str, Any], obj: Optional[GameObject] = None):
        try:
            locals_dict = {
                "X": obj.x if obj else 0.0, "Y": obj.y if obj else 0.0,
                "W": ctx["engine"].width, "H": ctx["engine"].height,
                "Counter": lambda name: ctx["engine"].get_counter(name),
                "String": lambda name: ctx["engine"].get_string(name),
                **ctx["engine"].counters
            }
            return eval(expr, ExpressionEvaluator.SAFE_GLOBALS, locals_dict)
        except Exception:
            return None

# -------------------------------------------------------------------
# ENGINE
# -------------------------------------------------------------------
class ClickteamTkEngine:
    def __init__(self, width=WIDTH, height=HEIGHT, title="CAT'S CLICKTEAM ENGINE v2.5 – Tkinter Edition"):
        self.width, self.height = width, height
        self.root = tk.Tk()
        self.root.title(title)
        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height, bg=BG, highlightthickness=0)
        self.canvas.pack()

        # State
        self.objects: List[GameObject] = []
        self.events: List[Event] = []
        self.counters: Dict[str, float] = {}
        self.keys_down = set()
        self.time = 0.0
        self.dt = 1.0 / FPS
        self.running = True
        self.paused = False
        self._last_ms = now_ms()
        self._fps = 0.0
        self._frame_counter = 0
        self._fps_acc_ms = 0
        self.show_overlay = True

        # Frames (list-of-object lists); index of current frame
        self.frames: List[List[GameObject]] = [[]]
        self.current_frame_index = 0

        # Bindings
        self.root.bind("<KeyPress>", self._on_keypress)
        self.root.bind("<KeyRelease>", self._on_keyrelease)
        self.root.protocol("WM_DELETE_WINDOW", self._quit)

        # Build menu
        self._build_menu()

        # Schedule loop
        self.root.after(int(self.dt * 1000), self._loop)

        # Draw static tags ordering once
        self.canvas.tag_lower("layer_backdrop")
        self.canvas.tag_lower("layer_active")
        self.canvas.tag_raise("layer_string")

    # ------------------------- Input ------------------------------
    def _on_keypress(self, e):
        key = e.keysym.lower()
        self.keys_down.add(key)
        if key == "escape": self._quit()
        if key == "f1": self.show_overlay = not self.show_overlay
        if key == "p": self.paused = not self.paused
        if key in ("left", "right"):
            delta = -1 if key == "left" else 1
            new_idx = (self.current_frame_index + delta) % max(1, len(self.frames))
            self.change_frame(new_idx)

    def _on_keyrelease(self, e):
        key = e.keysym.lower()
        if key in self.keys_down: self.keys_down.remove(key)

    # ------------------------- Menu -------------------------------
    def _build_menu(self):
        menubar = tk.Menu(self.root)
        build = tk.Menu(menubar, tearoff=0)
        build.add_command(label="Export Windows .exe", command=self.export_exe)
        build.add_command(label="Export macOS .app + .dmg", command=self.export_dmg)
        build.add_command(label="Export HTML (single file)", command=self.export_html)
        menubar.add_cascade(label="Build", menu=build)

        util = tk.Menu(menubar, tearoff=0)
        util.add_command(label="Save manifest (JSON)", command=self.save_project_dialog)
        util.add_separator()
        util.add_command(label="Quit", command=self._quit)
        menubar.add_cascade(label="File", menu=util)
        self.root.config(menu=menubar)

    def save_project_dialog(self):
        try:
            import tkinter.filedialog as fd
            path = fd.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")], initialfile="project_manifest.json")
            if path:
                self.save_project(path)
        except Exception as e:
            print("[Save] Error:", e)

    # ---------------------- Object API ----------------------------
    def create_object(self, obj_type: ObjectType, x=0, y=0, w=32, h=32, color=FG, **data) -> GameObject:
        obj = GameObject(self, obj_type, x, y, w, h, color=color, **data)
        self.objects.append(obj)
        # attach to current frame
        if self.current_frame_index >= len(self.frames):
            self.frames.extend([[] for _ in range(self.current_frame_index - len(self.frames) + 1)])
        self.frames[self.current_frame_index].append(obj)
        # Trigger create events
        ctx = self._ctx()
        ctx["created_obj"] = obj
        for ev in self.events:
            if ev.type == EventType.ON_CREATE and (ev.target is None or ev.target == obj.data.get("id")):
                ev.tick_and_trigger(ctx)
        return obj

    def destroy_object(self, obj_or_id):
        target = obj_or_id
        if isinstance(obj_or_id, str):
            target = self.get_object_by_id(obj_or_id)
        if not target: return
        # fire destroy events
        ctx = self._ctx()
        ctx["destroyed_obj"] = target
        for ev in self.events:
            if ev.type == EventType.ON_DESTROY and (ev.target is None or ev.target == target.data.get("id")):
                ev.tick_and_trigger(ctx)
        # remove
        try:
            for frame_objs in self.frames:
                if target in frame_objs: frame_objs.remove(target)
            if target in self.objects: self.objects.remove(target)
            target.destroy()
        except Exception:
            pass

    def get_object_by_id(self, obj_id: str) -> Optional[GameObject]:
        for o in self.objects:
            if o.data.get("id") == obj_id:
                return o
        return None

    def objects_of_type(self, obj_type: ObjectType) -> List[GameObject]:
        return [o for o in self.objects if o.type == obj_type]

    def pick_by_qualifier(self, name: str) -> List[GameObject]:
        return [o for o in self.objects if name in o.qualifiers]

    # ---------------------- Counters/Strings/Arrays ---------------
    def set_counter(self, name: str, value: float): self.counters[name] = float(value)
    def add_counter(self, name: str, delta: float): self.counters[name] = float(self.counters.get(name, 0.0) + delta)
    def get_counter(self, name: str) -> float: return float(self.counters.get(name, 0.0))

    def set_string(self, obj_id: str, text: str):
        obj = self.get_object_by_id(obj_id)
        if obj and obj.type == ObjectType.STRING:
            obj.data["text"] = str(text)

    def get_string(self, obj_id: str) -> str:
        obj = self.get_object_by_id(obj_id)
        return str(obj.data.get("text","")) if obj and obj.type == ObjectType.STRING else ""

    # Arrays stored inside STRING/ARRAY objects as dict with "(i,j)" -> value
    def array_put(self, arr_id: str, i: int, j: Optional[int], value: Any):
        obj = self.get_object_by_id(arr_id)
        if not obj: return
        store = obj.data.setdefault("contents", {})
        key = f"({i},{j})" if j is not None else f"({i})"
        store[key] = value

    def array_get(self, arr_id: str, i: int, j: Optional[int]):
        obj = self.get_object_by_id(arr_id)
        if not obj: return None
        store = obj.data.get("contents", {})
        key = f"({i},{j})" if j is not None else f"({i})"
        return store.get(key, None)

    # ---------------------- Frames --------------------------------
    def change_frame(self, idx: int):
        if idx < 0 or idx >= len(self.frames): return
        # Remove current frame's visual items (leave objects but hide by clearing canvas)
        for o in self.objects:
            o.destroy()
        self.current_frame_index = idx
        # Trigger frame change
        ctx = self._ctx()
        for ev in self.events:
            if ev.type == EventType.ON_FRAME_CHANGE:
                ev.tick_and_trigger(ctx)

    # ---------------------- Project Save/Load ----------------------
    def save_project(self, filename: str):
        manifest = {
            "width": self.width, "height": self.height, "bg": BG,
            "objects": [
                {
                    "type": o.type.value, "x": o.x, "y": o.y, "w": o.w, "h": o.h,
                    "color": o.color, "visible": o.visible, "opacity": o.opacity,
                    "angle": o.angle, "z": o.z, "qualifiers": sorted(list(o.qualifiers)),
                    "data": o.data
                } for o in self.objects
            ],
            "counters": self.counters,
            "frames": len(self.frames)
        }
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        print(f"[Save] Wrote manifest to {filename}")

    # ---------------------- Loop ----------------------------------
    def _ctx(self) -> Dict[str, Any]:
        return {
            "engine": self,
            "dt": self.dt,
            "time": self.time,
            "keys": self.keys_down,
        }

    def _compute_collisions(self) -> List[Tuple[GameObject, GameObject]]:
        actives = [o for o in self.objects if o.type == ObjectType.ACTIVE]
        pairs = []
        for i in range(len(actives)):
            a = actives[i]
            ax1, ay1, ax2, ay2 = a.rect()
            for j in range(i+1, len(actives)):
                b = actives[j]
                bx1, by1, bx2, by2 = b.rect()
                if (ax1 < bx2 and ax2 > bx1 and ay1 < by2 and ay2 > by1):
                    pairs.append((a,b))
        return pairs

    def _loop(self):
        if not self.running: return
        # dt by wall clock for better stability
        cur = now_ms()
        self.dt = max(0.001, min(0.1, (cur - self._last_ms) / 1000.0))
        self._last_ms = cur

        if not self.paused:
            # events first (conditions may read last frame's state)
            ctx = self._ctx()
            for ev in self.events:
                ev.tick_and_trigger(ctx)

            # physics updates
            for o in list(self.objects):
                o.update(self.dt)

            # detect collisions & raise events that depend on them
            collisions = self._compute_collisions()
            if collisions:
                ctx["collisions"] = collisions
                for ev in self.events:
                    if ev.type == EventType.ON_COLLISION:
                        # optional filters by qualifiers/ids in ev.meta
                        filt = ev.meta.get("filter")
                        if not filt:
                            ev.tick_and_trigger(ctx)
                        else:
                            # filter pairs
                            a_tag, b_tag = filt
                            def match_tag(obj, tag):
                                if tag == "*": return True
                                if tag in (obj.data.get("id"), obj.type.value): return True
                                if tag in obj.qualifiers: return True
                                return False
                            ctx_pairs = [(a,b) for (a,b) in collisions if match_tag(a, a_tag) and match_tag(b, b_tag)]
                            if ctx_pairs:
                                ctx["collisions"] = ctx_pairs
                                ev.tick_and_trigger(ctx)

        # render (persistent items; update coords)
        for o in self.objects:
            o.render(self.canvas)

        # enforce layer ordering
        try:
            self.canvas.tag_lower("layer_backdrop")
            self.canvas.tag_raise("layer_active")
            self.canvas.tag_raise("layer_string")
        except tk.TclError:
            pass

        # overlay + fps
        self._frame_counter += 1
        self._fps_acc_ms += int(self.dt * 1000)
        if self._fps_acc_ms >= 500:  # update twice per second
            self._fps = self._frame_counter / (self._fps_acc_ms / 1000.0)
            self._frame_counter = 0
            self._fps_acc_ms = 0
        if self.show_overlay:
            self._draw_overlay()

        # schedule next frame
        self.root.after(max(1, int(1000 / FPS)), self._loop)

    def _draw_overlay(self):
        # light HUD in the lower-left
        txt = f"FPS {self._fps:4.1f} | objs {len(self.objects)} | frame {self.current_frame_index} | t={self.time:5.2f}"
        # draw text using a dedicated top layer
        if not hasattr(self, "_overlay_id"):
            self._overlay_id = self.canvas.create_text(8, self.height-8, text=txt, fill="#FFFFFF",
                                                       font=("TkDefaultFont", 12), anchor="sw", tags=("layer_string", "overlay"))
        else:
            self.canvas.itemconfigure(self._overlay_id, text=txt)
            self.canvas.coords(self._overlay_id, 8, self.height-8)

    def _quit(self):
        self.running = False
        try:
            self.root.destroy()
        except Exception:
            pass

    # ---------------------- Exporters ------------------------------
    def _ensure_dist(self) -> str:
        dist = os.path.abspath("dist")
        os.makedirs(dist, exist_ok=True)
        return dist

    def _pyinstaller_check(self) -> bool:
        from shutil import which
        return which("pyinstaller") is not None

    def export_exe(self, app_name: str = "CatsEngine"):
        """Windows: EXE via PyInstaller."""
        if platform.system() != "Windows":
            print("[Export] EXE export must be run on Windows host.")
            return
        if not self._pyinstaller_check():
            print("[Export] PyInstaller not found. Install: pip install pyinstaller")
            return
        dist = self._ensure_dist()
        cmd = ["pyinstaller", "--noconfirm", "--onefile", "--windowed", "--name", app_name, os.path.abspath(__file__)]
        print("[Export] Running:", " ".join(cmd))
        subprocess.call(cmd)
        exe_path = os.path.join("dist", f"{app_name}.exe")
        print(f"[Export] Done. Output: {exe_path}")

    def export_dmg(self, app_name: str = "CatsEngine"):
        """macOS: .app via PyInstaller, then .dmg via hdiutil."""
        if platform.system() != "Darwin":
            print("[Export] DMG export must be run on macOS host.")
            return
        if not self._pyinstaller_check():
            print("[Export] PyInstaller not found. Install: pip install pyinstaller")
            return
        dist = self._ensure_dist()
        cmd = ["pyinstaller", "--noconfirm", "--windowed", "--name", app_name, os.path.abspath(__file__)]
        print("[Export] Running:", " ".join(cmd))
        subprocess.call(cmd)
        app_path = os.path.join("dist", f"{app_name}.app")
        dmg_path = os.path.join("dist", f"{app_name}.dmg")
        if os.path.isdir(app_path):
            hdi = ["hdiutil", "create", "-volname", app_name, "-srcfolder", app_path, "-ov", "-format", "UDZO", dmg_path]
            print("[Export] Creating DMG:", " ".join(hdi))
            subprocess.call(hdi)
            print(f"[Export] Done. Output: {dmg_path}")
        else:
            print("[Export] .app not found; PyInstaller may have failed.")

    def export_html(self, app_name: str = "CatsEngine"):
        """Generate a single-file HTML preview that replays a practical subset of the engine."""
        dist = self._ensure_dist()
        html_path = os.path.join(dist, f"{app_name}.html")
        project = self._snapshot_for_html()
        html = self._html_template(project, title=app_name)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[Export] Wrote HTML preview: {html_path}")

    def _snapshot_for_html(self) -> Dict[str, Any]:
        # Convert current runtime into a JS-friendly model
        objs = []
        for o in self.objects:
            od = {"type": o.type.value, "x": o.x, "y": o.y, "w": o.w, "h": o.h, "color": o.color,
                  "vx": o.vel_x, "vy": o.vel_y}
            if o.type == ObjectType.STRING:
                od["text"] = o.data.get("text", "")
                od["fontSize"] = int(o.data.get("font_size", 18))
            objs.append(od)
        # Heuristics: infer demo events if present (space spawn & 5s timer)
        # For a general project, you can edit the resulting HTML to customize events.
        events = {
            "always": {"friction": 0.01},
            "keys": [
                {"key": " ", "actions": [{"type": "spawn", "w": 20, "h": 20,
                                          "color": "#FF0000", "vx1": -40, "vx2": 40, "vy1": -40, "vy2": 40}]}
            ],
            "timers": [
                {"interval": 5.0, "actions": [{"type": "spawn", "w": 20, "h": 20,
                                                "color": "#00AAFF", "vx1": -40, "vx2": 40, "vy1": -40, "vy2": 40}]}
            ]
        }
        return {"width": self.width, "height": self.height, "bg": BG, "objects": objs, "events": events}

    def _html_template(self, project: Dict[str, Any], title: str = "CatsEngine") -> str:
        js = r"""
const PROJECT = __PROJECT_JSON__;
const W = PROJECT.width, H = PROJECT.height;
document.title = __TITLE__;
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
canvas.width = W; canvas.height = H;

const keys = {};
window.addEventListener('keydown', e => { keys[e.key.toLowerCase()] = true; });
window.addEventListener('keyup',   e => { delete keys[e.key.toLowerCase()]; });

let objs = PROJECT.objects.map(o => Object.assign({}, o));
function spawn(rect) {
  const o = Object.assign({type:'active', x:0,y:0,w:20,h:20,color:'#FF0000',vx:0,vy:0}, rect);
  o.x = Math.random()*(W-o.w);
  o.y = Math.random()*(H-o.h);
  objs.push(o);
}

let last = performance.now();
function step(ts) {
  const dt = Math.min(0.1, Math.max(0.001, (ts - last)/1000)); last = ts;

  // ALWAYS: friction
  if (PROJECT.events.always && PROJECT.events.always.friction) {
    const f = PROJECT.events.always.friction;
    for (const o of objs) { if (o.type === 'active') { o.vx *= (1 - f); o.vy *= (1 - f); } }
  }

  // TIMERS
  for (const ev of (PROJECT.events.timers||[])) {
    ev._acc = (ev._acc||0) + dt;
    if (ev._acc >= ev.interval) {
      ev._acc -= ev.interval;
      for (const a of (ev.actions||[])) {
        if (a.type === 'spawn') {
          const vx = Math.random()*(a.vx2 - a.vx1) + a.vx1;
          const vy = Math.random()*(a.vy2 - a.vy1) + a.vy1;
          spawn({w:a.w,h:a.h,color:a.color,vx:vx,vy:vy});
        }
      }
    }
  }

  // KEYS
  for (const ev of (PROJECT.events.keys||[])) {
    const key = (ev.key||'').toLowerCase();
    if ((key === ' ' && keys[' ']) || keys[key]) {
      for (const a of (ev.actions||[])) {
        if (a.type === 'spawn') {
          const vx = Math.random()*(a.vx2 - a.vx1) + a.vx1;
          const vy = Math.random()*(a.vy2 - a.vy1) + a.vy1;
          spawn({w:a.w,h:a.h,color:a.color,vx:vx,vy:vy});
        }
      }
    }
  }

  // MOVE & BOUNCE
  for (const o of objs) {
    if (o.type !== 'active') continue;
    o.x += (o.vx||0)*dt; o.y += (o.vy||0)*dt;
    if (o.x < 0 || o.x + o.w > W) { o.vx *= -1; o.x = Math.max(0, Math.min(W-o.w, o.x)); }
    if (o.y < 0 || o.y + o.h > H) { o.vy *= -1; o.y = Math.max(0, Math.min(H-o.h, o.y)); }
  }

  // DRAW
  ctx.fillStyle = PROJECT.bg; ctx.fillRect(0,0,W,H);
  for (const o of objs) {
    if (o.type === 'string') {
      ctx.fillStyle = o.color || '#FFFFFF';
      ctx.font = `${o.fontSize||18}px sans-serif`;
      ctx.textBaseline = 'top';
      ctx.fillText(o.text||'', o.x, o.y);
    } else if (o.type === 'backdrop') {
      ctx.fillStyle = o.color || '#111111';
      ctx.fillRect(o.x, o.y, o.w, o.h);
    } else {
      ctx.fillStyle = o.color || '#FFFFFF';
      ctx.fillRect(o.x, o.y, o.w, o.h);
      ctx.strokeStyle = '#111111';
      ctx.strokeRect(o.x, o.y, o.w, o.h);
    }
  }
  requestAnimationFrame(step);
}

requestAnimationFrame(step);
"""
        # Inject JSON & title
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>{title}</title>
<style>
html,body{{margin:0;padding:0;background:#000;color:#eee;font-family:system-ui, -apple-system, Segoe UI, Roboto, sans-serif;}}
#wrap{{display:flex;align-items:center;justify-content:center;min-height:100vh;}}
canvas{{image-rendering:pixelated;box-shadow:0 0 0 1px #333, 0 0 20px #000 inset;}}
.note{{position:fixed;left:0;right:0;bottom:0;padding:6px 10px;font-size:12px;color:#aaa;text-align:center;opacity:.8;}}
</style>
</head>
<body>
<div id="wrap">
  <canvas id="c" width="{project['width']}" height="{project['height']}"></canvas>
</div>
<div class="note">HTML preview: SPACE spawns red, timer spawns blue, rectangles bounce. Exported from Tk engine.</div>
<script>
{js.replace("__PROJECT_JSON__", json.dumps(project)).replace("__TITLE__", json.dumps(title))}
</script>
</body>
</html>"""
        return html

# -------------------------------------------------------------------
# DEMO SCENE (you can replace this with your own project setup)
# -------------------------------------------------------------------
def demo_project(engine: ClickteamTkEngine):
    # Backdrop
    engine.create_object(ObjectType.BACKDROP, 0, 0, engine.width, engine.height, color="#111111", id="bg")
    # Moving "cat" block
    cat = engine.create_object(ObjectType.ACTIVE, engine.width/2-25, engine.height/2-15, 50, 30,
                               color="#FFFFFF", vel_x=random.uniform(-90, 90), vel_y=random.uniform(-90, 90), id="cat")
    # UI: score text
    score = engine.create_object(ObjectType.STRING, 8, 8, 0, 0, color="#FFFFFF", id="score_text", font_size=18, text="Score: 0")
    engine.set_counter("score", 0)

    # --- EVENTS ----------------------------------------------------
    # ALWAYS: mild friction
    def always_friction(ctx):
        for o in engine.objects_of_type(ObjectType.ACTIVE):
            o.vel_x *= 0.99
            o.vel_y *= 0.99
    engine.events.append(Event(EventType.ALWAYS, actions=[always_friction]))

    # KEY: SPACE spawns a red block and increments score
    def spawn_red(ctx):
        if "space" in ctx["keys"]:
            engine.create_object(ObjectType.ACTIVE,
                                 random.randint(0, engine.width-20),
                                 random.randint(0, engine.height-20),
                                 20, 20, color="#FF0000",
                                 vel_x=random.uniform(-40,40), vel_y=random.uniform(-40,40))
            engine.add_counter("score", 1)
            engine.set_string("score_text", f"Score: {int(engine.get_counter('score'))}")
    engine.events.append(Event(EventType.ON_KEY_PRESS,
                               condition=lambda c: "space" in c["keys"],
                               actions=[spawn_red]))

    # TIMER: every 5 seconds spawn a blue orb
    def timer_spawn(ctx):
        engine.create_object(ObjectType.ACTIVE,
                             random.randint(0, engine.width-20),
                             random.randint(0, engine.height-20),
                             20, 20, color="#00AAFF",
                             vel_x=random.uniform(-40,40), vel_y=random.uniform(-40,40))
    engine.events.append(Event(EventType.ON_TIMER, actions=[timer_spawn], meta={"interval": 5.0}))

    # COLLISION: on any collision, teleport both
    def warp_on_collision(ctx):
        for (a,b) in ctx.get("collisions", []):
            a.x, a.y = random.randint(0, engine.width-int(a.w)), random.randint(0, engine.height-int(a.h))
            b.x, b.y = random.randint(0, engine.width-int(b.w)), random.randint(0, engine.height-int(b.h))
    engine.events.append(Event(EventType.ON_COLLISION, actions=[warp_on_collision]))

# -------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------
def run_app():
    eng = ClickteamTkEngine(WIDTH, HEIGHT)
    demo_project(eng)
    eng.root.mainloop()

def main():
    ap = argparse.ArgumentParser(description="CAT'S CLICKTEAM ENGINE v2.5 — Tkinter Edition")
    ap.add_argument("--export", choices=["exe","dmg","html"], help="Build target")
    ap.add_argument("--name", default="CatsEngine", help="App name for export")
    args = ap.parse_args()

    if args.export:
        # Create a headless engine instance for exporting snapshot where needed
        eng = ClickteamTkEngine(WIDTH, HEIGHT, title="Build Mode")
        # Don't show window during export
        eng.root.withdraw()
        demo_project(eng)
        if args.export == "exe":
            eng.export_exe(args.name)
        elif args.export == "dmg":
            eng.export_dmg(args.name)
        elif args.export == "html":
            eng.export_html(args.name)
        try:
            eng.root.destroy()
        except Exception:
            pass
        return

    # Run interactive
    run_app()

if __name__ == "__main__":
    main()
