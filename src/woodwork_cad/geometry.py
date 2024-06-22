from itertools import pairwise
from math import cos, radians, sin, sqrt
from typing import List, Optional, Tuple

from .polygon import clip_polygon as _clip_polygon

Point = Tuple[float, float]
Points = List[Point]
Point3d = Tuple[float, float, float]
Points3d = List[Point3d]

Line = Tuple[Point, Point]

Vector3d = Tuple[float, float, float]


def to2d(p: Point3d) -> Point:
    x, y, z = p
    zx = cos(radians(45))
    zy = sin(radians(45))
    return (x + zx * z, y + zy * z)


def length(a: Vector3d) -> float:
    return sqrt(sum(a1 * a2 for a1, a2 in zip(a, a)))


def normalize(a: Vector3d) -> Vector3d:
    r = length(a)
    return (a[0] / r, a[1] / r, a[2] / r)


def line_length(x1: float, y1: float, x2: float, y2: float) -> float:
    return length((x2 - x1, y2 - y1, 0))


def subtract(p1: Point3d, p2: Point3d) -> Vector3d:
    return (p1[0] - p2[0], p1[1] - p2[1], p1[2] - p2[2])


def cross(a: Vector3d, b: Vector3d) -> Vector3d:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def dotproduct(a: Vector3d, b: Vector3d) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def is_inside(p: Point, line: Line) -> bool:
    a, b = line
    return (b[0] - a[0]) * (p[1] - a[1]) > (b[1] - a[1]) * (p[0] - a[0])


def get_edges(polygon: Points) -> List[Line]:
    return list(pairwise(polygon[-1:] + polygon))


def line_intersection(line0: Line, line1: Line) -> Optional[Point]:
    """
    calculate the point of intersection between two lines
    see {@link https://en.wikipedia.org/wiki/Line%E2%80%93line_intersection#Given_two_points_on_each_line|Wikipedia}
    """

    x1, y1 = line0[0]
    x2, y2 = line0[1]
    x3, y3 = line1[0]
    x4, y4 = line1[1]
    denominator = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)

    if abs(denominator) < 0.0001:
        return None  # parallel lines

    numerator_x = (x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)
    numerator_y = (x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)

    x = numerator_x / denominator
    y = numerator_y / denominator

    return (x, y)


def clip_polygon(clipping_polygon: Points, subject_polygon: Points) -> Points:
    """
    @see {@link https://en.wikipedia.org/wiki/Sutherland%E2%80%93Hodgman_algorithm|Sutherland–Hodgman algorithm}
    """
    result = subject_polygon
    for clip_edge in get_edges(clipping_polygon):
        points = result
        result = []

        for point_edge in get_edges(points):
            if is_inside(point_edge[1], clip_edge):
                if not is_inside(point_edge[0], clip_edge):
                    if point := line_intersection(point_edge, clip_edge):
                        result.append(point)

                result.append(point_edge[1])

            elif is_inside(point_edge[0], clip_edge):
                if point := line_intersection(point_edge, clip_edge):
                    result.append(point)

    return result


def clip_polygon2(
    clipping_polygon: Points, subject_polygon: Points, operation: str = "intersection"
) -> Points:
    result = _clip_polygon(subject_polygon, clipping_polygon, operation)
    return [poly.points for poly in result]
