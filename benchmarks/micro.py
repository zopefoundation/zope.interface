import pyperf

from zope.interface import Interface
from zope.interface import classImplements
from zope.interface import implementedBy
from zope.interface.interface import InterfaceClass
from zope.interface.registry import Components

# Long, mostly similar names are a worst case for equality
# comparisons.
ifaces = [
    InterfaceClass('I' + ('0' * 20) + str(i), (Interface,), {})
    for i in range(100)
]

class IWideInheritance(*ifaces):
    """
    Inherits from 100 unrelated interfaces.
    """

class WideInheritance(object):
    pass
classImplements(WideInheritance, IWideInheritance)

def make_deep_inheritance():
    children = []
    base = Interface
    for iface in ifaces:
        child = InterfaceClass('IDerived' + base.__name__, (iface, base,), {})
        base = child
        children.append(child)
    return children

deep_ifaces = make_deep_inheritance()

class DeepestInheritance(object):
    pass
classImplements(DeepestInheritance, deep_ifaces[-1])


class ImplementsNothing(object):
    pass


class HasConformReturnNone(object):
    def __conform__(self, iface):
        return None


class HasConformReturnObject(object):
    def __conform__(self, iface):
        return self


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

INNER = 100

def bench_in(loops, o):
    t0 = pyperf.perf_counter()
    for _ in range(loops):
        for _ in range(INNER):
            o.__contains__(Interface)

    return pyperf.perf_counter() - t0

def bench_sort(loops, objs):
    import random
    rand = random.Random(8675309)

    shuffled = list(objs)
    rand.shuffle(shuffled)

    t0 = pyperf.perf_counter()
    for _ in range(loops):
        for _ in range(INNER):
            sorted(shuffled)

    return pyperf.perf_counter() - t0

def bench_query_adapter(loops, components, objs=providers):
    components_queryAdapter = components.queryAdapter
    # One time through to prime the caches
    for iface in ifaces:
        for provider in providers:
            components_queryAdapter(provider, iface)

    t0 = pyperf.perf_counter()
    for _ in range(loops):
        for iface in ifaces:
            for provider in objs:
                components_queryAdapter(provider, iface)
    return pyperf.perf_counter() - t0


def bench_getattr(loops, name, get=getattr):
    t0 = pyperf.perf_counter()
    for _ in range(loops):
        for _ in range(INNER):
            get(Interface, name) # 1
            get(Interface, name) # 2
            get(Interface, name) # 3
            get(Interface, name) # 4
            get(Interface, name) # 5
            get(Interface, name) # 6
            get(Interface, name) # 7
            get(Interface, name) # 8
            get(Interface, name) # 9
            get(Interface, name) # 10
    return pyperf.perf_counter() - t0


def bench_iface_call_no_conform_no_alternate_not_provided(loops):
    inst = ImplementsNothing()
    t0 = pyperf.perf_counter()
    for _ in range(loops):
        for _ in range(INNER):
            for iface in ifaces:
                try:
                    iface(inst)
                except TypeError:
                    pass
                else:
                    raise TypeError("Should have failed")
    return pyperf.perf_counter() - t0


def bench_iface_call_no_conform_w_alternate_not_provided(loops):
    inst = ImplementsNothing()
    t0 = pyperf.perf_counter()
    for _ in range(loops):
        for _ in range(INNER):
            for iface in ifaces:
                iface(inst, 42)
    return pyperf.perf_counter() - t0


def bench_iface_call_w_conform_return_none_not_provided(loops):
    inst = HasConformReturnNone()
    t0 = pyperf.perf_counter()
    for _ in range(loops):
        for _ in range(INNER):
            for iface in ifaces:
                iface(inst, 42)
    return pyperf.perf_counter() - t0


def bench_iface_call_w_conform_return_non_none_not_provided(loops):
    inst = HasConformReturnObject()
    t0 = pyperf.perf_counter()
    for _ in range(loops):
        for _ in range(INNER):
            for iface in ifaces:
                iface(inst)
    return pyperf.perf_counter() - t0

