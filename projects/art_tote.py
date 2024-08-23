# ruff: noqa: F401
import sys

from woodwork_cad.assembly import Assembly, Dimension
from woodwork_cad.board import Board, Size
from woodwork_cad.geometry import Vector3d
from woodwork_cad.operations import (
    cut,
    cut_waste,
    dovetail_boards,
    draw_boards,
    draw_dimension,
    joint,
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
## Notes
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
    Ta = 12.0
    Tb = 15.0

    s_inside = Size(400.0, 200.0, 100.0)
    s_base = s_inside.expand(Ta * 2, Ta * 2, Ta)
    s_box = Size(s_inside.length, s_inside.width, 60 + 2 * Ta)
    s_box_lid = s_box.contract(2 * Ta, 2 * Ta)
    s_till = Size(s_inside.length, s_inside.width / 2, 30)

    pile = StockPile()
    pile.add("a", 3, Board(790, 180, Ta))
    pile.add("b", 3, Board(740, 135, Tb))
    # unused boards
    # pile.add("c", 3, Board(400, 165, 19))
    # pile.add("d", 2, Board(390, 185, 15))
    # pile.add("e", 2, Board(720, 65, 19))
    # pile.add("f", 1, Board(750, 45, 12))
    pile.add("ply", 1, Board(420, 320, 3))
    pile.add("stick", 1, Board(400, 15, 15))

    ply_board_a = process(cut(s_inside.length), waste)(pile.take("ply"))[0]
    till_bottom, box_bottom = process(
        rip(s_till.width, label="till bottom"),
        rip(s_inside.width, label="box bottom"),
        waste,
    )(ply_board_a)

    board_j1 = joint(
        pile.take_part("b", cut(s_box_lid.length, label="box lid a"), "b2"),
        pile.take_part("b", cut(s_box_lid.length, label="box lid b"), "b2"),
    )
    box_lid = process(rip(s_box_lid.width, label="box lid"), waste)(board_j1)[0]

    till_front, till_back, till_ends, board_j2_4a = process(
        rip(s_till.depth, label="till front"),
        rip(s_till.depth, label="till back"),
        rip(s_till.depth),
    )(pile.take_part("b", cut(s_inside.length), "b3"))
    board_j2_4 = process(cut(s_base.width, label="base bottom d"), waste)(board_j2_4a)[
        0
    ]

    till_left, till_right = process(
        cut(s_till.width, label="till left"),
        cut(s_till.width, label="till right"),
        waste,
    )(till_ends)

    till_boards = [till_front, till_right, till_back, till_left, till_bottom]

    board_j2_1 = pile.take_part("b2", cut(s_base.width, label="base bottom a"), "b4")
    board_j2_2 = pile.take_part("b2", cut(s_base.width, label="base bottom b"), "b4")
    board_j2_3 = pile.take_part("b3", cut(s_base.width, label="base bottom c"), "b5")

    board_j2 = joint(board_j2_1, board_j2_2, board_j2_3, board_j2_4)

    print("## Base")
    print("- 60mm for tubes + 30mm for till + 10mm inset for box --> 100m inside depth")
    print("- central divider/stiffener, ~40mm high")

    board_a1_1 = pile.take_part("a", rip(s_base.depth), "a2")
    board_a2_1 = pile.take_part("a", rip(s_base.depth), "a2")

    board_a1_1.grooves.add(s_inside.depth, 5, 5, face=False)
    board_a2_1.grooves.add(s_inside.depth, 5, 5, face=False)
    base_boards = process(
        cut(s_base.length, label="base front"),
        cut(s_base.width, label="base left"),
        waste,
    )(board_a1_1) + process(
        cut(s_base.length, label="base back"),
        cut(s_base.width, label="base right"),
        waste,
    )(board_a2_1)

    dovetail_boards(base_boards[0:4:2], base_boards[1:4:2], tails=2, pin1_ratio=1.0)

    base_boards.append(
        process(rip(s_base.length, label="base bottom"), waste)(board_j2)[0]
    )

    with print_svg(550, zoom=2.0) as canvas:
        draw_boards(canvas, 10, 10, base_boards)

    print("## Till")
    print("- 30mm deep, 1/2 width")
    print("- will sit/ride on small rails set into grooves in base end walls")

    dovetail_boards(till_boards[0:4:2], till_boards[1:4:2], tails=1, pin1_ratio=1.0)

    with print_svg(550, zoom=2.0) as canvas:
        draw_boards(canvas, 10, 10, till_boards)

    print("## Handle")
    print("not too high, but has to have room to easily remove box")

    print("## Removable box")
    print("- 60mm deep inside")
    print("- sits on small rails set into grooves in base font/back walls")

    board_a3_1, board_a3_2 = process(rip(s_box.depth), rip(s_box.depth), waste)(
        pile.take("a")
    )

    box_boards = process(
        cut(s_inside.length, label="box front"),
        cut(s_inside.width, label="box left"),
        waste,
    )(board_a3_1) + process(
        cut(s_inside.length, label="box back"),
        cut(s_inside.width, label="box right"),
        waste,
    )(board_a3_2)

    box_wedge = process(cut(s_inside.width, label="wedge"), waste)(pile.take("stick"))[
        0
    ]

    box_boards.extend(
        [
            box_lid,
            box_bottom,
            box_wedge,
        ]
    )

    board_a1_2 = pile.take_part("a2", rip(30), "a3")
    box_battens = process(
        cut(s_inside.width, label="batten"),
        cut(s_inside.width, label="batten"),
        cut(s_inside.width, label="batten"),
        waste,
    )(board_a1_2)
    box_boards.extend(box_battens)

    board_a2_2 = pile.take_part("a2", rip(30), "a3")
    box_brace = process(cut(s_inside.width, label="bottom brace"), waste)(board_a2_2)[0]
    box_boards.append(box_brace)

    dovetail_boards(box_boards[0:4:2], box_boards[1:4:2], tails=2, pin1_ratio=1.0)

    with print_svg(550, zoom=2.0) as canvas:
        draw_boards(canvas, 10, 10, box_boards)

    print("## Stock")

    print("""
- 3 x 790 x 180 x 12 (10mm moulded)

![3 x 790 x 180 x 12](images/art_tote/3x790x180x12.jpg)

- 3 x 740 x 135 x 15 (excluding groove)

![3 x 740 x 135 x 15](images/art_tote/3x740x135x15.jpg)

- 2 x 390 x 185 x 15 (10mm mouldings) (unused)
- 3 x 400 x 165 x 19 (20mm bevels) (unused)
- 1 x 750 x 45 x 12
- 2 x 720 x 65 x 19 (60x8 mortice at 150,10)

![other-stock-1](images/art_tote/other-stock-1.jpg)

          """)

    with print_svg(1000) as canvas:
        pile.draw(canvas, 20, 10)

    print("## Cut list")
    pile.mark_waste()
    with print_svg(1400) as canvas:
        draw_boards(canvas, 10, 10, pile.cutlist, dimension_cuts=True)

    print("## Jointing")
    with print_svg(1000) as canvas:
        draw_boards(canvas, 10, 10, [board_j1, board_j2], dimension_cuts=True)

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

    base_assembly = Assembly()
    base_assembly.add_walls(90, base_boards[:4])
    base_boards[-1].rotate(rotate_x=90.0)
    base_boards[-1].rotate(rotate_y=90.0)
    base_assembly.add_board(base_boards[-1], Vector3d(0.0, s_inside.depth, 0.0), 0.0)

    till_assembly = Assembly()
    till_assembly.add_walls(90, till_boards[:4])
    till_bottom.rotate(rotate_x=90.0)
    till_assembly.add_board(till_bottom, Vector3d(0.0, s_till.depth, 0.0), 0.0)

    box_assembly = Assembly()
    box_assembly.add_walls(90, box_boards[:4])
    box_bottom.rotate(rotate_x=90.0)
    box_assembly.add_board(box_bottom, Vector3d(0.0, s_box.depth, 0.0), 0.0)
    box_lid.rotate(rotate_x=90.0)
    box_assembly.add_board(
        box_lid, Vector3d(box_boards[0].T, 0.0, box_boards[0].T), 0.0
    )
    batten = box_battens[0]
    batten.rotate(rotate_x=90)
    batten.rotate(rotate_y=90)
    box_wedge.rotate(rotate_x=90)
    box_wedge.rotate(rotate_y=90)
    box_assembly.add_board(batten, Vector3d(0.0, -batten.W, 0.0), 0.0)
    box_assembly.add_board(batten, Vector3d(batten.L, -batten.W, 0.0), 0.0)
    box_assembly.add_board(
        batten, Vector3d(s_box.length - batten.L, -batten.W, 0.0), 0.0
    )
    box_assembly.add_board(
        box_wedge,
        Vector3d(s_box.length - batten.L - box_wedge.L, -box_wedge.W, 0.0),
        0.0,
    )
    box_assembly.add_board(
        batten, Vector3d(s_box.length - 2 * batten.L - box_wedge.L, -batten.W, 0.0), 0.0
    )

    assembly = Assembly()
    assembly.add_subassembly(Vector3d(0.0, 0.0, 0.0), base_assembly)
    assembly.add_subassembly(Vector3d(Ta, -s_box.depth + Ta, Ta), box_assembly)
    assembly.add_subassembly(Vector3d(Ta, Ta + 5, Ta + s_till.width), till_assembly)

    # NOTE: omit this as it isn't very useful
    # print("## Plan view")
    # with print_svg(550, zoom=2, camera="plan") as canvas:
    #     assembly.draw(canvas, 20, 20)

    print("## Front view")
    with print_svg(550, zoom=2, camera="front") as canvas:
        assembly.draw(
            canvas,
            20,
            20,
            Dimension(0, "L", "below", pad=15, subassembly=0),
            Dimension(0, "W", "right", pad=30, subassembly=0),
            Dimension(0, "L", "above", pad=25, subassembly=1),
            Dimension(0, "W", "right", pad=15, subassembly=1),
            Dimension(0, "W", "right", pad=30, subassembly=2),
        )

    print("## Side view")
    with print_svg(550, zoom=2, camera="side") as canvas:
        assembly.draw(
            canvas,
            20,
            20,
            Dimension(1, "L", "below", pad=15, subassembly=0),
            Dimension(1, "W", "right", pad=15, subassembly=0),
            Dimension(1, "L", "above", pad=25, subassembly=1),
            Dimension(1, "W", "right", pad=15, subassembly=1),
            Dimension(1, "L", "below", pad=15, subassembly=2),
            Dimension(1, "W", "left", pad=15, subassembly=2),
        )

    print("## Base assembly")
    with print_svg(800, zoom=2, camera="above") as canvas:
        base_assembly.draw(
            canvas,
            40,
            20,
            Dimension(0, "W", "left", pad=20),
            Dimension(0, "L", "below", pad=20),
            Dimension(1, "L", "below", pad=20),
        )

    print("## Till assembly")
    with print_svg(800, zoom=2, camera="above") as canvas:
        till_assembly.draw(
            canvas,
            20,
            20,
            Dimension(0, "W", "left", pad=20),
            Dimension(0, "L", "below", pad=20),
            Dimension(1, "L", "below", pad=20),
        )

    print("## Box assembly")
    with print_svg(800, zoom=2, camera="above") as canvas:
        box_assembly.draw(
            canvas,
            20,
            20,
            Dimension(0, "W", "left", pad=20),
            Dimension(0, "L", "below", pad=20),
            Dimension(1, "L", "below", pad=20),
        )

    print("## Full assembly")
    with print_svg(800, zoom=2, camera="above") as canvas:
        assembly.draw(canvas, 20, 20)


if __name__ == "__main__":
    draw_art_tote()
