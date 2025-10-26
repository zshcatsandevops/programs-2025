# UNDERMARIO 1.0

A complete Undertale-style RPG engine built with Pygame, featuring turn-based combat, bullet-hell dodging mechanics, and an ACT system.

## Features

### Overworld Exploration
- **Free Movement**: Use arrow keys to explore the world
- **NPCs**: Interact with various characters (Luigi, Toad, Sans)
- **Beautiful Environment**: Trees, houses, and atmospheric backgrounds

### Battle System
- **Turn-Based Combat**: Classic RPG-style menu system
- **Four Actions**:
  - **FIGHT**: Deal damage to enemies
  - **ACT**: Use special actions to calm enemies
  - **ITEM**: Use items (coming soon!)
  - **MERCY**: Spare enemies when conditions are met

### SOUL Mechanics
- **Dodge Phase**: Control your SOUL (heart) to dodge enemy attacks
- **Unique Attack Patterns**:
  - **Fireballs** (Luigi): Explosive radial attacks
  - **Spores** (Toad): Falling projectiles
  - **Bones** (Sans): Fast horizontal/vertical patterns

### Enemy System
- **Stats**: HP, ATK, DEF for each enemy
- **ACT Options**: Multiple interaction choices per enemy
- **Spare Threshold**: Different conditions for mercy
- **Dynamic Difficulty**: Each enemy has unique challenge

## Controls

### Overworld
- **Arrow Keys**: Move your Goomba character
- **Space**: Interact with NPCs

### Battle Menu
- **Arrow Keys**: Navigate menus
- **Enter/Space**: Select option
- **ESC**: Go back (in ACT menu)

### Dodge Phase
- **Arrow Keys**: Move SOUL to dodge attacks
- Avoid all projectiles to survive the turn!

## Enemy Info

### Luigi Boss
- HP: 50 | ATK: 8 | DEF: 5
- Pattern: Fireball explosions
- Acts: Check, Talk, Compliment, Jump

### Toad Warrior
- HP: 35 | ATK: 6 | DEF: 8
- Pattern: Falling spores
- Acts: Check, Reassure, Help, Question

### Sans
- HP: 1 | ATK: 99 | DEF: 1
- Pattern: Bone attacks
- Acts: Check, Joke, Spare, Hug
- **Warning**: You're gonna have a bad time!

## Player Stats
- **Name**: Goomba
- **HP**: 20/20
- **ATK**: 10
- **DEF**: 10
- **LV**: 1

## Gameplay Tips

1. **Check First**: Use ACT → Check to learn enemy stats
2. **Build Mercy**: Use ACT options to make enemies spareable
3. **Watch Patterns**: Each enemy has predictable attack patterns
4. **Defense Matters**: Higher DEF reduces damage taken
5. **Spare When Yellow**: Enemy names turn spareable after enough ACT uses

## Technical Details

- **Engine**: Pygame
- **Resolution**: 640x480
- **FPS**: 60
- **Python Version**: 3.6+

## Installation

```bash
pip install pygame
python undermario.py
```

## Future Features
- Item system
- Multiple areas/rooms
- Save/Load functionality
- More enemies
- Boss battles
- Story progression
- Equipment system
- Level up mechanics

## Credits

Inspired by:
- **Undertale** by Toby Fox
- **Super Mario Bros** by Nintendo

Created as a demonstration of RPG game engine mechanics.

---

**Version**: 1.0
**Status**: Playable Demo
**License**: MIT
