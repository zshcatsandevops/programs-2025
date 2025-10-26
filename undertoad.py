"""
UNDERTOAD: MISSION LUIGI 1.0
An Undertale-style RPG engine in the Mario universe
Help Toad save Luigi from the Mushroom Kingdom's darkest threats!
"""

import pygame
import sys
import math
import random

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("UNDERTOAD: Mission Luigi")

# Colors
BACKGROUND = (135, 206, 235)  # Sky blue
GROUND = (139, 69, 19)  # Brown
GRASS = (34, 139, 34)  # Green
BRICK = (178, 34, 34)  # Brick red
PIPE_GREEN = (0, 128, 0)
MUSHROOM_RED = (220, 20, 60)
MUSHROOM_WHITE = (255, 240, 245)
GOOMBA_BROWN = (139, 90, 43)
KOOPA_GREEN = (50, 205, 50)
SHELL_RED = (255, 69, 0)
BOWSER_GREEN = (85, 107, 47)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 60, 60)
YELLOW = (255, 220, 60)
BLUE = (80, 120, 220)
GREEN = (60, 220, 80)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
ORANGE = (255, 140, 0)
PURPLE = (147, 112, 219)

# Game clock
clock = pygame.time.Clock()
FPS = 60

# ===== PLAYER STATS =====
player_stats = {
    "name": "Toad",
    "hp": 25,
    "max_hp": 25,
    "atk": 8,
    "def": 12,
    "gold": 0,
    "exp": 0,
    "lv": 1,
    "items": ["Mushroom", "Super Star"]
}

# ===== OVERWORLD STATE =====
player_x = WIDTH // 2
player_y = HEIGHT // 2
player_speed = 2.5
player_size = 32
animation_counter = 0
facing_right = True

# NPC/Enemy properties - All Mario characters now!
npcs = [
    {
        "x": 120, "y": 200, "color": GOOMBA_BROWN, "name": "Wild Goomba",
        "dialog": "Mmmph! I'm just trying to get by!",
        "visible": True,
        "enemy_data": {
            "hp": 40, "max_hp": 40, "atk": 6, "def": 4,
            "acts": ["Check", "Stomp", "Intimidate", "Dance"],
            "spare_threshold": 20,
            "attack_pattern": "goombas",
            "gold": 10,
            "exp": 15
        }
    },
    {
        "x": 480, "y": 180, "color": KOOPA_GREEN, "name": "Koopa Troopa",
        "dialog": "Mama mia! You're not Mario!",
        "visible": True,
        "enemy_data": {
            "hp": 55, "max_hp": 55, "atk": 8, "def": 10,
            "acts": ["Check", "Shell Kick", "Befriend", "Race"],
            "spare_threshold": 25,
            "attack_pattern": "shells",
            "gold": 15,
            "exp": 20
        }
    },
    {
        "x": 320, "y": 320, "color": BOWSER_GREEN, "name": "BOWSER",
        "dialog": "GWAHAHAHA! Luigi is MINE!",
        "visible": True,
        "enemy_data": {
            "hp": 80, "max_hp": 80, "atk": 15, "def": 8,
            "acts": ["Check", "Reason", "Dodge Fire", "Call Mario"],
            "spare_threshold": 30,
            "attack_pattern": "bowser",
            "gold": 50,
            "exp": 100
        }
    }
]

# Friendly NPCs (non-combat)
friendly_npcs = [
    {"x": 200, "y": 120, "color": RED, "name": "Mario", "dialog": "Mama mia! Please-a help find Luigi!", "visible": True},
    {"x": 450, "y": 300, "color": PURPLE, "name": "Princess Peach", "dialog": "Thank you Toad! Save Luigi!", "visible": True}
]

# ===== BATTLE STATE =====
battle_state = {
    "active": False,
    "enemy": None,
    "phase": "menu",  # "menu", "fight", "act", "item", "mercy", "enemy_turn", "dodge"
    "menu_selection": 0,
    "act_selection": 0,
    "item_selection": 0,
    "can_spare": False,
    "turn_count": 0,
    "soul_x": WIDTH // 2,
    "soul_y": HEIGHT // 2,
    "attacks": [],
    "damage_flash": 0,
    "dialog_text": "",
    "dialog_progress": 0,
    "dialog_timer": 0,
    "fight_bar_pos": 0,
    "fight_bar_direction": 1
}

# ===== GAME STATE =====
game_state = "exploring"  # "exploring", "dialog", "battle"
current_npc = None
current_friendly_npc = None
dialog_timer = 0
dialog_progress = 0

# Fonts
font = pygame.font.SysFont("Arial", 16)
dialog_font = pygame.font.SysFont("Arial", 14)
battle_font = pygame.font.SysFont("Arial", 18, bold=True)
small_font = pygame.font.SysFont("Arial", 12)
title_font = pygame.font.SysFont("Arial", 24, bold=True)

