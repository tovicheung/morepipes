from __future__ import annotations

from pipe import Pipe
import itertools as _itertools
import functools as _functools
from collections import deque
from collections.abc import Iterable, Sequence

_EMPTY = object()

# Partial pipes
class _PartialPipe(Pipe):
    def __or__(self, other) -> "_PartialPipe":
        if isinstance(other, Pipe):
            return type(self)(lambda obj, *args, **kwargs: other.function(self.function(obj, *args, **kwargs)))
        return NotImplemented

P = _PartialPipe(lambda x: x) # must be constructed like this


# Generate iterator
# These pipes take in objects of any type and generate an iterator for piping

@Pipe
def repeat(obj, n=_EMPTY):
    return _itertools.repeat(obj, n)
    # if n is _EMPTY:
    #     while True:
    #         yield obj
    # else:
    #     for _ in range(n):
    #         yield obj


# Pipe tails
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
    counter = _itertools.count()
    deque(zip(iterable, counter), maxlen=0) # consume at C speed without storing elements
    return next(counter)

@Pipe
def flattento(iterable, typ):
    return iterable | flatten | collect(typ)

@Pipe
def isum(iterable):
    return sum(iterable)

@Pipe
def iall(iterable, predicate):
    return all(predicate(x) for x in iterable)

@Pipe
def iany(iterable, predicate):
    return any(predicate(x) for x in iterable)

@Pipe
def first(iterable):
    return next(iter(iterable), None)

@Pipe
def last(iterable):
    if isinstance(iterable, Sequence):
        if len(iterable) < 1:
            return None
        return iterable[-1]
    item = None
    for item in iterable:
        pass
    return item

@Pipe
def find(iterable, predicate):
    return iterable | where(predicate) | first

@Pipe
def reduce(iterable, predicate, initial=_EMPTY):
    if initial is _EMPTY:
        return _functools.reduce(predicate, iterable)
    return _functools.reduce(predicate, iterable, initial)


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

from pipe import tail

@Pipe
def cycle(iterable):
    return _itertools.cycle(iterable)

@Pipe
def enumerations(iterable): # could be ienumerate() ?
    return enumerate(iterable)

@Pipe
def take(iterable, n):
    # The original implementation (pipe.take) eats one more item
    it = iter(iterable)
    for _ in range(n):
        try:
            yield next(it)
        except StopIteration:
            return

@Pipe
def drop(iterable, n):
    return _itertools.islice(iterable, n, None)

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

@Pipe
def chunks(iterable, n):
    # TODO: separate implementation for sequences that support slicing
    it = iter(iterable)
    chunk = it | take(n) | collect(list)
    while True:
        if len(chunk) < n:
            break
        yield chunk
        chunk = it | take(n) | collect(list)


# Transform and filter iterables
# Length of iterable may change (often by predicate), lazily evaluated

from pipe import select, where

def _complement(func):
    def f(*args, **kwargs):
        return not func(*args, **kwargs)
    return f

imap = select

@Pipe
def wherenot(iterable, predicate):
    return filter(_complement(predicate), iterable)

reject = wherenot # not related to select

@Pipe
def keep(iterable, f):
    return iterable | imap(f) | where(bool)

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

    assert range(7) | chunks(3) | collect(list) == [[0, 1, 2], [3, 4, 5]]
    
    obj = object()
    assert obj | repeat(5) | take(1) | collect(list) | first is obj
    assert [1, 3, 5, 7, 6, 9, 11, 13] | find(iseven) == 6

    assert [1, 3, 5, 6, 2] | reduce(lambda x, y: x + y) == 17

    assert range(8) | imap(lambda x: x * 2) | last == 14
