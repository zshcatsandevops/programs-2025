# Ultra Mario 2D Bros - Complete SMB1 Recreation

A complete recreation of Super Mario Bros 1 with all 32 levels, featuring pygame mixer music system and Team Level Up assets support.

## Features

- **All 32 Levels**: Every level from World 1-1 to World 8-4
- **Complete Music System**: Pygame mixer OST for each level theme
  - Overworld theme
  - Underground theme
  - Castle theme
  - Underwater theme
  - Star power theme
  - Level complete music
  - Game over music
- **Main Menu**: Full menu system with level select
- **Classic Gameplay**:
  - Mario physics (running, jumping, power-ups)
  - Enemy system (Goombas, Koopas)
  - Power-ups (Mushroom, Fire Flower, Star)
  - Blocks (Question blocks, Brick blocks)
  - Pipes
  - Coins and scoring
- **Multiple Power States**:
  - Small Mario
  - Super Mario
  - Fire Mario
  - Star Mario (invincibility)

## Installation

### Requirements

- Python 3.7 or higher
- Pygame 2.0 or higher

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Setup Assets

The game supports Team Level Up assets. Create the following directory structure:

```
assets/
├── music/
│   ├── overworld.ogg
│   ├── underground.ogg
│   ├── underwater.ogg
│   ├── castle.ogg
│   ├── starman.ogg
│   ├── level_clear.ogg
│   ├── game_over.ogg
│   ├── world_clear.ogg
│   └── title.ogg
├── sounds/
│   ├── jump.ogg
│   ├── coin.ogg
│   ├── powerup.ogg
│   ├── powerup_appears.ogg
│   ├── stomp.ogg
│   ├── kick.ogg
│   ├── pipe.ogg
│   ├── fireball.ogg
│   ├── bump.ogg
│   ├── break_block.ogg
│   ├── flagpole.ogg
│   ├── death.ogg
│   └── 1up.ogg
└── graphics/
    └── (sprite sheets and images)
```

**Note**: The game will run without assets using colored rectangles as placeholders. Add Team Level Up assets or any Mario assets to enhance the visual and audio experience.

## How to Run

```bash
python program.py
```

Or make it executable:

```bash
chmod +x program.py
./program.py
```

## Controls

### Gameplay
- **Arrow Keys / WASD** - Move left/right
- **Space / Up Arrow / W** - Jump
- **ESC** - Pause game
- **R** - Restart current level
- **N** - Skip to next level (for testing)

### Menu Navigation
- **Up/Down Arrows** - Navigate menu
- **Enter** - Confirm selection
- **ESC** - Go back

## Game Structure

### All 32 Levels

#### World 1
- 1-1: Classic overworld level
- 1-2: Underground level
- 1-3: Tree platforms level
- 1-4: Castle level

#### World 2
- 2-1: Overworld with more enemies
- 2-2: Underground level
- 2-3: Tree platforms level
- 2-4: Castle level

#### World 3
- 3-1 through 3-4: Progressive difficulty

#### World 4
- 4-1 through 4-4: Progressive difficulty

#### World 5
- 5-1 through 5-4: Progressive difficulty

#### World 6
- 6-1 through 6-4: Progressive difficulty

#### World 7
- 7-1 through 7-4: Progressive difficulty

#### World 8 (Final World)
- 8-1 through 8-4: Maximum difficulty, final castle with Bowser

### Music Mapping

Each level plays appropriate music based on theme:
- **Overworld levels**: Main theme (1-1, 2-1, 3-1, etc.)
- **Underground levels**: Underground theme (1-2, 2-2, etc.)
- **Tree/Platform levels**: Main theme variations (1-3, 2-3, etc.)
- **Castle levels**: Castle theme (1-4, 2-4, 3-4, 4-4, 5-4, 6-4, 7-4, 8-4)
- **Star Power**: Special invincibility music
- **Level Complete**: Victory fanfare

## Code Structure

### Main Classes

- **Game**: Main game controller and loop
- **Mario**: Player character with physics and power states
- **Level**: Level data and entity management
- **Enemy**: Enemy base class (Goombas, Koopas)
- **PowerUp**: Power-up items (Mushroom, Fire Flower, Star)
- **Platform**: Ground, blocks, and obstacles
- **Camera**: Scrolling camera system
- **MusicManager**: Complete pygame.mixer music and sound system

### Game States

- **MENU**: Main menu
- **PLAYING**: Active gameplay
- **PAUSED**: Game paused
- **GAME_OVER**: Player lost all lives
- **LEVEL_COMPLETE**: Level finished successfully
- **WORLD_COMPLETE**: All 4 levels in world complete

## Development

### Adding New Levels

Levels are defined in `create_all_levels()` method with:
- World number (1-8)
- Level number (1-4)
- Music track
- Theme (overworld, underground, castle, underwater)
- Time limit

Each level has a `load_world_X_Y()` method for custom layouts.

### Adding Music

1. Place music files in `assets/music/` as .ogg format
2. Update `MusicManager.tracks` dictionary with file paths
3. Assign track to level in `LevelData`

### Adding Sound Effects

1. Place sound files in `assets/sounds/` as .ogg format
2. Update `MusicManager.load_sounds()` with sound names
3. Call `music_manager.play_sound('sound_name')` where needed

## Features Implemented

- ✅ All 32 levels structure
- ✅ Pygame mixer music system
- ✅ Main menu with level select
- ✅ Mario physics and controls
- ✅ Power-up system
- ✅ Enemy system
- ✅ Collision detection
- ✅ Camera scrolling
- ✅ Score tracking
- ✅ Lives system
- ✅ Game states management
- ✅ HUD display

## Customization

### Change Colors
Edit the color constants at the top of `program.py`

### Adjust Physics
Modify these constants:
- `GRAVITY` - Falling acceleration
- `JUMP_STRENGTH` - Jump power
- `MOVE_SPEED` - Horizontal movement speed
- `MAX_FALL_SPEED` - Terminal velocity

### Screen Size
Change `SCREEN_WIDTH` and `SCREEN_HEIGHT` constants

## Credits

- Game Engine: Pygame
- Original Game: Nintendo (Super Mario Bros)
- Assets Support: Team Level Up (assets not included)
- Code: Ultra Mario 2D Bros Project

## License

See LICENSE file for details.

## Notes

This is a recreation for educational purposes. Super Mario Bros is a trademark of Nintendo.
The game framework supports Team Level Up assets or any compatible sprite sheets and music files.

Enjoy playing all 32 levels!
