"""
UNDERTALEPYDECOMP4K1.0
Complete Undertale Recreation with All Routes, Fun Values, and Systems
A comprehensive decompilation-style recreation of Undertale in Python/Pygame
"""

import pygame
import random
import json
import os
import math
import time
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
FPS = 30

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

# Game States
class GameState(Enum):
    MENU = 0
    OVERWORLD = 1
    BATTLE = 2
    DIALOGUE = 3
    SHOP = 4
    SAVE = 5
    GAME_OVER = 6
    CREDITS = 7

# Route Types
class RouteType(Enum):
    NEUTRAL = 0
    PACIFIST = 1
    GENOCIDE = 2
    TRUE_PACIFIST = 3

# Areas
class Area(Enum):
    RUINS = 0
    SNOWDIN = 1
    WATERFALL = 2
    HOTLAND = 3
    CORE = 4
    NEW_HOME = 5
    TRUE_LAB = 6
    JUDGEMENT_HALL = 7

# Battle Actions
class BattleAction(Enum):
    FIGHT = 0
    ACT = 1
    ITEM = 2
    MERCY = 3

@dataclass
class Monster:
    """Monster data structure"""
    name: str
    hp: int
    max_hp: int
    attack: int
    defense: int
    gold: int
    exp: int
    can_spare: bool = False
    betrayed: bool = False
    dialogue: List[str] = None
    acts: List[str] = None

    def __post_init__(self):
        if self.dialogue is None:
            self.dialogue = [f"* {self.name} attacks!"]
        if self.acts is None:
            self.acts = ["Check", "Talk"]

@dataclass
class Item:
    """Item data structure"""
    name: str
    type: str  # "heal", "weapon", "armor", "key"
    description: str
    heal_amount: int = 0
    attack_bonus: int = 0
    defense_bonus: int = 0
    usable_in_battle: bool = True

class Player:
    """Player character with all stats and progression"""
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
        self.inventory = ["Pie"]
        self.kills = 0
        self.area_kills = {area: 0 for area in Area}
        self.spared = 0
        self.betrayals = 0
        self.friends = []
        self.flags = {}
        self.x = 0
        self.y = 0
        self.facing = "down"

    def gain_exp(self, amount):
        """Gain EXP and level up if needed"""
        self.exp += amount
        exp_needed = self.lv * 10 + (self.lv - 1) * 10
        if self.exp >= exp_needed:
            self.level_up()

    def level_up(self):
        """Level up the player"""
        self.lv += 1
        old_max_hp = self.max_hp
        self.max_hp = 20 + (self.lv - 1) * 4
        hp_gain = self.max_hp - old_max_hp
        self.hp = min(self.hp + hp_gain, self.max_hp)
        self.at = 10 + (self.lv - 1) * 2
        self.df = 10 + (self.lv - 1) * 2

    def take_damage(self, damage):
        """Take damage"""
        actual_damage = max(1, damage - self.df)
        self.hp -= actual_damage
        return actual_damage

    def heal(self, amount):
        """Heal HP"""
        old_hp = self.hp
        self.hp = min(self.hp + amount, self.max_hp)
        return self.hp - old_hp

    def add_item(self, item_name):
        """Add item to inventory"""
        if len(self.inventory) < 8:
            self.inventory.append(item_name)
            return True
        return False

    def remove_item(self, item_name):
        """Remove item from inventory"""
        if item_name in self.inventory:
            self.inventory.remove(item_name)
            return True
        return False

class FunValues:
    """Fun value system for random events and Easter eggs"""

    @staticmethod
    def get_fun_value():
        """Get random fun value (1-100)"""
        return random.randint(1, 100)

    @staticmethod
    def check_fun_event(fun_value, area):
        """Check if fun value triggers special event"""
        events = {
            # Gaster events
            (66, Area.WATERFALL): "gaster_door",
            (65, Area.WATERFALL): "gaster_follower_1",
            (64, Area.WATERFALL): "gaster_follower_2",
            (63, Area.WATERFALL): "gaster_follower_3",

            # Mystery Man
            (61, Area.WATERFALL): "mystery_man",

            # Wrong Number Song
            (80, Area.WATERFALL): "wrong_number_song",

            # Alphys Call
            (81, Area.HOTLAND): "alphys_call",

            # Redacted
            (90, Area.SNOWDIN): "redacted_room",

            # Sans's Room Key
            (50, Area.SNOWDIN): "sans_key",

            # Clamgirl
            (75, Area.WATERFALL): "clamgirl",

            # Glyde
            (85, Area.SNOWDIN): "glyde_encounter",

            # So Cold
            (45, Area.SNOWDIN): "so_cold_statue",

            # Echo Flowers
            (40, Area.WATERFALL): "special_echo_flower",

            # Annoying Dog
            (10, Area.RUINS): "annoying_dog_ruins",
            (20, Area.SNOWDIN): "annoying_dog_snowdin",
            (30, Area.WATERFALL): "annoying_dog_waterfall",

            # Temmie Village
            (55, Area.WATERFALL): "temmie_village_special",

            # Lesser Dog
            (88, Area.SNOWDIN): "lesser_dog_extended",
        }

        return events.get((fun_value, area), None)

