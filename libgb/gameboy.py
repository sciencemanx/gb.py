import time
from typing import NamedTuple

from . import cpu
from . import gpu
from . import joypad
from . import mmu
from . import rom
from . import serial
from . import timer

class Gameboy(NamedTuple):
    cpu: cpu.CPU
    gpu: gpu.GPU
    mmu: mmu.MMU
    timer: timer.Timer

    def run(self):
        done = False
        start = time.time()
        ticks = 0
        while not done:
            if ticks >= self.cpu.cycles:
                done |= self.cpu.step(self.mmu)
            done |= self.gpu.step(self.cpu, self.mmu)
            self.timer.step(self.cpu)
            ticks += 1
        end = time.time()
        print("-- REGS --")
        print(self.cpu.regs)
        print("num execs: {}".format(self.cpu.execs))
        print("ticks: {}".format(ticks))
        print("cpu secs: {}".format(ticks / cpu.CPU_CLOCK))
        print("wall secs: {}".format(end - start))

    @staticmethod
    def from_rom(rom: rom.Rom):
        c = cpu.CPU()
        g = gpu.GPU()
        m = mmu.MMU.from_rom(rom)
        t = timer.Timer()

        display_io_handler = gpu.DisplayIOHandler(g, m)
        interrupt_io_handler = cpu.InterruptIOHandler(c)
        joypad_io_handler = joypad.JoypadIOHandler()
        serial_io_handler = serial.SerialIOHandler()
        timer_io_handler = timer.TimerIOHandler(t)
        m.io_ports.register_handler(display_io_handler)
        m.io_ports.register_handler(interrupt_io_handler)
        m.io_ports.register_handler(joypad_io_handler)
        m.io_ports.register_handler(serial_io_handler)
        # m.io_ports.register_handler(sound_io_handler)
        m.io_ports.register_handler(timer_io_handler)

        return Gameboy(c, g, m, t)
