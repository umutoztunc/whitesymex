from __future__ import annotations

from typing import Union

import z3

from whitesymex.errors import SolverError


class Solver:
    """SMT solver to solve path constraints.

    Attributes:
        constraints: A list of path constraints.
        store: A dict mapping symbolic variables to concrete values.
    """

    def __init__(self):
        self.constraints = []
        self.store = {}

    def clone(self):
        """Returns a copy of the solver.

        Both constraints and store are shallow-copied.
        """
        solver = Solver()
        solver.constraints = self.constraints.copy()
        solver.store = self.store.copy()
        return solver

    def add(self, constraints: Union[z3.BoolRef, list[z3.BoolRef]]):
        """Adds constraints to the solver.

        Args:
            constraints: A single constraint or a list of constraints to add.
        """
        if isinstance(constraints, list):
            self.constraints.extend(constraints)
        else:
            self.constraints.append(constraints)

    def is_satisfiable(self) -> bool:
        """Checks and returns if the constraints are satisfiable."""
        solver = z3.Solver()
        solver.add(self.constraints)
        if solver.check() == z3.sat:
            model = solver.model()
            for decl in model:
                self.store[decl()] = model[decl]
            return True
        return False

    def simplify(self, expression: z3.ExprRef) -> z3.ExprRef:
        """Simplifies an expression by substituting concrete values.

        Only the variables that exist in store are substituted.

        Args:
            expression: An expression to be simplified.

        Returns:
            The substituted and simplified expression.
        """
        expr = z3.substitute(expression, *self.store.items())
        return z3.simplify(expr)

    def eval(self, expression: z3.ExprRef) -> Union[bool, int]:
        """Evaluates an expression using the concrete values from the store.

        Args:
            expression: An expression to be evaluated.

        Returns:
            The evaluated value of the expression.

        Raises:
            SolverError: Failed to evaluate the expression as int or bool.
        """
        if not z3.is_expr(expression):
            return expression

        result = self.simplify(expression)
        if isinstance(result, z3.BoolRef):
            return bool(result)
        if isinstance(result, (z3.IntNumRef, z3.BitVecNumRef)):
            return result.as_long()
        raise SolverError(f"Failed to evaluate: {expression}")