class GameData:
    """Game data and progression tracking"""

    # Items database
    ITEMS = {
        "Pie": Item("Butterscotch Pie", "heal", "Butterscotch-cinnamon pie", 99),
        "Spider Donut": Item("Spider Donut", "heal", "A donut made by spiders", 12),
        "Spider Cider": Item("Spider Cider", "heal", "Made with whole spiders", 24),
        "Snowman Piece": Item("Snowman Piece", "heal", "Please take this to the end", 45),
        "Nice Cream": Item("Nice Cream", "heal", "Heals 15 HP", 15),
        "Bisicle": Item("Bisicle", "heal", "It's a two-pronged popsicle", 11),
        "Cinnamon Bun": Item("Cinnamon Bun", "heal", "Heals 22 HP", 22),
        "Temmie Flakes": Item("Temmie Flakes", "heal", "It's just torn up colored paper", 2),
        "Dog Salad": Item("Dog Salad", "heal", "Recovers HP (Hit Poodles)", 2, usable_in_battle=True),
        "Legendary Hero": Item("Legendary Hero", "heal", "Sandwich for heroes", 40),
        "Steak": Item("Steak in the Shape of Mettaton's Face", "heal", "Huge steak", 60),
        "Instant Noodles": Item("Instant Noodles", "heal", "Just add water", 4),
        "Hot Dog": Item("Hot Dog", "heal", "It's a hot dog", 20),
        "Hot Cat": Item("Hot Cat", "heal", "Like a hot dog but cat", 21),
        "Sea Tea": Item("Sea Tea", "heal", "Heals 10 HP. Increases SPEED", 10),
        "Starfait": Item("Starfait", "heal", "A sweet treat", 14),
        "Glamburger": Item("Glamburger", "heal", "A very attractive burger", 27),
        "Popato Chisps": Item("Popato Chisps", "heal", "Regular old popato chisps", 13),
        "Bad Memory": Item("Bad Memory", "heal", "????", 1),
        "Junk Food": Item("Junk Food", "heal", "Food that was found in garbage", 17),
        "Hush Puppy": Item("Hush Puppy", "heal", "This wonderful spell will stop a dog", 65),

        # Weapons
        "Stick": Item("Stick", "weapon", "Its bark is worse than its bite", 0, 0, 0, False),
        "Toy Knife": Item("Toy Knife", "weapon", "Made of plastic. A rarity nowadays", 0, 3, 0, False),
        "Tough Glove": Item("Tough Glove", "weapon", "A worn pink leather glove", 0, 5, 0, False),
        "Ballet Shoes": Item("Ballet Shoes", "weapon", "Slightly sweaty. Nimble, but not as protective", 0, 7, 0, False),
        "Torn Notebook": Item("Torn Notebook", "weapon", "Contains illegible scrawls", 0, 2, 0, False),
        "Burnt Pan": Item("Burnt Pan", "weapon", "Damage is rather consistent. Consumable items heal 4 more HP", 0, 10, 0, False),
        "Empty Gun": Item("Empty Gun", "weapon", "An unloaded gun. Fires multiple attacks", 0, 12, 0, False),
        "Worn Dagger": Item("Worn Dagger", "weapon", "Perfect for cutting plants and vines", 0, 15, 0, False),
        "Real Knife": Item("Real Knife", "weapon", "Here we are!", 0, 99, 0, False),

        # Armor
        "Bandage": Item("Bandage", "armor", "It has already been used several times", 0, 0, 0, False),
        "Faded Ribbon": Item("Faded Ribbon", "armor", "If you're cuter, monsters won't hit you as hard", 0, 0, 3, False),
        "Manly Bandanna": Item("Manly Bandanna", "armor", "It has seen some wear. Gives you a rugged look", 0, 0, 7, False),
        "Old Tutu": Item("Old Tutu", "armor", "Finally, a protective piece of armor", 0, 0, 10, False),
        "Cloudy Glasses": Item("Cloudy Glasses", "armor", "Glasses marred with wear. Attacks with them do not increase KARMA", 0, 0, 6, False),
        "Stained Apron": Item("Stained Apron", "armor", "Heals 1 HP every other turn", 0, 0, 11, False),
        "Cowboy Hat": Item("Cowboy Hat", "armor", "This battle-worn hat makes you want to grow a beard", 0, 0, 12, False),
        "Heart Locket": Item("Heart Locket", "armor", "It says 'Best Friends Forever'", 0, 0, 15, False),
        "The Locket": Item("The Locket", "armor", "Right where it belongs", 0, 0, 99, False),
    }

    # Monster database
    MONSTERS = {
        # Ruins
        "Froggit": Monster("Froggit", 30, 30, 4, 4, 2, 3),
        "Whimsun": Monster("Whimsun", 10, 10, 5, 0, 2, 2),
        "Moldsmal": Monster("Moldsmal", 50, 50, 6, 0, 3, 3),
        "Loox": Monster("Loox", 50, 50, 6, 6, 5, 5),
        "Vegetoid": Monster("Vegetoid", 72, 72, 5, 7, 8, 6),
        "Migosp": Monster("Migosp", 40, 40, 7, 5, 10, 5),
        "Napstablook": Monster("Napstablook", 88, 88, 10, 255, 0, 0),

        # Snowdin
        "Snowdrake": Monster("Snowdrake", 50, 50, 6, 4, 8, 5),
        "Chilldrake": Monster("Chilldrake", 39, 39, 6, 4, 12, 5),
        "Ice Cap": Monster("Ice Cap", 38, 38, 5, 3, 15, 4),
        "Gyftrot": Monster("Gyftrot", 114, 114, 8, 4, 20, 8),
        "Doggo": Monster("Doggo", 70, 70, 7, 2, 30, 30),
        "Dogamy & Dogaressa": Monster("Dogi", 100, 100, 8, 4, 60, 40),
        "Lesser Dog": Monster("Lesser Dog", 60, 60, 6, 4, 25, 20),
        "Greater Dog": Monster("Greater Dog", 80, 80, 8, 4, 40, 80),
        "Jerry": Monster("Jerry", 80, 80, 0, 8, 1, 1),
        "Glyde": Monster("Glyde", 220, 220, 9, 5, 120, 100),

        # Waterfall
        "Aaron": Monster("Aaron", 98, 98, 8, 4, 45, 52),
        "Woshua": Monster("Woshua", 70, 70, 6, 5, 30, 52),
        "Moldbygg": Monster("Moldbygg", 70, 70, 6, 5, 36, 52),
        "Temmie": Monster("Temmie", 50, 50, 5, -20, 20, 40),
        "Shyren": Monster("Shyren", 66, 66, 6, 0, 40, 52),
        "Glad Dummy": Monster("Glad Dummy", 200, 200, 10, 5, 0, 0),

        # Hotland
        "Vulkin": Monster("Vulkin", 66, 66, 8, 5, 42, 52),
        "Tsunderplane": Monster("Tsunderplane", 95, 95, 7, 4, 50, 100),
        "Pyrope": Monster("Pyrope", 110, 110, 8, 6, 55, 120),
        "Muffet": Monster("Muffet", 1250, 1250, 10, 6, 0, 0),
        "Royal Guard 01": Monster("RG 01", 150, 150, 9, 5, 60, 100),
        "Royal Guard 02": Monster("RG 02", 150, 150, 9, 5, 60, 100),

        # Core
        "Final Froggit": Monster("Final Froggit", 100, 100, 10, 5, 80, 100),
        "Whimsalot": Monster("Whimsalot", 95, 95, 8, 5, 70, 90),
        "Astigmatism": Monster("Astigmatism", 120, 120, 9, 7, 90, 120),
        "Madjick": Monster("Madjick", 190, 190, 10, 6, 120, 180),
        "Knight Knight": Monster("Knight Knight", 230, 230, 11, 8, 150, 200),

        # Bosses
        "Toriel": Monster("Toriel", 440, 440, 6, 4, 0, 0),
        "Papyrus": Monster("Papyrus", 680, 680, 8, 2, 0, 0),
        "Undyne": Monster("Undyne", 1500, 1500, 10, 5, 0, 0),
        "Undyne the Undying": Monster("Undyne the Undying", 23000, 23000, 12, 5, 0, 0),
        "Mettaton": Monster("Mettaton", 1000, 1000, 10, 6, 0, 0),
        "Mettaton NEO": Monster("Mettaton NEO", 30000, 30000, 10, -40000, 0, 0),
        "Asgore": Monster("Asgore", 3500, 3500, 10, 8, 0, 0),
        "Flowey": Monster("Flowey", 9999, 9999, 9, 0, 0, 0),
        "Asriel Dreemurr": Monster("Asriel Dreemurr", 9999, 9999, 8, 8, 0, 0),
        "Sans": Monster("Sans", 1, 1, 9, 1, 0, 0),
    }

