#!/usr/bin/env python
#-*- encoding: utf-8 -*-
import os
import random
import time


PLAYER_1 = 0
PLAYER_2 = 1
AMBOS = 6
AMBO_BEANS = 6


def clear():
    os.system("cls" if os.name == "nt" else "clear")


class Board(object):
    def __init__(self, ambos=None, kalahas=None):
        if ambos is None or kalahas is None:
            self.reset()
        else:
            self.ambos = ambos
            self.kalahas = kalahas

    def reset(self):
        self.ambos = [
            [AMBO_BEANS] * AMBOS,
            [AMBO_BEANS] * AMBOS,
        ]
        self.kalahas = [0, 0]

    def clone(self):
        from copy import deepcopy
        return Board(ambos=deepcopy(self.ambos),
                     kalahas=deepcopy(self.kalahas))

    def __str__(self):
        return (
          "   {5:2d} {4:2d} {3:2d} {2:2d} {1:2d} {0:2d}\n".format(*self.ambos[1])
        + "{0:2d}                   {1:2d}\n".format(self.kalahas[1], self.kalahas[0])
        + "   {0:2d} {1:2d} {2:2d} {3:2d} {4:2d} {5:2d}".format(*self.ambos[0])
        )

    def is_end_position(self):
        return not any(self.ambos[0]) or not any(self.ambos[1])

    def is_valid_move(self, move):
        ambo, player = move.ambo, move.player
        if ambo < 0 or ambo >= AMBOS:
            return False
        beans = self.ambos[player][ambo]
        return beans > 0

    def _anim_frame(self):
        # An uglyish way to show animations to the player
        # Should probably be done some oher way
        pass

    def make_move(self, move):
        """Alter the board by making a move on it
        Return index of the player to make the next move
        """
        ambo, player = move.ambo, move.player
        opponent = PLAYER_2 if player == PLAYER_1 else PLAYER_1
        beans = self.ambos[player][ambo]
        if beans == 0:
            raise ValueError("Invalid move")
        self.ambos[player][ambo] = 0
        player_side = player
        ambo += 1
        while True:
            self._anim_frame()
            if ambo >= AMBOS:
                # Inside kalaha
                if player_side == player:
                    # Own kalaha - sow
                    self.kalahas[player] += 1
                    beans -= 1
                    if not beans:
                        # Turn ended inside own kalaha => new turn for player
                        return player
                ambo = 0
                player_side = PLAYER_2 if player_side == PLAYER_1 else PLAYER_1
            else:
                beans -= 1
                self.ambos[player_side][ambo] += 1
                if not beans:
                    # Turn ended
                    if player_side == player and self.ambos[player][ambo] == 1:
                        # Ended in own, empty ambo
                        opposite_ambo = AMBOS - ambo - 1
                        self.kalahas[player] += (self.ambos[player][ambo]
                                                 + self.ambos[opponent][opposite_ambo])
                        self.ambos[player][ambo] = self.ambos[opponent][opposite_ambo] = 0
                    # Game ended?
                    if not any(self.ambos[player]):
                        for i in range(AMBOS):
                            if self.ambos[opponent][i]:
                                self.kalahas[player] += self.ambos[opponent][i]
                                self.ambos[opponent][i] = 0
                                self._anim_frame()
                    elif not any(self.ambos[opponent]):
                        for i in range(AMBOS):
                            if self.ambos[player][i]:
                                self.kalahas[opponent] += self.ambos[player][i]
                                self.ambos[player][i] = 0
                                self._anim_frame()
                    return opponent
                ambo += 1


class AnimatedBoard(Board):
    def _anim_frame(self):
        clear()
        print(self)
        #time.sleep(0.5)


class Move(object):
    def __init__(self, ambo, player):
        self.ambo = ambo
        self.player = player

    def __str__(self):
        return "Player {0}, Ambo {1}".format(self.player + 1, self.ambo + 1)


class HumanPlayer(object):
    def __init__(self, player_index):
        self.index = player_index

    def get_move(self, board):
        while True:
            raw = raw_input("P{0} [1-{1}]: ".format(self.index + 1, AMBOS))
            try:
                ambo = int(raw) - 1
            except ValueError:
                print "Invalid move"
            else:
                move = Move(ambo=ambo, player=self.index)
                if not board.is_valid_move(move):
                    print "Invalid move"
                else:
                    return move


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
        """Get all possible child states that result from moves by current player"""
        children = []
        for ambo in range(AMBOS):
            move = Move(ambo=ambo, player=self.turn)
            if self.board.is_valid_move(move):
                children.append(self.get_child(ambo))
        return children

    def __str__(self):
        return "GameState\nNext move: Player {0}\nPrev move: {1}\n{2}".format(
                self.turn + 1, self.move, self.board)


