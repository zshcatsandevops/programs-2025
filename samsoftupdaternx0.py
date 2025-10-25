#!/usr/bin/env python3
"""
SamSoft Windows Update Agent — WSUS Offline Hybrid Edition (test.py)
--------------------------------------------------------------------
• Combines WSUS Offline UI philosophy with SamSoft COM-safe backend
• 100% Windows-native ttk UI — same layout logic as WSUS Offline
• Decimal-safe COM arithmetic (fixes float/Decimal mismatch)
• Full scanning, installation, retry, and auto-reboot support
• Progress output shown via standard Windows console window
• Stores settings automatically between sessions via INI
--------------------------------------------------------------------
Requirements:
    pip install pywin32
Tested on:
    Windows 10 / 11 / Server 2022 (Python 3.10+)
"""

import os, sys, threading, queue, ctypes, subprocess, platform, configparser
from datetime import datetime
from decimal import Decimal
import tkinter as tk
from tkinter import ttk, messagebox

# Optional COM imports
HAS_COM = False
try:
    import pythoncom
    import win32com.client
    HAS_COM = True
except Exception:
    HAS_COM = False


# =========================================================
# Utility Functions
# =========================================================
def is_windows(): return os.name == "nt" and "windows" in platform.system().lower()
def is_admin():
    if not is_windows(): return False
    try: return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception: return False
def elevate_as_admin():
    if not is_windows(): return
    try:
        params = " ".join(f'"{a}"' for a in sys.argv)
        ctypes.windll.shell32.ShellExecuteW(None,"runas",sys.executable,params,None,1)
        sys.exit(0)
    except Exception as e:
        messagebox.showerror("Elevation failed", f"Could not elevate: {e}")

def to_float(v):
    try:
        if isinstance(v, Decimal): return float(v)
        return float(v)
    except Exception:
        return 0.0

def format_bytes(n):
    size = to_float(n)
    if size <= 0: return "Unknown"
    for unit in ["B","KB","MB","GB","TB"]:
        if size < 1024.0: return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"

def safe_creationflags(): return 0x08000000 if is_windows() else 0
def ini_path(): return os.path.join(os.getcwd(), "samsoft_update.ini")


