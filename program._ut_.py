"""
program._ut_.py
Support module for UNDERTALEPYDECOMP4K1.0
Contains extended game data, utilities, and special mechanics
"""

import random
from typing import Dict, List, Tuple

# ============================================================================
# EXTENDED MONSTER DATA
# ============================================================================

MONSTER_DIALOGUE = {
    "Froggit": [
        "* Froggit doesn't seem to know why it's here.",
        "* Froggit hops to and fro.",
        "* The battlefield is filled with the smell of mustard seed.",
        "* Froggit looks nervous."
    ],
    "Whimsun": [
        "* Whimsun approached meekly!",
        "* Whimsun is trying to muster courage...",
        "* Whimsun continues to mutter apologies.",
    ],
    "Moldsmal": [
        "* Moldsmal wavers around.",
        "* Moldsmal burbles intensely!",
        "* Moldsmal has started to spoil."
    ],
    "Loox": [
        "* Loox stares at you.",
        "* Loox gazes at you.",
        "* Don't pick on Loox!"
    ],
    "Napstablook": [
        "* oh no...",
        "* i'm in the way, aren't i?",
        "* this is really cool...",
        "* ........................................"
    ],
    "Sans": [
        "* you're gonna have a bad time.",
        "* get dunked on!!!",
        "* heh heh heh heh heh...",
        "* what? you think i'm just gonna stand there and take it?"
    ],
    "Papyrus": [
        "* NYEH HEH HEH!",
        "* I, THE GREAT PAPYRUS, WILL CAPTURE YOU!",
        "* WOWIE!!!",
    ],
    "Undyne": [
        "* Undyne attacks with everything she's got!",
        "* Undyne's eye is twitching.",
        "* Undyne is smiling as if nothing is wrong.",
    ],
    "Undyne the Undying": [
        "* The heroine appears.",
        "* Undyne the Undying draws her spear.",
        "* You feel your sins crawling on your back.",
    ],
    "Mettaton": [
        "* OH YESSSS!",
        "* Mettaton does a sexy attack!",
        "* The audience goes wild!",
    ],
    "Mettaton NEO": [
        "* Mettaton NEO attacks!",
        "* Mettaton NEO is powering up.",
        "* It's the most powerful robot in the Underground.",
    ],
    "Toriel": [
        "* Toriel checks if you are hurt.",
        "* Toriel is acting aloof.",
        "* Toriel prepares a magical attack.",
        "* The smell of butterscotch and cinnamon fills the air.",
    ],
    "Asgore": [
        "* Asgore offers you a cup of tea.",
        "* Asgore takes a deep breath.",
        "* Asgore prepares a devastating attack.",
        "* ASGORE's SOUL power is too strong for mercy!",
    ],
    "Flowey": [
        "* You idiot.",
        "* In this world, it's kill or BE killed.",
        "* Die.",
    ],
    "Asriel Dreemurr": [
        "* Asriel is preparing something...",
        "* Asriel is trying to finish the job.",
        "* Asriel is using his full power!",
    ],
}

MONSTER_ACT_EFFECTS = {
    "Froggit": {
        "Compliment": "You compliment Froggit. Its jumping becomes more enthusiastic. Can be spared.",
        "Threaten": "You threaten Froggit. It runs away!",
    },
    "Whimsun": {
        "Encourage": "You encourage Whimsun. It flutters happily. Can be spared.",
        "Terrorize": "Whimsun runs away, hoping you'll leave it alone!",
    },
    "Napstablook": {
        "Cheer": "You cheer on Napstablook. It seems a little happier.",
        "Flirt": "You flirt with Napstablook. It says 'oh no...'",
    },
    "Toriel": {
        "Talk": "You talk to Toriel. She seems to calm down.",
        "Plead": "You plead with Toriel. She remembers someone else...",
        "Spare": "Toriel stops attacking after enough attempts.",
    },
    "Papyrus": {
        "Flirt": "You flirt with Papyrus. He doesn't know what that means!",
        "Insult": "You insult Papyrus. He... doesn't understand insults.",
    },
    "Undyne": {
        "Challenge": "You challenge Undyne. She grins and attacks harder!",
        "Plead": "You plead with Undyne. She doesn't listen.",
    },
    "Sans": {
        "Check": "* The easiest enemy. Can only deal 1 damage.",
    },
}

# ============================================================================
# FUN VALUE EVENTS EXTENDED
# ============================================================================

