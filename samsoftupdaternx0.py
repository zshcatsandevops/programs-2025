#!/usr/bin/env python3
"""
SamSoft Windows Update Agent — Final Decimal-Safe COM Edition
--------------------------------------------------------------
• Installs ALL available updates automatically (batch mode)
• Handles COM property differences safely
• Fixes Decimal vs float arithmetic error
• Accepts all EULAs, retries failed updates once
• Optional auto-reboot after install
Requires:  pip install pywin32
Tested on: Windows 10 / 11 / Server 2022 (Python 3.10+)
"""

import os, sys, platform, threading, queue, ctypes, subprocess
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from decimal import Decimal

# Optional COM bindings
HAS_COM = False
try:
    import pythoncom
    import win32com.client
    HAS_COM = True
except Exception:
    HAS_COM = False


# =========================================================
# Utility helpers
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
    """Convert COM numeric types (Decimal, int, etc.) safely to float."""
    try:
        if isinstance(v, Decimal): return float(v)
        return float(v)
    except Exception:
        return 0.0
def format_bytes(n):
    """Human-readable file size string."""
    size = to_float(n)
    if size <= 0: return "Unknown"
    for unit in ["B","KB","MB","GB","TB"]:
        if size < 1024.0: return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"
def safe_creationflags(): return 0x08000000 if is_windows() else 0


