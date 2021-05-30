from whitesymex.strategies import Strategy


class DFS(Strategy):
    def select_states(self):
        state = self.path_group.active.pop()
        return [state]
