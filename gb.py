#! pypy3

import argparse
import cProfile
import sys

from libgb.gameboy import Gameboy
from libgb.rom import Rom
from libgb.instr import diag


def main(rom_path: str, max_execs: int, headless: bool):
    if not headless:
        print("warning! display not supported")

    rom = Rom.from_file(rom_path)
    gb = Gameboy.from_rom(rom)
    gb.cpu.max_execs = max_execs

    gb.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("rom")
    parser.add_argument("--max-execs", default="0")
    parser.add_argument("--prof", action="store_true")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--diag", action="store_true")

    args = parser.parse_args()

    if args.diag:
        diag()
        sys.exit(0)

    if args.prof:
        cProfile.run("main('{}', 0, True)".format(args.rom), sort="tottime")
    else:
        main(args.rom, int(args.max_execs), args.headless)
