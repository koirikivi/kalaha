import pygame
import pygame.locals as pg


BG_COLOR = (20, 20, 20)
TEXT_SIZE = 15
TEXT_MARGIN = 3
NODE_WIDTH = 160
NODE_HEIGHT = 120
NODE_MARGIN = 10
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 1000


class TreeviewGui(object):

    def __init__(self, viewer):
        self.viewer = viewer
        self.running = False
        self.components = pygame.sprite.Group()

    def launch(self):
        self._init()
        clock = pygame.time.Clock()
        self.running = True
        while self.running:
            clock.tick(30)
            self._process_events()
            self._render()

    def _init(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.camera = [0, 0]
        self._init_tree()

    def _init_tree(self):
        self.components.empty()
        if not self.viewer._leaves:
            return
        y_pos = NODE_MARGIN
        tree = self.viewer._construct_tree()
        while tree and tree[0]:
            next_level = []
            x_pos = NODE_MARGIN
            for node, leaf_count, subtree in tree:
                midway = (leaf_count * (NODE_WIDTH + NODE_MARGIN)) / 2
                x_pos += midway
                component = _NodeComponent(node, self.viewer,
                                           position=(x_pos, y_pos))
                self.components.add(component)
                x_pos += midway
                next_level.extend(subtree)
            y_pos += NODE_HEIGHT + NODE_MARGIN
            tree = next_level

    def _process_events(self):
        for event in pygame.event.get():
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                self.running = False
            elif event.type == pg.MOUSEMOTION:
                if event.buttons[0]:
                    self.camera[0] += event.rel[0]
                    self.camera[1] += event.rel[1]
            elif event.type == pg.MOUSEBUTTONUP:
                if event.button == 1:
                    pos = (event.pos[0] - self.camera[0],
                           event.pos[1] - self.camera[1])
                    for component in self.components:
                        if component.rect.collidepoint(pos):
                            component.on_click()
                            # XXX: just update the whole tree
                            for c in self.components:
                                c.update()

    def _render(self):
        self.screen.fill(BG_COLOR)
        for component in self.components:
            pos = list(component.rect.topleft)
            pos[0] += self.camera[0]
            pos[1] += self.camera[1]
            self.screen.blit(component.image, pos)
        pygame.display.update()


def _draw_text(text, size=TEXT_SIZE, color=(100, 100, 100)):
    font = pygame.font.Font(None, size)
    return font.render(str(text), 1, color)


class _SimpleComponent(pygame.sprite.Sprite, object):
    bg_color = (245, 245, 245)

    def __init__(self, position=(0,0), dimensions=(NODE_WIDTH, NODE_HEIGHT),
                 text=""):
        super(_SimpleComponent, self).__init__()
        self.rect = pygame.Rect(position, dimensions)
        self.image = pygame.Surface(dimensions)
        self.image.fill(self.bg_color)
        if text:
            set_text(text)

    def on_click(self):
        pass

    def update(self):
        pass

    def set_text(self, text):
        self.image.fill(self.bg_color)
        for i, line in enumerate(text.splitlines()):
            text_surf = _draw_text(line)
            text_pos = (TEXT_MARGIN, TEXT_MARGIN + (i * TEXT_SIZE))
            self.image.blit(text_surf, text_pos)


class _NodeComponent(_SimpleComponent):
    def __init__(self, node, viewer, position=(0,0)):
        super(_NodeComponent, self).__init__(
                position=position, dimensions=(NODE_WIDTH, NODE_HEIGHT))
        self.node = node
        self.viewer = viewer
        self._text = ""
        self.update()

    def update(self):
        text = self.viewer._node_repr(self.node)
        if text != self._text:
            self.set_text(text)
            self._text = text

    def on_click(self):
        self.viewer.on_click(self.node)
