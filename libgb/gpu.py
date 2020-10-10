from enum import IntFlag
from typing import Dict, List

from .cpu import CPU, Interrupt
from .io import IOHandler, DisplayIO
from .lcd import LCD
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



def load_tile(tile_bs: bytes):
    assert len(tile_bs) == 16
    tile = [[0] * 8 for _ in range(8)]
    for i in range(8):
        lo = tile_bs[2 * i]
        hi = tile_bs[2 * i + 1]
        for j in range(8):
            lo_color = int(lo & (1 << j) != 0)
            hi_color = int(hi & (1 << j) != 0)
            color = lo_color + (hi_color << 1)
            tile[i][7 - j] = color
    return tile


def load_tiles(tile_bs: bytes):
    assert len(tile_bs) % 16 == 0
    return [load_tile(tile_bs[i:i + 16]) for i in range(0, len(tile_bs), 16)]


def load_sprite(sprite_bs: bytes):
    assert len(sprite_bs) == 4
    y = sprite_bs[0]
    x = sprite_bs[1]
    tile_idx = sprite_bs[2]
    flags = sprite_bs[3]
    return x, y, tile_idx, flags


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
        self.lcd = LCD()

    def get_palette(self, palette_reg: DisplayIO):
        bgp = self.regs[palette_reg]
        return [bgp & 3, (bgp >> 2) & 3, (bgp >> 4) & 3, (bgp >> 6) & 3]

    def render_bg(self, display, tiles, tile_map, offset):
        palette = self.get_palette(DisplayIO.BGP)

        bg = [[0] * 256 for _ in range(256)]
        for i, tile_idx in enumerate(tile_map):
            tile = tiles[(tile_idx + offset) % 256]
            x, y = i % 32, i // 32
            for j in range(8):
                for k in range(8):
                    bg[(x * 8) + j][(y * 8) + k] = palette[tile[k][j]]

        scx = self.regs[DisplayIO.SCX]
        scy = self.regs[DisplayIO.SCY]

        for i in range(160):
            for j in range(144):
                display[i][j] = bg[(i + scx) % 256][(j + scy) % 256]

    def render_obj(self, display, tiles, sprites):
        palette_0 = self.get_palette(DisplayIO.OBP0)
        palette_1 = self.get_palette(DisplayIO.OBP0)

        for X,Y,idx,flags in reversed(sorted(sprites)):
            if 0 in (X, Y):
                continue
            x_flip = (flags & (1 << 5)) != 0
            y_flip = (flags & (1 << 6)) != 0
            tile = tiles[idx]
            X -= 8
            Y -= 16
            palette = palette_0 if flags & 0x10 == 0 else palette_1
            for i in range(8):
                for j in range(8):
                    x_off = 7 - i if x_flip else i
                    y_off = 7 - j if y_flip else j
                    x = X + x_off
                    y = Y + y_off
                    color = tile[j][i]
                    if 0 <= x < 160 and 0 <= y < 144 and color != 0:
                        display[x][y] = palette[color]

    def draw_display(self, mmu: MMU):
        lcdc = LCDC(self.regs[DisplayIO.LCDC])
        display = [[0] * 144 for _ in range(160)]

        if LCDC.BG_WINDOW_DATA_SELECT in lcdc:
            bg_window_data_range = (0x8000, 0x8FFF)
            offset = 0
        else:
            bg_window_data_range = (0x8800, 0x97FF)
            offset = 128

        if LCDC.BG_DISPLAY in lcdc:
            bg_window_data = get_mem(mmu.video_ram, bg_window_data_range)
            bg_window_tiles = load_tiles(bg_window_data)

            if LCDC.BG_TILE_SELECT in lcdc:
                tile_map = get_mem(mmu.video_ram, BGMAP_2)
            else:
                tile_map = get_mem(mmu.video_ram, BGMAP_1)

            self.render_bg(display, bg_window_tiles, tile_map, offset)

        if LCDC.OBJ_DISPLAY in lcdc:
            obj_tile_data = get_mem(mmu.video_ram, (0x8000, 0x8FFF))
            obj_tiles = load_tiles(obj_tile_data)
            obj_map = mmu.oam.mem
            sprites = [load_sprite(obj_map[i:i+4]) for i in range(0, len(obj_map), 4)]
            self.render_obj(display, obj_tiles, sprites)

        self.lcd.draw_display(display)

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
                self.draw_display(mmu)

            self.next_ly = LY_CLKS

    def dump(self, mmu: MMU):
        block_0 = get_mem(mmu.video_ram, BLOCK_0)
        block_1 = get_mem(mmu.video_ram, BLOCK_1)
        block_2 = get_mem(mmu.video_ram, BLOCK_2)
        bgmap_1 = get_mem(mmu.video_ram, BGMAP_1)
        bgmap_2 = get_mem(mmu.video_ram, BGMAP_2)


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
            return self.gpu.regs[port]
    def store(self, addr: int, val: int):
        port = DisplayIO(addr)
        if port is DisplayIO.STAT:
            print("STAT: ${:02X}".format(val))
        if port is DisplayIO.DMA:
            src_start = val << 8
            dst_start = 0xFE00
            for i in range(0xA0):
                v = self.mmu.load(src_start + i)
                self.mmu.store(dst_start + i, v)
        else:
            mask = DISPLAY_MASK.get(port, 0xff)
            inv_mask = (~mask) & 0xff
            old = self.gpu.regs[port]
            self.gpu.regs[port] = (val & mask) | (old & inv_mask)
