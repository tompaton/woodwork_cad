from functools import partial

from woodwork_cad.geometry import (
    clip_polygon,
    clip_polygon2,
    cross,
    dotproduct,
    is_inside,
    length,
    line_intersection,
    to2d,
)
from woodwork_cad.svg import offset_points, print_svg


def test_line_intersection(canvas, offset, l1, l2):
    x, y = offset
    (x1, y1), (x2, y2) = l1
    canvas.line(x + x1, y + y1, x + x2, y + y2, "blue")
    (x1, y1), (x2, y2) = l2
    canvas.line(x + x1, y + y1, x + x2, y + y2, "green")
    p = line_intersection(l1, l2)
    if p:
        cx, cy = p
        canvas.circle(x + cx, y + cy, 3, "red")


def test_is_inside(canvas, offset, l1, points):
    x, y = offset
    (x1, y1), (x2, y2) = l1
    canvas.line(x + x1, y + y1, x + x2, y + y2, "blue")
    for p in points:
        cx, cy = p
        canvas.circle(x + cx, y + cy, 3, "green" if is_inside(p, l1) else "red")


def test_sutherland_hodgman_intuition(canvas, offset, edge, *to_add):
    x, y = offset
    clip = ((50, 10), (50, 100))
    canvas.line(x + 50, y + 10, x + 50, y + 100, "gray")
    canvas.text(x + 40, y + 10, content="in", font_size="12px")
    canvas.text(x + 65, y + 10, content="out", font_size="12px")
    (x1, y1), (x2, y2) = edge
    canvas.line(x + x1, y + y1, x + x2, y + y2, "blue")
    canvas.circle(x + x1, y + y1, 2, "blue")
    canvas.text(x + x1 + 5, y + y1 - 5, content="p1", font_size="12px")
    canvas.circle(x + x2, y + y2, 2, "blue")
    canvas.text(x + x2 + 5, y + y2 + 15, content="p2", font_size="12px")
    p3 = line_intersection(edge, clip)
    if p3:
        x3, y3 = p3
        canvas.circle(x + x3, y + y3, 2, "blue")
        canvas.text(x + x3 + 8, y + y3 + 5, content="i", font_size="12px")
    for i in to_add:
        x4, y4 = p3 if i == 3 else (x2, y2) if i == 2 else (x1, y1)
        canvas.circle(x + x4, y + y4, 4, "red", fill="none")


def test_clip_polygon1(canvas, offset, clip_poly, target_poly):
    return _test_clip_polygon(clip_polygon, canvas, offset, clip_poly, target_poly)


def test_clip_polygon2(canvas, offset, clip_poly, target_poly, operation):
    return _test_clip_polygon(
        partial(clip_polygon2, operation=operation),
        canvas,
        offset,
        clip_poly,
        target_poly,
    )


def _test_clip_polygon(algo, canvas, offset, clip_poly, target_poly):
    x, y = offset
    canvas.polyline("blue", offset_points(x - 1, y - 1, clip_poly), closed=True)
    canvas.polyline("green", offset_points(x + 1, y + 1, target_poly), closed=True)
    poly3a = algo(clip_poly, target_poly)
    if poly3a and not isinstance(poly3a[0], list):
        poly3a = [poly3a]
    for poly3 in poly3a:
        canvas.polyline("red", offset_points(x, y, poly3), closed=True)


