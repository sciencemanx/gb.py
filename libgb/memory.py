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
        print("! write to {} at 0x{:04x}".format(self.name, addr))

class FixedWorkRam(MemoryRegion):
    name = "fixed-work-ram-bank"
    def load(self, addr: int) -> int:
        return self.mem[self.translate(addr)]
    def store(self, addr: int, val: int):
        self.mem[self.translate(addr)] = val

class VideoRam(FixedWorkRam):
    name = "video-ram"

class ExternalRam(Unimplemented):
    name = "external-ram"

class MirrorRam(Unimplemented):
    name = "mirror-ram"

class IOPorts(FixedRom):
    PORTS = {
        0xFF07: "TAC",
        0xFF0F: "IF",
        0xFF24: "NR50",
        0xFF25: "NR51",
        0xFF26: "NR52",
        0xFF40: "LCDC",
        0xFF42: "SCY",
        0xFF43: "SCX",
        0xFF44: "LY",
        0xFF45: "LYC",
        0xFF47: "BGP",
    }
    name = "io-ports"
    def load(self, addr: int) -> int:
        # if addr in IOPorts.PORTS:
        #     print("! load from {}".format(IOPorts.PORTS[addr]))
        # else:
        #     print("! load from unknown IO Port 0x{:04X}".format(addr))
        if addr == 0xFF44:
            return 0x94
        return 0
    def store(self, addr: int, val: int):
        if addr == 0xFF01:
            self.SB = val
            return
        if addr == 0xFF02:
            print(chr(self.SB), end="")
            return
        # if addr in IOPorts.PORTS:
        #     print("! store to {} = ${:02X}".format(IOPorts.PORTS[addr], val))
        # else:
        #     print("! store to unknown IO Port 0x{:04X} = ${:02X}".format(addr, val))

class InterruptEnableFlag(FixedRom):
    name = "interrupt-enable-flag"
