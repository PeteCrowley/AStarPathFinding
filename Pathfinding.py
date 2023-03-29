import arcade
import random
import math
import time

PADDING = 50
NODES = 50
NODE_RADIUS = 5
LINE_WIDTH = max(1, NODE_RADIUS // 10)
DELAY = 0.1


class PriorityQueue:
    def __init__(self):
        self.queue = []

    def add_node(self, node):
        self.queue.append(node)

    def pop_off_top(self):
        least = min(self.queue, key=lambda x: x.h)
        self.queue.remove(least)
        return least


class Node(arcade.SpriteCircle):
    def __init__(self,
                 x: int,
                 y: int,
                 radius: int = NODE_RADIUS,
                 color: arcade.Color = arcade.color.BLUE):
        super().__init__(radius, color)
        self.center_x = x
        self.center_y = y
        self.connected_nodes = []
        self.line_color = arcade.color.BLACK
        self.line_width = LINE_WIDTH
        self.f = 1_000_000
        self.g = 1_000_000
        self.h = self.f + self.g
        self.parent = None

    def add_connected_nodes(self, nodes):
        self.connected_nodes.extend(nodes)

    def add_connected_node(self, other):
        self.connected_nodes.append(other)
        other.connected_nodes.append(self)

    def delete_connection(self, other):
        self.connected_nodes.remove(other)
        other.connected_nodes.remove(self)

    def draw_connections(self):
        for node in self.connected_nodes:
            arcade.draw_line(self.center_x, self.center_y, node.center_x, node.center_y,
                             self.line_color, self.line_width)


class Pathfinding(arcade.Window):
    def __init__(self, num_nodes: int = 10):
        super().__init__()
        self.start_nodes = num_nodes
        self.nodes = None
        self.selected_node = None
        self.moving_node = False
        self.start_node = None
        self.end_node = None
        self.path = None

    def setup(self):
        self.nodes = arcade.sprite_list.SpriteList()
        self.start_node = Node(50, self.height - 50, color=arcade.color.WHITE)
        self.end_node = Node(self.width - 50, 50, color=arcade.color.RED)
        self.path = None
        self.nodes.extend([self.start_node, self.end_node])
        self.background_color = arcade.color.JUNGLE_GREEN
        for i in range(0, self.start_nodes - 2):
            self.add_node()
        self.random_edges()

    def random_edges(self):
        for i in range(0, len(self.nodes)):
            for x in range(i+1, len(self.nodes)):
                odds_of_edge = 10 / self.calculate_distance(self.nodes[i], self.nodes[x])
                if random.random() < odds_of_edge:
                    self.nodes[i].add_connected_node(self.nodes[x])

    def calculate_heuristic(self, node) -> float:
        return math.sqrt((node.center_x - self.end_node.center_x) ** 2 + (node.center_y - self.end_node.center_y) ** 2)

    @staticmethod
    def calculate_distance(node, parent):
        return math.sqrt((node.center_x - parent.center_x) ** 2 + (node.center_y - parent.center_y) ** 2)

    def astar_pathfinding(self):
        checked_nodes = []
        q = PriorityQueue()
        self.start_node.f = 0
        self.start_node.g = self.calculate_distance(self.start_node, self.end_node)
        self.start_node.h = self.start_node.g
        parent = self.start_node
        checked_nodes.append(parent)
        while parent != self.end_node:
            children = parent.connected_nodes
            for child in children:
                new_f = parent.f + self.calculate_distance(parent, child)
                if new_f > child.f:
                    continue
                child.f = parent.f + self.calculate_distance(parent, child)
                child.g = self.calculate_heuristic(child)
                child.h = child.f + child.g
                child.parent = parent
                child.texture = arcade.make_circle_texture(NODE_RADIUS*2, arcade.color.GOLD)
                if child not in checked_nodes:
                    q.add_node(child)
                self.dispatch_events()
                self.on_draw()
                self.flip()
            time.sleep(DELAY)

            try:
                parent = q.pop_off_top()
            except ValueError:
                print("There is no path between the start and end nodes. Please make one.")
                return
            checked_nodes.append(parent)
        path = [self.end_node]
        current_node = self.end_node
        while current_node != self.start_node:
            current_node = current_node.parent
            path.append(current_node)
        return list(path.__reversed__())

    def add_node(self):
        node_x = random.randint(PADDING, self.width - PADDING)
        node_y = random.randint(PADDING, self.height - PADDING)
        node = Node(node_x, node_y)
        while len(self.nodes) > 0 and arcade.get_closest_sprite(node, self.nodes)[1] < 10:
            node.center_x = random.randint(PADDING, self.width - PADDING)
            node.center_y = random.randint(PADDING, self.height - PADDING)

        self.nodes.append(node)

    def delete_node(self, node):
        for n in self.nodes:
            if node in n.connected_nodes:
                n.connected_nodes.remove(node)
        self.nodes.remove(node)

    def on_draw(self):
        self.clear()
        for node in self.nodes:
            node.draw_connections()
        self.nodes.draw()

        if self.selected_node is not None:
            arcade.draw_circle_outline(self.selected_node.center_x, self.selected_node.center_y, NODE_RADIUS,
                                       arcade.color.YELLOW, border_width=3)
            if self.moving_node:
                arcade.draw_circle_outline(self.selected_node.center_x, self.selected_node.center_y, NODE_RADIUS,
                                           arcade.color.RED, border_width=1)
        if self.path is None:
            return
        for i in range(0, len(self.path)-1):
            arcade.draw_line(self.path[i].center_x, self.path[i].center_y,
                             self.path[i+1].center_x, self.path[i+1].center_y,
                             arcade.color.GREEN, line_width=LINE_WIDTH)

    def on_key_press(self, symbol: int, modifiers: int):
        """
        N for a new node
        M to move a selected node
        Backspace to delete a selected node
        A to run astar pathfinding algorithm
        R to reset the nodes
        C to clear all edges
        D to clear a found path
        E to delete all nodes
        :param symbol: The symbol clicked
        :param modifiers: modifiers
        :return: None
        """
        if symbol == arcade.key.N:
            self.add_node()
        elif symbol == arcade.key.M and self.selected_node is not None:
            self.moving_node = not self.moving_node
        elif symbol == arcade.key.BACKSPACE and self.selected_node is not None:
            self.delete_node(self.selected_node)
            self.selected_node = None
        elif symbol == arcade.key.A:
            self.path = self.astar_pathfinding()
        elif symbol == arcade.key.R:
            self.setup()
        elif symbol == arcade.key.C:
            for node in self.nodes:
                node.connected_nodes = []
        elif symbol == arcade.key.D:
            self.path = None
            for node in self.nodes:
                if node == self.start_node:
                    node.texture = arcade.make_circle_texture(NODE_RADIUS*2, arcade.color.WHITE)
                elif node == self.end_node:
                    node.texture = arcade.make_circle_texture(NODE_RADIUS * 2, arcade.color.RED)
                else:
                    node.texture = arcade.make_circle_texture(NODE_RADIUS * 2, arcade.color.BLUE)


        elif symbol == arcade.key.E:
            self.nodes = arcade.sprite_list.SpriteList()
            self.nodes.append(self.start_node)
            self.nodes.append(self.end_node)
            self.start_node.connected_nodes = []
            self.end_node.connected_nodes = []

    def get_node_at_point(self, x, y):
        for node in self.nodes:
            if node.collides_with_point((x, y)):
                return node
        return None

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):

        if self.selected_node is None:
            self.selected_node = self.get_node_at_point(x, y)
            return
        if self.moving_node:
            if len(arcade.check_for_collision_with_list(self.selected_node, self.nodes)) < 1:
                self.selected_node = None
                self.moving_node = False
            return
        if (n := self.get_node_at_point(x, y)) is not None and n != self.selected_node:
            if n not in self.selected_node.connected_nodes:
                self.selected_node.add_connected_node(n)
            else:
                self.selected_node.delete_connection(n)
        self.selected_node = None
        self.moving_node = False

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        if self.moving_node:
            self.selected_node.center_x = x
            self.selected_node.center_y = y


def main():
    p = Pathfinding(num_nodes=NODES)
    p.setup()
    p.run()


if __name__ == "__main__":
    main()
