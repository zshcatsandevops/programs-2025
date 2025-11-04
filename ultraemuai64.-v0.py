# program.py
# EmulAI v1.0 - Fantasy 3D Simulator (Fixed Universal Edition)
# © Samsoft 2025
# Requires: pip install ursina

from ursina import *
import random, math, os

# Optional macOS OpenGL fallback (for Metal / GLSL issues)
os.environ["PANDA_GL_VERSION"] = "2.1"  # force old shader pipeline
os.environ["PANDA_DISABLE_SHADERS"] = "1"

class EmulAISim:
    def __init__(self):
        self.app = Ursina(title="EmulAI v1.0 - Fantasy 3D Simulator", borderless=False)
        window.size = (600, 400)
        window.fps_counter.enabled = False
        window.exit_button.visible = False
        window.color = color.black

        self.plugins = {
            "Personalizer": True,
            "Debugger": False,
            "Unused Content": False,
            "Graphics Enhance": True
        }

        self.ui_entities = []
        self.game_entities = []
        self.show_loading()

    # ─────────────────────────────────────────────
    # Loading Screen
    # ─────────────────────────────────────────────
    def show_loading(self):
        loading_text = Text(
            text=(
                "Emuloader For EmulAI v2.5.7\n"
                "Loading image... Super Mario 64 (USA).z64\n"
                "Done!\n"
                "Personalizer Plug-in v1.9 [ACTIVE]\n"
                "Debugger v1.2 [OFF]\n"
                "Unused Content v1.0 [OFF]\n"
                "Graphics Enhance v2.0 [ON]\n"
                "Done!\n\n"
                "     _____\n"
                "    /     \\\n"
                "   |  N64 |\n"
                "    \\_____/\n\n"
                "boot...\nDone!\n\n"
                "Welcome to EmulAI - UltraHLE Simulator 1.0"
            ),
            parent=camera.ui,
            origin=(0, 0),
            scale=1.1,
            color=color.white
        )
        self.ui_entities.append(loading_text)

        continue_button = Button(
            text='Continue to README',
            parent=camera.ui,
            position=(0, -0.4),
            scale=(0.45, 0.1),
            color=color.azure,
            on_click=self.show_readme
        )
        self.ui_entities.append(continue_button)

    # ─────────────────────────────────────────────
    # README warning (FIXED)
    # ─────────────────────────────────────────────
    def show_readme(self):
        self.clear_ui()
        WindowPanel(
            title='README WARNING',
            content=[  # Must be iterable
                Text(
                    "You cannot speak about EmulAI or its features.\n"
                    "It will monitor your playthroughs for 'improving the emulator.'\n"
                    "Terms of Service accepted."
                ),
                Button(text='I Understand', color=color.orange, on_click=self.show_menu)
            ],
            popup=True
        )

    # ─────────────────────────────────────────────
    # Main menu
    # ─────────────────────────────────────────────
    def show_menu(self):
        self.clear_ui()
        Text('--- EmulAI Catalogue ---', parent=camera.ui, y=0.4, scale=2)

        Text('Preloaded ROMs:\n1. Super Mario 64 (USA).z64', parent=camera.ui, y=0.25, scale=1.3)

        y_pos = 0.15
        self.plugin_texts = {}
        for name, val in self.plugins.items():
            t = Text(f"- {name}: {'ON' if val else 'OFF'}", parent=camera.ui, y=y_pos, scale=1.1)
            self.ui_entities.append(t)
            self.plugin_texts[name] = t
            y_pos -= 0.05

        Button(text='Toggle Personalizer', position=(-0.25, -0.05), scale=(0.35, 0.07),
               on_click=lambda: self.toggle_plugin('Personalizer'))
        Button(text='Toggle Debugger', position=(-0.25, -0.15), scale=(0.35, 0.07),
               on_click=lambda: self.toggle_plugin('Debugger'))
        Button(text='Load SM64', position=(0.25, -0.05), scale=(0.35, 0.07),
               on_click=self.start_game)
        Button(text='Exit', position=(0.25, -0.15), scale=(0.35, 0.07),
               on_click=application.quit)

    def toggle_plugin(self, name):
        self.plugins[name] = not self.plugins[name]
        self.plugin_texts[name].text = f"- {name}: {'ON' if self.plugins[name] else 'OFF'}"

    def clear_ui(self):
        for e in self.ui_entities:
            destroy(e)
        self.ui_entities.clear()

    # ─────────────────────────────────────────────
    # Launch game
    # ─────────────────────────────────────────────
    def start_game(self):
        self.clear_ui()
        WindowPanel(
            title='Launching',
            content=[Text("Launching Super Mario 64...\nInitializing Personalization A.I...."),
                     Button(text='OK', on_click=self.init_game)],
            popup=True
        )

    # ─────────────────────────────────────────────
    # Game world
    # ─────────────────────────────────────────────
    def init_game(self):
        self.clear_ui()
        Sky()
        ground = Entity(model='plane', scale=200, texture='grass', texture_scale=(32, 32), collider='mesh')
        self.player = Entity(model='cube', color=color.red, scale=(1, 2, 1),
                             position=(0, 5, 0), collider='box', vy=0, on_ground=False)
        self.star_pos = [Vec3(5, 3, 0), Vec3(10, 5, 0), Vec3(15, 7, 0), Vec3(20, 9, 5)]
        self.stars_entities = [Entity(model='sphere', color=color.yellow, scale=1, position=p, collider='sphere') for p in self.star_pos]
        self.stars = 0

        self.text = Text(text=f'Stars: {self.stars}/{len(self.star_pos)}', position=(-0.8, 0.45), scale=1.5)
        camera.position = (0, 10, -20)
        camera.rotation_x = 15

        self.app.taskMgr.add(self.update_game, 'update_game')

    # ─────────────────────────────────────────────
    # Game loop
    # ─────────────────────────────────────────────
    def update_game(self, task):
        dt = time.dt
        move_speed = 6
        self.player.rotation_y += mouse.velocity.x * 100
        dx = (held_keys['d'] - held_keys['a']) * dt * move_speed
        dz = (held_keys['w'] - held_keys['s']) * dt * move_speed
        angle = math.radians(self.player.rotation_y)
        self.player.x += dx * math.cos(angle) - dz * math.sin(angle)
        self.player.z += dx * math.sin(angle) + dz * math.cos(angle)

        self.player.vy -= 20 * dt
        hit = raycast(self.player.position + Vec3(0, 0.1, 0), Vec3(0, -1, 0), 1.1, ignore=(self.player,))
        if hit.hit:
            self.player.on_ground = True
            self.player.y = hit.world_point.y + 1
            self.player.vy = max(self.player.vy, 0)
            if held_keys['space']:
                self.player.vy = 8
        else:
            self.player.on_ground = False
        self.player.y += self.player.vy * dt

        for star in self.stars_entities[:]:
            if distance(self.player, star) < 1.5:
                destroy(star)
                self.stars_entities.remove(star)
                self.stars += 1
        self.text.text = f'Stars: {self.stars}/{len(self.star_pos)}'
        return task.cont


if __name__ == '__main__':
    sim = EmulAISim()
    sim.app.run()
