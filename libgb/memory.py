from abc import ABC, abstractmethod

class MemoryRegion(ABC):
    name: str
    def __init__(self, lower: int, upper: int, mem: bytearray = None):
        self.lower = lower
        self.upper = upper
        self.size = upper - lower + 1
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
        assert 0, "read in {} from 0x{:04x}".format(self.name, addr)
    def store(self, addr: int, val: int):
        assert 0, "!!! write in {} to 0x{:04x} = 0x{:X}".format(self.name, addr, val)

class RomBank(MemoryRegion):
    name = "rom-bank"
    def load(self, addr: int, bank=0) -> int:
        base = self.size * bank
        return self.mem[base + self.translate(addr)]
    def store(self, addr: int, val: int):
        print("! write to {} at 0x{:04x} = 0x{:X}".format(self.name, addr, val))

class FixedWorkRam(MemoryRegion):
    name = "fixed-work-ram-bank"
    def load(self, addr: int) -> int:
        return self.mem[self.translate(addr)]
    def store(self, addr: int, val: int):
        self.mem[self.translate(addr)] = val

class Unusable(MemoryRegion):
    name = "unusable"
    def load(self, addr: int) -> int:
        return 0xff
    def store(self, addr: int, val: int):
        pass

class VideoRam(FixedWorkRam):
    name = "video-ram"

class SpriteAttributeTable(FixedWorkRam):
    name = "sprite-attribute-table"

class ExternalRam(Unimplemented):
    name = "external-ram"
    def store(self, addr: int, val: int):
        return

class MirrorRam(Unimplemented):
    name = "mirror-ram"
