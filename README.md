# Whitesymex
[![Build Status](https://github.com/umutoztunc/whitesymex/workflows/build/badge.svg)](https://github.com/umutoztunc/whitesymex/actions)
[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![PyPI](https://img.shields.io/pypi/v/whitesymex)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)


Whitesymex is a symbolic execution engine for [Whitespace](https://en.wikipedia.org/wiki/Whitespace_(programming_language)). It uses dynamic symbolic analysis to find execution paths of a Whitespace program. It is inspired by [angr](//angr.io).

## Installation
It is available on pypi. It requires python 3.7.0+ to run.

```sh
$ pip install whitesymex
```

## Usage
### Command-line Interface
```sh
$ whitesymex -h
# usage: whitesymex [-h] [--version] [--find FIND] [--avoid AVOID] [--strategy {bfs,dfs,random}]
#                   [--loop-limit LIMIT]
#                   file
#
# Symbolic execution engine for Whitespace.
#
# positional arguments:
#   file                  program to execute
#
# optional arguments:
#   -h, --help            show this help message and exit
#   --version             show program's version number and exit
#   --find FIND           string to find
#   --avoid AVOID         string to avoid
#   --strategy {bfs,dfs,random}
#                         path exploration strategy (default: bfs)
#   --loop-limit LIMIT    maximum number of iterations for symbolic loops
```

Simple example:
```sh
$ whitesymex password_checker.ws --find 'Correct!' --avoid 'Nope.'
# p4ssw0rd
```

### Python API
Simple example:
```python
from whitesymex import parser
from whitesymex.state import State
from whitesymex.path_group import PathGroup

instructions = parser.parse_file("password_checker.ws")
state = State.create_entry_state(instructions)
path_group = PathGroup(state)
path_group.explore(find=b"Correct!", avoid=b"Nope.")
password = path_group.found[0].concretize()
print(password.encode())
# p4ssw0rd
```

More complex example from XCTF Finals 2020:
```python
import z3

from whitesymex import parser, strategies
from whitesymex.path_group import PathGroup
from whitesymex.state import State

instructions = parser.parse_file("xctf-finals-2020-spaceship.ws")
flag_length = 18
flag = [z3.BitVec(f"flag_{i}", 24) for i in range(flag_length)] + list(b"\n")
state = State.create_entry_state(instructions, stdin=flag)

# The flag is printable.
for i in range(flag_length):
    state.solver.add(z3.And(0x20 <= flag[i], flag[i] <= 0x7f))

path_group = PathGroup(state)
path_group.explore(avoid=b"Imposter!", strategy=strategies.DFS)
flag = path_group.deadended[0].concretize()
print(flag.decode())
# xctf{Wh1t3sym3x!?}
```

You can also concretize your symbolic variables instead of stdin:
```python
import z3

from whitesymex import parser
from whitesymex.path_group import PathGroup
from whitesymex.state import State

instructions = parser.parse_file("tests/data/xctf-finals-2020-spaceship.ws")
symflag = [z3.BitVec(f"flag_{i}", 24) for i in range(12)]
stdin = list(b"xctf{") + symflag + list(b"}\n")
state = State.create_entry_state(instructions, stdin=stdin)
for c in symflag:
    state.solver.add(z3.And(0x20 <= c, c <= 0x7f))
path_group = PathGroup(state)
path_group.explore(find=b"crewmember", avoid=b"Imposter!")
flag = path_group.found[0].concretize(symflag)
print("xctf{%s}" % flag)
# xctf{Wh1t3sym3x!?}
```
