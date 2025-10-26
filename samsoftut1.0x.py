# program.py
# UNDERTALEPYDECOMP4K — Compact 600x400 / 60 FPS Windows build (single-file, no external assets)
# This is a clean, optimized refactor of the provided prototype aiming to *feel*
# closer to Undertale while staying asset-free and fan-project friendly.
# Notes:
# - Resolution: 600x400
# - FPS: 60
# - Save to disk is DISABLED by default (toggle SAVE_ENABLED = True to enable).
# - No external files, fonts, images, or sounds required.
# - Windows-friendly (works cross‑platform, too). For packaging on Windows, see bottom.

import os
import sys
import json
import math
import time
import random
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

# ---------- Windows friendliness (safe defaults, no-ops on other OS) ----------
if sys.platform.startswith("win"):
    # Use default drivers; keep environment minimal for broad compatibility
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    # (Optional) Reduce audio init issues on some Windows systems; we don't load audio here.
    os.environ.setdefault("SDL_AUDIODRIVER", "directsound")

import pygame

# ---------- Global configuration ----------
SCREEN_WIDTH, SCREEN_HEIGHT = 600, 400
FPS = 60
SAVE_ENABLED = False  # <- set True to enable JSON save/load to disk

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
PURPLE = (128, 0, 128)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)

# ---------- Enums ----------
class GameState(Enum):
    MENU = auto()
    OVERWORLD = auto()
    BATTLE = auto()
    DIALOGUE = auto()
    SAVE = auto()
    GAME_OVER = auto()
    CREDITS = auto()

class RouteType(Enum):
    NEUTRAL = auto()
    PACIFIST = auto()
    GENOCIDE = auto()
    TRUE_PACIFIST = auto()

class Area(Enum):
    RUINS = auto()
    SNOWDIN = auto()
    WATERFALL = auto()
    HOTLAND = auto()
    CORE = auto()
    NEW_HOME = auto()
    TRUE_LAB = auto()
    JUDGEMENT_HALL = auto()

# ---------- Data classes ----------
@dataclass
class Monster:
    name: str
    hp: int
    max_hp: int
    attack: int
    defense: int
    gold: int
    exp: int
    can_spare: bool = False
    betrayed: bool = False
    dialogue: List[str] = field(default_factory=list)
    acts: List[str] = field(default_factory=lambda: ["Check", "Talk"])

    def __post_init__(self):
        if not self.dialogue:
            self.dialogue = [f"* {self.name} approaches!"]

@dataclass
class Item:
    name: str
    type: str  # "heal", "weapon", "armor", "key"
    description: str
    heal_amount: int = 0
    attack_bonus: int = 0
    defense_bonus: int = 0
    usable_in_battle: bool = True

