import argparse

from gb.cpu import CPU
from gb.gameboy import Gameboy
from gb.mmu import MMU


def main(rom: str):
    cpu = CPU()
    mmu = MMU.from_rom(rom)
    gb = Gameboy(cpu, mmu)
    gb.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("rom")

    args = parser.parse_args()
    main(args.rom)