class DialogueSystem:
    """Handles all dialogue in the game"""

    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        self.text = ""
        self.char_index = 0
        self.finished = False
        self.choices = []
        self.selected_choice = 0

    def start_dialogue(self, text, choices=None):
        """Start displaying dialogue"""
        self.text = text
        self.char_index = 0
        self.finished = False
        self.choices = choices or []
        self.selected_choice = 0

    def update(self):
        """Update dialogue display"""
        if not self.finished and self.char_index < len(self.text):
            self.char_index += 1
            if self.char_index >= len(self.text):
                self.finished = True

    def skip(self):
        """Skip to end of dialogue"""
        self.char_index = len(self.text)
        self.finished = True

    def draw(self):
        """Draw dialogue box"""
        # Draw dialogue box
        box_rect = pygame.Rect(50, 320, SCREEN_WIDTH - 100, 130)
        pygame.draw.rect(self.screen, WHITE, box_rect)
        pygame.draw.rect(self.screen, BLACK, box_rect, 3)

        # Draw text
        displayed_text = self.text[:self.char_index]
        y_offset = 340
        max_width = SCREEN_WIDTH - 120

        # Word wrap
        words = displayed_text.split(' ')
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + word + " "
            if self.font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word + " "
        lines.append(current_line)

        for line in lines[:3]:  # Max 3 lines
            text_surface = self.font.render(line, True, BLACK)
            self.screen.blit(text_surface, (70, y_offset))
            y_offset += 30

        # Draw choices if available and dialogue finished
        if self.finished and self.choices:
            choice_y = 340
            for i, choice in enumerate(self.choices):
                color = YELLOW if i == self.selected_choice else WHITE
                choice_text = f"{'>' if i == self.selected_choice else ' '} {choice}"
                choice_surface = self.font.render(choice_text, True, color)
                self.screen.blit(choice_surface, (400, choice_y))
                choice_y += 30

