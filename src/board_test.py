# ruff: noqa: F401
from woodwork_cad.board import (
    Board,
    Hole,
    Notch,
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


def board_test() -> None:
    print_svg = PrintToSVGFiles("board_test")

    print("# Hexagonal box")

    print("## Stock")

    print("create a simple board")
    board = Board(300, 100, 12)

    print(f" - length {board.profile.length()[0]}")
    print(f" - area {board.area}")
    print(f" - aspect {board.aspect}")

    with print_svg(500, zoom=2) as canvas:
        draw_boards(canvas, 10, 10, [board])

    print("mark any defects")
    board.defects.add(Hole(30, 80))

    with print_svg(500, zoom=2) as canvas:
        draw_boards(canvas, 10, 10, [board])

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

    print("mitre")
    board1 = boards2[-1]
    board1.mitre(45, 45)
    with print_svg(500, zoom=2) as canvas:
        draw_boards(canvas, 10, 10, [board1])

    print("joint")
    boards3 = process(cut(150, kerf=0), cut(150, kerf=0))(Board(450, 75, 12))
    boards3[0].defects.add(Hole(50, 50))
    boards3[1].shade("rgba(200,150,150,0.25)")
    boards3[1].defects.add(Hole(75, 25))
    board3 = joint(*boards3)

    with print_svg(500, zoom=2) as canvas:
        draw_boards(canvas, 10, 10, boards3)
        draw_boards(canvas, 200, 10, [board3])

    print("dovetails")
    board3.dovetail_pins(right=False, width=20, tails=3, base=12)
    board3.dovetail_tails(right=True, width=20, tails=3, base=12)
    with print_svg(500, zoom=2) as canvas:
        draw_boards(canvas, 10, 10, [board3])

    print("grooves")
    board4 = Board(200, 100, 19)
    board4.grooves.add(10, 10, 10)
    board4.grooves.add(75, 15, 5, face=False)
    with print_svg(500, zoom=2) as canvas:
        draw_boards(canvas, 10, 10, [board4])


if __name__ == "__main__":
    board_test()
