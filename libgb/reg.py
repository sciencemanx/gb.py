from collections import defaultdict
from enum import Enum
from typing import Dict, List, NamedTuple

from .mmu import MMU


RawRegs = Dict[str, int]


class Flag(Enum):
    C = 1 << 4 # carry flag
    H = 1 << 5 # half carry flag
    N = 1 << 6 # subtract flag
    Z = 1 << 7 # zero flag


class Reg(NamedTuple):
    name: str
    parts: List[str]
    def size(self):
        return len(self.name) * 8  # fun hack
    def max(self):
        return 2 ** self.size()
    def mask(self):
        return self.max() - 1
    def read(self, rawregs: RawRegs) -> int:
        if len(self.parts) == 1:
            return rawregs[self.name]
        else:
            hi_reg, lo_reg = self.parts
            hi, lo = rawregs[hi_reg], rawregs[lo_reg]
            return (hi << 8) + lo
            # return sum(rawregs[r] << i * 8 for i, r in enumerate(reversed(self.parts)))
    def write(self, rawregs: RawRegs, val: int):
        val = val % self.max()
        if len(self.parts) == 1:
            rawregs[self.name] = val
        else:
            for i, r in enumerate(reversed(self.parts)):
                rawregs[r] = (val >> i * 8) & (2 ** (len(r) * 8) - 1)
    def __str__(self):
        return self.name
    def __repr__(self):
        return "{}.{}".format(type(self).__name__, self.name)


# 8 bit regs
A = Reg("A", ["A"])
F = Reg("F", ["F"])  # not individually addressable
B = Reg("B", ["B"])
C = Reg("C", ["C"])
D = Reg("D", ["D"])
E = Reg("E", ["E"])
H = Reg("H", ["H"])
L = Reg("L", ["L"])

# 16 bit compound regs
AF = Reg("AF", ["A", "F"])
BC = Reg("BC", ["B", "C"])
DE = Reg("DE", ["D", "E"])
HL = Reg("HL", ["H", "L"])

# 16 bit regs
PC = Reg("PC", ["PC"])
SP = Reg("SP", ["SP"])


REG_FMT = "AF ${:02X}:{:02X}\n" \
          "BC ${:02X}:{:02X}\n" \
          "DE ${:02X}:{:02X}\n" \
          "HL ${:02X}:{:02X}\n" \
          "PC ${:04X}\n" \
          "SP ${:04X}"


class Regs:
    def __init__(self):
        self._rawregs: RawRegs = defaultdict(int)
        self.IME = False
        self.halted = False

    def load(self, reg: Reg) -> int:
        return reg.read(self._rawregs)

    def store(self, reg: Reg, val: int):
        reg.write(self._rawregs, val)

    def get_flag(self, flag: Flag) -> bool:
        return (self.load(F) & flag.value) != 0

    def set_flag(self, flag: Flag, on: bool):
        old_flags = self.load(F)
        if on:
            self.store(F, old_flags | flag.value)
        else:
            self.store(F, old_flags & ~flag.value)

    def __str__(self):
        return REG_FMT.format(
            self.load(A),
            self.load(F),
            self.load(B),
            self.load(C),
            self.load(D),
            self.load(E),
            self.load(H),
            self.load(L),
            self.load(PC),
            self.load(SP),
        )
