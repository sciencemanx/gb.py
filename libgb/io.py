from abc import ABC, abstractmethod
from enum import Enum
from typing import List

from . import memory


class JoypadIO(Enum):
    JOYP = 0xFF00


class SerialIO(Enum):
    SB = 0xFF01
    SC = 0xFF02


class TimerIO(Enum):
    DIV = 0xFF04
    TIMA = 0xFF05
    TMA = 0xFF06
    TAC = 0xFF07


class SoundIO(Enum):
    NR10 = 0xFF10
    NR11 = 0xFF11
    NR12 = 0xFF12
    NR13 = 0xFF13
    NR14 = 0xFF14
    NR21 = 0xFF16
    NR22 = 0xFF17
    NR23 = 0xFF18
    NR24 = 0xFF19
    NR30 = 0xFF1A
    NR31 = 0xFF1B
    NR32 = 0xFF1C
    NR33 = 0xFF1D
    NR34 = 0xFF1E
    NR41 = 0xFF20
    NR42 = 0xFF21
    NR43 = 0xFF22
    NR44 = 0xFF23
    NR50 = 0xFF24
    NR51 = 0xFF25
    NR52 = 0xFF26


class InterruptIO(Enum):
    IF = 0xFF0F
    IE = 0xFFFF


class DisplayIO(Enum):
    LCDC = 0xFF40
    STAT = 0xFF41
    SCY = 0xFF42
    SCX = 0xFF43
    LY = 0xFF44
    LYC = 0xFF45
    DMA = 0xFF46
    BGP = 0xFF47
    OBP0 = 0xFF48
    OBP1 = 0xFF49
    WY = 0xFF4A
    WX = 0xFF4B


class IOHandler(ABC):
    @abstractmethod
    def load(self, addr: int) -> int:
        pass
    @abstractmethod
    def store(self, addr: int, val: int):
        pass
    @abstractmethod
    def __contains__(self, addr: int) -> bool:
        pass


class IOPorts(memory.MemoryRegion):
    name = "io-ports"
    handlers: List[IOHandler] = []

    def __contains__(self, addr: int) -> bool:
        return super().__contains__(addr) or addr == 0xFFFF

    def register_handler(self, handler: IOHandler):
        self.handlers.append(handler)

    def load(self, addr: int) -> int:
        for handler in self.handlers:
            if addr in handler:
                return handler.load(addr)
        else:
            print("returning 0xff for {:02X}".format(addr))
            return 0xff

    def store(self, addr: int, val: int):
        for handler in self.handlers:
            if addr in handler:
                handler.store(addr, val)
                return
