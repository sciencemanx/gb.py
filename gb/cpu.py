from collections import defaultdict
from typing import Dict, List, NamedTuple

MASK_8BIT = 2 ** 8 - 1

RawRegs = Dict[str, int]


class Reg(NamedTuple):
    name: str
    parts: List[str]
    def size(self):
        return len(self.name) * 8  # fun hack
    def mask(self):
        return 2 ** self.size() - 1
    def read(self, rawregs: RawRegs) -> int:
        return sum(rawregs[r] << i * 8 for i, r in enumerate(reversed(self.parts)))
    def write(self, rawregs: RawRegs, val: int):
        for i, r in enumerate(reversed(self.parts)):
            rawregs[r] = (val >> i * 8) & MASK_8BIT
    def __str__(self):
        return self.name
    def __repr__(self):
        return "{}.{}".format(type(self).__name__, self.name)


# 8 bit regs
Reg.A = Reg("A", ["A"])
Reg.F = Reg("F", ["F"])  # not individually addressable
Reg.B = Reg("B", ["B"])
Reg.C = Reg("C", ["C"])
Reg.D = Reg("D", ["D"])
Reg.E = Reg("E", ["E"])
Reg.H = Reg("H", ["H"])
Reg.L = Reg("L", ["L"])

# 16 bit compound regs
Reg.AF = Reg("AF", ["A", "F"])
Reg.BC = Reg("BC", ["B", "C"])
Reg.DE = Reg("DE", ["D", "E"])
Reg.HL = Reg("HL", ["H", "L"])

# 16 bit regs
Reg.PC = Reg("PC", ["PC"])
Reg.SP = Reg("SP", ["SP"])


class CPU:
    def __init__(self):
        self._rawregs: RawRegs = defaultdict(int)
    def load(self, reg: Reg) -> int:
        return reg.read(self._rawregs)
    def store(self, reg: Reg, val: int):
        reg.write(self._rawregs, val)