class RandomBot(object):
    def __init__(self, player_index):
        self.index = player_index

    def _pre_move(self, move):
        print("RandomBot {0}: Making move {1}".format(self.index + 1, move))
        #time.sleep(1)
        #time.sleep(0.5)

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
        #time.sleep(1)
        #time.sleep(0.5)

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
        score = self.evaluate(state)
        print("SearchBot {0}, Move: {1}, Score: {2}".format(
            self.index + 1, state.move, score))
        #time.sleep(1)
        time.sleep(0.5)

    #def evaluate(self, state):
    #    kalahas = state.board.kalahas
    #    ambos = [sum(state.board.ambos[0]), sum(state.board.ambos[1])]

    #    kalaha_score = kalahas[self.index] - kalahas[self.opponent]

    #    next_turn_score = 0
    #    if not state.board.is_end_position() and state.turn == self.index:
    #        next_turn_score += 1 + int(kalaha_score * 0.1)
    #    #elif not state.board.is_end_position() and state.turn == self.opponent:
    #        #next_turn_score -= 1 - int(kalaha_score * 0.1)

    #    ambo_score = ambos[self.opponent] - ambos[self.index]
    #    #return (kalaha_score * 3) + (next_turn_score * 2)
    #    return kalaha_score + next_turn_score

    def evaluate(self, state):
        kalahas = state.board.kalahas
        score = kalahas[self.index] - kalahas[self.opponent]
        #if not state.board.is_end_position() and state.turn == self.index:
        #    score += 1 + int(score * 0.2)
        if state.board.is_end_position():
            if score > 0:
                return 1000
            elif score < 0:
                return -1000
        return score

    def get_move(self, board):
        return self.ids(board, depth=5)

    def propagate_score(self, node, maximize):
        if node.parent:
            parent_score = getattr(node.parent, "score", None)
            score = node.score
            if parent_score is None:
                node.parent.score = score
            else:
                if maximize and score > parent_score:
                    node.parent.score = score
                elif score < parent_score:
                    node.parent.score = score
            self.propagate_score(node.parent, not maximize)

    def ids(self, board, depth):
        print("IDS Depth {0}".format(depth))
        state = GameState(board=board, turn=self.index)
        children = state.get_children()
        frontier = [c for c in children]
        choices = []
        while frontier:
            node = frontier.pop()
            if node.depth >= depth or node.board.is_end_position():
                maximize = node.turn == self.index
                node.score = self.evaluate(node)
                self.propagate_score(node, maximize=maximize)
            else:
                for child in node.get_children():
                    frontier.append(child)
        children.sort(key=lambda s: getattr(s, "score", 0), reverse=True)
        if children:
            self._pre_move(children[0])
            return children[0].move


def play_game(board_cls=AnimatedBoard,
              #player_1_cls=GreedyBot,
              #player_1_cls=RandomBot,
              player_1_cls=HumanPlayer,
              player_2_cls=SearchBot):
    board = board_cls()
    players = [player_1_cls(PLAYER_1), player_2_cls(PLAYER_2)]
    # XXX
    #players = [player_2_cls(PLAYER_1), player_1_cls(PLAYER_2)]

    board.reset()
    current_turn = PLAYER_1
    while not board.is_end_position():
        clear()
        print(board)
        move = players[current_turn].get_move(board)
        current_turn = board.make_move(move)
    if board.kalahas[PLAYER_1] > board.kalahas[PLAYER_2]:
        print("Player 1 wins! ({0:2d} - {1:2d})".format(*board.kalahas))
    elif board.kalahas[PLAYER_2] > board.kalahas[PLAYER_1]:
        print("Player 2 wins! ({0:2d} - {1:2d})".format(*board.kalahas))
    else:
        print("It's a tie! ({0:2d} - {1:2d})".format(*board.kalahas))


def _print_children(board, current_turn):
    state = GameState(board=board, turn=current_turn)
    print("=== Children ===")
    for child in state.get_children():
        print("=====================")
        print(child)
        print("=== Grandchildren ===")
        for grandchild in child.get_children():
            print(grandchild)
        print("=====================")
        print("")


if __name__ == "__main__":
    play_game()
