#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Cat's Rave.dj 0.1 — Unlimited Mashup Generator
# Adapted from HQRIPPER backend with RaveDJ-style UI (Files = Off)
# Python 3.13 / 3.14 compatible, supports unlimited remixes from YouTube URLs
# -----------------------------------------------------------------------------

from __future__ import annotations

import sys
import os
import subprocess
import importlib.util
import threading
import random
from pathlib import Path

import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from tkinter.constants import DEVNULL

# -----------------------------------------------------------------------------
# Environment + encoding (be liberal; don't crash if not supported)
# -----------------------------------------------------------------------------
os.environ.setdefault("PYTHONUTF8", "1")
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

# -----------------------------------------------------------------------------
# Tiny helpers
# -----------------------------------------------------------------------------
def ensure_package(import_name: str, pip_spec: str | None = None):
    """
    Ensure a Python package is available. `import_name` is the module to import.
    `pip_spec` is the spec passed to pip (can include version constraints).
    """
    pip_spec = pip_spec or import_name
    if importlib.util.find_spec(import_name) is None:
        # Use --upgrade to avoid old, incompatible versions
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", pip_spec],
            check=True,
            text=True,
        )

def _has_ffmpeg() -> bool:
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=DEVNULL,
            stderr=DEVNULL,
            check=True,
        )
        return True
    except Exception:
        return False

def ensure_ffmpeg() -> bool:
    """
    Check for FFmpeg; if missing, offer best-effort install and re-check.
    """
    if _has_ffmpeg():
        return True

    resp = messagebox.askyesno(
        "FFmpeg Missing",
        "FFmpeg is not installed or not in PATH.\n\n"
        "Attempt automatic installation?\n\n"
        "• Windows: winget (Gyan.FFmpeg)\n"
        "• macOS: Homebrew (brew install ffmpeg)\n"
        "• Linux (Debian/Ubuntu): apt-get (requires sudo)",
    )
    if not resp:
        return False

    try:
        if sys.platform.startswith("win"):
            subprocess.run(["winget", "install", "-e", "--id", "Gyan.FFmpeg"], check=False)
        elif sys.platform == "darwin":
            subprocess.run(["brew", "install", "ffmpeg"], check=False)
        else:
            subprocess.run(["sudo", "apt-get", "update"], check=False)
            subprocess.run(["sudo", "apt-get", "install", "-y", "ffmpeg"], check=False)
    except Exception:
        pass

    return _has_ffmpeg()

# -----------------------------------------------------------------------------
# Tk root early so we can show setup dialogs
# -----------------------------------------------------------------------------
root = tk.Tk()
root.withdraw()
messagebox.showinfo("Cat's Rave.dj 0.1 Setup Wizard", "Checking dependencies…")

# -----------------------------------------------------------------------------
# Dependencies (Python 3.13+ removed stdlib audioop → use audioop-lts)
# -----------------------------------------------------------------------------
try:
    ensure_package("yt_dlp")
    # Prefer latest pydub (older versions relied more on stdlib audioop)
    ensure_package("pydub")
    if sys.version_info >= (3, 13):
        # pip package name is "audioop-lts" but import name remains "audioop"
        ensure_package("audioop", "audioop-lts")
    import yt_dlp
    from pydub import AudioSegment
except Exception as e:
    messagebox.showerror("Setup Failed", f"Dependency install failed:\n{e}")
    sys.exit(1)

if not ensure_ffmpeg():
    messagebox.showerror(
        "FFmpeg Required",
        "FFmpeg is still missing. Please install it manually and try again.",
    )
    sys.exit(1)

# -----------------------------------------------------------------------------
# UI-thread marshaling (Tkinter is not thread-safe)
# -----------------------------------------------------------------------------
def ui_call(fn, *args, **kwargs):
    root.after(0, lambda: fn(*args, **kwargs))

