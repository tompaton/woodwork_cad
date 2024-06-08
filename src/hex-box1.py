# ruff: noqa: F401
from decimal import Decimal

from woodwork_cad.board import (
    ZERO,
    Board,
    Hole,
    Notch,
    cut,
    cut_waste,
    draw_boards,
    joint2,
    label_all,
    mitre,
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

    R = Decimal(160)  # hexagon radius (outside)

    L2a = 3 * R + 2 * Decimal(5)
    L2b = L - L2a - 2 * raw_waste

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

    lid = panels.pop(0)
    assert lid

    print("## Cut sides")
    print("6 sides")

    sides = process_all(panels, cut(R), cut(R))
    with print_svg(1100, 500) as canvas:
        draw_boards(canvas, Decimal(10), Decimal(20), sides[:3])
        draw_boards(canvas, Decimal(300), Decimal(20), sides[3:])

    print("## Sides")

    print("mitre at 60 degrees")
    sides = process_all(sides, mitre(Decimal(60), Decimal(60)))

    print("TODO: Dovetails")

    corners = []
    with print_svg(500, 400, zoom=1) as canvas:
        x, y, angle = 150, 50, 0
        for side in sides:
            x, y = side.draw_plan(canvas, x, y, angle)
            corners.append((x, y))
            angle += 60
            canvas.circle(x, y, 2, "red", stroke_width=1)

    hex_L = max(x for x, y in corners) - min(x for x, y in corners)
    hex_W = max(y for x, y in corners) - min(y for x, y in corners)

    print(f"Width = {hex_L:.1f}, Height = {hex_W:.1f}")

    print("## Base")
    print("TODO")

    # roughly check if there's enough lid/base to cut hex panel out of
    lid2 = process(cut(Decimal(hex_L), kerf=ZERO), waste)(lid)[0]
    lid2 = process(rip(Decimal(hex_W), kerf=ZERO), waste)(lid2)[0]

    with print_svg(1100, 700) as canvas:
        draw_boards(canvas, Decimal(10), Decimal(20), [lid, lid2])

    print("## Lid")
    print("TODO")

    print("## Final box")
    print("TODO: side elevations")

    # options:
    # - framed lid (hexagonal frame with panel might need less jointed
    #   panel than a single piece)
    # - kumiko lid
    # - plywood base
    # - lid from the middle, base from 4 corner pieces


if __name__ == "__main__":
    draw_hex_box1()
