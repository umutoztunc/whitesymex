from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Callable, Optional

import z3

from whitesymex.errors import StrategyNotImplementedError, SymbolicExecutionError
from whitesymex.ops import FlowControlOp, IOOp

if TYPE_CHECKING:
    from whitesymex.path_group import PathGroup
    from whitesymex.state import State


def is_symbolic_conditional(state: State) -> bool:
    """Checks whether a state is on a symbolic conditional instruction.

    A symbolic conditional is a conditional instruction that contains symbolic
    expressions in its condition.

    Args:
        state: A state to be checked.

    Returns:
        True if the current instruction is a symbolic conditional. Otherwise,
        returns False.
    """
    if state.instruction is None:
        return False
    if state.instruction.op not in [
        FlowControlOp.JUMP_IF_ZERO,
        FlowControlOp.JUMP_IF_NEGATIVE,
    ]:
        return False
    return z3.is_expr(state._stack_peek())


class Strategy:
    """Strategy to select and step states during symbolic execution.

    This class is supposed to be subclassed for each strategy.

    Attributes:
        path_group: A PathGroup instance to run the strategy.
        find: A filter function to decide if a state should be marked as found.
        avoid: A filter function to decide if a state should be avoided.
        loop_limit: A maximum number of iterations for loops with a symbolic
            expression as a condition.
        loop_counts: A dict mapping ip values of conditionals to hit counts.
        num_find: Number of states to be found.
    """

    def __init__(
        self,
        path_group: PathGroup,
        find: Callable[[State], bool],
        avoid: Callable[[State], bool],
        loop_limit: Optional[int],
        num_find: int = 1,
    ):
        self.path_group = path_group
        self.find = find
        self.avoid = avoid
        self.loop_limit = loop_limit
        self.loop_counts: defaultdict[int, int] = defaultdict(int)
        self.num_find = num_find

    def select_states(self) -> list[State]:
        """Selects states to be executed in the next iteration.

        This function is supposed to be implemented in subclasses.

        Returns:
            A list of states to be executed.
        """
        raise StrategyNotImplementedError()

    def step(self, state: State) -> Optional[list[State]]:
        """Steps the given state.

        The state is stepped until one of the followings happen:
            - The state exits.
            - The state throws an error.
            - The state gets marked as found.
            - The state gets marked as avoided.
            - The state returns multiple successor states.
            - The state hits the loop limit.

        Args:
            state: A state to be stepped.

        Returns:
            A list of successor states is returned. If the state is classified
            such as errored, found, avoided, or hits the loop limit, None is
            returned.
        """
        while state.instruction:
            if self.loop_limit is not None and is_symbolic_conditional(state):
                if self.loop_counts[state.ip] >= self.loop_limit:
                    return None
                self.loop_counts[state.ip] += 1

            op = state.instruction.op
            try:
                successors = state.step()
            except SymbolicExecutionError:
                self.path_group.errored.append(state)
                return None

            # If the instruction stepped is a print instruciton, try to filter
            # the state as found/avoided.
            if op in [IOOp.PRINT_CHAR, IOOp.PRINT_NUMBER]:
                if self.find(state):
                    self.path_group.found.append(state)
                    return None
                if self.avoid(state):
                    self.path_group.avoided.append(state)
                    return None

            # As long as there is only one successor state, keep stepping.
            if len(successors) == 1:
                continue
            return successors
        return []

    def run(self):
        """Runs the symbolic execution with the strategy.

        Returns if num_find states are found. Otherwise, runs until no active
        states left.
        """
        while self.path_group.active:
            states = self.select_states()
            for state in states:
                successors = self.step(state)
                if len(self.path_group.found) >= self.num_find:
                    return

                if successors is None:
                    continue

                if successors:
                    self.path_group.active.extend(successors)
                else:
                    self.path_group.deadended.append(state)
