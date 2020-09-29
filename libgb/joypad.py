import pygame

from .io import IOHandler, JoypadIO

JOYP_DIR_FLAG = 1 << 4
JOYP_BUTTON_FLAG = 1 << 5
JOYP_MODE_MASK = JOYP_DIR_FLAG | JOYP_BUTTON_FLAG

DIR_KEYS = {
    pygame.K_RIGHT: 1 << 0,
    pygame.K_LEFT: 1 << 1,
    pygame.K_UP: 1 << 2,
    pygame.K_DOWN: 1 << 3,
}

BUTTON_KEYS = {
    pygame.K_z: 1 << 0,
    pygame.K_x: 1 << 1,
    pygame.K_RSHIFT: 1 << 2,
    pygame.K_RETURN: 1 << 3,
}

class JoypadIOHandler(IOHandler):
    mode: int
    def __init__(self):
        self.mode = 0
    def __contains__(self, addr: int) -> bool:
        return addr == JoypadIO.JOYP.value
    def load(self, addr: int) -> int:
        keys = pygame.key.get_pressed()
        joyp = self.mode | 0xf
        if (joyp & JOYP_DIR_FLAG) == 0:
            for dir, flag in DIR_KEYS.items():
                if keys[dir]:
                    joyp &= ~flag
        if (joyp & JOYP_BUTTON_FLAG) == 0:
            for button, flag in BUTTON_KEYS.items():
                if keys[button]:
                    joyp &= ~flag
        return joyp
    def store(self, addr: int, val: int):
        self.mode = val & JOYP_MODE_MASK