FUN_EVENT_DIALOGUE = {
    "gaster_door": [
        "* (There's a poorly-drawn picture of a door here.)",
        "* (It seems like someone wanted to cover this up...)",
        "* (...)",
    ],
    "gaster_follower_1": [
        "* I'm holding a piece of him.",
        "* I wonder what he was like?",
        "* ...Have you ever thought about a world where everything is exactly the same...",
        "* ...Except you don't exist?",
        "* Everything functions perfectly without you.",
        "* Ha ha... The thought terrifies me.",
    ],
    "gaster_follower_2": [
        "* It makes sense why ASGORE is waiting to wage war.",
        "* He's waiting for a massive power-up.",
        "* A human has to die, right?",
        "* With their SOUL, ASGORE can cross the barrier.",
        "* He would be the greatest monarch of all time.",
        "* But ASGORE hates this plan.",
    ],
    "gaster_follower_3": [
        "* he's watching...",
        "* he's listening...",
        "* but nobody came.",
    ],
    "mystery_man": [
        "* ...",
        "* . . .",
        "* ... ... ...",
    ],
    "wrong_number_song": [
        "* (You dial the number.)",
        "* Hello! You've reached the wrong number! Song Request Line!",
        "* (Catchy music plays)",
    ],
    "clamgirl": [
        "* Hello! I'd like to tell you about my neighbor's daughter.",
        "* She's a very sweet girl, about your age.",
        "* I think you two would make great friends.",
        "* Her name is...",
        "* ...",
        "* ...",
        "* Suzy.",
        "* ...",
        "* You'll meet her someday.",
    ],
    "glyde_special": [
        "* Glyde has appeared!",
        "* This is a rare encounter!",
    ],
    "temmie_secret": [
        "* hOI!",
        "* i'm temmie!",
        "* and dis is my friend... temmie!",
        "* hOI!",
    ],
    "sans_secret": [
        "* you're watching me sleep?",
        "* ...that's kinda creepy, kiddo.",
    ],
}

# ============================================================================
# ATTACK PATTERNS
# ============================================================================

class AttackPatterns:
    """Pre-defined bullet patterns for bosses"""

    @staticmethod
    def toriel_fireball_circle(center_x, center_y, num_bullets=8):
        """Toriel's circular fireball pattern"""
        bullets = []
        for i in range(num_bullets):
            angle = (i / num_bullets) * 2 * 3.14159
            import math
            vx = math.cos(angle) * 3
            vy = math.sin(angle) * 3
            bullets.append({
                'x': center_x,
                'y': center_y,
                'vx': vx,
                'vy': vy,
                'type': 'fire'
            })
        return bullets

    @staticmethod
    def sans_bone_wave(start_y, direction='left'):
        """Sans's bone wave pattern"""
        bullets = []
        for i in range(10):
            bullets.append({
                'x': 640 if direction == 'left' else 0,
                'y': start_y + i * 8,
                'vx': -6 if direction == 'left' else 6,
                'vy': 0,
                'type': 'bone'
            })
        return bullets

    @staticmethod
    def undyne_spear_rain(num_spears=15):
        """Undyne's spear rain pattern"""
        bullets = []
        for i in range(num_spears):
            bullets.append({
                'x': random.randint(100, 540),
                'y': 0,
                'vx': 0,
                'vy': random.uniform(4, 7),
                'type': 'spear'
            })
        return bullets

    @staticmethod
    def papyrus_bone_pattern():
        """Papyrus's blue bone pattern"""
        bullets = []
        # Top row
        for i in range(8):
            bullets.append({
                'x': 100 + i * 60,
                'y': 280,
                'vx': 0,
                'vy': 0,
                'type': 'blue_bone'
            })
        # Bottom row
        for i in range(8):
            bullets.append({
                'x': 130 + i * 60,
                'y': 400,
                'vx': 0,
                'vy': 0,
                'type': 'blue_bone'
            })
        return bullets

    @staticmethod
    def mettaton_bomb_pattern(num_bombs=8):
        """Mettaton's bomb pattern"""
        bullets = []
        for i in range(num_bombs):
            bullets.append({
                'x': random.randint(100, 540),
                'y': random.randint(280, 400),
                'vx': 0,
                'vy': 0,
                'type': 'bomb',
                'timer': 60  # 2 seconds
            })
        return bullets

    @staticmethod
    def asgore_trident_wave():
        """Asgore's trident wave pattern"""
        bullets = []
        for i in range(5):
            bullets.append({
                'x': 100 + i * 110,
                'y': 280,
                'vx': 0,
                'vy': 4,
                'type': 'trident',
                'color': 'orange' if i % 2 == 0 else 'blue'
            })
        return bullets

    @staticmethod
    def flowey_vine_chaos():
        """Flowey's chaotic vine pattern"""
        bullets = []
        for i in range(20):
            bullets.append({
                'x': random.randint(80, 560),
                'y': random.randint(260, 420),
                'vx': random.uniform(-3, 3),
                'vy': random.uniform(-3, 3),
                'type': 'vine'
            })
        return bullets

    @staticmethod
    def asriel_star_burst(center_x, center_y):
        """Asriel's star burst pattern"""
        bullets = []
        for i in range(16):
            angle = (i / 16) * 2 * 3.14159
            import math
            vx = math.cos(angle) * 5
            vy = math.sin(angle) * 5
            bullets.append({
                'x': center_x,
                'y': center_y,
                'vx': vx,
                'vy': vy,
                'type': 'rainbow_star'
            })
        return bullets

