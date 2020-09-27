from typing import NamedTuple
from .memory import ExternalRam, FixedRom, VideoRam, FixedWorkRam, SpriteAttributeTable, Unusable
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


def get_rom_regions(rom: Rom):
    rom_1 = FixedRom(ROM_BANK_1, ROM_BANK_2 - 1, rom.data[ROM_BANK_1:ROM_BANK_2])
    rom_2 = FixedRom(ROM_BANK_2, VIDEO_RAM - 1, rom.data[ROM_BANK_2:VIDEO_RAM])
    return rom_1, rom_2


def get_ram_regions(rom: Rom):
    video_ram = VideoRam(VIDEO_RAM, EXTERNAL_RAM - 1)
    ext_ram = ExternalRam(EXTERNAL_RAM, RAM_BANK_1 - 1)
    ram_1 = FixedWorkRam(RAM_BANK_1, RAM_BANK_2 - 1)
    ram_2 = FixedWorkRam(RAM_BANK_2, RAM_MIRROR - 1)
    return video_ram, ext_ram, ram_1, ram_2


class MMU(NamedTuple):
    rom_1: FixedRom
    rom_2: FixedRom
    video_ram: VideoRam
    ext_ram: ExternalRam
    ram_1: FixedWorkRam
    ram_2: FixedWorkRam
    # echo:
    oam: SpriteAttributeTable
    unusable: Unusable
    io_ports: IOPorts
    hi_ram: FixedWorkRam

    @staticmethod
    def from_rom(rom: Rom):
        rom_1, rom_2 = get_rom_regions(rom)
        video_ram, ext_ram, ram_1, ram_2 = get_ram_regions(rom)
        oam = SpriteAttributeTable(SPRITE_TABLE, UNUSABLE - 1)
        unusable = Unusable(UNUSABLE, IO_PORTS - 1)
        io = IOPorts(IO_PORTS, HIGH_RAM - 1)
        hi_ram = FixedWorkRam(HIGH_RAM, INT_ENABLE_REG - 1)
        return MMU(rom_1, rom_2, video_ram, ext_ram, ram_1, ram_2, oam, unusable, io, hi_ram)

    def mem_map(self):
        return list(self)

    def load(self, addr: int) -> int:
        for region in self.mem_map():
            if addr in region:
                return region.load(addr)
        else:
            assert 0, "read from 0x{:04x}".format(addr)

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
