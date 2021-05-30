from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Optional, Union

from whitesymex import strategies
from whitesymex.errors import StrategyError, WhitesymexError

if TYPE_CHECKING:
    from whitesymex.state import State


def condition_to_lambda(
    condition: Optional[Union[bytes, Callable[[State], bool]]], default: bool = False
) -> Callable[[State], bool]:
    """Converts condition to lambda function that returns True or False.

    Args:
        condition: A condition can be a function or bytes that are expected to
            be found in a state's stdout.
        default: A bool value to be returned by lambda function if the
            condition is None.

    Returns:
        A lambda function that accepts a state as parameter that returns True
        if the condition is satisfied.
    """
    if condition is None:
        return lambda state: default

    if hasattr(condition, "__call__"):
        return condition  # type: ignore

    if isinstance(condition, bytes):

        def condition_function(state):
            stdout = b"".join(state.stdout)
            return condition in stdout

        return condition_function

    raise WhitesymexError("Unable to convert condition to function.")


class PathGroup:
    """Organizes states into stashes for symbolic execution.

    Attributes:
        active: A list of states that are still active.
        deadended: A list of states that are exited gracefully.
        avoided: A list of avoided states.
        found: A list of found states.
        errored: A list of states that encounter an error during execution.
    """

    def __init__(self, state: State):
        self.active: list[State] = [state]
        self.deadended: list[State] = []
        self.avoided: list[State] = []
        self.found: list[State] = []
        self.errored: list[State] = []

    def __repr__(self):
        stash_info = []
        if self.active:
            stash_info.append(f"{len(self.active)} active")
        if self.deadended:
            stash_info.append(f"{len(self.deadended)} deadended")
        if self.avoided:
            stash_info.append(f"{len(self.avoided)} avoided")
        if self.found:
            stash_info.append(f"{len(self.found)} found")
        if self.errored:
            stash_info.append(f"{len(self.errored)} errored")
        stash_repr = ", ".join(stash_info)
        return f"<PathGroup with {stash_repr}>"

    def explore(
        self,
        find: Optional[Union[bytes, Callable[[State], bool]]] = None,
        avoid: Optional[Union[bytes, Callable[[State], bool]]] = None,
        strategy: type[strategies.Strategy] = strategies.BFS,
        loop_limit: Optional[int] = None,
        num_find: int = 1,
    ):
        """Explores the active states and updates stashes accordingly.

        It returns when there is no active states left or num_find states are
        found.

        Args:
            find: Either bytes that are expected to be found in a state's
                stdout or a function that accepts a state and returns True if
                the state shall be classified as found.
            avoid: Either bytes that are expected to be avoided in a state's
                stdout or a function that accepts a state and returns True if
                the state shall be classified as avoided.
            strategy: A strategies.Strategy subclass that will be used to
                select states at each iteration.
            loop_limit: A maximum limit for loops with a symbolic expression as
                its condition.
            num_find: Number of states to be found.

        Raises:
            StrategyError: The given strategy is not a subclass of
                strategies.Strategy class.
        """
        if not issubclass(strategy, strategies.Strategy):
            raise StrategyError(f"Invalid strategy: {strategy}")

        find = condition_to_lambda(find)
        avoid = condition_to_lambda(avoid)
        strategy(self, find, avoid, loop_limit, num_find).run()
