import random
from .game import Move, PLAYER_1, PLAYER_2, AMBOS, AMBO_BEANS


class GameState(object):
    def __init__(self, board, turn, parent=None, move=None, depth=0):
        self.parent = parent
        self.move = move
        self.board = board
        self.turn = turn
        self.depth = depth

    def get_child(self, ambo=None):
        """Get child for a move (ambo index for current player)"""
        board = self.board.clone()
        move = Move(ambo=ambo, player=self.turn)
        next_turn = board.make_move(move)
        return GameState(parent=self, move=move, board=board, turn=next_turn,
                         depth=self.depth + 1)

    def get_children(self, ambo=None):
        """Get all possible child states that result from moves by current
        player"""
        children = []
        for ambo in range(AMBOS):
            move = Move(ambo=ambo, player=self.turn)
            if self.board.is_valid_move(move):
                children.append(self.get_child(ambo))
        return children

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "GameState\nNext move: Player {0}\nPrev move: {1}\n{2}".format(
            self.turn + 1, self.move, self.board)


class RandomBot(object):
    def __init__(self, player_index):
        self.index = player_index

    def _pre_move(self, move):
        print("RandomBot {0}: Making move {1}".format(self.index + 1, move))

    def get_move(self, board):
        possible_ambos = range(AMBOS)
        random.shuffle(possible_ambos)
        for ambo in possible_ambos:
            move = Move(ambo=ambo, player=self.index)
            if board.is_valid_move(move):
                self._pre_move(move)
                return move


class GreedyBot(object):
    def __init__(self, player_index):
        self.index = player_index
        self.opponent = PLAYER_2 if player_index == PLAYER_1 else PLAYER_1

    def _pre_move(self, state):
        score = self.evaluate(state)
        print("GreedyBot {0}, Move: {1}, Score: {2}".format(
            self.index + 1, state.move, score))

    def evaluate(self, state):
        kalahas = state.board.kalahas
        score = kalahas[self.index] - kalahas[self.opponent]
        if not state.board.is_end_position() and state.turn == self.index:
            score += 1 + int(score * 0.2)
        return score

    def get_move(self, board):
        state = GameState(board=board, turn=self.index)
        children = state.get_children()
        children.sort(key=self.evaluate, reverse=True)
        if children:
            self._pre_move(children[0])
            return children[0].move


class SearchBot(object):
    def __init__(self, player_index):
        self.index = player_index
        self.opponent = PLAYER_2 if player_index == PLAYER_1 else PLAYER_1

    def _pre_move(self, state):
        score = getattr(state, "score", None)
        print("SearchBot {0}, Move: {1}, Score: {2}".format(
            self.index + 1, state.move, score))

    def evaluate(self, state):
        kalahas = state.board.kalahas
        score = kalahas[self.index] - kalahas[self.opponent]

        # Always follow the winning path, but for fun also try to
        # get the maximum number of points possible
        winning_kalaha_points = (AMBOS * AMBO_BEANS) + 1
        if kalahas[self.index] >= winning_kalaha_points:
            score += 1000
        elif kalahas[self.opponent] >= winning_kalaha_points:
            score -= 1000

        return score

    def get_move(self, board):
        # TODO: actually implement iterative deepening with time constraints
        return self.ids(board, depth=6)

    def propagate_score(self, node):
        if node.parent:
            maximize = node.move.player == self.index
            parent_score = getattr(node.parent, "score", None)
            score = node.score
            if parent_score is None:
                node.parent.score = score
            else:
                if maximize and score > parent_score:
                    node.parent.score = score
                elif not maximize and score < parent_score:
                    node.parent.score = score
            self.propagate_score(node.parent)

    def ids(self, board, depth):
        print("IDS Depth {0}".format(depth))
        state = GameState(board=board, turn=self.index)
        children = state.get_children()
        frontier = [c for c in children]
        while frontier:
            node = frontier.pop()
            if node.depth >= depth or node.board.is_end_position():
                node.score = self.evaluate(node)
                self.propagate_score(node)
            else:
                for child in node.get_children():
                    frontier.append(child)

        children.sort(key=lambda s: getattr(s, "score", 0), reverse=True)
        if children:
            self._pre_move(children[0])
            return children[0].move
