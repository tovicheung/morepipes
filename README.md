# morepipes
Based on the [pipe](https://github.com/JulienPalard/Pipe) library, adding more utilities and pipes to it

Some pipes are inspired by other programming languages (eg Rust)

## Installation
`pip install morepipes`

## Examples
Consume iterable
```py
range(9) | where(lambda x: x % 2) | collect
# List of odd numbers
```
Cut iterables
```py
range(9) | take(5) | drop(2) | collect
# [2, 3, 4]
```
Remove duplicates
```py
a = [1, 3, 3, 1, 2, 4, 4, 2, 2, 2, 1, 4, 4, 3, 3, 1]
b = a | squeeze | collect
# [1, 3, 1, 2, 4, 2, 1, 4, 3, 1], remove consecutive duplicates
c = b | unique | collect
# [1, 3, 2, 4]
```
Manipulate iterations
```py
range(9) | chunks(4)
# [[0, 1, 2, 3], [4, 5, 6, 7]]
range(9) | alternate
# [0, 2, 4, 6, 8]
```
Side effects
```py
range(9) | ... | inspect | ...
# Prints out each object received on evaluation
```
Or, more generally
```py
range(9) | ... | foreach(print) | ...
```
There's also bindings for builtins and itertools
```py
[1, 2, 3] | combinations(2)
[1, 2, 3] | permutations
[1, 2, 3] | cycle
[1, 2, 3] | imap(iseven)

[1, 2, 3] | isum # 6, equivalent to sum([1, 2, 3])
[1, 2, 3] | iall(iseven) # equivalent to all(iseven(x) for x in [1, 2, 3])
[1, 2, 3] | iany(iseven) # equivalent to any(iseven(x) for x in [1, 2, 3])
[1, 2, 3] | ilen # 3, equivalent to len([1, 2, 3])
```
`isum`, `iall`, `iany`, `ilen` is useful when working with long pipe chains (no messy parentheses)
## New: Partial Pipes
Creating a partial pipe
```py
reverse_sort = P | reverse | sort
# P is a special object placeholder
```
Using a partial pipe
```py
[1, 3, 4, 2] | reverse_sort
# Just like any other pipe
# Strictly equivalent to:
[1, 3, 4, 2] | reverse | sort
# as if P is replaced by [1, 3, 4, 2]
```
---

Have fun!

---

## Todos
- add full type annotation support
    - piping (dunder ror) can be typed easily
    - there is seemingly no way to type varargs currying (supported by the original `pipe` library)
    - use classes instead of functions for full type support??
- alternative implementation on `chunk` for sequences (supports slicing)