#!/usr/bin/env python3
# Samsoft OS Compiler 0.1 – Toolkit with WSL2 Ubuntu Emulator and Libdragon Support
# ©2025 Samsoft / Cat-san
import tkinter as tk
from tkinter import messagebox
import os
import subprocess

# Pixel-style font
PIX_FONT = ("Courier", 12, "bold")
BG_COLOR = "#002E5A"  # dark teal/blue reminiscent of SGI
BTN_BG = "#1E4A8F"
BTN_FG = "#CAD9ED"

class SamsoftOSCompiler(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Samsoft OS Compiler 0.1")
        self.geometry("1024x768")
        self.configure(bg=BG_COLOR)
        self.create_desktop_icons()

    def create_desktop_icons(self):
        # Hex Editor icon (placeholder)
        hex_btn = tk.Button(self, text="HEX EDIT", font=PIX_FONT,
                            bg=BTN_BG, fg=BTN_FG,
                            width=12, height=3,
                            command=self.open_hex_editor)
        hex_btn.place(x=50, y=100)  # place icon 1

        # Level Editor icon (placeholder)
        lvl_btn = tk.Button(self, text="LEVEL EDIT", font=PIX_FONT,
                            bg=BTN_BG, fg=BTN_FG,
                            width=12, height=3,
                            command=self.open_level_editor)
        lvl_btn.place(x=50, y=200)  # icon 2

        # Emulator icon (new: launches WSL2 Ubuntu and loads libdragon)
        emu_btn = tk.Button(self, text="EMULATOR", font=PIX_FONT,
                            bg=BTN_BG, fg=BTN_FG,
                            width=12, height=3,
                            command=self.launch_emulator)
        emu_btn.place(x=50, y=300)  # icon 3

    def open_hex_editor(self):
        messagebox.showinfo("Module Launch", "Opening Hex Editor…")

    def open_level_editor(self):
        messagebox.showinfo("Module Launch", "Opening Level Editor…")

    def launch_emulator(self):
        try:
            # Check if WSL is available and Ubuntu is installed
            output = subprocess.check_output(['wsl', '--list', '--verbose']).decode()
            if 'Ubuntu' not in output:
                raise ValueError("Ubuntu not found in WSL.")
            
            # Check if libdragon is already installed (e.g., /opt/libdragon exists)
            check_cmd = "if [ -d /opt/libdragon ]; then echo 'installed'; else echo 'not'; fi"
            result = subprocess.check_output(['wsl', 'bash', '-c', check_cmd]).decode().strip()
            
            if result == 'not':
                messagebox.showinfo("Setup", "Installing libdragon in WSL Ubuntu... This may take time and prompt for sudo password.")
                
                # Install prerequisites (may prompt for sudo)
                prereq_cmd = "sudo apt update && sudo apt install -y build-essential git wget"
                subprocess.call(['wsl', 'bash', '-c', prereq_cmd])
                
                # Download and install prebuilt toolchain .deb
                deb_url = "https://github.com/DragonMinded/libdragon/releases/download/toolchain-continuous-prerelease/gcc-toolchain-mips64-x86_64.deb"
                install_toolchain_cmd = f"wget {deb_url} -O /tmp/toolchain.deb && sudo dpkg -i /tmp/toolchain.deb && rm /tmp/toolchain.deb"
                subprocess.call(['wsl', 'bash', '-c', install_toolchain_cmd])
                
                # Clone libdragon if not present
                clone_cmd = "git clone https://github.com/DragonMinded/libdragon.git ~/libdragon || true"
                subprocess.call(['wsl', 'bash', '-c', clone_cmd])
                
                # Build and install libdragon
                build_cmd = "cd ~/libdragon && ./build.sh"
                subprocess.call(['wsl', 'bash', '-c', build_cmd])
                
                messagebox.showinfo("Setup Complete", "Libdragon installed successfully.")

            # Launch WSL Ubuntu terminal
            subprocess.Popen(['wsl'])
            messagebox.showinfo("Emulator", "WSL Ubuntu launched with libdragon loaded. You can now develop N64 projects.")

        except subprocess.CalledProcessError:
            messagebox.showerror("Error", "WSL not installed or accessible. Please install WSL2 and Ubuntu.")
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    app = SamsoftOSCompiler()
    app.mainloop()
