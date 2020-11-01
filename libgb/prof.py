from collections import Counter, deque
import enum
from typing import Any, Deque, Dict

history: Deque[Any]
loop_count: Counter
loops: Dict[int, Any]

loop_start = 0
total = 0

def init(maxlen=100):
    global history
    global loop_count
    global loops
    history = deque(maxlen=maxlen)
    loop_count = Counter()
    loops = {}


def update(pc, next_pc, insn):
    global total
    history.appendleft((pc, insn))
    total += insn.cycles

    if insn.step == 0:
        global loop_start
        if loop_start == next_pc:
            loop_count[(loop_start, pc)] += 1
            if loop_start not in loops:
                for i, (addr, _) in enumerate(history):
                    if addr == loop_start:
                        break
                else:
                    i = None
                if i is not None:
                    loops[loop_start] = list(history)[:i+1][::-1]

        loop_start = next_pc



def show(n=30):
    print("top loops:")
    for (start, end), n_hits in loop_count.most_common(10):
        print("{}:".format(n_hits))
        if start in loops:
            cost = sum(insn.cycles for _, insn in loops[start])
            print("\t{:.2f}%".format(cost * n_hits / total * 100))
            for addr, insn in loops[start]:
                print("\t{:04X} - {}".format(addr, insn.mnem))
        else:
            print("\tloop too long ({:04X}:{:04X})".format(start, end))
