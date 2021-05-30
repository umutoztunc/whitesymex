import re
from enum import Enum

from whitesymex import ops


class IMP(Enum):
    """Instruction Modification Parameters (IMP) for Whitespace.

    Attributes:
        op_type: Respective ops.Op subclass for the IMP value.
        pattern: A string pattern to match the IMP.
    """

    IO = (ops.IOOp, "\t\n")
    STACK_MANIPULATION = (ops.StackManipulationOp, " ")
    ARITHMETIC = (ops.ArithmeticOp, "\t ")
    FLOW_CONTROL = (ops.FlowControlOp, "\n")
    HEAP_ACCESS = (ops.HeapAccessOp, "\t\t")

    def __new__(cls, op_type: ops.Op, pattern: str):
        obj = object.__new__(cls)
        obj.op_type = op_type
        obj.pattern = re.escape(pattern)
        obj._value_ = pattern
        return obj
