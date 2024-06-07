# ruff: noqa: F401
from decimal import Decimal

from woodwork_cad.board import (
    ZERO,
    Board,
    Hole,
    Notch,
    cube_net,
    cut,
    cut_waste,
    draw_boards,
    joint2,
    label_all,
    process,
    process_all,
    process_first,
    rip,
    waste,
)
from woodwork_cad.svg import print_svg


def draw_hex_box1() -> None:
    print("# Hexagonal box")

    print("## Stock")
    print("6 boards, trim waste, cut in half")

    L = Decimal(1000)
    W = Decimal(43)
    T = Decimal(13)
    raw_waste = Decimal(20)

    L2a = Decimal(600)
    L2b = L - Decimal(600) - 2 * raw_waste

    rawboards = [Board(L, W, T) for _ in range(6)]

    rawboards[2].add_defect(Notch(Decimal(360), W - Decimal(10), Decimal(400), W))
    rawboards[1].add_defect(Notch(Decimal(780), ZERO, Decimal(820), Decimal(10)))

    for rawboard in rawboards:
        rawboard.add_defect(Hole(Decimal(315), Decimal(12)))
        rawboard.add_defect(Hole(Decimal(350), W - Decimal(12)))
        rawboard.add_defect(Hole(Decimal(655), Decimal(12)))
        rawboard.add_defect(Hole(Decimal(690), W - Decimal(12)))

    panels = process_all(
        rawboards, cut_waste(raw_waste), cut(L2a), cut(L2b, kerf=ZERO), waste
    )

    with print_svg(1100, 500) as canvas:
        draw_boards(canvas, Decimal(10), Decimal(20), rawboards)

    print("## Join panels")
    print("4 boards")

    joint2(panels, 1, 3, 5, 7, 9, 11)
    joint2(panels, 3, 4, 5)
    joint2(panels, 0, 1, 2)

    with print_svg(1100, 600) as canvas:
        draw_boards(canvas, Decimal(10), Decimal(20), panels)

    print("## Cut sides")
    print("TODO: 6 sides")
    print("TODO: mitre at 60 degrees")

    print("## Dovetails")
    print("TODO")

    print("## Base")
    print("TODO")

    print("## Lid")
    print("TODO")

    print("## Final box")
    print("TODO")


if __name__ == "__main__":
    draw_hex_box1()
