import pyperf

from zope.interface import Interface
from zope.interface.interface import InterfaceClass

ifaces = [
    InterfaceClass('I' + str(i), (Interface,), {})
    for i in range(100)
]

INNER = 1000

def bench_in(loops, o):
    t0 = pyperf.perf_counter()
    for _ in range(loops):
        for _ in range(INNER):
            o.__contains__(Interface)

    return pyperf.perf_counter() - t0

runner = pyperf.Runner()

runner.bench_time_func(
    'contains (empty dict)',
    bench_in,
    {},
    inner_loops=INNER
)

runner.bench_time_func(
    'contains (populated dict)',
    bench_in,
    {k: k for k in ifaces},
    inner_loops=INNER
)

runner.bench_time_func(
    'contains (populated list)',
    bench_in,
    ifaces,
    inner_loops=INNER
)
