from __future__ import annotations
import enum

from itertools import product
from typing import NamedTuple, Union

from .mmu import MMU
from . import ops, reg
from .reg import Flag, Regs


class Instr(NamedTuple):
    cycles: int
    step: int
    mnem: str


MSB_8BIT = 1 << 7
def from_rel(n: int) -> int:
    if n & MSB_8BIT:
        return n - 0x100
    else:
        return n


def unimplemented(ctx: ops.Ctx):
    op = ctx.mmu.load(ctx.regs.load(reg.PC))
    return Instr(-1, 0, "UNIMP [0x{:02X}]".format(op))


def nop(ctx: ops.Ctx) -> Instr:
    return Instr(4, 1, "NOP")


def jp(ctx: ops.Ctx) -> Instr:
    target = ops.imm16.load(ctx)
    ops.PC.store(ctx, target)
    return Instr(16, 0, "JP ${:04X}".format(target))


def jp_cc(flag: Flag, N: bool):
    def f(ctx: ops.Ctx) -> Instr:
        target = ops.imm16.load(ctx)
        if ctx.regs.get_flag(flag) != N:
            step = 0
            cycles = 16
            ops.PC.store(ctx, target)
        else:
            step = 3
            cycles = 12
        cond = "{}{}".format("N" if N else "", flag.name)
        return Instr(cycles, step, "JP {},{}".format(cond, ops.imm16.fmt(ctx)))
    return f


def jr(ctx: ops.Ctx) -> Instr:
    offset = ops.imm8.load(ctx)
    target = ops.PC.load(ctx) + from_rel(offset) + 2
    ops.PC.store(ctx, target)
    return Instr(12, 0, "JR ${:04X}".format(target))


def jr_cc(flag: Flag, N: bool):
    def f(ctx: ops.Ctx) -> Instr:
        offset = ops.imm8.load(ctx)
        target = ops.PC.load(ctx) + from_rel(offset) + 2
        if ctx.regs.get_flag(flag) != N:
            step = 0
            cycles = 12
            ops.PC.store(ctx, target)
        else:
            step = 2
            cycles = 8
        cond = "{}{}".format("N" if N else "", flag.name)
        return Instr(cycles, step, "JR {},${:04X}".format(cond, target))
    return f


def push(src: ops.Reg):
    def f(ctx: ops.Ctx) -> Instr:
        ops.SP.store(ctx, ops.SP.load(ctx) - 2)
        val = src.load(ctx)
        ops.stack.store(ctx, val)

        return Instr(16, 1, "PUSH {}".format(src))
    return f


def pop(dst: ops.Reg):
    def f(ctx: ops.Ctx) -> Instr:
        val = ops.stack.load(ctx)
        dst.store(ctx, val)
        ops.SP.store(ctx, ops.SP.load(ctx) + 2)

        return Instr(16, 1, "POP {}".format(dst))
    return f


def do_call(ctx: ops.Ctx):
    target = ops.imm16.load(ctx)
    ret = (ops.PC.load(ctx) + 3) % reg.PC.max()

    ops.SP.store(ctx, ops.SP.load(ctx) - 2)
    ops.stack.store(ctx, ret)
    ops.PC.store(ctx, target)


def call(ctx: ops.Ctx) -> Instr:
    target_str = ops.imm16.fmt(ctx)

    do_call(ctx)

    return Instr(24, 0, "CALL {}".format(target_str))


def call_cc(flag: Flag, N: bool):
    def f(ctx: ops.Ctx) -> Instr:
        target_str = ops.imm16.fmt(ctx)

        if ctx.regs.get_flag(flag) != N:
            do_call(ctx)
            step = 0
            cycles = 24
        else:
            step = 3
            cycles = 12
        cond = "{}{}".format("N" if N else "", flag.name)
        return Instr(cycles, step, "CALL {},{}".format(cond, target_str))
    return f


def do_ret(ctx: ops.Ctx):
    ret_addr = ops.stack.load(ctx)
    ops.PC.store(ctx, ret_addr)
    ops.SP.store(ctx, ops.SP.load(ctx) + 2)


def ret(ctx: ops.Ctx) -> Instr:
    do_ret(ctx)

    return Instr(16, 0, "RET")


def ret_cc(flag: Flag, N: bool):
    def f(ctx: ops.Ctx) -> Instr:
        if ctx.regs.get_flag(flag) != N:
            do_ret(ctx)
            step = 0
            cycles = 20
        else:
            step = 1
            cycles = 8
        cond = "{}{}".format("N" if N else "", flag.name)
        return Instr(cycles, step, "RET {}".format(cond))
    return f


def ld(dst: ops.Operand, src: ops.Operand):
    def f(ctx: ops.Ctx) -> Instr:
        dst.store(ctx, src.load(ctx))
        cycles = 4 + dst.cost() + src.cost()
        step = 1 + dst.space() + src.space()
        return Instr(cycles, step, "LD {},{}".format(dst.fmt(ctx), src.fmt(ctx)))
    return f


