#!/usr/bin/env python3
import argparse
from typing import Type

import whitesymex
from whitesymex import parser, strategies
from whitesymex.path_group import PathGroup
from whitesymex.state import State


def str_to_strategy(s: str) -> Type[strategies.Strategy]:
    return {
        "bfs": strategies.BFS,
        "dfs": strategies.DFS,
        "random": strategies.Random,
    }[s]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="whitesymex", description="Symbolic execution engine for Whitespace."
    )
    parser.add_argument("file", help="program to execute")
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {whitesymex.__version__}"
    )
    parser.add_argument("--find", type=str.encode, help="string to find")
    parser.add_argument("--avoid", type=str.encode, help="string to avoid")
    parser.add_argument(
        "--strategy",
        default="bfs",
        choices=["bfs", "dfs", "random"],
        type=str.lower,
        help="path exploration strategy (default: bfs)",
    )
    parser.add_argument(
        "--loop-limit",
        metavar="LIMIT",
        type=int,
        help="maximum number of iterations for symbolic loops",
    )
    args = parser.parse_args()
    args.strategy = str_to_strategy(args.strategy)
    return args


def main():
    args = parse_args()
    instructions = parser.parse_file(args.file)
    state = State.create_entry_state(instructions)
    path_group = PathGroup(state)
    path_group.explore(
        find=args.find,
        avoid=args.avoid,
        strategy=args.strategy,
        loop_limit=args.loop_limit,
    )
    if args.find and len(path_group.found) > 0:
        print(path_group.found[0].concretize().decode())
    elif len(path_group.deadended) > 0:
        print(path_group.deadended[0].concretize().decode())
    else:
        print("No solution found.")


if __name__ == "__main__":
    main()
