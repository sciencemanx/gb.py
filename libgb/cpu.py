from . import instr
from .mmu import MMU
from .regs import Reg, Regs


class CPU:
    def __init__(self, max_execs=None):
        self.execs = 0
        self.max_execs = max_execs

        self.regs = Regs()
        self.regs.store(Reg.AF, 0x01B0)
        self.regs.store(Reg.BC, 0x0013)
        self.regs.store(Reg.DE, 0x00D8)
        self.regs.store(Reg.HL, 0x014D)
        self.regs.store(Reg.SP, 0xFFFE)
        self.regs.store(Reg.PC, 0x0100)

    def step(self, mmu: MMU) -> bool:
        pc = self.regs.load(Reg.PC)
        op = mmu.load(pc)
        inst = instr.exec_instr(op, self.regs, mmu)
        print("{:04X}: {}".format(pc, inst.mnem))
        self.regs.store(Reg.PC, self.regs.load(Reg.PC) + inst.step)

        self.execs += 1
        if self.max_execs and self.execs > self.max_execs:
            return True

        return inst.cycles == -1
