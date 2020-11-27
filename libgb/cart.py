from os import stat
from .rom import Rom
from .memory import RomBank, FixedWorkRam, MemoryRegion

# 0xA in lower 4 bits turns on, else off
RAM_ENABLE_LO = 0
RAM_ENABLE_HI = 0x1FFF
# in MBC 1, 00 translates to 01
ROM_BANK_NUM_LO = 0x2000
ROM_BANK_NUM_HI = 0x3FFF
# RAM_BANK_NUM region can select upper bits of ROM depending on mode
# only first (lowest?) two bits used
RAM_BANK_NUM_LO = 0x4000
RAM_BANK_NUM_HI = 0x5FFF

RAM_ROM_MODE_LO = 0x6000
RAM_ROM_MODE_HI = 0x7FFF

LATCH_CLK_DATA_LO = 0x6000
LATCH_CLK_DATA_HI = 0x7FFF


ROM_FIXED_LO = 0x0000
ROM_FIXED_HI = 0x3FFF
ROM_BANKED_LO = 0x4000
ROM_BANKED_HI = 0x7FFF

EXTERNAL_RAM_LO = 0xA000
EXTERNAL_RAM_HI = 0xBFFF

class Cart(MemoryRegion):
    pass

class MBC3(Cart):
    name="MBC3"

    def __init__(self, fixed_rom: RomBank, banked_rom: RomBank, ram: FixedWorkRam):
        self.fixed_rom = fixed_rom
        self.banked_rom = banked_rom
        self.ram = ram
        self.ram_rtc_enable = False
        self.rom_bank = 1
        self.ram_bank = 0
        self.clock_latch = 0

    def __contains__(self, addr: int) -> bool:
        return addr in self.fixed_rom or addr in self.banked_rom or addr in self.ram

    @staticmethod
    def from_rom(rom: Rom) -> "MBC3":
        fixed_rom = RomBank(ROM_FIXED_LO, ROM_FIXED_HI, rom.data)
        banked_rom = RomBank(ROM_BANKED_LO, ROM_BANKED_HI, rom.data)
        ram = FixedWorkRam(EXTERNAL_RAM_LO, EXTERNAL_RAM_HI)

        return MBC3(fixed_rom, banked_rom, ram)

    def load(self, addr: int) -> int:
        if addr in self.fixed_rom:
            return self.fixed_rom.load(addr)
        if addr in self.banked_rom:
            return self.banked_rom.load(addr, bank=self.rom_bank)
        if addr in self.ram:
            if self.ram_rtc_enable:
                return self.ram.load(addr)
            else:
                return 0xff
        assert False, "bad addr"

    def store(self, addr: int, val: int):
        if addr in self.ram:
            self.ram.store(addr, val)
        elif RAM_ENABLE_LO <= addr <= RAM_ENABLE_HI:
            self.ram_rtc_enable = (val & 0xa) == 0xa
        elif ROM_BANK_NUM_LO <= addr <= ROM_BANK_NUM_HI:
            if val == 0:
                val = 1
            self.rom_bank = val
        elif RAM_BANK_NUM_LO <= addr <= RAM_BANK_NUM_HI:
            self.ram_bank = val
        elif LATCH_CLK_DATA_LO <= addr <= LATCH_CLK_DATA_HI:
            if self.clock_latch == 0 and val == 1:
                # update clock registers
                pass
            self.clock_latch = val


def from_rom(rom: Rom) -> Cart:
    # assume mbc3 :)
    pass
