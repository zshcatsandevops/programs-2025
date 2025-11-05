#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# cat's HQRIPPER 9.1 — SiIvaGunner-style remix generator
# Python 3.13 / 3.14 compatible (uses audioop-lts), thread-safe UI, safer slicing
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
from tkinter import messagebox, filedialog

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
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
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
messagebox.showinfo("HQRIPPER 9.1 Setup Wizard", "Checking dependencies…")

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


def remix_audios(audio_files: list[str], num_songs: int, output_dir: str):
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

    # Build remixes
    for i in range(1, num_songs + 1):
        base = random.choice(audios)
        # Base duration: up to full track; prefer at least 20s if available
        base_slice = _safe_random_slice(base, min_len_ms=8000, max_len_ms=max(20000, len(base)))
        remix = base_slice

        # Overlay 2–5 random slices (3–15s each), faded & gain-shifted
        layers = random.randint(2, 5)
        for _ in range(layers):
            overlay_src = random.choice(audios)
            if len(overlay_src) < 2500:
                continue
            seg = _safe_random_slice(overlay_src, min_len_ms=3000, max_len_ms=15000)
            # Gentle fades; scale with length
            fade_amt = max(150, min(800, len(seg) // 12))
            seg = seg.fade_in(fade_amt).fade_out(fade_amt)
            # Random gain between -6 dB and +3 dB
            seg = seg + random.uniform(-6.0, 3.0)
            # Position within current remix length
            pos = random.randint(0, max(0, len(remix) - len(seg)))
            remix = remix.overlay(seg, position=pos)

        # Tail fade (≤ 2.5s or 20% of length)
        remix = remix.fade_out(min(2500, max(250, len(remix) // 5)))

        out_path = os.path.join(output_dir, f"rip_{i:02d}.mp3")
        remix.export(out_path, format="mp3", bitrate="192k")


# -----------------------------------------------------------------------------
# UI actions (thread-safe)
# -----------------------------------------------------------------------------
_urls_entry: tk.Entry
_num_entry: tk.Entry
_rip_button: tk.Button


def run_rip():
    urls_raw = _urls_entry.get().strip()
    if not urls_raw:
        messagebox.showerror("Error", "Please enter at least one YouTube URL.")
        return
    # Split by commas or whitespace, remove empties
    urls = [u.strip() for chunk in urls_raw.split(",") for u in chunk.split() if u.strip()]
    if not urls:
        messagebox.showerror("Error", "No valid URLs found.")
        return

    try:
        n = int(_num_entry.get())
        if n <= 0:
            raise ValueError
    except Exception:
        messagebox.showerror("Error", "Invalid number of rips.")
        return

    outdir = filedialog.askdirectory(title="Select Output Folder")
    if not outdir:
        return

    _rip_button.config(state="disabled", text="Generating…")

    def worker():
        try:
            files = download_audio(urls, outdir)
            if not files:
                raise RuntimeError(
                    "No audio files were downloaded.\n\n"
                    "Tip: Make sure the links are public and available."
                )
            remix_audios(files, n, outdir)
            ui_call(
                messagebox.showinfo,
                "Success",
                f"{n} High-Quality Rips generated!\nSaved in:\n{outdir}",
            )
        except Exception as e:
            ui_call(messagebox.showerror, "Error", f"An error occurred:\n{e}")
        finally:
            ui_call(_rip_button.config, state="normal", text="High Quality Rip!")

    threading.Thread(target=worker, daemon=True).start()


# -----------------------------------------------------------------------------
# GUI
# -----------------------------------------------------------------------------
def build_gui():
    global _urls_entry, _num_entry, _rip_button

    root.deiconify()
    root.title("cat's HQRIPPER 9.1 — Python 3.13/3.14 Edition")
    root.geometry("560x390")
    root.config(bg="#181818")
    root.resizable(False, False)

    pad = dict(pady=8)

    tk.Label(
        root, text="YouTube URLs (comma or whitespace separated):",
        fg="white", bg="#181818"
    ).pack(**pad)

    _urls_entry = tk.Entry(root, width=70)
    _urls_entry.pack()
    _urls_entry.focus_set()

    tk.Label(
        root, text="Number of Rips to Generate:",
        fg="white", bg="#181818"
    ).pack(**pad)

    _num_entry = tk.Entry(root, width=10)
    _num_entry.insert(0, "3")
    _num_entry.pack()

    _rip_button = tk.Button(
        root, text="High Quality Rip!", width=28, height=2,
        command=run_rip, bg="#404040", fg="white", activebackground="#505050"
    )
    _rip_button.pack(pady=20)

    tk.Label(
        root,
        text=(
            "Inspired by SiIvaGunner — HQRIPPER 9.1\n"
            "Use only content you have permission to remix."
        ),
        fg="#aaaaaa", bg="#181818", font=("Arial", 9)
    ).pack(pady=10)

    # Enter to start
    root.bind("<Return>", lambda _e: run_rip())


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    build_gui()
    root.mainloop()
