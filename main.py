import pyxel
from enum import Enum, auto
from typing import Union
import random
from itertools import product


BOARD_WIDTH = 6
BOARD_HEIGHT = 12


class PuyoColor(Enum):
    EMPTY = 0
    RED = 1
    BLUE = 2
    GREEN = 3
    YELLOW = 4
    PURPLE = 5

    def draw(self, x: float, y: float) -> None:
        if self.value != 0:
            pyxel.blt(x, y, 0, self.value * 8, 0, 8, 8)


PUYO_COLORS = [
    PuyoColor.RED,
    PuyoColor.BLUE,
    PuyoColor.GREEN,
    PuyoColor.YELLOW,
    PuyoColor.PURPLE,
]


class Direction(Enum):
    DOWN = 0, 0, 1
    LEFT = 1, -1, 0
    UP = 2, 0, -1
    RIGHT = 3, 1, 0

    def __init__(self, index: int, x: int, y: int) -> None:
        super().__init__()
        self.index = index
        self.x = x
        self.y = y


DIRECTIONS = [
    Direction.DOWN,
    Direction.LEFT,
    Direction.UP,
    Direction.RIGHT,
]


def rotate_left(direction: Direction) -> Direction:
    return DIRECTIONS[(direction.index + 3) % 4]

def rotate_right(direction: Direction) -> Direction:
    return DIRECTIONS[(direction.index + 1) % 4]


class Puyo:
    def __init__(self, dir: Direction, col1: PuyoColor, col2: PuyoColor) -> None:
        self.dir = dir
        self.col1 = col1
        self.col2 = col2

    def draw(self, x: float, y: float) -> None:
        self.col1.draw(x, y)
        self.col2.draw(x + self.dir.x * 8, y + self.dir.y * 8)


def generate_random_puyo() -> Puyo:
    col1 = random.choice(PUYO_COLORS)
    col2 = random.choice(PUYO_COLORS)
    return Puyo(Direction.DOWN, col1, col2)


class DroppingPuyo:
    def __init__(self, x: int, y: int, color: PuyoColor) -> None:
        self.x = x
        self.y = y
        self.color = color

    def __str__(self) -> str:
        return f"({self.x}, {self.y}, {self.color})"


class Board:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.board: list[list[PuyoColor]] = []
        for x in range(self.width):
            self.board.append([])
            for y in range(self.height):
                self.board[x].append(PuyoColor.EMPTY)

    def is_empty(self, x: int, y: int) -> bool:
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return False
        return self.board[x][y] == PuyoColor.EMPTY


class GameState(Enum):
    OPERATING = auto()
    DROPPING = auto()
    ERASING = auto()