# ============================================================================
# SPECIAL ENCOUNTERS
# ============================================================================

SPECIAL_ENCOUNTERS = {
    "so_sorry": {
        "name": "So Sorry",
        "hp": 1100,
        "at": 9,
        "df": 6,
        "gold": 300,
        "exp": 0,
        "condition": "October 10th, 8pm",
    },
    "glyde": {
        "name": "Glyde",
        "hp": 220,
        "at": 9,
        "df": 5,
        "gold": 120,
        "exp": 100,
        "condition": "Fun Value 85, Snowdin Forest",
    },
    "mad_dummy": {
        "name": "Mad Dummy",
        "hp": 200,
        "at": 10,
        "df": 255,
        "gold": 0,
        "exp": 0,
        "condition": "Waterfall",
    },
}

# ============================================================================
# ENDING VARIANTS
# ============================================================================

ENDING_VARIANTS = {
    "neutral_toriel_alive": {
        "condition": {"toriel_killed": False, "kills": ">0"},
        "phone_call": "Toriel becomes the new queen.",
    },
    "neutral_toriel_dead_undyne_alive": {
        "condition": {"toriel_killed": True, "undyne_killed": False},
        "phone_call": "Undyne becomes the new queen.",
    },
    "neutral_everyone_dead": {
        "condition": {"kills": ">20"},
        "phone_call": "A flower has taken over the Underground.",
    },
    "neutral_mettaton_rules": {
        "condition": {"mettaton_alive": True, "undyne_killed": True},
        "phone_call": "Mettaton becomes the new king.",
    },
    "neutral_papyrus_rules": {
        "condition": {"papyrus_alive": True, "kills": "==0"},
        "phone_call": "Papyrus becomes the new king!",
    },
    "genocide": {
        "condition": {"route": "genocide", "kills": ">=100"},
        "ending": "* But nobody came.",
    },
    "true_pacifist": {
        "condition": {"kills": "==0", "dated_all": True},
        "ending": "You break the barrier. Everyone is free.",
    },
}

# ============================================================================
# DETERMINATION MECHANICS
# ============================================================================

class DeterminationMechanics:
    """Special mechanics for DETERMINATION"""

    @staticmethod
    def save_point_heal(player):
        """Heal player at save point"""
        player.hp = player.max_hp
        return "* The power of fluffy boys shines within you."

    @staticmethod
    def check_determination_level(player):
        """Get determination message based on player state"""
        if player.hp == player.max_hp:
            return "* You are filled with DETERMINATION."
        elif player.hp > player.max_hp * 0.5:
            return "* You are filled with determination."
        else:
            return "* Despite everything, it's still you."

    @staticmethod
    def game_over_messages(area):
        """Get game over message based on area"""
        messages = {
            "RUINS": "* You cannot give up just yet...\n* Frisk! Stay determined...",
            "SNOWDIN": "* You cannot give up just yet...\n* Frisk! Stay determined...",
            "WATERFALL": "* You cannot give up just yet...\n* Frisk! Stay determined...",
            "HOTLAND": "* You cannot give up just yet...\n* Frisk! Stay determined...",
            "CORE": "* You cannot give up just yet...\n* Frisk! Stay determined...",
        }
        return messages.get(area, "* You cannot give up just yet...")

# ============================================================================
# FLAVOR TEXT DATABASE
# ============================================================================

