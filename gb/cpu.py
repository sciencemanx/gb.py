import json
from typing import List, NamedTuple

OPCODES_PATH = "gb/opcodes.json"
OPCODES = json.loads(open(OPCODES_PATH, "r").read())


class Insn(NamedTuple):
    mnem: str
    ops: List[str]
    cycles: int
    size: int

    def __str__(self):
        op_str = ", ".join(self.ops)
        return "{} {}".format(self.mnem, op_str)


def n(b: bytes):
    pass


def nn(bb: bytes):
    pass


def disass(bs: bytes) -> Insn:
    if bs[0] == 0xCB:  # opcode prefix
        opcodes = OPCODES["cbprefixed"]
        opcode = bs[1]
    else:
        opcodes = OPCODES["unprefixed"]
        opcode = bs[0]

    insn = opcodes[hex(opcode)]

    mnem = insn["mnemonic"]
    ops = [insn.get("operand1"), insn.get("operand2")]
    ops = [op for op in ops if op is not None]
    cycles = insn["cycles"][0]
    size = insn["length"]

    return Insn(mnem, ops, cycles, size)
