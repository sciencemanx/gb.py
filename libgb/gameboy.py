from typing import NamedTuple

from . import cpu
from . import mmu

class Gameboy(NamedTuple):
    cpu: cpu.CPU
    mmu: mmu.MMU

    def run(self, debug=False):
        done = False
        while not done:
            done = self.cpu.step(self.mmu)
            if debug:
                print(cpu)
        print("-- REGS --")
        print(self.cpu.regs)
        print("done")
