from decimal import Decimal

from woodwork_cad.board import (
    ZERO,
    Board,
    cube_net,
    cut,
    draw_boards,
    joint2,
    label_all,
    process,
    process_all,
    process_first,
    rip,
    waste,
)
from woodwork_cad.svg import SVGCanvas


def box1(boxL, boxW, boxH):
    L = Decimal(550)
    W = Decimal(100)
    board1 = Board(L, W, Decimal(20))
    board2 = Board(L, W, Decimal(8))
    board3 = Board(L, W, Decimal(8))

    groove_depth = Decimal(5)
    extra = Decimal(2) * (board1.T - groove_depth)

    # width = board1.T
    kerf = Decimal(5)
    width = (board1.W - Decimal(5) * kerf) / Decimal(6)
    print(f"sticks {width :.1f} x {board1.T :.1f}")
    sticks = process(rip(width), rip(width), rip(width), rip(width))(board1)
    sticks2 = process(rip(width), rip(width), waste)(sticks.pop())

    stickL = boxL + extra
    stickW = boxW + extra
    stickH = boxH + extra

    frame = process_all(sticks, cut(stickL), cut(stickW), cut(stickH), waste)
    frame.extend(process_all(sticks2, cut(stickL), cut(stickW), waste))

    label_all(
        frame,
        "top-back",
        "left-bottom",
        "left-back",
        "top-front",
        "left-top",
        "left-front",
        "bottom-front",
        "right-top",
        "right-front",
        "bottom-back",
        "right-bottom",
        "right-back",
        "lid-back",
        "lid-left",
        "lid-front",
        "lid-right",
    )

    panels = process_all(
        [board2, board3],
        process_first(cut(boxW, kerf=ZERO), rip(boxH), waste),
        process_first(cut(boxL, kerf=ZERO), rip(boxH, kerf=ZERO)),
        cut(boxL, kerf=ZERO),
        waste,
    )

    label_all(
        panels, "left", "front", "top2", "top1", "right", "back", "bottom2", "bottom1"
    )

    joint2(panels, 6, 7, "top")
    joint2(panels, 2, 3, "bottom")

    return board1, board2, board3, frame, panels


def build_box(box, net):
    board1, board2, board3, frame2, panels2 = box

    cube = cube_net(panels2, *net)

    canvas = SVGCanvas()

    with canvas.document(1400, (0, 0, 1400, 1000)):
        draw_boards(canvas, 10, 10, frame2)
        draw_boards(canvas, 400, 10, panels2)

        board1.draw_board(canvas, 700, 20)
        board2.draw_board(canvas, 700, 170)
        board3.draw_board(canvas, 700, 300)

        cube.draw_board(canvas, 700, 500)

    return canvas.result


def box1_dimensions(boxH):
    boxW = Decimal(200) - boxH
    boxL = (Decimal(550) - boxW) / 2
    return (boxL, boxW, boxH)


def draw_box1(boxH=Decimal(55)):
    boxL, boxW, boxH = box1_dimensions(boxH)
    print("# Framed box\n")
    print(f"{boxL} x {boxW} x {boxH}")
    box_svg = build_box(box1(boxL, boxW, boxH), [4, 0, 1, 2, 3, 5])
    print("\n")
    print(box_svg)


if __name__ == "__main__":
    draw_box1()
