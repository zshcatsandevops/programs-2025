import pygame
import sys
import math
import random

pygame.init()
pygame.mixer.init()

# ========================
# UNDERTALE BATTLE ENGINE
# ========================

# Screen
WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Undertale Battle Engine - Sans Fight")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
SNOW = (240, 248, 255)
DARK_SNOW = (200, 220, 230)
BONE_WHITE = (240, 240, 240)

# Fonts
font_large = pygame.font.SysFont("Arial", 32, bold=True)
font_dialogue = pygame.font.SysFont("Arial", 22, bold=True)
font_small = pygame.font.SysFont("Arial", 18)
font_damage = pygame.font.SysFont("Arial", 24, bold=True)

# Battle States
STATE_INTRO = 0
STATE_MENU = 1
STATE_FIGHT = 2
STATE_ACT = 3
STATE_ITEM = 4
STATE_MERCY = 5
STATE_ENEMY_TURN = 6
STATE_DIALOGUE = 7
STATE_GAME_OVER = 8
STATE_VICTORY = 9

# ========================
# GAME CLASSES
# ========================

class Player:
    def __init__(self):
        self.max_hp = 20
        self.hp = 20
        self.attack = 10
        self.defense = 10
        self.lv = 1
        self.inv_frames = 0  # Invincibility frames
        self.karma = 0  # KR poison damage (Sans special)

