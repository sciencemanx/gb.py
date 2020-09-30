from collections import deque
from enum import IntFlag

from . import instr, reg
from .mmu import MMU
from .reg import Regs
from .io import InterruptIO, IOHandler


CPU_CLOCK = 4194304


VBLANK_INT = 1 << 0
LCD_STAT_INT = 1 << 1
TIMER_INT = 1 << 2
SERIAL_INT = 1 << 3
JOYPAD_INT = 1 << 4

class Interrupt(IntFlag):
    VBLANK = VBLANK_INT
    LCD_STAT = LCD_STAT_INT
    TIMER = TIMER_INT
    SERIAL = SERIAL_INT
    JOYPAD = JOYPAD_INT


INTERRUPT_VECTOR = [
    (VBLANK_INT, 0x40),
    (LCD_STAT_INT, 0x48),
    (TIMER_INT, 0x50),
    (SERIAL_INT, 0x58),
    (JOYPAD_INT, 0x60),
]


class CPU:
    if_vector: int
    ie_vector: int
    def __init__(self, max_execs=None):
        self.execs = 0
        self.cycles = 0
        self.max_execs = max_execs
        self.execed = []
        self.bps = []
        self.single_step = False
        self.trace = deque(maxlen=20)

        self.if_vector = 0
        self.ie_vector = 0

        self.regs = Regs()
        self.regs.store(reg.AF, 0x01B0)
        self.regs.store(reg.BC, 0x0013)
        self.regs.store(reg.DE, 0x00D8)
        self.regs.store(reg.HL, 0x014D)
        self.regs.store(reg.SP, 0xFFFE)
        self.regs.store(reg.PC, 0x0100)


    def request_interrupt(self, i: Interrupt):
        self.if_vector |= i.value


    def service_interrupts(self, mmu: MMU):
        if self.ie_vector & self.if_vector == 0:
            return
        triggered_interrupts = self.ie_vector & self.if_vector
        for interrupt, target in INTERRUPT_VECTOR:
            if interrupt & triggered_interrupts != 0:
                self.if_vector &= ~interrupt
                instr.interrupt(self.regs, mmu, target)
                self.regs.halted = False
                return

    def step(self, mmu: MMU, show=False) -> bool:
        if self.regs.IME:
            self.service_interrupts(mmu)

        if self.regs.halted:
            return False

        pc = self.regs.load(reg.PC)
        op = mmu.load(pc)
        inst = instr.exec_instr(op, self.regs, mmu)
        self.trace.append((pc, inst.mnem))
        if pc in self.bps:
            self.single_step = True
            for t in self.trace:
                print("{:04X}: {}".format(t[0], t[1]))


        if show or self.single_step:
            print("{:04X}:{:02X} {}".format(pc, op, inst.mnem))
        if self.single_step:
            print(self.regs)
            if input() == "c":
                self.single_step = False

        self.regs.store(reg.PC, self.regs.load(reg.PC) + inst.step)

        self.cycles += inst.cycles

        self.execs += 1
        done = self.max_execs and self.execs > self.max_execs
        done |= inst.cycles == -1

        if done:
            print(inst.mnem)

        return done


class InterruptIOHandler(IOHandler):
    def __init__(self, cpu: CPU):
        self.cpu = cpu
    def __contains__(self, addr: int) -> bool:
        return addr in [InterruptIO.IF.value, InterruptIO.IE.value]
    def load(self, addr: int) -> int:
        port = InterruptIO(addr)
        if port == InterruptIO.IF:

            return self.cpu.if_vector
        if port == InterruptIO.IE:
            return self.cpu.ie_vector
        assert 0
    def store(self, addr: int, val: int):
        port = InterruptIO(addr)
        if port == InterruptIO.IF:
            self.cpu.if_vector = val
        if port == InterruptIO.IE:
            self.cpu.ie_vector = val
