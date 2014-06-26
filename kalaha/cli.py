import os
import time
from .game import Board, Move, PLAYER_1, PLAYER_2, AMBOS
from . import ai


ANIM_SLEEP_TIME = 0.3


def clear():
    os.system("cls" if os.name == "nt" else "clear")


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


class AnimatedBoard(Board):
    def _anim_frame(self):
        clear()
        print(self)
        time.sleep(ANIM_SLEEP_TIME)


def play_game(board_cls=AnimatedBoard,
              player_1_cls=HumanPlayer,
              player_2_cls=ai.SearchBot
              ):
    board = board_cls()
    players = [player_1_cls(PLAYER_1), player_2_cls(PLAYER_2)]

    board.reset()
    current_turn = PLAYER_1
    while not board.is_end_position():
        clear()
        print(board)
        move = players[current_turn].get_move(board)
        current_turn = board.make_move(move)
    if board.kalahas[PLAYER_1] > board.kalahas[PLAYER_2]:
        print("Player 1 ({0}) wins! ({1:2d} - {2:2d})".format(
            players[0].__class__.__name__, *board.kalahas))
    elif board.kalahas[PLAYER_2] > board.kalahas[PLAYER_1]:
        print("Player 2 ({0}) wins! ({1:2d} - {2:2d})".format(
            players[1].__class__.__name__, *board.kalahas))
    else:
        print("It's a tie! ({0:2d} - {1:2d})".format(*board.kalahas))
