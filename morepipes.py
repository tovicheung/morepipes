from pipe import Pipe
from itertools import islice, count
from collections import deque
from collections.abc import Iterable

from typing import Self

_EMPTY = object()

# Partial pipes
class _PartialPipe(Pipe):
    def __or__(self, other) -> Self:
        if isinstance(other, Pipe):
            return type(self)(lambda obj, *args, **kwargs: other.function(self.function(obj, *args, **kwargs)))
        return NotImplemented

P = _PartialPipe(lambda x: x) # must be constructed like this


# Pipe tail
# These pipes should be the tail of pipes in most cases
# May not necessarily return iterable that can be further piped

from pipe import sort, reverse

@Pipe
def collect(iterable, typ=_EMPTY):
    # consumes iterator if typ is not specified
    if typ is _EMPTY:
        deque(iterable, maxlen=0) # consume at C speed without storing elements
    else:
        return typ(iterable)

@Pipe
def ilen(iterable):
    counter = count()
    deque(zip(iterable, counter), maxlen=0) # consume at C speed without storing elements
    return next(counter)

@Pipe
def flattento(iterable, typ):
    return iterable | flatten | collect(typ)

# Side effects

@Pipe
def foreach(iterable, func):
    for item in iterable:
        func(item)
        yield item

@Pipe
def inspect(iterable):
    return iterable | foreach(print)


# Manipulate iterables
# Length of iterable may change, lazy evaluated

from pipe import take, tail

@Pipe
def drop(iterable, n):
    return islice(iterable, n, None)

@Pipe
def butlast(iterable):
    it = iter(iterable)
    try:
        prev = next(it)
    except StopIteration:
        pass
    else:
        for item in it:
            yield prev
            prev = item

@Pipe
def flatten(iterable):
    for item in iterable:
        if isinstance(item, Iterable):
            for x in item:
                yield x
        else:
            yield item

@Pipe
def interpose(iterable, sep):
    it = iter(iterable)
    try:
        yield next(it)
    except StopIteration:
        pass
    else:
        for item in it:
            yield sep
            yield item


# Transform and filter iterables
# Length of iterable may change (often by predicate), lazily evaluated

from pipe import select, where

def _complement(func):
    def f(*args, **kwargs):
        return not func(*args, **kwargs)
    return f

pmap = select

@Pipe
def wherenot(iterable, predicate):
    return filter(_complement(predicate), iterable)

reject = wherenot # not related to select

@Pipe
def keep(iterable, f):
    return iterable | pmap(f) | where(bool)

if __name__ == "__main__":
    def iseven(value):
        return value % 2 == 0

    def ismul3(value):
        return value % 3 == 0
    
    assert range(9) | butlast | collect(list) == list(range(8))
    assert range(9) | take(3) | ilen == 3
    assert [[1, 2, 3], (9, 8, 7), 4, 6] | flatten | collect(list) == [[1, 2, 3], (9, 8, 7), 4, 6] | flattento(list) == [1, 2, 3, 9, 8, 7, 4, 6]
    assert range(4) | interpose(-1) | collect(list) == [0, -1, 1, -1, 2, -1, 3]

    assert range(9) | where(iseven) | wherenot(ismul3) | collect(list) == [2, 4, 8]
    assert range(9) | keep(lambda x: x % 3) | collect(list) == [1, 2, 1, 2, 1, 2]

    s = P | where(iseven) | wherenot(ismul3)
    assert range(9) | s | collect(list) == [2, 4, 8]
