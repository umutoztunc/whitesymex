from enum import Enum


class Parameter(Enum):
    """Parameter types for the commands.

    Attributes:
        pattern: A string regex pattern to match the parameter.
    """

    NUMBER = r"([\t ]+)\n"
    LABEL = r"([\t ]+)\n"

    def __init__(self, pattern: str):
        self.pattern = pattern
