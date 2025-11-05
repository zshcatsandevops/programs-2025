    #!/usr/bin/env python3
    # -*- coding: utf-8 -*-
    # -----------------------------------------------------------------------------
    # Cat's Rave.dj Pro 2.0 — Professional Mashup Engine (FIXED)
    # Full-featured RaveDJ clone with BPM matching, key detection, stem separation
    # Python 3.13+ compatible, unlimited remixes from YouTube URLs
    # -----------------------------------------------------------------------------
    #
    # --- FIXES APPLIED ---
    # 1.  [FEATURE] Implemented Stem Separation logic:
    #     - Added `STEM_MIX` to `MashupStyle` and the UI.
    #     - The worker thread now calls `StemSeparator` if the checkbox is ticked.
    #     - `TrackInfo` dataclass now stores stem paths.
    #     - `MashupGenerator` now has a new logic path for `STEM_MIX` which
    #       creates a mix using Vocals(T1) + Instrumental(T2).
    # 2.  [BUG] Fixed `apply_mastering`: The `compressed` audio was calculated
    #     but never assigned back to the `audio` variable. It is now.
    # 3.  [BUG] Fixed `apply_effects`: The `filter_sweep` effect was broken as
    #     `scipy.signal.butter` does not accept an array for the cutoff.
    #     Replaced it with a functional `static_lowpass` and updated the
    Choose
    #     `effects` list for the AGGRESSIVE style.
    # 4.  [FIX] Improved `StemSeparator`:
    #     - Switched from `--two-stems` to the 4-stem model (`htdemucs_4s`)
    #       for more professional results (vocals, bass, drums, other).
    #     - Added error checking for the `subprocess.run` call to log
    #       failures during stem separation.
    #     - Updated output directory path to match the 4-stem model name.
    # 5.  [CLEANUP] Removed unused `pydub` dependency and imports.
    #     The script was already using `librosa` and `soundfile` for I/O.
    # 6.  [TYPING] Added `Optional`, `List`, `Tuple`, `Dict`, `Any` imports
    #     and updated `TrackInfo` to support `Optional[Dict[...]]` for stems.
    #
    # -----------------------------------------------------------------------------

    from __future__ import annotations

    import sys
    import os
    import subprocess
    import importlib.util
    import threading
    import random
    import json
    import tempfile
    import shutil
    import time
    import re
    from pathlib import Path
    from typing import Optional, List, Tuple, Dict, Any
    from dataclasses import dataclass, field
    from enum import Enum

    import tkinter as tk
    from tkinter import messagebox, filedialog, ttk, scrolledtext
    from tkinter.constants import DEVNULL

    # -----------------------------------------------------------------------------
    # Environment setup
    # -----------------------------------------------------------------------------
    os.environ.setdefault("PYTHONUTF8", "1")
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8")
        except Exception:
            pass

    # -----------------------------------------------------------------------------
    # Data structures
    # -----------------------------------------------------------------------------
    @dataclass
    class TrackInfo:
        """Metadata for analyzed tracks"""
        path: str
        title: str
        bpm: float
        key: str
        energy: float
        duration: float
        beats: List[float]
        sections: List[Tuple[float, float]]
        # FIX: Added field to store paths to separated stems
        stems: Optional[Dict[str, str]] = field(default_factory=dict)

    class MashupStyle(Enum):
        """Different mashup generation styles"""
        CLASSIC = "classic"
        AGGRESSIVE = "aggressive"
        SMOOTH = "smooth"
        EXPERIMENTAL = "experimental"
        HARMONIC = "harmonic"
        # FIX: Added a new style for stem mixing
        STEM_MIX = "stem_mix"
        DRUM_N_BASS = "dnb"
        TRAP = "trap"
        HOUSE = "house"

    # -----------------------------------------------------------------------------
    # Dependency management
    # -----------------------------------------------------------------------------
    def ensure_package(import_name: str, pip_spec: str | None = None):
        """Ensure a Python package is available."""
        pip_spec = pip_spec or import_name
        if importlib.util.find_spec(import_name) is None:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", pip_spec],
                check=True,
                text=True,
                stdout=DEVNULL,
                stderr=DEVNULL
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
        """Check for FFmpeg; if missing, offer best-effort install."""
        if _has_ffmpeg():
            return True

        resp = messagebox.askyesno(
            "FFmpeg Missing",
            "FFmpeg is required for audio processing.\n\n"
            "Attempt automatic installation?\n\n"
            "• Windows: winget (Gyan.FFmpeg)\n"
            "• macOS: Homebrew (brew install ffmpeg)\n"
            "• Linux: apt-get (requires sudo)",
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
    # Early Tk setup
    # -----------------------------------------------------------------------------
    root = tk.Tk()
    root.withdraw()

    loading_window = tk.Toplevel(root)
    loading_window.title("Cat's Rave.dj Pro 2.0")
    loading_window.geometry("400x200")
    loading_window.configure(bg="#1a1a1a")

    loading_label = tk.Label(
        loading_window,
        text="🎵 Cat's Rave.dj Pro 2.0 🎵\n\nInitializing professional audio engine...",
        font=("Arial", 12, "bold"),
        fg="#00ffcc",
        bg="#1a1a1a"
    )
    loading_label.pack(pady=30)

    loading_progress = ttk.Progressbar(
        loading_window,
        mode="indeterminate",
        length=300
    )
    loading_progress.pack(pady=20)
    loading_progress.start()

    loading_status = tk.Label(
        loading_window,
        text="Installing dependencies...",
        font=("Arial", 9),
        fg="#888888",
        bg="#1a1a1a"
    )
    loading_status.pack()

    loading_window.update()

    # -----------------------------------------------------------------------------
    # Install dependencies
    # -----------------------------------------------------------------------------
    try:
        loading_status.config(text="Installing core packages...")
        loading_window.update()
        
        ensure_package("yt_dlp")
        # FIX: Removed unused pydub dependency
        # ensure_package("pydub")
        ensure_package("numpy")
        ensure_package("scipy")
        
        loading_status.config(text="Installing audio analysis libraries...")
        loading_window.update()
        
        ensure_package("librosa")
        ensure_package("soundfile")
        ensure_package("pyrubberband")
        ensure_package("madmom")
        
        loading_status.config(text="Installing stem separation (Demucs)...")
        loading_window.update()
        
        ensure_package("demucs")
        
        if sys.version_info >= (3, 13):
            ensure_package("audioop", "audioop-lts")
        
        # Import after installation
        import yt_dlp
        # FIX: Removed unused pydub imports
        # from pydub import AudioSegment
        # from pydub.effects import normalize
        import numpy as np
        import scipy.signal
        import librosa
        import soundfile as sf
        import pyrubberband as pyrb
        import madmom
        
        loading_status.config(text="Checking FFmpeg...")
        loading_window.update()
        
    except Exception as e:
        loading_window.destroy()
        messagebox.showerror("Setup Failed", f"Dependency installation failed:\n{e}")
        sys.exit(1)

    if not ensure_ffmpeg():
        loading_window.destroy()
        messagebox.showerror(
            "FFmpeg Required",
            "FFmpeg is required. Please install it manually and try again.",
        )
        sys.exit(1)

    loading_status.config(text="Ready!")
    loading_window.update()
    time.sleep(1)
    loading_window.destroy()

    # -----------------------------------------------------------------------------
    # Audio Analysis Engine
    # -----------------------------------------------------------------------------
    class AudioAnalyzer:
        """Professional audio analysis with BPM, key detection, and beat tracking"""
        
        # Camelot wheel for harmonic mixing
        CAMELOT_WHEEL = {
            'C major': '8B', 'A minor': '8A',
            'G major': '9B', 'E minor': '9A',
            'D major': '10B', 'B minor': '10A',
            'A major': '11B', 'F# minor': '11A',
            'E major': '12B', 'C# minor': '12A',
            'B major': '1B', 'G# minor': '1A',
            'F# major': '2B', 'D# minor': '2A',
            'C# major': '3B', 'A# minor': '3A',
            'G# major': '4B', 'F minor': '4A',
            'D# major': '5B', 'C minor': '5A',
            'A# major': '6B', 'G minor': '6A',
            'F major': '7B', 'D minor': '7A'
        }
        
        @staticmethod
        def analyze_track(file_path: str, progress_callback=None) -> TrackInfo:
            """Comprehensive track analysis"""
            if progress_callback:
                progress_callback("Loading audio...")
            
            # Load audio with librosa
            y, sr = librosa.load(file_path, sr=44100, mono=False)
            if len(y.shape) > 1:
                y = librosa.to_mono(y)
            
            if progress_callback:
                progress_callback("Detecting BPM...")
            
            # BPM detection using multiple methods for accuracy
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units='time')
            
            # Refine BPM with madmom
            try:
                proc = madmom.features.beats.DBNBeatTrackingProcessor(fps=100)
                act = madmom.features.beats.RNNBeatProcessor()(file_path)
                beat_times = proc(act)
                if len(beat_times) > 1:
                    intervals = np.diff(beat_times)
                    refined_tempo = 60.0 / np.median(intervals)
                    tempo = refined_tempo
                    beats = beat_times
            except:
                pass
            
            if progress_callback:
                progress_callback("Detecting key...")
            
            # Key detection
            chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
            chroma_mean = np.mean(chroma, axis=1)
            
            # Key profiles for major and minor
            major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
            minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
            
            key_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            
            major_scores = []
            minor_scores = []
            
            for shift in range(12):
                shifted_chroma = np.roll(chroma_mean, shift)
                major_scores.append(np.corrcoef(shifted_chroma, major_profile)[0, 1])
                minor_scores.append(np.corrcoef(shifted_chroma, minor_profile)[0, 1])
            
            major_key_idx = np.argmax(major_scores)
            minor_key_idx = np.argmax(minor_scores)
            
            if major_scores[major_key_idx] > minor_scores[minor_key_idx]:
                key = f"{key_names[major_key_idx]} major"
            else:
                key = f"{key_names[minor_key_idx]} minor"
            
            if progress_callback:
                progress_callback("Analyzing energy...")
            
            # Energy analysis
            rms = librosa.feature.rms(y=y)[0]
            energy = float(np.mean(rms))
            
            # Section detection
            if progress_callback:
                progress_callback("Detecting sections...")
            
            sections = []
            hop_length = 512
            C = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop_length)
            bounds = librosa.segment.agglomerative(C, k=8)
            bound_times = librosa.frames_to_time(bounds, sr=sr, hop_length=hop_length)
            
            for i in range(len(bound_times) - 1):
                sections.append((bound_times[i], bound_times[i + 1]))
            
            # Get track title
            title = Path(file_path).stem
            duration = float(len(y) / sr)
            
            return TrackInfo(
                path=file_path,
                title=title,
                bpm=float(tempo),
                key=key,
                energy=energy,
                duration=duration,
                beats=list(beats),
                sections=sections
                # Note: `stems` field is populated later in the worker
            )
        
        @staticmethod
        def are_keys_compatible(key1: str, key2: str) -> bool:
            """Check if two keys are harmonically compatible"""
            camelot1 = AudioAnalyzer.CAMELOT_WHEEL.get(key1, '1A')
            camelot2 = AudioAnalyzer.CAMELOT_WHEEL.get(key2, '1A')
            
            # Compatible if same, adjacent, or relative major/minor
            num1 = int(camelot1[:-1])
            type1 = camelot1[-1]
            num2 = int(camelot2[:-1])
            type2 = camelot2[-1]
            
            # Same key
            if camelot1 == camelot2:
                return True
            
            # Adjacent keys on wheel
            if type1 == type2:
                diff = abs(num1 - num2)
                if diff == 1 or diff == 11:
                    return True
            
            # Relative major/minor
            if num1 == num2 and type1 != type2:
                return True
            
            return False

    # -----------------------------------------------------------------------------
    # Stem Separation Engine
    # -----------------------------------------------------------------------------
    class StemSeparator:
        """Neural stem separation using Demucs"""
        
        @staticmethod
        def separate_stems(file_path: str, output_dir: str, progress_callback=None) -> Dict[str, str]:
            """Separate audio into drums, bass, vocals, other"""
            if progress_callback:
                progress_callback("Separating stems (this may take a while)...")
            
            stems = {}
            temp_dir = Path(output_dir) / "stems_temp"
            temp_dir.mkdir(exist_ok=True)
            
            try:
                # Run Demucs separation
                # FIX: Switched to 4-stem model for better results
                cmd = [
                    sys.executable, "-m", "demucs",
                    "-n", "htdemucs_4s",  # Use 4-stem model
                    "-o", str(temp_dir),
                    file_path
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                # FIX: Added error checking
                if result.returncode != 0:
                    if progress_callback:
                        progress_callback(f"Demucs failed (code {result.returncode}):")
                        progress_callback(f"STDOUT: {result.stdout[:200]}...")
                        progress_callback(f"STDERR: {result.stderr[:200]}...")
                    return stems
                
                # Find output files
                track_name = Path(file_path).stem
                # FIX: Updated path to match 4-stem model name
                stem_dir = temp_dir / "htdemucs_4s" / track_name
                
                if stem_dir.exists():
                    for stem_file in stem_dir.glob("*.wav"):
                        stem_name = stem_file.stem
                        output_path = Path(output_dir) / f"{track_name}_{stem_name}.wav"
                        shutil.copy2(stem_file, output_path)
                        stems[stem_name] = str(output_path)
                
            except Exception as e:
                if progress_callback:
                    progress_callback(f"Stem separation failed: {e}")
            finally:
                # Cleanup
                if temp_dir.exists():
                    shutil.rmtree(temp_dir, ignore_errors=True)
            
            return stems

    # -----------------------------------------------------------------------------
    # Advanced Mashup Generator
    # -----------------------------------------------------------------------------
    class MashupGenerator:
        """Professional mashup generation with tempo matching and harmonic mixing"""
        
        def __init__(self):
            self.analyzer = AudioAnalyzer()
            self.stem_separator = StemSeparator()
        
        def time_stretch(self, audio: np.ndarray, sr: int, target_bpm: float, current_bpm: float) -> np.ndarray:
            """Time stretch audio to match target BPM"""
            stretch_factor = current_bpm / target_bpm
            return pyrb.time_stretch(audio, sr, stretch_factor)
        
        def pitch_shift(self, audio: np.ndarray, sr: int, semitones: int) -> np.ndarray:
            """Pitch shift audio by semitones"""
            return pyrb.pitch_shift(audio, sr, semitones)
        
        def beatmatch_tracks(self, track1: TrackInfo, track2: TrackInfo, 
                            audio1: np.ndarray, audio2: np.ndarray, sr: int) -> Tuple[np.ndarray, np.ndarray]:
            """Match BPM of two tracks"""
            target_bpm = (track1.bpm + track2.bpm) / 2
            
            audio1_stretched = self.time_stretch(audio1, sr, target_bpm, track1.bpm)
            audio2_stretched = self.time_stretch(audio2, sr, target_bpm, track2.bpm)
            
            return audio1_stretched, audio2_stretched
        
        def harmonic_mix(self, track1: TrackInfo, track2: TrackInfo,
                        audio1: np.ndarray, audio2: np.ndarray, sr: int) -> Tuple[np.ndarray, np.ndarray]:
            """Adjust pitch for harmonic compatibility"""
            if self.analyzer.are_keys_compatible(track1.key, track2.key):
                return audio1, audio2
            
            # Calculate optimal pitch shift
            key_map = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5,
                    'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}
            
            key1_root = track1.key.split()[0]
            key2_root = track2.key.split()[0]
            
            if key1_root in key_map and key2_root in key_map:
                shift = (key_map[key1_root] - key_map[key2_root]) % 12
                if shift > 6:
                    shift -= 12
                
                audio2 = self.pitch_shift(audio2, sr, shift)
            
            return audio1, audio2
        
        def create_crossfade(self, audio1: np.ndarray, audio2: np.ndarray, 
                            overlap_duration: float, sr: int) -> np.ndarray:
            """Create smooth crossfade between tracks"""
            overlap_samples = int(overlap_duration * sr)
            
            if len(audio1) < overlap_samples or len(audio2) < overlap_samples:
                return np.concatenate([audio1, audio2])
            
            fade_out = np.linspace(1, 0, overlap_samples)
            fade_in = np.linspace(0, 1, overlap_samples)
            
            audio1_fade = audio1[-overlap_samples:] * fade_out
            audio2_fade = audio2[:overlap_samples] * fade_in
            
            crossfade = audio1_fade + audio2_fade
            
            result = np.concatenate([
                audio1[:-overlap_samples],
                crossfade,
                audio2[overlap_samples:]
            ])
            
            return result
        
        def apply_effects(self, audio: np.ndarray, sr: int, effect_type: str) -> np.ndarray:
            """Apply various audio effects"""
            if effect_type == "reverb":
                # Simple reverb using convolution
                impulse = np.random.randn(sr // 10) * np.exp(-np.linspace(0, 4, sr // 10))
                return scipy.signal.convolve(audio, impulse, mode='same')
            
            elif effect_type == "delay":
                # Simple delay
                delay_samples = sr // 4
                delayed = np.zeros_like(audio)
                delayed[delay_samples:] = audio[:-delay_samples] * 0.5
                return audio + delayed
            
            # FIX: This was broken. `butter` doesn't take an array.
            # Replaced with a static lowpass.
            elif effect_type == "static_lowpass":
                try:
                    b, a = scipy.signal.butter(4, 8000 / (sr / 2), btype='low')
                    return scipy.signal.filtfilt(b, a, audio)
                except ValueError:
                    return audio # Return original if filter fails

            elif effect_type == "sidechain":
                # Sidechain compression effect
                envelope = np.abs(audio)
                smoothed = scipy.signal.savgol_filter(envelope, 1001, 3)
                compression = 1.0 - (smoothed / np.max(smoothed)) * 0.7
                return audio * compression
            
            return audio
        
        def generate_mashup(self, tracks: List[TrackInfo], style: MashupStyle, 
                            output_path: str, progress_callback=None) -> bool:
            """Generate a professional mashup"""
            try:
                if len(tracks) < 2:
                    if progress_callback:
                        progress_callback("[ERROR] Need at least 2 tracks.")
                    return False
                
                sr = 44100
                result = np.array([])
                
                # --- FIX: NEW LOGIC PATH FOR STEM MIXING ---
                if style == MashupStyle.STEM_MIX:
                    if not all(t.stems for t in tracks[:2]):
                        if progress_callback:
                            progress_callback("[ERROR] Stem Mix style requires stems.")
                            progress_callback("   → Did you check 'Enable Stem Separation'?")
                        return False
                    
                    if progress_callback:
                        progress_callback("Creating Stem Mix (Vocals T1 + Instrumental T2)...")
                    
                    track1 = tracks[0]
                    track2 = tracks[1]
                    
                    # Load Vocals from T1, Instrumental from T2
                    vocals_path = track1.stems.get('vocals')
                    bass_path = track2.stems.get('bass')
                    drums_path = track2.stems.get('drums')
                    other_path = track2.stems.get('other')

                    if not all([vocals_path, bass_path, drums_path, other_path]):
                        if progress_callback:
                            progress_callback("[ERROR] Missing required stems (vocals, bass, drums, other).")
                        return False

                    if progress_callback: progress_callback("Loading stems...")
                    y_vox, _ = librosa.load(vocals_path, sr=sr, mono=True)
                    y_bass, _ = librosa.load(bass_path, sr=sr, mono=True)
                    y_drums, _ = librosa.load(drums_path, sr=sr, mono=True)
                    y_other, _ = librosa.load(other_path, sr=sr, mono=True)
                    
                    # Create instrumental (sum and normalize)
                    y_inst = y_bass + y_drums + y_other
                    y_inst = y_inst / np.max(np.abs(y_inst)) * 0.95
                    
                    # Beatmatch and Harmonic Mix
                    if progress_callback: progress_callback("Beatmatching stems...")
                    y_vox, y_inst = self.beatmatch_tracks(track1, track2, y_vox, y_inst, sr)
                    
                    if progress_callback: progress_callback("Harmonic mixing...")
                    y_vox, y_inst = self.harmonic_mix(track1, track2, y_vox, y_inst, sr)
                    
                    # Mix them
                    len_vox = len(y_vox)
                    len_inst = len(y_inst)
                    max_len = max(len_vox, len_inst)
                    
                    y_vox_padded = librosa.util.pad_center(y_vox, size=max_len)
                    y_inst_padded = librosa.util.pad_center(y_inst, size=max_len)
                    
                    result = (y_vox_padded * 0.9) + (y_inst_padded * 0.8) # Mix (vocals slightly louder)

                # --- [Original logic for other styles] ---
                else:
                    # Load all full audio files
                    audios = []
                    for track in tracks:
                        if progress_callback:
                            progress_callback(f"Loading {track.title}...")
                        y, _ = librosa.load(track.path, sr=sr, mono=True)
                        audios.append(y)
                    
                    if style == MashupStyle.HARMONIC:
                        # Harmonic mixing mode
                        if progress_callback:
                            progress_callback("Applying harmonic mixing...")
                        
                        # Match BPMs
                        base_track = tracks[0]
                        
                        for i in range(1, len(audios)):
                            audios[0], audios[i] = self.beatmatch_tracks(
                                base_track, tracks[i], audios[0], audios[i], sr
                            )
                            audios[0], audios[i] = self.harmonic_mix(
                                base_track, tracks[i], audios[0], audios[i], sr
                            )
                        
                        # Mix with crossfades
                        result = audios[0]
                        for i in range(1, len(audios)):
                            overlap = random.uniform(4, 8)  # seconds
                            result = self.create_crossfade(result, audios[i], overlap, sr)
                    
                    elif style == MashupStyle.AGGRESSIVE:
                        # Fast cuts and heavy processing
                        if progress_callback:
                            progress_callback("Creating aggressive mashup...")
                        
                        result = np.array([])
                        segment_duration = 2  # seconds
                        
                        # FIX: Updated effects list
                        effects = ["reverb", "delay", "sidechain", "static_lowpass"]
                        
                        for _ in range(30):  # 30 segments
                            track_idx = random.randint(0, len(audios) - 1)
                            audio = audios[track_idx]
                            
                            # Random segment
                            start = random.randint(0, max(0, len(audio) - sr * segment_duration))
                            segment = audio[start:start + sr * segment_duration]
                            
                            # Apply random effect
                            segment = self.apply_effects(segment, sr, random.choice(effects))
                            
                            result = np.concatenate([result, segment])
                    
                    elif style == MashupStyle.SMOOTH:
                        # Long crossfades, minimal processing
                        if progress_callback:
                            progress_callback("Creating smooth blend...")
                        
                        # Beatmatch all to same BPM
                        target_bpm = np.mean([t.bpm for t in tracks])
                        for i, (track, audio) in enumerate(zip(tracks, audios)):
                            audios[i] = self.time_stretch(audio, sr, target_bpm, track.bpm)
                        
                        # Create smooth mix
                        result = audios[0][:sr * 30]  # First 30 seconds
                        
                        for audio in audios[1:]:
                            segment = audio[:sr * 30]
                            overlap = 10  # 10 second crossfade
                            result = self.create_crossfade(result, segment, overlap, sr)
                    
                    else:  # CLASSIC or EXPERIMENTAL
                        if progress_callback:
                            progress_callback("Creating classic mashup...")
                        
                        # Classic A-B-A-B pattern
                        segment_duration = 8  # seconds
                        segments = []
                        
                        for i in range(16):  # 16 segments total
                            track_idx = i % len(audios)
                            audio = audios[track_idx]
                            track = tracks[track_idx]
                            
                            # Align to beats
                            if track.beats and len(track.beats) > 1:
                                beat_idx = min(i * 4, len(track.beats) - 1)
                                start_time = track.beats[beat_idx]
                                start_sample = int(start_time * sr)
                            else:
                                start_sample = i * sr * segment_duration
                            
                            end_sample = min(start_sample + sr * segment_duration, len(audio))
                            segment = audio[start_sample:end_sample]
                            
                            # Fade edges
                            fade_len = sr // 4
                            if len(segment) > fade_len * 2:
                                segment[:fade_len] *= np.linspace(0, 1, fade_len)
                                segment[-fade_len:] *= np.linspace(1, 0, fade_len)
                            
                            segments.append(segment)
                        
                        result = np.concatenate(segments)
                
                # --- [Final mastering and saving] ---
                
                if progress_callback:
                    progress_callback("Finalizing mashup...")
                
                # Normalize to prevent clipping
                result_max = np.max(np.abs(result))
                if result_max == 0:
                    raise Exception("Empty audio generated")
                result = result / result_max * 0.95
                
                # Apply final mastering
                result = self.apply_mastering(result, sr)
                
                # Save output
                sf.write(output_path, result, sr, subtype='PCM_16')
                
                # Convert to MP3
                mp3_path = output_path.replace('.wav', '.mp3')
                subprocess.run([
                    'ffmpeg', '-i', output_path, '-b:a', '320k',
                    '-y', mp3_path
                ], stdout=DEVNULL, stderr=DEVNULL)
                
                # Remove WAV file
                os.remove(output_path)
                
                return True
                
            except Exception as e:
                if progress_callback:
                    progress_callback(f"Error: {e}")
                return False
        
        def apply_mastering(self, audio: np.ndarray, sr: int) -> np.ndarray:
            """Apply basic mastering chain"""
            # High-pass filter to remove rumble
            b, a = scipy.signal.butter(4, 30 / (sr / 2), btype='high')
            audio = scipy.signal.filtfilt(b, a, audio)
            
            # Soft compression
            threshold = 0.7
            ratio = 4.0
            compressed = np.where(
                np.abs(audio) > threshold,
                np.sign(audio) * (threshold + (np.abs(audio) - threshold) / ratio),
                audio
            )
            # FIX: The compressed audio was not being assigned back.
            audio = compressed
            
            # EQ boost (presence)
            b, a = scipy.signal.butter(2, [3000 / (sr / 2), 5000 / (sr / 2)], btype='band')
            presence = scipy.signal.filtfilt(b, a, audio) * 0.2
            audio = audio + presence
            
            # Final limiting
            audio = np.clip(audio, -0.99, 0.99)
            
            return audio

    # -----------------------------------------------------------------------------
    # Download Manager
    # -----------------------------------------------------------------------------
    class DownloadManager:
        """YouTube download with progress tracking"""
        
        @staticmethod
        def download_audio(urls: List[str], output_dir: str, progress_callback=None) -> List[str]:
            """Download audio from YouTube URLs"""
            os.makedirs(output_dir, exist_ok=True)
            downloaded_files = []
            
            outtmpl = os.path.join(output_dir, "%(title).200B-%(id)s.%(ext)s")
            
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": outtmpl,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "320",
                    }
                ],
                "overwrites": True,
                "ignoreerrors": "only_download",
                "quiet": True,
                "no_warnings": True,
                "extract_flat": False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                for url in urls:
                    try:
                        if progress_callback:
                            progress_callback(f"Downloading: {url}")
                        
                        info = ydl.extract_info(url, download=True)
                        
                        if info:
                            # Handle playlists
                            if info.get("_type") == "playlist" or "entries" in info:
                                for entry in info.get("entries", []):
                                    if entry:
                                        filename = ydl.prepare_filename(entry)
                                        mp3_path = os.path.splitext(filename)[0] + ".mp3"
                                        if os.path.exists(mp3_path):
                                            downloaded_files.append(mp3_path)
                            else:
                                filename = ydl.prepare_filename(info)
                                mp3_path = os.path.splitext(filename)[0] + ".mp3"
                                if os.path.exists(mp3_path):
                                    downloaded_files.append(mp3_path)
                    
                    except Exception as e:
                        if progress_callback:
                            progress_callback(f"Failed to download {url}: {e}")
            
            return list(set(downloaded_files))  # Remove duplicates

    # -----------------------------------------------------------------------------
    # Main Application
    # -----------------------------------------------------------------------------
    class RaveDJApp:
        """Main application window"""
        
        def __init__(self, root: tk.Tk):
            self.root = root
            self.root.title("Cat's Rave.dj Pro 2.0 — Professional Mashup Studio")
            self.root.geometry("900x700")
            self.root.configure(bg="#0a0a0a")
            
            self.generator = MashupGenerator()
            self.analyzer = AudioAnalyzer()
            self.download_manager = DownloadManager()
            
            self.analyzed_tracks: List[TrackInfo] = []
            self.current_thread: Optional[threading.Thread] = None
            
            self.setup_ui()
            self.root.deiconify()
        
        def setup_ui(self):
            """Create the user interface"""
            # Header
            header_frame = tk.Frame(self.root, bg="#0a0a0a")
            header_frame.pack(fill=tk.X, pady=10)
            
            title = tk.Label(
                header_frame,
                text="🎵 Cat's Rave.dj Pro 2.0 🎵",
                font=("Arial", 18, "bold"),
                fg="#00ffcc",
                bg="#0a0a0a"
            )
            title.pack()
            
            subtitle = tk.Label(
                header_frame,
                text="Professional Mashup Studio with AI-Powered Mixing",
                font=("Arial", 10),
                fg="#888888",
                bg="#0a0a0a"
            )
            subtitle.pack()
            
            # Main content area
            main_frame = tk.Frame(self.root, bg="#0a0a0a")
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            # Left panel - Track inputs
            left_panel = tk.Frame(main_frame, bg="#1a1a1a", relief=tk.RAISED, bd=2)
            left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
            
            tk.Label(
                left_panel,
                text="TRACK INPUTS",
                font=("Arial", 12, "bold"),
                fg="#00ffcc",
                bg="#1a1a1a"
            ).pack(pady=10)
            
            # Track 1
            track1_frame = tk.Frame(left_panel, bg="#1a1a1a")
            track1_frame.pack(fill=tk.X, padx=10, pady=5)
            
            tk.Label(
                track1_frame,
                text="Track 1 URLs (Vocals for Stem Mix):",
                font=("Arial", 10),
                fg="#ffffff",
                bg="#1a1a1a"
            ).pack(anchor=tk.W)
            
            self.track1_text = tk.Text(
                track1_frame,
                height=4,
                bg="#222222",
                fg="#00ff00",
                insertbackground="#00ff00",
                font=("Consolas", 9)
            )
            self.track1_text.pack(fill=tk.X, pady=5)
            
            # Track 2
            track2_frame = tk.Frame(left_panel, bg="#1a1a1a")
            track2_frame.pack(fill=tk.X, padx=10, pady=5)
            
            tk.Label(
                track2_frame,
                text="Track 2 URLs (Instrumental for Stem Mix):",
                font=("Arial", 10),
                fg="#ffffff",
                bg="#1a1a1a"
            ).pack(anchor=tk.W)
            
            self.track2_text = tk.Text(
                track2_frame,
                height=4,
                bg="#222222",
                fg="#00ff00",
                insertbackground="#00ff00",
                font=("Consolas", 9)
            )
            self.track2_text.pack(fill=tk.X, pady=5)
            
            # Additional tracks
            track3_frame = tk.Frame(left_panel, bg="#1a1a1a")
            track3_frame.pack(fill=tk.X, padx=10, pady=5)
            
            tk.Label(
                track3_frame,
                text="Additional URLs (for other modes):",
                font=("Arial", 10),
                fg="#ffffff",
                bg="#1a1a1a"
            ).pack(anchor=tk.W)
            
            self.track3_text = tk.Text(
                track3_frame,
                height=3,
                bg="#222222",
                fg="#00ff00",
                insertbackground="#00ff00",
                font=("Consolas", 9)
            )
            self.track3_text.pack(fill=tk.X, pady=5)
            
            # Right panel - Settings
            right_panel = tk.Frame(main_frame, bg="#1a1a1a", relief=tk.RAISED, bd=2)
            right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
            
            tk.Label(
                right_panel,
                text="MASHUP SETTINGS",
                font=("Arial", 12, "bold"),
                fg="#00ffcc",
                bg="#1a1a1a"
            ).pack(pady=10)
            
            # Style selection
            style_frame = tk.Frame(right_panel, bg="#1a1a1a")
            style_frame.pack(fill=tk.X, padx=10, pady=10)
            
            tk.Label(
                style_frame,
                text="Mashup Style:",
                font=("Arial", 10),
                fg="#ffffff",
                bg="#1a1a1a"
            ).pack(side=tk.LEFT, padx=(0, 10))
            
            self.style_var = tk.StringVar(value="classic")
            # FIX: Added new "stem_mix" style to dropdown
            self.style_combo = ttk.Combobox(
                style_frame,
                textvariable=self.style_var,
                values=[s.value for s in MashupStyle],
                state="readonly",
                width=20
            )
            self.style_combo.pack(side=tk.LEFT)
            
            # Number of mashups
            count_frame = tk.Frame(right_panel, bg="#1a1a1a")
            count_frame.pack(fill=tk.X, padx=10, pady=10)
            
            tk.Label(
                count_frame,
                text="Number of Mashups:",
                font=("Arial", 10),
                fg="#ffffff",
                bg="#1a1a1a"
            ).pack(side=tk.LEFT, padx=(0, 10))
            
            self.count_var = tk.IntVar(value=1)
            self.count_spinbox = tk.Spinbox(
                count_frame,
                from_=1,
                to=100,
                textvariable=self.count_var,
                width=10,
                bg="#222222",
                fg="#ffffff",
                insertbackground="#ffffff"
            )
            self.count_spinbox.pack(side=tk.LEFT)
            
            # Options
            options_frame = tk.Frame(right_panel, bg="#1a1a1a")
            options_frame.pack(fill=tk.X, padx=10, pady=10)
            
            self.analyze_var = tk.BooleanVar(value=True)
            tk.Checkbutton(
                options_frame,
                text="Deep Audio Analysis (BPM/Key)",
                variable=self.analyze_var,
                bg="#1a1a1a",
                fg="#ffffff",
                selectcolor="#1a1a1a",
                activebackground="#1a1a1a",
                font=("Arial", 9)
            ).pack(anchor=tk.W, pady=2)
            
            self.stems_var = tk.BooleanVar(value=False)
            tk.Checkbutton(
                options_frame,
                text="Enable Stem Separation (VERY Slow)",
                variable=self.stems_var,
                bg="#1a1a1a",
                fg="#ffffff",
                selectcolor="#1a1a1a",
                activebackground="#1a1a1a",
                font=("Arial", 9)
            ).pack(anchor=tk.W, pady=2)
            
            self.beatmatch_var = tk.BooleanVar(value=True)
            tk.Checkbutton(
                options_frame,
                text="Auto Beat-Matching",
                variable=self.beatmatch_var,
                bg="#1a1a1a",
                fg="#ffffff",
                selectcolor="#1a1a1a",
                activebackground="#1a1a1a",
                font=("Arial", 9)
            ).pack(anchor=tk.W, pady=2)
            
            # Output directory
            output_frame = tk.Frame(right_panel, bg="#1a1a1a")
            output_frame.pack(fill=tk.X, padx=10, pady=10)
            
            tk.Label(
                output_frame,
                text="Output Folder:",
                font=("Arial", 10),
                fg="#ffffff",
                bg="#1a1a1a"
            ).pack(anchor=tk.W)
            
            output_entry_frame = tk.Frame(output_frame, bg="#1a1a1a")
            output_entry_frame.pack(fill=tk.X, pady=5)
            
            self.output_var = tk.StringVar(value=str(Path.home() / "RaveDJ_Mashups"))
            self.output_entry = tk.Entry(
                output_entry_frame,
                textvariable=self.output_var,
                bg="#222222",
                fg="#ffffff",
                insertbackground="#ffffff"
            )
            self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            tk.Button(
                output_entry_frame,
                text="Browse",
                command=self.browse_output,
                bg="#333333",
                fg="#ffffff",
                activebackground="#444444"
            ).pack(side=tk.RIGHT, padx=(5, 0))
            
            # Generate button
            self.generate_btn = tk.Button(
                right_panel,
                text="🎵 GENERATE MASHUPS 🎵",
                command=self.generate_mashups,
                bg="#00ff00",
                fg="#000000",
                font=("Arial", 12, "bold"),
                height=2,
                activebackground="#00cc00"
            )
            self.generate_btn.pack(pady=20)
            
            # Progress bar
            self.progress = ttk.Progressbar(
                self.root,
                mode="indeterminate",
                length=860
            )
            self.progress.pack(pady=10)
            
            # Console output
            console_frame = tk.Frame(self.root, bg="#000000")
            console_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
            
            self.console = scrolledtext.ScrolledText(
                console_frame,
                height=8,
                bg="#000000",
                fg="#00ff00",
                insertbackground="#00ff00",
                font=("Consolas", 9)
            )
            self.console.pack(fill=tk.BOTH, expand=True)
            
            self.log("[SYSTEM] Cat's Rave.dj Pro 2.0 (Fixed) initialized")
            self.log("[INFO] Professional audio engine ready")
            self.log("[INFO] For 'stem_mix' style, use Track 1 for Vocals and Track 2 for Instrumental.")
        
        def browse_output(self):
            """Browse for output directory"""
            directory = filedialog.askdirectory()
            if directory:
                self.output_var.set(directory)
        
        def log(self, message: str):
            """Add message to console"""
            self.console.insert(tk.END, f"{message}\n")
            self.console.see(tk.END)
            self.root.update_idletasks()
        
        def get_all_urls(self) -> List[str]:
            """Extract all URLs from text fields"""
            urls = []
            
            for text_widget in [self.track1_text, self.track2_text, self.track3_text]:
                content = text_widget.get(1.0, tk.END).strip()
                if content:
                    # Split by comma, newline, or space
                    for url in re.split(r'[,\n\s]+', content):
                        url = url.strip()
                        if url and ('youtube.com' in url or 'youtu.be' in url):
                            urls.append(url)
            
            return list(set(urls)) # Return unique URLs
        
        def generate_mashups(self):
            """Start mashup generation process"""
            if self.current_thread and self.current_thread.is_alive():
                messagebox.showwarning("Processing", "Generation already in progress!")
                return
            
            urls = self.get_all_urls()
            if not urls:
                messagebox.showerror("Error", "Please enter at least one YouTube URL")
                return
            
            output_dir = self.output_var.get()
            if not output_dir:
                messagebox.showerror("Error", "Please select an output directory")
                return
            
            self.generate_btn.config(state=tk.DISABLED)
            self.progress.start()
            
            def worker():
                try:
                    # Download tracks
                    self.log(f"\n[DOWNLOAD] Fetching {len(urls)} URL(s)...")
                    audio_files = self.download_manager.download_audio(
                        urls, output_dir, lambda msg: self.log(f"[DOWNLOAD] {msg}")
                    )
                    
                    if not audio_files:
                        raise Exception("No audio files were downloaded")
                    
                    self.log(f"[SUCCESS] Downloaded {len(audio_files)} tracks")
                    
                    # Analyze tracks if enabled
                    if self.analyze_var.get():
                        self.log("\n[ANALYSIS] Analyzing audio characteristics...")
                        self.analyzed_tracks = []
                        
                        for file_path in audio_files:
                            self.log(f"[ANALYSIS] Processing {Path(file_path).name}...")
                            track_info = self.analyzer.analyze_track(
                                file_path,
                                lambda msg: self.log(f"  → {msg}")
                            )
                            self.analyzed_tracks.append(track_info)
                            
                            self.log(f"  → BPM: {track_info.bpm:.1f}")
                            self.log(f"  → Key: {track_info.key}")
                            self.log(f"  → Duration: {track_info.duration:.1f}s")
                    else:
                        # Create basic track info without analysis
                        self.analyzed_tracks = [
                            TrackInfo(
                                path=f,
                                title=Path(f).stem,
                                bpm=128.0,
                                key="C major",
                                energy=0.5,
                                duration=180.0,
                                beats=[],
                                sections=[]
                            ) for f in audio_files
                        ]
                    
                    # --- FIX: CALL STEM SEPARATION IF ENABLED ---
                    if self.stems_var.get():
                        self.log("\n[STEMS] Separating stems (This is VERY slow)...")
                        stem_output_dir = os.path.join(output_dir, "Stems")
                        os.makedirs(stem_output_dir, exist_ok=True)
                        
                        for track in self.analyzed_tracks:
                            self.log(f"[STEMS] Processing {track.title}...")
                            stems = self.stem_separator.separate_stems(
                                track.path, 
                                stem_output_dir, 
                                lambda msg: self.log(f"   → {msg}")
                            )
                            if stems:
                                track.stems = stems
                                self.log(f"[STEMS] Found {', '.join(stems.keys())} for {track.title}")
                            else:
                                self.log(f"[WARN] No stems separated for {track.title}")
                    
                    # Generate mashups
                    style_enum = MashupStyle(self.style_var.get())
                    num_mashups = self.count_var.get()
                    
                    self.log(f"\n[GENERATION] Creating {num_mashups} {style_enum.value} mashup(s)...")
                    
                    for i in range(num_mashups):
                        self.log(f"[MASHUP {i+1}/{num_mashups}] Generating...")
                        
                        # Randomly select 2-4 tracks for mashup
                        # For Stem Mix, we primarily use the first 2
                        if style_enum == MashupStyle.STEM_MIX:
                            if len(self.analyzed_tracks) < 2:
                                self.log("[ERROR] Stem Mix requires at least 2 tracks.")
                                continue
                            # Use tracks in order (T1 = Vocals, T2 = Instrumental)
                            selected_tracks = self.analyzed_tracks
                        else:
                            num_tracks = min(len(self.analyzed_tracks), random.randint(2, 4))
                            selected_tracks = random.sample(self.analyzed_tracks, num_tracks)
                        
                        output_path = os.path.join(
                            output_dir,
                            f"mashup_{style_enum.value}_{i+1:02d}.wav"
                        )
                        
                        success = self.generator.generate_mashup(
                            selected_tracks,
                            style_enum,
                            output_path,
                            lambda msg: self.log(f"  → {msg}")
                        )
                        
                        if success:
                            self.log(f"[SUCCESS] Saved mashup_{style_enum.value}_{i+1:02d}.mp3")
                        else:
                            self.log(f"[ERROR] Failed to generate mashup {i+1}")
                    
                    self.log(f"\n[COMPLETE] All mashups saved to {output_dir}")
                    
                    # Show success dialog
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Success!",
                        f"Generated {num_mashups} mashup(s)!\n\nLocation:\n{output_dir}"
                    ))
                    
                except Exception as e:
                    self.log(f"[ERROR] Generation failed: {str(e)}")
                    self.root.after(0, lambda: messagebox.showerror(
                        "Error",
                        f"Generation failed:\n{str(e)}"
                    ))
                
                finally:
                    self.root.after(0, lambda: self.generate_btn.config(state=tk.NORMAL))
                    self.root.after(0, lambda: self.progress.stop())
            
            self.current_thread = threading.Thread(target=worker, daemon=True)
            self.current_thread.start()

    # -----------------------------------------------------------------------------
    # Main entry point
    # -----------------------------------------------------------------------------
    def main():
        """Main application entry point"""
        try:
            app = RaveDJApp(root)
            root.mainloop()
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as e:
            messagebox.showerror("Fatal Error", f"Application error:\n{str(e)}")
            sys.exit(1)

    if __name__ == "__main__":
        main()
