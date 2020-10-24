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
        assert 0, "read in {} from 0x{:04x}".format(self.name, addr)
    def store(self, addr: int, val: int):
        assert 0, "!!! write in {} to 0x{:04x} = 0x{:X}".format(self.name, addr, val)

class FixedRom(MemoryRegion):
    name = "fixed-rom-bank"
    def __init__(self, *args, set_rom_bank=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.set_rom_bank=None
    def load(self, addr: int) -> int:
        return self.mem[self.translate(addr)]
    def store(self, addr: int, val: int):
        if self.set_rom_bank and 0x2000 <= addr < 0x4000:
            self.set_rom_bank(val)
        # print("! write to {} at 0x{:04x} = 0x{:X}".format(self.name, addr, val))

class BankedRom(MemoryRegion):
    name = "banked-rom-bank"
    bank = 1
    def set_bank(self, bank: int):
        self.bank = bank
    def get_bank(self) -> bytes:
        size = self.upper - self.lower + 1
        bank_start = size * (self.bank - 1)
        return self.mem[bank_start:bank_start+size]
    def load(self, addr: int) -> int:
        return self.get_bank()[self.translate(addr)]
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
    def store(self, addr: int, val: int):
        return

class MirrorRam(Unimplemented):
    name = "mirror-ram"
