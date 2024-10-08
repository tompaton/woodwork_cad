# ruff: noqa: F401
from math import sqrt

from woodwork_cad.assembly import Assembly
from woodwork_cad.board import Board
from woodwork_cad.defects import Hole, Notch
from woodwork_cad.geometry import Vector3d, to2d
from woodwork_cad.operations import (
    cut,
    cut_waste,
    draw_boards,
    draw_dimension,
    draw_dimension_ex,
    joint,
    process,
    process_all,
    process_first,
    rip,
    waste,
)
from woodwork_cad.svg import PrintToSVGFiles


def board_test() -> None:
    print_svg = PrintToSVGFiles("board_test")

    print("# Basic Operations")

    print("## Orientation")
    board = Board(100, 100, 100 / sqrt(2))
    board.label = "Board"
    assembly = Assembly()
    assembly.add_walls(
        90,
        [
            Board(100, 100, 5).mitre(-45, -45),
            Board(100 / sqrt(2), 100, 5).mitre(-45, -45),
            Board(100, 100, 5).mitre(-45, -45),
            Board(100 / sqrt(2), 100, 5).mitre(-45, -45),
        ],
    )
    with print_svg(500, zoom=2) as canvas:
        draw_boards(canvas, 40, 20, [board])
        assembly.draw(canvas, 300, 20)

        # HACK: use board to do dimensions for both board and assembly
        # (doesn't quite work as the board thickness means the assembly is bigger)
        board.label = "Assembly"
        board._draw_cuts(canvas, 300, 20)  # noqa: SLF001

        arrow = board.get_dimension("L", "above", 20)[:4]
        draw_dimension_ex(canvas, 40, 20, *arrow, "L, length, x", "L", "above")
        draw_dimension_ex(canvas, 300, 20, *arrow, "length", "L", "above")

        arrow = board.get_dimension("W", "left", 20)[:4]
        draw_dimension_ex(canvas, 40, 20, *arrow, "W, width, y", "W", "left")
        draw_dimension_ex(canvas, 300, 20, *arrow, "depth", "W", "left")

        arrow = board.get_dimension("T", "above", 20)[:4]
        draw_dimension_ex(canvas, 40, 20, *arrow, "T, thickness, z", "T", "above")
        draw_dimension_ex(canvas, 300, 20, *arrow, "width", "T", "above")

    print("## Stock")

    print("create a simple board")
    board = Board(300, 100, 12)

    print(f" - length {board.profile.length()[0]}")
    print(f" - area {board.area}")
    print(f" - aspect {board.aspect}")

    with print_svg(500, zoom=2) as canvas:
        draw_boards(canvas, 20, 20, [board])
        draw_dimension(canvas, 20, 20, board, "L", "below", pad=20)
        draw_dimension(canvas, 20, 20, board, "W", "left")
        draw_dimension(canvas, 20, 20, board, "T", "above")

    print("mark any defects")
    board.defects.add(Hole(30, 80))

    with print_svg(500, zoom=2) as canvas:
        draw_boards(canvas, 20, 20, [board])
        draw_dimension(canvas, 20, 20, board, "L", "above")
        draw_dimension(canvas, 20, 20, board, "W", "right", pad=20)
        draw_dimension(canvas, 20, 20, board, "T", "below")

    print("rip cut")
    boards = process(rip(50))(board)

    with print_svg(500, zoom=2) as canvas:
        draw_boards(canvas, 10, 10, boards)

    print("cross cut")
    boards2 = process(cut(100))(boards[0])
    boards2.extend(process(cut(150))(boards[1]))

    with print_svg(500, zoom=2) as canvas:
        draw_boards(canvas, 10, 10, boards2)

    print("cut list on original board")
    with print_svg(500, zoom=2) as canvas:
        draw_boards(canvas, 10, 10, [board])

    print("joint")
    boards3 = process(cut(150, kerf=0), cut(150, kerf=0))(Board(450, 75, 12))
    boards3[0].defects.add(Hole(50, 50))
    boards3[1].shade("rgba(200,150,150,0.25)")
    boards3[1].defects.add(Hole(75, 25))
    board3 = joint(*boards3)

    with print_svg(500, zoom=2) as canvas:
        draw_boards(canvas, 10, 10, boards3)
        draw_boards(canvas, 200, 10, [board3])

    print("mitre")
    board1 = boards2[-1]
    board1.mitre(45, 45)
    board1a = joint(
        Board(150, 15, 10),
        Board(150, 15, 10).shade("rgba(200,150,150,0.25)"),
        Board(150, 15, 10),
    )
    board1a.mitre(45, 45)
    with print_svg(500, zoom=2) as canvas:
        draw_boards(canvas, 10, 10, [board1])
        draw_boards(canvas, 200, 10, [board1a])

    print("mitred cut")
    boards1a = Board(350, 50, 10)
    boards1 = process(cut(150, kerf=5, angle=45))(boards1a)
    boards2 = process(cut(50, kerf=5, angle=-45))(boards1[0])
    boards3a = process(cut(150 + 15, kerf=5, angle=-45))(boards1[1])
    boards3b = process(rip(20))(boards3a[0])
    # print(f"{boards2[1].L=}, {boards3a[0].L=}\n")
    # print(f"{boards2[1].profile.length2()=}\n")
    # print(f"{boards3a[0].profile.length2()=}\n")
    # board3b = joint(boards2[1], boards3a[0])
    with print_svg(500, zoom=2) as canvas:
        draw_boards(canvas, 10, 10, [boards1a])
        draw_boards(canvas, 10, 90, boards1[:1])
        draw_boards(canvas, 200, 90, boards1[1:])
        draw_boards(canvas, 10, 170, boards2[:1])
        draw_boards(canvas, 100, 170, boards2[1:])
        draw_boards(canvas, 100, 260, boards3a[:1])
        draw_boards(canvas, 300, 260, boards3a[1:])
        draw_boards(canvas, 10, 350, boards3b[:1])
        draw_boards(canvas, 200, 350, boards3b[1:])
        # draw_boards(canvas, 10, 350, [board3b])

    print("dovetails")
    board3.dovetail_pins(right=False, tails=3, base=12)
    board3.dovetail_tails(right=True, tails=3, base=12)
    with print_svg(500, zoom=2) as canvas:
        draw_boards(canvas, 10, 10, [board3])
        board3.mitre(45, 45)
        draw_boards(canvas, 200, 10, [board3])

    print("dovetails (from above)")
    board3 = joint(*boards3)
    board3.dovetails.pin_ratio = 0.5
    board3.dovetails.pin1_ratio = 1.0
    board3.dovetail_pins(right=False, tails=3, base=12)
    board3.dovetail_tails(right=True, tails=3, base=12)
    with print_svg(500, zoom=2, camera="above") as canvas:
        draw_boards(canvas, 10, 10, [board3])
        board3.mitre(45, 45)
        draw_boards(canvas, 200, 10, [board3])

    print("grooves")
    board4 = Board(200, 100, 19)
    board4.grooves.add(10, 10, 10)
    board4.grooves.add(75, 15, 5, face=False)
    with print_svg(500, zoom=2) as canvas:
        draw_boards(canvas, 10, 10, [board4])
        board4.mitre(45, 45)
        draw_boards(canvas, 250, 10, [board4])

    print("grooves (from above)")
    board4 = Board(200, 100, 19)
    board4.grooves.add(10, 10, 10)
    board4.grooves.add(75, 15, 5, face=False)
    with print_svg(500, zoom=2, camera="above") as canvas:
        draw_boards(canvas, 10, 10, [board4])
        board4.mitre(45, 45)
        draw_boards(canvas, 250, 10, [board4])

    print("rotation")

    def _draw_rotated(canvas, board, x, y, angle, **kwargs):
        board.label = f"{angle}°"
        origin, mate = board.draw_board(canvas, x, y, rotate_y=angle, **kwargs)
        o = to2d(origin)
        m = to2d(mate)
        canvas.circle(x + o.x, y + o.y, 3, "red")
        canvas.circle(x + m.x, y + m.y, 3, "green")

    with print_svg(500, zoom=2) as canvas:
        _draw_rotated(canvas, board4, 10, 10, 0)
        _draw_rotated(canvas, board4, 250, 10, 180, offset=Vector3d(board4.L, 0, board4.T))
        _draw_rotated(canvas, board4, 10, 150, 90, offset=Vector3d(2 * board4.T, 0, 0))
        _draw_rotated(canvas, board4, 250, 150, 45)

    print("rotation (from above)")

    with print_svg(500, zoom=2, camera="above") as canvas:
        _draw_rotated(canvas, board4, 10, 10, 0)
        _draw_rotated(canvas, board4, 250, 10, 180, offset=Vector3d(board4.L, 0, board4.T))
        _draw_rotated(canvas, board4, 10, 250, 90, offset=Vector3d(2 * board4.T, 0, 0))
        _draw_rotated(canvas, board4, 250, 250, 45)

    print("plan view")

    board4.label = ""
    with print_svg(500, zoom=2, camera="plan") as canvas:
        board4.draw_board(canvas, 10, 10)

    print("front view")

    with print_svg(500, zoom=2, camera="front") as canvas:
        board4.draw_board(canvas, 10, 10)

    print("side view")

    with print_svg(500, zoom=2, camera="side") as canvas:
        board4.draw_board(canvas, 10, 10)


if __name__ == "__main__":
    board_test()
