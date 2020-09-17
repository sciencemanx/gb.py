from abc import ABC, abstractmethod
from typing import NamedTuple, Union

from . import mmu, reg


IMM_TABLE = {
    0xC093: "init_printing",
    0xC17E: "init_testing",
    0xC79B: "init_runtime",
    0xC04D: "init_crc",
    0xC36D: "console_init",
    0xC410: "console_hide",
    0xC35C: "console_wait_vbl",
    0xC16B: "set_test_",
    0xC7B1: "std_print",
}


class Ctx(NamedTuple):
    regs: reg.Regs
    mmu: mmu.MMU
    def pc(self):
        return self.regs.load(reg.PC)


class Operand:
    @abstractmethod
    def load(self, ctx: Ctx) -> int:
        pass
    @abstractmethod
    def store(self, ctx: Ctx, val: int):
        pass
    @abstractmethod
    def cost(self) -> int:
        pass
    @abstractmethod
    def space(self) -> int:
        pass
    @abstractmethod
    def is_dword(self) -> bool:
        pass
    @abstractmethod
    def fmt(self, ctx: Ctx) -> str:
        pass


class Reg(Operand):
    def __init__(self, reg: reg.Reg):
        self.reg = reg
    def load(self, ctx: Ctx) -> int:
        return ctx.regs.load(self.reg)
    def store(self, ctx: Ctx, val: int):
        ctx.regs.store(self.reg, val)
    def cost(self) -> int:
        return 0
    def space(self) -> int:
        return 0
    def is_dword(self) -> bool:
        return self.reg.size() == 16
    def fmt(self, ctx: Ctx) -> str:
        return str(self)
    def __str__(self):
        return str(self.reg)


class IncReg(Reg):
    def __init__(self, reg: reg.Reg, inc: bool):
        super().__init__(reg)
        self.step = 1 if inc else -1
    def load(self, ctx: Ctx) -> int:
        val = super().load(ctx)
        super().store(ctx, val + self.step)
        return val
    def __str__(self):
        sign = "+" if self.step == 1 else "-"
        return "{}{}".format(super().__str__(), sign)


class Imm(Operand):
    def __init__(self, dword=False):
        self.dword = dword
    def load(self, ctx: Ctx) -> int:
        pc = ctx.pc()
        if self.dword:
            return ctx.mmu.load_nn(pc + 1)
        else:
            return ctx.mmu.load(pc + 1)
    def store(self, ctx: Ctx, val: int):
        raise NotImplementedError
    def cost(self) -> int:
        if self.dword:
            return 8
        else:
            return 4
    def space(self) -> int:
        if self.dword:
            return 2
        else:
            return 1
    def is_dword(self) -> bool:
        return self.dword
    def fmt(self, ctx: Ctx) -> str:
        val = self.load(ctx)
        if val in IMM_TABLE:
            name = " '{}'".format(IMM_TABLE[val])
        else:
            name = ""
        if self.dword:
            return "${:04X}{}".format(self.load(ctx), name)
        else:
            return "${:02X}".format(self.load(ctx))
    def __str__(self):
        if self.dword:
            return "$xxxx"
        else:
            return "$xx"


RawOperand = Union[Imm, Reg]


class Mem(Operand):
    def __init__(self, ptr: RawOperand, offset=0, dword=False):
        self.ptr = ptr
        self.offset = offset
        self.dword = dword
    def load(self, ctx: Ctx) -> int:
        addr = self.ptr.load(ctx) + self.offset
        if self.dword:
            return ctx.mmu.load_nn(addr)
        else:
            return ctx.mmu.load(addr)
    def store(self, ctx: Ctx, val: int):
        addr = self.ptr.load(ctx) + self.offset
        if self.dword:
            ctx.mmu.store_nn(addr, val)
        else:
            ctx.mmu.store(addr, val)
    def cost(self) -> int:
        if self.dword:
            return 8 + self.ptr.cost()
        else:
            return 4 + self.ptr.cost()
    def space(self) -> int:
        return self.ptr.space()
    def is_dword(self) -> bool:
        return self.dword
    def fmt(self, ctx: Ctx = None) -> str:
        if ctx is None:
            base_detail = str(self.ptr)
        else:
            base_detail = self.ptr.fmt(ctx)
        if self.offset == 0:
            offset_detail = ""
        else:
            offset_detail = "+${:X}".format(self.offset)
        return "({}{})".format(base_detail, offset_detail)
    def __str__(self):
        return self.fmt(ctx=None)


A = Reg(reg.A)
B = Reg(reg.B)
C = Reg(reg.C)
D = Reg(reg.D)
E = Reg(reg.E)
H = Reg(reg.H)
L = Reg(reg.L)

AF = Reg(reg.AF)
BC = Reg(reg.BC)
DE = Reg(reg.DE)
HL = Reg(reg.HL)
PC = Reg(reg.PC)
SP = Reg(reg.SP)

HLI = IncReg(reg.HL, inc=True)
HLD = IncReg(reg.HL, inc=False)

stack = Mem(SP, dword=True)

imm8 = Imm(dword=False)
imm16 = Imm(dword=True)