# =========================================================
# Main App
# =========================================================
class SamSoftUpdateApp:
    def __init__(self, root):
        self.root=root
        root.title("SamSoft Windows Update Agent — Final Decimal-Safe Edition")
        root.geometry("900x600")

        self.is_running=False
        self.available_updates=[]
        self.include_drivers=tk.BooleanVar(value=False)
        self.auto_accept_eula=tk.BooleanVar(value=True)
        self.auto_reboot=tk.BooleanVar(value=True)

        self._ui_queue=queue.Queue()
        self._build_ui()
        self._poll()
        self._log("SamSoft Windows Update Agent started.")

    # ---------- UI ----------
    def _build_ui(self):
        style=ttk.Style(); style.theme_use("clam")
        style.configure("Header.TLabel",font=("Segoe UI",16,"bold"))
        ttk.Label(self.root,text="SamSoft Windows Update Agent",style="Header.TLabel").pack(pady=8)
        opts=ttk.Frame(self.root,padding=8); opts.pack(fill="x")
        ttk.Checkbutton(opts,text="Include Drivers",variable=self.include_drivers).pack(side="left")
        ttk.Checkbutton(opts,text="Auto-accept EULAs",variable=self.auto_accept_eula).pack(side="left")
        ttk.Checkbutton(opts,text="Auto-reboot if needed",variable=self.auto_reboot).pack(side="left")

        bar=ttk.Frame(self.root,padding=8); bar.pack(fill="x")
        self.btn_scan=ttk.Button(bar,text="Scan Updates",command=self._start_scan)
        self.btn_scan.pack(side="left",padx=5)
        self.btn_install=ttk.Button(bar,text="Install All Updates",command=self._start_install,state="disabled")
        self.btn_install.pack(side="left",padx=5)
        ttk.Button(bar,text="Run as Administrator",command=elevate_as_admin).pack(side="right")

        lf=ttk.LabelFrame(self.root,text="Log",padding=6)
        lf.pack(fill="both",expand=True,padx=10,pady=8)
        self.log=tk.Text(lf,wrap="word",state="disabled")
        self.log.pack(fill="both",expand=True)

        self.pb=ttk.Progressbar(self.root,mode="indeterminate")
        self.pb.pack(fill="x",padx=10,pady=4)

    # ---------- logging ----------
    def _append_log(self,msg):
        ts=datetime.now().strftime("%H:%M:%S")
        self.log.config(state="normal")
        self.log.insert(tk.END,f"[{ts}] {msg}\n")
        self.log.see(tk.END)
        self.log.config(state="disabled")
    def _log(self,msg): self._ui_queue.put(msg)
    def _poll(self):
        try:
            while True: self._append_log(self._ui_queue.get_nowait())
        except queue.Empty: pass
        self.root.after(100,self._poll)
    def _busy(self,b=True):
        s="disabled" if b else "normal"
        self.btn_scan.config(state=s); self.btn_install.config(state=s)
        self.pb.start(10) if b else self.pb.stop()

    # ---------- scan / install triggers ----------
    def _start_scan(self):
        if self.is_running or not HAS_COM: return
        self.is_running=True; self._busy(True)
        threading.Thread(target=self._scan_online,daemon=True).start()
    def _start_install(self):
        if self.is_running or not HAS_COM: return
        self.is_running=True; self._busy(True)
        threading.Thread(target=self._install_online,daemon=True).start()

    # ---------- scan ----------
    def _scan_online(self):
        try:
            pythoncom.CoInitialize()
            self._log("Scanning for available updates…")
            session=win32com.client.gencache.EnsureDispatch("Microsoft.Update.Session")
            searcher=session.CreateUpdateSearcher()
            q="IsInstalled=0 and IsHidden=0"
            if not self.include_drivers.get(): q+=" and Type='Software'"
            res=searcher.Search(q)
            ups=res.Updates; n=int(ups.Count)
            self.available_updates.clear()
            if n==0:
                self._log("No updates found — system is up to date."); return
            for i in range(n):
                up=ups.Item(i)
                title=str(getattr(up,"Title","Unknown update"))
                kbids=[]
                try:
                    kbcol=getattr(up,"KBArticleIDs",None)
                    if kbcol:
                        for j in range(kbcol.Count): kbids.append(str(kbcol.Item(j)))
                except Exception: pass
                kb=f"KB{kbids[0]}" if kbids else ""
                size_val=to_float(getattr(up,"MaxDownloadSize",-1))
                size=format_bytes(size_val)
                self.available_updates.append({"com":up,"title":f"{title} {kb} ({size})"})
            self._log(f"Found {n} update(s).")
            self.btn_install.config(state="normal")
        except Exception as e:
            self._log(f"Scan error: {e}")
        finally:
            self._busy(False); self.is_running=False
            try: pythoncom.CoUninitialize()
            except Exception: pass

    # ---------- install ----------
    def _install_online(self):
        try:
            if not is_admin(): self._log("⚠️ Not elevated — installs may fail.")
            pythoncom.CoInitialize()
            session=win32com.client.gencache.EnsureDispatch("Microsoft.Update.Session")
            installer=session.CreateUpdateInstaller()
            if not self.available_updates:
                self._log("No updates available. Please scan first."); return

            coll=win32com.client.Dispatch("Microsoft.Update.UpdateColl")
            for up in self.available_updates:
                obj=up["com"]
                try:
                    if self.auto_accept_eula.get() and getattr(obj,"EulaAccepted",True) is False:
                        obj.AcceptEula()
                except Exception: pass
                coll.Add(obj)
            installer.Updates=coll

            # Only set props if they exist (older WUA builds skip these)
            for name,value in (("ForceQuiet",True),("AllowSourcePrompts",False)):
                try:
                    if hasattr(installer,name): setattr(installer,name,value)
                except Exception: pass

            self._log(f"Installing {coll.Count} update(s)…")
            result=installer.Install()
            code=int(getattr(result,"ResultCode",0))
            reboot=bool(getattr(result,"RebootRequired",False))
            self._log(f"Install result: {code} (2=OK,3=Partial,4=Fail)")

            try:
                rcodes=list(getattr(result,"ResultCodes",[]))
                for i,rc in enumerate(rcodes):
                    t=self.available_updates[i]["title"]
                    self._log(f"  • {t}: {rc}")
            except Exception: pass

            # Retry failed once
            if code==4:
                failed=[]
                try:
                    for i,rc in enumerate(rcodes):
                        if rc==4: failed.append(self.available_updates[i]["com"])
                except Exception: pass
                if failed:
                    self._log(f"Retrying {len(failed)} failed update(s)…")
                    coll2=win32com.client.Dispatch("Microsoft.Update.UpdateColl")
                    for f in failed: coll2.Add(f)
                    installer.Updates=coll2
                    res2=installer.Install()
                    self._log(f"Retry result: {int(getattr(res2,'ResultCode',0))}")

            if reboot:
                self._log("Reboot required.")
                if self.auto_reboot.get() and is_admin():
                    self._log("Scheduling reboot in 30 seconds…")
                    subprocess.Popen(["shutdown","/r","/t","30"],creationflags=safe_creationflags())
                else:
                    self._log("Please reboot manually.")
            else:
                self._log("All updates installed successfully or no reboot needed.")
        except Exception as e:
            self._log(f"Install error: {e}")
        finally:
            self._busy(False); self.is_running=False
            try: pythoncom.CoUninitialize()
            except Exception: pass


# =========================================================
def main():
    root=tk.Tk()
    SamSoftUpdateApp(root)
    root.mainloop()

if __name__=="__main__":
    main()