def incdec(op: ops.Operand, inc: bool):
    def f(ctx: ops.Ctx) -> Instr:
        step = 1 if inc else -1
        val = op.load(ctx)
        op.store(ctx, val + step)
        res = op.load(ctx)
        if not op.is_dword():
            ctx.regs.set_flag(Flag.Z, res == 0)
            ctx.regs.set_flag(Flag.N, False)
            # regs.set_flag(Flag.H, idk lol)
        cycles = 4
        if isinstance(op, ops.Mem):
            cycles += op.cost() * 2 # read/write
        elif op.is_dword():
            cycles += 4 # arith on dword
        insn = "INC" if inc else "DEC"
        return Instr(cycles, 1, "{} {}".format(insn, op))
    return f


def add(lhs: ops.Operand, rhs: ops.Operand):
    def f(ctx: ops.Ctx) -> Instr:
        old_l = lhs.load(ctx)
        lhs.store(ctx, old_l + rhs.load(ctx))
        new_l = lhs.load(ctx)

        ctx.regs.set_flag(Flag.C, old_l > new_l)
        ctx.regs.set_flag(Flag.N, True)
        # ctx.regs.set_flag(Flag.H, )
        if not lhs.is_dword():
            ctx.regs.set_flag(Flag.Z, new_l == 0)

        cycles = 4 + lhs.cost() + rhs.cost()
        step = 1 + lhs.space() + rhs.space()

        return Instr(cycles, step, "ADD {},{}".format(lhs.fmt(ctx), rhs.fmt(ctx)))
    return f


def and_(lhs: ops.Operand, rhs: ops.Operand):
    def f(ctx: ops.Ctx) -> Instr:
        lhs.store(ctx, lhs.load(ctx) & rhs.load(ctx))
        val = lhs.load(ctx)

        ctx.regs.set_flag(Flag.C, False)
        ctx.regs.set_flag(Flag.N, False)
        ctx.regs.set_flag(Flag.H, True)
        ctx.regs.set_flag(Flag.Z, val == 0)

        cycles = 4 + rhs.cost()
        step = 1 + rhs.space()
        return Instr(cycles, step, "AND {}".format(rhs.fmt(ctx)))
    return f


def xor(lhs: ops.Operand, rhs: ops.Operand):
    def f(ctx: ops.Ctx) -> Instr:
        lhs.store(ctx, lhs.load(ctx) ^ rhs.load(ctx))
        val = lhs.load(ctx)

        ctx.regs.set_flag(Flag.C, False)
        ctx.regs.set_flag(Flag.N, False)
        ctx.regs.set_flag(Flag.H, False)
        ctx.regs.set_flag(Flag.Z, val == 0)

        cycles = 4 + rhs.cost()
        step = 1 + rhs.space()
        return Instr(cycles, step, "XOR {}".format(rhs.fmt(ctx)))
    return f


def or_(lhs: ops.Operand, rhs: ops.Operand):
    def f(ctx: ops.Ctx) -> Instr:
        lhs.store(ctx, lhs.load(ctx) | rhs.load(ctx))
        val = lhs.load(ctx)

        ctx.regs.set_flag(Flag.C, False)
        ctx.regs.set_flag(Flag.N, False)
        ctx.regs.set_flag(Flag.H, False)
        ctx.regs.set_flag(Flag.Z, val == 0)

        cycles = 4 + rhs.cost()
        step = 1 + rhs.space()
        return Instr(cycles, step, "OR {}".format(rhs.fmt(ctx)))
    return f


def cp(lhs: ops.Operand, rhs: ops.Operand):
    def f(ctx: ops.Ctx) -> Instr:
        val = lhs.load(ctx) - rhs.load(ctx)

        ctx.regs.set_flag(Flag.C, val < 0)
        ctx.regs.set_flag(Flag.N, True)
        # ctx.regs.set_flag(Flag.H, idk)
        ctx.regs.set_flag(Flag.Z, val == 0)

        cycles = 4 + rhs.cost()
        step = 1 + rhs.space()
        return Instr(cycles, step, "CP {}".format(rhs.fmt(ctx)))
    return f


def di(ctx: ops.Ctx) -> Instr:
    ctx.regs.IME = False
    return Instr(4, 1, "DI")


def ei(ctx: ops.Ctx) -> Instr:
    ctx.regs.IME = True
    return Instr(4, 1, "EI")


NOP = 0x00
JR = 0x18
JP = 0xC3
CALL = 0xCD
RET = 0xC9
HALT = 0x76
DI = 0xF3
EI = 0xFB

OP_TABLE = {
    NOP: nop,
    JR: jr,
    JP: jp,
    CALL: call,
    RET: ret,
    DI: di,
    EI: ei,

    0xE0: ld(ops.Mem(ops.imm8, offset=0xFF00), ops.A),
    0xE2: ld(ops.Mem(ops.C), ops.A),
    0xEA: ld(ops.Mem(ops.imm16), ops.A),
    0xF0: ld(ops.A, ops.Mem(ops.imm8, offset=0xFF00)),
    0xF2: ld(ops.A, ops.Mem(ops.C)),
    0xFA: ld(ops.A, ops.Mem(ops.imm16)),
}

