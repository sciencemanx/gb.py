from libgb.instr import ret
from .cpu import CPU, CPU_CLOCK, Interrupt
from .io import IOHandler, TimerIO


DIV_HZ = 16384
DIV_TICKS = CPU_CLOCK // DIV_HZ

MODE_HZ = [
    4096,
    262144,
    65536,
    16384,
]
MODE_TICKS = [CPU_CLOCK // hz for hz in MODE_HZ]


TAC_RUNNING_BIT = 1 << 2
TAC_MODE_MASK = 0x3
TAC_MASK = 0x7

TIMER_IO_PORTS = [e.value for e in TimerIO.__members__.values()]


class Timer:
    div: int
    tima: int
    tma: int
    tac: int
    ticks: int

    def is_running(self):
        return self.tac & TAC_RUNNING_BIT != 0

    def get_mode(self):
        return self.tac & TAC_MODE_MASK

    def __init__(self):
        self.div = 0
        self.tima = 0
        self.tma = 0
        self.tac = 0
        self.ticks = 0

    def step(self, cpu: CPU):
        self.ticks += 1
        if self.ticks % DIV_TICKS == 0:
            self.div += 1
            if self.div > 0xff:
                self.div = 0
        if not self.is_running():
            return
        if self.ticks % MODE_TICKS[self.get_mode()] == 0:
            self.tima += 1
            if self.tima > 0xff:
                cpu.request_interrupt(Interrupt.TIMER)
                self.tima = self.tma


class TimerIOHandler(IOHandler):
    def __init__(self, timer: Timer):
        self.timer = timer
    def __contains__(self, addr: int) -> bool:
        return addr in TIMER_IO_PORTS
    def load(self, addr: int) -> int:
        port = TimerIO(addr)
        if port is TimerIO.DIV:
            return self.timer.div
        elif port is TimerIO.TAC:
            return self.timer.tac
        elif port is TimerIO.TMA:
            return self.timer.tma
        elif port is TimerIO.TIMA:
            return self.timer.tima
        else:
            assert 0
    def store(self, addr: int, val: int):
        port = TimerIO(addr)
        if port is TimerIO.DIV:
            self.timer.div = 0
        elif port is TimerIO.TAC:
            self.timer.tac = val & TAC_MASK
        elif port is TimerIO.TMA:
            self.timer.tma = val
        elif port is TimerIO.TIMA:
            self.timer.tima = val
        else:
            assert 0
