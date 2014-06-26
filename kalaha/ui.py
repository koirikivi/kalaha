import pygame
import pygame.locals as pg
from . import ai
from . import game
from .game import PLAYER_1, PLAYER_2, AMBOS


ANIMATE_EVENT = pg.USEREVENT + 1
PLAYER_MOVE_EVENT = pg.USEREVENT + 2


def draw_text(text, size=36, color=(100, 100, 100)):
    font = pygame.font.Font(None, size)
    return font.render(str(text), 1, color)


class Human(object):
    is_human = True

    def __init__(self, player_index):
        self.index = player_index

    def get_move(self, board):
        # Leave for the UI
        pass


class Game(object):
    def init(self):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        self.running = False
        self.components = pygame.sprite.Group()
        self.ambo_components = [[], []]
        self.kalaha_components = []
        self.name_components = []
        self.turn_component = None
        self.score_component = None
        self.new_game_components = []
        self.players = [Human(PLAYER_1), ai.RandomBot(PLAYER_2)]
        self.board = game.Board()

        center = self.screen.get_rect().center
        width = AmboComponent.w + 20
        left = center[0] - (((AMBOS - 1) * width) / 2)

        for index in range(AMBOS):
            component = AmboComponent(PLAYER_1, index)
            component.rect.centerx = left + index * width
            component.rect.centery = (center[1]) + 100
            component.active = True
            self.components.add(component)
            self.ambo_components[PLAYER_1].append(component)

            component = AmboComponent(PLAYER_2, index)
            component.rect.centerx = left + (width * (AMBOS - 1)) - index * width
            component.rect.centery = (center[1]) - 100
            self.components.add(component)
            self.ambo_components[PLAYER_2].append(component)

        component = KalahaComponent(PLAYER_1)
        self.kalaha_components.append(component)
        component.rect.centery = center[1]
        component.rect.right = 800 - 20
        self.components.add(component)

        component = KalahaComponent(PLAYER_2)
        self.kalaha_components.append(component)
        component.rect.centery = center[1]
        component.rect.left = 20
        self.components.add(component)

        component = SimpleTextComponent("Player")
        self.components.add(component)
        self.name_components.append(component)

        component = SimpleTextComponent("Player")
        self.components.add(component)
        self.name_components.append(component)

        self.turn_component = SimpleTextComponent("Current turn: Player 1")
        self.turn_component.rect.top = 10
        self.turn_component.rect.left = 10
        self.components.add(self.turn_component)

        self.score_component = SimpleTextComponent("Score: ")
        self.score_component.rect.left = 10
        self.score_component.rect.bottom = 600 - 20
        self.score_component.visible = False
        self.components.add(self.score_component)

        top = 500
        right = 800 - 40
        height = 30
        from functools import partial
        for i, bot_class in enumerate([ai.RandomBot, ai.GreedyBot, ai.SearchBot]):
            component = SimpleTextComponent("New game ({0})".format(bot_class.__name__), size=20)
            component.active = True
            component.on_click = partial(self.init_round, player_2_class=bot_class)
            component.rect.top = top + (height * i)
            component.rect.right = right
            self.components.add(component)

    def init_round(self, player_1_class=Human, player_2_class=ai.RandomBot):
        self.players = [player_1_class(PLAYER_1),
                        player_2_class(PLAYER_2)]
        self.name_components[PLAYER_1].set_text(player_1_class.__name__)
        self.name_components[PLAYER_1].rect.centerx = 400
        self.name_components[PLAYER_1].rect.bottom = 600 - 80
        self.name_components[PLAYER_2].set_text(player_2_class.__name__)
        self.name_components[PLAYER_2].rect.centerx = 400
        self.name_components[PLAYER_2].rect.top = 80
        self.board.reset()
        self.set_board_components(self.board)
        self.running = True
        self.current_turn = PLAYER_1
        self.waiting = False
        self.current_animation = None
        self.update_turn_component()
        self.score_component.visible = False

    def update_turn_component(self):
        self.turn_component.set_text("Current turn: Player {0} ({1})".format(
            self.current_turn + 1, self.players[self.current_turn].__class__.__name__))

    def set_board_components(self, board):
        self.kalaha_components[PLAYER_1].beans = board.kalahas[PLAYER_1]
        self.kalaha_components[PLAYER_2].beans = board.kalahas[PLAYER_2]
        for i in range(AMBOS):
            self.ambo_components[PLAYER_1][i].beans = board.ambos[PLAYER_1][i]
            self.ambo_components[PLAYER_2][i].beans = board.ambos[PLAYER_2][i]

    def play(self):
        self.init()
        clock = pygame.time.Clock()
        self.init_round()
        while self.running:
            clock.tick(30)
            self.process_events()
            self.render()
            self.logic()
            self.update_turn_component()

    def process_events(self):
        for event in pygame.event.get():
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                self.running = False
            elif event.type == pg.MOUSEMOTION and not self.waiting:
                self.remove_hilights()
                for component in self.components:
                    if component.active \
                            and component.rect.collidepoint(event.pos):
                        if hasattr(component, "ambo"):
                            move = game.Move(ambo=component.index, player=PLAYER_1)
                            if self.board.is_valid_move(move):
                                component.hilight = True
                        else:
                            component.hilight = True
            elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
                for component in self.components:
                    if component.active \
                            and not self.waiting \
                            and component.rect.collidepoint(event.pos) \
                            and hasattr(component, "on_click"):
                        component.on_click()
            elif event.type == ANIMATE_EVENT:
                self.animate()
            elif event.type == PLAYER_MOVE_EVENT:
                move = game.Move(ambo=event.ambo, player=PLAYER_1)
                if self.board.is_valid_move(move):
                    self.waiting = True
                    self.start_animation(move)

    def logic(self):
        is_computer_turn = self.running \
                           and not self.waiting \
                           and not self.board.is_end_position() \
                           and not getattr(self.players[self.current_turn], "is_human", False)
        if is_computer_turn:
            self.waiting = True
            move = self.players[self.current_turn].get_move(self.board)
            self.start_animation(move)
        if self.board.is_end_position():
            board = self.board
            if board.kalahas[PLAYER_1] > board.kalahas[PLAYER_2]:
                win_text = "Player 1 wins! ({0:2d} - {1:2d})".format(*board.kalahas)
            elif board.kalahas[PLAYER_2] > board.kalahas[PLAYER_1]:
                win_text = "Player 2 wins! ({0:2d} - {1:2d})".format(*board.kalahas)
            else:
                win_text = "It's a tie! ({0:2d} - {1:2d})".format(*board.kalahas)
            self.score_component.visible = True
            self.score_component.set_text(win_text)
            self.set_board_components(board)

    def start_animation(self, move):
        self.current_animation = Animation(self.board, move)
        self.animate()
        pygame.time.set_timer(ANIMATE_EVENT, 600)

    def animate(self):
        if self.current_animation.is_over():
            pygame.time.set_timer(ANIMATE_EVENT, 0)
            self.remove_hilights()
            self.make_move(self.current_animation.get_move())
        else:
            self.remove_hilights()
            active_type, active_player, active_index = self.current_animation.get_active_tile()
            if active_type == "kalaha":
                self.kalaha_components[active_player].hilight = True
            elif active_type == "ambo":
                self.ambo_components[active_player][active_index].hilight = True
            self.set_board_components(self.current_animation.get_board())
        self.current_animation.next()

    def make_move(self, move):
        print("Making move {0}".format(move))
        self.current_turn = self.board.make_move(move)
        self.set_board_components(self.board)
        self.waiting = False

    def remove_hilights(self):
        for component in self.components:
            if hasattr(component, "hilight"):
                component.hilight = False

    def render(self):
        self.screen.fill((20, 20, 20))
        for component in self.components:
            if getattr(component, "visible", True):
                component.update()
                self.screen.blit(component.image, component.rect)
        pygame.display.update()