FLAVOR_TEXT = {
    "check_froggit": "* FROGGIT - ATK 4 DEF 4\n* Life is difficult for this enemy.",
    "check_whimsun": "* WHIMSUN - ATK 5 DEF 0\n* This monster is too sensitive for this world.",
    "check_napstablook": "* NAPSTABLOOK - ATK 10 DEF 255\n* This ghost doesn't seem to have a sense of humor.",
    "check_toriel": "* TORIEL - ATK 6 DEF 4\n* Knows best for you.",
    "check_sans": "* SANS - ATK 1 DEF 1\n* The easiest enemy.\n* Can only deal 1 damage.",
    "check_papyrus": "* PAPYRUS - ATK 8 DEF 2\n* He likes to say 'NYEH HEH HEH!'",
    "check_undyne": "* UNDYNE - ATK 10 DEF 5\n* The heroine that NEVER gives up.",
    "check_undyne_undying": "* UNDYNE THE UNDYING - ATK 12 DEF 5\n* The heroine that NEVER gives up.",
    "check_mettaton": "* METTATON - ATK 10 DEF 6\n* Everyone's favorite TV star!",
    "check_mettaton_neo": "* METTATON NEO - ATK 10 DEF -40000\n* The form he always dreamed of.",
    "check_asgore": "* ASGORE - ATK 10 DEF 8\n* The king of the Underground.",
    "check_flowey": "* FLOWEY - ATK 9 DEF 0\n* Don't let his friendly smile fool you.",
    "check_asriel": "* ASRIEL DREEMURR - ATK 8 DEF 8\n* ...",
}

# ============================================================================
# ROOM TRANSITIONS
# ============================================================================

ROOM_CONNECTIONS = {
    # Ruins
    "ruins_start": {"south": "ruins_02", "north": None},
    "ruins_02": {"north": "ruins_start", "south": "ruins_03", "east": "ruins_02e"},
    "ruins_03": {"north": "ruins_02", "south": "ruins_toriel_home"},
    "ruins_toriel_home": {"north": "ruins_03", "south": "ruins_exit"},
    "ruins_exit": {"north": "ruins_toriel_home", "south": "snowdin_start"},

    # Snowdin
    "snowdin_start": {"north": "ruins_exit", "south": "snowdin_town"},
    "snowdin_forest": {"north": "snowdin_start", "south": "snowdin_town", "east": "snowdin_secret"},
    "snowdin_town": {"north": "snowdin_forest", "south": "snowdin_exit", "west": "sans_house"},
    "snowdin_exit": {"north": "snowdin_town", "south": "waterfall_start"},

    # Waterfall
    "waterfall_start": {"north": "snowdin_exit", "south": "waterfall_02"},
    "waterfall_02": {"north": "waterfall_start", "south": "waterfall_undyne", "east": "temmie_village"},
    "waterfall_undyne": {"north": "waterfall_02", "south": "waterfall_exit"},
    "waterfall_exit": {"north": "waterfall_undyne", "south": "hotland_start"},

    # Hotland
    "hotland_start": {"north": "waterfall_exit", "south": "hotland_lab"},
    "hotland_lab": {"north": "hotland_start", "south": "hotland_resort"},
    "hotland_resort": {"north": "hotland_lab", "south": "core_start"},

    # Core
    "core_start": {"north": "hotland_resort", "south": "core_elevator"},
    "core_elevator": {"north": "core_start", "south": "new_home"},

    # New Home
    "new_home": {"north": "core_elevator", "south": "throne_room"},
    "throne_room": {"north": "new_home", "south": "barrier"},
}

# ============================================================================
# MUSIC TRACKS
# ============================================================================

