from __future__ import annotations

from itertools import product
from typing import NamedTuple, Union

from .regs import Flag, Reg, Regs
from .mmu import MMU


class Instr(NamedTuple):
    cycles: int
    step: int
    mnem: str


class AddrMode:
    def __init__(self, op: Reg, address: bool, inc=0):
        self.op = op
        self.address = address
        self.inc = inc
    @staticmethod
    def by_addr(op: Reg, inc=0) -> AddrMode:
        return AddrMode(op, address=True, inc=inc)
    @staticmethod
    def by_reg(op: Reg) -> AddrMode:
        return AddrMode(op, address=False)

    def __str__(self):
        if self.address:
            inc = {-1: "-", 0: "", 1: "+"}.get(self.inc)
            return "({}{})".format(self.op, inc)
        else:
            return "{}".format(self.op)

    def increment(self, regs: Regs):
        regs.store(self.op, regs.load(self.op) + self.inc)

    def load(self, mmu: MMU, regs: Regs) -> int:
        if self.address:
            val = mmu.load(regs.load(self.op))
            self.increment(regs)
            return val
        else:
            return regs.load(self.op)
    def store(self, mmu: MMU, regs: Regs, val: int):
        if self.address:
            mmu.store(regs.load(self.op), val)
            self.increment(regs)
        else:
            regs.store(self.op, val)


def fetch(mmu: MMU, regs: Regs, offset=0) -> int:
    pc = regs.load(Reg.PC)
    return mmu.load(pc + offset)


def fetch_n(mmu: MMU, regs: Regs) -> int:
    return fetch(mmu, regs, offset=1)


def fetch_nn(mmu: MMU, regs: Regs) -> int:
    lo = fetch(mmu, regs, offset=1)
    hi = fetch(mmu, regs, offset=2)
    nn = (hi << 8) + lo
    # print("lo: {:04x} hi: {:04x} nn: {:04x}".format(lo, hi, nn))
    return nn

MSB_8BIT = 1 << 7
def from_rel(n: int) -> int:
    if n & MSB_8BIT:
        return n - 0x100
    else:
        return n


def unimplemented(regs: Regs, mmu: MMU):
    op = fetch(mmu, regs)
    return Instr(-1, 0, "UNIMP [0x{:02X}]".format(op))


def nop(regs: Regs, mmu: MMU) -> Instr:
    return Instr(4, 1, "NOP")


def jp(regs: Regs, mmu: MMU) -> Instr:
    target = fetch_nn(mmu, regs)
    regs.store(Reg.PC, target)
    return Instr(16, 0, "JP ${:04X}".format(target))


def jp_cc(flag: Flag, N: bool):
    def f(regs: Regs, mmu: MMU) -> Instr:
        target = fetch_nn(mmu, regs)
        if regs.get_flag(flag) != N:
            step = 0
            cycles = 16
            regs.store(Reg.PC, target)
        else:
            step = 3
            cycles = 12
        return Instr(cycles, step, "JP {}{},${:04X}".format("N" if N else "", flag.name, target))
    return f


def jr(regs: Regs, mmu: MMU) -> Instr:
    offset = fetch_n(mmu, regs)
    target = regs.load(Reg.PC) + from_rel(offset) + 2
    regs.store(Reg.PC, target)
    return Instr(12, 0, "JR ${:04X}".format(target))


def jr_cc(flag: Flag, N: bool):
    def f(regs: Regs, mmu: MMU) -> Instr:
        offset = fetch_n(mmu, regs)
        target = regs.load(Reg.PC) + from_rel(offset) + 2
        if regs.get_flag(flag) != N:
            step = 0
            cycles = 12
            regs.store(Reg.PC, target)
        else:
            step = 2
            cycles = 8
        return Instr(cycles, step, "JR {}{},${:04X}".format("N" if N else "", flag.name, target))
    return f


def push(src: Reg):
    def f(regs: Regs, mmu: MMU) -> Instr:
        sp = regs.load(Reg.SP)
        val = regs.load(src)
        lo = val & 0xff
        hi = val >> 8

        mmu.store(sp - 2, lo)
        mmu.store(sp - 1, hi)
        regs.store(Reg.SP, sp - 2)

        return Instr(16, 1, "PUSH {}".format(src))
    return f


def pop(dst: Reg):
    def f(regs: Regs, mmu: MMU) -> Instr:
        sp = regs.load(Reg.SP)
        lo = mmu.load(sp)
        hi = mmu.load(sp + 1)
        val = (hi << 8) + lo

        regs.store(Reg.SP, sp + 2)
        regs.store(dst, val)

        return Instr(16, 1, "POP {}".format(dst))
    return f


