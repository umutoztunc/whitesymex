import z3

from whitesymex import parser, strategies
from whitesymex.path_group import PathGroup
from whitesymex.state import State


def test_hworld():
    instructions = parser.parse_file("tests/data/hworld.ws")
    state = State.create_entry_state(instructions)
    path_group = PathGroup(state)
    path_group.explore()
    stdout = b"".join(path_group.deadended[0].stdout)
    assert stdout == b"Hello, world of spaces!\r\n"


def test_count():
    instructions = parser.parse_file("tests/data/count.ws")
    state = State.create_entry_state(instructions)
    path_group = PathGroup(state)
    path_group.explore()
    stdout = b"".join(path_group.deadended[0].stdout)
    assert stdout == b"1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n"


def test_password_checker_bfs():
    instructions = parser.parse_file("tests/data/password_checker.ws")
    state = State.create_entry_state(instructions)
    path_group = PathGroup(state)
    path_group.explore(find=b"Correct!", avoid=b"Nope.", strategy=strategies.BFS)
    password = path_group.found[0].concretize()
    assert password.startswith(b"p4ssw0rd")


def test_password_checker_dfs():
    instructions = parser.parse_file("tests/data/password_checker.ws")
    state = State.create_entry_state(instructions)
    path_group = PathGroup(state)
    path_group.explore(find=b"Correct!", avoid=b"Nope.", strategy=strategies.DFS)
    password = path_group.found[0].concretize()
    assert password.startswith(b"p4ssw0rd")


def test_password_checker_random():
    instructions = parser.parse_file("tests/data/password_checker.ws")
    state = State.create_entry_state(instructions)
    path_group = PathGroup(state)
    path_group.explore(find=b"Correct!", avoid=b"Nope.", strategy=strategies.Random)
    password = path_group.found[0].concretize()
    assert password.startswith(b"p4ssw0rd")


def test_spaceship():
    instructions = parser.parse_file("tests/data/xctf-finals-2020-spaceship.ws")
    symflag = [z3.BitVec(f"flag_{i}", 24) for i in range(12)]
    stdin = list(b"xctf{") + symflag + list(b"}\n")
    state = State.create_entry_state(instructions, stdin=stdin)
    for c in symflag:
        state.solver.add(z3.And(0x20 <= c, c <= 0x7F))
    path_group = PathGroup(state)
    path_group.explore(avoid=b"Imposter!")
    flag = path_group.deadended[0].concretize(symflag)
    assert flag == b"Wh1t3sym3x!?"
