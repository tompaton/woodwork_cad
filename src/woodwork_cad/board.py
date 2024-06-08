from dataclasses import dataclass, field
from math import cos, radians, sin, sqrt
from typing import Iterable, List, Optional, Tuple

from .svg import SVGCanvas

__all__ = [
    "Board",
    "draw_boards",
    "cut",
    "cut_waste",
    "rip",
    "waste",
    "process",
    "process_all",
    "process_first",
    "joint2",
    "label_all",
    "cube_net",
]


class Defect:
    def offset(self, offset_x: float, offset_y: float) -> "Defect":
        raise NotImplementedError

    def visible(self, offset_x: float, offset_y: float, L: float, W: float) -> bool:
        raise NotImplementedError

    def draw(self, canvas: SVGCanvas, x: float, y: float) -> None:
        raise NotImplementedError


@dataclass
class Hole(Defect):
    x: float
    y: float
    r: float = 5

    def offset(self, offset_x: float, offset_y: float) -> "Hole":
        return Hole(self.x + offset_x, self.y + offset_y, self.r)

    def visible(self, offset_x: float, offset_y: float, L: float, W: float) -> bool:
        return (offset_x < self.x < offset_x + L) and (offset_y < self.y < offset_y + W)

    def draw(self, canvas: SVGCanvas, x: float, y: float) -> None:
        canvas.circle(x + self.x, y + self.y, self.r, "orange", stroke_width=1)


@dataclass
class Notch(Defect):
    x1: float
    y1: float
    x2: float
    y2: float

    def offset(self, offset_x: float, offset_y: float) -> "Notch":
        return Notch(
            self.x1 + offset_x,
            self.y1 + offset_y,
            self.x2 + offset_x,
            self.y2 + offset_y,
        )

    def visible(self, offset_x: float, offset_y: float, L: float, W: float) -> bool:
        return not (
            self.x2 < offset_x
            or self.x1 > offset_x + L
            or self.y2 < offset_y
            or self.y1 > offset_y + W
        )

    def draw(self, canvas: SVGCanvas, x: float, y: float) -> None:
        canvas.rect(
            x + self.x1,
            y + self.y1,
            self.x2 - self.x1,
            self.y2 - self.y1,
            "orange",
            stroke_width=1,
        )


