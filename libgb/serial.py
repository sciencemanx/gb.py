from .io import IOHandler, SerialIO

SERIAL_IO_PORTS = [e.value for e in SerialIO.__members__.values()]

TRANSFER_START_FLAG = 1 << 7

class SerialIOHandler(IOHandler):
    sb: int
    sc: int
    def __init__(self):
        self.sb = 0
        self.sc = 0
    def __contains__(self, addr: int) -> bool:
        return addr in SERIAL_IO_PORTS
    def load(self, addr: int) -> int:
        return 0
    def store(self, addr: int, val: int):
        if addr == SerialIO.SB.value:
            self.sb = val
        if addr == SerialIO.SC.value:
            self.sc = val
            if val & TRANSFER_START_FLAG:
                print(chr(self.sb), end="")
