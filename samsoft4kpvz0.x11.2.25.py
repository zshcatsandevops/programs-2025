    #!/usr/bin/env python3
    # -*- coding: utf-8 -*-
    """
    Plants vs. Zombies: Rebooted InfDev 0.1 — Cinematic Intro + Lawn Prototype
    ---------------------------------------------------------------------------
    Samsoft Presents → EA swirl → PopCap logo sequence → PVZ‑style lawn gameplay.
    Procedural effects, no external files.

    © Samsoft 2025
    © 2000s PopCap Games (fanmade prototype mechanics; no proprietary assets).
    """

    import pygame, math, sys, random, time
    try:
        import numpy as np
        HAS_NUMPY = True
    except ImportError:
        HAS_NUMPY = False
        np = None

    pygame.init()
    try:
        # BUG FIX 1: Changed to stereo (channels=2)
        pygame.mixer.init(frequency=44100, size=-16, channels=2)
    except Exception:
        pass

    # ───────── CONFIG ─────────
    SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
    BLACK, WHITE = (0,0,0), (255,255,255)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Samsoft + EA + PopCap Intro → PVZ Lawn Prototype")
    clock = pygame.time.Clock()  # BUG FIX 2: Moved clock to global scope

    # Grid / board layout
    ROWS, COLS = 5, 9
    TOP_UI_H = 84
    BOARD_Y = TOP_UI_H
    CELL_W = 80
    CELL_H = (SCREEN_HEIGHT - TOP_UI_H - 20) // ROWS  # 600 - 84 - 20 = 496 -> 99 per row; we fix to 100
    CELL_H = 100
    BOARD_H = CELL_H * ROWS  # 500
    BOARD_W = CELL_W * COLS  # 720
    BOARD_X = (SCREEN_WIDTH - BOARD_W) // 2  # 40
    BOARD_RECT = pygame.Rect(BOARD_X, BOARD_Y, BOARD_W, BOARD_H)

    LANE_CENTERS_Y = [BOARD_Y + r * CELL_H + CELL_H // 2 for r in range(ROWS)]
    COL_CENTER_X = [BOARD_X + c * CELL_W + CELL_W // 2 for c in range(COLS)]

    # ───────── SIMPLE SYNTH HELPERS ─────────
    def _mixer_channels():
        try:
            info = pygame.mixer.get_init()
            if info:
                _, _, ch = info
                return ch
        except Exception:
            pass
        return 1

    def make_tone(freq=440, dur=0.20, vol=0.25, wave="square"):
        """Procedurally generate a tone sound (mono or stereo) using numpy if available."""
        if not HAS_NUMPY:
            return None
        sr = 44100
        t = np.linspace(0, dur, int(sr * dur), False)
        if wave == "square":
            w = np.sign(np.sin(2 * math.pi * freq * t))
        elif wave == "sine":
            w = np.sin(2 * math.pi * freq * t)
        else:
            w = np.sin(2 * math.pi * freq * t)

        audio = (w * vol * 32767).astype(np.int16)
        try:
            # BUG FIX 7: Match stereo mixer with stereo buffer to avoid make_sound errors.
            ch = _mixer_channels()
            if ch == 2:
                audio = np.repeat(audio[:, None], 2, axis=1)
            return pygame.sndarray.make_sound(audio)
        except Exception:
            return None

    def play_seq(seq):
        """Play a sequence of (freq, duration) tones (non-blocking per-event, timed by waits)."""
        for f, d in seq:
            s = make_tone(f, d)
            if s:
                s.play()
            pygame.time.wait(int(d * 1000))

    # ───────── HELPERS ─────────
    def safe_quit_check():
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif e.type == pygame.KEYDOWN:  # BUG FIX 3: Added keyboard quit
                if e.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

    def fade_to_black(speed=10, delay=15):
        fade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        fade.fill(BLACK)
        for a in range(0, 255, speed):
            safe_quit_check()
            fade.set_alpha(a)
            screen.blit(fade, (0, 0))
            pygame.display.flip()
            pygame.time.delay(delay)

    # ───────── SAMSOFT PRESENTS ─────────
    def samsoft_intro():
        font = pygame.font.SysFont("arialblack", 72, bold=True)
        angle = 0
        play_seq([(220, 0.18), (440, 0.18), (880, 0.22)])
        for frame in range(180):
            safe_quit_check()
            screen.fill(BLACK)
            # rotating rectangles
            for i in range(6):
                size = 120 + 40 * math.sin(math.radians(angle + i * 60))
                c = int(150 + 100 * math.sin(math.radians(angle * 2 + i * 30)))
                rect = pygame.Rect(0, 0, size, size)
                rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
                try:
                    pygame.draw.rect(screen, (c, c, 255), rect, 6, border_radius=12)  # BUG FIX 4
                except:
                    pygame.draw.rect(screen, (c, c, 255), rect, 6)
            # text
            pulse = 0.5 + 0.5 * math.sin(math.radians(angle * 3))
            text = font.render(
                "Samsoft Presents", True, (int(255 * pulse), int(255 * pulse), 255)
            )
            screen.blit(
                text,
                (
                    SCREEN_WIDTH // 2 - text.get_width() // 2,
                    SCREEN_HEIGHT // 2 - text.get_height() // 2,
                ),
            )
            pygame.display.flip()
            clock.tick(60)  # BUG FIX 5: Use global clock
            angle += 4
        fade_to_black()

    # ───────── EA LOGO ─────────
    def ea_logo():
        font = pygame.font.SysFont("arialblack", 100, bold=True)
        alpha, angle = 0, 0
        play_seq([(220, 0.26), (330, 0.26), (440, 0.32)])
        for frame in range(180):
            safe_quit_check()
            screen.fill(BLACK)
            # swirl ring safely bounded
            for i in range(20):
                radius = 60 + i * 4
                c = (100 + i * 6, 100 + i * 4, 255 - i * 6)
                rect = pygame.Rect(
                    SCREEN_WIDTH // 2 - radius, SCREEN_HEIGHT // 2 - radius,
                    radius * 2, radius * 2
                )  # BUG FIX 6
                pygame.draw.arc(
                    screen,
                    c,
                    rect,
                    math.radians(angle + i * 12),
                    math.radians(angle + i * 12 + 200),
                    4,
                )
            # EA text
            text = font.render("EA", True, WHITE)
            surf = text.copy()
            surf.set_alpha(alpha)
            screen.blit(
                surf,
                (
                    SCREEN_WIDTH // 2 - text.get_width() // 2,
                    SCREEN_HEIGHT // 2 - text.get_height() // 2,
                ),
            )
            pygame.display.flip()
            clock.tick(60)
            angle += 6
            if frame < 60:
                alpha = min(255, alpha + 5)
            elif frame > 120:
                alpha = max(0, alpha - 6)
        fade_to_black()

    # ───────── POPCAP LOGO ─────────
    def popcap_logo():
        font_main = pygame.font.SysFont("arialblack", 100, bold=True)
        font_sub = pygame.font.SysFont("arial", 42, bold=True)
        alpha, angle = 0, 0
        play_seq([(440, 0.12), (660, 0.12), (880, 0.12), (1320, 0.12), (990, 0.22)])
        for frame in range(240):
            safe_quit_check()
            screen.fill(BLACK)
            # red circle background
            pygame.draw.circle(screen, (255, 60, 60), (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 150)
            pygame.draw.circle(screen, WHITE, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 160, 8)
            # swirl sparkle
            for i in range(12):
                a = angle + i * 30
                x = SCREEN_WIDTH // 2 + 140 * math.cos(math.radians(a))
                y = SCREEN_HEIGHT // 2 + 140 * math.sin(math.radians(a))
                pygame.draw.circle(screen, (255, 255, 255), (int(x), int(y)), 6)
            # text
            text1 = font_main.render("Pop", True, WHITE)
            text2 = font_sub.render("Cap", True, WHITE)
            text1.set_alpha(alpha)
            text2.set_alpha(alpha)
            screen.blit(text1, (SCREEN_WIDTH // 2 - text1.get_width() // 2, SCREEN_HEIGHT // 2 - 60))
            screen.blit(text2, (SCREEN_WIDTH // 2 - text2.get_width() // 2, SCREEN_HEIGHT // 2 + 20))
            pygame.display.flip()
            clock.tick(60)
            angle += 4
            if frame < 60:
                alpha = min(255, alpha + 5)
            elif frame > 180:
                alpha = max(0, alpha - 5)
        fade_to_black()

    # ───────── GAMEPLAY (PVZ‑style prototype) ─────────
    FONT_BIG = pygame.font.SysFont("arialblack", 32, bold=True)
    FONT_MED = pygame.font.SysFont("arialblack", 18, bold=True)
    FONT_SMALL = pygame.font.SysFont("arial", 16, bold=True)

    # tiny tone helpers
    SND_PLANT = lambda: (make_tone(660, 0.05, 0.25, "sine") or None).play() if make_tone else None
    SND_SHOOT = lambda: (make_tone(880, 0.03, 0.2, "square") or None).play() if make_tone else None
    SND_BITE = lambda: (make_tone(220, 0.04, 0.25, "square") or None).play() if make_tone else None
    SND_SUN   = lambda: (make_tone(1320, 0.06, 0.25, "sine") or None).play() if make_tone else None
    SND_MOWER = lambda: (make_tone(330, 0.15, 0.3, "square") or None).play() if make_tone else None
    SND_WIN   = lambda: (make_tone(990, 0.25, 0.3, "sine") or None).play() if make_tone else None
    SND_LOSE  = lambda: (make_tone(110, 0.35, 0.3, "square") or None).play() if make_tone else None

    def cell_center(rc):
        r, c = rc
        return (BOARD_X + c * CELL_W + CELL_W // 2,
                BOARD_Y + r * CELL_H + CELL_H // 2)

    def pos_to_cell(px, py):
        if not BOARD_RECT.collidepoint(px, py):
            return None
        c = (px - BOARD_X) // CELL_W
        r = (py - BOARD_Y) // CELL_H
        r = max(0, min(ROWS-1, int(r)))
        c = max(0, min(COLS-1, int(c)))
        return (int(r), int(c))

    class SeedPacket:
        def __init__(self, name, cost, cooldown_ms, color, key, tooltip):
            self.name = name
            self.cost = cost
            self.cooldown_ms = cooldown_ms
            self.color = color
            self.key = key  # hotkey char for quick select
            self.tooltip = tooltip
            self.last_used = -1_000_000
            self.rect = pygame.Rect(0, 0, 110, 64)

        def ready(self, sun, now_ms):
            cooled = (now_ms - self.last_used) >= self.cooldown_ms
            return cooled and sun >= self.cost

        def draw(self, surf, x, y, sun, now_ms, selected=False):
            self.rect.topleft = (x, y)
            pygame.draw.rect(surf, (40, 40, 40), self.rect, border_radius=8)
            inner = self.rect.inflate(-6, -6)
            pygame.draw.rect(surf, self.color, inner, border_radius=8)
            # cooldown overlay
            since = now_ms - self.last_used
            if since < self.cooldown_ms:
                pct = 1 - (since / self.cooldown_ms)
                h = int(inner.height * pct)
                cd_rect = pygame.Rect(inner.left, inner.top, inner.width, h)
                cd = pygame.Surface((inner.width, h), pygame.SRCALPHA)
                cd.fill((0,0,0,160))
                surf.blit(cd, cd_rect.topleft)
            # cost & label
            label = FONT_SMALL.render(f"{self.name}  [{self.key}]  {self.cost}☼", True, WHITE)
            surf.blit(label, (inner.left + 8, inner.top + 6))
            tip = FONT_SMALL.render(self.tooltip, True, WHITE)
            surf.blit(tip, (inner.left + 8, inner.top + 30))
            # selected highlight
            if selected:
                pygame.draw.rect(surf, WHITE, self.rect, 3, border_radius=8)
            else:
                pygame.draw.rect(surf, (0,0,0), self.rect, 2, border_radius=8)

    class Plant:
        cost = 0
        max_hp = 300
        color = (80, 180, 80)
        cooldown_ms = 7000
        def __init__(self, r, c):
            self.r, self.c = r, c
            cx, cy = cell_center((r,c))
            self.x, self.y = cx, cy
            self.hp = self.max_hp
            self.width, self.height = 62, 82
            self.shoot_timer = 0.0

        @property
        def rect(self):
            return pygame.Rect(int(self.x - self.width//2), int(self.y - self.height//2), self.width, self.height)

        def update(self, game, dt):
            pass

        def draw(self, surf):
            pygame.draw.rect(surf, self.color, self.rect, border_radius=10)
            # tiny health bar
            hp_ratio = max(0, self.hp / self.max_hp)
            bar = pygame.Rect(self.rect.left, self.rect.top - 6, int(self.rect.width * hp_ratio), 4)
            pygame.draw.rect(surf, (20, 200, 30), bar)

        def take_damage(self, dmg):
            self.hp -= dmg

    class Sunflower(Plant):
        cost = 50
        color = (255, 200, 60)
        cooldown_ms = 7000
        max_hp = 300
        def __init__(self, r, c):
            super().__init__(r,c)
            self.gen_timer = 3.0  # first sun sooner, then every ~7s
        def update(self, game, dt):
            self.gen_timer -= dt
            if self.gen_timer <= 0:
                self.gen_timer = 7.0 + random.uniform(-1.0, 1.2)
                sx = self.x + random.randint(-8, 8)
                sy = self.y - 24
                game.spawn_sun(sx, sy, fall=False)

    class Peashooter(Plant):
        cost = 100
        color = (80, 200, 255)
        cooldown_ms = 7500
        max_hp = 300
        def __init__(self, r, c):
            super().__init__(r,c)
            self.shoot_cd = 1.35
            self.shoot_timer = random.uniform(0.1, 0.9)
        def update(self, game, dt):
            self.shoot_timer -= dt
            if self.shoot_timer <= 0:
                self.shoot_timer = self.shoot_cd
                game.spawn_pea(self.x + 30, self.y)
                try: SND_SHOOT()
                except: pass
        def draw(self, surf):
            super().draw(surf)
            # muzzle
            pygame.draw.circle(surf, (200, 255, 255), (int(self.x+22), int(self.y-10)), 8)

    class WallNut(Plant):
        cost = 50
        color = (170, 120, 60)
        cooldown_ms = 12000
        max_hp = 1600
        def draw(self, surf):
            # chunky body + face
            pygame.draw.rect(surf, self.color, self.rect, border_radius=16)
            eye1 = (int(self.x-12), int(self.y-10))
            eye2 = (int(self.x+12), int(self.y-10))
            pygame.draw.circle(surf, BLACK, eye1, 4)
            pygame.draw.circle(surf, BLACK, eye2, 4)

    PLANT_TYPES = {
        "Sunflower": Sunflower,
        "Peashooter": Peashooter,
        "Wall‑Nut":  WallNut
    }

    class Pea:
        def __init__(self, x, y):
            self.x, self.y = x, y
            self.speed = 280  # px/s
            self.radius = 6
            self.damage = 20
            self.dead = False
        @property
        def rect(self):
            return pygame.Rect(int(self.x-self.radius), int(self.y-self.radius), self.radius*2, self.radius*2)
        def update(self, game, dt):
            self.x += self.speed * dt
            # collide with first zombie in lane
            for z in game.zombies:
                if abs(z.y - self.y) < 32 and self.rect.colliderect(z.rect):
                    z.take_damage(self.damage)
                    self.dead = True
                    break
            if self.x > SCREEN_WIDTH + 20:
                self.dead = True
        def draw(self, surf):
            pygame.draw.circle(surf, (80, 240, 80), (int(self.x), int(self.y)), self.radius)

    class SunToken:
        def __init__(self, x, y, fall=True):
            self.x, self.y = x, y
            self.value = 25
            self.fall = fall
            self.target_y = y + random.randint(120, 220) if fall else y
            self.vy = 40 if fall else 0
            self.spawn_time = pygame.time.get_ticks()
            self.life_ms = 7500
            self.collected = False
            self.radius = 16
            self.bob_phase = random.random() * math.tau
        @property
        def rect(self):
            return pygame.Rect(int(self.x - self.radius), int(self.y - self.radius), self.radius*2, self.radius*2)
        def update(self, game, dt):
            if self.fall and self.y < self.target_y:
                self.y = min(self.target_y, self.y + self.vy * dt)
            else:
                # gentle bob
                self.y += math.sin((pygame.time.get_ticks()/300.0) + self.bob_phase) * 0.2
            if pygame.time.get_ticks() - self.spawn_time > self.life_ms:
                self.collected = True
        def draw(self, surf):
            # sun-like burst
            pygame.draw.circle(surf, (255, 240, 90), (int(self.x), int(self.y)), self.radius)
            for i in range(8):
                ang = i * (math.pi/4)
                x2 = self.x + math.cos(ang)* (self.radius+7)
                y2 = self.y + math.sin(ang)* (self.radius+7)
                pygame.draw.line(surf, (255, 255, 130), (self.x, self.y), (x2, y2), 2)

    class Zombie:
        def __init__(self, r, speed=22, hp=220):
            self.r = r
            self.y = LANE_CENTERS_Y[r]
            self.x = BOARD_X + COLS*CELL_W + 40 + random.randint(0,60)  # offscreen start
            self.width, self.height = 54, 92
            self.speed = speed  # px/s
            self.hp = hp
            self.eating = False
            self.eat_timer = 0.0
            self.dead = False
            self.bite_dps = 18.0
        @property
        def rect(self):
            return pygame.Rect(int(self.x - self.width//2), int(self.y - self.height//2), self.width, self.height)
        def update(self, game, dt):
            self.eating = False
            # check plant in same cell range
            c = int((self.x - BOARD_X) // CELL_W)
            c = max(0, min(COLS-1, c))
            plant = game.plants.get((self.r, c))
            if plant:
                # overlap check
                if self.rect.colliderect(plant.rect):
                    self.eating = True
                    plant.take_damage(self.bite_dps * dt)
                    self.eat_timer += dt
                    if self.eat_timer > 0.30:
                        self.eat_timer = 0
                        try: SND_BITE()
                        except: pass
            if not self.eating:
                self.x -= self.speed * dt

            if self.hp <= 0: self.dead = True
            # hit mower / lose if reaches house
            if self.x < BOARD_X - 26:
                # if the mower hasn't saved the lane, trigger lose
                if not game.trigger_mower_if_possible(self.r):
                    game.lose()
                    self.dead = True
        def draw(self, surf):
            body_col = (140, 160, 140) if not self.eating else (170, 100, 90)
            pygame.draw.rect(surf, body_col, self.rect, border_radius=8)
            # head
            head = pygame.Rect(self.rect.left+8, self.rect.top-14, 26, 20)
            pygame.draw.rect(surf, (200, 210, 200), head, border_radius=5)
            # hp bar
            hp_ratio = max(0, self.hp/220.0)
            hb = pygame.Rect(self.rect.left, self.rect.top-6, int(self.rect.width*hp_ratio), 4)
            pygame.draw.rect(surf, (220, 40, 40), hb)

        def take_damage(self, dmg):
            self.hp -= dmg

    class Mower:
        def __init__(self, r):
            self.r = r
            self.x = BOARD_X - 30
            self.y = LANE_CENTERS_Y[r] + 16
            self.width, self.height = 44, 28
            self.active = True
            self.triggered = False
            self.speed = 520  # px/s once triggered
        @property
        def rect(self):
            return pygame.Rect(int(self.x - self.width//2), int(self.y - self.height//2), self.width, self.height)
        def update(self, game, dt):
            if not self.active: return
            if self.triggered:
                self.x += self.speed * dt
                # shred zombies in lane
                for z in game.zombies:
                    if z.r == self.r and self.rect.colliderect(z.rect):
                        z.dead = True
                if self.x > SCREEN_WIDTH + 40:
                    self.active = False
        def draw(self, surf):
            if not self.active: return
            pygame.draw.rect(surf, (230, 230, 230), self.rect, border_radius=6)
            wheel1 = (int(self.x-12), int(self.y+12))
            wheel2 = (int(self.x+12), int(self.y+12))
            pygame.draw.circle(surf, BLACK, wheel1, 6)
            pygame.draw.circle(surf, BLACK, wheel2, 6)

    class Game:
        def __init__(self):
            self.reset()

        def reset(self):
            self.sun = 50
            self.selected = None  # index into self.cards
            self.plants = {}  # (r,c) -> Plant instance
            self.projectiles = []
            self.zombies = []
            self.suns = []
            self.mowers = [Mower(r) for r in range(ROWS)]
            # UI seed packets
            self.cards = [
                SeedPacket("Sunflower", Sunflower.cost, Sunflower.cooldown_ms, (250,190,60), "1", "Generates ☼"),
                SeedPacket("Peashooter", Peashooter.cost, Peashooter.cooldown_ms, (80,200,255), "2", "Shoots peas"),
                SeedPacket("Wall‑Nut",  WallNut.cost,  WallNut.cooldown_ms,  (170,120,60), "3", "Blocks"),
            ]
            # spawn timing
            self.level_total = 26
            self.spawned = 0
            self.next_spawn_t = 2.5
            self.sky_sun_t = 3.0
            self.state = "play"  # play|win|lose
            self.state_time = 0.0
            self.start_time = time.time()

        # ---- spawners
        def spawn_pea(self, x, y):
            self.projectiles.append(Pea(x, y))

        def spawn_sun(self, x, y, fall=True):
            self.suns.append(SunToken(x, y, fall=fall))
            try: SND_SUN()
            except: pass

        def trigger_mower_if_possible(self, r):
            m = self.mowers[r]
            if m.active and not m.triggered:
                m.triggered = True
                try: SND_MOWER()
                except: pass
                return True
            return False

        def lose(self):
            if self.state != "lose":
                self.state = "lose"
                self.state_time = 0.0
                try: SND_LOSE()
                except: pass

        def win(self):
            if self.state != "win":
                self.state = "win"
                self.state_time = 0.0
                try: SND_WIN()
                except: pass

        # ---- main loop
        def run(self):
            running = True
            while running:
                dt = clock.tick(60) / 1000.0
                # Events (do NOT call safe_quit_check here; we need clicks)
                for e in pygame.event.get():
                    if e.type == pygame.QUIT:
                        running = False
                    elif e.type == pygame.KEYDOWN:
                        if e.key == pygame.K_ESCAPE:
                            running = False
                        if self.state in ("win","lose"):
                            if e.key == pygame.K_r:
                                self.reset()
                                continue
                        # hotspots quick-select
                        if e.key in (pygame.K_1, pygame.K_KP1): self.selected = 0
                        elif e.key in (pygame.K_2, pygame.K_KP2): self.selected = 1
                        elif e.key in (pygame.K_3, pygame.K_KP3): self.selected = 2
                    elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                        self.on_click(e.pos)

                # Update
                if self.state == "play":
                    self.update(dt)
                else:
                    self.state_time += dt

                # Draw
                self.draw()

                if not running:
                    break
            pygame.quit()
            sys.exit()

        # ---- input helpers
        def on_click(self, pos):
            now = pygame.time.get_ticks()
            # collect suns?
            for s in self.suns:
                if s.rect.collidepoint(pos) and not s.collected:
                    s.collected = True
                    self.sun += s.value
                    try: SND_SUN()
                    except: pass
                    return
            # seed packets click?
            for i,card in enumerate(self.cards):
                if card.rect.collidepoint(pos):
                    self.selected = i if self.selected != i else None
                    return
            # plant placement
            if self.selected is not None:
                rc = pos_to_cell(*pos)
                if rc:
                    r,c = rc
                    if (r,c) not in self.plants:
                        card = self.cards[self.selected]
                        if card.ready(self.sun, now):
                            plant_cls = PLANT_TYPES[card.name]
                            self.plants[(r,c)] = plant_cls(r,c)
                            self.sun -= card.cost
                            card.last_used = now
                            try: SND_PLANT()
                            except: pass

        # ---- game update/draw
        def update(self, dt):
            now = pygame.time.get_ticks()

            # spawn sky sun periodically
            self.sky_sun_t -= dt
            if self.sky_sun_t <= 0:
                self.sky_sun_t = random.uniform(6.5, 9.0)
                cx = BOARD_X + random.randint(0, BOARD_W)
                self.spawn_sun(cx, BOARD_Y - 24, fall=True)

            # spawn zombies
            self.next_spawn_t -= dt
            if self.spawned < self.level_total and self.next_spawn_t <= 0:
                lane = random.randint(0, ROWS-1)
                # dynamic difficulty: faster spawns over time
                elapsed = time.time() - self.start_time
                base = max(1.4, 5.0 - 0.05 * elapsed)
                self.next_spawn_t = base + random.uniform(0.0, 1.6)
                self.zombies.append(Zombie(lane))
                self.spawned += 1

            # update mowers
            for m in self.mowers:
                m.update(self, dt)

            # update plants
            died = []
            for rc, plant in list(self.plants.items()):
                plant.update(self, dt)
                if plant.hp <= 0:
                    died.append(rc)
            for rc in died:
                self.plants.pop(rc, None)

            # update peas
            for p in self.projectiles:
                p.update(self, dt)
            self.projectiles = [p for p in self.projectiles if not p.dead]

            # update suns
            for s in self.suns:
                s.update(self, dt)
            self.suns = [s for s in self.suns if not s.collected]

            # update zombies
            for z in self.zombies:
                z.update(self, dt)
            self.zombies = [z for z in self.zombies if not z.dead]

            # win condition
            if self.spawned >= self.level_total and not self.zombies:
                self.win()

        def draw_grid(self, surf):
            # lawn stripes
            for r in range(ROWS):
                y0 = BOARD_Y + r * CELL_H
                col = (70, 140, 70) if r % 2 == 0 else (78, 150, 78)
                pygame.draw.rect(surf, col, (BOARD_X, y0, BOARD_W, CELL_H))
            # vertical separators
            for c in range(COLS+1):
                x = BOARD_X + c * CELL_W
                pygame.draw.line(surf, (30, 90, 30), (x, BOARD_Y), (x, BOARD_Y + BOARD_H), 2)
            # edge
            pygame.draw.rect(surf, (20, 60, 20), BOARD_RECT, 3)

        def draw_ui(self, surf):
            # top bar
            pygame.draw.rect(surf, (25, 25, 25), (0,0, SCREEN_WIDTH, TOP_UI_H))
            title = FONT_BIG.render("PVZ‑style Lawn — Samsoft Rebooted (Prototype)", True, WHITE)
            surf.blit(title, (16, 10))

            # sun counter
            sun_text = FONT_MED.render(f"☼ {self.sun}", True, (255, 230, 120))
            surf.blit(sun_text, (SCREEN_WIDTH - 130, 14))

            # seed packets
            x = 16
            for i, card in enumerate(self.cards):
                selected = (self.selected == i)
                card.draw(surf, x, 44 - 8, self.sun, pygame.time.get_ticks(), selected)
                x += card.rect.width + 10

        def draw(self):
            screen.fill((10, 20, 14))
            self.draw_grid(screen)
            # suns beneath plants so they peek out properly
            for s in self.suns:
                s.draw(screen)
            # plants
            for plant in self.plants.values():
                plant.draw(screen)
            # projectiles
            for p in self.projectiles:
                p.draw(screen)
            # zombies
            for z in self.zombies:
                z.draw(screen)
            # mowers
            for m in self.mowers:
                m.draw(screen)
            # UI
            self.draw_ui(screen)
            # state overlays
            if self.state == "win":
                self.draw_center_message("LEVEL COMPLETE!", "Press R to play again")
            elif self.state == "lose":
                self.draw_center_message("ZOMBIES REACHED YOUR HOUSE!", "Press R to retry")
            pygame.display.flip()

        def draw_center_message(self, title, subtitle):
            # dim
            shade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            shade.fill((0,0,0,150))
            screen.blit(shade, (0,0))
            t = FONT_BIG.render(title, True, WHITE)
            s = FONT_MED.render(subtitle, True, WHITE)
            screen.blit(t, (SCREEN_WIDTH//2 - t.get_width()//2, SCREEN_HEIGHT//2 - 32))
            screen.blit(s, (SCREEN_WIDTH//2 - s.get_width()//2, SCREEN_HEIGHT//2 + 10))


    # ───────── RUN ─────────
    if __name__ == "__main__":
        try:
            # Cinematic → Gameplay
            samsoft_intro()
            ea_logo()
            popcap_logo()
            pygame.time.wait(350)

            Game().run()

        finally:
            pygame.quit()
