from functools import partial

from woodwork_cad.geometry import (
    Point,
    Point3d,
    Vector3d,
    clip_polygon,
    clip_polygon2,
    cross,
    dotproduct,
    is_inside,
    length,
    line_intersection,
    to2d,
)
from woodwork_cad.svg import PrintToSVGFiles, offset_points


def test_line_intersection(canvas, offset, l1, l2):
    x, y = offset
    p1, p2 = l1
    canvas.line(x + p1.x, y + p1.y, x + p2.x, y + p2.y, "blue")
    p1, p2 = l2
    canvas.line(x + p1.x, y + p1.y, x + p2.x, y + p2.y, "green")
    p = line_intersection(l1, l2)
    if p:
        canvas.circle(x + p.x, y + p.y, 3, "red")


def test_is_inside(canvas, offset, l1, points):
    x, y = offset
    p1, p2 = l1
    canvas.line(x + p1.x, y + p1.y, x + p2.x, y + p2.y, "blue")
    for p in points:
        canvas.circle(x + p.x, y + p.y, 3, "green" if is_inside(p, l1) else "red")


def test_sutherland_hodgman_intuition(canvas, offset, edge, *to_add):
    x, y = offset
    clip = (Point(50, 10), Point(50, 100))
    canvas.line(x + 50, y + 10, x + 50, y + 100, "gray")
    canvas.text(x + 40, y + 10, content="in", font_size="12px")
    canvas.text(x + 65, y + 10, content="out", font_size="12px")
    p1, p2 = edge
    canvas.line(x + p1.x, y + p1.y, x + p2.x, y + p2.y, "blue")
    canvas.circle(x + p1.x, y + p1.y, 2, "blue")
    canvas.text(x + p1.x + 5, y + p1.y - 5, content="p1", font_size="12px")
    canvas.circle(x + p2.x, y + p2.y, 2, "blue")
    canvas.text(x + p2.x + 5, y + p2.y + 15, content="p2", font_size="12px")
    p3 = line_intersection(edge, clip)
    if p3:
        canvas.circle(x + p3.x, y + p3.y, 2, "blue")
        canvas.text(x + p3.x + 8, y + p3.y + 5, content="i", font_size="12px")
    for i in to_add:
        x4, y4 = (p3.x, p3.y) if i == 3 else (p2.x, p2.y) if i == 2 else (p1.x, p1.y)
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

    v1 = Point3d(v1.x * 70, v1.y * 70, v1.z * 70)
    v2 = Point3d(v2.x * 70, v2.y * 70, v2.z * 70)
    v3 = Point3d(v3.x * 70, v3.y * 70, v3.z * 70)

    p1 = to2d(v1)
    p2 = to2d(v2)
    p3 = to2d(v3)

    canvas.polyline("blue", [Point(x0, y0), Point(x0 + p1.x, y0 + p1.y)])
    canvas.text(
        x0 + p1.x + 5, y0 + p1.y, "start", content=f"v1 {l1:.2f}", font_size="12px"
    )

    canvas.polyline("green", [Point(x0, y0), Point(x0 + p2.x, y0 + p2.y)])
    canvas.text(
        x0 + p2.x + 5, y0 + p2.y, "start", content=f"v2 {l2:.2f}", font_size="12px"
    )

    canvas.polyline("red", [Point(x0, y0), Point(x0 + p3.x, y0 + p3.y)])
    canvas.text(
        x0 + p3.x + 5, y0 + p3.y, "start", content=f"v3 {l3:.2f}", font_size="12px"
    )

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
    print_svg = PrintToSVGFiles("geometry_test")

    print("# Geometry test\n")

    print("## line_intersection")
    with print_svg(500, zoom=2) as canvas:
        grid = xy_grid(150)
        for l1, l2 in [
            ((Point(10, 10), Point(10, 100)), (Point(100, 10), Point(100, 100))),
            ((Point(100, 10), Point(10, 100)), (Point(10, 10), Point(100, 100))),
            ((Point(10, 10), Point(10, 100)), (Point(10, 10), Point(100, 100))),
            ((Point(100, 10), Point(10, 100)), (Point(100, 10), Point(100, 100))),
            ((Point(100, 100), Point(10, 10)), (Point(100, 10), Point(100, 100))),
            ((Point(10, 10), Point(10, 100)), (Point(100, 10), Point(10, 100))),
            ((Point(10, 10), Point(50, 100)), (Point(100, 10), Point(10, 100))),
            ((Point(10, 10), Point(100, 50)), (Point(100, 10), Point(10, 100))),
            ((Point(100, 10), Point(10, 100)), (Point(10, 10), Point(100, 50))),
            ((Point(100, 10), Point(10, 100)), (Point(10, 10), Point(40, 50))),
            ((Point(10, 10), Point(50, 40)), (Point(10, 100), Point(50, 60))),
        ]:
            test_line_intersection(canvas, next(grid), l1, l2)

    print("## is_inside")
    with print_svg(500, zoom=2) as canvas:
        grid = xy_grid(150)
        points = [Point(x, y) for x in range(10, 100, 10) for y in range(10, 100, 10)]
        for l1 in [
            (Point(0, 0), Point(100, 100)),
            (Point(100, 10), Point(10, 100)),
            (Point(40, 0), Point(60, 100)),
        ]:
            test_is_inside(canvas, next(grid), l1, points)

    print("## test for sutherland-hodgman")
    with print_svg(500, zoom=2) as canvas:
        grid = xy_grid(150)
        for edge, to_add in [
            # edge leaving clip region, include intersection point
            ((Point(10, 10), Point(80, 100)), [3]),
            # edge entering clip region, include intersection point and edge end
            ((Point(80, 10), Point(10, 100)), [2, 3]),
            # edge inside clip region, add edge end
            ((Point(10, 10), Point(40, 100)), [2]),
            # edge outside clip region
            ((Point(80, 10), Point(60, 100)), []),
            # edge coincident with clip region is outside
            ((Point(50, 20), Point(50, 90)), []),
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
            poly1 = [Point(10, 10), Point(100, 10), Point(100, 50), Point(10, 50)]
            poly2 = [Point(20, 20), Point(50, 20), Point(50, 100), Point(20, 100)]
            poly3 = [
                Point(15, 15),
                Point(45, 15),
                Point(50, 0),
                Point(55, 15),
                Point(60, 15),
                Point(80, 50),
                Point(70, 90),
                Point(60, 80),
                Point(55, 70),
                Point(20, 60),
                Point(55, 50),
                Point(60, 40),
                Point(50, 30),
            ]
            test_clip_polygon(canvas, next(grid), poly1, poly2)
            test_clip_polygon(canvas, next(grid), poly2, poly1)
            test_clip_polygon(canvas, next(grid), poly1, poly3)
            test_clip_polygon(canvas, next(grid), poly2, poly3)
            test_clip_polygon(canvas, next(grid), poly3, poly1)
            test_clip_polygon(canvas, next(grid), poly3, poly2)

            dovetail = [
                Point(10 - 1, 25),
                Point(30, 20),
                Point(30, 50),
                Point(10 - 1, 45),
            ]
            panel = [Point(10, 10), Point(100, 10), Point(100, 100), Point(10, 100)]
            test_clip_polygon(canvas, next(grid), dovetail, panel)

            dovetail2 = [
                Point(10 - 1, 10 - 1),
                Point(100 + 1, 10 - 1),
                Point(100 + 1, 100 + 1),
                Point(10 - 1, 100 + 1),
                Point(10 - 1, 45),
                Point(30, 50),
                Point(30, 20),
                Point(10 - 1, 25),
            ]
            test_clip_polygon(canvas, next(grid), dovetail2, panel)
            panel2 = [
                Point(10, 10),
                Point(100, 10),
                Point(100, 100),
                Point(10, 100),
                Point(10, 85),
                Point(30, 90),
                Point(30, 60),
                Point(10, 65),
            ]
            test_clip_polygon(canvas, next(grid), dovetail2, panel2)

            dovetail3 = [
                Point(10 + 0.01, 10 + 0.01),
                Point(100 + 0.01, 10 + 0.01),
                Point(100 + 0.01, 100 + 0.01),
                Point(10 + 0.01, 100 + 0.01),
                Point(10 + 0.01, 45 + 0.01),
                Point(30 + 0.01, 50 + 0.01),
                Point(30 + 0.01, 20 + 0.01),
                Point(10 + 0.01, 25 + 0.01),
            ]
            test_clip_polygon(canvas, next(grid), dovetail3, panel2)

            # subject polygon
            spoly = [
                Point(u * 15, v * 15)
                for u, v in [(1.5, 1.3), (7.5, 2.5), (4.0, 3.0), (4.5, 6.5)]
            ]

            # clip polygon
            cpoly = [
                Point(u * 15, v * 15)
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
            (Vector3d(1, 0, 0), Vector3d(0, 1, 0)),
            (Vector3d(0, 1, 0), Vector3d(1, 0, 0)),
            (Vector3d(0.5, 0.5, 0), Vector3d(0, 1, 0)),
            (Vector3d(0, 1, 0), Vector3d(0.5, 0.5, 0)),
            (Vector3d(0, 1, 0), Vector3d(0, 0, 1)),
            (Vector3d(0, 0, 1), Vector3d(0, 1, 0)),
        ]:
            test_cross_product(canvas, next(grid), v1, v2)

    # TODO: tests for normals


if __name__ == "__main__":
    geometry_test()
