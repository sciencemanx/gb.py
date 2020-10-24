from enum import Enum
from typing import NamedTuple

TITLE_START_OFFSET = 0x134
TITLE_END_OFFSET = 0x143
CGB_FLAG_OFFSET = 0x143
CARTRIDGE_TYPE_OFFSET = 0x147
ROM_SIZE_OFFSET = 0x148
RAM_SIZE_OFFSET = 0x149


class CartridgeType(Enum):
    ROM_ONLY = 0x00
    MBC1 = 0x01
    MBC1_RAM = 0x02
    MBC1_RAM_BATTERY = 0x03
    MBC2 = 0x05
    MBC2_BATTERY = 0x06
    ROM_RAM = 0x08
    ROM_RAM_BATTERY = 0x09
    MMM01 = 0x0B
    MMM01_RAM = 0x0C
    MMM01_RAM_BATTERY = 0x0D
    MBC3_TIMER_BATTERY = 0x0F
    MBC3_TIMER_RAM_BATTERY = 0x10
    MBC3 = 0x11
    MBC3_RAM = 0x12
    MBC3_RAM_BATTERY = 0x13
    MBC4 = 0x15
    MBC4_RAM = 0x16
    MBC4_RAM_BATTERY = 0x17
    MBC5 = 0x19
    MBC5_RAM = 0x1A
    MBC5_RAM_BATTERY = 0x1B
    MBC5_RUMBLE = 0x1C
    MBC5_RUMBLE_RAM = 0x1D
    MBC5_RUMBLE_RAM_BATTERY = 0x1E
    POCKET_CAMERA = 0xFC
    BANDAI_TAMA5 = 0xFD
    HuC3 = 0xFE
    HuC1_RAM_BATTERY = 0xFF


class CGBSupport(Enum):
    GB = -1
    CGB_ENHANCED = 0x80
    CGB_ONLY = 0xC0

CGB_CODES = [e.value for e in CGBSupport.__members__.values()]


class Header(NamedTuple):
    title: str
    cart_type: CartridgeType
    rom_code: int
    ram_code: int
    cgb: CGBSupport

    @staticmethod
    def from_rom(rom: bytes):
        whole_title = rom[TITLE_START_OFFSET:TITLE_END_OFFSET + 1]
        title = whole_title[:whole_title.find(0)].decode()

        cart_type = CartridgeType(rom[CARTRIDGE_TYPE_OFFSET])

        rom_code = rom[ROM_SIZE_OFFSET]
        ram_code = rom[RAM_SIZE_OFFSET]

        cgb_code = rom[CGB_FLAG_OFFSET]
        cgb = CGBSupport(cgb_code) if cgb_code in CGB_CODES else CGBSupport.GB

        return Header(title, cart_type, rom_code, ram_code, cgb)

class Rom(NamedTuple):
    header: Header
    data: bytes

    @staticmethod
    def from_file(path: str):
        with open(path, "rb") as f:
            data = f.read()
        header = Header.from_rom(data)

        return Rom(header, data)
