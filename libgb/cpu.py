from . import instr, reg
from .mmu import MMU
from .reg import Regs


class CPU:
    def __init__(self, max_execs=None):
        self.execs = 0
        self.max_execs = max_execs
        self.execed = []

        self.regs = Regs()
        self.regs.store(reg.AF, 0x01B0)
        self.regs.store(reg.BC, 0x0013)
        self.regs.store(reg.DE, 0x00D8)
        self.regs.store(reg.HL, 0x014D)
        self.regs.store(reg.SP, 0xFFFE)
        self.regs.store(reg.PC, 0x0100)

    def step(self, mmu: MMU) -> bool:
        pc = self.regs.load(reg.PC)
        op = mmu.load(pc)
        inst = instr.exec_instr(op, self.regs, mmu)
        print("{:04X}:{:02X} {}".format(pc, op, inst.mnem))
        i = inst.mnem.split()[0]
        if i not in self.execed:
            self.execed.append(i)
        self.regs.store(reg.PC, self.regs.load(reg.PC) + inst.step)

        self.execs += 1
        if self.max_execs and self.execs > self.max_execs:
            return True

        return inst.cycles == -1