@dataclass
class Board:
    L: float
    W: float
    T: float

    parent: Optional["Board"] = None
    offset_x: float = 0
    offset_y: float = 0

    cuts: list[tuple[str, float, float, float, float, str, float, float]] = field(
        default_factory=list
    )

    _defects: list[Defect] = field(default_factory=list)
    _profile: List[Tuple[float, float]] = field(default_factory=list)

    label: str = ""

    @property
    def area(self):
        return self.L * self.W

    @property
    def aspect(self):
        return self.L / self.W

    def add_defect(self, defect: Defect) -> None:
        self._defects.append(defect)

    @property
    def defects(self) -> Iterable[Defect]:
        yield from self._defects
        if self.parent:
            for defect in self.parent.defects:
                if defect.visible(self.offset_x, self.offset_y, self.L, self.W):
                    yield defect.offset(-self.offset_x, -self.offset_y)

    def source_defects(self, offset_x: float, offset_y: float) -> Iterable[Defect]:
        for defect in self.defects:
            yield defect.offset(offset_x, offset_y)

    def add_cut(
        self,
        op: str,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        label: str = "",
        lx: float = 0,
        ly: float = 0,
    ):
        self.cuts.append((op, x1, y1, x2, y2, label, lx, ly))
        if self.parent:
            self.parent.add_cut(
                op,
                x1 + self.offset_x,
                y1 + self.offset_y,
                x2 + self.offset_x,
                y2 + self.offset_y,
                label,
                lx + self.offset_x,
                ly + self.offset_y,
            )

    def cut(self, length: float, kerf: float = 5):
        self.add_cut("cut", length, 0, length + kerf, self.W)
        return [
            Board(length, self.W, self.T, self, 0, 0),
            Board(self.L - length - kerf, self.W, self.T, self, length + kerf, 0),
        ]

    def rip(self, width: float, kerf: float = 5):
        self.add_cut("rip", 0, width, self.L, width + kerf)
        return [
            Board(self.L, width, self.T, self, 0, 0),
            Board(self.L, self.W - width - kerf, self.T, self, 0, width + kerf),
        ]

    def waste(self):
        self.add_cut("waste", 0, 0, self.L, self.W)
        return []

    def cut_waste(self, length: float):
        self.add_cut("cut_waste", 0, 0, length, self.W)
        return [
            Board(self.L - length, self.W, self.T, self, length, 0),
        ]

    @property
    def profile(self) -> List[Tuple[float, float]]:
        return self._profile or [
            (0, 0),
            (self.L, 0),
            (self.L, self.T),
            (0, self.T),
        ]

    def mitre(self, left: float, right: float) -> List["Board"]:
        self._profile = self.profile

        # offset the point of rotation
        # length is base + hypotenuse of 60 degree triangle with height equal to the
        # board thickness
        hyp = self.T / sin(radians(left))
        offset_x = hyp * cos(radians(left))
        x1, y1 = self._profile[0]
        self._profile[0] = (x1 + offset_x, y1)

        hyp = self.T / sin(radians(right))
        offset_x = hyp * cos(radians(right))
        x1, y1 = self._profile[1]
        self._profile[1] = (x1 - offset_x, y1)

        return [self]

    def draw_board(self, canvas: SVGCanvas, x: float, y: float) -> None:
        # to support mitred ends, maybe treat the board as a profile that
        # is extruded along it's width?
        # draw as polylines rather than rectangles

        canvas.rect(x, y, self.L, self.W, "black", stroke_width=1)

        zx = self.T / sqrt(2)
        zy = self.T / sqrt(2)

        canvas.polyline(
            "gray",
            [
                (x, y + self.W),
                (x + zx, y + self.W + zy),
                (x + zx + self.L, y + self.W + zy),
                (x + zx + self.L, y + self.W + zy),
                (x + self.L, y + self.W),
            ],
            stroke_dasharray="",
        )
        canvas.polyline(
            "gray",
            [
                (x + self.L, y),
                (x + self.L + zx, y + zy),
                (x + self.L + zx, y + self.W + zy),
            ],
            stroke_dasharray="",
        )

        order = 0
        for op, x1, y1, x2, y2, label, lx, ly in self.cuts:
            if op:
                if op == "cut":
                    colour = "green"
                    fill = "rgba(0,255,0,0.25)"
                elif op == "rip":
                    colour = "blue"
                    fill = "rgba(0,0,255,0.25)"
                else:
                    colour = "rgba(255,0,0,0.25)"
                    fill = "rgba(255,0,0,0.25)"

                canvas.rect(
                    x + x1,
                    y + y1,
                    x2 - x1 + 1,
                    y2 - y1 + 1,
                    colour,
                    fill=fill,
                    stroke_width=1,
                )

                if op != "waste":
                    order += 1
                    canvas.text(
                        x + x1 + 10,
                        y + y1 + 10,
                        "left",
                        content=str(order),
                        style="",
                    )

            if label:
                canvas.text(x + lx, y + ly, "start", content=label, style="")

        if self.label:
            canvas.text(
                x + self.L / 2,
                y + self.W / 2,
                content=self.label,
                style="",
            )

        for defect in self.defects:
            defect.draw(canvas, x, y)

    def draw_plan(
        self,
        canvas: SVGCanvas,
        x: float,
        y: float,
        angle: float,
        colour: str = "black",
    ) -> Tuple[float, float]:
        offset_x, offset_y = self.profile[0]
        points = [(x1 - offset_x, y1 - offset_y) for (x1, y1) in self.profile]
        cos_a = cos(radians(angle))
        sin_a = sin(radians(angle))
        rotated = [
            (
                x + x1 * cos_a - y1 * sin_a,
                y + x1 * sin_a + y1 * cos_a,
            )
            for (x1, y1) in points
        ]
        canvas.polyline(
            colour, rotated, stroke_width=1, stroke_dasharray="", closed=True
        )
        return rotated[1]


def draw_boards(canvas: SVGCanvas, x: float, y: float, boards: list[Board]) -> None:
    for board in boards:
        board.draw_board(canvas, x, y)
        y += board.W + 2 * board.T


