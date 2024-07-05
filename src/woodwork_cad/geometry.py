from itertools import pairwise
from math import cos, radians, sin, sqrt
from typing import Callable, List, Optional, Tuple

from .polygon import clip_polygon as _clip_polygon

Point = Tuple[float, float]
Points = List[Point]
Point3d = Tuple[float, float, float]
Points3d = List[Point3d]

Line = Tuple[Point, Point]

Vector3d = Tuple[float, float, float]


def to2d_isometric_above(p: Point3d) -> Point:
    x, y, z = p
    zx = cos(radians(-45))
    zy = sin(radians(-45))
    return (x + zx * z, y + zy * z)


def to2d_isometric_below(p: Point3d) -> Point:
    x, y, z = p
    zx = cos(radians(45))
    zy = sin(radians(45))
    return (x + zx * z, y + zy * z)


_to2d = to2d_isometric_below


def to2d(p: Point3d) -> Point:
    return _to2d(p)


def set_camera(mode: str) -> None:
    global _to2d, CAMERA, LIGHT
    if mode == "above":
        _to2d = to2d_isometric_above
        CAMERA = normalize((-1.0, 1.0, 1.0))
        LIGHT = normalize((-1.0, 1.0, 1.0))
    elif mode == "below":
        _to2d = to2d_isometric_below
        CAMERA = normalize((-1.0, -1.0, 1.0))
        LIGHT = normalize((-1.0, 1.0, 1.0))
    else:
        msg = f"Unknown camera mode '{mode}'"
        raise ValueError(msg)


def get_camera() -> str:
    if _to2d == to2d_isometric_above:
        return "above"
    elif _to2d == to2d_isometric_below:
        return "below"
    else:
        msg = f"Unknown camera mode '{_to2d}'"
        raise ValueError(msg)


def length(a: Vector3d) -> float:
    return sqrt(sum(a1 * a2 for a1, a2 in zip(a, a)))


def normalize(a: Vector3d) -> Vector3d:
    r = length(a)
    return (a[0] / r, a[1] / r, a[2] / r)


def equal_vectors(a: Vector3d, b: Vector3d) -> bool:
    a_rounded = f"{a[0]:.4f},{a[1]:.4f},{a[2]:.4f}"
    b_rounded = f"{b[0]:.4f},{b[1]:.4f},{b[2]:.4f}"
    return a_rounded == b_rounded


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
    clipping_polygon: Points, subject_polygon: Points, operation: str = "difference"
) -> List[Points]:
    result = _clip_polygon(subject_polygon, clipping_polygon, operation)
    return [poly.points for poly in result]


CAMERA: Vector3d = normalize((-1.0, -1.0, 1.0))

LIGHT: Vector3d = normalize((-1.0, 1.0, 1.0))


def get_lighting(normal: Vector3d) -> Tuple[float, float]:
    camera = dotproduct(normal, CAMERA)
    light = dotproduct(normal, LIGHT)
    return camera, light


def point_rotator(
    angle: float, origin_x: float, origin_y: float, offset_x: float, offset_y: float
) -> Callable[[Point], Point]:
    cos_a = cos(radians(angle))
    sin_a = sin(radians(angle))

    def rotate(point: Point) -> Point:
        x1 = point[0] - origin_x
        y1 = point[1] - origin_y
        return (
            offset_x + x1 * cos_a - y1 * sin_a,
            offset_y + x1 * sin_a + y1 * cos_a,
        )

    return rotate