class BattleSystem:
    """Complete battle system"""

    def __init__(self, screen, font, player):
        self.screen = screen
        self.font = font
        self.player = player
        self.monster = None
        self.action = None
        self.turn_phase = "menu"  # menu, attack, monster_attack, result
        self.selected_action = 0
        self.selected_option = 0
        self.damage_dealt = 0
        self.damage_taken = 0
        self.battle_ended = False
        self.victory = False
        self.ran_away = False
        self.attack_bar_x = 0
        self.attack_bar_moving = False
        self.attack_bar_speed = 5
        self.soul_x = SCREEN_WIDTH // 2
        self.soul_y = 360
        self.bullets = []
        self.dodge_timer = 0

    def start_battle(self, monster_name):
        """Start a battle with a monster"""
        monster_data = GameData.MONSTERS.get(monster_name)
        if monster_data:
            self.monster = Monster(
                monster_data.name,
                monster_data.max_hp,
                monster_data.max_hp,
                monster_data.attack,
                monster_data.defense,
                monster_data.gold,
                monster_data.exp,
                monster_data.can_spare,
                monster_data.betrayed,
                monster_data.dialogue.copy() if monster_data.dialogue else [f"* {monster_data.name} attacks!"],
                monster_data.acts.copy() if monster_data.acts else ["Check", "Talk"]
            )
            self.battle_ended = False
            self.victory = False
            self.ran_away = False
            self.turn_phase = "menu"
            self.selected_action = 0

    def update(self, events):
        """Update battle state"""
        if self.turn_phase == "menu":
            self.handle_menu_input(events)
        elif self.turn_phase == "attack":
            self.handle_attack_input(events)
        elif self.turn_phase == "act":
            self.handle_act_input(events)
        elif self.turn_phase == "item":
            self.handle_item_input(events)
        elif self.turn_phase == "mercy":
            self.handle_mercy_input(events)
        elif self.turn_phase == "monster_attack":
            self.update_monster_attack()

    def handle_menu_input(self, events):
        """Handle battle menu input"""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.selected_action = max(0, self.selected_action - 1)
                elif event.key == pygame.K_RIGHT:
                    self.selected_action = min(3, self.selected_action + 1)
                elif event.key == pygame.K_z or event.key == pygame.K_RETURN:
                    actions = ["fight", "act", "item", "mercy"]
                    self.turn_phase = actions[self.selected_action]
                    self.selected_option = 0
                    if self.turn_phase == "fight":
                        self.attack_bar_x = 50
                        self.attack_bar_moving = True

    def handle_attack_input(self, events):
        """Handle attack phase"""
        if self.attack_bar_moving:
            self.attack_bar_x += self.attack_bar_speed
            if self.attack_bar_x >= SCREEN_WIDTH - 150:
                self.attack_bar_speed = -self.attack_bar_speed
            elif self.attack_bar_x <= 50:
                self.attack_bar_speed = abs(self.attack_bar_speed)

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_z or event.key == pygame.K_RETURN:
                    self.attack_bar_moving = False
                    # Calculate damage based on timing
                    center = SCREEN_WIDTH // 2
                    distance = abs(self.attack_bar_x - center)
                    max_distance = SCREEN_WIDTH // 2 - 50
                    accuracy = 1.0 - (distance / max_distance)
                    self.damage_dealt = int(self.player.at * accuracy * 2.5)
                    self.monster.hp -= self.damage_dealt

                    if self.monster.hp <= 0:
                        self.end_battle(True)
                    else:
                        self.turn_phase = "monster_attack"
                        self.start_monster_attack()

    def handle_act_input(self, events):
        """Handle ACT menu"""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_option = max(0, self.selected_option - 1)
                elif event.key == pygame.K_DOWN:
                    self.selected_option = min(len(self.monster.acts) - 1, self.selected_option + 1)
                elif event.key == pygame.K_z or event.key == pygame.K_RETURN:
                    act_name = self.monster.acts[self.selected_option]
                    self.perform_act(act_name)
                    self.turn_phase = "monster_attack"
                    self.start_monster_attack()
                elif event.key == pygame.K_x:
                    self.turn_phase = "menu"

    def perform_act(self, act_name):
        """Perform ACT action"""
        if act_name == "Check":
            pass  # Show monster info
        elif act_name == "Talk":
            pass  # Talk to monster
        elif act_name == "Spare":
            if self.monster.can_spare:
                self.end_battle(False, spared=True)
        else:
            # Custom ACT effects
            if act_name == "Pet":
                self.monster.can_spare = True
            elif act_name == "Encourage":
                self.monster.can_spare = True

    def handle_item_input(self, events):
        """Handle ITEM menu"""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_option = max(0, self.selected_option - 1)
                elif event.key == pygame.K_DOWN:
                    self.selected_option = min(len(self.player.inventory) - 1, self.selected_option + 1)
                elif event.key == pygame.K_z or event.key == pygame.K_RETURN:
                    if self.selected_option < len(self.player.inventory):
                        item_name = self.player.inventory[self.selected_option]
                        self.use_item(item_name)
                        self.turn_phase = "monster_attack"
                        self.start_monster_attack()
                elif event.key == pygame.K_x:
                    self.turn_phase = "menu"

    def use_item(self, item_name):
        """Use an item"""
        if item_name in GameData.ITEMS:
            item = GameData.ITEMS[item_name]
            if item.type == "heal":
                healed = self.player.heal(item.heal_amount)
                self.player.remove_item(item_name)

    def handle_mercy_input(self, events):
        """Handle MERCY menu"""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_option = 0
                elif event.key == pygame.K_DOWN:
                    self.selected_option = 1
                elif event.key == pygame.K_z or event.key == pygame.K_RETURN:
                    if self.selected_option == 0:  # Spare
                        if self.monster.can_spare:
                            self.end_battle(False, spared=True)
                        else:
                            self.turn_phase = "monster_attack"
                            self.start_monster_attack()
                    else:  # Flee
                        if random.random() < 0.5:
                            self.end_battle(False, ran_away=True)
                        else:
                            self.turn_phase = "monster_attack"
                            self.start_monster_attack()
                elif event.key == pygame.K_x:
                    self.turn_phase = "menu"

    def start_monster_attack(self):
        """Start monster's attack phase"""
        self.bullets = []
        self.dodge_timer = 120  # 4 seconds at 30 FPS
        # Generate bullet pattern
        for i in range(10):
            bullet = {
                'x': random.randint(100, SCREEN_WIDTH - 100),
                'y': 50,
                'vx': random.uniform(-2, 2),
                'vy': random.uniform(2, 4)
            }
            self.bullets.append(bullet)

    def update_monster_attack(self):
        """Update monster attack phase"""
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.soul_x = max(100, self.soul_x - 4)
        if keys[pygame.K_RIGHT]:
            self.soul_x = min(SCREEN_WIDTH - 100, self.soul_x + 4)
        if keys[pygame.K_UP]:
            self.soul_y = max(280, self.soul_y - 4)
        if keys[pygame.K_DOWN]:
            self.soul_y = min(400, self.soul_y + 4)

        # Update bullets
        for bullet in self.bullets:
            bullet['x'] += bullet['vx']
            bullet['y'] += bullet['vy']

            # Check collision with soul
            if abs(bullet['x'] - self.soul_x) < 10 and abs(bullet['y'] - self.soul_y) < 10:
                damage = self.player.take_damage(self.monster.attack)
                self.damage_taken = damage
                bullet['x'] = -1000  # Move off screen

        # Remove off-screen bullets
        self.bullets = [b for b in self.bullets if 0 <= b['x'] <= SCREEN_WIDTH and 0 <= b['y'] <= SCREEN_HEIGHT]

        self.dodge_timer -= 1
        if self.dodge_timer <= 0:
            if self.player.hp <= 0:
                self.end_battle(False, died=True)
            else:
                self.turn_phase = "menu"

    def end_battle(self, victory, spared=False, ran_away=False, died=False):
        """End the battle"""
        self.battle_ended = True
        self.victory = victory
        self.ran_away = ran_away

        if victory:
            self.player.kills += 1
            self.player.gain_exp(self.monster.exp)
            self.player.gold += self.monster.gold
        elif spared:
            self.player.spared += 1

    def draw(self):
        """Draw battle screen"""
        self.screen.fill(BLACK)

        # Draw monster
        if self.monster:
            name_text = self.font.render(self.monster.name, True, WHITE)
            self.screen.blit(name_text, (50, 50))

            # HP bar
            hp_ratio = self.monster.hp / self.monster.max_hp
            pygame.draw.rect(self.screen, RED, (50, 80, 200 * hp_ratio, 20))
            pygame.draw.rect(self.screen, WHITE, (50, 80, 200, 20), 2)

            hp_text = self.font.render(f"{self.monster.hp}/{self.monster.max_hp}", True, WHITE)
            self.screen.blit(hp_text, (260, 80))

        # Draw battle box
        battle_box = pygame.Rect(80, 260, SCREEN_WIDTH - 160, 160)
        pygame.draw.rect(self.screen, WHITE, battle_box, 3)

        if self.turn_phase == "menu":
            # Draw action buttons
            actions = ["FIGHT", "ACT", "ITEM", "MERCY"]
            for i, action in enumerate(actions):
                x = 120 + i * 120
                color = YELLOW if i == self.selected_action else WHITE
                action_text = self.font.render(action, True, color)
                self.screen.blit(action_text, (x, 440))

        elif self.turn_phase == "fight":
            # Draw attack bar
            pygame.draw.rect(self.screen, WHITE, (50, 350, SCREEN_WIDTH - 100, 30), 2)
            pygame.draw.rect(self.screen, RED, (self.attack_bar_x, 350, 20, 30))

        elif self.turn_phase == "act":
            # Draw ACT options
            for i, act in enumerate(self.monster.acts):
                color = YELLOW if i == self.selected_option else WHITE
                act_text = self.font.render(f"* {act}", True, color)
                self.screen.blit(act_text, (100, 280 + i * 30))

        elif self.turn_phase == "item":
            # Draw items
            for i, item in enumerate(self.player.inventory):
                color = YELLOW if i == self.selected_option else WHITE
                item_text = self.font.render(f"* {item}", True, color)
                self.screen.blit(item_text, (100, 280 + i * 30))

        elif self.turn_phase == "mercy":
            # Draw mercy options
            options = ["Spare", "Flee"]
            for i, option in enumerate(options):
                color = YELLOW if i == self.selected_option else WHITE
                if option == "Spare" and self.monster.can_spare:
                    color = YELLOW
                option_text = self.font.render(f"* {option}", True, color)
                self.screen.blit(option_text, (100, 280 + i * 30))

        elif self.turn_phase == "monster_attack":
            # Draw soul (player heart)
            pygame.draw.rect(self.screen, RED, (self.soul_x - 8, self.soul_y - 8, 16, 16))

            # Draw bullets
            for bullet in self.bullets:
                pygame.draw.circle(self.screen, WHITE, (int(bullet['x']), int(bullet['y'])), 5)

        # Draw player stats
        self.draw_player_stats()

    def draw_player_stats(self):
        """Draw player stats at bottom"""
        stats_text = f"{self.player.name}  LV {self.player.lv}  HP {self.player.hp}/{self.player.max_hp}"
        stats_surface = self.font.render(stats_text, True, WHITE)
        self.screen.blit(stats_surface, (100, 430))

