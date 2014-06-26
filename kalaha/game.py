from copy import deepcopy


PLAYER_1 = 0
PLAYER_2 = 1
AMBOS = 6
AMBO_BEANS = 6


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
        return Board(ambos=deepcopy(self.ambos),
                     kalahas=deepcopy(self.kalahas))

    def __str__(self):
        return (
          "   {5:2d} {4:2d} {3:2d} {2:2d} {1:2d} {0:2d}\n".format(*self.ambos[1])
        + "{0:2d}                   {1:2d}\n".format(self.kalahas[1], self.kalahas[0])
        + "   {0:2d} {1:2d} {2:2d} {3:2d} {4:2d} {5:2d}".format(*self.ambos[0])
        )

    def is_end_position(self):
        return not any(self.ambos[0]) and not any(self.ambos[1])

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
                        # or victory if no more moves left
                        if not any(self.ambos[player]):
                            for i in range(AMBOS):
                                if self.ambos[opponent][i]:
                                    self.kalahas[player] += self.ambos[opponent][i]
                                    self.ambos[opponent][i] = 0
                                    self._anim_frame()
                        return player
                ambo = 0
                player_side = PLAYER_2 if player_side == PLAYER_1 else PLAYER_1
            else:
                # Inside ambo
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
                    # Game ended - opponent wins?
                    if not any(self.ambos[opponent]):
                        for i in range(AMBOS):
                            if self.ambos[player][i]:
                                self.kalahas[opponent] += self.ambos[player][i]
                                self.ambos[player][i] = 0
                                self._anim_frame()
                    return opponent
                ambo += 1


class Move(object):
    def __init__(self, ambo, player):
        self.ambo = ambo
        self.player = player

    def __str__(self):
        return "Player {0}, Ambo {1}".format(self.player + 1, self.ambo + 1)


if __name__ == "__main__":
    from .cli import play_game
    play_game()