def _bench_iface_call_simple(loops, inst):
    t0 = pyperf.perf_counter()
    for _ in range(loops):
        for _ in range(INNER):
            for iface in ifaces:
                iface(inst)
    return pyperf.perf_counter() - t0


def bench_iface_call_no_conform_provided_wide(loops):
    return _bench_iface_call_simple(loops, WideInheritance())


def bench_iface_call_no_conform_provided_deep(loops):
    return _bench_iface_call_simple(loops, DeepestInheritance())


runner = pyperf.Runner()

runner.bench_time_func(
    'call interface (provides; deep)',
    bench_iface_call_no_conform_provided_deep,
    inner_loops=INNER * len(ifaces)
)

runner.bench_time_func(
    'call interface (provides; wide)',
    bench_iface_call_no_conform_provided_wide,
    inner_loops=INNER * len(ifaces)
)

runner.bench_time_func(
    'call interface (no alternate, no conform, not provided)',
    bench_iface_call_no_conform_no_alternate_not_provided,
    inner_loops=INNER * len(ifaces)
)

runner.bench_time_func(
    'call interface (alternate, no conform, not provided)',
    bench_iface_call_no_conform_w_alternate_not_provided,
    inner_loops=INNER * len(ifaces)
)

runner.bench_time_func(
    'call interface (no alternate, valid conform, not provided)',
    bench_iface_call_w_conform_return_non_none_not_provided,
    inner_loops=INNER * len(ifaces)
)

runner.bench_time_func(
    'call interface (alternate, invalid conform, not provided)',
    bench_iface_call_w_conform_return_none_not_provided,
    inner_loops=INNER * len(ifaces)
)

runner.bench_time_func(
    'read __module__', # stored in C, accessed through __getattribute__
    bench_getattr,
    '__module__',
    inner_loops=INNER * 10
)

runner.bench_time_func(
    'read __name__', # stored in C, accessed through PyMemberDef
    bench_getattr,
    '__name__',
    inner_loops=INNER * 10
)

runner.bench_time_func(
    'read __doc__', # stored in Python instance dictionary directly
    bench_getattr,
    '__doc__',
    inner_loops=INNER * 10
)

runner.bench_time_func(
    'read providedBy', # from the class, wrapped into a method object.
    bench_getattr,
    'providedBy',
    inner_loops=INNER * 10
)

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
    'query adapter (all trivial registrations, wide inheritance)',
    bench_query_adapter,
    populate_components(),
    [WideInheritance()],
    inner_loops=1
)

runner.bench_time_func(
    'query adapter (all trivial registrations, deep inheritance)',
    bench_query_adapter,
    populate_components(),
    [DeepestInheritance()],
    inner_loops=1
)

runner.bench_time_func(
    'sort interfaces',
    bench_sort,
    ifaces,
    inner_loops=INNER,
)

runner.bench_time_func(
    'sort implementedBy',
    bench_sort,
    [implementedBy(p) for p in implementers],
    inner_loops=INNER,
)

runner.bench_time_func(
    'sort mixed',
    bench_sort,
    [implementedBy(p) for p in implementers] + ifaces,
    inner_loops=INNER,
)

runner.bench_time_func(
    'contains (empty dict)',
    bench_in,
    {},
    inner_loops=INNER
)

runner.bench_time_func(
    'contains (populated dict: interfaces)',
    bench_in,
    {k: k for k in ifaces},
    inner_loops=INNER
)

runner.bench_time_func(
    'contains (populated list: interfaces)',
    bench_in,
    ifaces,
    inner_loops=INNER
)

runner.bench_time_func(
    'contains (populated dict: implementedBy)',
    bench_in,
    {implementedBy(p): 1 for p in implementers},
    inner_loops=INNER
)

runner.bench_time_func(
    'contains (populated list: implementedBy)',
    bench_in,
    [implementedBy(p) for p in implementers],
    inner_loops=INNER
)
