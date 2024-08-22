from woodwork_cad.board import Board
from woodwork_cad.operations import (
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
from woodwork_cad.svg import PrintToSVGFiles


def box1(boxL, boxW, boxH):
    L = 550
    W = 100
    board1 = Board(L, W, 20)
    board2 = Board(L, W, 8)
    board3 = Board(L, W, 8)

    groove_depth = 5
    extra = 2 * (board1.T - groove_depth)

    # width = board1.T
    kerf = 5
    width = (board1.W - 5 * kerf) / 6
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
        process_first(cut(boxW, kerf=0), rip(boxH), waste),
        process_first(cut(boxL, kerf=0), rip(boxH, kerf=0)),
        cut(boxL, kerf=0),
        waste,
    )

    label_all(panels, "left", "front", "top2", "top1", "right", "back", "bottom2", "bottom1")

    joint2(panels, 6, 7, label="top")
    joint2(panels, 2, 3, label="bottom")

    return board1, board2, board3, frame, panels


def box1_dimensions(boxH):
    boxW = 200 - boxH
    boxL = (550 - boxW) / 2
    return (boxL, boxW, boxH)


def draw_box1(boxH=55):
    boxL, boxW, boxH = box1_dimensions(boxH)

    print_svg = PrintToSVGFiles("box1")

    print("# Framed box\n")
    print(f"{boxL} x {boxW} x {boxH}")

    # TODO: add dimensions etc.

    board1, board2, board3, frame2, panels2 = box1(boxL, boxW, boxH)

    net = [4, 0, 1, 2, 3, 5]
    cube = cube_net(panels2, *net)

    print("## Frame")
    with print_svg(1000) as canvas:
        board1.draw_board(canvas, 10, 20)

        draw_boards(canvas, 10, 170, frame2)

    print("## Panels")
    with print_svg(1000) as canvas:
        board2.draw_board(canvas, 10, 20)
        board3.draw_board(canvas, 10, 170)

        draw_boards(canvas, 10, 300, panels2)

    print("## Final box")
    with print_svg(1000) as canvas:
        cube.draw_board(canvas, 10, 10)


if __name__ == "__main__":
    draw_box1()
