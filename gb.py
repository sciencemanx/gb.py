import argparse

from libgb.cpu import CPU
from libgb.gameboy import Gameboy
from libgb.mmu import MMU


def main(rom: str, max_execs: int):
    cpu = CPU(max_execs)
    mmu = MMU.from_rom(rom)
    gb = Gameboy(cpu, mmu)
    gb.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("rom")
    parser.add_argument("--max-execs", default="0")

    args = parser.parse_args()
    main(args.rom, int(args.max_execs))
