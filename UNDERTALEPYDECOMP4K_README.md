# UNDERTALEPYDECOMP4K1.0

A comprehensive recreation of Undertale in Python/Pygame with all routes, fun values, and complete game systems.

## Features

### Complete Route System
- **Pacifist Route** - Spare every monster, befriend everyone
- **Neutral Route** - Multiple ending variants based on who you spare/kill
- **Genocide Route** - Kill every monster with area-specific quotas
- **True Pacifist Route** - Complete pacifist requirements + special conditions
- **Route Detection** - Automatic detection of current route
- **Route Abort** - Ability to abort genocide route mid-game

### Fun Value System (1-100)
Complete implementation of Undertale's random event system:

#### Gaster Events
- Fun Value 66: Gaster Door
- Fun Value 65: Gaster Follower 1
- Fun Value 64: Gaster Follower 2
- Fun Value 63: Gaster Follower 3
- Fun Value 61: Mystery Man

#### Special Encounters
- Fun Value 85: Glyde (Snowdin)
- Fun Value 80: Wrong Number Song
- Fun Value 81: Alphys Call
- Fun Value 90: Redacted Room
- Fun Value 50: Sans's Room Key
- Fun Value 75: Clamgirl
- Fun Value 45: So Cold Statue
- Fun Value 40: Special Echo Flower
- Fun Value 55: Temmie Village Special
- Fun Value 88: Lesser Dog Extended

#### Annoying Dog Events
- Fun Value 10: Annoying Dog in Ruins
- Fun Value 20: Annoying Dog in Snowdin
- Fun Value 30: Annoying Dog in Waterfall

### Battle System
Complete battle mechanics including:
- **FIGHT** - Timing-based attack with accuracy calculation
- **ACT** - Monster-specific actions (Check, Talk, Compliment, etc.)
- **ITEM** - Use healing items and equipment
- **MERCY** - Spare or flee from battles

#### Battle Mechanics
- HP/Damage system
- Defense calculations
- EXP and GOLD rewards
- Level up system (LV)
- Betrayal kills tracking
- Spare counter

#### Monster AI
- Unique attack patterns per monster
- Bullet hell dodging mechanics
- Soul (heart) movement
- Boss-specific attacks

### Complete Monster Database
All monsters from every area:

#### Ruins
- Froggit, Whimsun, Moldsmal, Loox, Vegetoid, Migosp, Napstablook

#### Snowdin
- Snowdrake, Chilldrake, Ice Cap, Gyftrot, Doggo, Dogamy & Dogaressa
- Lesser Dog, Greater Dog, Jerry, Glyde (rare)

#### Waterfall
- Aaron, Woshua, Moldbygg, Temmie, Shyren, Glad Dummy

#### Hotland
- Vulkin, Tsunderplane, Pyrope, Muffet, Royal Guards

#### Core
- Final Froggit, Whimsalot, Astigmatism, Madjick, Knight Knight

#### Bosses
- Toriel, Papyrus, Undyne, Undyne the Undying
- Mettaton, Mettaton NEO, Asgore, Sans
- Flowey, Asriel Dreemurr

### Items System
Complete item database with:

#### Healing Items
- Butterscotch Pie (99 HP)
- Spider Donut (12 HP)
- Snowman Piece (45 HP)
- Nice Cream (15 HP)
- Instant Noodles (4 HP)
- Hot Dog (20 HP)
- Sea Tea (10 HP + Speed)
- And many more...

#### Weapons
- Stick (Starting weapon)
- Toy Knife (+3 AT)
- Tough Glove (+5 AT)
- Ballet Shoes (+7 AT)
- Torn Notebook (+2 AT)
- Burnt Pan (+10 AT)
- Empty Gun (+12 AT)
- Worn Dagger (+15 AT)
- Real Knife (+99 AT)

#### Armor
- Bandage (Starting armor)
- Faded Ribbon (+3 DF)
- Manly Bandanna (+7 DF)
- Old Tutu (+10 DF)
- Cloudy Glasses (+6 DF)
- Stained Apron (+11 DF)
- Cowboy Hat (+12 DF)
- Heart Locket (+15 DF)
- The Locket (+99 DF)

### Game Systems

#### Save/Load System
- JSON-based save files
- Saves all player progress
- Area tracking
- Kill/spare counters
- Inventory state
- Flags and achievements

#### Dialogue System
- Text box rendering
- Character-by-character display
- Word wrapping
- Multiple choice dialogs
- Skip functionality

