from whitesymex.strategies import Strategy


class BFS(Strategy):
    def select_states(self):
        states = self.path_group.active[:]
        self.path_group.active.clear()
        return states