MUSIC_TRACKS = {
    "Once Upon a Time": "ruins_start",
    "Your Best Friend": "flowey_encounter",
    "Fallen Down": "toriel_home",
    "Ruins": "ruins_general",
    "Anticipation": "before_toriel",
    "Unnecessary Tension": "fake_battle",
    "Enemy Approaching": "random_encounter",
    "Ghost Fight": "napstablook",
    "Determination": "save_point",
    "Home": "toriel_house",
    "Heartache": "toriel_boss",
    "Snowy": "snowdin",
    "Uwa!! So Temperate": "snowing",
    "Dogbass": "dog_encounters",
    "Mysterious Place": "mysterious",
    "Dogsong": "lesser_dog",
    "Snowdin Town": "snowdin_town",
    "Shop": "shop",
    "Bonetrousle": "papyrus_encounter",
    "Dating Start!": "papyrus_date",
    "Dating Tense!": "date_intense",
    "Dating Fight!": "date_fight",
    "Premonition": "something_bad",
    "Danger Mystery": "more_mysterious",
    "Undyne": "undyne_chase",
    "Waterfall": "waterfall_area",
    "Run!": "run_away",
    "Quiet Water": "quiet_waterfall",
    "Memory": "memory_scene",
    "Bird That Carries You Over A Disproportionately Small Gap": "bird",
    "Dummy!": "mad_dummy",
    "Pathetic House": "napstablook_house",
    "Spooktune": "ghost_music",
    "Spookwave": "ghost_music_2",
    "Ghouliday": "ghost_music_3",
    "Chill": "napstablook_chill",
    "Thundersnail": "thundersnail_game",
    "Temmie Village": "temmie_area",
    "Tem Shop": "temmie_shop",
    "NGAHHH!!": "undyne_encounter",
    "Spear of Justice": "undyne_battle",
    "Ooo": "woshua",
    "It's Showtime!": "mettaton_intro",
    "Metal Crusher": "mettaton_battle",
    "Another Medium": "hotland",
    "Uwa!! So Holiday": "hotland_remix",
    "Alphys Takes Action": "alphys_action",
    "Alphys": "alphys_theme",
    "She's Playing Piano": "undyne_piano",
    "Here We Are": "true_lab",
    "Amalgam": "amalgamates",
    "Fallen Down (Reprise)": "memory_reprise",
    "Don't Give Up": "asriel_save",
    "Hopes and Dreams": "asriel_battle",
    "Burn in Despair!": "asriel_intense",
    "SAVE the World": "save_everyone",
    "His Theme": "asriel_sad",
    "Final Power": "asriel_final",
    "Reunited": "happy_ending",
    "Menu (Full)": "menu_screen",
    "Respite": "geno_save",
    "Bring It In, Guys!": "true_pacifist_end",
    "Last Goodbye": "credits",
    "But the Earth Refused to Die": "undying",
    "Battle Against a True Hero": "undyne_undying",
    "Power of NEO": "mettaton_neo",
    "MEGALOVANIA": "sans_battle",
    "Song That Might Play When You Fight Sans": "unused_sans",
    "The Choice": "final_choice",
    "Small Shock": "slight_surprise",
    "Barrier": "the_barrier",
    "Bergentrückung": "asgore_intro",
    "ASGORE": "asgore_battle",
    "You Idiot": "flowey_reveal",
    "Your Best Nightmare": "photoshop_flowey",
    "Finale": "flowey_finale",
    "An Ending": "neutral_end",
    "She's Watching": "new_home_walk",
    "Core Approach": "approaching_core",
    "CORE": "core_area",
    "Last Episode!": "mettaton_ex",
    "Oh! One True Love": "mettaton_musical",
    "Oh! Dungeon": "mettaton_quiz",
    "It's Raining Somewhere Else": "sans_dinner",
    "Death by Glamour": "mettaton_ex_battle",
    "For the Fans": "mettaton_stage",
    "Long Elevator": "long_elevator",
    "Undertale": "undertale_main",
    "Song that Might Play When You Fight Sans": "sans_unused",
    "The Legend": "opening_story",
    "Good Night": "sleep",
    "Confession": "confession_time",
}

# ============================================================================
# EASTER EGGS
# ============================================================================

EASTER_EGGS = {
    "name_chara": "The true name.",
    "name_frisk": "WARNING: This name will make your life hell.",
    "name_asriel": "...",
    "name_sans": "nope.",
    "name_papyrus": "I'LL ALLOW IT!",
    "name_undyne": "Get your OWN name!",
    "name_alphys": "D... don't do that.",
    "name_toriel": "I think you should think of your own name, my child.",
    "name_asgore": "You cannot.",
    "name_flowey": "I already CHOSE that name.",
    "name_mettaton": "OOOH!!! ARE YOU PROMOTING MY BRAND?",
    "name_napstablook": "............... (They're powerless to stop you.)",
    "name_murder": "Hee hee hee.",
    "name_mercy": "What a wonderful name!",
    "name_gaster": "[REDACTED]",
    "name_catty": "Bratty! Bratty! That's MY name!",
    "name_bratty": "Like, OK I guess.",
    "name_temmie": "hOI!",
    "name_jerry": "Jerry.",
    "name_aaron": ";)",
    "name_woshua": "Wosh u SOUL",
    "name_shyren": "...?",
}

# ============================================================================
# ACHIEVEMENTS / FLAGS
# ============================================================================

