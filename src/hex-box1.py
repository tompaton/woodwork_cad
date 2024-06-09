# ruff: noqa: F401
from woodwork_cad.board import (
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

    L = 1000
    W = 43
    T = 13
    raw_waste = 20

    R = 155  # hexagon radius (outside)

    L2a = 3 * R + 2 * 5
    L2b = L - L2a - 2 * raw_waste

    rawboards = [Board(L, W, T) for _ in range(6)]

    rawboards[2].add_defect(Notch(360, W - 10, 400, W))
    rawboards[1].add_defect(Notch(780, 0, 820, 10))

    for rawboard in rawboards:
        rawboard.add_defect(Hole(315, 12))
        rawboard.add_defect(Hole(350, W - 12))
        rawboard.add_defect(Hole(655, 12))
        rawboard.add_defect(Hole(690, W - 12))

    panels = process_all(
        rawboards, cut_waste(raw_waste), cut(L2a), cut(L2b, kerf=0), waste
    )

    with print_svg(1100) as canvas:
        draw_boards(canvas, 10, 20, rawboards)

    print("## Join panels")
    print("4 boards")

    joint2(panels, 7, 9, 11)
    joint2(panels, 1, 3, 5)
    joint2(panels, 3, 4, 5)
    joint2(panels, 0, 1, 2)

    with print_svg(1100) as canvas:
        draw_boards(canvas, 10, 20, panels)

    lid1, lid2 = panels.pop(0), panels.pop(0)

    print("## Cut sides")
    print("6 sides")

    sides = process_all(panels, cut(R), cut(R))
    with print_svg(1100) as canvas:
        draw_boards(canvas, 10, 20, sides[:3])
        draw_boards(canvas, 300, 20, sides[3:])

    print("## Sides")

    print("- mitre at 60 degrees")
    sides = process_all(sides, mitre(60, 60))

    print("- TODO: Dovetails")

    corners = []
    with print_svg(550, zoom=2) as canvas:
        x, y, angle = 150, 50, 0
        for side in sides:
            x, y = side.draw_plan(canvas, x, y, angle)
            corners.append((x, y))
            angle += 60
            canvas.circle(x, y, 2, "red")

    min_hex_x = min(x for x, y in corners)
    min_hex_y = min(y for x, y in corners)
    hex_L = max(x for x, y in corners) - min_hex_x
    hex_W = max(y for x, y in corners) - min_hex_y

    print(f"Width = {hex_L:.1f}, Height = {hex_W:.1f}")

    print("## Base and Lid")
    print("- Cut base and lid out of boards in 2 halves and join")
    print("- these will be a little oversized if either is fitted into a groove")

    with print_svg(1100) as canvas:
        draw_boards(canvas, 10, 20, [lid1, lid2])
        # draw hex over panel
        canvas.polyline(
            "blue",
            [
                (x - min_hex_x + 10, y - min_hex_y + 20 + lid1.W - hex_W / 2)
                for x, y in corners
                if y - min_hex_y <= lid1.W
            ],
            stroke_dasharray=2,
            closed=True,
        )
        canvas.polyline(
            "blue",
            [
                (
                    x - min_hex_x + 10 + hex_L - (hex_L - hex_W) * 2 + 5,
                    y - min_hex_y + 20 - hex_W / 2,
                )
                for x, y in corners
                if y - min_hex_y >= lid1.W / 2
            ],
            stroke_dasharray=2,
            closed=True,
        )

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