class App:
    def __init__(self) -> None:
        pyxel.init(8 * (BOARD_WIDTH + 4), 8 * (BOARD_HEIGHT + 3), title="Puyo", fps=30)
        pyxel.load("./resource.pyxres")
        self.initialize()
        pyxel.run(self.update, self.draw)

    def initialize(self) -> None:
        self.board = Board(BOARD_WIDTH, BOARD_HEIGHT)

        self.puyo = generate_random_puyo()
        self.next = generate_random_puyo()
        self.puyo_x = 2
        self.puyo_y = 1
        self.state = GameState.OPERATING
        self.dropping_puyos = []

    def update(self) -> None:
        # for p in self.dropping_puyos:
        #     print(p, end=" | ")
        # print("*")
        match self.state:
            case GameState.OPERATING:
                self._handle_operation()
                if pyxel.frame_count % 20 == 0 or pyxel.btnp(pyxel.KEY_DOWN):
                    stop = self._drop_puyo()
                    if stop:
                        self.state = GameState.DROPPING
            case GameState.DROPPING:
                if pyxel.frame_count % 5 == 0:
                    stop = self._drop_dropping_puyos()
                    if stop:
                        self.erased_puyos = self._detect_eraseable()
                        if self.erased_puyos:
                            self.state = GameState.ERASING
                            self.erase_end_frame = pyxel.frame_count + 10
                        else:
                            self._next_puyo()
                            self.state = GameState.OPERATING
            case GameState.ERASING:
                if pyxel.frame_count > self.erase_end_frame:
                    self._erase()
                    dropping_puyos = self._detect_dropping_puyos()
                    if dropping_puyos:
                        self.dropping_puyos = dropping_puyos
                        self.state = GameState.DROPPING
                    else:
                        self._next_puyo()
                        self.state = GameState.OPERATING

    def _next_puyo(self) -> None:
        self.puyo_x = 2
        self.puyo_y = 1
        self.puyo = self.next
        self.next = generate_random_puyo()

    def _handle_operation(self) -> None:
        if pyxel.btnp(pyxel.KEY_LEFT):
            new_dir = self.puyo.dir
            pos1x = self.puyo_x - 1
            pos1y = self.puyo_y
            pos2x = self.puyo_x + self.puyo.dir.x - 1
            pos2y = self.puyo_y + self.puyo.dir.y
        elif pyxel.btnp(pyxel.KEY_RIGHT):
            new_dir = self.puyo.dir
            pos1x = self.puyo_x + 1
            pos1y = self.puyo_y
            pos2x = self.puyo_x + self.puyo.dir.x + 1
            pos2y = self.puyo_y + self.puyo.dir.y
        elif pyxel.btnp(pyxel.KEY_A):
            new_dir = rotate_left(self.puyo.dir)
            pos1x = self.puyo_x
            pos1y = self.puyo_y
            pos2x = self.puyo_x + new_dir.x
            pos2y = self.puyo_y + new_dir.y
        elif pyxel.btnp(pyxel.KEY_D):
            new_dir = rotate_right(self.puyo.dir)
            pos1x = self.puyo_x
            pos1y = self.puyo_y
            pos2x = self.puyo_x + new_dir.x
            pos2y = self.puyo_y + new_dir.y
        else:
            return
        
        if self.board.is_empty(pos1x, pos1y) and self.board.is_empty(pos2x, pos2y):
            self.puyo.dir = new_dir
            self.puyo_x = pos1x
            self.puyo_y = pos1y

    def _drop_puyo(self) -> bool:
        movable1 = self.board.is_empty(self.puyo_x, self.puyo_y + 1)
        movable2 = self.board.is_empty(self.puyo_x + self.puyo.dir.x, self.puyo_y + self.puyo.dir.y + 1)
        if not (movable1 and movable2):
            self.dropping_puyos = [
                DroppingPuyo(self.puyo_x, self.puyo_y, self.puyo.col1),
                DroppingPuyo(self.puyo_x + self.puyo.dir.x, self.puyo_y + self.puyo.dir.y, self.puyo.col2),
            ]
            return True
        self.puyo_y += 1
        return False
    
    def _drop_dropping_puyos(self) -> bool:
        res = True
        # 下にあるぷよから処理する
        self.dropping_puyos.sort(key=lambda dropping_puyo: dropping_puyo.y, reverse=True)
        for dropping_puyo in self.dropping_puyos[:]:
            if self.board.is_empty(dropping_puyo.x, dropping_puyo.y + 1):
                dropping_puyo.y += 1
                res = False
            else:
                self.board.board[dropping_puyo.x][dropping_puyo.y] = dropping_puyo.color
                self.dropping_puyos.remove(dropping_puyo)
        return res

    def _detect_eraseable(self) -> list[tuple[int, int]]:
        groupings: list[list[int]] = []
        for x in range(BOARD_WIDTH):
            groupings.append([])
            for y in range(BOARD_HEIGHT):
                groupings[x].append(0)

        group_pos_list: dict[int, list[tuple[int, int]]] = {}
        group_pos_list[0] = [(0, 0)]
        next_group = 1

        for x in range(1, BOARD_WIDTH):
            current = self.board.board[x][0]
            previous = self.board.board[x - 1][0]
            if current == previous:
                group_pos_list[groupings[x - 1][0]].append((x, 0))
                groupings[x][0] = groupings[x - 1][0]
            else:
                group_pos_list[next_group] = [(x, 0)]
                groupings[x][0] = next_group
                next_group += 1
        for y in range(1, BOARD_HEIGHT):
            current = self.board.board[0][y]
            previous = self.board.board[0][y - 1]
            if current == previous:
                group_pos_list[groupings[0][y - 1]].append((0, y))
                groupings[0][y] = groupings[0][y - 1]
            else:
                group_pos_list[next_group] = [(0, y)]
                groupings[0][y] = next_group
                next_group += 1
        for x, y in product(range(1, BOARD_WIDTH), range(1, BOARD_HEIGHT)):
            current = self.board.board[x][y]
            left = self.board.board[x - 1][y]
            up = self.board.board[x][y - 1]
            if current == left and current == up:
                left_grouping = groupings[x - 1][y]
                up_grouping = groupings[x][y - 1]
                if left_grouping == up_grouping:
                    group_pos_list[left_grouping].append((x, y))
                    groupings[x][y] = left_grouping
                else:
                    group_pos_list[left_grouping].append((x, y))
                    groupings[x][y] = left_grouping
                    for px, py in group_pos_list[up_grouping]:
                        group_pos_list[left_grouping].append((px, py))
                        groupings[px][py] = left_grouping
                    del(group_pos_list[up_grouping])
            elif current == left:
                group_pos_list[groupings[x - 1][y]].append((x, y))
                groupings[x][y] = groupings[x - 1][y]
            elif current == up:
                group_pos_list[groupings[x][y - 1]].append((x, y))
                groupings[x][y] = groupings[x][y - 1]
            else:
                group_pos_list[next_group] = [(x, y)]
                groupings[x][y] = next_group
                next_group += 1

        res: list[tuple[int, int]] = []
        for pos_list in group_pos_list.values():
            first_pos = pos_list[0]
            if self.board.board[first_pos[0]][first_pos[1]] != PuyoColor.EMPTY and len(pos_list) >= 4:
                res.extend(pos_list)
        return res
    
    def _erase(self) -> None:
        for x, y in self.erased_puyos:
            self.board.board[x][y] = PuyoColor.EMPTY
    
    def _detect_dropping_puyos(self) -> list[DroppingPuyo]:
        dropping_puyos: list[DroppingPuyo] = []
        for x in range(BOARD_WIDTH):
            over_empty = False
            for h in range(0, BOARD_HEIGHT):
                y = BOARD_HEIGHT - h - 1
                if self.board.is_empty(x, y):
                    over_empty = True
                elif over_empty:
                    dropping_puyos.append(DroppingPuyo(x, y, self.board.board[x][y]))
                    self.board.board[x][y] = PuyoColor.EMPTY

        return dropping_puyos

    def draw(self) -> None:
        pyxel.cls(pyxel.COLOR_BLACK)
        self._draw_frame()
        self._draw_board_puyo()
        self._draw_next_puyo()
        match self.state:
            case GameState.OPERATING:
                self._draw_puyo()
            case GameState.DROPPING:
                self._draw_dropping_puyos()
            case GameState.ERASING:
                if pyxel.frame_count % 2 == 0:
                    self._draw_erasing_effects()

    def _draw_frame(self) -> None:
        by = 8 * (BOARD_HEIGHT + 1)
        for x in range(BOARD_WIDTH + 2):
            pyxel.blt(x * 8, 0, 0, 0, 0, 8, 8)
            pyxel.blt(x * 8, by, 0, 0, 0, 8, 8)
        rx = 8 * (BOARD_WIDTH + 1)
        for y in range(1, BOARD_HEIGHT + 2):
            pyxel.blt(0, y * 8, 0, 0, 0, 8, 8)
            pyxel.blt(rx, y * 8, 0, 0, 0, 8, 8)
        pyxel.blt(24, 8, 0, 56, 0, 8, 8)

    def _draw_board_puyo(self) -> None:
        for x in range(BOARD_WIDTH):
            for y in range(BOARD_HEIGHT):
                self.board.board[x][y].draw((x + 1) * 8, (y + 1) * 8)

    def _draw_next_puyo(self) -> None:
        self.next.col1.draw(8 * 8, 0)
        self.next.col2.draw(8 * 8, 1 * 8)

    def _draw_puyo(self) -> None:
        self.puyo.draw((self.puyo_x + 1) * 8, (self.puyo_y + 1) * 8)

    def _draw_dropping_puyos(self) -> None:
        for dropping_puyo in self.dropping_puyos:
            dropping_puyo.color.draw((dropping_puyo.x + 1) * 8, (dropping_puyo.y + 1) * 8)

    def _draw_erasing_effects(self) -> None:
        for x, y in self.erased_puyos:
            pyxel.blt((x + 1) * 8, (y + 1) * 8, 0, 48, 0, 8, 8)

App()