ACHIEVEMENTS = {
    "true_pacifist": "Completed True Pacifist Route",
    "genocide": "Completed Genocide Route",
    "all_neutral": "Saw all Neutral endings",
    "no_hit_sans": "Defeated Sans without getting hit",
    "no_hit_undyne": "Defeated Undyne the Undying without getting hit",
    "found_gaster": "Found the Mystery Man",
    "tem_shop": "Bought from Temmie Shop",
    "dog_residue": "Found the Dog Residue",
    "annoying_dog": "Met the Annoying Dog",
    "hacker_ending": "Got the hacker ending",
    "speed_run": "Completed game in under 2 hours",
    "all_items": "Collected all items",
    "max_gold": "Reached 9999 G",
    "all_phone_calls": "Got all phone calls",
}

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'MONSTER_DIALOGUE',
    'MONSTER_ACT_EFFECTS',
    'FUN_EVENT_DIALOGUE',
    'AttackPatterns',
    'SPECIAL_ENCOUNTERS',
    'ENDING_VARIANTS',
    'DeterminationMechanics',
    'FLAVOR_TEXT',
    'ROOM_CONNECTIONS',
    'MUSIC_TRACKS',
    'EASTER_EGGS',
    'ACHIEVEMENTS',
]

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_monster_dialogue(monster_name, index=None):
    """Get random or specific dialogue for a monster"""
    if monster_name not in MONSTER_DIALOGUE:
        return f"* {monster_name} attacks!"

    dialogue_list = MONSTER_DIALOGUE[monster_name]
    if index is not None and 0 <= index < len(dialogue_list):
        return dialogue_list[index]

    return random.choice(dialogue_list)

def get_act_effect(monster_name, act_name):
    """Get the effect text for an ACT"""
    if monster_name in MONSTER_ACT_EFFECTS:
        if act_name in MONSTER_ACT_EFFECTS[monster_name]:
            return MONSTER_ACT_EFFECTS[monster_name][act_name]
    return f"* You use {act_name} on {monster_name}."

def get_flavor_text(check_id):
    """Get flavor text for CHECK command"""
    return FLAVOR_TEXT.get(check_id, "* No information available.")

def check_easter_egg(name):
    """Check if name triggers an easter egg"""
    name_lower = name.lower()
    for egg_key, egg_text in EASTER_EGGS.items():
        if egg_key.replace("name_", "") == name_lower:
            return egg_text
    return None

def get_ending_type(player_state):
    """Determine which ending variant to show"""
    for ending_name, ending_data in ENDING_VARIANTS.items():
        conditions = ending_data["condition"]
        # Check conditions
        all_met = True
        for key, value in conditions.items():
            if key in player_state:
                player_value = player_state[key]
                if isinstance(value, str):
                    if value.startswith("=="):
                        if player_value != int(value[2:]):
                            all_met = False
                    elif value.startswith(">"):
                        if player_value <= int(value[1:]):
                            all_met = False
                else:
                    if player_value != value:
                        all_met = False

        if all_met:
            return ending_name

    return "neutral_generic"

def calculate_karma_damage(attack_value, defense_value, karma_level):
    """Calculate damage with KARMA effect (for Sans fight)"""
    base_damage = max(1, attack_value - defense_value)
    karma_damage = karma_level * 0.5
    return base_damage + karma_damage

def get_room_connection(current_room, direction):
    """Get the connected room in a direction"""
    if current_room in ROOM_CONNECTIONS:
        return ROOM_CONNECTIONS[current_room].get(direction, None)
    return None

# ============================================================================
# DEBUG UTILITIES
# ============================================================================

def print_game_stats():
    """Print comprehensive game statistics"""
    print("\n" + "="*60)
    print("UNDERTALEPYDECOMP4K1.0 - GAME DATA STATISTICS")
    print("="*60)
    print(f"Monster Dialogue Entries: {len(MONSTER_DIALOGUE)}")
    print(f"Monster ACT Effects: {len(MONSTER_ACT_EFFECTS)}")
    print(f"Fun Event Dialogues: {len(FUN_EVENT_DIALOGUE)}")
    print(f"Special Encounters: {len(SPECIAL_ENCOUNTERS)}")
    print(f"Ending Variants: {len(ENDING_VARIANTS)}")
    print(f"Flavor Text Entries: {len(FLAVOR_TEXT)}")
    print(f"Room Connections: {len(ROOM_CONNECTIONS)}")
    print(f"Music Tracks: {len(MUSIC_TRACKS)}")
    print(f"Easter Eggs: {len(EASTER_EGGS)}")
    print(f"Achievements: {len(ACHIEVEMENTS)}")
    print("="*60)

if __name__ == "__main__":
    print_game_stats()
