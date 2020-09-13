from abc import ABC, abstractmethod
from typing import NamedTuple

class MemoryRegion(ABC):
    name: str
    def __init__(self, lower: int, upper: int, mem: bytearray = None):
        self.lower = lower
        self.upper = upper
        self.mem = mem if mem else bytearray(upper - lower + 1)
    @abstractmethod
    def load(self, addr: int) -> int:
        pass
    @abstractmethod
    def store(self, addr: int, val: int):
        pass
    def __contains__(self, addr: int) -> bool:
        return self.lower <= addr <= self.upper
    def translate(self, addr: int) -> int:
        assert addr in self
        return addr - self.lower
    def __str__(self):
        return "[{:04X}:{:04X}] {}".format(self.lower, self.upper, self.name)

class Unimplemented(MemoryRegion):
    name = "unimplemented"
    def load(self, addr: int) -> int:
        assert 0, "read from 0x{:04x}".format(addr)
    def store(self, addr: int, val: int):
        assert 0, "write to 0x{:04x} = 0x{x}".format(addr, val)

class FixedRom(MemoryRegion):
    name = "fixed-rom-bank"
    def load(self, addr: int) -> int:
        return self.mem[self.translate(addr)]
    def store(self, addr: int, val: int):
        print("! write to rom at 0x{:04x}".format(addr))

class FixedWorkRam(MemoryRegion):
    name = "fixed-work-ram-bank"
    def load(self, addr: int) -> int:
        return self.mem[self.translate(addr)]
    def store(self, addr: int, val: int):
        self.mem[self.translate(addr)] = val

class VideoRam(Unimplemented):
    name = "video-ram"

class ExternalRam(Unimplemented):
    name = "external-ram"

class MirrorRam(Unimplemented):
    name = "mirror-ram"

ROM_BANK_1 = 0x0000 # to 0x3FFF
ROM_BANK_2 = 0x4000 # to 0x7FFF
VIDEO_RAM = 0x8000 # to 0x9FFF
EXTERNAL_RAM = 0xA000 # to 0xBFFF
RAM_BANK_1 = 0xC000 # to 0xCFFF
RAM_BANK_2 = 0xD000 # to 0xDFFF
RAM_MIRROR = 0xE000 # to 0xFDFF (mirrors 0xC000-0xDDFF)
SPRITE_TABLE = 0xFE00 # to FE9F
UNUSABLE = 0xFEA0 # to 0xFEFF
IO_PORTS = 0xFF00 # to 0xFF7F
HIGH_RAM = 0xFF80 # to 0xFFFE
INT_ENABLE_REG = 0xFFFF # to 0xFFFF
MEM_MAX = 0xFFFF

def mk_mmap(rom: bytes):
    return [
        FixedRom(ROM_BANK_1, ROM_BANK_2 - 1, rom[ROM_BANK_1:ROM_BANK_2]),
        FixedRom(ROM_BANK_2, VIDEO_RAM - 1, rom[ROM_BANK_2:VIDEO_RAM]),
        # VideoRam(VIDEO_RAM, EXTERNAL_RAM - 1),
        # ExternalRam(EXTERNAL_RAM, RAM_BANK_1 - 1),
        FixedWorkRam(RAM_BANK_1, RAM_BANK_2 - 1),
        FixedWorkRam(RAM_BANK_2, RAM_MIRROR - 1),
        # Unimplemented(RAM_MIRROR, MEM_MAX),
    ]

class MMU:
    def __init__(self, rom_data: bytes):
        self.mem_map = mk_mmap(rom_data)

    @staticmethod
    def from_rom(rom: str) -> MMU:
        with open(rom, 'rb') as f:
            rom_data = f.read()
        return MMU(rom_data)

    def load(self, addr: int) -> int:
        for region in self.mem_map:
            if addr in region:
                return region.load(addr)
        else:
            assert 0, "read from 0x{:04x}".format(addr)

    def store(self, addr: int, val: int):
        for region in self.mem_map:
            if addr in region:
                region.store(addr, val)
                return
        else:
            assert 0, "read from 0x{:04x}".format(addr)