# ===== ATTACK PATTERNS =====
class Attack:
    def __init__(self, x, y, vx, vy, width, height, color=WHITE, shape="rect"):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.width = width
        self.height = height
        self.color = color
        self.active = True
        self.shape = shape  # "rect" or "circle"

    def update(self):
        self.x += self.vx
        self.y += self.vy

        # Remove if out of bounds
        if (self.x < -50 or self.x > WIDTH + 50 or
            self.y < -50 or self.y > HEIGHT + 50):
            self.active = False

    def draw(self):
        if self.shape == "circle":
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.width)
        else:
            pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))

    def collides_with_soul(self, soul_x, soul_y, soul_size=8):
        if self.shape == "circle":
            dist = math.sqrt((self.x - soul_x) ** 2 + (self.y - soul_y) ** 2)
            return dist < (self.width + soul_size)
        else:
            return (self.x < soul_x + soul_size and
                    self.x + self.width > soul_x and
                    self.y < soul_y + soul_size and
                    self.y + self.height > soul_y)

def create_attack_pattern(pattern_type):
    """Generate attacks based on enemy pattern"""
    attacks = []

    if pattern_type == "goombas":
        # Marching goombas from both sides
        for i in range(6):
            side = random.choice([-1, 1])
            start_x = -30 if side == 1 else WIDTH + 30
            attacks.append(Attack(
                start_x,
                random.randint(280, 400),
                3 * side,
                0,
                24, 24, GOOMBA_BROWN, "rect"
            ))

    elif pattern_type == "shells":
        # Koopa shell spin attacks
        for i in range(4):
            # Shells bounce across the screen
            attacks.append(Attack(
                random.choice([0, WIDTH]),
                random.randint(280, 400),
                random.choice([-5, 5]),
                0,
                28, 28, SHELL_RED, "circle"
            ))

        # Some vertical shells
        for i in range(3):
            attacks.append(Attack(
                random.randint(100, WIDTH - 100),
                -30,
                0,
                4,
                28, 28, KOOPA_GREEN, "circle"
            ))

    elif pattern_type == "bowser":
        # Bowser's fire breath and hammers
        # Fire breath (horizontal waves)
        for i in range(5):
            attacks.append(Attack(
                -30,
                random.randint(270, 420),
                random.uniform(4, 6),
                random.uniform(-1, 1),
                40, 20, ORANGE, "rect"
            ))

        # Falling hammers
        for i in range(6):
            attacks.append(Attack(
                random.randint(80, WIDTH - 80),
                -30,
                0,
                random.uniform(3, 5),
                16, 20, GRAY, "rect"
            ))

        # Fireballs
        for i in range(3):
            angle = random.uniform(-math.pi/4, math.pi/4)
            speed = 5
            attacks.append(Attack(
                WIDTH + 30,
                random.randint(300, 400),
                math.cos(angle + math.pi) * speed,
                math.sin(angle) * speed,
                20, 0, RED, "circle"
            ))

    return attacks

# ===== DRAWING FUNCTIONS =====
def draw_background():
    """Draw Mario-style overworld background"""
    # Sky
    screen.fill(BACKGROUND)

    # Ground layers
    pygame.draw.rect(screen, GRASS, (0, HEIGHT - 120, WIDTH, 40))
    pygame.draw.rect(screen, GROUND, (0, HEIGHT - 80, WIDTH, 80))

    # Question blocks
    for x in [100, 250, 400, 550]:
        draw_question_block(x, HEIGHT - 200)

    # Pipes
    draw_pipe(50, HEIGHT - 140, 50, 60)
    draw_pipe(500, HEIGHT - 140, 50, 60)

    # Bushes
    for x in [150, 350, 450]:
        draw_bush(x, HEIGHT - 95)

    # Clouds
    for x, y in [(100, 60), (400, 80), (550, 50)]:
        draw_cloud(x, y)

def draw_question_block(x, y):
    """Draw a Mario question block"""
    pygame.draw.rect(screen, YELLOW, (x, y, 30, 30))
    pygame.draw.rect(screen, ORANGE, (x, y, 30, 30), 3)
    # Question mark
    font = pygame.font.SysFont("Arial", 20, bold=True)
    q_mark = font.render("?", True, WHITE)
    screen.blit(q_mark, (x + 8, y + 3))

def draw_pipe(x, y, width, height):
    """Draw a Mario pipe"""
    # Pipe body
    pygame.draw.rect(screen, PIPE_GREEN, (x, y, width, height))
    pygame.draw.rect(screen, (0, 100, 0), (x, y, width, height), 3)
    # Pipe top
    pygame.draw.ellipse(screen, PIPE_GREEN, (x - 5, y - 10, width + 10, 20))
    pygame.draw.ellipse(screen, (0, 100, 0), (x - 5, y - 10, width + 10, 20), 3)

def draw_bush(x, y):
    """Draw a Mario bush"""
    pygame.draw.circle(screen, (34, 139, 34), (x, y), 15)
    pygame.draw.circle(screen, (34, 139, 34), (x + 15, y), 12)
    pygame.draw.circle(screen, (34, 139, 34), (x - 15, y), 12)

def draw_cloud(x, y):
    """Draw a Mario cloud"""
    pygame.draw.circle(screen, WHITE, (x, y), 20)
    pygame.draw.circle(screen, WHITE, (x + 20, y), 18)
    pygame.draw.circle(screen, WHITE, (x + 35, y), 20)
    pygame.draw.circle(screen, WHITE, (x + 17, y - 12), 15)