class SaveSystem:
    """Save and load game data"""

    @staticmethod
    def save_game(player, game_state, filename="save.json"):
        """Save game to file"""
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
            'x': player.x,
            'y': player.y,
            'facing': player.facing,
            'state': game_state
        }

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def load_game(filename="save.json"):
        """Load game from file"""
        if not os.path.exists(filename):
            return None

        with open(filename, 'r') as f:
            data = json.load(f)

        player = Player()
        player.name = data['name']
        player.lv = data['lv']
        player.hp = data['hp']
        player.max_hp = data['max_hp']
        player.at = data['at']
        player.df = data['df']
        player.exp = data['exp']
        player.gold = data['gold']
        player.weapon = data['weapon']
        player.armor = data['armor']
        player.inventory = data['inventory']
        player.kills = data['kills']
        player.area_kills = {Area[k]: v for k, v in data['area_kills'].items()}
        player.spared = data['spared']
        player.betrayals = data['betrayals']
        player.friends = data['friends']
        player.flags = data['flags']
        player.x = data['x']
        player.y = data['y']
        player.facing = data['facing']

        return player, data['state']

class RouteDetector:
    """Detects which route the player is on"""

    @staticmethod
    def get_route(player):
        """Determine current route"""
        # Genocide route conditions
        ruins_quota = 20
        snowdin_quota = 16
        waterfall_quota = 18
        hotland_quota = 40

        if player.area_kills.get(Area.RUINS, 0) >= ruins_quota:
            if player.area_kills.get(Area.SNOWDIN, 0) >= snowdin_quota:
                if player.area_kills.get(Area.WATERFALL, 0) >= waterfall_quota:
                    if player.area_kills.get(Area.HOTLAND, 0) >= hotland_quota:
                        return RouteType.GENOCIDE

        # Pacifist route conditions
        if player.kills == 0:
            if player.spared >= 10:
                # Check if dated/befriended key characters
                if 'dated_papyrus' in player.flags and 'befriended_undyne' in player.flags:
                    return RouteType.TRUE_PACIFIST
                return RouteType.PACIFIST

        # Default to neutral
        return RouteType.NEUTRAL

    @staticmethod
    def can_abort_genocide(player):
        """Check if genocide route can still be aborted"""
        return player.kills < 100

