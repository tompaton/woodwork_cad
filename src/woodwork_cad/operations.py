from itertools import pairwise
from typing import Any

from woodwork_cad.board import Board
from woodwork_cad.defects import Defects
from woodwork_cad.geometry import Point, Point3d, Points, to2d
from woodwork_cad.shades import Shades
from woodwork_cad.svg import SVGCanvas


def draw_boards(
    canvas: SVGCanvas,
    x: float,
    y: float,
    boards: list[Board],
    *,
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
    start, end, arrow_start, arrow_end, text = board.get_dimension(dimension, position, pad)
    draw_dimension_ex(canvas, x, y, start, end, arrow_start, arrow_end, text, dimension, position)


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

    elif dimension in {"L", "T"}:
        canvas.horizontal_arrow(x, y, start, end, arrow_start, arrow_end, text)

    else:
        msg = f"Unsupported {dimension=} and {position=}"
        raise ValueError(msg)


def cut(length: float, kerf: float = 5, label: str = "", angle: float = 90):
    def operation(board: Board):
        return label_all(board.cut(length, kerf, angle), label)

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
        # round(board1.profile.length2()[1]) == round(board2.profile.length2()[0])
        board1.L == board2.L and board1.T == board2.T
        for board1, board2 in pairwise(boards)
    ):
        msg = "Board length and thickness must match to be joined"
        raise ValueError(msg)

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
        return [*process(*operations[1:])(result), remainder]

    return inner


def process_all(boards: list[Board], *operations):
    result = []
    for board in boards:
        result.extend(process(*operations)(board))
    return result


def joint2(boards: list[Board], *indexes: int, label: str = ""):
    if len(indexes) < 2:
        msg = "Need 2 or more boards to join"
        raise ValueError(msg)
    if not all(index2 > index1 for index1, index2 in pairwise(indexes)):
        msg = "Boards must be joined in order"
        raise ValueError(msg)
    boards2 = [boards.pop(index) for index in reversed(indexes)]
    boards.append(joint(*boards2, label=label))


def label_all(boards: list[Board], *labels):
    for board, label in zip(boards, labels, strict=False):
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
    if len({boards[side].T for side in all_sides}) != 1:
        msg = "Cube sides must have equal thickness"
        raise ValueError(msg)

    if not boards[top].L == boards[front].L == boards[bottom].L == boards[back].L:
        msg = "Cube top, front, bottom and back must be the same length"
        raise ValueError(msg)
    if not boards[top].W == boards[left].L == boards[bottom].W == boards[right].L:
        msg = "Cube top, bottom width must match left and right length"
        raise ValueError(msg)
    if not boards[left].W == boards[front].W == boards[right].W == boards[back].W:
        msg = "Cube left, front, right and back must be the same width"
        raise ValueError(msg)

    if boards[top].label != "top":
        msg = f"top label invalid: {boards[top].label}"
        raise ValueError(msg)

    if boards[left].label != "left":
        msg = f"left label invalid: {boards[left].label}"
        raise ValueError(msg)

    if boards[front].label != "front":
        msg = f"front label invalid: {boards[front].label}"
        raise ValueError(msg)

    if boards[right].label != "right":
        msg = f"right label invalid: {boards[right].label}"
        raise ValueError(msg)

    if boards[back].label != "back":
        msg = f"back label invalid: {boards[back].label}"
        raise ValueError(msg)

    if boards[bottom].label != "bottom":
        msg = f"bottom label invalid: {boards[bottom].label}"
        raise ValueError(msg)

    area = sum(boards[side].area for side in all_sides)
    volume = boards[top].area * boards[front].W
    print(  # noqa
        f"cube {boards[top].L :.1f} x {boards[top].W :.1f} x {boards[front].W :.1f} "
        f"area = {area / 100 :.2f} volume = {volume / 1000 :.2f} "
        f"aspect = {boards[top].aspect :.2f}"
    )

    return Board(boards[top].L, boards[top].W, boards[front].W)


def dovetail_boards(
    sides: list[Board],
    ends: list[Board],
    pin1_ratio: float | None = None,
    **kwargs: Any,
) -> None:
    for side in sides:
        if pin1_ratio is not None:
            side.dovetails.pin1_ratio = pin1_ratio

        side.dovetail_tails(base=ends[0].T, right=False, **kwargs)
        side.dovetail_tails(base=ends[0].T, right=True, **kwargs)

    for end in ends:
        if pin1_ratio is not None:
            end.dovetails.pin1_ratio = pin1_ratio

        end.dovetail_pins(base=sides[0].T, right=False, **kwargs)
        end.dovetail_pins(base=sides[0].T, right=True, **kwargs)