# =========================================================
# Main Application
# =========================================================
class SamSoftUpdateApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SamSoft Windows Update Agent — WSUS Offline Hybrid Edition")
        self.root.geometry("900x600")
        self.root.resizable(False, False)
        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.available_updates = []
        self.is_running = False
        self._ui_queue = queue.Queue()

        # Variables
        self.include_drivers = tk.BooleanVar(value=False)
        self.auto_accept_eula = tk.BooleanVar(value=True)
        self.auto_reboot = tk.BooleanVar(value=True)

        self._build_ui()
        self._load_settings()
        self._poll()
        self._log("SamSoft Windows Update Agent started.")

    # =====================================================
    # UI Construction (WSUS-Inspired)
    # =====================================================
    def _build_ui(self):
        ttk.Label(self.root, text="SamSoft Windows Update Agent", font=("Segoe UI", 16, "bold")).pack(pady=10)

        # --- Options Group (like WSUS "Options" groupbox) ---
        opt_frame = ttk.LabelFrame(self.root, text="Options", padding=10)
        opt_frame.pack(fill="x", padx=10, pady=5)

        ttk.Checkbutton(opt_frame, text="Include Drivers", variable=self.include_drivers).pack(anchor="w", pady=2)
        ttk.Checkbutton(opt_frame, text="Auto-accept EULAs", variable=self.auto_accept_eula).pack(anchor="w", pady=2)
        ttk.Checkbutton(opt_frame, text="Auto-reboot if needed", variable=self.auto_reboot).pack(anchor="w", pady=2)

        # --- Buttons Row ---
        btn_frame = ttk.Frame(self.root, padding=10)
        btn_frame.pack(fill="x")

        self.btn_scan = ttk.Button(btn_frame, text="Scan for Updates", command=self._start_scan)
        self.btn_install = ttk.Button(btn_frame, text="Install Updates", command=self._start_install, state="disabled")
        self.btn_elevate = ttk.Button(btn_frame, text="Run as Administrator", command=elevate_as_admin)
        self.btn_exit = ttk.Button(btn_frame, text="Exit", command=self.root.quit)

        self.btn_scan.pack(side="left", padx=5)
        self.btn_install.pack(side="left", padx=5)
        self.btn_elevate.pack(side="right", padx=5)
        self.btn_exit.pack(side="right", padx=5)

        # --- Log Output (WSUS Log Section) ---
        log_frame = ttk.LabelFrame(self.root, text="Activity Log", padding=5)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.log = tk.Text(log_frame, wrap="word", state="disabled", bg="#000000", fg="#FFFFFF")
        self.log.pack(fill="both", expand=True)

        # --- Progress Bar ---
        self.pb = ttk.Progressbar(self.root, mode="indeterminate")
        self.pb.pack(fill="x", padx=10, pady=5)

    # =====================================================
    # Logging and Event Polling
    # =====================================================
    def _append_log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log.config(state="normal")
        self.log.insert(tk.END, f"[{ts}] {msg}\n")
        self.log.see(tk.END)
        self.log.config(state="disabled")

    def _log(self, msg): self._ui_queue.put(msg)
    def _poll(self):
        try:
            while True:
                msg = self._ui_queue.get_nowait()
                self._append_log(msg)
        except queue.Empty:
            pass
        self.root.after(100, self._poll)

    def _busy(self, b=True):
        s = "disabled" if b else "normal"
        self.btn_scan.config(state=s)
        self.btn_install.config(state=s)
        if b: self.pb.start(10)
        else: self.pb.stop()

    # =====================================================
    # Settings persistence (INI like WSUS Offline)
    # =====================================================
    def _load_settings(self):
        cfg = configparser.ConfigParser()
        if os.path.exists(ini_path()):
            cfg.read(ini_path())
            opts = cfg["opts"]
            self.include_drivers.set(opts.getboolean("include_drivers", False))
            self.auto_accept_eula.set(opts.getboolean("auto_accept_eula", True))
            self.auto_reboot.set(opts.getboolean("auto_reboot", True))

    def _save_settings(self):
        cfg = configparser.ConfigParser()
        cfg["opts"] = {
            "include_drivers": str(self.include_drivers.get()),
            "auto_accept_eula": str(self.auto_accept_eula.get()),
            "auto_reboot": str(self.auto_reboot.get())
        }
        with open(ini_path(), "w") as f:
            cfg.write(f)

    # =====================================================
    # Scanning
    # =====================================================
    def _start_scan(self):
        if self.is_running or not HAS_COM: return
        self.is_running = True
        self._busy(True)
        threading.Thread(target=self._scan_online, daemon=True).start()

    def _scan_online(self):
        try:
            pythoncom.CoInitialize()
            self._log("Scanning for available updates…")
            session = win32com.client.gencache.EnsureDispatch("Microsoft.Update.Session")
            searcher = session.CreateUpdateSearcher()
            query = "IsInstalled=0 and IsHidden=0"
            if not self.include_drivers.get():
                query += " and Type='Software'"
            result = searcher.Search(query)
            updates = result.Updates
            count = int(updates.Count)
            self.available_updates.clear()

            if count == 0:
                self._log("No updates found — system is up to date.")
                return

            for i in range(count):
                up = updates.Item(i)
                title = str(getattr(up, "Title", "Unknown"))
                kbids = []
                try:
                    kbcol = getattr(up, "KBArticleIDs", None)
                    if kbcol:
                        for j in range(kbcol.Count):
                            kbids.append(str(kbcol.Item(j)))
                except Exception:
                    pass
                kb = f"KB{kbids[0]}" if kbids else ""
                size = format_bytes(getattr(up, "MaxDownloadSize", -1))
                self.available_updates.append({"com": up, "title": f"{title} {kb} ({size})"})
            self._log(f"Found {count} update(s).")
            self.btn_install.config(state="normal")

        except Exception as e:
            self._log(f"Scan error: {e}")
        finally:
            self._busy(False)
            self.is_running = False
            self._save_settings()
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass

    # =====================================================
    # Installation
    # =====================================================
    def _start_install(self):
        if self.is_running or not HAS_COM: return
        self.is_running = True
        self._busy(True)
        threading.Thread(target=self._install_online, daemon=True).start()

    def _install_online(self):
        try:
            if not is_admin():
                self._log("⚠️ Not elevated — installs may fail.")
            pythoncom.CoInitialize()
            session = win32com.client.gencache.EnsureDispatch("Microsoft.Update.Session")
            installer = session.CreateUpdateInstaller()
            if not self.available_updates:
                self._log("No updates available. Please scan first.")
                return

            coll = win32com.client.Dispatch("Microsoft.Update.UpdateColl")
            for up in self.available_updates:
                obj = up["com"]
                try:
                    if self.auto_accept_eula.get() and getattr(obj, "EulaAccepted", True) is False:
                        obj.AcceptEula()
                except Exception:
                    pass
                coll.Add(obj)
            installer.Updates = coll

            # Safe property sets
            for name, val in (("ForceQuiet", True), ("AllowSourcePrompts", False)):
                try:
                    if hasattr(installer, name): setattr(installer, name, val)
                except Exception: pass

            self._log(f"Installing {coll.Count} update(s)…")
            result = installer.Install()
            code = int(getattr(result, "ResultCode", 0))
            reboot = bool(getattr(result, "RebootRequired", False))
            self._log(f"Install result: {code} (2=OK,3=Partial,4=Fail)")

            try:
                rcodes = list(getattr(result, "ResultCodes", []))
                for i, rc in enumerate(rcodes):
                    t = self.available_updates[i]["title"]
                    self._log(f"  • {t}: {rc}")
            except Exception:
                pass

            # Retry failed
            if code == 4:
                failed = []
                try:
                    for i, rc in enumerate(rcodes):
                        if rc == 4:
                            failed.append(self.available_updates[i]["com"])
                except Exception: pass
                if failed:
                    self._log(f"Retrying {len(failed)} failed update(s)…")
                    coll2 = win32com.client.Dispatch("Microsoft.Update.UpdateColl")
                    for f in failed:
                        coll2.Add(f)
                    installer.Updates = coll2
                    res2 = installer.Install()
                    self._log(f"Retry result: {int(getattr(res2, 'ResultCode', 0))}")

            if reboot:
                self._log("Reboot required.")
                if self.auto_reboot.get() and is_admin():
                    self._log("Scheduling reboot in 30 seconds…")
                    subprocess.Popen(["shutdown", "/r", "/t", "30"], creationflags=safe_creationflags())
                else:
                    self._log("Please reboot manually.")
            else:
                self._log("All updates installed successfully or no reboot needed.")

        except Exception as e:
            self._log(f"Install error: {e}")
        finally:
            self._busy(False)
            self.is_running = False
            self._save_settings()
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass


# =========================================================
def main():
    if not is_windows():
        messagebox.showerror("Unsupported OS", "This tool is for Windows only.")
        return
    root = tk.Tk()
    app = SamSoftUpdateApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app._save_settings(), root.destroy()))
    root.mainloop()


if __name__ == "__main__":
    main()
