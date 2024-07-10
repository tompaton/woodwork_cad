from typing import Any, List

from .board import Board
from .defects import Defects
from .geometry import Point, Point3d, Points, to2d
from .shades import Shades
from .svg import SVGCanvas


def draw_boards(
    canvas: SVGCanvas,
    x: float,
    y: float,
    boards: list[Board],
    dimension_cuts: bool = False,
) -> Points:
    points = []
    for board in boards:
        board.draw_board(canvas, x, y)
        points.append(Point(x, y))
        if dimension_cuts:
            y += board.draw_cut_dimensions(canvas, x, y)
        y += board.W + to2d(Point3d(0, 0, board.T)).y + 20
    return points


def draw_dimension(
    canvas: SVGCanvas,
    x: float,
    y: float,
    board: Board,
    dimension: str,
    position: str,
    pad: float = 10,
) -> None:
    start, end, arrow_start, arrow_end, text = board.get_dimension(
        dimension, position, pad
    )
    draw_dimension_ex(
        canvas, x, y, start, end, arrow_start, arrow_end, text, dimension, position
    )


def draw_dimension_ex(
    canvas: SVGCanvas,
    x: float,
    y: float,
    start: Point3d,
    end: Point3d,
    arrow_start: Point3d,
    arrow_end: Point3d,
    text: str,
    dimension: str,
    position: str,
) -> None:
    if dimension == "W":
        canvas.vertical_arrow(
            x,
            y,
            start,
            end,
            arrow_start,
            arrow_end,
            text,
            left=position == "left",
        )

    elif dimension == "L":
        canvas.horizontal_arrow(x, y, start, end, arrow_start, arrow_end, text)

    elif dimension == "T":
        canvas.horizontal_arrow(x, y, start, end, arrow_start, arrow_end, text)

    else:
        msg = f"Unsupported {dimension=} and {position=}"
        raise ValueError(msg)


def cut(length: float, kerf: float = 5, label: str = ""):
    def operation(board: Board):
        return label_all(board.cut(length, kerf), label)

    return operation


def rip(width: float, kerf: float = 5, label: str = ""):
    def operation(board: Board):
        return label_all(board.rip(width, kerf), label)

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

    defects = Defects()
    shade = Shades()
    offset_y = 0.0
    for board in boards:
        defects.extend(board.defects.select(0, offset_y))
        shade.extend(board.shades.select(0, board.W, offset_y))
        offset_y += board.W

    return Board(
        boards[0].L,
        sum(board.W for board in boards),
        boards[0].T,
        label=label,
        _defects=defects,
        shades=shade,
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
        if label:
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
    return boards


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


def dovetail_boards(sides: List[Board], ends: List[Board], **kwargs: Any) -> None:
    for side in sides:
        side.dovetail_tails(base=ends[0].T, right=False, **kwargs)
        side.dovetail_tails(base=ends[0].T, right=True, **kwargs)

    for end in ends:
        end.dovetail_pins(base=sides[0].T, right=False, **kwargs)
        end.dovetail_pins(base=sides[0].T, right=True, **kwargs)
