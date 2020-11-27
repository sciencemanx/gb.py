from libgb.cart import Cart, MBC3
from typing import NamedTuple
from .memory import ExternalRam, VideoRam, FixedWorkRam, SpriteAttributeTable, Unusable
from .io import IOPorts
from .rom import Rom

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


def get_ram_regions(rom: Rom):
    video_ram = VideoRam(VIDEO_RAM, EXTERNAL_RAM - 1)
    ram_1 = FixedWorkRam(RAM_BANK_1, RAM_BANK_2 - 1)
    ram_2 = FixedWorkRam(RAM_BANK_2, RAM_MIRROR - 1)
    return video_ram, ram_1, ram_2


class MMU(NamedTuple):
    cart: Cart
    video_ram: VideoRam
    ram_1: FixedWorkRam
    ram_2: FixedWorkRam
    oam: SpriteAttributeTable
    unusable: Unusable
    io_ports: IOPorts
    hi_ram: FixedWorkRam

    @staticmethod
    def from_rom(rom: Rom):
        cart = MBC3.from_rom(rom)
        video_ram, ram_1, ram_2 = get_ram_regions(rom)
        oam = SpriteAttributeTable(SPRITE_TABLE, UNUSABLE - 1)
        unusable = Unusable(UNUSABLE, IO_PORTS - 1)
        io = IOPorts(IO_PORTS, HIGH_RAM - 1)
        hi_ram = FixedWorkRam(HIGH_RAM, INT_ENABLE_REG - 1)
        hi_ram.name = "hi-ram"
        return MMU(cart, video_ram, ram_1, ram_2, oam, unusable, io, hi_ram)

    def mem_map(self):
        return list(self)

    def where(self, addr: int) -> str:
        for region in self.mem_map():
            if addr in region:
                return region.name
        else:
            return "unk"

    def load(self, addr: int) -> int:
        for region in self.mem_map():
            if addr in region:
                return region.load(addr)
        else:
            print("!!! read from 0x{:04x}".format(addr))
            return 0xff

    def load_nn(self, addr: int) -> int:
        lo = self.load(addr)
        hi = self.load(addr + 1)
        return (hi << 8) + lo

    def store(self, addr: int, val: int):
        for region in self.mem_map():
            if addr in region:
                region.store(addr, val & 0xff)
                return
        else:
            print("!!! write to 0x{:04x}".format(addr))

    def store_nn(self, addr: int, val: int):
        lo = val & 0xff
        hi = val >> 8
        self.store(addr, lo)
        self.store(addr + 1, hi)
