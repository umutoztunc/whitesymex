from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from whitesymex.imp import IMP
    from whitesymex.ops import Op


@dataclass
class Instruction:
    imp: IMP
    op: Op
    parameter: Optional[int]

    def __repr__(self):
        return f"Instruction({self.imp}, {self.op}, {self.parameter})"
