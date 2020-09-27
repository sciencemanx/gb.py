from abc import ABC, abstractmethod

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
        assert 0, "write to 0x{:04x} = 0x{:X}".format(addr, val)

class FixedRom(MemoryRegion):
    name = "fixed-rom-bank"
    def load(self, addr: int) -> int:
        return self.mem[self.translate(addr)]
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
        assert 0, "read from 0x{:04x} in {}".format(addr, self.__class__.name)
    def store(self, addr: int, val: int):
        pass

class VideoRam(FixedWorkRam):
    name = "video-ram"

class SpriteAttributeTable(FixedWorkRam):
    name = "sprite-attribute-table"

class ExternalRam(Unimplemented):
    name = "external-ram"

class MirrorRam(Unimplemented):
    name = "mirror-ram"
