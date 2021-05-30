class WhitesymexError(Exception):
    pass


class SymbolicExecutionError(WhitesymexError):
    pass


class EmptyStackError(SymbolicExecutionError):
    pass


class EmptyCallstackError(SymbolicExecutionError):
    pass


class DivideByZeroError(SymbolicExecutionError, ZeroDivisionError):
    pass


class SolverError(WhitesymexError):
    pass


class StrategyError(WhitesymexError):
    pass


class StrategyNotImplementedError(StrategyError, NotImplementedError):
    pass


class ParserError(WhitesymexError):
    pass


class UnknownIMPError(ParserError):
    pass


class UnknownOpError(ParserError):
    pass


class UnknownParameterError(ParserError):
    pass


class ParameterDecodeError(ParserError):
    pass