def test_cross_product(canvas, offset, v1, v2):
    v3 = cross(v1, v2)
    print(f"{v1} x {v2} = {v3}\n")
    dot = dotproduct(v1, v2)
    l1 = length(v1)
    l2 = length(v2)
    l3 = length(v3)

    x, y = offset
    x0, y0 = x + 50, y + 50

    v1 = tuple(c * 70 for c in v1)
    v2 = tuple(c * 70 for c in v2)
    v3 = tuple(c * 70 for c in v3)

    x1, y1 = to2d(v1)
    x2, y2 = to2d(v2)
    x3, y3 = to2d(v3)

    canvas.polyline("blue", [(x0, y0), (x0 + x1, y0 + y1)])
    canvas.text(x0 + x1 + 5, y0 + y1, "start", content=f"v1 {l1:.2f}", font_size="12px")

    canvas.polyline("green", [(x0, y0), (x0 + x2, y0 + y2)])
    canvas.text(x0 + x2 + 5, y0 + y2, "start", content=f"v2 {l2:.2f}", font_size="12px")

    canvas.polyline("red", [(x0, y0), (x0 + x3, y0 + y3)])
    canvas.text(x0 + x3 + 5, y0 + y3, "start", content=f"v3 {l3:.2f}", font_size="12px")

    canvas.text(x0 + 5, y0 - 15, "start", content=f"dot = {dot:.2f}", font_size="12px")


def xy_grid(width, height=None, max_width=None):
    height = height or width
    max_width = max_width or width * 3
    x = 0
    y = 0
    while True:
        yield x + 10, y + 10
        x += width
        if max_width - x < width:
            x = 0
            y += height


