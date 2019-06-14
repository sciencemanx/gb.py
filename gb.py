import argparse

from gb.cpu import disass


def main(rom_name: str):
    with open(rom_name, "rb") as rom_file:
        rom = rom_file.read()
    addr = 0
    while addr < len(rom):
        insn = disass(rom[addr:])
        print("{}: {}".format(hex(addr), insn))
        addr += insn.size


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--rom")

    args = parser.parse_args()
    main(args.rom)
