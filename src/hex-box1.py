# ruff: noqa: F401
import sys

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
from woodwork_cad.svg import (
    Points,
    crop_points,
    offset_points,
    polyline_bounds,
    print_svg,
    shrink_points,
)


# flags for design options
# STRIPS: alternate contrasting strips in panels
# MITRE: overlapping mitres
def draw_hex_box1(STRIPS: bool = True, MITRE: bool = True) -> None:
    print("# Hexagonal box")

    print("## Stock")

    L = 1000
    W = 43
    T = 13
    raw_waste = 20

    if MITRE:
        R = 160  # hexagon radius (outside)
        L2a = 3 * R + 2 * 5 - 15
    else:
        R = 160  # hexagon radius (outside)
        L2a = 3 * R + 2 * 5

    L2b = L - L2a - 2 * raw_waste

    rawboards = [Board(L, W, T) for _ in range(6)]
    short_strips = [Board(L2a, 5, T).shade("rgba(192,192,192,0.5)") for _ in range(4)]
    long_strips = [Board(L2b, 5, T).shade("rgba(192,192,192,0.5)") for _ in range(4)]

    print(f"6 boards {rawboards[0]}, trim {raw_waste} from each end, cut at {L2a}")

    rawboards[2].defects.add(Notch(360, W - 10, 400, W))
    rawboards[1].defects.add(Notch(780, 0, 820, 10))

    for rawboard in rawboards:
        rawboard.defects.add(Hole(315, 12))
        rawboard.defects.add(Hole(350, W - 12))
        rawboard.defects.add(Hole(655, 12))
        rawboard.defects.add(Hole(690, W - 12))

    cut_boards = process_all(
        rawboards, cut_waste(raw_waste), cut(L2a), cut(L2b, kerf=0), waste
    )

    with print_svg(1100) as canvas:
        if STRIPS:
            draw_boards(canvas, 10, 20, rawboards + short_strips + long_strips)
        else:
            draw_boards(canvas, 10, 20, rawboards)

    print("## Join panels")
    print("4 panels from 3 boards")
    if STRIPS:
        print("- insert contrasting 5mm strips between")

    short_boards = cut_boards[::2]
    long_boards = cut_boards[1::2]

    if STRIPS:
        lid1 = joint(
            long_boards.pop(),
            long_strips.pop(),
            long_boards.pop(),
            long_strips.pop(),
            long_boards.pop(),
        )
        lid2 = joint(
            long_boards.pop(),
            long_strips.pop(),
            long_boards.pop(),
            long_strips.pop(),
            long_boards.pop(),
        )
        panels = [
            lid1,
            lid2,
            joint(
                short_boards.pop(),
                short_strips.pop(),
                short_boards.pop(),
                short_strips.pop(),
                short_boards.pop(),
            ),
            joint(
                short_boards.pop(),
                short_strips.pop(),
                short_boards.pop(),
                short_strips.pop(),
                short_boards.pop(),
            ),
        ]

        assert not long_boards
        assert not short_boards
        assert not short_strips
        assert not long_strips

    else:
        lid1 = joint(*long_boards[:3])
        lid2 = joint(*long_boards[3:])
        panels = [
            lid1,
            lid2,
            joint(*short_boards[:3]),
            joint(*short_boards[3:]),
        ]

    for panel in panels:
        print(f"- {panel}")

    panels[2].grooves.add(5, T, 5, face=False)
    panels[2].grooves.add(panels[2].W - T - 5, T, 5, face=False)
    panels[3].grooves.add(5, T, 5, face=False)
    panels[3].grooves.add(panels[3].W - T - 5, T, 5, face=False)

    if MITRE:
        sides = process_all(panels[2:], cut(R), cut(R - 15))
    else:
        sides = process_all(panels[2:], cut(R), cut(R))

    with print_svg(1100, zoom=2) as canvas:
        draw_boards(canvas, 10, 20, panels)

    print("## Cut grooves")
    print("- grooves for top and bottom")
    print(f"- {T}mm groove 5mm from top and bottom edges")
    print("- groove on inside with defects/holes")

    if MITRE:
        print(
            "- this should be done before cutting sides, however that means that "
            "the mitres can't be overlapped as that alternates inside/outside "
            "faces."
        )

    print("## Cut sides")
    print(f"- 6 sides {sides[0]}")
    if MITRE:
        print("- mitre at 60 degrees, overlapping so no waste")
    else:
        print("- mitre at 60 degrees")

    print("- outside edge is 15mm shorter")
    print("- defects/holes and groove go on longer side (inside)")

    sides[0].mitre(60, 60)
    if MITRE:
        sides[1].mitre(-60, -60)
        sides[1].flip_profile()
    else:
        sides[1].mitre(60, 60)
    sides[2].mitre(60, 60)
    sides[3].mitre(60, 60)
    if MITRE:
        sides[4].mitre(-60, -60)
        sides[4].flip_profile()
    else:
        sides[4].mitre(60, 60)
    sides[5].mitre(60, 60)

    with print_svg(1100, zoom=2) as canvas:
        draw_boards(canvas, 10, 20, sides[:3])
        draw_boards(canvas, 300, 20, sides[3:])

    print("## Dovetails")
    print("TODO")

    print("## Sides")

    # TODO: factor out assemble function some how (separate from drawing...)
    corners: Points = []
    with print_svg(550, zoom=2) as canvas:
        x, y, angle = 150, 50, 0
        for side in sides:
            x, y = side.draw_plan(canvas, x, y, angle)
            corners.append((x, y))
            angle += 60
            canvas.circle(x, y, 2, "red")

        hex_L, hex_W, corners2 = polyline_bounds(corners)
        length_outside, length_inside = sides[0].profile.length()

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
    print("- TODO: rebates so groove for base can be smaller?")

    side_length = corners3[2][0] - corners3[3][0]
    print(f"- lid/base width {hex_W3:.1f}, side length {side_length:.1f}")

    half = hex_L3 - (hex_L3 - hex_W3) * 2

    with print_svg(1100, zoom=2) as canvas:
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
    draw_hex_box1(STRIPS="--strips" in sys.argv, MITRE="--mitre" in sys.argv)
