from __future__ import print_function


class TreeViewer(object):
    """A class to print a constant-depth tree with a single root"""
    # TODO: varying depths, multiple roots and stuff
    # TODO: make the thing cosume less memory -- it seems very terrible now

    default_config = {
        "parent_attr": "parent",
        "leaf_repr_width": 10,
        "repr_function": None,
        "on_click": lambda n: None,
    }

    def __init__(self, **config):
        self._leaves = []
        for key, value in self.default_config.items():
            setattr(self, key, config.get(key, value))

    def __repr__(self):
        return "<TreeViewer: {0} leaves>".format(len(self._leaves))

    def add_leaf(self, node):
        self._leaves.append(node)

    def print_tree(self):
        if not self._leaves:
            print("[Empty tree]")
            return
        tree = self._construct_tree()
        while tree and tree[0]:
            next_level = []
            for node, leaf_count, subtree in tree:
                string = self._node_repr(node)
                string = string.center(leaf_count * self.leaf_repr_width)
                print(string, end="")
                next_level.extend(subtree)
            print("")
            tree = next_level

    def launch_gui(self):
        from .treeview_gui import TreeviewGui
        TreeviewGui(self).launch()
        
    def _node_repr(self, node):
        if self.repr_function is not None:
            return self.repr_function(node)
        repr_or_func = getattr(node, "__inspect_repr__", None)
        if repr_or_func is None:
            return str(node)
        elif hasattr(repr_or_func, "__call__"):
            return str(repr_or_func())
        else:
            return str(repr_or_func)

    def _construct_tree(self):
        """Construct and return the whole tree based on the leaves given
        Tree form:
            (node, cumulative leaf count, children)
        where `children` is in the same form as the whole tree
        """
        tree = [[n, 1, []] for n in self._leaves]
        while tree[0][0].parent is not None:
            tree = sorted(tree, key=lambda t: self._node_parent(t[0]))
            parents = []
            for node, count, subtree in tree:
                if parents and parents[-1][0] is node.parent:
                    parents[-1][1] += count
                    parents[-1][2].append([node, count, subtree])
                else:
                    parents.append([node.parent, count, [[node, count, subtree]]])
            tree = parents
        return tree

    def _poot_node(self, node):
        while True:
            parent = self._node_parent(node)
            if parent is None:
                return node
            node = parent

    def _node_parent(self, node):
        return getattr(node, self.parent_attr)


def test():
    class Node(object):
        def __init__(self, parent, level, score=0.0):
            self.parent = parent
            self.level = level
            self.score = score

        def __inspect_repr__(self):
            return "{0}: {1}".format(self.level, self.score)

        def __repr__(self):
            return self.__inspect_repr__()

    grand_grand_parent_node = Node(None, 0, score=1.0)
    grand_parent_node_1 = Node(grand_grand_parent_node, 1, score=1.0)
    grand_parent_node_2 = Node(grand_grand_parent_node, 1, score=1.0)
    parent_node_1 = Node(grand_parent_node_1, 2, score=1.0)
    parent_node_2 = Node(grand_parent_node_2, 2, score=2.0)
    parent_node_3 = Node(grand_parent_node_1, 2, score=2.0)

    viewer = TreeViewer(on_click=lambda n: print(n))
    viewer.add_leaf(Node(parent_node_1, 3, score=1.0))
    viewer.add_leaf(Node(parent_node_1, 3, score=2.0))
    viewer.add_leaf(Node(parent_node_1, 3, score=3.0))
    viewer.add_leaf(Node(parent_node_2, 3, score=4.0))
    viewer.add_leaf(Node(parent_node_3, 3, score=5.0))
    viewer.add_leaf(Node(parent_node_3, 3, score=5.0))
    viewer.print_tree()
    viewer.launch_gui()


if __name__ == "__main__":
    test()
