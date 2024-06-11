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
from woodwork_cad.svg import (
    Points,
    crop_points,
    offset_points,
    polyline_bounds,
    print_svg,
    shrink_points,
)


def draw_hex_box1() -> None:
    print("# Hexagonal box")

    print("## Stock")

    L = 1000
    W = 43
    T = 13
    raw_waste = 20

    R = 160  # hexagon radius (outside)

    L2a = 3 * R + 2 * 5 - 15
    L2b = L - L2a - 2 * raw_waste

    rawboards = [Board(L, W, T) for _ in range(6)]
    strips = [Board(L2a, 5, T).shade("rgba(192,192,192,0.5)") for _ in range(4)] + [
        Board(L2b, 5, T).shade("rgba(192,192,192,0.5)") for _ in range(4)
    ]

    print(f"6 boards {rawboards[0]}, trim {raw_waste} from each end, cut at {L2a}")

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
        draw_boards(canvas, 10, 20, rawboards + strips)

    print("## Join panels")
    print("4 panels from 3 boards, insert contrasting 5mm strips between")

    panels.insert(1, strips.pop(0))
    panels.insert(3, strips.pop())
    panels.insert(5, strips.pop(0))
    panels.insert(7, strips.pop())
    panels.insert(11, strips.pop(0))
    panels.insert(13, strips.pop())
    panels.insert(15, strips.pop(0))
    panels.insert(17, strips.pop())

    joint2(panels, 12, 13, 16, 17, 19)
    joint2(panels, 2, 3, 6, 7, 9)
    joint2(panels, 5, 6, 7, 8, 9)
    joint2(panels, 0, 1, 2, 3, 4)

    for panel in panels:
        print(f"- {panel}")

    lid1, lid2 = panels.pop(0), panels.pop(0)
    sides = process_all(panels, cut(R), cut(R - 15))

    with print_svg(1100) as canvas:
        draw_boards(canvas, 10, 20, [lid1, lid2] + panels)

    print("## Cut grooves")
    print("TODO")
    print("- grooves for top and bottom")

    print("## Cut sides")
    print(f"- 6 sides {sides[0]}")
    print("- mitre at 60 degrees, overlapping so no waste")
    print("- outside edge is 15mm shorter")
    sides[0].mitre(60, 60)
    sides[1].mitre(-60, -60)
    sides[1].flip_profile()
    sides[2].mitre(60, 60)
    sides[3].mitre(60, 60)
    sides[4].mitre(-60, -60)
    sides[4].flip_profile()
    sides[5].mitre(60, 60)

    with print_svg(1100) as canvas:
        draw_boards(canvas, 10, 20, sides[:3])
        draw_boards(canvas, 300, 20, sides[3:])

    print("## Dovetails")
    print("TODO")

    print("## Sides")

    corners: Points = []
    with print_svg(550, zoom=2) as canvas:
        x, y, angle = 150, 50, 0
        for side in sides:
            x, y = side.draw_plan(canvas, x, y, angle)
            corners.append((x, y))
            angle += 60
            canvas.circle(x, y, 2, "red")

        hex_L, hex_W, corners2 = polyline_bounds(corners)
        length_outside, length_inside = sides[0].profile_length()

        # shrink these a bit as they will be set in a groove
        hex_L3, hex_W3, corners3 = shrink_points(corners2, T - 5)

        hex_top = crop_points(offset_points(0, lid1.W - hex_W3 / 2, corners3), lid1.W)
        hex_bottom = crop_points(
            offset_points(0, -hex_W3 / 2, corners3),
            lid1.W,
        )

        canvas.polyline(
            "green",
            offset_points(
                150 + length_outside / 2 - hex_L3 / 2,
                50 + (hex_W - hex_W3) / 2,
                corners3,
            ),
            stroke_dasharray=3,
            closed=True,
        )

    print(f"- Final width = {hex_L:.1f}, Final height = {hex_W:.1f}")
    print(
        f"- Inside length = {length_inside:.1f}, Outside length = {length_outside:.1f}"
    )

    print("## Base and Lid")
    print("- Cut base and lid out of boards in 2 halves and join")

    side_length = corners3[2][0] - corners3[3][0]
    print(f"- lid/base width {hex_W3:.1f}, side length {side_length:.1f}")

    half = hex_L3 - (hex_L3 - hex_W3) * 2

    with print_svg(1100) as canvas:
        lid1_xy, lid2_xy = draw_boards(canvas, 10, 20, [lid1, lid2])

        # draw hex over panel
        canvas.polyline(
            "green",
            offset_points(
                lid1_xy[0],
                lid1_xy[1],
                hex_top,
            ),
            stroke_dasharray=3,
            closed=True,
        )
        canvas.polyline(
            "green",
            offset_points(
                lid1_xy[0] + half,
                lid1_xy[1],
                hex_bottom,
            ),
            stroke_dasharray=3,
            closed=True,
        )

        canvas.polyline(
            "green",
            offset_points(
                lid2_xy[0],
                lid2_xy[1],
                hex_bottom,
            ),
            stroke_dasharray=3,
            closed=True,
        )
        canvas.polyline(
            "green",
            offset_points(
                lid2_xy[0] + half,
                lid2_xy[1],
                hex_top,
            ),
            stroke_dasharray=3,
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
