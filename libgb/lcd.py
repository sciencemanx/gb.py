from typing import List

import pygame

DIMENSION = (160, 144)

class LCD:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("gb.py")

        self.screen = pygame.display.set_mode(DIMENSION)
        self.pixels = pygame.PixelArray(self.screen)

    def wait(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return

    def draw_display(self, display: List[List[int]]):
        assert len(display) == 160
        assert len(display[0]) == 144

        bs = bytearray(160 * 144 * 4)
        k = 0
        for j in range(144):
            for i in range(160):
                p = (3 - display[i][j]) * 85
                bs[k] = p
                bs[k+1] = p
                bs[k+2] = p
                bs[k+3] = 0xff
                k += 4

        self.screen.get_buffer().write(bs)
        pygame.display.flip()
        return pygame.QUIT in [e.type for e in pygame.event.get()]