def cut(length: float, kerf: float = 5):
    def operation(board: Board):
        return board.cut(length, kerf)

    return operation


def rip(width: float, kerf: float = 5):
    def operation(board: Board):
        return board.rip(width, kerf)

    return operation


def mitre(left: float, right: float):
    def operation(board: Board):
        return board.mitre(left, right)

    return operation


def waste(board: Board):
    return board.waste()


def cut_waste(length: float):
    def operation(board: Board):
        return board.cut_waste(length)

    return operation


def joint(*boards: Board, label: str = ""):
    if not all(
        board1.L == board2.L and board1.T == board2.T
        for board1, board2 in zip(boards, boards[1:])
    ):
        raise ValueError("Board length and thickness must match to be joined")

    defects: List[Defect] = []
    offset_y = 0.0
    for board in boards:
        defects.extend(board.source_defects(0, offset_y))
        offset_y += board.W

    return Board(
        boards[0].L,
        sum(board.W for board in boards),
        boards[0].T,
        label=label,
        _defects=defects,
    )


def process(*operations):
    def inner(board: Board):
        result = [board]
        for operation in operations:
            board = result.pop()
            result.extend(operation(board))
        return result

    return inner


def process_first(*operations):
    def inner(board: Board):
        result, remainder = process(operations[0])(board)
        return process(*operations[1:])(result) + [remainder]

    return inner


def process_all(boards: list[Board], *operations):
    result = []
    for board in boards:
        result.extend(process(*operations)(board))
    return result


def joint2(boards: list[Board], *indexes: int, label: str = ""):
    if len(indexes) < 2:
        raise ValueError("Need 2 or more boards to join")
    if not all(index2 > index1 for index1, index2 in zip(indexes, indexes[1:])):
        raise ValueError("Boards must be joined in order")
    boards2 = []
    for index in reversed(indexes):
        boards2.append(boards.pop(index))
    boards.append(joint(*boards2, label=label))


def label_all(boards: list[Board], *labels):
    for board, label in zip(boards, labels):
        board.label = label
        if board.parent:
            board.parent.add_cut(
                "",
                0,
                0,
                board.L,
                board.W,
                label,
                board.L / 2 + board.offset_x,
                board.W / 2 + board.offset_y,
            )


def cube_net(
    boards: list[Board],
    top: int,
    left: int,
    front: int,
    right: int,
    back: int,
    bottom: int,
):
    all_sides = [top, left, front, right, back, bottom]
    if not len({boards[side].T for side in all_sides}) == 1:
        raise ValueError("Cube sides must have equal thickness")

    if not boards[top].L == boards[front].L == boards[bottom].L == boards[back].L:
        raise ValueError("Cube top, front, bottom and back must be the same length")
    if not boards[top].W == boards[left].L == boards[bottom].W == boards[right].L:
        raise ValueError("Cube top, bottom width must match left and right length")
    if not boards[left].W == boards[front].W == boards[right].W == boards[back].W:
        raise ValueError("Cube left, front, right and back must be the same width")

    if not boards[top].label == "top":
        raise ValueError(f"top label invalid: {boards[top].label}")
    if not boards[left].label == "left":
        raise ValueError(f"left label invalid: {boards[left].label}")
    if not boards[front].label == "front":
        raise ValueError(f"front label invalid: {boards[front].label}")
    if not boards[right].label == "right":
        raise ValueError(f"right label invalid: {boards[right].label}")
    if not boards[back].label == "back":
        raise ValueError(f"back label invalid: {boards[back].label}")
    if not boards[bottom].label == "bottom":
        raise ValueError(f"bottom label invalid: {boards[bottom].label}")

    area = sum(boards[side].area for side in all_sides)
    volume = boards[top].area * boards[front].W
    print(
        f"cube {boards[top].L :.1f} x {boards[top].W :.1f} x {boards[front].W :.1f} "
        f"area = {area / 100 :.2f} volume = {volume / 1000 :.2f} "
        f"aspect = {boards[top].aspect :.2f}"
    )

    return Board(boards[top].L, boards[top].W, boards[front].W)
