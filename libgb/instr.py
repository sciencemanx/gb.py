from __future__ import annotations

from typing import NamedTuple

from .regs import Flag, Reg, Regs
from .mmu import MMU


class Instr(NamedTuple):
    cycles: int
    step: int
    mnem: str


class AddrMode:
    def __init__(self, reg: Reg, address: bool):
        self.reg = reg
        self.address = address
    @staticmethod
    def by_address(reg: Reg) -> AddrMode:
        return AddrMode(reg, address=True)
    @staticmethod
    def by_reg(reg: Reg) -> AddrMode:
        return AddrMode(reg, address=False)

    def load(self, mmu: MMU, regs: Regs) -> int:
        if self.address:
            return mmu.load(regs.load(self.reg))
        else:
            return regs.load(self.reg)
    def store(self, mmu: MMU, regs: Regs, val: int):
        if self.address:
            mmu.store(regs.load(self.reg), val)
        else:
            regs.store(self.reg, val)


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


def unimplemented(regs: Regs, mmu: MMU):
    op = fetch(mmu, regs)
    return Instr(-1, 0, "UNIMP [0x{:02X}]".format(op))


def nop(regs: Regs, mmu: MMU) -> Instr:
    return Instr(4, 1, "NOP")


def jp(regs: Regs, mmu: MMU) -> Instr:
    target = fetch_nn(mmu, regs)
    regs.store(Reg.PC, target)
    return Instr(16, 0, "JP ${:04X}".format(target))


def jp_cc_imm(flag: Flag, N: bool):
    def f(regs: Regs, mmu: MMU) -> Instr:
        target = fetch_nn(mmu, regs)
        if regs.get_flag(Flag.ZERO) != N:
            step = 0
            cycles = 16
            regs.store(Reg.PC, target)
        else:
            step = 3
            cycles = 12
        return Instr(cycles, step, "JP {}{} ${:04X}".format("N" if N else "", flag.name, target))
    return f


def ld_r_r(dst: Reg, src: Reg):
    def f(regs: Regs, mmu: MMU) -> Instr:
        regs.store(dst, regs.load(src))
        return Instr(12, 1, "LD {},{}".format(dst, src))
    return f


def ld_r_imm(dst: Reg):
    def f(regs: Regs, mmu: MMU) -> Instr:
        imm = fetch_n(mmu, regs)
        regs.store(dst, imm)
        return Instr(8, 2, "LD {},${:02X}".format(dst, imm))
    return f


def ld_rr_imm(dst: Reg):
    def f(regs: Regs, mmu: MMU) -> Instr:
        imm = fetch_nn(mmu, regs)
        regs.store(dst, imm)
        return Instr(12, 3, "LD {},${:04X}".format(dst, imm))
    return f


OP_TABLE = {
    0x00: nop,
    0x01: ld_rr_imm(Reg.BC),
    0x06: ld_r_imm(Reg.B),
    0x0E: ld_r_imm(Reg.C),
    0x11: ld_rr_imm(Reg.DE),
    0x16: ld_r_imm(Reg.D),
    0x1E: ld_r_imm(Reg.E),
    0x21: ld_rr_imm(Reg.HL),
    0x26: ld_r_imm(Reg.H),
    0x2E: ld_r_imm(Reg.L),
    0x31: ld_rr_imm(Reg.SP),
    0x3E: ld_r_imm(Reg.A),
    0x40: ld_r_r(Reg.B, Reg.B),
    0x41: ld_r_r(Reg.B, Reg.C),
    0x42: ld_r_r(Reg.B, Reg.D),
    0x43: ld_r_r(Reg.B, Reg.E),
    0x44: ld_r_r(Reg.B, Reg.H),
    0x45: ld_r_r(Reg.B, Reg.L),
    0x47: ld_r_r(Reg.B, Reg.A),
    0x48: ld_r_r(Reg.C, Reg.B),
    0x49: ld_r_r(Reg.C, Reg.C),
    0x4A: ld_r_r(Reg.C, Reg.D),
    0x4B: ld_r_r(Reg.C, Reg.E),
    0x4C: ld_r_r(Reg.C, Reg.H),
    0x4D: ld_r_r(Reg.C, Reg.L),
    0x4F: ld_r_r(Reg.C, Reg.A),
    0x50: ld_r_r(Reg.D, Reg.B),
    0x51: ld_r_r(Reg.D, Reg.C),
    0x52: ld_r_r(Reg.D, Reg.D),
    0x53: ld_r_r(Reg.D, Reg.E),
    0x54: ld_r_r(Reg.D, Reg.H),
    0x55: ld_r_r(Reg.D, Reg.L),
    0x57: ld_r_r(Reg.D, Reg.A),
    0x58: ld_r_r(Reg.E, Reg.B),
    0x59: ld_r_r(Reg.E, Reg.C),
    0x5A: ld_r_r(Reg.E, Reg.D),
    0x5B: ld_r_r(Reg.E, Reg.E),
    0x5C: ld_r_r(Reg.E, Reg.H),
    0x5D: ld_r_r(Reg.E, Reg.L),
    0x5F: ld_r_r(Reg.E, Reg.A),
    0x60: ld_r_r(Reg.H, Reg.B),
    0x61: ld_r_r(Reg.H, Reg.C),
    0x62: ld_r_r(Reg.H, Reg.D),
    0x63: ld_r_r(Reg.H, Reg.E),
    0x64: ld_r_r(Reg.H, Reg.H),
    0x65: ld_r_r(Reg.H, Reg.L),
    0x67: ld_r_r(Reg.H, Reg.A),
    0x68: ld_r_r(Reg.L, Reg.B),
    0x69: ld_r_r(Reg.L, Reg.C),
    0x6A: ld_r_r(Reg.L, Reg.D),
    0x6B: ld_r_r(Reg.L, Reg.E),
    0x6C: ld_r_r(Reg.L, Reg.H),
    0x6D: ld_r_r(Reg.L, Reg.L),
    0x6F: ld_r_r(Reg.L, Reg.A),
    0x78: ld_r_r(Reg.A, Reg.B),
    0x79: ld_r_r(Reg.A, Reg.C),
    0x7A: ld_r_r(Reg.A, Reg.D),
    0x7B: ld_r_r(Reg.A, Reg.E),
    0x7C: ld_r_r(Reg.A, Reg.H),
    0x7D: ld_r_r(Reg.A, Reg.L),
    0x7F: ld_r_r(Reg.A, Reg.A),
    0xC2: jp_cc_imm(Flag.Z, N=True),
    0xC3: jp,
    0xD2: jp_cc_imm(Flag.C, N=True),
}

print("*** {}/512 opcode implemented ***".format(len(OP_TABLE)))


def exec_instr(op: int, regs: Regs, mmu: MMU) -> Instr:
    handler = OP_TABLE.get(op, unimplemented)
    return handler(regs, mmu)