def draw_toad(x, y, frame, facing_right):
    """Draw Toad character (player)"""
    # Body (white vest)
    pygame.draw.ellipse(screen, MUSHROOM_WHITE, (x - 12, y, 24, 30))

    # Mushroom cap (red with white spots)
    pygame.draw.ellipse(screen, MUSHROOM_RED, (x - 16, y - 18, 32, 28))

    # White spots on cap
    spot_positions = [(x - 8, y - 15), (x + 5, y - 12), (x - 2, y - 8)]
    for spot_x, spot_y in spot_positions:
        pygame.draw.circle(screen, WHITE, (spot_x, spot_y), 4)

    # Face
    pygame.draw.circle(screen, MUSHROOM_WHITE, (x, y + 5), 10)

    # Eyes
    eye_offset = 3 if facing_right else -3
    pygame.draw.circle(screen, BLACK, (x - 3 + eye_offset, y + 3), 2)
    pygame.draw.circle(screen, BLACK, (x + 3 + eye_offset, y + 3), 2)

    # Mouth
    pygame.draw.arc(screen, BLACK, (x - 4, y + 6, 8, 5), 0, math.pi, 2)

    # Arms and legs (animate)
    offset = 2 if frame < 15 else -2
    pygame.draw.circle(screen, MUSHROOM_WHITE, (x - 14, y + 15), 5)  # Left arm
    pygame.draw.circle(screen, MUSHROOM_WHITE, (x + 14, y + 15), 5)  # Right arm
    pygame.draw.ellipse(screen, MUSHROOM_RED, (x - 10, y + 25, 8, 10))  # Left leg
    pygame.draw.ellipse(screen, MUSHROOM_RED, (x + 2 + offset, y + 25, 8, 10))  # Right leg

