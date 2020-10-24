# `./gb.py`

## Goals
- Full speed emulation of all Gameboy games in the standard Python interpreter (see [CPython vs PyPy](#cpython-vs-pypy))
- Code readability
- Accurate emulation is important but the previous two goals take priority

## CPython vs PyPy
Like a similar project (PyBoy), I found that CPython was far too slow for use with emulating even the Gameboy's 4MHz (!) processor. Even without the display, gpu, or other peripherials, I was experiencing a 3x slowdown over actual hardware on a 2.4GHz laptop.

Thus, I am developing `./gb.py` to a feature-complete state while using PyPy as the interpreter. Using PyPy, I can achieve real time gameplay — very helpful for running/test/debugging games! However, PyPy is not without its challenges.

For instance, PyPy's Python -> C interactions are orders of magnitude slower than CPython's. Because of this, I cannot render the display pixel-by-pixel with Pygame. Instead, I have to serialize the display to Pygame's internal byte representation in Python and then overwrite the interal frame buffer all at once to achieve acceptable speeds.

Now, of course one of my goals for this project is to emulate full speed in CPython. I plan to solve this after reaching a feature-complete state of emulation with the following optimizations:

- Independent subsystem execution
  - For many subsystems, the number of ticks until the next "interaction" can be calculated ahead of time. We can use this to skip the "step" function for these subsystems and only "step" when a meaning full state-change or interaction will occur.
- JITing to Python of common Z80 "idioms"
  - Building off of "independent subsystem execution", we can execute groups of common CPU instructions ("idioms") as higher level operations. Examples of these idioms include memcpy's, memcmp's, and wait loops for resource availability. I will discover more candidates as I profile the CPU execution.

## Playable games

Below are a list of *playable* games. Many experience [bugs](#bugs)!

- Dr. Mario
- Tetris
- Super Mario Land
- Kirby's Dreamland
- Pokemon Red

## Implemented functionality
- CPU
- MMU
- Cartridge/ROM support for MBC1 + partial MBC4
- GPU
- Display
- Serial output
- Internal timer
- Joypad

## Unimplemented (dis?)functionality
- Sound
- Bidirection serial cable
- External RAM
- External timer
- Full STAT and LCDC register/interrupt support
- "Display-on-CLI" support
- Save states
- Debugger :)

## Bugs
- Sprites disappear during dialog in Pokemon Red
  - Likely due to VBLANK rendering of display (SCX/SCY are saved per HBLANK but used at the end)
- Failing timing test ROMs
- Lots more! Open an issue or PR if you find one!