REG_DECODE_TABLE = [
    ops.Reg(reg.B),
    ops.Reg(reg.C),
    ops.Reg(reg.D),
    ops.Reg(reg.E),
    ops.Reg(reg.H),
    ops.Reg(reg.L),
    ops.Mem(ops.Reg(reg.HL)),
    ops.Reg(reg.A),
]

INC_R_START = 0x04
DEC_R_START = 0x05
INC_RR_START = 0x03
DEC_RR_START = 0x0B
LD_R_IMM_START = 0x6
LD_R_R_START = 0x40
LD_RR_IMM_START = 0x01
LD_RRp_R_START = 0x02
LD_R_RRp_START = 0x0A
JR_CC_START = 0x20
JP_CC_START = 0xC2
CALL_CC_START = 0xC4
RET_CC_START = 0xC0
POP_START = 0xC1
PUSH_START = 0xC5

for i, dst in enumerate(REG_DECODE_TABLE):
    OP_TABLE[INC_R_START + i * 8] = incdec(dst, inc=True)
    OP_TABLE[DEC_R_START + i * 8] = incdec(dst, inc=False)
    OP_TABLE[LD_R_IMM_START + i * 8] = ld(dst, ops.imm8)

for i, (dst, src) in enumerate(product(REG_DECODE_TABLE, repeat=2)):
    op = LD_R_R_START + i
    if op == HALT:
        continue
    OP_TABLE[op] = ld(dst, src)

for i, r in enumerate([ops.BC, ops.DE, ops.HL, ops.SP]):
    OP_TABLE[LD_RR_IMM_START + i * 0x10] = ld(r, ops.imm16)
    OP_TABLE[INC_RR_START + i * 0x10] = incdec(r, inc=True)
    OP_TABLE[DEC_RR_START + i * 0x10] = incdec(r, inc=False)

for i, r in enumerate([ops.BC, ops.DE, ops.HLI, ops.HLD]):
    mem = ops.Mem(r)
    OP_TABLE[LD_RRp_R_START + i * 0x10] = ld(mem, ops.A)
    OP_TABLE[LD_R_RRp_START + i * 0x10] = ld(ops.A, mem)

for i, (flag, is_n) in enumerate(product((Flag.Z, Flag.C), (True, False))):
    OP_TABLE[JR_CC_START + i * 8] = jr_cc(flag, is_n)
    OP_TABLE[JP_CC_START + i * 8] = jp_cc(flag, is_n)
    OP_TABLE[CALL_CC_START + i * 8] = call_cc(flag, is_n)
    OP_TABLE[RET_CC_START + i * 8] = ret_cc(flag, is_n)

for i, r in enumerate([ops.BC, ops.DE, ops.HL, ops.AF]):
    OP_TABLE[POP_START + i * 0x10] = pop(r)
    OP_TABLE[PUSH_START + i * 0x10] = push(r)

for i, rhs in enumerate(REG_DECODE_TABLE):
    OP_TABLE[0x80 + i] = add(ops.A, rhs)
    OP_TABLE[0xA0 + i] = and_(ops.A, rhs)
    OP_TABLE[0xA8 + i] = xor(ops.A, rhs)
    OP_TABLE[0xB0 + i] = or_(ops.A, rhs)
    OP_TABLE[0xB8 + i] = cp(ops.A, rhs)

OP_TABLE[0x08] = ld(ops.Mem(ops.imm16, dword=True), ops.SP)
OP_TABLE[0xC6] = add(ops.A, ops.imm8)
OP_TABLE[0xE6] = and_(ops.A, ops.imm8)
OP_TABLE[0xEE] = xor(ops.A, ops.imm8)
OP_TABLE[0xF6] = or_(ops.A, ops.imm8)
OP_TABLE[0xFE] = cp(ops.A, ops.imm8)


UNUSED = [0xd3, 0xdb, 0xdd, 0xe3, 0xe4, 0xeb, 0xec, 0xed, 0xf4, 0xfc, 0xfd]
def diag():
    print("*** {}/256 opcodes implemented ***".format(len(OP_TABLE)))
    for i in range(0x10):
        for j in range(0x10):
            idx = i * 0x10 + j
            if idx in OP_TABLE:
                mark = "X"
            elif idx in UNUSED:
                mark = "-"
            elif idx == 0xcb:
                mark = "C"
            else:
                mark = " "
            print(mark, end=" ")
        print("")


def exec_instr(op: int, regs: Regs, mmu: MMU) -> Instr:
    handler = OP_TABLE.get(op, unimplemented)
    ctx = ops.Ctx(regs, mmu)
    return handler(ctx)
