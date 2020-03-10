import pyperf

from zope.interface import Interface
from zope.interface import classImplements
from zope.interface.interface import InterfaceClass
from zope.interface.registry import Components

# Long, mostly similar names are a worst case for equality
# comparisons.
ifaces = [
    InterfaceClass('I' + ('0' * 20) + str(i), (Interface,), {})
    for i in range(100)
]

def make_implementer(iface):
    c = type('Implementer' + iface.__name__, (object,), {})
    classImplements(c, iface)
    return c

implementers = [
    make_implementer(iface)
    for iface in ifaces
]

providers = [
    implementer()
    for implementer in implementers
]

INNER = 10

def bench_in(loops, o):
    t0 = pyperf.perf_counter()
    for _ in range(loops):
        for _ in range(INNER):
            o.__contains__(Interface)

    return pyperf.perf_counter() - t0

def bench_query_adapter(loops, components):
    # One time through to prime the caches
    for iface in ifaces:
        for provider in providers:
            components.queryAdapter(provider, iface)

    t0 = pyperf.perf_counter()
    for _ in range(loops):
        for iface in ifaces:
            for provider in providers:
                components.queryAdapter(provider, iface)
    return pyperf.perf_counter() - t0

runner = pyperf.Runner()

runner.bench_time_func(
    'query adapter (no registrations)',
    bench_query_adapter,
    Components(),
    inner_loops=1
)

def populate_components():

    def factory(o):
        return 42

    pop_components = Components()
    for iface in ifaces:
        for other_iface in ifaces:
            pop_components.registerAdapter(factory, (iface,), other_iface, event=False)

    return pop_components

runner.bench_time_func(
    'query adapter (all trivial registrations)',
    bench_query_adapter,
    populate_components(),
    inner_loops=1
)

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
