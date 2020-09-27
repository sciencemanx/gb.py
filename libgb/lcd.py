
import pygame

DIMENSION = (160, 144)

class LCD:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("gb.py")

        self.screen = pygame.display.set_mode(DIMENSION)
        self.pixels = pygame.PixelArray(self.screen)

        pygame.event.get()

    def wait(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return

    def draw_pixel(self, x: int, y: int, color: int):
        assert 0 <= color < 4
        true_color = color * 85
        pixel = (true_color, true_color, true_color)
        self.pixels[x, y] = pixel
        # self.screen.blit(self.screen, (0, 0))