def call(regs: Regs, mmu: MMU) -> Instr:
    target = fetch_nn(mmu, regs)
    pc = regs.load(Reg.PC)
    ret = (pc + 3) % Reg.PC.max()

    regs.store(Reg.PC, ret)
    push(ret)(regs, mmu)
    regs.store(Reg.PC, target)

    return Instr(24, 0, "CALL ${:04X}".format(target))


def ret(regs: Regs, mmu: MMU) -> Instr:
    before = regs.load(Reg.PC)
    pop(Reg.PC)(regs, mmu)
    after = regs.load(Reg.PC)

    return Instr(16, 0, "RET")


def ld_r_r(dst: AddrMode, src: AddrMode):
    def f(regs: Regs, mmu: MMU) -> Instr:
        dst.store(mmu, regs, src.load(mmu, regs))
        cycles = 8 if dst.address or src.address else 4
        return Instr(cycles, 1, "LD {},{}".format(dst, src))
    return f


def ld_r_imm(dst: AddrMode):
    def f(regs: Regs, mmu: MMU) -> Instr:
        imm = fetch_n(mmu, regs)
        dst.store(mmu, regs, imm)
        return Instr(8, 2, "LD {},${:02X}".format(dst, imm))
    return f


def ld_rr_imm(dst: Reg):
    def f(regs: Regs, mmu: MMU) -> Instr:
        imm = fetch_nn(mmu, regs)
        regs.store(dst, imm)
        return Instr(12, 3, "LD {},${:04X}".format(dst, imm))
    return f


def ld_r_immp(dword):
    def f(regs: Regs, mmu: MMU) -> Instr:
        if dword:
            ptr = fetch_nn(mmu, regs)
        else:
            ptr = fetch_n(mmu, regs) + 0xff00
        regs.store(Reg.A, mmu.load(ptr))
        cycles = 16 if dword else 12
        step = 3 if dword else 2
        return Instr(cycles, step, "LD A,(${:X})".format(ptr))
    return f


def ld_immp_r(dword):
    def f(regs: Regs, mmu: MMU) -> Instr:
        if dword:
            ptr = fetch_nn(mmu, regs)
        else:
            ptr = fetch_n(mmu, regs) + 0xff00
        mmu.store(ptr, regs.load(Reg.A))
        cycles = 16 if dword else 12
        step = 3 if dword else 2
        return Instr(cycles, step, "LD (${:X}),A".format(ptr))
    return f


def incdec_r(dst: AddrMode, inc: bool):
    def f(regs: Regs, mmu: MMU) -> Instr:
        step = 1 if inc else -1
        val = dst.load(mmu, regs)
        res = (val + step) % (1 << dst.op.size())
        dst.store(mmu, regs, res)
        if dst.address or dst.op.size() == 8:
            regs.set_flag(Flag.Z, res == 0)
            regs.set_flag(Flag.N, 0)
            # regs.set_flag(Flag.H, idk lol)
        if dst.op.size() == 8:
            cycles = 4
        elif dst.address:
            cycles = 12
        else:
            cycles = 8
        return Instr(cycles, 1, "{} {}".format("INC" if inc else "DEC", dst))
    return f


def add_a_r(src: AddrMode):
    def f(regs: Regs, mmu: MMU) -> Instr:
        old_a = regs.load(Reg.A)
        r = src.load(mmu, regs)
        val = old_a + r

        regs.store(Reg.A, val)

        regs.set_flag(Flag.C, old_a > regs.load(Reg.A))
        regs.set_flag(Flag.N, 1)
        # regs.set_flag(Flag.H, )
        regs.set_flag(Flag.Z, val == 0)

        cycles = 8 if src.address else 4

        return Instr(cycles, 1, "ADD A,{}".format(src))
    return f


def di(regs: Regs, mmu: MMU) -> Instr:
    regs.IME = False
    return Instr(4, 1, "DI")


def ei(regs: Regs, mmu: MMU) -> Instr:
    regs.IME = True
    return Instr(4, 1, "EI")


NOP_OP = 0x00
HALT_OP = 0x76
DI_OP = 0xF3
EI_OP = 0xFB

