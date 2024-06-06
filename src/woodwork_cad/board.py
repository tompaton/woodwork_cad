from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional, Tuple

from .svg import SVGCanvas

__all__ = [
    "Board",
    "draw_boards",
    "cut",
    "rip",
    "waste",
    "process",
    "process_all",
    "process_first",
    "joint2",
    "label_all",
    "cube_net",
]

ZERO = Decimal(0)


@dataclass
class Board:
    L: Decimal
    W: Decimal
    T: Decimal

    parent: Optional["Board"] = None
    offset_x: Decimal = ZERO
    offset_y: Decimal = ZERO

    cuts: list[
        tuple[str, Decimal, Decimal, Decimal, Decimal, str, Decimal, Decimal]
    ] = field(default_factory=list)

    label: str = ""

    @property
    def area(self):
        return self.L * self.W

    @property
    def aspect(self):
        return self.L / self.W

    def add_cut(
        self,
        op: str,
        x1: Decimal,
        y1: Decimal,
        x2: Decimal,
        y2: Decimal,
        label: str = "",
        lx: Decimal = ZERO,
        ly: Decimal = ZERO,
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

    def cut(self, length: Decimal, kerf: Decimal = Decimal(5)):
        self.add_cut("cut", length, ZERO, length + kerf, self.W)
        return [
            Board(length, self.W, self.T, self, ZERO, ZERO),
            Board(self.L - length - kerf, self.W, self.T, self, length + kerf, ZERO),
        ]

    def rip(self, width: Decimal, kerf: Decimal = Decimal(5)):
        self.add_cut("rip", ZERO, width, self.L, width + kerf)
        return [
            Board(self.L, width, self.T, self, ZERO, ZERO),
            Board(self.L, self.W - width - kerf, self.T, self, ZERO, width + kerf),
        ]

    def waste(self):
        self.add_cut("waste", ZERO, ZERO, self.L, self.W)
        return []

    def draw_board(self, canvas: SVGCanvas, x: Decimal, y: Decimal) -> None:
        canvas.rect(
            float(x), float(y), float(self.L), float(self.W), "black", stroke_width=1
        )

        zx = self.T / Decimal(2).sqrt()
        zy = self.T / Decimal(2).sqrt()

        canvas.polyline(
            "gray",
            float_points(
                [
                    (x, y + self.W),
                    (x + zx, y + self.W + zy),
                    (x + zx + self.L, y + self.W + zy),
                    (x + zx + self.L, y + self.W + zy),
                    (x + self.L, y + self.W),
                ]
            ),
            stroke_dasharray="",
        )
        canvas.polyline(
            "gray",
            float_points(
                [
                    (x + self.L, y),
                    (x + self.L + zx, y + zy),
                    (x + self.L + zx, y + self.W + zy),
                ]
            ),
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
                    float(x + x1),
                    float(y + y1),
                    float(x2 - x1) + 1,
                    float(y2 - y1) + 1,
                    colour,
                    fill=fill,
                    stroke_width=1,
                )

                if op != "waste":
                    order += 1
                    canvas.text(
                        float(x + x1) + 10,
                        float(y + y1) + 10,
                        "left",
                        content=str(order),
                        style="",
                    )

            if label:
                canvas.text(
                    float(x + lx), float(y + ly), "start", content=label, style=""
                )

        if self.label:
            canvas.text(
                float(x + self.L / Decimal(2)),
                float(y + self.W / Decimal(2)),
                content=self.label,
                style="",
            )


def float_points(points: List[Tuple[Decimal, Decimal]]) -> List[Tuple[float, float]]:
    return [(float(x), float(y)) for x, y in points]


def draw_boards(canvas: SVGCanvas, x: Decimal, y: Decimal, boards: list[Board]) -> None:
    for board in boards:
        board.draw_board(canvas, x, y)
        y += board.W + 2 * board.T


def cut(length: Decimal, kerf: Decimal = Decimal(5)):
    def operation(board: Board):
        return board.cut(length, kerf)

    return operation


def rip(width: Decimal, kerf: Decimal = Decimal(5)):
    def operation(board: Board):
        return board.rip(width, kerf)

    return operation


def waste(board: Board):
    return board.waste()


def joint(board1: Board, board2: Board, label: str = ""):
    assert board1.L == board2.L
    assert board1.T == board2.T
    return Board(board1.L, board1.W + board2.W, board1.T, label=label)


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


def joint2(boards: list[Board], index1: int, index2: int, label: str = ""):
    assert index2 > index1
    board2 = boards.pop(index2)
    board1 = boards.pop(index1)
    boards.append(joint(board1, board2, label))


def label_all(boards: list[Board], *labels):
    for board, label in zip(boards, labels):
        board.label = label
        if board.parent:
            board.parent.add_cut(
                "",
                ZERO,
                ZERO,
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
    assert len({boards[side].T for side in all_sides}) == 1

    assert boards[top].L == boards[front].L == boards[bottom].L == boards[back].L
    assert boards[top].W == boards[left].L == boards[bottom].W == boards[right].L
    assert boards[left].W == boards[front].W == boards[right].W == boards[back].W

    assert boards[top].label == "top"
    assert boards[left].label == "left"
    assert boards[front].label == "front"
    assert boards[right].label == "right"
    assert boards[back].label == "back"
    assert boards[bottom].label == "bottom"

    area = sum(boards[side].area for side in all_sides)
    volume = boards[top].area * boards[front].W
    print(
        f"cube {boards[top].L :.1f} x {boards[top].W :.1f} x {boards[front].W :.1f} "
        f"area = {area / 100 :.2f} volume = {volume / 1000 :.2f} "
        f"aspect = {boards[top].aspect :.2f}"
    )

    return Board(boards[top].L, boards[top].W, boards[front].W)