# -----------------------------------------------------------------------------
# Core logic
# -----------------------------------------------------------------------------
def download_audio(urls: list[str], output_dir: str) -> list[str]:
    """
    Download audio (single videos or playlists) as MP3 using yt_dlp.
    Returns a list of existing .mp3 file paths created by the run.
    """
    os.makedirs(output_dir, exist_ok=True)
    # Unique filenames via title + id to avoid collisions across playlists
    outtmpl = os.path.join(output_dir, "%(title).200B-%(id)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "overwrites": True,
        "ignoreerrors": "only_download",
        "quiet": True,
        "no_warnings": True,
    }

    produced: list[str] = []

    def _collect_from_entry(ydl: yt_dlp.YoutubeDL, entry: dict | None):
        if not entry:
            return
        pre = ydl.prepare_filename(entry)  # path with original ext
        mp3_path = os.path.splitext(pre)[0] + ".mp3"
        if os.path.isfile(mp3_path):
            produced.append(mp3_path)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for url in urls:
            info = ydl.extract_info(url, download=True)
            # Playlist or multi-entry
            if isinstance(info, dict) and (info.get("_type") == "playlist" or "entries" in info):
                for ent in info.get("entries", []):
                    _collect_from_entry(ydl, ent)
            else:
                _collect_from_entry(ydl, info)

    # De-duplicate and keep only files that actually exist
    uniq = []
    seen = set()
    for p in produced:
        if p not in seen and os.path.isfile(p):
            uniq.append(p)
            seen.add(p)
    return uniq

def _normalize(seg: AudioSegment) -> AudioSegment:
    """
    Ensure consistent parameters so overlays behave (44.1kHz, stereo, 16-bit).
    """
    return seg.set_frame_rate(44100).set_channels(2).set_sample_width(2)

def _safe_random_slice(seg: AudioSegment, min_len_ms: int, max_len_ms: int) -> AudioSegment:
    """
    Take a random slice of seg with a duration in [min_len_ms, max_len_ms],
    but never exceed seg length; if seg is shorter than min_len_ms, return seg.
    """
    L = len(seg)
    if L <= min_len_ms:
        return seg
    dur = random.randint(min_len_ms, min(max_len_ms, L))
    start_max = L - dur
    start = random.randint(0, max(0, start_max))
    return seg[start : start + dur]