# ---------- Player ----------
class Player:
    def __init__(self):
        self.name = "Frisk"
        self.lv = 1
        self.hp = 20
        self.max_hp = 20
        self.at = 10
        self.df = 10
        self.exp = 0
        self.gold = 0
        self.weapon = "Stick"
        self.armor = "Bandage"
        self.inventory: List[str] = ["Pie"]
        self.kills = 0
        self.area_kills: Dict[Area, int] = {area: 0 for area in Area}
        self.spared = 0
        self.betrayals = 0
        self.friends: List[str] = []
        self.flags: Dict[str, bool] = {}
        self.x = 0
        self.y = 0
        self.facing = "down"

    def gain_exp(self, amount: int):
        self.exp += amount
        exp_needed = self.lv * 10 + (self.lv - 1) * 10
        while self.exp >= exp_needed:
            self.level_up()
            exp_needed = self.lv * 10 + (self.lv - 1) * 10

    def level_up(self):
        self.lv += 1
        old_max = self.max_hp
        self.max_hp = 20 + (self.lv - 1) * 4
        self.hp = min(self.hp + (self.max_hp - old_max), self.max_hp)
        self.at = 10 + (self.lv - 1) * 2
        self.df = 10 + (self.lv - 1) * 2

    def take_damage(self, damage: int) -> int:
        # Softer defense curve (feels closer to Undertale's early game)
        reduced = int(max(1, damage - max(0, self.df // 3)))
        self.hp -= reduced
        return reduced

    def heal(self, amount: int) -> int:
        old = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - old

    def add_item(self, item_name: str) -> bool:
        if len(self.inventory) < 8:
            self.inventory.append(item_name)
            return True
        return False

    def remove_item(self, item_name: str) -> bool:
        if item_name in self.inventory:
            self.inventory.remove(item_name)
            return True
        return False

# ---------- Game Data ----------
class GameData:
    ITEMS: Dict[str, Item] = {
        "Pie": Item("Butterscotch Pie", "heal", "Butterscotch-cinnamon pie", 99),
        "Nice Cream": Item("Nice Cream", "heal", "Heals 15 HP", 15),
        "Cinnamon Bun": Item("Cinnamon Bun", "heal", "Heals 22 HP", 22),
        "Snowman Piece": Item("Snowman Piece", "heal", "Please take this to the end", 45),

        # Weapons
        "Stick": Item("Stick", "weapon", "Its bark is worse than its bite", 0, 0, 0, False),
        "Toy Knife": Item("Toy Knife", "weapon", "Made of plastic. A rarity nowadays", 0, 3, 0, False),

        # Armor
        "Bandage": Item("Bandage", "armor", "It has already been used several times", 0, 0, 0, False),
        "Faded Ribbon": Item("Faded Ribbon", "armor", "If you're cuter, monsters won't hit you as hard", 0, 0, 3, False),
    }

    MONSTERS: Dict[str, Monster] = {
        # Ruins
        "Froggit": Monster("Froggit", 30, 30, 5, 4, 2, 3),
        "Whimsun": Monster("Whimsun", 12, 12, 5, 0, 2, 2, acts=["Check","Console","Spare"]),
        "Moldsmal": Monster("Moldsmal", 50, 50, 6, 0, 3, 3, acts=["Check","Flirt","Spare"]),
        "Loox": Monster("Loox", 50, 50, 6, 6, 5, 5, acts=["Check","Don't Pick On","Pick On"]),
        "Vegetoid": Monster("Vegetoid", 72, 72, 6, 7, 8, 6, acts=["Check","Dinner","Talk"]),

        # Snowdin (selection)
        "Snowdrake": Monster("Snowdrake", 50, 50, 6, 4, 8, 5, acts=["Check","Laugh","Heckle"]),
        "Doggo": Monster("Doggo", 70, 70, 7, 2, 30, 30, acts=["Check","Pet","Throw Stick"]),

        # Boss samples (HP tuned for prototype balance)
        "Toriel": Monster("Toriel", 300, 300, 8, 4, 0, 0, acts=["Check","Talk"]),
        "Papyrus": Monster("Papyrus", 420, 420, 9, 3, 0, 0, acts=["Check","Flirt","Insult"]),
        "Undyne": Monster("Undyne", 900, 900, 10, 5, 0, 0, acts=["Check","Plead"]),
        "Sans": Monster("Sans", 1, 1, 10, 1, 0, 0, acts=["Check"]),
    }

# ---------- Utility: text wrap & caching ----------
class TextCache:
    def __init__(self, font: pygame.font.Font):
        self.font = font
        self.cache: Dict[Tuple[str, Tuple[int,int,int]], pygame.Surface] = {}

    def render(self, text: str, color=WHITE) -> pygame.Surface:
        key = (text, color)
        surf = self.cache.get(key)
        if surf is None:
            surf = self.font.render(text, True, color)
            self.cache[key] = surf
        return surf

def wrap_text(font: pygame.font.Font, text: str, max_width: int) -> List[str]:
    words = text.split(' ')
    lines: List[str] = []
    cur = ''
    for w in words:
        test = f"{cur}{w} " if cur else f"{w} "
        if font.size(test)[0] <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur.rstrip())
            cur = f"{w} "
    if cur:
        lines.append(cur.rstrip())
    return lines

# ---------- Dialogue System ----------
class DialogueSystem:
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        self.text = ""
        self.char_index = 0
        self.finished = False
        self.choices: List[str] = []
        self.selected_choice = 0
        self.box = pygame.Rect(24, SCREEN_HEIGHT - 120, SCREEN_WIDTH - 48, 100)
        self.text_cache = TextCache(font)

    def start_dialogue(self, text: str, choices: Optional[List[str]] = None):
        self.text = text
        self.char_index = 0
        self.finished = False
        self.choices = choices or []
        self.selected_choice = 0

    def update(self, dt: float):
        # Reveal ~60 chars/second
        if not self.finished and self.char_index < len(self.text):
            self.char_index += max(1, int(60 * dt))
            if self.char_index >= len(self.text):
                self.char_index = len(self.text)
                self.finished = True

    def skip(self):
        self.char_index = len(self.text)
        self.finished = True

    def draw(self):
        pygame.draw.rect(self.screen, WHITE, self.box, 2)
        displayed = self.text[:self.char_index]
        lines = wrap_text(self.font, displayed, self.box.width - 20)[:3]
        y = self.box.y + 10
        for ln in lines:
            self.screen.blit(self.text_cache.render(ln, WHITE), (self.box.x + 10, y))
            y += 24

        if self.finished and self.choices:
            cy = self.box.y + 10
            for i, choice in enumerate(self.choices):
                col = YELLOW if i == self.selected_choice else GRAY
                prefix = ">" if i == self.selected_choice else " "
                self.screen.blit(self.text_cache.render(f"{prefix} {choice}", col), (self.box.right - 180, cy))
                cy += 24

# ---------- Bullet patterns ----------
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x: float, y: float, vx: float, vy: float):
        super().__init__()
        self.image = pygame.Surface((6, 6), pygame.SRCALPHA)
        pygame.draw.circle(self.image, WHITE, (3, 3), 3)
        self.rect = self.image.get_rect(center=(x, y))
        self.vx = vx
        self.vy = vy

    def update(self, dt: float):
        self.rect.x += int(self.vx * dt * 60)
        self.rect.y += int(self.vy * dt * 60)

        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH or self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT:
            self.kill()

# ---------- Battle System ----------
class BattleSystem:
    def __init__(self, screen, font, player: Player):
        self.screen = screen
        self.font = font
        self.player = player
        self.monster: Optional[Monster] = None

        self.turn_phase = "menu"  # menu, fight, act, item, mercy, monster_attack
        self.selected_action = 0
        self.selected_option = 0

        self.damage_dealt = 0
        self.damage_taken = 0
        self.victory = False
        self.ran_away = False
        self.battle_ended = False

        # Attack bar
        self.attack_bar_x = 0.0
        self.attack_dir = 1

        # Soul (heart) box
        self.soul_x = SCREEN_WIDTH // 2
        self.soul_y = SCREEN_HEIGHT - 80
        self.soul_rect = pygame.Rect(self.soul_x - 7, self.soul_y - 7, 14, 14)

        # Bullets
        self.bullets = pygame.sprite.Group()
        self.dodge_timer = 0.0

        self.text_cache = TextCache(font)

    # ---- Battle control
    def start_battle(self, monster_name: str):
        base = GameData.MONSTERS.get(monster_name)
        if not base:
            return
        self.monster = Monster(
            base.name, base.max_hp, base.max_hp, base.attack, base.defense,
            base.gold, base.exp, base.can_spare, base.betrayed,
            base.dialogue.copy(), base.acts.copy()
        )
        self.turn_phase = "menu"
        self.selected_action = 0
        self.selected_option = 0
        self.battle_ended = False
        self.victory = False
        self.ran_away = False
        self.attack_bar_x = 40
        self.attack_dir = 1
        self.bullets.empty()
        self.dodge_timer = 0.0

    def update(self, events: List[pygame.event.Event], dt: float):
        if self.turn_phase == "menu":
            self.handle_menu_input(events)
        elif self.turn_phase == "fight":
            self.update_attack_bar(dt, events)
        elif self.turn_phase == "act":
            self.handle_act_input(events)
        elif self.turn_phase == "item":
            self.handle_item_input(events)
        elif self.turn_phase == "mercy":
            self.handle_mercy_input(events)
        elif self.turn_phase == "monster_attack":
            self.update_monster_attack(dt)

    def handle_menu_input(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_LEFT, pygame.K_a):
                    self.selected_action = max(0, self.selected_action - 1)
                elif e.key in (pygame.K_RIGHT, pygame.K_d):
                    self.selected_action = min(3, self.selected_action + 1)
                elif e.key in (pygame.K_z, pygame.K_RETURN):
                    self.turn_phase = ["fight", "act", "item", "mercy"][self.selected_action]
                elif e.key in (pygame.K_x, pygame.K_ESCAPE):
                    self.ran_away = True
                    self.battle_ended = True

    def update_attack_bar(self, dt: float, events: List[pygame.event.Event]):
        # Attack lane
        lane_left, lane_right = 40, SCREEN_WIDTH - 40
        speed_px_s = 520  # fast bar; timing matters
        self.attack_bar_x += self.attack_dir * speed_px_s * dt
        if self.attack_bar_x <= lane_left:
            self.attack_bar_x, self.attack_dir = lane_left, 1
        elif self.attack_bar_x >= lane_right:
            self.attack_bar_x, self.attack_dir = lane_right, -1

        for e in events:
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_z, pygame.K_RETURN):
                # Timing window centered near middle
                center = (lane_left + lane_right) / 2
                dist = abs(self.attack_bar_x - center)
                max_dist = (lane_right - lane_left) / 2
                accuracy = max(0.1, 1.0 - (dist / max_dist))  # 0.1..1.0
                base = self.player.at * 2.2
                # Defense reduces more on bad timing
                defense = max(0, self.monster.defense * (0.6 + (1.0 - accuracy) * 0.8))
                self.damage_dealt = max(1, int(base * accuracy - defense * 0.25))
                self.monster.hp -= self.damage_dealt
                if self.monster.hp <= 0:
                    self.end_battle(victory=True)
                else:
                    self.turn_phase = "monster_attack"
                    self.start_monster_attack()
            elif e.type == pygame.KEYDOWN and e.key in (pygame.K_x, pygame.K_ESCAPE):
                self.turn_phase = "menu"

    def handle_act_input(self, events):
        acts = self.monster.acts
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_UP, pygame.K_w):
                    self.selected_option = (self.selected_option - 1) % len(acts)
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    self.selected_option = (self.selected_option + 1) % len(acts)
                elif e.key in (pygame.K_z, pygame.K_RETURN):
                    act = acts[self.selected_option]
                    self.perform_act(act)
                    self.turn_phase = "monster_attack"
                    self.start_monster_attack()
                elif e.key in (pygame.K_x, pygame.K_ESCAPE):
                    self.turn_phase = "menu"

    def perform_act(self, act_name: str):
        # Minimal flavor without copyrighted lines; basic flags that can unlock spare
        if act_name.lower() in ("pet", "laugh", "console", "dinner", "flirt", "plead", "don't pick on", "dont pick on"):
            self.monster.can_spare = True
        elif act_name.lower() == "spare" and self.monster.can_spare:
            self.end_battle(victory=False, spared=True)

    def handle_item_input(self, events):
        inv = self.player.inventory
        if not inv:
            self.turn_phase = "menu"
            return
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_UP, pygame.K_w):
                    self.selected_option = (self.selected_option - 1) % len(inv)
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    self.selected_option = (self.selected_option + 1) % len(inv)
                elif e.key in (pygame.K_z, pygame.K_RETURN):
                    item_name = inv[self.selected_option]
                    self.use_item(item_name)
                    self.turn_phase = "monster_attack"
                    self.start_monster_attack()
                elif e.key in (pygame.K_x, pygame.K_ESCAPE):
                    self.turn_phase = "menu"

    def use_item(self, item_name: str):
        it = GameData.ITEMS.get(item_name)
        if not it:
            return
        if it.type == "heal":
            healed = self.player.heal(it.heal_amount)
            # Optional: Burnt Pan style passive can modify healing; omitted asset-specific logic
            self.player.remove_item(item_name)

    def handle_mercy_input(self, events):
        # Options: Spare, Flee
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_UP, pygame.K_w, pygame.K_DOWN, pygame.K_s):
                    self.selected_option = 1 - getattr(self, "selected_option", 0)
                elif e.key in (pygame.K_z, pygame.K_RETURN):
                    if self.selected_option == 0:  # Spare
                        if self.monster.can_spare:
                            self.end_battle(victory=False, spared=True)
                        else:
                            self.turn_phase = "monster_attack"
                            self.start_monster_attack()
                    else:  # Flee
                        self.end_battle(victory=False, ran_away=True)
                elif e.key in (pygame.K_x, pygame.K_ESCAPE):
                    self.turn_phase = "menu"

    # ---- Monster attack phase
    def start_monster_attack(self):
        self.bullets.empty()
        self.dodge_timer = 2.6  # seconds
        # Pattern variety based on monster name (simple but gives flavor)
        name = (self.monster.name or "").lower()
        if "loox" in name:
            self.pattern_rain(speed=150, spread=7)
        elif "dog" in name:
            self.pattern_sine(speed=120, lanes=4)
        elif "froggit" in name:
            self.pattern_bursts(speed=160, count=3)
        elif "sans" in name:
            self.pattern_fast_wall(speed=280)
        else:
            # Default mixed light pattern
            self.pattern_rain(speed=140, spread=5)

    def pattern_rain(self, speed=140, spread=5):
        for _ in range(12 + spread * 2):
            x = random.randint(80, SCREEN_WIDTH - 80)
            vy = random.uniform(speed * 0.8, speed * 1.2)
            self.bullets.add(Bullet(x, 40, 0, vy / 60.0))

    def pattern_sine(self, speed=120, lanes=4):
        base_y = 60
        for i in range(lanes * 6):
            x = 80 + (i % lanes) * ((SCREEN_WIDTH - 160) // max(1, (lanes - 1)))
            phase = random.uniform(0, math.tau)
            vx = math.cos(phase) * 60
            self.bullets.add(Bullet(x, base_y, vx / 60.0, speed / 60.0))

    def pattern_bursts(self, speed=160, count=3):
        cx = SCREEN_WIDTH // 2
        cy = 80
        for _ in range(count):
            for k in range(10):
                ang = k * (math.tau / 10) + random.uniform(-0.1, 0.1)
                vx = math.cos(ang) * speed
                vy = math.sin(ang) * speed
                self.bullets.add(Bullet(cx, cy, vx / 60.0, (vy + 100) / 60.0))

    def pattern_fast_wall(self, speed=280):
        y = 60
        for i in range(10):
            x = 80 + i * ((SCREEN_WIDTH - 160) // 9)
            self.bullets.add(Bullet(x, y, 0, speed / 60.0))

    def update_monster_attack(self, dt: float):
        keys = pygame.key.get_pressed()
        move = 180  # px/s
        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])

        self.soul_rect.x += int(dx * move * dt)
        self.soul_rect.y += int(dy * move * dt)

        # Bound within battle box
        box = pygame.Rect(50, SCREEN_HEIGHT - 130, SCREEN_WIDTH - 100, 110)
        self.soul_rect.clamp_ip(box)

        self.bullets.update(dt)

        # Collision
        hit_list = [b for b in self.bullets if self.soul_rect.colliderect(b.rect)]
        if hit_list:
            dmg = self.player.take_damage(max(1, self.monster.attack // 2))
            self.damage_taken = dmg
            for b in hit_list:
                b.kill()

        self.dodge_timer -= dt
        if self.dodge_timer <= 0:
            if self.player.hp <= 0:
                self.end_battle(victory=False, died=True)
            else:
                self.turn_phase = "menu"

    def end_battle(self, victory: bool, spared: bool=False, ran_away: bool=False, died: bool=False):
        self.victory = victory
        self.ran_away = ran_away
        if victory:
            self.player.kills += 1
            if self.monster:
                self.player.gain_exp(self.monster.exp)
                self.player.gold += self.monster.gold
        elif spared:
            self.player.spared += 1
        self.battle_ended = True

    # ---- Draw
    def draw(self):
        self.screen.fill(BLACK)

        # Monster header
        if self.monster:
            self.screen.blit(self.text_cache.render(self.monster.name, WHITE), (24, 24))
            # Monster HP bar
            hp_ratio = max(0.0, self.monster.hp / max(1, self.monster.max_hp))
            pygame.draw.rect(self.screen, RED, (24, 44, int(200 * hp_ratio), 10))
            pygame.draw.rect(self.screen, WHITE, (24, 44, 200, 10), 2)
            self.screen.blit(self.text_cache.render(f"{self.monster.hp}/{self.monster.max_hp}", WHITE), (230, 38))

        # Battle box
        box = pygame.Rect(50, SCREEN_HEIGHT - 130, SCREEN_WIDTH - 100, 110)
        pygame.draw.rect(self.screen, WHITE, box, 2)

        if self.turn_phase == "menu":
            actions = ["FIGHT", "ACT", "ITEM", "MERCY"]
            for i, a in enumerate(actions):
                x = 90 + i * 120
                col = YELLOW if i == self.selected_action else WHITE
                self.screen.blit(self.text_cache.render(a, col), (x, SCREEN_HEIGHT - 18))

        elif self.turn_phase == "fight":
            # Attack bar
            lane_left, lane_right = 40, SCREEN_WIDTH - 40
            pygame.draw.rect(self.screen, WHITE, (lane_left, SCREEN_HEIGHT - 95, lane_right - lane_left, 12), 2)
            pygame.draw.rect(self.screen, RED, (int(self.attack_bar_x) - 6, SCREEN_HEIGHT - 97, 12, 16))

        elif self.turn_phase == "act":
            for i, act in enumerate(self.monster.acts):
                col = YELLOW if i == self.selected_option else WHITE
                self.screen.blit(self.text_cache.render(f"* {act}", col), (box.x + 12, box.y + 10 + i * 22))

        elif self.turn_phase == "item":
            for i, item in enumerate(self.player.inventory):
                col = YELLOW if i == self.selected_option else WHITE
                self.screen.blit(self.text_cache.render(f"* {item}", col), (box.x + 12, box.y + 10 + i * 22))

        elif self.turn_phase == "mercy":
            opts = ["Spare", "Flee"]
            for i, opt in enumerate(opts):
                col = YELLOW if (i == getattr(self, "selected_option", 0) or (opt == "Spare" and self.monster and self.monster.can_spare)) else WHITE
                self.screen.blit(self.text_cache.render(f"* {opt}", col), (box.x + 12, box.y + 10 + i * 22))

        elif self.turn_phase == "monster_attack":
            # Soul (heart)
            pygame.draw.rect(self.screen, RED, self.soul_rect)
            # Bullets
            self.bullets.draw(self.screen)

        # Player stats
        stats = f"{self.player.name}  LV {self.player.lv}  HP {max(0,self.player.hp)}/{self.player.max_hp}"
        self.screen.blit(self.text_cache.render(stats, WHITE), (box.x + 8, box.y - 18))

# ---------- Fun Values ----------
class FunValues:
    @staticmethod
    def get_fun_value() -> int:
        return random.randint(1, 100)

    @staticmethod
    def check_fun_event(fun_value: int, area: Area) -> Optional[str]:
        events = {
            (66, Area.WATERFALL): "mystery_door",
            (65, Area.WATERFALL): "follower_1",
            (80, Area.WATERFALL): "wrong_number_song",
            (85, Area.SNOWDIN): "glyde_encounter",
            (50, Area.SNOWDIN): "sans_key",
        }
        return events.get((fun_value, area))

# ---------- Save System (optional) ----------
class SaveSystem:
    @staticmethod
    def _save_path() -> str:
        if sys.platform.startswith("win"):
            base = os.getenv("APPDATA", os.path.expanduser("~"))
        else:
            base = os.path.expanduser("~")
        return os.path.join(base, "undertale_pydecomp_save.json")

    @staticmethod
    def save_game(player: Player, game_state: GameState):
        if not SAVE_ENABLED:
            return False
        data = {
            'name': player.name,
            'lv': player.lv,
            'hp': player.hp,
            'max_hp': player.max_hp,
            'at': player.at,
            'df': player.df,
            'exp': player.exp,
            'gold': player.gold,
            'weapon': player.weapon,
            'armor': player.armor,
            'inventory': player.inventory,
            'kills': player.kills,
            'area_kills': {k.name: v for k, v in player.area_kills.items()},
            'spared': player.spared,
            'betrayals': player.betrayals,
            'friends': player.friends,
            'flags': player.flags,
            'x': player.x, 'y': player.y, 'facing': player.facing,
            'state': game_state.name
        }
        with open(SaveSystem._save_path(), 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True

    @staticmethod
    def load_game() -> Optional[Tuple[Player, GameState]]:
        if not SAVE_ENABLED:
            return None
        path = SaveSystem._save_path()
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        p = Player()
        p.name = data['name']
        p.lv = data['lv']
        p.hp = data['hp']
        p.max_hp = data['max_hp']
        p.at = data['at']
        p.df = data['df']
        p.exp = data['exp']
        p.gold = data['gold']
        p.weapon = data['weapon']
        p.armor = data['armor']
        p.inventory = data['inventory']
        p.kills = data['kills']
        p.area_kills = {Area[k]: v for k, v in data['area_kills'].items()}
        p.spared = data['spared']
        p.betrayals = data['betrayals']
        p.friends = data['friends']
        p.flags = data['flags']
        p.x = data['x']
        p.y = data['y']
        p.facing = data['facing']
        state = GameState[data['state']]
        return p, state

# ---------- Route Detector ----------
class RouteDetector:
    @staticmethod
    def get_route(player: Player) -> RouteType:
        ruins_q, snow_q, water_q, hot_q = 20, 16, 18, 40
        if (player.area_kills.get(Area.RUINS, 0) >= ruins_q and
            player.area_kills.get(Area.SNOWDIN, 0) >= snow_q and
            player.area_kills.get(Area.WATERFALL, 0) >= water_q and
            player.area_kills.get(Area.HOTLAND, 0) >= hot_q):
            return RouteType.GENOCIDE
        if player.kills == 0:
            if player.spared >= 10:
                if player.flags.get('dated_papyrus') and player.flags.get('befriended_undyne'):
                    return RouteType.TRUE_PACIFIST
                return RouteType.PACIFIST
        return RouteType.NEUTRAL

# ---------- Main Game ----------
class UndertaleGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("UNDERTALEPYDECOMP4K — 600x400/60FPS")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 48)

        self.running = True
        self.state = GameState.MENU
        self.player = Player()
        self.current_area = Area.RUINS
        self.fun_value = FunValues.get_fun_value()

        self.dialogue = DialogueSystem(self.screen, self.font)
        self.battle = BattleSystem(self.screen, self.font, self.player)

        self.menu_selection = 0
        self.menu_options = ["Continue", "New Game", "Settings", "Quit"]

        self.show_debug = False
        self.text_cache = TextCache(self.font)

    def run(self):
        while self.running:
            dt = self.clock.tick_busy_loop(FPS) / 1000.0  # Stable 60 FPS feel
            events = pygame.event.get()
            for e in events:
                if e.type == pygame.QUIT:
                    self.running = False
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_F3:
                    self.show_debug = not self.show_debug

            self.update(events, dt)
            self.draw()
            pygame.display.flip()

        pygame.quit()

    # ---- Update states
    def update(self, events, dt: float):
        if self.state == GameState.MENU:
            self.update_menu(events)
        elif self.state == GameState.OVERWORLD:
            self.update_overworld(events, dt)
        elif self.state == GameState.BATTLE:
            self.battle.update(events, dt)
            if self.battle.battle_ended:
                self.state = GameState.OVERWORLD if self.player.hp > 0 else GameState.GAME_OVER
        elif self.state == GameState.DIALOGUE:
            self.dialogue.update(dt)
            self.update_dialogue(events)
        elif self.state == GameState.SAVE:
            self.update_save(events)

    def update_menu(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_UP, pygame.K_w):
                    self.menu_selection = (self.menu_selection - 1) % len(self.menu_options)
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    self.menu_selection = (self.menu_selection + 1) % len(self.menu_options)
                elif e.key in (pygame.K_z, pygame.K_RETURN):
                    if self.menu_selection == 0:  # Continue
                        loaded = SaveSystem.load_game()
                        if loaded:
                            self.player, state = loaded
                            self.state = GameState.OVERWORLD if isinstance(state, GameState) else GameState.OVERWORLD
                        else:
                            # No save or saves disabled
                            self.state = GameState.OVERWORLD
                    elif self.menu_selection == 1:  # New Game
                        self.player = Player()
                        self.state = GameState.DIALOGUE
                        self.dialogue.start_dialogue(
                            "Once upon a time, two races ruled over Earth: HUMANS and MONSTERS..."
                        )
                        self.fun_value = FunValues.get_fun_value()
                    elif self.menu_selection == 2:  # Settings (stub)
                        # Toggle saves quickly as a demo
                        global SAVE_ENABLED
                        SAVE_ENABLED = not SAVE_ENABLED
                    elif self.menu_selection == 3:  # Quit
                        self.running = False

    def update_overworld(self, events, dt: float):
        # Simple centered player with world coords updated (feel).
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_c:
                    self.state = GameState.SAVE
                elif e.key == pygame.K_b:
                    # Test battle with random monster
                    name = random.choice(list(GameData.MONSTERS.keys()))
                    self.battle.start_battle(name)
                    self.state = GameState.BATTLE
                elif e.key == pygame.K_f:
                    ev = FunValues.check_fun_event(self.fun_value, self.current_area)
                    if ev:
                        self.handle_fun_event(ev)

        # Smooth movement (held keys)
        keys = pygame.key.get_pressed()
        speed = 120  # world px/s
        self.player.x += int((keys[pygame.K_RIGHT] or keys[pygame.K_d]) * speed * dt)
        self.player.x -= int((keys[pygame.K_LEFT]  or keys[pygame.K_a]) * speed * dt)
        self.player.y += int((keys[pygame.K_DOWN]  or keys[pygame.K_s]) * speed * dt)
        self.player.y -= int((keys[pygame.K_UP]    or keys[pygame.K_w]) * speed * dt)

    def update_dialogue(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_z, pygame.K_RETURN):
                    if self.dialogue.finished:
                        self.state = GameState.OVERWORLD
                    else:
                        self.dialogue.skip()
                elif e.key in (pygame.K_x, pygame.K_ESCAPE):
                    self.state = GameState.OVERWORLD

    def update_save(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_z, pygame.K_RETURN):
                    saved = SaveSystem.save_game(self.player, self.state)
                    self.state = GameState.OVERWORLD
                elif e.key in (pygame.K_x, pygame.K_ESCAPE):
                    self.state = GameState.OVERWORLD

    def handle_fun_event(self, event_name: str):
        dialog = {
            "mystery_door": "* A very old door. It won't budge.",
            "follower_1": "* The figure vanishes before you can speak.",
            "wrong_number_song": "* ... ring, ring ... (nothing answers)",
            "sans_key": "* You found a small key. Where does it go?",
        }
        if event_name == "glyde_encounter":
            self.battle.start_battle("Doggo")  # placeholder encounter for a rare event
            self.state = GameState.BATTLE
        elif event_name in dialog:
            self.dialogue.start_dialogue(dialog[event_name])
            self.state = GameState.DIALOGUE

    # ---- Draw states
    def draw(self):
        self.screen.fill(BLACK)
        if self.state == GameState.MENU:
            self.draw_menu()
        elif self.state == GameState.OVERWORLD:
            self.draw_overworld()
        elif self.state == GameState.BATTLE:
            self.battle.draw()
        elif self.state == GameState.DIALOGUE:
            self.draw_overworld()
            self.dialogue.draw()
        elif self.state == GameState.SAVE:
            self.draw_save_menu()

        if self.show_debug:
            self.draw_debug()

    def draw_menu(self):
        title = self.title_font.render("UNDERTALE", True, WHITE)
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 90)))
        subtitle = self.font.render("PYDECOMP — 600x400 @ 60 FPS", True, GRAY)
        self.screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_WIDTH // 2, 130)))
        for i, opt in enumerate(self.menu_options):
            col = YELLOW if i == self.menu_selection else WHITE
            txt = self.font.render(opt, True, col)
            self.screen.blit(txt, txt.get_rect(center=(SCREEN_WIDTH // 2, 210 + i * 36)))

    def draw_overworld(self):
        # Area label
        self.screen.blit(self.text_cache.render(self.current_area.name, WHITE), (16, 12))
        # Player: centered 16x16 "heart-box-style square"
        pygame.draw.rect(self.screen, RED, (SCREEN_WIDTH//2 - 8, SCREEN_HEIGHT//2 - 8, 16, 16))
        # Movement hint
        hint = "Move: Arrow/WASD | C: Save | B: Battle | F: Fun | F3: Debug"
        self.screen.blit(self.text_cache.render(hint, GRAY), (16, SCREEN_HEIGHT - 20))

    def draw_save_menu(self):
        # Simple star polygon
        cx, cy = SCREEN_WIDTH // 2, 120
        points = [
            (cx, cy-26), (cx+10, cy-4), (cx+32, cy-4), (cx+13, cy+8),
            (cx+20, cy+30), (cx, cy+16), (cx-20, cy+30), (cx-13, cy+8),
            (cx-32, cy-4), (cx-10, cy-4),
        ]
        pygame.draw.polygon(self.screen, YELLOW, points)
        self.screen.blit(self.text_cache.render(f"{self.player.name}  LV {self.player.lv}", WHITE),
                         (cx-60, cy+48))
        self.screen.blit(self.text_cache.render(self.current_area.name, WHITE), (cx-40, cy+70))
        self.screen.blit(self.text_cache.render("Save?  [Z] Yes   [X] No", WHITE),
                         (cx-90, cy+102))

    def draw_debug(self):
        dbg = [
            f"FPS: {int(self.clock.get_fps())}",
            f"State: {self.state.name}",
            f"Route: {RouteDetector.get_route(self.player).name}",
            f"Fun: {self.fun_value}",
            f"LV: {self.player.lv}  HP: {self.player.hp}/{self.player.max_hp}",
            f"Kills: {self.player.kills}  Spared: {self.player.spared}",
            f"Pos: ({self.player.x}, {self.player.y})",
        ]
        y = 8
        for line in dbg:
            self.screen.blit(self.text_cache.render(line, GREEN), (SCREEN_WIDTH - 220, y))
            y += 16

# ---------- Entry point ----------
def main():
    print("=" * 48)
    print(" UNDERTALEPYDECOMP4K — 600x400 / 60 FPS (Windows‑friendly) ")
    print("=" * 48)
    print("Controls:")
    print("  Arrow/WASD: Move | Z/Enter: Confirm | X/Esc: Back")
    print("  C: Save | B: Test Battle | F: Fun Event | F3: Debug")
    print()
    game = UndertaleGame()
    game.run()

if __name__ == "__main__":
    main()

# ---------------- Packaging (Windows) ----------------
# 1) Install Python 3.10+ and pip install pygame pyinstaller
# 2) From a terminal in this folder:
#       pyinstaller --onefile --windowed program.py
#    The EXE will be in the dist/ folder.