class Animation(object):
    def __init__(self, board, move):
        self.move = move
        self.board = board.clone()
        self.player_side = move.player
        self.player = move.player
        self.index = move.ambo
        self.beans = self.board.ambos[self.player_side][self.index]
        self.board.ambos[self.player_side][self.index] = 0
        self.active_tile = ("ambo", self.player_side, self.index)
        self.index += 1

    def is_over(self):
        return self.beans <= -1

    def get_board(self):
        return self.board

    def get_move(self):
        return self.move

    def get_active_tile(self):
        return self.active_tile

    def next(self):
        if self.beans < 0:
            return
        elif self.index >= AMBOS:
            if self.player_side == self.player:
                self.board.kalahas[self.player] += 1
                self.beans -= 1
            self.index = 0
            self.active_tile = ("kalaha", self.player_side, 0)
            self.player_side = PLAYER_1 if self.player_side == PLAYER_2 \
                                        else PLAYER_2
        else:
            self.board.ambos[self.player_side][self.index] += 1
            self.active_tile = ("ambo", self.player_side, self.index)
            self.beans -= 1
            self.index += 1


class ClickableComponent(pygame.sprite.Sprite, object):
    w, h = (60, 80)
    bg_color = (100, 200, 150)

    def __init__(self):
        super(ClickableComponent, self).__init__()
        pos = (0, 0)
        self.rect = pygame.Rect(pos, (self.w, self.h))
        self.bg = pygame.Surface((self.w, self.h))
        self.bg.fill(self.bg_color)
        self.image = self.bg
        self.active = False
        self.visible = True

    def update(self):
        pass

    def on_click(self):
        pass