def generate_mashups(audio_files: list[str], num_mashups: int, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)

    # Load and normalize audio files
    audios: list[AudioSegment] = []
    for f in audio_files:
        try:
            seg = AudioSegment.from_file(f)
            audios.append(_normalize(seg))
        except Exception as e:
            print(f"[WARN] Skipping '{f}': {e}")

    if not audios:
        raise RuntimeError("No audio files could be loaded.")

    # Build mashups
    for i in range(1, num_mashups + 1):
        base = random.choice(audios)
        # Base duration: up to full track; prefer at least 20s if available
        base_slice = _safe_random_slice(base, min_len_ms=10000, max_len_ms=min(60000, len(base)))
        mashup = base_slice

        # Overlay 2–5 random slices (3–15s each), faded & gain-shifted
        layers = random.randint(2, 5)
        for _ in range(layers):
            overlay_src = random.choice(audios)
            if len(overlay_src) < 2500:
                continue
            seg = _safe_random_slice(overlay_src, min_len_ms=5000, max_len_ms=20000)
            # Gentle fades; scale with length
            fade_amt = max(150, min(800, len(seg) // 12))
            seg = seg.fade_in(fade_amt).fade_out(fade_amt)
            # Random gain between -6 dB and +3 dB
            seg = seg + random.uniform(-6.0, 3.0)
            # Position within current mashup length
            pos = random.randint(0, max(0, len(mashup) - len(seg)))
            mashup = mashup.overlay(seg, position=pos)

        # Tail fade (≤ 5s or 25% of length)
        mashup = mashup.fade_out(min(5000, max(500, len(mashup) // 4)))

        out_path = os.path.join(output_dir, f"mashup_{i:02d}.mp3")
        mashup.export(out_path, format="mp3", bitrate="192k")

# -----------------------------------------------------------------------------
# UI actions (thread-safe)
# -----------------------------------------------------------------------------
_text1: tk.Text
_text2: tk.Text
_spin_mashups: tk.Spinbox
_entry_output: tk.Entry
_generate_button: ttk.Button
_console: tk.Text
_prog: ttk.Progressbar

def get_urls_from_text(text_widget: tk.Text) -> list[str]:
    raw = text_widget.get(1.0, tk.END).strip()
    return [u.strip() for chunk in raw.split(",") for u in chunk.split() if (u := u.strip())]

def console_update(msg: str):
    _console.config(state=tk.NORMAL)
    _console.insert(tk.END, msg + "\n")
    _console.see(tk.END)
    _console.config(state=tk.DISABLED)

def browse_output():
    selected = filedialog.askdirectory()
    if selected:
        _entry_output.delete(0, tk.END)
        _entry_output.insert(0, selected)

def stop_action():
    messagebox.showinfo("Stop", "Stopping generation... (Remixes may continue in background.)")

def run_generate():
    urls1 = get_urls_from_text(_text1)
    urls2 = get_urls_from_text(_text2)
    urls = urls1 + urls2
    if not urls:
        messagebox.showerror("Error", "Please enter at least one YouTube URL in Track 1 or Track 2.")
        return

    try:
        n = int(_spin_mashups.get())
        if n <= 0:
            raise ValueError
    except Exception:
        messagebox.showerror("Error", "Invalid number of mashups.")
        return

    outdir = _entry_output.get().strip()
    if not outdir:
        outdir = filedialog.askdirectory(title="Select Output Folder")
        if not outdir:
            return

    _generate_button.config(state="disabled", text="Generating…")
    _prog.start()

    def worker():
        try:
            ui_call(console_update, "[INFO] Starting download of tracks...")
            files = download_audio(urls, outdir)
            if not files:
                raise RuntimeError(
                    "No audio files were downloaded.\n\n"
                    "Tip: Make sure the links are public and available."
                )
            ui_call(console_update, f"[INFO] Downloaded {len(files)} audio tracks.")
            if len(files) < 2:
                ui_call(console_update, "[WARN] Only one track found; remixes will use self-overlays.")
            ui_call(console_update, f"[INFO] Generating {n} mashups...")
            generate_mashups(files, n, outdir)
            ui_call(console_update, "[SUCCESS] All mashups generated successfully!")
            ui_call(
                messagebox.showinfo,
                "Success",
                f"{n} Unlimited Mashups generated!\nSaved in:\n{outdir}",
            )
        except Exception as e:
            ui_call(console_update, f"[ERROR] Generation failed: {e}")
            ui_call(messagebox.showerror, "Error", f"An error occurred:\n{e}")
        finally:
            ui_call(lambda: _generate_button.config(state="normal", text="Generate Mashup!"))
            ui_call(_prog.stop)

    threading.Thread(target=worker, daemon=True).start()

# -----------------------------------------------------------------------------
# GUI
# -----------------------------------------------------------------------------
def build_ravedj_gui():
    global _text1, _text2, _spin_mashups, _entry_output, _generate_button, _console, _prog

    root.deiconify()
    root.title("Cat's Rave.dj 0.1 — Unlimited Mashup Edition")
    root.geometry("640x480")
    root.config(bg="#0a0a0a")
    root.resizable(False, False)

    # --- Banner ---
    title = tk.Label(root, text="Cat's Rave.dj 0.1", font=("Lucida Console", 15, "bold"), fg="#00ffcc", bg="#0a0a0a")
    title.pack(pady=10)
    sub = tk.Label(root, text="(Files = Off Mode - YouTube URLs Only)", fg="#aaaaaa", bg="#0a0a0a", font=("Arial", 9))
    sub.pack(pady=2)

    # --- Track 1 URL Entry ---
    tk.Label(root, text="Track 1 YouTube URLs (comma-separated):", fg="#cccccc", bg="#0a0a0a", font=("Arial", 10)).pack(pady=5)
    _text1 = tk.Text(root, height=3, width=70, bg="#111111", fg="#00ffcc", insertbackground="#00ffcc")
    _text1.pack(pady=5)

    # --- Track 2 URL Entry ---
    tk.Label(root, text="Track 2 YouTube URLs (comma-separated):", fg="#cccccc", bg="#0a0a0a", font=("Arial", 10)).pack(pady=5)
    _text2 = tk.Text(root, height=3, width=70, bg="#111111", fg="#00ffcc", insertbackground="#00ffcc")
    _text2.pack(pady=5)

    # --- Mashup Count ---
    frame_count = tk.Frame(root, bg="#0a0a0a")
    frame_count.pack(pady=5)
    tk.Label(frame_count, text="Number of Mashups:", fg="#cccccc", bg="#0a0a0a", font=("Arial", 10)).pack(side=tk.LEFT)
    _spin_mashups = tk.Spinbox(frame_count, from_=1, to=999, width=6, bg="#111111", fg="#ffffff", insertbackground="#ffffff")
    _spin_mashups.pack(side=tk.LEFT, padx=5)
    _spin_mashups.delete(0, tk.END)
    _spin_mashups.insert(0, "5")

    # --- Output Folder ---
    frame_output = tk.Frame(root, bg="#0a0a0a")
    frame_output.pack(pady=5)
    tk.Label(frame_output, text="Output Folder:", fg="#cccccc", bg="#0a0a0a", font=("Arial", 10)).pack(side=tk.LEFT)
    _entry_output = tk.Entry(frame_output, width=40, bg="#111111", fg="#ffffff", insertbackground="#ffffff")
    _entry_output.pack(side=tk.LEFT, padx=5)
    ttk.Button(frame_output, text="Browse", command=browse_output).pack(side=tk.LEFT)

    # --- Buttons ---
    frame_btns = tk.Frame(root, bg="#0a0a0a")
    frame_btns.pack(pady=15)
    _generate_button = ttk.Button(frame_btns, text="Generate Mashup!", width=25, command=run_generate)
    _generate_button.pack(side=tk.LEFT, padx=8)
    ttk.Button(frame_btns, text="Stop", width=10, command=stop_action).pack(side=tk.LEFT)

    # --- Progress Bar ---
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("DJ.Horizontal.TProgressbar", troughcolor="#222", background="#00ffcc", thickness=20)
    _prog = ttk.Progressbar(root, style="DJ.Horizontal.TProgressbar", mode="indeterminate", length=500)
    _prog.pack(pady=20)

    # --- Console Output ---
    _console = tk.Text(root, height=6, width=75, bg="#000000", fg="#00ff00", insertbackground="#00ff00")
    _console.insert(tk.END, "[BOOT] Cat's Rave.dj 0.1 Engine loaded.\n")
    _console.insert(tk.END, "[INFO] Unlimited remixes: Set any number up to 999.\n")
    _console.insert(tk.END, "[INFO] Files = Off: YouTube URLs only.\n")
    _console.insert(tk.END, "[READY] Enter URLs for Track 1 and Track 2 to start mashing...\n")
    _console.config(state=tk.DISABLED)
    _console.pack(pady=5)

    # --- Footer ---
    footer = tk.Label(root, text="© Samsoft 1999-2025 — Cat's Rave.dj 0.1", fg="#555555", bg="#0a0a0a", font=("Consolas", 9))
    footer.pack(side=tk.BOTTOM, pady=10)

    # Enter to start
    root.bind("<Return>", lambda _e: run_generate())

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    build_ravedj_gui()
    root.mainloop()
