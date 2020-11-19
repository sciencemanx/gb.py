from collections import Counter, deque, defaultdict
import enum
from typing import Any, Deque, Dict, DefaultDict

history: Deque[Any]
loop_count: Counter
loops: Dict[int, Any]
ngrams: DefaultDict[int, Counter]

loop_start = 0
total = 0


def hash_trace(trace):
    return hash(tuple(op for op, _, _ in trace))


def init(maxlen=100):
    global history
    global loop_count
    global loops
    global ngrams
    history = deque(maxlen=maxlen)
    loop_count = Counter()
    loops = {}
    ngrams = defaultdict(Counter)


def update(op, pc, next_pc, insn):
    global total
    history.appendleft((op, pc, insn))
    total += insn.cycles

    if insn.step == 0:
        global loop_start
        if loop_start == next_pc:
            for i, (_, addr, _) in enumerate(history):
                if addr == loop_start:
                    break
            else:
                assert False
            trace = list(history)[:i+1][::-1]
            h = hash_trace(trace)
            loops[h] = trace
            loop_count[h] += 1

        loop_start = next_pc
    else:
        return
        his = tuple(insn.mnem.split()[0] for _, _, insn in history)
        for n in range(3,6):
            last_n = his[:n][::-1]
            ngrams[n][last_n] += 1



def show(n=30):
    print("top loops:")
    for h, n_hits in loop_count.most_common(10):
        print("{}:".format(n_hits))
        if h in loops:
            cost = sum(insn.cycles for _, _, insn in loops[h])
            print("\t{:.2f}%".format(cost * n_hits / total * 100))
            for _, addr, insn in loops[h]:
                print("\t{:04X} - {}".format(addr, insn.mnem))
        else:
            print("\tloop too long")
    for n, grams in ngrams.items():
        print("{}-grams:".format(n))
        for trace, n_hits in grams.most_common(10):
            print("\t{}: {}".format(n_hits, "->".join(trace)))