class Soul:
    """The player's SOUL (red heart)"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 8
        self.speed = 2.5
        self.color = RED

    def move(self, keys, battle_box):
        """Move the soul based on keyboard input"""
        dx, dy = 0, 0
        if keys[pygame.K_LEFT]:
            dx -= self.speed
        if keys[pygame.K_RIGHT]:
            dx += self.speed
        if keys[pygame.K_UP]:
            dy -= self.speed
        if keys[pygame.K_DOWN]:
            dy += self.speed

        # Update position with collision
        new_x = self.x + dx
        new_y = self.y + dy

        # Keep within battle box
        if new_x - self.size >= battle_box.x and new_x + self.size <= battle_box.x + battle_box.width:
            self.x = new_x
        if new_y - self.size >= battle_box.y and new_y + self.size <= battle_box.y + battle_box.height:
            self.y = new_y

    def draw(self, screen):
        """Draw the soul"""
        # Draw red heart
        points = [
            (self.x, self.y + self.size),  # bottom point
            (self.x - self.size, self.y - self.size // 2),  # left top
            (self.x, self.y - self.size),  # top middle
            (self.x + self.size, self.y - self.size // 2),  # right top
        ]
        pygame.draw.polygon(screen, self.color, points)

    def get_rect(self):
        """Get collision rectangle"""
        return pygame.Rect(self.x - self.size, self.y - self.size,
                          self.size * 2, self.size * 2)

class BattleBox:
    """The box where attacks happen"""
    def __init__(self):
        self.x = WIDTH // 2 - 140
        self.y = HEIGHT // 2 + 10
        self.width = 280
        self.height = 140

    def draw(self, screen):
        """Draw the battle box"""
        pygame.draw.rect(screen, WHITE,
                        (self.x - 5, self.y - 5, self.width + 10, self.height + 10), 5)
        pygame.draw.rect(screen, BLACK,
                        (self.x, self.y, self.width, self.height))

class Bone:
    """Bone attack object"""
    def __init__(self, x, y, width, height, vx=0, vy=0, damage=1):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.vx = vx
        self.vy = vy
        self.damage = damage
        self.active = True

    def update(self):
        """Update bone position"""
        self.x += self.vx
        self.y += self.vy

        # Deactivate if off screen
        if self.x < -100 or self.x > WIDTH + 100 or self.y < -100 or self.y > HEIGHT + 100:
            self.active = False

    def draw(self, screen):
        """Draw the bone"""
        if self.active:
            # Draw white bone with outline
            pygame.draw.rect(screen, WHITE, (self.x, self.y, self.width, self.height))
            pygame.draw.rect(screen, (200, 200, 200), (self.x, self.y, self.width, self.height), 2)

    def get_rect(self):
        """Get collision rectangle"""
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def collides_with(self, soul):
        """Check collision with soul"""
        return self.active and self.get_rect().colliderect(soul.get_rect())

class AttackPattern:
    """Manages attack patterns"""
    def __init__(self, battle_box):
        self.battle_box = battle_box
        self.bones = []
        self.timer = 0
        self.pattern_duration = 300  # frames (5 seconds at 60fps)
        self.pattern_type = 0

    def start_pattern(self, pattern_type):
        """Start a new attack pattern"""
        self.pattern_type = pattern_type
        self.bones = []
        self.timer = 0

    def update(self):
        """Update attack pattern"""
        self.timer += 1

        # Pattern 0: Horizontal bones from sides
        if self.pattern_type == 0:
            if self.timer % 30 == 0:
                y = random.randint(self.battle_box.y + 20,
                                  self.battle_box.y + self.battle_box.height - 20)
                # From left
                if random.random() < 0.5:
                    self.bones.append(Bone(self.battle_box.x - 20, y, 15, 60, vx=3))
                # From right
                else:
                    self.bones.append(Bone(self.battle_box.x + self.battle_box.width + 5, y, 15, 60, vx=-3))

        # Pattern 1: Vertical bones from top and bottom
        elif self.pattern_type == 1:
            if self.timer % 25 == 0:
                x = random.randint(self.battle_box.x + 20,
                                  self.battle_box.x + self.battle_box.width - 20)
                # From top
                if random.random() < 0.5:
                    self.bones.append(Bone(x, self.battle_box.y - 20, 60, 15, vy=3))
                # From bottom
                else:
                    self.bones.append(Bone(x, self.battle_box.y + self.battle_box.height + 5, 60, 15, vy=-3))

        # Pattern 2: Circle of bones
        elif self.pattern_type == 2:
            if self.timer % 20 == 0:
                center_x = self.battle_box.x + self.battle_box.width // 2
                center_y = self.battle_box.y + self.battle_box.height // 2
                angle = random.random() * math.pi * 2
                distance = 100
                x = center_x + math.cos(angle) * distance
                y = center_y + math.sin(angle) * distance
                vx = -math.cos(angle) * 2
                vy = -math.sin(angle) * 2
                self.bones.append(Bone(x, y, 40, 12, vx=vx, vy=vy))

        # Pattern 3: Wave pattern
        elif self.pattern_type == 3:
            if self.timer % 15 == 0:
                y_offset = math.sin(self.timer / 10) * 30
                y = self.battle_box.y + self.battle_box.height // 2 + y_offset
                self.bones.append(Bone(self.battle_box.x - 20, y, 15, 50, vx=4))

        # Pattern 4: Slam pattern (bones fall from top)
        elif self.pattern_type == 4:
            if self.timer % 10 == 0:
                x = random.randint(self.battle_box.x + 10,
                                  self.battle_box.x + self.battle_box.width - 30)
                self.bones.append(Bone(x, self.battle_box.y - 100, 20, 80, vy=5))

        # Update all bones
        for bone in self.bones:
            bone.update()

        # Remove inactive bones
        self.bones = [b for b in self.bones if b.active]

    def draw(self, screen):
        """Draw all bones"""
        for bone in self.bones:
            bone.draw(screen)

    def check_collision(self, soul):
        """Check if any bone hits the soul"""
        for bone in self.bones:
            if bone.collides_with(soul):
                bone.active = False
                return bone.damage
        return 0

    def is_finished(self):
        """Check if pattern is finished"""
        return self.timer >= self.pattern_duration

class Enemy:
    """Enemy character"""
    def __init__(self, name, hp, attack, defense):
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.attack = attack
        self.defense = defense
        self.can_spare = False
        self.dialogue_index = 0

        # Sans-specific dialogues
        self.dialogues = [
            "heya.",
            "you've been busy, huh?",
            "...",
            "do you wanna have a bad time?",
            "here we go."
        ]

        self.check_text = [
            "* SANS - ATK 1 DEF 1",
            "* The easiest enemy.",
            "* Can only deal 1 damage."
        ]

    def get_dialogue(self):
        """Get current dialogue"""
        if self.dialogue_index < len(self.dialogues):
            text = self.dialogues[self.dialogue_index]
            self.dialogue_index += 1
            return text
        return "..."

    def take_damage(self, damage):
        """Take damage"""
        self.hp -= damage
        if self.hp < 0:
            self.hp = 0

class Menu:
    """Battle menu system"""
    def __init__(self):
        self.options = ["FIGHT", "ACT", "ITEM", "MERCY"]
        self.selected = 0
        self.soul_positions = [
            (50, HEIGHT - 60),
            (170, HEIGHT - 60),
            (290, HEIGHT - 60),
            (410, HEIGHT - 60)
        ]

    def move(self, direction):
        """Move menu selection"""
        if direction == "left":
            self.selected = max(0, self.selected - 1)
        elif direction == "right":
            self.selected = min(len(self.options) - 1, self.selected + 1)

    def draw(self, screen, player):
        """Draw the menu"""
        # Draw HP bar
        hp_text = font_small.render(f"HP", True, WHITE)
        screen.blit(hp_text, (30, HEIGHT - 110))

        # HP bar background
        pygame.draw.rect(screen, (128, 0, 0), (70, HEIGHT - 105, 100, 20))
        # HP bar fill
        hp_width = int((player.hp / player.max_hp) * 100)
        pygame.draw.rect(screen, YELLOW, (70, HEIGHT - 105, hp_width, 20))

        # HP numbers
        hp_num = font_small.render(f"{player.hp} / {player.max_hp}", True, WHITE)
        screen.blit(hp_num, (180, HEIGHT - 110))

        # Menu options
        for i, option in enumerate(self.options):
            x = 70 + i * 120
            y = HEIGHT - 60

            # Draw button
            color = YELLOW if i == self.selected else WHITE
            text = font_dialogue.render(option, True, color)
            screen.blit(text, (x, y))

        # Draw soul at selected option
        soul_x, soul_y = self.soul_positions[self.selected]
        draw_menu_soul(screen, soul_x, soul_y)

def draw_menu_soul(screen, x, y):
    """Draw the small soul for menu selection"""
    size = 8
    points = [
        (x, y + size),
        (x - size, y - size // 2),
        (x, y - size),
        (x + size, y - size // 2),
    ]
    pygame.draw.polygon(screen, RED, points)

# ========================
# SPRITE CREATION
# ========================

def create_sans_sprite():
    """Create Sans sprite"""
    s = pygame.Surface((120, 140), pygame.SRCALPHA)
    # Head
    pygame.draw.circle(s, WHITE, (60, 35), 30)
    # Hood
    pygame.draw.rect(s, (0, 0, 0), (35, 8, 50, 25))
    pygame.draw.rect(s, (0, 0, 0), (28, 25, 64, 18))
    # Body
    pygame.draw.rect(s, WHITE, (30, 65, 60, 60), border_radius=12)
    pygame.draw.rect(s, (0, 0, 0), (35, 70, 50, 45), border_radius=10)
    # Jacket
    pygame.draw.rect(s, (0, 50, 100), (25, 65, 70, 50), border_radius=10)
    # Eyes
    pygame.draw.circle(s, BLACK, (48, 32), 7)
    pygame.draw.circle(s, BLACK, (72, 32), 7)
    # Smile
    pygame.draw.arc(s, BLACK, (45, 38, 30, 15), 0, math.pi, 3)
    # Arms
    pygame.draw.rect(s, WHITE, (15, 75, 15, 40), border_radius=7)
    pygame.draw.rect(s, WHITE, (90, 75, 15, 40), border_radius=7)
    # Slippers
    pygame.draw.ellipse(s, (200, 100, 100), (35, 120, 20, 15))
    pygame.draw.ellipse(s, (200, 100, 100), (65, 120, 20, 15))

    return s

# ========================
# BACKGROUND
# ========================

def draw_background():
    """Draw battle background"""
    # Night sky gradient
    for y in range(HEIGHT // 2):
        ratio = y / (HEIGHT // 2)
        color = (
            int(10 * (1 - ratio) + 30 * ratio),
            int(10 * (1 - ratio) + 40 * ratio),
            int(30 * (1 - ratio) + 80 * ratio)
        )
        pygame.draw.line(screen, color, (0, y), (WIDTH, y))

    # Ground
    for y in range(HEIGHT // 2, HEIGHT):
        ratio = (y - HEIGHT // 2) / (HEIGHT // 2)
        color = (
            int(240 * (1 - ratio) + 200 * ratio),
            int(248 * (1 - ratio) + 220 * ratio),
            int(255 * (1 - ratio) + 230 * ratio)
        )
        pygame.draw.line(screen, color, (0, y), (WIDTH, y))

# Snow particles
snowflakes = []
for _ in range(60):
    snowflakes.append({
        'x': random.randint(0, WIDTH),
        'y': random.randint(-HEIGHT, 0),
        'speed': random.uniform(0.5, 2.0),
        'size': random.randint(1, 3)
    })

def update_snow():
    """Update and draw snow"""
    for f in snowflakes:
        f['y'] += f['speed']
        if f['y'] > HEIGHT:
            f['y'] = random.randint(-50, -5)
            f['x'] = random.randint(0, WIDTH)
    for f in snowflakes:
        pygame.draw.circle(screen, WHITE, (int(f['x']), int(f['y'])), f['size'])

# ========================
# DIALOGUE SYSTEM
# ========================

class DialogueBox:
    """Dialogue box with typewriter effect"""
    def __init__(self):
        self.text = ""
        self.displayed_text = ""
        self.char_index = 0
        self.timer = 0
        self.speed = 2  # chars per frame
        self.finished = False

    def set_text(self, text):
        """Set new dialogue text"""
        self.text = text
        self.displayed_text = ""
        self.char_index = 0
        self.finished = False

    def update(self):
        """Update typewriter effect"""
        if self.char_index < len(self.text):
            self.timer += 1
            if self.timer >= self.speed:
                self.displayed_text += self.text[self.char_index]
                self.char_index += 1
                self.timer = 0
        else:
            self.finished = True

    def skip(self):
        """Skip to end of text"""
        self.displayed_text = self.text
        self.char_index = len(self.text)
        self.finished = True

    def draw(self, screen):
        """Draw dialogue box"""
        # Box
        box_rect = pygame.Rect(170, 250, 440, 120)
        pygame.draw.rect(screen, BLACK, box_rect)
        pygame.draw.rect(screen, WHITE, box_rect, 4)

        # Text (word wrap)
        words = self.displayed_text.split(' ')
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + word + " "
            if font_dialogue.size(test_line)[0] < 410:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word + " "
        lines.append(current_line)

        # Draw lines
        y = 270
        for line in lines[:3]:  # Max 3 lines
            text_surface = font_dialogue.render(line, True, WHITE)
            screen.blit(text_surface, (185, y))
            y += 30

        # Continue indicator
        if self.finished:
            indicator = font_small.render("[Z]", True, YELLOW)
            screen.blit(indicator, (580, 350))

# ========================
# MAIN GAME
# ========================

class BattleGame:
    def __init__(self):
        self.state = STATE_INTRO
        self.player = Player()
        self.enemy = Enemy("Sans", hp=1, attack=1, defense=1)
        self.soul = Soul(WIDTH // 2, HEIGHT // 2 + 80)
        self.battle_box = BattleBox()
        self.menu = Menu()
        self.attack_pattern = AttackPattern(self.battle_box)
        self.dialogue = DialogueBox()
        self.sans_sprite = create_sans_sprite()

        self.turn_count = 0
        self.damage_timer = 0
        self.damage_text = ""
        self.damage_x = 0
        self.damage_y = 0

        self.intro_timer = 0
        self.enemy_turn_timer = 0

        # Start with intro dialogue
        self.dialogue.set_text("* Sans blocks the way!")

    def handle_input(self, event):
        """Handle keyboard input"""
        if event.type == pygame.KEYDOWN:
            # STATE: INTRO
            if self.state == STATE_INTRO:
                if event.key == pygame.K_z:
                    if self.dialogue.finished:
                        self.state = STATE_MENU
                    else:
                        self.dialogue.skip()

            # STATE: MENU
            elif self.state == STATE_MENU:
                if event.key == pygame.K_LEFT:
                    self.menu.move("left")
                elif event.key == pygame.K_RIGHT:
                    self.menu.move("right")
                elif event.key == pygame.K_z:
                    # Select menu option
                    selected = self.menu.selected
                    if selected == 0:  # FIGHT
                        self.state = STATE_FIGHT
                        self.dialogue.set_text("* You prepare to attack!")
                    elif selected == 1:  # ACT
                        self.state = STATE_ACT
                        self.dialogue.set_text("* Check  * Joke  * Compliment")
                    elif selected == 2:  # ITEM
                        self.state = STATE_ITEM
                        self.dialogue.set_text("* You have no items.")
                    elif selected == 3:  # MERCY
                        self.state = STATE_MERCY
                        self.dialogue.set_text("* Spare  * Flee")

            # STATE: FIGHT
            elif self.state == STATE_FIGHT:
                if event.key == pygame.K_z:
                    if self.dialogue.finished:
                        # Simple attack - deals damage
                        damage = max(1, self.player.attack - self.enemy.defense)
                        self.enemy.take_damage(damage)
                        self.show_damage(damage, WIDTH // 2, 100)

                        if self.enemy.hp <= 0:
                            self.state = STATE_VICTORY
                            self.dialogue.set_text("* You won! Gained 0 EXP and 0 gold.")
                        else:
                            self.start_enemy_turn()
                    else:
                        self.dialogue.skip()

            # STATE: ACT
            elif self.state == STATE_ACT:
                if event.key == pygame.K_z:
                    if self.dialogue.finished:
                        self.dialogue.set_text("* " + "\n* ".join(self.enemy.check_text))
                        self.state = STATE_DIALOGUE
                    else:
                        self.dialogue.skip()

            # STATE: ITEM
            elif self.state == STATE_ITEM:
                if event.key == pygame.K_z:
                    if self.dialogue.finished:
                        self.start_enemy_turn()
                    else:
                        self.dialogue.skip()

            # STATE: MERCY
            elif self.state == STATE_MERCY:
                if event.key == pygame.K_z:
                    if self.dialogue.finished:
                        self.state = STATE_VICTORY
                        self.dialogue.set_text("* You spared Sans. * You won!")
                    else:
                        self.dialogue.skip()

            # STATE: DIALOGUE
            elif self.state == STATE_DIALOGUE:
                if event.key == pygame.K_z:
                    if self.dialogue.finished:
                        self.start_enemy_turn()
                    else:
                        self.dialogue.skip()

            # STATE: VICTORY
            elif self.state == STATE_VICTORY:
                if event.key == pygame.K_r:
                    self.__init__()  # Restart

            # STATE: GAME OVER
            elif self.state == STATE_GAME_OVER:
                if event.key == pygame.K_r:
                    self.__init__()  # Restart

    def start_enemy_turn(self):
        """Start enemy's attack turn"""
        self.state = STATE_ENEMY_TURN
        self.enemy_turn_timer = 0
        self.turn_count += 1

        # Choose attack pattern
        pattern = random.randint(0, 4)
        self.attack_pattern.start_pattern(pattern)

        # Show enemy dialogue
        dialogue = self.enemy.get_dialogue()
        self.dialogue.set_text(f"* {dialogue}")

    def show_damage(self, damage, x, y):
        """Show damage number"""
        self.damage_text = str(damage)
        self.damage_x = x
        self.damage_y = y
        self.damage_timer = 60

    def update(self):
        """Update game state"""
        # Update dialogue
        self.dialogue.update()

        # Update damage display
        if self.damage_timer > 0:
            self.damage_timer -= 1
            self.damage_y -= 1

        # STATE: INTRO
        if self.state == STATE_INTRO:
            self.intro_timer += 1

        # STATE: ENEMY_TURN
        elif self.state == STATE_ENEMY_TURN:
            self.enemy_turn_timer += 1

            # Update attack pattern
            self.attack_pattern.update()

            # Move soul
            keys = pygame.key.get_pressed()
            self.soul.move(keys, self.battle_box)

            # Check collision
            if self.player.inv_frames <= 0:
                damage = self.attack_pattern.check_collision(self.soul)
                if damage > 0:
                    self.player.hp -= damage
                    self.player.inv_frames = 30  # 0.5 seconds of invincibility
                    self.show_damage(damage, int(self.soul.x), int(self.soul.y) - 20)

                    if self.player.hp <= 0:
                        self.state = STATE_GAME_OVER
            else:
                self.player.inv_frames -= 1

            # End enemy turn after pattern finishes
            if self.attack_pattern.is_finished():
                self.state = STATE_MENU
                self.menu.selected = 0

    def draw(self):
        """Draw everything"""
        # Background
        draw_background()
        update_snow()

        # Draw Sans
        screen.blit(self.sans_sprite, (WIDTH // 2 - 60, 60))

        # Draw enemy HP bar (if visible)
        if self.state != STATE_INTRO:
            # Enemy name
            name_text = font_dialogue.render(self.enemy.name, True, WHITE)
            screen.blit(name_text, (WIDTH // 2 - name_text.get_width() // 2, 30))

            # HP bar
            bar_width = 200
            bar_x = WIDTH // 2 - bar_width // 2
            bar_y = 210
            pygame.draw.rect(screen, (100, 0, 0), (bar_x, bar_y, bar_width, 15))
            hp_ratio = self.enemy.hp / self.enemy.max_hp
            pygame.draw.rect(screen, GREEN, (bar_x, bar_y, int(bar_width * hp_ratio), 15))
            pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, 15), 2)

        # Draw damage numbers
        if self.damage_timer > 0:
            alpha = min(255, self.damage_timer * 4)
            damage_surf = font_damage.render(self.damage_text, True, RED)
            damage_surf.set_alpha(alpha)
            screen.blit(damage_surf, (self.damage_x - 10, self.damage_y))

        # STATE-SPECIFIC DRAWING
        if self.state == STATE_INTRO:
            self.dialogue.draw(screen)

        elif self.state == STATE_MENU:
            self.menu.draw(screen, self.player)

        elif self.state in [STATE_FIGHT, STATE_ACT, STATE_ITEM, STATE_MERCY, STATE_DIALOGUE]:
            self.menu.draw(screen, self.player)
            self.dialogue.draw(screen)

        elif self.state == STATE_ENEMY_TURN:
            self.menu.draw(screen, self.player)
            self.battle_box.draw(screen)
            self.attack_pattern.draw(screen)
            self.soul.draw(screen)

            # Draw invincibility indicator
            if self.player.inv_frames > 0 and self.player.inv_frames % 10 < 5:
                inv_text = font_small.render("INVINCIBLE", True, CYAN)
                screen.blit(inv_text, (WIDTH // 2 - 50, HEIGHT - 130))

        elif self.state == STATE_VICTORY:
            screen.fill(BLACK)
            victory_text = font_large.render("YOU WON!", True, YELLOW)
            screen.blit(victory_text, (WIDTH // 2 - victory_text.get_width() // 2, HEIGHT // 2 - 50))

            restart_text = font_dialogue.render("Press R to restart", True, WHITE)
            screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 20))

        elif self.state == STATE_GAME_OVER:
            screen.fill(BLACK)
            death_text = font_large.render("YOU DIED", True, RED)
            screen.blit(death_text, (WIDTH // 2 - death_text.get_width() // 2, HEIGHT // 2 - 50))

            restart_text = font_dialogue.render("Press R to restart", True, WHITE)
            screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 20))

# ========================
# MAIN LOOP
# ========================

def main():
    clock = pygame.time.Clock()
    game = BattleGame()
    running = True

    while running:
        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            game.handle_input(event)

        # Update
        game.update()

        # Draw
        game.draw()

        # Display
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
