# ruff: noqa: F401
import sys

from woodwork_cad.board import Board
from woodwork_cad.operations import (
    cut,
    cut_waste,
    dovetail_boards,
    draw_boards,
    joint,
    label_all,
    process,
    process_all,
    process_first,
    rip,
    waste,
)
from woodwork_cad.stock import StockPile
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
    pile = StockPile()
    pile.add("a", 3, Board(790, 180, 12))
    pile.add("b", 3, Board(740, 135, 15))
    # pile.add("c", 3, Board(400, 165, 19))
    # pile.add("d", 2, Board(390, 185, 15))
    # pile.add("e", 2, Board(720, 65, 19))
    # pile.add("f", 1, Board(750, 45, 12))
    pile.add("ply", 1, Board(420, 320, 3))
    pile.add("stick", 1, Board(400, 15, 15))

    L_inside = 400.0
    W_inside = 200.0
    D_inside = 100.0
    T = 12.0
    T2 = 8.0
    till_depth = 30
    till_width = W_inside / 2
    box_depth = 60 + 2 * T2

    ply_board_a = process(cut(L_inside), waste)(pile.take("ply"))[0]
    till_bottom, box_bottom = process(rip(till_width), rip(W_inside), waste)(
        ply_board_a
    )

    label_all([till_bottom, box_bottom], "till bottom", "box bottom")

    board_b1_1 = pile.take_part("b", cut(L_inside - 2 * T), "b2")
    board_b2_1 = pile.take_part("b", cut(L_inside - 2 * T), "b2")

    label_all([board_b1_1, board_b2_1], "box lid a", "box lid b")
    board_j1 = joint(board_b1_1, board_b2_1)

    board_b3_1 = pile.take_part("b", cut(L_inside), "b3")
    till_front, till_back, till_ends, board_b3_4a = process(
        rip(till_depth), rip(till_depth), rip(till_depth)
    )(board_b3_1)
    board_b3_4 = process(cut(W_inside + 2 * T2), waste)(board_b3_4a)[0]
    label_all([board_b3_4], "base bottom d")

    till_left, till_right = process(cut(till_width), cut(till_width), waste)(till_ends)

    till_boards = [till_front, till_right, till_back, till_left]
    label_all(till_boards, "till front", "till right", "till back", "till left")

    till_boards.append(till_bottom)

    board_b1_2 = pile.take_part("b2", cut(W_inside + 2 * T2), "b4")
    board_b2_2 = pile.take_part("b2", cut(W_inside + 2 * T2), "b4")
    board_b3_2 = pile.take_part("b3", cut(W_inside + 2 * T2), "b5")

    label_all(
        [board_b1_2, board_b2_2, board_b3_2],
        "base bottom a",
        "base bottom b",
        "base bottom c",
    )
    board_j2 = joint(board_b1_2, board_b2_2, board_b3_2, board_b3_4)

    box_lid = process(rip(W_inside - 2 * T2), waste)(board_j1)[0]

    base_bottom = process(rip(L_inside + 2 * T2), waste)(board_j2)[0]

    label_all([base_bottom, box_lid], "base bottom", "box lid")

    print("## Base")
    print("- 60mm for tubes + 30mm for till + 10mm inset for box --> 100m inside depth")

    board_a1_1 = pile.take_part("a", rip(D_inside + T), "a2")
    board_a2_1 = pile.take_part("a", rip(D_inside + T), "a2")

    board_a1_1.grooves.add(D_inside, 5, 5, face=False)
    board_a2_1.grooves.add(D_inside, 5, 5, face=False)
    base_boards = process(cut(L_inside + 2 * T), cut(W_inside + 2 * T), waste)(
        board_a1_1
    ) + process(
        cut(L_inside + 2 * T),
        cut(W_inside + 2 * T),
        waste,
    )(board_a2_1)

    label_all(base_boards, "base front", "base left", "base back", "base right")

    dovetail_boards(base_boards[0:4:2], base_boards[1:4:2], tails=2, width=15)

    base_boards.append(base_bottom)

    with print_svg(550, zoom=2.0) as canvas:
        draw_boards(canvas, 10, 10, base_boards)

    print("## Till")
    print("- 30mm deep, 1/2 width")

    dovetail_boards(till_boards[0:4:2], till_boards[1:4:2], tails=1, width=5)

    with print_svg(550, zoom=2.0) as canvas:
        draw_boards(canvas, 10, 10, till_boards)

    print("## Handle")
    print("not too high, but has to have room to easily remove box")

    print("## Removable box")
    print("- 60mm deep inside")

    board_a3_1, board_a3_2 = process(rip(box_depth), rip(box_depth), waste)(
        pile.take("a")
    )

    box_boards = process(cut(L_inside), cut(W_inside), waste)(board_a3_1) + process(
        cut(L_inside), cut(W_inside), waste
    )(board_a3_2)

    label_all(box_boards, "box front", "box left", "box back", "box right")

    box_wedge = process(cut(W_inside), waste)(pile.take("stick"))[0]
    label_all([box_wedge], "wedge")

    box_boards.extend(
        [
            box_lid,
            box_bottom,
            box_wedge,
        ]
    )

    board_a1_2 = pile.take_part("a2", rip(30), "a3")
    box_battens = process(cut(W_inside), cut(W_inside), cut(W_inside), waste)(
        board_a1_2
    )
    label_all(box_battens, "batten", "batten", "batten")
    box_boards.extend(box_battens)

    board_a2_2 = pile.take_part("a2", rip(30), "a3")
    box_brace = process(cut(W_inside), waste)(board_a2_2)[0]
    label_all([box_brace], "bottom brace")
    box_boards.append(box_brace)

    dovetail_boards(box_boards[0:4:2], box_boards[1:4:2], tails=2, width=5)

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

    with print_svg(1000) as canvas:
        pile.draw(canvas, 10, 10)

    print("## Cut list")
    pile.mark_waste()
    with print_svg(1400) as canvas:
        draw_boards(canvas, 10, 10, pile.cutlist)

    print("## Jointing")
    with print_svg(1000) as canvas:
        draw_boards(canvas, 10, 10, [board_j1, board_j2])

    print("## Dimensions")
    print("- base")
    for board in base_boards:
        print(f"  - {board}")
    print("- box")
    for board in box_boards:
        print(f"  - {board}")
    print("- till")
    for board in till_boards:
        print(f"  - {board}")

    print("## Plan view")

    # corners: Points = []
    with print_svg(550, zoom=2) as canvas:
        x, y, angle = 10, 10, 0
        for side in base_boards[:4]:
            x, y = side.draw_plan(canvas, x, y, angle)
            # corners.append((x, y))
            angle += 90
            canvas.circle(x, y, 2, "red")

        x, y, angle = 10 + base_boards[3].T, 10 + base_boards[0].T, 0
        for side in box_boards[:4]:
            x, y = side.draw_plan(canvas, x, y, angle)
            # corners.append((x, y))
            angle += 90
            canvas.circle(x, y, 2, "red")

        x, y, angle = 10 + base_boards[3].T, 10 + base_boards[0].T, 0
        for side in till_boards[:4]:
            x, y = side.draw_plan(canvas, x, y, angle)
            # corners.append((x, y))
            angle += 90
            canvas.circle(x, y, 2, "red")

    print("## Base assembly")
    angle, mate = 0, (0, 0, 0)
    base_faces: list = []
    for side in base_boards[:4]:
        # need to collect together all rotate faces, then sort, then draw
        mate = side.rotated_faces(rotate_y=angle, offset=mate, faces=base_faces)[1]
        angle += 90

    with print_svg(800, zoom=2) as canvas:
        for face in sorted(base_faces):
            face.draw(canvas, 20, 20)

    print("## Till assembly")
    angle, mate = 0, (0, 0, 0)
    till_faces: list = []
    for side in till_boards[:4]:
        # need to collect together all rotate faces, then sort, then draw
        mate = side.rotated_faces(rotate_y=angle, offset=mate, faces=till_faces)[1]
        angle += 90

    with print_svg(800, zoom=2) as canvas:
        for face in sorted(till_faces):
            face.draw(canvas, 20, 20)

    print("## Box assembly")
    angle, mate = 0, (0, 0, 0)
    box_faces: list = []
    for side in box_boards[:4]:
        # need to collect together all rotate faces, then sort, then draw
        mate = side.rotated_faces(rotate_y=angle, offset=mate, faces=box_faces)[1]
        angle += 90

    with print_svg(800, zoom=2) as canvas:
        for face in sorted(box_faces):
            face.draw(canvas, 20, 20)


if __name__ == "__main__":
    draw_art_tote()
