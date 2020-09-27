from .io import IOHandler, JoypadIO

class JoypadIOHandler(IOHandler):
    def __contains__(self, addr: int) -> bool:
        return addr == JoypadIO.JOYP.value
    def load(self, addr: int) -> int:
        return 0
    def store(self, addr: int, val: int):
        pass