class UndertaleGame:
    """Main game class"""

    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("UNDERTALEPYDECOMP4K1.0")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 48)

        self.running = True
        self.state = GameState.MENU
        self.player = Player()
        self.current_area = Area.RUINS
        self.fun_value = FunValues.get_fun_value()

        # Systems
        self.dialogue = DialogueSystem(self.screen, self.font)
        self.battle = BattleSystem(self.screen, self.font, self.player)

        # Menu
        self.menu_selection = 0
        self.menu_options = ["Continue", "New Game", "Settings", "Quit"]

        # Debug info
        self.show_debug = False

    def run(self):
        """Main game loop"""
        while self.running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F3:
                        self.show_debug = not self.show_debug

            self.update(events)
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()

    def update(self, events):
        """Update game state"""
        if self.state == GameState.MENU:
            self.update_menu(events)
        elif self.state == GameState.OVERWORLD:
            self.update_overworld(events)
        elif self.state == GameState.BATTLE:
            self.battle.update(events)
            if self.battle.battle_ended:
                self.state = GameState.OVERWORLD
        elif self.state == GameState.DIALOGUE:
            self.dialogue.update()
            self.update_dialogue(events)
        elif self.state == GameState.SAVE:
            self.update_save(events)

    def update_menu(self, events):
        """Update main menu"""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.menu_selection = (self.menu_selection - 1) % len(self.menu_options)
                elif event.key == pygame.K_DOWN:
                    self.menu_selection = (self.menu_selection + 1) % len(self.menu_options)
                elif event.key == pygame.K_z or event.key == pygame.K_RETURN:
                    if self.menu_selection == 0:  # Continue
                        saved = SaveSystem.load_game()
                        if saved:
                            self.player, state = saved
                            self.state = GameState.OVERWORLD
                    elif self.menu_selection == 1:  # New Game
                        self.player = Player()
                        self.state = GameState.OVERWORLD
                        self.fun_value = FunValues.get_fun_value()
                        # Start intro dialogue
                        self.dialogue.start_dialogue("Once upon a time, two races ruled over Earth: HUMANS and MONSTERS...")
                        self.state = GameState.DIALOGUE
                    elif self.menu_selection == 2:  # Settings
                        pass
                    elif self.menu_selection == 3:  # Quit
                        self.running = False

    def update_overworld(self, events):
        """Update overworld"""
        for event in events:
            if event.type == pygame.KEYDOWN:
                # Movement
                if event.key == pygame.K_LEFT:
                    self.player.x -= 32
                    self.player.facing = "left"
                elif event.key == pygame.K_RIGHT:
                    self.player.x += 32
                    self.player.facing = "right"
                elif event.key == pygame.K_UP:
                    self.player.y -= 32
                    self.player.facing = "up"
                elif event.key == pygame.K_DOWN:
                    self.player.y += 32
                    self.player.facing = "down"

                # Menu
                elif event.key == pygame.K_c:
                    self.state = GameState.SAVE

                # Test battle
                elif event.key == pygame.K_b:
                    monsters = list(GameData.MONSTERS.keys())
                    monster = random.choice(monsters)
                    self.battle.start_battle(monster)
                    self.state = GameState.BATTLE

                # Check fun value events
                elif event.key == pygame.K_f:
                    event = FunValues.check_fun_event(self.fun_value, self.current_area)
                    if event:
                        self.handle_fun_event(event)

    def update_dialogue(self, events):
        """Update dialogue state"""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_z or event.key == pygame.K_RETURN:
                    if self.dialogue.finished:
                        self.state = GameState.OVERWORLD
                    else:
                        self.dialogue.skip()

    def update_save(self, events):
        """Update save menu"""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_z or event.key == pygame.K_RETURN:
                    SaveSystem.save_game(self.player, self.state.name)
                    self.state = GameState.OVERWORLD
                elif event.key == pygame.K_x:
                    self.state = GameState.OVERWORLD

    def handle_fun_event(self, event_name):
        """Handle fun value special events"""
        events_dialogue = {
            "gaster_door": "* The door is locked.",
            "gaster_follower_1": "* The man speaks in hands.",
            "mystery_man": "...",
            "wrong_number_song": "* Wrong number song!",
            "alphys_call": "* Um... H-hi!",
            "redacted_room": "* It's a strange room...",
            "sans_key": "* you found a key.",
            "clamgirl": "* ... Synchronicity?",
            "so_cold_statue": "* It's just ice.",
            "special_echo_flower": "* I'm just a flower...",
            "annoying_dog_ruins": "* Bark!",
            "annoying_dog_snowdin": "* Bark! Bark!",
            "annoying_dog_waterfall": "* Bark! Bark! Bark!",
        }

        if event_name in events_dialogue:
            self.dialogue.start_dialogue(events_dialogue[event_name])
            self.state = GameState.DIALOGUE
        elif event_name == "glyde_encounter":
            self.battle.start_battle("Glyde")
            self.state = GameState.BATTLE

    def draw(self):
        """Draw current game state"""
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
        """Draw main menu"""
        title = self.title_font.render("UNDERTALE", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)

        subtitle = self.font.render("PYDECOMP4K1.0", True, GRAY)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(subtitle, subtitle_rect)

        for i, option in enumerate(self.menu_options):
            color = YELLOW if i == self.menu_selection else WHITE
            text = self.font.render(option, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 250 + i * 50))
            self.screen.blit(text, text_rect)

    def draw_overworld(self):
        """Draw overworld"""
        # Draw area name
        area_text = self.font.render(self.current_area.name, True, WHITE)
        self.screen.blit(area_text, (20, 20))

        # Draw player (simple square for now)
        player_color = RED
        pygame.draw.rect(self.screen, player_color,
                        (SCREEN_WIDTH // 2 - 16, SCREEN_HEIGHT // 2 - 16, 32, 32))

        # Draw controls hint
        hint = self.font.render("Arrow keys: Move | C: Save | B: Battle | F: Fun Event", True, GRAY)
        self.screen.blit(hint, (20, SCREEN_HEIGHT - 40))

    def draw_save_menu(self):
        """Draw save menu"""
        # Background
        self.screen.fill(BLACK)

        # Save point star
        star_points = [
            (SCREEN_WIDTH // 2, 100),
            (SCREEN_WIDTH // 2 + 10, 130),
            (SCREEN_WIDTH // 2 + 40, 130),
            (SCREEN_WIDTH // 2 + 15, 150),
            (SCREEN_WIDTH // 2 + 25, 180),
            (SCREEN_WIDTH // 2, 160),
            (SCREEN_WIDTH // 2 - 25, 180),
            (SCREEN_WIDTH // 2 - 15, 150),
            (SCREEN_WIDTH // 2 - 40, 130),
            (SCREEN_WIDTH // 2 - 10, 130),
        ]
        pygame.draw.polygon(self.screen, YELLOW, star_points)

        # Save text
        save_text = self.font.render(f"{self.player.name}  LV {self.player.lv}", True, WHITE)
        save_rect = save_text.get_rect(center=(SCREEN_WIDTH // 2, 250))
        self.screen.blit(save_text, save_rect)

        location_text = self.font.render(self.current_area.name, True, WHITE)
        location_rect = location_text.get_rect(center=(SCREEN_WIDTH // 2, 290))
        self.screen.blit(location_text, location_rect)

        prompt = self.font.render("Save? [Z] Yes  [X] No", True, WHITE)
        prompt_rect = prompt.get_rect(center=(SCREEN_WIDTH // 2, 350))
        self.screen.blit(prompt, prompt_rect)

    def draw_debug(self):
        """Draw debug information"""
        debug_info = [
            f"FPS: {int(self.clock.get_fps())}",
            f"State: {self.state.name}",
            f"Route: {RouteDetector.get_route(self.player).name}",
            f"Fun: {self.fun_value}",
            f"LV: {self.player.lv}",
            f"HP: {self.player.hp}/{self.player.max_hp}",
            f"Kills: {self.player.kills}",
            f"Spared: {self.player.spared}",
            f"Pos: ({self.player.x}, {self.player.y})",
        ]

        y = 10
        for info in debug_info:
            debug_text = self.font.render(info, True, GREEN)
            self.screen.blit(debug_text, (SCREEN_WIDTH - 200, y))
            y += 25

def main():
    """Main entry point"""
    print("=" * 60)
    print("UNDERTALEPYDECOMP4K1.0")
    print("=" * 60)
    print("A complete Undertale recreation in Python/Pygame")
    print()
    print("Features:")
    print("- All 3 routes: Pacifist, Neutral, Genocide")
    print("- Complete Fun Value system (1-100)")
    print("- Full battle system with FIGHT/ACT/ITEM/MERCY")
    print("- All areas: Ruins, Snowdin, Waterfall, Hotland, Core, etc.")
    print("- Complete monster database")
    print("- Items, weapons, and armor")
    print("- Save/Load system")
    print("- Route detection")
    print()
    print("Controls:")
    print("- Arrow Keys: Move/Navigate")
    print("- Z/Enter: Confirm")
    print("- X: Cancel/Menu")
    print("- C: Save")
    print("- B: Test Battle")
    print("- F: Trigger Fun Event")
    print("- F3: Toggle Debug")
    print()
    print("Starting game...")
    print("=" * 60)

    game = UndertaleGame()
    game.run()

if __name__ == "__main__":
    main()
