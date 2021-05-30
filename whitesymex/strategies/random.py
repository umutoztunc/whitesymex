import random

from whitesymex.strategies import Strategy


class Random(Strategy):
    def select_states(self):
        index = random.randrange(len(self.path_group.active))
        state = self.path_group.active.pop(index)
        return [state]