OP_TABLE = {
    NOP_OP: nop,
    0x01: ld_rr_imm(Reg.BC),
    0x11: ld_rr_imm(Reg.DE),
    0x21: ld_rr_imm(Reg.HL),
    0x31: ld_rr_imm(Reg.SP),
    0x02: ld_r_r(AddrMode.by_addr(Reg.BC), AddrMode.by_reg(Reg.A)),
    0x0A: ld_r_r(AddrMode.by_reg(Reg.A), AddrMode.by_addr(Reg.BC)),
    0x12: ld_r_r(AddrMode.by_addr(Reg.DE), AddrMode.by_reg(Reg.A)),
    0x1A: ld_r_r(AddrMode.by_reg(Reg.A), AddrMode.by_addr(Reg.DE)),
    0x22: ld_r_r(AddrMode.by_addr(Reg.HL, inc=1), AddrMode.by_reg(Reg.A)),
    0x2A: ld_r_r(AddrMode.by_reg(Reg.A), AddrMode.by_addr(Reg.HL, inc=1)),
    0x32: ld_r_r(AddrMode.by_addr(Reg.HL, inc=-1), AddrMode.by_reg(Reg.A)),
    0x3A: ld_r_r(AddrMode.by_reg(Reg.A), AddrMode.by_addr(Reg.HL, inc=-1)),
    0x03: incdec_r(AddrMode.by_reg(Reg.BC), inc=True),
    0x13: incdec_r(AddrMode.by_reg(Reg.DE), inc=True),
    0x23: incdec_r(AddrMode.by_reg(Reg.HL), inc=True),
    0x33: incdec_r(AddrMode.by_reg(Reg.SP), inc=True),
    0x0B: incdec_r(AddrMode.by_reg(Reg.BC), inc=False),
    0x1B: incdec_r(AddrMode.by_reg(Reg.DE), inc=False),
    0x2B: incdec_r(AddrMode.by_reg(Reg.HL), inc=False),
    0x3B: incdec_r(AddrMode.by_reg(Reg.SP), inc=False),
    0x18: jr,
    0xC3: jp,
    0xCD: call,
    0xC9: ret,
    0xE0: ld_immp_r(dword=False),
    0xEA: ld_immp_r(dword=True),
    0xF0: ld_r_immp(dword=False),
    0xFA: ld_r_immp(dword=True),
    DI_OP: di,
    EI_OP: ei,
}

REG_DECODE_TABLE = [
    AddrMode.by_reg(Reg.B),
    AddrMode.by_reg(Reg.C),
    AddrMode.by_reg(Reg.D),
    AddrMode.by_reg(Reg.E),
    AddrMode.by_reg(Reg.H),
    AddrMode.by_reg(Reg.L),
    AddrMode.by_addr(Reg.HL),
    AddrMode.by_reg(Reg.A),
]
COND_DECODE_TABLE = [
    (Flag.Z, True),
    (Flag.Z, False),
    (Flag.C, True),
    (Flag.C, False),
]

INC_R_START = 0x04
DEC_R_START = 0x05
LD_R_IMM_START = 0x6
LD_R_R_START = 0x40
JR_CC_START = 0x20
JP_CC_START = 0xC2
POP_START = 0xC1
PUSH_START = 0xC5

for i, dst in enumerate(REG_DECODE_TABLE):
    OP_TABLE[INC_R_START + i * 8] = incdec_r(dst, inc=True)
    OP_TABLE[DEC_R_START + i * 8] = incdec_r(dst, inc=False)
    OP_TABLE[LD_R_IMM_START + i * 8] = ld_r_imm(dst)

for i, (dst, src) in enumerate(product(REG_DECODE_TABLE, repeat=2)):
    op = LD_R_R_START + i
    if op == HALT_OP:
        continue
    OP_TABLE[op] = ld_r_r(dst, src)

for i, (flag, is_n) in enumerate(COND_DECODE_TABLE):
    OP_TABLE[JR_CC_START + i * 8] = jr_cc(flag, is_n)
    OP_TABLE[JP_CC_START + i * 8] = jp_cc(flag, is_n)

for i, (flag, is_n) in enumerate(COND_DECODE_TABLE):
    OP_TABLE[JR_CC_START + i * 8] = jr_cc(flag, is_n)

for i, reg in enumerate([Reg.BC, Reg.DE, Reg.HL, Reg.AF]):
    OP_TABLE[POP_START + i * 0x10] = pop(reg)
    OP_TABLE[PUSH_START + i * 0x10] = push(reg)

print("*** {}/256 opcode implemented ***".format(len(OP_TABLE)))

def exec_instr(op: int, regs: Regs, mmu: MMU) -> Instr:
    handler = OP_TABLE.get(op, unimplemented)
    return handler(regs, mmu)