class SimpleTextComponent(ClickableComponent):
    def __init__(self, text="", color=(245, 245, 245), bg_color=(20, 20, 20), size=36):
        super(SimpleTextComponent, self).__init__()
        self.active = False
        self.visible = True
        self.color = color
        self.bg_color = bg_color
        self.size = size
        self.set_text(text)

    def set_text(self, text):
        topleft = None
        if hasattr(self, "rect"):
            topleft = self.rect.top, self.rect.left
        text_surf = draw_text(text, size=self.size, color=self.color)
        text_rect = text_surf.get_rect()
        self.image = pygame.Surface((text_rect.w + 20, text_rect.h + 20))
        self.image.fill(self.bg_color)
        self.rect = self.image.get_rect()
        text_rect.center = (self.rect.w / 2, self.rect.h / 2)
        self.image.blit(text_surf, text_rect)
        if topleft:
            self.rect.top = topleft[0]
            self.rect.left = topleft[1]


class BeanComponent(ClickableComponent):
    bg_color_normal = (100, 200, 150)
    bg_color_hilight = (60, 140, 100)

    def __init__(self, player):
        self.player = player
        self.beans = 0
        self.hilight = False
        super(BeanComponent, self).__init__()
        self.update()

    @property
    def bg_color(self):
        return self.bg_color_hilight if self.hilight else self.bg_color_normal

    def get_text(self):
        return self.beans

    def update(self):
        self.image.fill(self.bg_color)
        text = draw_text(self.get_text())
        text_rect = text.get_rect()
        text_rect.center = (self.w / 2, self.h / 2)
        self.image.blit(text, text_rect)


class AmboComponent(BeanComponent):
    def __init__(self, player, index):
        self.index = index
        super(AmboComponent, self).__init__(player)

    def on_click(self):
        pygame.event.post(pygame.event.Event(PLAYER_MOVE_EVENT, ambo=self.index))


class KalahaComponent(BeanComponent):
    w = 140


if __name__ == "__main__":
    Game().play()
