from collections import Counter, deque
from typing import Deque

history: Deque[str]
hits: Counter
hot_spots: Counter

loop_start = 0
loop_count: Counter = Counter()

def init(n=3):
    global history
    global hits
    global hot_spots
    global loop_count
    history = deque(maxlen=n)
    hits = Counter()
    hot_spots = Counter()
    loop_count = Counter()


def update(pc, next_pc, insn):
    if insn.step == 0:
        global loop_start
        if loop_start == next_pc:
            loop_count[(loop_start, pc)] += 1
        loop_start = next_pc

    op = insn.mnem.split()[0]
    history.append(op)
    hits[tuple(history)] += 1
    hot_spots[(pc,insn.mnem)] += 1


def show(n=30):
    print("\nngrams:")
    for hit, n_hits in hits.most_common(n):
        print("{}: {}".format(n_hits, " -> ".join(hit)))
    print("hotspots:")
    for (spot, mnem), n_hits in hot_spots.most_common(200):
        print("{}: {:04X} - {}".format(n_hits, spot, mnem))
    print("top loops:")
    for (start, end), n_hits in loop_count.most_common(20):
        print("{}: {:04X} - {:04X}".format(n_hits, start, end))
