from enum import IntFlag
from typing import Dict

from .cpu import CPU, Interrupt
from .io import IOHandler, DisplayIO
# from .lcd import LCD
from .mmu import MMU

BLOCK_0 = 0x8000, 0x87FF
BLOCK_1 = 0x8800, 0x8FFF
BLOCK_2 = 0x9000, 0x97FF
BGMAP_1 = 0x9800, 0x9BFF
BGMAP_2 = 0x9C00, 0x9FFF

DISPLAY_IO_ADDRS = [e.value for e in DisplayIO.__members__.values()]
DISPLAY_MASK = {
    DisplayIO.STAT: 0b01111000,
    DisplayIO.LY: 0x00,
}


class LCDC(IntFlag):
    BG_DISPLAY = 1 << 0
    OBJ_DISPLAY = 1 << 1
    OBJ_SIZE_SELECT = 1 << 2 # 0=8x8, 1=8x16
    BG_TILE_SELECT = 1 << 3 # 0=9800-9BFF, 1=9C00-9FFF
    BG_WINDOW_DATA_SELECT = 1 << 4 # 0=8800-97FF, 1=8000-8FFF
    WINDOW_DISPLAY = 1 << 5
    WINDOW_TILE_SELECT = 1 << 6 # 0=9800-9BFF, 1=9C00-9FFF
    LCD_DISPLAY = 1 << 7


def get_mem(region, lohi):
    lo, hi = lohi
    lo = region.translate(lo)
    hi = region.translate(hi)
    return region.mem[lo:hi+1]


# if LY >= 144 VBLANK
# if LY > 153 wrap to 0

LY_CLKS = 456
VBLANK_START = 144
LY_END = 153

class GPU:
    regs: Dict[DisplayIO, int]
    def __init__(self):
        self.regs = {
            DisplayIO.LCDC: 0,
            DisplayIO.STAT: 0,
            DisplayIO.LY: 0,

            DisplayIO.SCY: 0,
            DisplayIO.SCX: 0,
            DisplayIO.LYC: 0,
            DisplayIO.BGP: 0,
            DisplayIO.OBP0: 0,
            DisplayIO.OBP1: 0,
            DisplayIO.WY: 0,
            DisplayIO.WX: 0,
        }
        self.next_ly = LY_CLKS

    def draw_display(self):
        lcdc = LCDC(self.regs[DisplayIO.LCDC])
        # print(lcdc)
        # if LCDC.BG_DISPLAY in lcdc:
            # print("showing background")

        # print(LCDC(self.regs[DisplayIO.LCDC]))

    def step(self, cpu: CPU, mmu: MMU):
        self.next_ly -= 1
        if self.next_ly == 0:
            self.regs[DisplayIO.LY] += 1

            if self.regs[DisplayIO.LY] > LY_END:
                self.regs[DisplayIO.LY] = 0
            if self.regs[DisplayIO.LY] == self.regs[DisplayIO.LYC]:
                cpu.request_interrupt(Interrupt.LCD_STAT)
            if self.regs[DisplayIO.LY] == VBLANK_START:
                cpu.request_interrupt(Interrupt.VBLANK)
                self.draw_display()

            self.next_ly = LY_CLKS

    def dump(self, mmu: MMU):
        block_0 = get_mem(mmu.video_ram, BLOCK_0)
        block_1 = get_mem(mmu.video_ram, BLOCK_1)
        block_2 = get_mem(mmu.video_ram, BLOCK_2)
        bgmap_1 = get_mem(mmu.video_ram, BGMAP_1)
        bgmap_2 = get_mem(mmu.video_ram, BGMAP_2)

        print(block_1)
        # print(block_2)
        print(self.regs)
        print(bgmap_1)
        # print(bgmap_2)


class DisplayIOHandler(IOHandler):
    def __init__(self, gpu: GPU, mmu: MMU):
        self.gpu = gpu
        self.mmu = mmu
    def __contains__(self, addr: int) -> bool:
        return addr in DISPLAY_IO_ADDRS
    def load(self, addr: int) -> int:
        port = DisplayIO(addr)
        if port is DisplayIO.DMA:
            print("!!! attempting to read from DMA!")
            return 0xff
        else:
            # print("!gpu load from {} = {}".format(repr(port), self.gpu.regs[port]))
            return self.gpu.regs[port]
    def store(self, addr: int, val: int):
        port = DisplayIO(addr)
        if port is DisplayIO.STAT:
            print(val)
        if port is DisplayIO.DMA:
            src_start = val << 8
            dst_start = 0xFE00
            # print("!!! triggering DMA request from {:04X}".format(src_start))
            for i in range(0xA0):
                v = self.mmu.load(src_start + i)
                self.mmu.store(dst_start + i, v)
        else:
            mask = DISPLAY_MASK.get(port, 0xff)
            inv_mask = (~mask) & 0xff
            old = self.gpu.regs[port]
            self.gpu.regs[port] = (val & mask) | (old & inv_mask)