def geometry_test():
    print("# Geometry test\n")

    print("## line_intersection")
    with print_svg(500, zoom=2) as canvas:
        grid = xy_grid(150)
        for l1, l2 in [
            (((10, 10), (10, 100)), ((100, 10), (100, 100))),
            (((100, 10), (10, 100)), ((10, 10), (100, 100))),
            (((10, 10), (10, 100)), ((10, 10), (100, 100))),
            (((100, 10), (10, 100)), ((100, 10), (100, 100))),
            (((100, 100), (10, 10)), ((100, 10), (100, 100))),
            (((10, 10), (10, 100)), ((100, 10), (10, 100))),
            (((10, 10), (50, 100)), ((100, 10), (10, 100))),
            (((10, 10), (100, 50)), ((100, 10), (10, 100))),
            (((100, 10), (10, 100)), ((10, 10), (100, 50))),
            (((100, 10), (10, 100)), ((10, 10), (40, 50))),
            (((10, 10), (50, 40)), ((10, 100), (50, 60))),
        ]:
            test_line_intersection(canvas, next(grid), l1, l2)

    print("## is_inside")
    with print_svg(500, zoom=2) as canvas:
        grid = xy_grid(150)
        points = [(x, y) for x in range(10, 100, 10) for y in range(10, 100, 10)]
        for l1 in [
            ((0, 0), (100, 100)),
            ((100, 10), (10, 100)),
            ((40, 0), (60, 100)),
        ]:
            test_is_inside(canvas, next(grid), l1, points)

    print("## test for sutherland-hodgman")
    with print_svg(500, zoom=2) as canvas:
        grid = xy_grid(150)
        for edge, to_add in [
            # edge leaving clip region, include intersection point
            (((10, 10), (80, 100)), [3]),
            # edge entering clip region, include intersection point and edge end
            (((80, 10), (10, 100)), [2, 3]),
            # edge inside clip region, add edge end
            (((10, 10), (40, 100)), [2]),
            # edge outside clip region
            (((80, 10), (60, 100)), []),
            # edge coincident with clip region is outside
            (((50, 20), (50, 90)), []),
        ]:
            test_sutherland_hodgman_intuition(canvas, next(grid), edge, *to_add)

    for title, test_clip_polygon in [
        (
            "## clip_polygon (sutherland-hodgman)\n"
            "this fails when the clip polygon is not convex",
            test_clip_polygon1,
        ),
        (
            "## clip_polygon2 - union (Greiner and Hormann)",
            partial(test_clip_polygon2, operation="union"),
        ),
        (
            "## clip_polygon2 - difference (Greiner and Hormann)\n"
            "this is now the simplest, but clip polygon still can't be coincident...",
            partial(test_clip_polygon2, operation="difference"),
        ),
        (
            "## clip_polygon2 - reversed-diff (Greiner and Hormann)",
            partial(test_clip_polygon2, operation="reversed-diff"),
        ),
        (
            "## clip_polygon2 - intersection (Greiner and Hormann)\n"
            "polygons can't be coincident, so make clip region a little larger and it works",
            partial(test_clip_polygon2, operation="intersection"),
        ),
    ]:
        print(title)
        with print_svg(500, zoom=2) as canvas:
            grid = xy_grid(150)
            poly1 = [(10, 10), (100, 10), (100, 50), (10, 50)]
            poly2 = [(20, 20), (50, 20), (50, 100), (20, 100)]
            poly3 = [
                (15, 15),
                (45, 15),
                (50, 0),
                (55, 15),
                (60, 15),
                (80, 50),
                (70, 90),
                (60, 80),
                (55, 70),
                (20, 60),
                (55, 50),
                (60, 40),
                (50, 30),
            ]
            test_clip_polygon(canvas, next(grid), poly1, poly2)
            test_clip_polygon(canvas, next(grid), poly2, poly1)
            test_clip_polygon(canvas, next(grid), poly1, poly3)
            test_clip_polygon(canvas, next(grid), poly2, poly3)
            test_clip_polygon(canvas, next(grid), poly3, poly1)
            test_clip_polygon(canvas, next(grid), poly3, poly2)

            dovetail = [(10 - 1, 25), (30, 20), (30, 50), (10 - 1, 45)]
            panel = [(10, 10), (100, 10), (100, 100), (10, 100)]
            test_clip_polygon(canvas, next(grid), dovetail, panel)

            dovetail2 = [
                (10 - 1, 10 - 1),
                (100 + 1, 10 - 1),
                (100 + 1, 100 + 1),
                (10 - 1, 100 + 1),
                (10 - 1, 45),
                (30, 50),
                (30, 20),
                (10 - 1, 25),
            ]
            test_clip_polygon(canvas, next(grid), dovetail2, panel)
            panel2 = [
                (10, 10),
                (100, 10),
                (100, 100),
                (10, 100),
                (10, 85),
                (30, 90),
                (30, 60),
                (10, 65),
            ]
            test_clip_polygon(canvas, next(grid), dovetail2, panel2)

            dovetail3 = [
                (10 + 0.01, 10 + 0.01),
                (100 + 0.01, 10 + 0.01),
                (100 + 0.01, 100 + 0.01),
                (10 + 0.01, 100 + 0.01),
                (10 + 0.01, 45 + 0.01),
                (30 + 0.01, 50 + 0.01),
                (30 + 0.01, 20 + 0.01),
                (10 + 0.01, 25 + 0.01),
            ]
            test_clip_polygon(canvas, next(grid), dovetail3, panel2)

            # subject polygon
            spoly = [
                (u * 15, v * 15)
                for u, v in [(1.5, 1.3), (7.5, 2.5), (4.0, 3.0), (4.5, 6.5)]
            ]

            # clip polygon
            cpoly = [
                (u * 15, v * 15)
                for u, v in [
                    (5.0, 4.5),
                    (3.0, 5.5),
                    (1.0, 4.0),
                    (1.5, 3.5),
                    (0.0, 2.0),
                    (3.0, 2.3),
                    (2.5, 1.0),
                    (5.5, 0.0),
                ]
            ]

            test_clip_polygon(canvas, next(grid), cpoly, spoly)

    print("## dot product, cross product")
    with print_svg(500, zoom=2) as canvas:
        grid = xy_grid(200, max_width=400)
        for v1, v2 in [
            ((1, 0, 0), (0, 1, 0)),
            ((0, 1, 0), (1, 0, 0)),
            ((0.5, 0.5, 0), (0, 1, 0)),
            ((0, 1, 0), (0.5, 0.5, 0)),
            ((0, 1, 0), (0, 0, 1)),
            ((0, 0, 1), (0, 1, 0)),
        ]:
            test_cross_product(canvas, next(grid), v1, v2)

    # TODO: tests for normals


if __name__ == "__main__":
    geometry_test()
