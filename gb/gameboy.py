from typing import NamedTuple

from .cpu import CPU
from .mmu import MMU

class Gameboy(NamedTuple):
    cpu: CPU
    mmu: MMU

    def run(self, debug=False):
        done = False
        while not done:
            done = self.cpu.step(self.mmu)
            if debug:
                print(cpu)
