from .memory import FixedRom, VideoRam, FixedWorkRam, IOPorts, InterruptEnableFlag
# from .lcd import VideoRam

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
        VideoRam(VIDEO_RAM, EXTERNAL_RAM - 1),
        # ExternalRam(EXTERNAL_RAM, RAM_BANK_1 - 1),
        FixedWorkRam(RAM_BANK_1, RAM_BANK_2 - 1),
        FixedWorkRam(RAM_BANK_2, RAM_MIRROR - 1),
        # Unimplemented(RAM_MIRROR, MEM_MAX),
        IOPorts(IO_PORTS, HIGH_RAM - 1),
        FixedWorkRam(HIGH_RAM, INT_ENABLE_REG - 1),
        InterruptEnableFlag(INT_ENABLE_REG, MEM_MAX),
    ]

class MMU:
    def __init__(self, rom_data: bytes):
        self.mem_map = mk_mmap(rom_data)

    @staticmethod
    def from_rom(rom: str) -> "MMU":
        with open(rom, 'rb') as f:
            rom_data = f.read()
        return MMU(rom_data)

    def load(self, addr: int) -> int:
        for region in self.mem_map:
            if addr in region:
                # print("{} load from 0x{:04X}".format(region, addr))
                return region.load(addr)
        else:
            assert 0, "read from 0x{:04x}".format(addr)

    def load_nn(self, addr: int) -> int:
        lo = self.load(addr)
        hi = self.load(addr + 1)
        return (hi << 8) + lo

    def store(self, addr: int, val: int):
        for region in self.mem_map:
            if addr in region:
                region.store(addr, val)
                return
        else:
            print("!!! write to 0x{:04x}".format(addr))

    def store_nn(self, addr: int, val: int):
        lo = val & 0xff
        hi = val >> 8
        self.store(addr, lo)
        self.store(addr + 1, hi)
