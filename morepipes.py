from __future__ import annotations

import itertools as _itertools
import functools as _functools
from collections import deque as _deque
from collections.abc import Iterable, Sequence
from typing import Generic, TypeVar, TYPE_CHECKING, Callable, ParamSpec, Optional

if not TYPE_CHECKING:
    from pipe import Pipe

_P = ParamSpec("_P")
_R = TypeVar("_R")

# Helpers

_EMPTY = object()

def _consume(iterator):
     # consume iterator at C speed without storing elements
    _deque(iterator, maxlen=0)

def _complement(func):
    def f(*args, **kwargs):
        return not func(*args, **kwargs)
    return f

def _identity(x):
    return x


# Typed for linters and type checkers, not used during runtime

if TYPE_CHECKING:
    class Pipe(Generic[_P, _R]):
        def __init__(self, function: Callable[_P, _R]):
            self.function = function
            # _functools.update_wrapper(self, function)

        def __ror__(self, *args: _P.args, **kwargs: _P.kwargs) -> _R:
            # __ror__ always receive one argument
            # tell the type system to trust that all arguments are supplied
            return self.function(*args, **kwargs)

        def __call__(self, *args, **kwargs):
            # (near) Impossible to type
            return Pipe(
                lambda iterable, *args2, **kwargs2: self.function(
                    iterable, *args, *args2, **kwargs, **kwargs2
                )
            )


# Partial pipes

class _PartialPipe(Pipe):
    def __call__(self, arg):
        # Enables passing partial pipes to map functions
        return self.function(arg)

    def __or__(self, other) -> "_PartialPipe":
        if isinstance(other, Pipe):
            return type(self)(lambda obj, *args, **kwargs: other.function(self.function(obj, *args, **kwargs)))
        if callable(other):
            return type(self)(lambda obj, *args, **kwargs: other(self.function(obj, *args, **kwargs)))
        return NotImplemented

P = _PartialPipe(_identity) # the HEAD of partial pipes must be constructed with identity function


# Generate iterator
# These pipes take in objects of any type and generate an iterator for piping

@Pipe
def repeat(obj, n=_EMPTY):
    if n is _EMPTY:
        return _itertools.repeat(obj)
    return _itertools.repeat(obj, n)


# Iteration tails
# These pipes should be the tail of a chain of lazily-evaluated pipes in most cases
# They consume the iterator with the pipes

from pipe import sort, reverse

@Pipe
def collect(iterable, typ=list):
    # consumes iterator if typ is not specified
    if issubclass(typ, str):
        return typ().join(iterable)
    return typ(iterable)

consume = Pipe(_consume)

@Pipe
def ilen(iterable):
    counter = _itertools.count()
    _consume(zip(iterable, counter))
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
def inone(iterable, predicate):
    return all((not predicate(x)) for x in iterable)

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
# Items will pass right through unmodified

@Pipe
def foreach(iterable, func):
    for item in iterable:
        func(item)
        yield item

@Pipe
def inspect(iterable):
    return iterable | foreach(print)

@Pipe
def asserteach(iterable, predicate=_identity):
    for item in iterable:
        assert predicate(item)
        yield item

@Pipe
def asserteq(target, obj):
    assert target == obj
    return target


# Manipulate iterables
# Length of iterable may change, lazy evaluated

from pipe import tail, transpose, islice, izip, chain, chain_with, groupby, take_while, skip_while, traverse as _traverse, permutations

takewhile = take_while
dropwhile = skipwhile = skip_while

@Pipe
def combinations(iterable, r):
    return _itertools.combinations(iterable, r)

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
    it = iter(iterable)
    chunk = it | take(n) | collect
    while True:
        if len(chunk) < n:
            break
        yield chunk
        chunk = it | take(n) | collect

@Pipe
def alternate(iterable):
    return iterable | enumerations | where(lambda x: x[0] % 2 == 0) | imap(lambda x: x[1])

@Pipe
def unique(iterable):
    # not to be confused with pipe.uniq
    seen = set()
    for item in iterable:
        if item not in seen:
            seen.add(item)
            yield item

@Pipe
def squeeze(iterable):
    prev = object()
    for item in iterable:
        if item != prev:
            yield item
            prev = item

@Pipe
def traverse(objs, key=_identity):
    if isinstance(objs, (str, bytes)):
        yield objs
        return
    for obj in key(objs):
        try:
            yield from obj | traverse(key)
        except TypeError:
            yield obj


# Transform and filter iterables
# Length of iterable may change (often by predicate), lazily evaluated

from pipe import select, where

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

    assert range(9) | butlast | collect == list(range(8))
    assert range(9) | take(3) | ilen == 3
    assert [[1, 2, 3], (9, 8, 7), 4, 6] | flatten | collect == [[1, 2, 3], (9, 8, 7), 4, 6] | flattento(list) == [1, 2, 3, 9, 8, 7, 4, 6]
    assert range(4) | interpose(-1) | collect == [0, -1, 1, -1, 2, -1, 3]

    assert range(9) | where(iseven) | wherenot(ismul3) | collect == [2, 4, 8]
    assert range(9) | keep(lambda x: x % 3) | collect == [1, 2, 1, 2, 1, 2]

    s = P | where(iseven) | wherenot(ismul3)
    assert range(9) | s | collect == [2, 4, 8]

    assert range(7) | chunks(3) | collect == [[0, 1, 2], [3, 4, 5]]

    obj = object()
    assert obj | repeat(5) | take(1) | collect | first is obj
    assert [1, 3, 5, 7, 6, 9, 11, 13] | find(iseven) == 6

    assert range(8) | imap(lambda x: x * 2) | last == 14

    assert range(9) | alternate | collect == [0, 2, 4, 6, 8]

    "Hello woooorld!" | squeeze | collect(str) | asserteq("Helo world!") | unique | collect(str) | asserteq("Helo wrd!")

    assert range(9) | wherenot(iseven) | inone(iseven)
    assert range(9) | where(iseven) | inone(iseven) is False

    assert "ABC" | imap(
        P | Pipe(ord) | Pipe(str)
    ) | collect(str) == "656667"
    # OR
    tostrcode = P | Pipe(ord) | Pipe(str)
    assert "ABC" | imap(tostrcode) | collect(str) == "656667"
    # OR
    tostrcode = P | ord | str
    assert "ABC" | imap(tostrcode) | collect(str) == "656667"

    range(9) | where(iseven) | asserteach(iseven) | consume

    assert range(8) | reduce(lambda x, y: x + y) == range(8) | isum == 28

    [[1, 2, 3], [4, 5, 6]] | traverse(P | reverse) | collect | asserteq([6, 5, 4, 3, 2, 1])

    # traverse subclasses
    object | traverse(type.__subclasses__) | consume

    a = [1, 2, 3, 4] | first
