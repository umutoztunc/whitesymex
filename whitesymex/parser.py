from __future__ import annotations

import re

from whitesymex.errors import (
    ParameterDecodeError,
    UnknownIMPError,
    UnknownOpError,
    UnknownParameterError,
)
from whitesymex.imp import IMP
from whitesymex.instruction import Instruction
from whitesymex.parameter import Parameter


def _get_imp(code, offset):
    patterns = [imp.pattern for imp in IMP]
    pattern = "|".join(patterns)
    match = re.match(pattern, code[offset:])
    if match is None:
        raise UnknownIMPError()
    imp = match.group(0)
    size = len(imp)
    return (IMP(imp), size)


def _get_op(op_type, code, offset):
    patterns = [op.pattern for op in op_type]
    pattern = "|".join(patterns)
    match = re.match(pattern, code[offset:])
    if match is None:
        raise UnknownOpError()
    op = match.group(0)
    size = len(op)
    return (op_type(op), size)


def _get_parameter_value(parameter, code, offset):
    assert isinstance(parameter, Parameter)
    match = re.match(parameter.pattern, code[offset:])
    if match is None:
        raise UnknownParameterError()
    value = match.group(1)
    size = len(match.group(0))
    bits = []
    for v in value:
        if v == " ":
            bits.append("0")
        elif v == "\t":
            bits.append("1")
        else:
            raise ParameterDecodeError(f"unknown value: {v}")

    bitstring = "".join(bits)
    if parameter is Parameter.NUMBER:
        if len(bitstring) == 1:
            # There is no value after the sign bit.
            return (0, size)

        number = int(bitstring[1:], 2)
        if bitstring[0] == "1":
            # If there is a sign bit and it is set, the number is negative.
            number *= -1

        return (number, size)

    if parameter is Parameter.LABEL:
        label = int(bitstring, 2)
        return (label, size)

    raise ParameterDecodeError()


def parse_code(code: str) -> list[Instruction]:
    """Parses the given code string to list of instructions."""
    # Remove non-whitespace characters.
    code = "".join([c for c in code if c in " \t\n"])

    instructions = []
    i = 0
    while i < len(code):
        imp, size = _get_imp(code, i)
        i += size

        op, size = _get_op(imp.op_type, code, i)
        i += size

        parameter = None
        if op.parameter is not None:
            parameter, size = _get_parameter_value(op.parameter, code, i)
            i += size

        ins = Instruction(imp, op, parameter)
        instructions.append(ins)

    return instructions


def parse_file(filename: str) -> list[Instruction]:
    """Reads and parses the given file to list of instructions."""
    with open(filename, "r") as f:
        code = f.read()
    return parse_code(code)
