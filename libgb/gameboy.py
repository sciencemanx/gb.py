import time
from typing import NamedTuple

from . import cpu
from . import mmu

class Gameboy(NamedTuple):
    cpu: cpu.CPU
    mmu: mmu.MMU

    def run(self):
        done = False
        start = time.time()
        while not done:
            done = self.cpu.step(self.mmu)
        end = time.time()
        print("-- REGS --")
        print(self.cpu.regs)
        print("num execs: {}".format(self.cpu.execs))
        print("cycles: {}".format(self.cpu.cycles))
        print("cpu secs: {}".format(self.cpu.cycles / 4190000))
        print("wall secs: {}".format(end - start))
