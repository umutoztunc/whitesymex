from __future__ import annotations

from collections import defaultdict, deque
from copy import copy
from enum import Enum
from typing import TYPE_CHECKING, Optional, Union

import z3

from whitesymex.errors import (
    DivideByZeroError,
    EmptyCallstackError,
    EmptyStackError,
    SymbolicExecutionError,
)
from whitesymex.ops import (
    ArithmeticOp,
    FlowControlOp,
    HeapAccessOp,
    IOOp,
    StackManipulationOp,
)
from whitesymex.solver import Solver

Value = Union[int, z3.ExprRef]
if TYPE_CHECKING:
    from whitesymex.instruction import Instruction


class VarType(Enum):
    CHAR = 1
    NUMBER = 2


def _get_labels(instructions):
    labels = {}
    for ip, ins in enumerate(instructions):
        if ins.op is FlowControlOp.MARK:
            labels[ins.parameter] = ip
    return labels


class State:
    """Represents the execution state.

    Attributes:
        ip: An integer representing instruction pointer/program counter.
        stack: A deque for the execution stack.
        callstack: A deque that stores return addresses as stack.
        heap: A dictionary to store/retrieve values by indexes.
        labels: A dictionary that maps labels to ip values.
        instructions: A list that contains program instructions.
        input: A deque to represent stdin. As long as this deque is not empty,
            inputs will be read from it. However, if it is empty, symbolic
            variables will be read automaticaly.
        stdin: A list that contains inputs read so far.
        stdout: A list that represents stdout.
        var_to_type: A dictionary that maps variables to VarType values.
        solver: A whitesymex.solver.Solver instance to store and solve path
            constraints.
        operations: A dictionary that maps whitesymex.ops.Op values to
            respective methods.
    """

    def __init__(
        self,
        instructions: list[Instruction],
        labels: dict[int, int],
        stdin: Optional[deque[Value]],
        bitlength: int,
    ):
        """The constructor should not be called directly.

        In order to create a state, State.create_entry_state should be used.

        Args:
            instructions: A list of instructions.
            labels: A dictionary that maps labels to ip values.
            stdin: A deque of ints or symbolic variables.
            bitlength: Length of symbolic bitvectors. If this value is None,
                unbounded symbolic integers are used instead of bitvectors.
        """
        self.ip = 0
        self.stack: deque[Value] = deque()
        self.callstack: deque[int] = deque()
        self.heap: defaultdict[Value, Value] = defaultdict(int)
        self.labels = labels
        self.instructions = instructions
        self.input = stdin
        self.bitlength = bitlength
        self.stdin: list[Value] = []
        self.stdout: list[bytes] = []
        self.var_to_type: dict[Value, VarType] = {}
        self.solver = Solver()
        self.operations = {
            # IO
            IOOp.READ_CHAR: self._read_char,
            IOOp.READ_NUMBER: self._read_number,
            IOOp.PRINT_CHAR: self._print_char,
            IOOp.PRINT_NUMBER: self._print_number,
            # StackManipulation
            StackManipulationOp.PUSH: self._push,
            StackManipulationOp.DUP_TOP: self._dup_top,
            StackManipulationOp.SWAP_TOP2: self._swap_top2,
            StackManipulationOp.DISCARD_TOP: self._discard_top,
            StackManipulationOp.COPY_TO_TOP: self._copy_to_top,
            StackManipulationOp.SLIDE_N_OFF: self._slide_n_off,
            # Arithmetic
            ArithmeticOp.ADD: self._add,
            ArithmeticOp.SUB: self._sub,
            ArithmeticOp.MUL: self._mul,
            ArithmeticOp.DIV: self._div,
            ArithmeticOp.MOD: self._mod,
            # FlowControl
            FlowControlOp.MARK: self._do_nothing,
            FlowControlOp.CALL: self._call,
            FlowControlOp.JUMP: self._jump,
            FlowControlOp.JUMP_IF_ZERO: self._jump_if_zero,
            FlowControlOp.JUMP_IF_NEGATIVE: self._jump_if_negative,
            FlowControlOp.RETURN: self._return,
            FlowControlOp.EXIT: self._exit,
            # HeapAccess
            HeapAccessOp.STORE: self._store,
            HeapAccessOp.RETRIEVE: self._retrieve,
        }

    @property
    def instruction(self) -> Optional[Instruction]:
        """Current instruction pointed by ip.

        If the ip points to a location that is out of program's space, None
        is returned."""
        try:
            return self.instructions[self.ip]
        except KeyError:
            return None

    def clone(self) -> State:
        """Returns a copy of the state.

        Properties are shallow copied except for instructions and labels which
        are not copied but shared between the clones.
        """
        # Instructions and labels are shared.
        state = State(self.instructions, self.labels, copy(self.input), self.bitlength)
        state.ip = self.ip
        state.stack = self.stack.copy()
        state.callstack = self.callstack.copy()
        state.heap = self.heap.copy()
        state.solver = self.solver.clone()
        state.stdin = self.stdin.copy()
        state.stdout = self.stdout.copy()
        state.var_to_type = self.var_to_type.copy()
        return state

    def is_satisfiable(self) -> bool:
        """Returns whether the path constraints are satisfiable or not."""
        return self.solver.is_satisfiable()

    def concretize(self, buffer: list[Union[int, z3.ExprRef]] = None) -> bytes:
        """Converts given symbolic buffer to concrete bytes.

        If the buffer is None, it concretizes stdin instead.

        Args:
            buffer: A list that contains either bytes or symbolic variables.

        Returns:
            Concretized buffer as bytes object.
        """
        if buffer is None:
            buffer = self.stdin

        solution = []
        for var in buffer:
            value = self.solver.eval(var)
            if self.var_to_type[var] == VarType.CHAR:
                concrete_value = bytes([value])
            elif self.var_to_type[var] == VarType.NUMBER:
                concrete_value = str(value).encode()
            else:
                raise SymbolicExecutionError("Unknown variable type.")
            solution.append(concrete_value)
        return b"".join(solution)

    def step(self) -> list[State]:
        """Single-steps the current state.

        If the instruction is conditional and the condition is a symbolic
        expression, the state clones itself and single-steps both paths.

        Returns:
            A list that contains the successor states."""
        if self.instruction is None:
            return []
        op = self.instruction.op
        successors = self.operations[op]()
        return successors

    def _read_symbolic_input(self):
        if self.input:
            symvar = self.input.popleft()
        else:
            if self.bitlength:
                symvar = z3.BitVec(f"input_{len(self.stdin)}", self.bitlength)
            else:
                symvar = z3.Int(f"input_{len(self.stdin)}")
            self.solver.add(z3.And(0 <= symvar, symvar <= 0xFF))
        self.stdin.append(symvar)
        if self.solver.is_satisfiable():
            return symvar
        return None

    def _read_char(self):
        index = self._stack_pop()
        char = self._read_symbolic_input()
        if char is None:
            return []
        self.var_to_type[char] = VarType.CHAR
        self.heap[index] = char
        self.ip += 1
        return [self]

    def _read_number(self):
        index = self._stack_pop()
        number = self._read_symbolic_input()
        if number is None:
            return []
        self.var_to_type[number] = VarType.NUMBER
        self.heap[index] = number
        self.ip += 1
        return [self]

    def _print_char(self):
        top = self._stack_pop()
        value = self.solver.eval(top)
        try:
            char = bytes([value])
        except (ValueError, OverflowError) as e:
            raise SymbolicExecutionError(f"Unable to convert {value} to char.") from e
        self.stdout.append(char)
        self.ip += 1
        return [self]

    def _print_number(self):
        top = self._stack_pop()
        number = self.solver.eval(top)
        self.stdout.append(str(number).encode())
        self.ip += 1
        return [self]

    def _push(self):
        value = self.instruction.parameter
        self.stack.append(value)
        self.ip += 1
        return [self]

    def _dup_top(self):
        top = self._stack_peek()
        self.stack.append(top)
        self.ip += 1
        return [self]

    def _swap_top2(self):
        top1 = self._stack_pop()
        top2 = self._stack_pop()
        self.stack.append(top1)
        self.stack.append(top2)
        self.ip += 1
        return [self]

    def _discard_top(self):
        self._stack_pop()
        self.ip += 1
        return [self]

    def _copy_to_top(self):
        n = self.instruction.parameter
        try:
            value = self.stack[-1 - n]
        except IndexError as e:
            raise EmptyStackError() from e
        self.stack.append(value)
        self.ip += 1
        return [self]

    def _slide_n_off(self):
        n = self.instruction.parameter
        top = self._stack_pop()
        for _ in range(n):
            self._stack_pop()
        self.stack.append(top)
        self.ip += 1
        return [self]

    def _add(self):
        rhs = self._stack_pop()
        lhs = self._stack_pop()
        self.stack.append(lhs + rhs)
        self.ip += 1
        return [self]

    def _sub(self):
        rhs = self._stack_pop()
        lhs = self._stack_pop()
        self.stack.append(lhs - rhs)
        self.ip += 1
        return [self]

    def _mul(self):
        rhs = self._stack_pop()
        lhs = self._stack_pop()
        self.stack.append(lhs * rhs)
        self.ip += 1
        return [self]

    def _div(self):
        rhs = self._stack_pop()
        lhs = self._stack_pop()
        if self.solver.eval(rhs) == 0:
            raise DivideByZeroError()
        self.stack.append(lhs // rhs)
        self.ip += 1
        return [self]

    def _mod(self):
        rhs = self._stack_pop()
        lhs = self._stack_pop()
        if self.solver.eval(rhs) == 0:
            raise DivideByZeroError()
        self.stack.append(lhs % rhs)
        self.ip += 1
        return [self]

    def _do_nothing(self):
        self.ip += 1
        return [self]

    def _call(self):
        label = self.instruction.parameter
        return_ip = self.ip + 1
        self.callstack.append(return_ip)
        function_ip = self.labels[label]
        self.ip = function_ip
        return [self]

    def _jump(self):
        label = self.instruction.parameter
        target_ip = self.labels[label]
        self.ip = target_ip
        return [self]

    def _conditional_jump(self, condition):
        label = self.instruction.parameter
        target_ip = self.labels[label]

        if isinstance(condition, bool):
            # The condition does not contain symbolic variables. Thus, it is
            # already known if it is True or False. There is no need for
            # branching out.
            if condition:
                self.ip = target_ip
            else:
                self.ip += 1
            return [self]

        assert z3.is_expr(condition)
        taken = self
        not_taken = self.clone()
        if taken.solver.eval(condition):
            taken.solver.add(condition)
            taken.ip = target_ip
            not_taken.solver.add(z3.Not(condition))
            not_taken.ip += 1
        else:
            taken.solver.add(z3.Not(condition))
            taken.ip += 1
            not_taken.solver.add(condition)
            not_taken.ip = target_ip

        successors = [taken]
        if not_taken.is_satisfiable():
            successors.append(not_taken)
        return successors

    def _jump_if_zero(self):
        top = self._stack_pop()
        condition = top == 0
        return self._conditional_jump(condition)

    def _jump_if_negative(self):
        top = self._stack_pop()
        condition = top < 0
        return self._conditional_jump(condition)

    def _return(self):
        try:
            return_ip = self.callstack.pop()
        except IndexError as e:
            raise EmptyCallstackError() from e
        self.ip = return_ip
        return [self]

    def _exit(self):
        self.ip += 1
        return []

    def _store(self):
        value = self._stack_pop()
        index = self._stack_pop()
        self.heap[index] = value
        self.ip += 1
        return [self]

    def _retrieve(self):
        index = self._stack_pop()
        value = self.heap[index]
        self.stack.append(value)
        self.ip += 1
        return [self]

    def _stack_pop(self):
        try:
            value = self.stack.pop()
        except IndexError as e:
            raise EmptyStackError() from e
        return value

    def _stack_peek(self):
        try:
            top = self.stack[-1]
        except IndexError as e:
            raise EmptyStackError() from e
        return top

    @classmethod
    def create_entry_state(
        cls,
        instructions: list[Instruction],
        stdin: list[Value] = None,
        bitlength: int = 24,
    ) -> State:
        """Returns an entry state for the Whitespace program.

        Args:
            instructions: A list of instructions.
            stdin: A list of ints or symbolic variables.
            bitlength: Length of symbolic bitvectors. If this value is None,
                unbounded symbolic integers are used instead of bitvectors.
        """
        labels = _get_labels(instructions)
        stdinq = None
        if stdin:
            stdinq = deque(stdin)
        state = cls(instructions, labels, stdinq, bitlength)
        return state