def draw_npcs():
    """Draw all enemy NPCs in overworld"""
    for npc in npcs:
        if npc["visible"]:
            if "Goomba" in npc["name"]:
                draw_goomba_npc(npc["x"], npc["y"])
            elif "Koopa" in npc["name"]:
                draw_koopa_npc(npc["x"], npc["y"])
            elif "BOWSER" in npc["name"]:
                draw_bowser_npc(npc["x"], npc["y"])

            # Name label
            name_text = small_font.render(npc["name"], True, WHITE)
            name_bg = pygame.Surface((name_text.get_width() + 10, name_text.get_height() + 4))
            name_bg.fill(BLACK)
            name_bg.set_alpha(180)
            screen.blit(name_bg, (npc["x"] - name_text.get_width() // 2 - 5, npc["y"] - 45))
            screen.blit(name_text, (npc["x"] - name_text.get_width() // 2, npc["y"] - 43))

def draw_friendly_npcs():
    """Draw friendly NPCs"""
    for npc in friendly_npcs:
        if npc["visible"]:
            if "Mario" in npc["name"]:
                draw_mario_npc(npc["x"], npc["y"])
            elif "Peach" in npc["name"]:
                draw_peach_npc(npc["x"], npc["y"])

            # Name label
            name_text = small_font.render(npc["name"], True, YELLOW)
            name_bg = pygame.Surface((name_text.get_width() + 10, name_text.get_height() + 4))
            name_bg.fill(BLACK)
            name_bg.set_alpha(180)
            screen.blit(name_bg, (npc["x"] - name_text.get_width() // 2 - 5, npc["y"] - 45))
            screen.blit(name_text, (npc["x"] - name_text.get_width() // 2, npc["y"] - 43))

def draw_goomba_npc(x, y):
    """Draw Goomba enemy"""
    pygame.draw.ellipse(screen, GOOMBA_BROWN, (x - 15, y - 10, 30, 35))
    # Eyes
    pygame.draw.circle(screen, WHITE, (x - 6, y), 5)
    pygame.draw.circle(screen, WHITE, (x + 6, y), 5)
    pygame.draw.circle(screen, BLACK, (x - 6, y), 3)
    pygame.draw.circle(screen, BLACK, (x + 6, y), 3)
    # Angry eyebrows
    pygame.draw.line(screen, BLACK, (x - 10, y - 5), (x - 2, y - 3), 2)
    pygame.draw.line(screen, BLACK, (x + 2, y - 3), (x + 10, y - 5), 2)
    # Feet
    pygame.draw.ellipse(screen, (101, 67, 33), (x - 18, y + 18, 14, 8))
    pygame.draw.ellipse(screen, (101, 67, 33), (x + 4, y + 18, 14, 8))

def draw_koopa_npc(x, y):
    """Draw Koopa Troopa"""
    # Shell
    pygame.draw.ellipse(screen, KOOPA_GREEN, (x - 18, y - 5, 36, 30))
    pygame.draw.ellipse(screen, YELLOW, (x - 13, y, 26, 20))
    # Head
    pygame.draw.circle(screen, YELLOW, (x, y - 15), 10)
    # Eyes
    pygame.draw.circle(screen, WHITE, (x - 4, y - 16), 3)
    pygame.draw.circle(screen, WHITE, (x + 4, y - 16), 3)
    pygame.draw.circle(screen, BLACK, (x - 4, y - 16), 2)
    pygame.draw.circle(screen, BLACK, (x + 4, y - 16), 2)
    # Snout
    pygame.draw.circle(screen, (255, 228, 181), (x, y - 10), 5)

def draw_bowser_npc(x, y):
    """Draw Bowser"""
    # Body
    pygame.draw.ellipse(screen, BOWSER_GREEN, (x - 20, y - 10, 40, 40))
    # Shell spikes
    for spike_x in range(x - 15, x + 16, 10):
        pygame.draw.polygon(screen, ORANGE, [
            (spike_x, y + 10),
            (spike_x - 5, y + 20),
            (spike_x + 5, y + 20)
        ])
    # Head
    pygame.draw.ellipse(screen, BOWSER_GREEN, (x - 15, y - 25, 30, 25))
    # Eyes (angry)
    pygame.draw.ellipse(screen, WHITE, (x - 10, y - 22, 8, 6))
    pygame.draw.ellipse(screen, WHITE, (x + 2, y - 22, 8, 6))
    pygame.draw.circle(screen, RED, (x - 6, y - 19), 3)
    pygame.draw.circle(screen, RED, (x + 6, y - 19), 3)
    # Horns
    pygame.draw.polygon(screen, ORANGE, [(x - 15, y - 20), (x - 20, y - 25), (x - 13, y - 25)])
    pygame.draw.polygon(screen, ORANGE, [(x + 15, y - 20), (x + 20, y - 25), (x + 13, y - 25)])

def draw_mario_npc(x, y):
    """Draw Mario"""
    # Overalls
    pygame.draw.rect(screen, BLUE, (x - 10, y, 20, 25))
    # Face
    pygame.draw.circle(screen, (255, 220, 177), (x, y + 5), 12)
    # Cap
    pygame.draw.ellipse(screen, RED, (x - 14, y - 15, 28, 18))
    # M logo
    m_text = small_font.render("M", True, WHITE)
    screen.blit(m_text, (x - 4, y - 13))
    # Mustache
    pygame.draw.ellipse(screen, BLACK, (x - 8, y + 8, 16, 6))
    # Eyes
    pygame.draw.circle(screen, BLACK, (x - 4, y + 2), 2)
    pygame.draw.circle(screen, BLACK, (x + 4, y + 2), 2)

def draw_peach_npc(x, y):
    """Draw Princess Peach"""
    # Dress
    pygame.draw.polygon(screen, (255, 192, 203), [
        (x, y),
        (x - 18, y + 30),
        (x + 18, y + 30)
    ])
    # Face
    pygame.draw.circle(screen, (255, 220, 177), (x, y), 12)
    # Crown
    pygame.draw.polygon(screen, YELLOW, [
        (x - 10, y - 10),
        (x, y - 18),
        (x + 10, y - 10)
    ])
    # Jewel
    pygame.draw.circle(screen, RED, (x, y - 13), 3)
    # Hair
    pygame.draw.circle(screen, (255, 215, 0), (x - 10, y - 5), 6)
    pygame.draw.circle(screen, (255, 215, 0), (x + 10, y - 5), 6)
    # Eyes
    pygame.draw.circle(screen, BLUE, (x - 4, y - 2), 2)
    pygame.draw.circle(screen, BLUE, (x + 4, y - 2), 2)

def draw_dialog_box(text, speaker_name=""):
    """Draw dialog box with typewriter effect"""
    box_rect = pygame.Rect(50, HEIGHT - 120, WIDTH - 100, 100)
    pygame.draw.rect(screen, BLACK, box_rect)
    pygame.draw.rect(screen, WHITE, box_rect, 3)

    if speaker_name:
        name_text = battle_font.render(speaker_name, True, YELLOW)
        screen.blit(name_text, (70, HEIGHT - 110))

    # Typewriter effect
    displayed_text = text[:dialog_progress]

    # Word wrap for long text
    words = displayed_text.split(' ')
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + word + " "
        if dialog_font.size(test_line)[0] < WIDTH - 140:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word + " "
    lines.append(current_line)

    # Draw lines
    for i, line in enumerate(lines[:3]):  # Max 3 lines
        dialog_text = dialog_font.render(line, True, WHITE)
        screen.blit(dialog_text, (70, HEIGHT - 80 + i * 20))

    if dialog_progress >= len(text):
        prompt = small_font.render("[SPACE] Continue", True, GRAY)
        screen.blit(prompt, (WIDTH - 170, HEIGHT - 30))

def draw_battle_ui():
    """Draw battle interface"""
    screen.fill(BLACK)

    # Enemy display
    enemy = battle_state["enemy"]

    # Draw enemy sprite (larger in battle)
    if "Goomba" in enemy["name"]:
        draw_goomba_npc(WIDTH // 2, 120)
    elif "Koopa" in enemy["name"]:
        draw_koopa_npc(WIDTH // 2, 120)
    elif "BOWSER" in enemy["name"]:
        draw_bowser_npc(WIDTH // 2, 120)

    # Enemy name
    enemy_name = title_font.render(enemy["name"], True, WHITE)
    screen.blit(enemy_name, (WIDTH // 2 - enemy_name.get_width() // 2, 30))

    # HP bar
    hp_percent = enemy["enemy_data"]["hp"] / enemy["enemy_data"]["max_hp"]
    bar_width = 250
    bar_x = WIDTH // 2 - bar_width // 2
    pygame.draw.rect(screen, DARK_GRAY, (bar_x, 70, bar_width, 24))
    pygame.draw.rect(screen, GREEN, (bar_x, 70, bar_width * hp_percent, 24))
    pygame.draw.rect(screen, WHITE, (bar_x, 70, bar_width, 24), 3)

    hp_text = font.render(
        f"HP: {enemy['enemy_data']['hp']}/{enemy['enemy_data']['max_hp']}",
        True, WHITE
    )
    screen.blit(hp_text, (bar_x + bar_width + 10, 73))

    # Battle box
    battle_box = pygame.Rect(50, 250, WIDTH - 100, 180)
    pygame.draw.rect(screen, BLACK, battle_box)
    pygame.draw.rect(screen, WHITE, battle_box, 4)

    if battle_state["phase"] == "menu":
        draw_battle_menu()
    elif battle_state["phase"] == "act":
        draw_act_menu()
    elif battle_state["phase"] == "item":
        draw_item_menu()
    elif battle_state["phase"] == "dodge":
        draw_dodge_phase()
    elif battle_state["phase"] == "enemy_turn":
        draw_enemy_dialog()
    elif battle_state["phase"] == "fight":
        draw_fight_minigame()

    # Player stats
    draw_player_stats()

def draw_battle_menu():
    """Draw main battle menu"""
    menu_items = ["FIGHT", "ACT", "ITEM", "MERCY"]
    menu_x = 120
    menu_y = 350
    spacing = 140

    for i, item in enumerate(menu_items):
        color = YELLOW if i == battle_state["menu_selection"] else WHITE
        text = battle_font.render(item, True, color)
        x = menu_x + (i % 2) * spacing
        y = menu_y + (i // 2) * 50

        if i == battle_state["menu_selection"]:
            # Draw mushroom cursor
            pygame.draw.circle(screen, MUSHROOM_RED, (x - 25, y + 10), 8)
            pygame.draw.circle(screen, WHITE, (x - 29, y + 7), 3)
            pygame.draw.circle(screen, WHITE, (x - 21, y + 7), 3)

        screen.blit(text, (x, y))

def draw_fight_minigame():
    """Draw FIGHT timing minigame"""
    box_rect = pygame.Rect(150, 300, 340, 60)
    pygame.draw.rect(screen, DARK_GRAY, box_rect)
    pygame.draw.rect(screen, WHITE, box_rect, 3)

    # Target zone (center)
    target_rect = pygame.Rect(300, 305, 40, 50)
    pygame.draw.rect(screen, GREEN, target_rect)

    # Moving bar
    bar_x = 160 + battle_state["fight_bar_pos"]
    pygame.draw.rect(screen, RED, (bar_x, 310, 10, 40))

    instruction = small_font.render("Press SPACE when the bar is in the GREEN zone!", True, WHITE)
    screen.blit(instruction, (WIDTH // 2 - instruction.get_width() // 2, 270))

def draw_act_menu():
    """Draw ACT options menu"""
    acts = battle_state["enemy"]["enemy_data"]["acts"]

    title = battle_font.render("* ACT", True, YELLOW)
    screen.blit(title, (80, 270))

    for i, act in enumerate(acts):
        color = YELLOW if i == battle_state["act_selection"] else WHITE
        text = font.render(f"* {act}", True, color)
        y = 305 + i * 28

        if i == battle_state["act_selection"]:
            pygame.draw.circle(screen, MUSHROOM_RED, (70, y + 8), 6)

        screen.blit(text, (90, y))

    back_text = small_font.render("[ESC] Back", True, GRAY)
    screen.blit(back_text, (WIDTH - 150, HEIGHT - 30))

def draw_item_menu():
    """Draw ITEM menu"""
    title = battle_font.render("* ITEMS", True, YELLOW)
    screen.blit(title, (80, 270))

    items = player_stats["items"]
    for i, item in enumerate(items):
        color = YELLOW if i == battle_state["item_selection"] else WHITE
        text = font.render(f"* {item}", True, color)
        y = 305 + i * 28

        if i == battle_state["item_selection"]:
            pygame.draw.circle(screen, MUSHROOM_RED, (70, y + 8), 6)

        screen.blit(text, (90, y))

    back_text = small_font.render("[ESC] Back", True, GRAY)
    screen.blit(back_text, (WIDTH - 150, HEIGHT - 30))

def draw_dodge_phase():
    """Draw dodge/bullet-hell phase"""
    # Draw Toad's soul (mushroom)
    soul_x = battle_state["soul_x"]
    soul_y = battle_state["soul_y"]

    # Red mushroom soul
    pygame.draw.circle(screen, MUSHROOM_RED, (soul_x, soul_y - 5), 10)
    pygame.draw.circle(screen, WHITE, (soul_x - 5, soul_y - 8), 3)
    pygame.draw.circle(screen, WHITE, (soul_x + 5, soul_y - 8), 3)
    pygame.draw.ellipse(screen, WHITE, (soul_x - 8, soul_y, 16, 10))

    # Draw attacks
    for attack in battle_state["attacks"]:
        if attack.active:
            attack.draw()

    # Damage flash
    if battle_state["damage_flash"] > 0:
        flash_surface = pygame.Surface((WIDTH, HEIGHT))
        flash_surface.set_alpha(battle_state["damage_flash"])
        flash_surface.fill(RED)
        screen.blit(flash_surface, (0, 0))

def draw_enemy_dialog():
    """Draw enemy's turn dialog"""
    dialog_rect = pygame.Rect(70, 270, WIDTH - 140, 90)
    pygame.draw.rect(screen, BLACK, dialog_rect)
    pygame.draw.rect(screen, WHITE, dialog_rect, 3)

    displayed_text = battle_state["dialog_text"][:battle_state["dialog_progress"]]

    # Word wrap
    words = displayed_text.split(' ')
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + word + " "
        if dialog_font.size(test_line)[0] < WIDTH - 180:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word + " "
    lines.append(current_line)

    for i, line in enumerate(lines[:3]):
        text = dialog_font.render(line, True, WHITE)
        screen.blit(text, (85, 285 + i * 22))

    if battle_state["dialog_progress"] >= len(battle_state["dialog_text"]):
        prompt = small_font.render("[SPACE] Continue", True, GRAY)
        screen.blit(prompt, (WIDTH - 170, HEIGHT - 155))

def draw_player_stats():
    """Draw player HP and stats"""
    stats_y = HEIGHT - 50

    # Name and LV
    name_text = font.render(f"{player_stats['name']}", True, WHITE)
    screen.blit(name_text, (60, stats_y))

    lv_text = small_font.render(f"LV {player_stats['lv']}", True, YELLOW)
    screen.blit(lv_text, (60, stats_y + 20))

    # HP label
    hp_label = font.render("HP", True, RED)
    screen.blit(hp_label, (180, stats_y + 5))

    # HP bar
    max_hp_width = 180
    current_hp_width = int(max_hp_width * (player_stats["hp"] / player_stats["max_hp"]))
    pygame.draw.rect(screen, DARK_GRAY, (220, stats_y + 7, max_hp_width, 18))
    pygame.draw.rect(screen, YELLOW, (220, stats_y + 7, current_hp_width, 18))
    pygame.draw.rect(screen, WHITE, (220, stats_y + 7, max_hp_width, 18), 2)

    hp_text = font.render(f"{player_stats['hp']} / {player_stats['max_hp']}", True, WHITE)
    screen.blit(hp_text, (410, stats_y + 5))

# ===== GAME LOGIC =====
def check_npc_collision():
    """Check if player collides with NPC"""
    global game_state, current_npc, current_friendly_npc, dialog_progress

    # Check enemy NPCs
    for npc in npcs:
        if npc["visible"]:
            distance = math.sqrt((player_x - npc["x"])**2 + (player_y - npc["y"])**2)
            if distance < player_size + 25:
                game_state = "dialog"
                current_npc = npc
                dialog_progress = 0
                return

    # Check friendly NPCs
    for npc in friendly_npcs:
        if npc["visible"]:
            distance = math.sqrt((player_x - npc["x"])**2 + (player_y - npc["y"])**2)
            if distance < player_size + 25:
                game_state = "dialog"
                current_friendly_npc = npc
                dialog_progress = 0
                return

def start_battle(npc):
    """Initialize battle with an NPC"""
    global game_state
    game_state = "battle"
    battle_state["active"] = True
    battle_state["enemy"] = npc
    battle_state["phase"] = "menu"
    battle_state["menu_selection"] = 0
    battle_state["turn_count"] = 0
    battle_state["can_spare"] = False

def handle_fight_action():
    """Start FIGHT minigame"""
    battle_state["phase"] = "fight"
    battle_state["fight_bar_pos"] = 0
    battle_state["fight_bar_direction"] = 1

def execute_fight_damage(accuracy):
    """Execute damage based on timing accuracy"""
    enemy = battle_state["enemy"]

    # Calculate damage based on accuracy
    base_damage = player_stats["atk"] - enemy["enemy_data"]["def"]
    damage_multiplier = 1.0 + accuracy  # 1.0x to 2.0x damage
    damage = max(1, int(base_damage * damage_multiplier))

    enemy["enemy_data"]["hp"] = max(0, enemy["enemy_data"]["hp"] - damage)

    if accuracy > 0.8:
        battle_state["dialog_text"] = f"CRITICAL HIT! You dealt {damage} damage!"
    elif accuracy > 0.5:
        battle_state["dialog_text"] = f"Nice hit! You dealt {damage} damage!"
    else:
        battle_state["dialog_text"] = f"You dealt {damage} damage."

    battle_state["dialog_progress"] = 0
    battle_state["phase"] = "enemy_turn"

    # Check if enemy defeated
    if enemy["enemy_data"]["hp"] <= 0:
        battle_state["dialog_text"] = f"You defeated {enemy['name']}! Got {enemy['enemy_data']['exp']} EXP and {enemy['enemy_data']['gold']} coins!"
        player_stats["exp"] += enemy["enemy_data"]["exp"]
        player_stats["gold"] += enemy["enemy_data"]["gold"]

def handle_act_action(act_index):
    """Handle ACT action"""
    enemy = battle_state["enemy"]
    acts = enemy["enemy_data"]["acts"]

    if act_index < len(acts):
        act = acts[act_index]

        # Different ACT effects based on enemy
        if act == "Check":
            battle_state["dialog_text"] = f"{enemy['name']} - ATK {enemy['enemy_data']['atk']} DEF {enemy['enemy_data']['def']}. "

            if "Goomba" in enemy["name"]:
                battle_state["dialog_text"] += "Just a regular Goomba trying to make a living."
            elif "Koopa" in enemy["name"]:
                battle_state["dialog_text"] += "Loyal to Bowser but can be reasoned with."
            elif "BOWSER" in enemy["name"]:
                battle_state["dialog_text"] += "King of the Koopas. Has kidnapped Luigi!"

        elif act == "Stomp":
            battle_state["dialog_text"] = "You pretend to stomp like Mario! Goomba looks worried."
            enemy["enemy_data"]["spare_threshold"] -= 15

        elif act == "Shell Kick":
            battle_state["dialog_text"] = "You kick an imaginary shell. Koopa respects your technique."
            enemy["enemy_data"]["spare_threshold"] -= 12

        elif act == "Call Mario":
            battle_state["dialog_text"] = "You shout for Mario! Bowser seems slightly concerned."
            enemy["enemy_data"]["spare_threshold"] -= 10
            battle_state["can_spare"] = True

        else:
            # Generic ACT
            enemy["enemy_data"]["spare_threshold"] = max(0, enemy["enemy_data"]["spare_threshold"] - 8)
            battle_state["dialog_text"] = f"You {act.lower()}! {enemy['name']} seems calmer."

        # Check if can spare
        if enemy["enemy_data"]["hp"] <= enemy["enemy_data"]["spare_threshold"]:
            battle_state["can_spare"] = True

        battle_state["dialog_progress"] = 0
        battle_state["phase"] = "enemy_turn"

def handle_item_action(item_index):
    """Handle ITEM action"""
    if item_index < len(player_stats["items"]):
        item = player_stats["items"][item_index]

        if item == "Mushroom":
            heal = 10
            player_stats["hp"] = min(player_stats["max_hp"], player_stats["hp"] + heal)
            battle_state["dialog_text"] = f"You ate a Mushroom! Restored {heal} HP!"
            player_stats["items"].remove(item)

        elif item == "Super Star":
            battle_state["dialog_text"] = "You used a Super Star! You feel invincible! (Next attack deals double damage!)"
            player_stats["atk"] *= 2  # Temporary boost
            player_stats["items"].remove(item)

        battle_state["dialog_progress"] = 0
        battle_state["phase"] = "enemy_turn"

def handle_mercy_action():
    """Handle MERCY action"""
    enemy = battle_state["enemy"]

    if battle_state["can_spare"] or enemy["enemy_data"]["hp"] <= enemy["enemy_data"]["spare_threshold"]:
        battle_state["dialog_text"] = f"You spared {enemy['name']}! They wander off peacefully."
        end_battle(spared=True)
    else:
        battle_state["dialog_text"] = f"{enemy['name']} is not ready to be spared yet."
        battle_state["dialog_progress"] = 0
        battle_state["phase"] = "enemy_turn"

def start_dodge_phase():
    """Start enemy attack phase"""
    battle_state["phase"] = "dodge"
    battle_state["soul_x"] = WIDTH // 2
    battle_state["soul_y"] = 350

    # Enemy dialog before attack
    enemy = battle_state["enemy"]

    # Create attack pattern
    pattern = enemy["enemy_data"]["attack_pattern"]
    battle_state["attacks"] = create_attack_pattern(pattern)

def end_battle(spared=False):
    """End the battle"""
    global game_state

    # Remove NPC if defeated
    if not spared:
        battle_state["enemy"]["visible"] = False

    game_state = "exploring"
    battle_state["active"] = False
    battle_state["enemy"] = None
    battle_state["attacks"] = []

# ===== MAIN GAME LOOP =====
running = True

while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            # Dialog state
            if game_state == "dialog":
                if event.key == pygame.K_SPACE:
                    if dialog_progress >= len((current_npc or current_friendly_npc)["dialog"]):
                        if current_npc:  # Enemy NPC
                            start_battle(current_npc)
                            current_npc = None
                        else:  # Friendly NPC
                            game_state = "exploring"
                            current_friendly_npc = None

            # Battle state
            elif game_state == "battle":
                if battle_state["phase"] == "menu":
                    if event.key == pygame.K_LEFT:
                        battle_state["menu_selection"] = (battle_state["menu_selection"] - 1) % 4
                    elif event.key == pygame.K_RIGHT:
                        battle_state["menu_selection"] = (battle_state["menu_selection"] + 1) % 4
                    elif event.key == pygame.K_UP:
                        battle_state["menu_selection"] = (battle_state["menu_selection"] - 2) % 4
                    elif event.key == pygame.K_DOWN:
                        battle_state["menu_selection"] = (battle_state["menu_selection"] + 2) % 4
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        selection = battle_state["menu_selection"]
                        if selection == 0:  # FIGHT
                            handle_fight_action()
                        elif selection == 1:  # ACT
                            battle_state["phase"] = "act"
                            battle_state["act_selection"] = 0
                        elif selection == 2:  # ITEM
                            battle_state["phase"] = "item"
                            battle_state["item_selection"] = 0
                        elif selection == 3:  # MERCY
                            handle_mercy_action()

                elif battle_state["phase"] == "fight":
                    if event.key == pygame.K_SPACE:
                        # Calculate accuracy based on bar position
                        target_center = 150  # Center of green zone
                        distance = abs(battle_state["fight_bar_pos"] - target_center)
                        accuracy = max(0, 1.0 - (distance / 150))
                        execute_fight_damage(accuracy)

                elif battle_state["phase"] == "act":
                    if event.key == pygame.K_UP:
                        battle_state["act_selection"] = max(0, battle_state["act_selection"] - 1)
                    elif event.key == pygame.K_DOWN:
                        max_acts = len(battle_state["enemy"]["enemy_data"]["acts"]) - 1
                        battle_state["act_selection"] = min(max_acts, battle_state["act_selection"] + 1)
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        handle_act_action(battle_state["act_selection"])
                    elif event.key == pygame.K_ESCAPE:
                        battle_state["phase"] = "menu"

                elif battle_state["phase"] == "item":
                    if event.key == pygame.K_UP:
                        battle_state["item_selection"] = max(0, battle_state["item_selection"] - 1)
                    elif event.key == pygame.K_DOWN:
                        max_items = len(player_stats["items"]) - 1
                        battle_state["item_selection"] = min(max_items, battle_state["item_selection"] + 1)
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        handle_item_action(battle_state["item_selection"])
                    elif event.key == pygame.K_ESCAPE:
                        battle_state["phase"] = "menu"

                elif battle_state["phase"] == "enemy_turn":
                    if event.key == pygame.K_SPACE:
                        if battle_state["dialog_progress"] >= len(battle_state["dialog_text"]):
                            # Check if battle ended
                            if battle_state["enemy"]["enemy_data"]["hp"] <= 0:
                                end_battle(spared=False)
                            else:
                                start_dodge_phase()

    # Get pressed keys for movement
    keys = pygame.key.get_pressed()

    # ===== EXPLORING STATE =====
    if game_state == "exploring":
        if keys[pygame.K_LEFT]:
            player_x -= player_speed
            facing_right = False
        if keys[pygame.K_RIGHT]:
            player_x += player_speed
            facing_right = True
        if keys[pygame.K_UP]:
            player_y -= player_speed
        if keys[pygame.K_DOWN]:
            player_y += player_speed

        player_x = max(player_size // 2, min(WIDTH - player_size // 2, player_x))
        player_y = max(player_size // 2, min(HEIGHT - player_size // 2, player_y))

        animation_counter = (animation_counter + 1) % 30
        check_npc_collision()

        # Draw
        draw_background()
        draw_npcs()
        draw_friendly_npcs()
        draw_toad(int(player_x), int(player_y), animation_counter, facing_right)

        # UI
        ui_bg = pygame.Surface((WIDTH, 35))
        ui_bg.fill((0, 0, 0))
        ui_bg.set_alpha(200)
        screen.blit(ui_bg, (0, 0))

        title = font.render("UNDERTOAD: Mission Luigi", True, YELLOW)
        screen.blit(title, (10, 10))

        hp_display = small_font.render(f"HP: {player_stats['hp']}/{player_stats['max_hp']} | Coins: {player_stats['gold']}", True, WHITE)
        screen.blit(hp_display, (WIDTH - 180, 12))

    # ===== DIALOG STATE =====
    elif game_state == "dialog":
        draw_background()
        draw_npcs()
        draw_friendly_npcs()
        draw_toad(int(player_x), int(player_y), animation_counter, facing_right)

        npc = current_npc or current_friendly_npc
        if npc:
            dialog_timer += 1
            if dialog_timer % 2 == 0:  # Typewriter speed
                dialog_progress = min(dialog_progress + 1, len(npc["dialog"]))
            draw_dialog_box(npc["dialog"], npc["name"])

    # ===== BATTLE STATE =====
    elif game_state == "battle":
        draw_battle_ui()

        # Dialog typewriter in battle
        if battle_state["phase"] == "enemy_turn":
            battle_state["dialog_timer"] += 1
            if battle_state["dialog_timer"] % 2 == 0:
                battle_state["dialog_progress"] = min(
                    battle_state["dialog_progress"] + 1,
                    len(battle_state["dialog_text"])
                )

        # Fight minigame
        elif battle_state["phase"] == "fight":
            battle_state["fight_bar_pos"] += battle_state["fight_bar_direction"] * 4
            if battle_state["fight_bar_pos"] >= 320 or battle_state["fight_bar_pos"] <= 0:
                battle_state["fight_bar_direction"] *= -1

        # Dodge phase
        elif battle_state["phase"] == "dodge":
            # Move soul
            soul_speed = 3.5
            if keys[pygame.K_LEFT]:
                battle_state["soul_x"] -= soul_speed
            if keys[pygame.K_RIGHT]:
                battle_state["soul_x"] += soul_speed
            if keys[pygame.K_UP]:
                battle_state["soul_y"] -= soul_speed
            if keys[pygame.K_DOWN]:
                battle_state["soul_y"] += soul_speed

            # Keep soul in battle box
            battle_state["soul_x"] = max(70, min(WIDTH - 70, battle_state["soul_x"]))
            battle_state["soul_y"] = max(270, min(HEIGHT - 70, battle_state["soul_y"]))

            # Update attacks
            all_cleared = True
            for attack in battle_state["attacks"]:
                if attack.active:
                    attack.update()
                    all_cleared = False

                    # Check collision
                    if attack.collides_with_soul(battle_state["soul_x"], battle_state["soul_y"], 10):
                        enemy = battle_state["enemy"]
                        damage = max(1, enemy["enemy_data"]["atk"] - player_stats["def"])
                        player_stats["hp"] = max(0, player_stats["hp"] - damage)
                        battle_state["damage_flash"] = 150
                        attack.active = False

                        # Check game over
                        if player_stats["hp"] <= 0:
                            battle_state["dialog_text"] = "You failed! But you can try again..."
                            end_battle(spared=False)
                            player_stats["hp"] = player_stats["max_hp"]  # Respawn

            # Fade damage flash
            if battle_state["damage_flash"] > 0:
                battle_state["damage_flash"] = max(0, battle_state["damage_flash"] - 10)

            # End dodge phase when all attacks cleared
            if all_cleared:
                battle_state["phase"] = "menu"
                battle_state["turn_count"] += 1

    # Update display
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
