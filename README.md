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
Side effects
```py
range(9) | ... | inspect | ...
# Prints out each object received on evaluation
```
Or, more generally
```py
range(9) | ... | foreach(print) | ...
```
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
- alternative implementation on `chunk` for sequences (supports slicing)