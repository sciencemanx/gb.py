import time
from typing import NamedTuple

from . import cpu
from . import gpu
from . import joypad
from . import mmu
from . import rom
from . import serial
from . import timer
from . import prof

class Gameboy(NamedTuple):
    cpu: cpu.CPU
    gpu: gpu.GPU
    mmu: mmu.MMU
    timer: timer.Timer

    def run(self):
        done = False
        start = time.time()
        ticks = 0
        prof.init()
        while not done:
            try:
                if ticks >= self.cpu.cycles:
                    done |= self.cpu.step(self.mmu)
                done |= self.gpu.step(self.cpu, self.mmu)
                self.timer.step(self.cpu)
                ticks += 1
            except:
                done = True
                print("-- branch history --")
                for addr in self.cpu.branch:
                    print("${:04X}".format(addr))
                print("-- -- --")
                self.cpu.show_trace()
        end = time.time()
        prof.show()
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