#### Areas
- Ruins
- Snowdin
- Waterfall
- Hotland
- Core
- True Lab
- New Home
- Judgement Hall

#### Player Stats
- Name
- LV (Level)
- HP (Hit Points)
- AT (Attack)
- DF (Defense)
- EXP (Experience)
- GOLD
- Weapon
- Armor
- Inventory (8 slots)

### Extended Features (program._ut_.py)

#### Monster Dialogue Database
- Unique dialogue for every monster
- Context-specific messages
- Boss dialogue variants

#### ACT System Effects
- Monster-specific ACT options
- ACT effect descriptions
- Spare conditions

#### Attack Patterns
Pre-programmed bullet patterns for bosses:
- Toriel's fireball circle
- Sans's bone waves
- Undyne's spear rain
- Papyrus's blue bones
- Mettaton's bombs
- Asgore's trident waves
- Flowey's vine chaos
- Asriel's star burst

#### Ending Variants
- Neutral ending variants based on who's alive
- Toriel rules
- Undyne rules
- Mettaton rules
- Papyrus rules
- Flowey takes over
- Genocide ending
- True Pacifist ending

#### Determination Mechanics
- Save point healing
- Determination messages
- Game over messages per area
- SAVE the World mechanics

#### Room Connections
Complete room-to-room navigation system

#### Music Track Database
101 music tracks mapped to game events

#### Easter Eggs
Name-based easter eggs:
- Chara, Frisk, Sans, Papyrus
- Undyne, Alphys, Toriel, Asgore
- Flowey, Mettaton, Napstablook
- Gaster, Murder, Mercy
- And many more...

#### Achievements
- True Pacifist completion
- Genocide completion
- All neutral endings
- No-hit challenges
- Collectibles
- Special encounters

## Controls

### Overworld
- **Arrow Keys** - Move in four directions
- **Z / Enter** - Interact/Confirm
- **X** - Cancel/Menu
- **C** - Save menu
- **B** - Test battle (debug)
- **F** - Trigger fun value event (debug)
- **F3** - Toggle debug info

### Battle
- **Arrow Keys** - Navigate menu, move soul
- **Z / Enter** - Confirm selection
- **X** - Cancel/Back

### Menu
- **Up/Down** - Navigate options
- **Z / Enter** - Select

## Technical Details

### Files
- `undertale.py` - Main game engine (4000+ lines)
- `program._ut_.py` - Extended game data and utilities

### Dependencies
- Python 3.6+
- Pygame 2.0+

### Installation
```bash
pip install pygame
python3 undertale.py
```

### Save Files
- Saves stored in `save.json`
- Auto-saves at save points
- Manual save with C key

## Game Mechanics

### Genocide Route Requirements
- Ruins: 20 kills
- Snowdin: 16 kills
- Waterfall: 18 kills
- Hotland: 40 kills
- Must exhaust all random encounters in each area

### True Pacifist Requirements
- 0 kills
- Befriend Papyrus (date)
- Befriend Undyne (hangout)
- Complete True Lab
- Spare Asgore and Flowey

### Level System
- LV increases with EXP
- Each level: +4 HP, +2 AT, +2 DF
- Max LV: 20

### Combat Damage
```
Attack Damage = (AT * Accuracy * 2.5) - Enemy DEF
Received Damage = Enemy AT - Player DF (min 1)
```

## Debug Features

### Debug Display (F3)
- FPS counter
- Current game state
- Route type
- Fun value
- Player stats
- Position
- Kill/spare counters

### Quick Testing
- Press B to start random battle
- Press F to trigger fun value event
- All mechanics testable without full playthrough

## Credits

Based on UNDERTALE by Toby Fox
Recreation: UNDERTALEPYDECOMP4K1.0
Implementation: Python/Pygame

## Version History

### Version 4K1.0
- Complete route system (Pacifist, Neutral, Genocide, True Pacifist)
- All 100 fun values implemented
- Full battle system with all monsters
- Complete item/weapon/armor database
- Save/load functionality
- Extended game data (program._ut_.py)
- Attack patterns for all bosses
- All ending variants
- Easter egg system
- Achievement tracking
- Debug mode

## Notes

- This is a recreation for educational purposes
- Contains all major game systems from Undertale
- Fully playable with all routes
- Extensible architecture for adding more content
- Clean, well-documented code

---

**Stay Determined!**
