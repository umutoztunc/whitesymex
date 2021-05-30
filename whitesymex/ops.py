import re
from enum import Enum

from whitesymex.parameter import Parameter


class Op(Enum):
    """Op values for Whitespace commands.

    Attributes:
        parameter: A Parameter value that represents the parameter type for the
            op. If the op does not take any parameters, this value is None.
        pattern: A string pattern to match the op.
    """

    def __new__(cls, parameter: Parameter, pattern: str):
        obj = object.__new__(cls)
        obj.parameter = parameter
        obj.pattern = re.escape(pattern)
        obj._value_ = pattern
        return obj


class IOOp(Op):
    READ_CHAR = (None, "\t ")
    READ_NUMBER = (None, "\t\t")
    PRINT_CHAR = (None, "  ")
    PRINT_NUMBER = (None, " \t")


class StackManipulationOp(Op):
    PUSH = (Parameter.NUMBER, " ")
    DUP_TOP = (None, "\n ")
    SWAP_TOP2 = (None, "\n\t")
    DISCARD_TOP = (None, "\n\n")
    COPY_TO_TOP = (Parameter.NUMBER, "\t ")
    SLIDE_N_OFF = (Parameter.NUMBER, "\t\n")


class ArithmeticOp(Op):
    ADD = (None, "  ")
    SUB = (None, " \t")
    MUL = (None, " \n")
    DIV = (None, "\t ")
    MOD = (None, "\t\t")


class FlowControlOp(Op):
    MARK = (Parameter.LABEL, "  ")
    CALL = (Parameter.LABEL, " \t")
    JUMP = (Parameter.LABEL, " \n")
    JUMP_IF_ZERO = (Parameter.LABEL, "\t ")
    JUMP_IF_NEGATIVE = (Parameter.LABEL, "\t\t")
    RETURN = (None, "\t\n")
    EXIT = (None, "\n\n")


class HeapAccessOp(Op):
    STORE = (None, " ")
    RETRIEVE = (None, "\t")
