# ruff: noqa: F401
import sys

from woodwork_cad.board import Board
from woodwork_cad.operations import (
    cut,
    cut_waste,
    draw_boards,
    joint,
    label_all,
    process,
    process_all,
    process_first,
    rip,
    waste,
)
from woodwork_cad.svg import PrintToSVGFiles


def draw_art_tote() -> None:
    print_svg = PrintToSVGFiles("art_tote")

    print("""
# Art supply tote box

## References

John Zhu scrap bin challenge toolbox

![John Zhu toolbox](images/art_tote/john-zhu-toolbox.jpg)

https://youtu.be/pxa88seXsNc?si=2QYJmRWRqUD6E20g&t=567


![paint tube measurements from sue](images/art_tote/paint-tube-measurements-from-sue.jpg)

The box is 290 X 180 mm and 55 deep. Two levels would fit all but 5 of my paint tubes.

          """)

    print("""
## Design
- 360 or 400 mm long?
- 200mm wide inside
- 55-60mm deep inside
- can't be too heavy
  - plywood for drawer bottoms
  - solid bottom for base
  - solid lid for box
  - plywood bottom for box

Not sure that the drawer is very useful, wouldn't be long enough for brushes etc.

might be better to have a long shallow(ish) removable till for brushes and small items

          """)
    stock = []

    L_inside = 400.0
    W_inside = 200.0
    D_inside = 100.0
    T = 12.0
    T2 = 8.0
    till_depth = 30
    till_width = W_inside / 2
    box_depth = 60 + 2 * T2

    ply_board = Board(420, 320, 3)
    stock.append(ply_board)
    ply_board_a = process(cut(L_inside), waste)(ply_board)[0]
    till_bottom, box_bottom = process(rip(till_width), rip(W_inside), waste)(
        ply_board_a
    )

    label_all([till_bottom, box_bottom], "till bottom", "box bottom")

    board1 = Board(830, W_inside + 2 * T, T2)
    stock.append(board1)
    base_bottom, box_lid = process(
        cut(L_inside + 2 * T), cut(L_inside - 2 * T2), waste
    )(board1)

    box_lid = process(rip(W_inside - 2 * T2), waste)(box_lid)[0]

    label_all([base_bottom, box_lid], "base bottom", "box lid")

    print("## Base")
    print("- 60mm for tubes + 30mm for till + 10mm inset for box --> 100m inside depth")

    board2 = Board(1320, D_inside + T, T)
    stock.append(board2)
    board2.grooves.add(D_inside, 5, 5, face=False)
    base_boards = process(
        cut(L_inside + 2 * T),
        cut(L_inside + 2 * T),
        cut(W_inside + 2 * T),
        cut(W_inside + 2 * T),
        waste,
    )(board2)

    label_all(base_boards, "base front", "base back", "base left", "base right")

    base_boards[0].dovetail_tails(tails=2, base=T, width=15, right=False)
    base_boards[0].dovetail_tails(tails=2, base=T, width=15, right=True)
    base_boards[1].dovetail_tails(tails=2, base=T, width=15, right=False)
    base_boards[1].dovetail_tails(tails=2, base=T, width=15, right=True)
    base_boards[2].dovetail_pins(tails=2, base=T, width=15, right=False)
    base_boards[2].dovetail_pins(tails=2, base=T, width=15, right=True)
    base_boards[3].dovetail_pins(tails=2, base=T, width=15, right=False)
    base_boards[3].dovetail_pins(tails=2, base=T, width=15, right=True)
    base_boards.append(base_bottom)

    with print_svg(550, zoom=2.0) as canvas:
        draw_boards(canvas, 10, 10, base_boards)

    print("## Till")
    print("- 30mm deep, 1/2 width")
    board3 = Board(1320, till_depth, T2)
    stock.append(board3)
    till_boards = process(
        cut(L_inside), cut(L_inside), cut(till_width), cut(till_width), waste
    )(board3)

    label_all(till_boards, "till front", "till back", "till left", "till right")

    till_boards.append(till_bottom)

    till_boards[0].dovetail_tails(tails=1, base=T2, width=5, right=False)
    till_boards[0].dovetail_tails(tails=1, base=T2, width=5, right=True)
    till_boards[1].dovetail_tails(tails=1, base=T2, width=5, right=False)
    till_boards[1].dovetail_tails(tails=1, base=T2, width=5, right=True)
    till_boards[2].dovetail_pins(tails=1, base=T2, width=5, right=False)
    till_boards[2].dovetail_pins(tails=1, base=T2, width=5, right=True)
    till_boards[3].dovetail_pins(tails=1, base=T2, width=5, right=False)
    till_boards[3].dovetail_pins(tails=1, base=T2, width=5, right=True)

    with print_svg(550, zoom=2.0) as canvas:
        draw_boards(canvas, 10, 10, till_boards)

    print("## Handle")
    print("not too high, but has to have room to easily remove box")

    print("## Removable box")
    print("- 60mm deep inside")
    board4 = Board(1320, box_depth, T2)
    stock.append(board4)
    box_boards = process(
        cut(L_inside), cut(L_inside), cut(W_inside), cut(W_inside), waste
    )(board4)

    label_all(box_boards, "box front", "box back", "box left", "box right")

    box_wedge = Board(W_inside, 15, 15, label="wedge")
    stock.append(box_wedge)

    box_boards.extend(
        [
            box_lid,
            box_bottom,
            box_wedge,
        ]
    )

    board5 = Board(W_inside, 150, T2)
    stock.append(board5)

    box_battens = process(rip(30), rip(30), rip(30), rip(30), waste)(board5)
    label_all(box_battens, "bottom brace", "batten", "batten", "batten")

    box_boards.extend(box_battens)

    box_boards[0].dovetail_tails(tails=2, base=T, width=5, right=False)
    box_boards[0].dovetail_tails(tails=2, base=T, width=5, right=True)
    box_boards[1].dovetail_tails(tails=2, base=T, width=5, right=False)
    box_boards[1].dovetail_tails(tails=2, base=T, width=5, right=True)
    box_boards[2].dovetail_pins(tails=2, base=T, width=5, right=False)
    box_boards[2].dovetail_pins(tails=2, base=T, width=5, right=True)
    box_boards[3].dovetail_pins(tails=2, base=T, width=5, right=False)
    box_boards[3].dovetail_pins(tails=2, base=T, width=5, right=True)

    with print_svg(550, zoom=2.0) as canvas:
        draw_boards(canvas, 10, 10, box_boards)

    print("## Stock")

    print("""
- 3 x 790 x 180 x 12 (10mm moulded)

![3 x 790 x 180 x 12](images/art_tote/3x790x180x12.jpg)

- 3 x 740 x 135 x 15 (excluding groove)

![3 x 740 x 135 x 15](images/art_tote/3x740x135x15.jpg)

- 2 x 390 x 185 x 15 (10mm mouldings)
- 3 x 400 x 165 x 19 (20mm bevels)
- 1 x 750 x 45 x 12
- 2 x 720 x 65 x 19 (60x8 mortice at 150,10)

![other-stock-1](images/art_tote/other-stock-1.jpg)

          """)

    raw_stock = [
        Board(790, 180, 12),
        # Board(790, 180, 12),
        # Board(790, 180, 12),
        Board(740, 135, 15),
        # Board(740, 135, 15),
        # Board(740, 135, 15),
        Board(400, 165, 19),
        # Board(400, 165, 19),
        # Board(400, 165, 19),
        Board(390, 185, 15),
        # Board(390, 185, 15),
        Board(720, 65, 19),
        # Board(720, 65, 19),
        Board(750, 45, 12),
    ]

    with print_svg(1000) as canvas:
        draw_boards(canvas, 10, 10, raw_stock)
        draw_boards(canvas, 30, 30, raw_stock[:5])
        draw_boards(canvas, 50, 50, raw_stock[:3])

    print("## Cut list")
    with print_svg(1400) as canvas:
        draw_boards(canvas, 10, 10, stock)


if __name__ == "__main__":
    draw_art_tote()
