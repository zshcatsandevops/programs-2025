"""
UNDERMARIO 1.0 - An Undertale-style RPG Engine
A complete battle and exploration system inspired by Undertale
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
pygame.display.set_caption("UNDERMARIO 1.0")

# Colors
BACKGROUND = (30, 30, 60)
GROUND = (80, 60, 40)
PATH = (120, 90, 60)
TREE_TRUNK = (90, 60, 30)
TREE_TOP = (30, 90, 40)
HOUSE_COLOR = (180, 120, 80)
ROOF_COLOR = (150, 60, 40)
GOOMBA_BROWN = (160, 120, 80)
GOOMBA_DARK = (120, 90, 60)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 60, 60)
YELLOW = (255, 220, 60)
BLUE = (80, 120, 220)
GREEN = (60, 220, 80)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)

# Game clock
clock = pygame.time.Clock()
FPS = 60

# ===== PLAYER STATS =====
player_stats = {
    "name": "Goomba",
    "hp": 20,
    "max_hp": 20,
    "atk": 10,
    "def": 10,
    "gold": 0,
    "exp": 0,
    "lv": 1
}

# ===== OVERWORLD STATE =====
player_x = WIDTH // 2
player_y = HEIGHT // 2
player_speed = 2
player_size = 30
animation_counter = 0
facing_right = True

# NPC/Enemy properties
npcs = [
    {
        "x": 150, "y": 200, "color": RED, "name": "Luigi Boss",
        "dialog": "It's-a me, Luigi! Let's-a go!",
        "visible": True,
        "enemy_data": {
            "hp": 50, "max_hp": 50, "atk": 8, "def": 5,
            "acts": ["Check", "Talk", "Compliment", "Jump"],
            "spare_threshold": 30,
            "attack_pattern": "fireballs"
        }
    },
    {
        "x": 450, "y": 150, "color": YELLOW, "name": "Toad Warrior",
        "dialog": "The princess is in another castle!",
        "visible": True,
        "enemy_data": {
            "hp": 35, "max_hp": 35, "atk": 6, "def": 8,
            "acts": ["Check", "Reassure", "Help", "Question"],
            "spare_threshold": 25,
            "attack_pattern": "spores"
        }
    },
    {
        "x": 350, "y": 300, "color": BLUE, "name": "Sans",
        "dialog": "heh. you're gonna have a bad time.",
        "visible": True,
        "enemy_data": {
            "hp": 1, "max_hp": 1, "atk": 99, "def": 1,
            "acts": ["Check", "Joke", "Spare", "Hug"],
            "spare_threshold": 1,
            "attack_pattern": "bones"
        }
    }
]

# ===== BATTLE STATE =====
battle_state = {
    "active": False,
    "enemy": None,
    "phase": "menu",  # "menu", "fight", "act", "item", "mercy", "enemy_turn", "dodge"
    "menu_selection": 0,
    "act_selection": 0,
    "can_spare": False,
    "turn_count": 0,
    "soul_x": WIDTH // 2,
    "soul_y": HEIGHT // 2,
    "attacks": [],
    "damage_flash": 0,
    "dialog_text": "",
    "dialog_progress": 0,
    "dialog_timer": 0
}

# ===== GAME STATE =====
game_state = "exploring"  # "exploring", "dialog", "battle"
current_npc = None
dialog_timer = 0
dialog_progress = 0

# Fonts
font = pygame.font.SysFont("Arial", 16)
dialog_font = pygame.font.SysFont("Arial", 14)
battle_font = pygame.font.SysFont("Arial", 18, bold=True)
small_font = pygame.font.SysFont("Arial", 12)

# ===== ATTACK PATTERNS =====
class Attack:
    def __init__(self, x, y, vx, vy, width, height, color=WHITE):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.width = width
        self.height = height
        self.color = color
        self.active = True

    def update(self):
        self.x += self.vx
        self.y += self.vy

        # Remove if out of bounds
        if (self.x < 0 or self.x > WIDTH or
            self.y < 0 or self.y > HEIGHT):
            self.active = False

    def draw(self):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))

    def collides_with_soul(self, soul_x, soul_y, soul_size=8):
        return (self.x < soul_x + soul_size and
                self.x + self.width > soul_x and
                self.y < soul_y + soul_size and
                self.y + self.height > soul_y)

def create_attack_pattern(pattern_type):
    """Generate attacks based on enemy pattern"""
    attacks = []

    if pattern_type == "fireballs":
        # Luigi's fireball pattern
        for i in range(5):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 4)
            attacks.append(Attack(
                WIDTH // 2, HEIGHT // 2,
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                16, 16, RED
            ))

    elif pattern_type == "spores":
        # Toad's falling spores
        for i in range(8):
            attacks.append(Attack(
                random.randint(100, WIDTH - 100),
                -20,
                0,
                random.uniform(2, 4),
                12, 12, YELLOW
            ))

    elif pattern_type == "bones":
        # Sans's bone attacks
        for i in range(6):
            if random.random() < 0.5:
                # Horizontal bone
                attacks.append(Attack(
                    -20 if random.random() < 0.5 else WIDTH + 20,
                    random.randint(100, HEIGHT - 100),
                    4 if random.random() < 0.5 else -4,
                    0,
                    30, 10, WHITE
                ))
            else:
                # Vertical bone
                attacks.append(Attack(
                    random.randint(100, WIDTH - 100),
                    -20 if random.random() < 0.5 else HEIGHT + 20,
                    0,
                    4 if random.random() < 0.5 else -4,
                    10, 30, WHITE
                ))

    return attacks

# ===== DRAWING FUNCTIONS =====
def draw_background():
    """Draw overworld background"""
    screen.fill(BACKGROUND)
    pygame.draw.rect(screen, GROUND, (0, HEIGHT - 100, WIDTH, 100))
    pygame.draw.rect(screen, PATH, (WIDTH // 2 - 50, HEIGHT - 100, 100, 100))

    # Trees
    for x, y in [(100, 150), (500, 120), (200, 80)]:
        pygame.draw.rect(screen, TREE_TRUNK, (x, y, 20, 60))
        pygame.draw.circle(screen, TREE_TOP, (x + 10, y - 20), 40)

    # Houses
    pygame.draw.rect(screen, HOUSE_COLOR, (50, HEIGHT - 180, 80, 80))
    pygame.draw.polygon(screen, ROOF_COLOR, [(30, HEIGHT - 180), (150, HEIGHT - 180), (90, HEIGHT - 220)])
    pygame.draw.rect(screen, HOUSE_COLOR, (470, HEIGHT - 160, 80, 60))
    pygame.draw.polygon(screen, ROOF_COLOR, [(450, HEIGHT - 160), (550, HEIGHT - 160), (500, HEIGHT - 200)])

def draw_goomba(x, y, frame, facing_right):
    """Draw player character"""
    pygame.draw.circle(screen, GOOMBA_BROWN, (x, y), player_size // 2)

    eye_offset = 5 if facing_right else -5
    pygame.draw.circle(screen, BLACK, (x + eye_offset, y - 5), 4)

    mouth_y = y + 5
    if frame < 15:
        pygame.draw.arc(screen, BLACK, (x - 8, mouth_y - 3, 16, 8), 0, math.pi, 2)
    else:
        pygame.draw.arc(screen, BLACK, (x - 8, mouth_y, 16, 6), math.pi, 2 * math.pi, 2)

    foot_offset = 3 if frame < 15 else -3
    pygame.draw.ellipse(screen, GOOMBA_DARK, (x - 12, y + 10, 8, 4))
    pygame.draw.ellipse(screen, GOOMBA_DARK, (x + 4 + foot_offset, y + 10, 8, 4))

def draw_npcs():
    """Draw all NPCs in overworld"""
    for npc in npcs:
        if npc["visible"]:
            pygame.draw.circle(screen, npc["color"], (npc["x"], npc["y"]), 20)

            # Face
            pygame.draw.circle(screen, WHITE, (npc["x"] - 5, npc["y"] - 3), 4)
            pygame.draw.circle(screen, WHITE, (npc["x"] + 5, npc["y"] - 3), 4)
            pygame.draw.circle(screen, BLACK, (npc["x"] - 5, npc["y"] - 3), 2)
            pygame.draw.circle(screen, BLACK, (npc["x"] + 5, npc["y"] - 3), 2)

            name_text = small_font.render(npc["name"], True, WHITE)
            screen.blit(name_text, (npc["x"] - name_text.get_width() // 2, npc["y"] - 35))

def draw_dialog_box(text, speaker_name=""):
    """Draw dialog box with typewriter effect"""
    box_rect = pygame.Rect(50, HEIGHT - 120, WIDTH - 100, 100)
    pygame.draw.rect(screen, BLACK, box_rect)
    pygame.draw.rect(screen, WHITE, box_rect, 3)

    if speaker_name:
        name_text = font.render(speaker_name, True, YELLOW)
        screen.blit(name_text, (70, HEIGHT - 110))

    # Typewriter effect
    displayed_text = text[:dialog_progress]
    dialog_text = dialog_font.render(displayed_text, True, WHITE)
    screen.blit(dialog_text, (70, HEIGHT - 80))

    if dialog_progress >= len(text):
        prompt = small_font.render("Press SPACE to continue", True, GRAY)
        screen.blit(prompt, (WIDTH - 200, HEIGHT - 30))

def draw_battle_ui():
    """Draw battle interface"""
    screen.fill(BLACK)

    # Enemy info
    enemy = battle_state["enemy"]
    enemy_name = battle_font.render(enemy["name"], True, WHITE)
    screen.blit(enemy_name, (50, 30))

    # HP bar
    hp_percent = enemy["enemy_data"]["hp"] / enemy["enemy_data"]["max_hp"]
    pygame.draw.rect(screen, DARK_GRAY, (50, 60, 200, 20))
    pygame.draw.rect(screen, GREEN, (50, 60, 200 * hp_percent, 20))
    pygame.draw.rect(screen, WHITE, (50, 60, 200, 20), 2)

    hp_text = small_font.render(
        f"{enemy['enemy_data']['hp']}/{enemy['enemy_data']['max_hp']}",
        True, WHITE
    )
    screen.blit(hp_text, (260, 63))

    # Battle box
    battle_box = pygame.Rect(50, 250, WIDTH - 100, 180)
    pygame.draw.rect(screen, BLACK, battle_box)
    pygame.draw.rect(screen, WHITE, battle_box, 3)

    if battle_state["phase"] == "menu":
        draw_battle_menu()
    elif battle_state["phase"] == "act":
        draw_act_menu()
    elif battle_state["phase"] == "dodge":
        draw_dodge_phase()
    elif battle_state["phase"] == "enemy_turn":
        draw_enemy_dialog()

    # Player stats
    draw_player_stats()

def draw_battle_menu():
    """Draw main battle menu"""
    menu_items = ["FIGHT", "ACT", "ITEM", "MERCY"]
    menu_x = 100
    menu_y = 350
    spacing = 140

    for i, item in enumerate(menu_items):
        color = YELLOW if i == battle_state["menu_selection"] else WHITE
        text = battle_font.render(item, True, color)
        x = menu_x + (i % 2) * spacing
        y = menu_y + (i // 2) * 40

        if i == battle_state["menu_selection"]:
            pygame.draw.polygon(screen, RED, [
                (x - 20, y + 10),
                (x - 10, y + 5),
                (x - 10, y + 15)
            ])

        screen.blit(text, (x, y))

def draw_act_menu():
    """Draw ACT options menu"""
    acts = battle_state["enemy"]["enemy_data"]["acts"]

    for i, act in enumerate(acts):
        color = YELLOW if i == battle_state["act_selection"] else WHITE
        text = font.render(f"* {act}", True, color)
        y = 280 + i * 30

        if i == battle_state["act_selection"]:
            pygame.draw.polygon(screen, RED, [
                (60, y + 8),
                (75, y + 3),
                (75, y + 13)
            ])

        screen.blit(text, (85, y))

    back_text = small_font.render("Press ESC to go back", True, GRAY)
    screen.blit(back_text, (WIDTH - 200, HEIGHT - 30))

def draw_dodge_phase():
    """Draw dodge/bullet-hell phase"""
    # Draw soul (heart)
    soul_size = 16
    pygame.draw.polygon(screen, RED, [
        (battle_state["soul_x"], battle_state["soul_y"] - 5),
        (battle_state["soul_x"] - 8, battle_state["soul_y"] + 8),
        (battle_state["soul_x"] + 8, battle_state["soul_y"] + 8)
    ])

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
    dialog_rect = pygame.Rect(70, 270, WIDTH - 140, 80)
    pygame.draw.rect(screen, BLACK, dialog_rect)
    pygame.draw.rect(screen, WHITE, dialog_rect, 2)

    displayed_text = battle_state["dialog_text"][:battle_state["dialog_progress"]]
    text = dialog_font.render(displayed_text, True, WHITE)
    screen.blit(text, (85, 290))

def draw_player_stats():
    """Draw player HP and stats"""
    stats_y = HEIGHT - 60

    # Name and LV
    name_text = small_font.render(f"{player_stats['name']} LV {player_stats['lv']}", True, WHITE)
    screen.blit(name_text, (50, stats_y))

    # HP
    hp_label = small_font.render("HP", True, WHITE)
    screen.blit(hp_label, (200, stats_y))

    # HP bar
    max_hp_width = 150
    current_hp_width = int(max_hp_width * (player_stats["hp"] / player_stats["max_hp"]))
    pygame.draw.rect(screen, DARK_GRAY, (230, stats_y, max_hp_width, 16))
    pygame.draw.rect(screen, YELLOW, (230, stats_y, current_hp_width, 16))
    pygame.draw.rect(screen, WHITE, (230, stats_y, max_hp_width, 16), 2)

    hp_text = small_font.render(f"{player_stats['hp']}/{player_stats['max_hp']}", True, WHITE)
    screen.blit(hp_text, (390, stats_y))

# ===== GAME LOGIC =====
def check_npc_collision():
    """Check if player collides with NPC"""
    global game_state, current_npc, dialog_progress
    for npc in npcs:
        if npc["visible"]:
            distance = math.sqrt((player_x - npc["x"])**2 + (player_y - npc["y"])**2)
            if distance < player_size + 20:
                game_state = "dialog"
                current_npc = npc
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
    """Handle FIGHT action"""
    enemy = battle_state["enemy"]

    # Calculate damage
    base_damage = player_stats["atk"] - enemy["enemy_data"]["def"]
    damage = max(1, base_damage + random.randint(-2, 2))

    enemy["enemy_data"]["hp"] = max(0, enemy["enemy_data"]["hp"] - damage)

    battle_state["dialog_text"] = f"You dealt {damage} damage!"
    battle_state["dialog_progress"] = 0
    battle_state["phase"] = "enemy_turn"

    # Check if enemy defeated
    if enemy["enemy_data"]["hp"] <= 0:
        battle_state["dialog_text"] = f"You defeated {enemy['name']}!"
        player_stats["exp"] += 10
        player_stats["gold"] += 5

def handle_act_action(act_index):
    """Handle ACT action"""
    enemy = battle_state["enemy"]
    acts = enemy["enemy_data"]["acts"]

    if act_index < len(acts):
        act = acts[act_index]

        # Different ACT effects
        if act == "Check":
            battle_state["dialog_text"] = f"{enemy['name']} - ATK {enemy['enemy_data']['atk']} DEF {enemy['enemy_data']['def']}"
        elif act == "Spare":
            battle_state["can_spare"] = True
            battle_state["dialog_text"] = "You can now SPARE this enemy!"
        else:
            # Generic ACT increases spare chance
            enemy["enemy_data"]["spare_threshold"] = max(
                0,
                enemy["enemy_data"]["spare_threshold"] - 10
            )
            battle_state["dialog_text"] = f"You {act.lower()}ed {enemy['name']}. They seem calmer."

            if enemy["enemy_data"]["hp"] <= enemy["enemy_data"]["spare_threshold"]:
                battle_state["can_spare"] = True

        battle_state["dialog_progress"] = 0
        battle_state["phase"] = "enemy_turn"

def handle_mercy_action():
    """Handle MERCY action"""
    enemy = battle_state["enemy"]

    if (battle_state["can_spare"] or
        enemy["enemy_data"]["hp"] <= enemy["enemy_data"]["spare_threshold"]):

        battle_state["dialog_text"] = f"You spared {enemy['name']}!"
        end_battle(spared=True)
    else:
        battle_state["dialog_text"] = f"{enemy['name']} is not ready to be spared."
        battle_state["dialog_progress"] = 0
        battle_state["phase"] = "enemy_turn"

def start_dodge_phase():
    """Start enemy attack phase"""
    battle_state["phase"] = "dodge"
    battle_state["soul_x"] = WIDTH // 2
    battle_state["soul_y"] = HEIGHT // 2

    # Create attack pattern
    pattern = battle_state["enemy"]["enemy_data"]["attack_pattern"]
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
                    if dialog_progress >= len(current_npc["dialog"]):
                        start_battle(current_npc)
                        current_npc = None

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
                            battle_state["dialog_text"] = "You have no items!"
                            battle_state["dialog_progress"] = 0
                            battle_state["phase"] = "enemy_turn"
                        elif selection == 3:  # MERCY
                            handle_mercy_action()

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
        draw_goomba(player_x, player_y, animation_counter, facing_right)

        # UI
        pygame.draw.rect(screen, (40, 40, 70), (0, 0, WIDTH, 30))
        title = font.render("UNDERMARIO 1.0 - Use arrows to move | HP: " + str(player_stats["hp"]) + "/" + str(player_stats["max_hp"]), True, WHITE)
        screen.blit(title, (10, 10))

    # ===== DIALOG STATE =====
    elif game_state == "dialog":
        draw_background()
        draw_npcs()
        draw_goomba(player_x, player_y, animation_counter, facing_right)

        if current_npc:
            dialog_timer += 1
            if dialog_timer % 2 == 0:  # Typewriter speed
                dialog_progress = min(dialog_progress + 1, len(current_npc["dialog"]))
            draw_dialog_box(current_npc["dialog"], current_npc["name"])

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

        # Dodge phase
        elif battle_state["phase"] == "dodge":
            # Move soul
            soul_speed = 3
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
                    if attack.collides_with_soul(battle_state["soul_x"], battle_state["soul_y"]):
                        enemy = battle_state["enemy"]
                        damage = max(1, enemy["enemy_data"]["atk"] - player_stats["def"])
                        player_stats["hp"] = max(0, player_stats["hp"] - damage)
                        battle_state["damage_flash"] = 150
                        attack.active = False

                        # Check game over
                        if player_stats["hp"] <= 0:
                            battle_state["dialog_text"] = "You died!"
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
