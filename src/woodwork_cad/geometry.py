from collections.abc import Callable
from dataclasses import dataclass
from itertools import pairwise
from math import cos, radians, sin, sqrt

from woodwork_cad.polygon import clip_polygon as _clip_polygon

"""
Notes re clipping algorithms

sutherland-hodgman algorithm doesn't handle non-convex polygons.

greiner-hormann works better, but doesn't handle "degenerate" polygons where
edges are coincident.

improved algorithms are more complicated.

peturbing the clip polygons by a small amount is a reasonable workaround though.

### references

https://sean.cm/a/polygon-clipping-pt2/

https://www.sciencedirect.com/science/article/abs/pii/S0965997813000379

https://github.com/lycantropos/martinez/blob/master/martinez/boolean.py

https://www.sciencedirect.com/science/article/pii/S259014861930007X#sec0012
https://www.inf.usi.ch/hormann/papers/Foster.2019.CSP.pdf

"""


@dataclass
class Point:
    x: float
    y: float

    def offset(self, dx: float = 0.0, dy: float = 0.0) -> "Point":
        return Point(self.x + dx, self.y + dy)


Points = list[Point]
Line = tuple[Point, Point]


@dataclass
class Point3d:
    x: float
    y: float
    z: float

    def offset(self, dx: float = 0.0, dy: float = 0.0, dz: float = 0.0) -> "Point3d":
        return Point3d(self.x + dx, self.y + dy, self.z + dz)


Points3d = list[Point3d]


@dataclass
class Vector3d:
    x: float
    y: float
    z: float

    def __str__(self) -> str:
        return f"{(self.x, self.y, self.z)}"


def to2d_isometric_above(p: Point3d) -> Point:
    zx = cos(radians(-45))
    zy = sin(radians(-45))
    return Point(p.x + zx * p.z, p.y + zy * p.z)


def to2d_isometric_below(p: Point3d) -> Point:
    zx = cos(radians(45))
    zy = sin(radians(45))
    return Point(p.x + zx * p.z, p.y + zy * p.z)


def to2d_plan(p: Point3d) -> Point:
    return Point(p.x, -p.z)


def to2d_front(p: Point3d) -> Point:
    return Point(p.x, p.y)


def to2d_side(p: Point3d) -> Point:
    return Point(p.z, p.y)


_to2d = to2d_isometric_below


def to2d(p: Point3d, offset_x: float = 0.0, offset_y: float = 0.0) -> Point:
    p2 = _to2d(p)
    return Point(p2.x + offset_x, p2.y + offset_y)


def set_camera(mode: str) -> None:
    global _to2d, _get_lighting, CAMERA, LIGHT  # noqa: PLW0603
    if mode == "above":
        _to2d = to2d_isometric_above
        _get_lighting = get_3d_lighting
        CAMERA = normalize(Vector3d(-1.0, 1.0, 1.0))
        LIGHT = normalize(Vector3d(-1.0, 1.0, 1.0))
    elif mode == "below":
        _to2d = to2d_isometric_below
        _get_lighting = get_3d_lighting
        CAMERA = normalize(Vector3d(-1.0, -1.0, 1.0))
        LIGHT = normalize(Vector3d(-1.0, 1.0, 1.0))
    elif mode == "plan":
        _to2d = to2d_plan
        _get_lighting = get_plan_lighting
    elif mode == "front":
        _to2d = to2d_front
        _get_lighting = get_plan_lighting
    elif mode == "side":
        _to2d = to2d_side
        _get_lighting = get_plan_lighting
    else:
        msg = f"Unknown camera mode '{mode}'"
        raise ValueError(msg)


def get_camera() -> str:
    if _to2d == to2d_isometric_above:
        return "above"
    if _to2d == to2d_isometric_below:
        return "below"
    if _to2d == to2d_plan:
        return "plan"
    if _to2d == to2d_front:
        return "front"
    if _to2d == to2d_side:
        return "side"

    msg = f"Unknown camera mode '{_to2d}'"
    raise ValueError(msg)


def length(a: Vector3d) -> float:
    return sqrt(dotproduct(a, a))


def normalize(a: Vector3d) -> Vector3d:
    r = length(a)
    return Vector3d(a.x / r, a.y / r, a.z / r)


def equal_vectors(a: Vector3d, b: Vector3d) -> bool:
    a_rounded = f"{a.x:.4f},{a.y:.4f},{a.z:.4f}"
    b_rounded = f"{b.x:.4f},{b.y:.4f},{b.z:.4f}"
    return a_rounded == b_rounded


def line_length(x1: float, y1: float, x2: float, y2: float) -> float:
    return length(Vector3d(x2 - x1, y2 - y1, 0))


def subtract(p1: Point3d, p2: Point3d) -> Vector3d:
    return Vector3d(p1.x - p2.x, p1.y - p2.y, p1.z - p2.z)


def cross(a: Vector3d, b: Vector3d) -> Vector3d:
    return Vector3d(
        a.y * b.z - a.z * b.y,
        a.z * b.x - a.x * b.z,
        a.x * b.y - a.y * b.x,
    )


def dotproduct(a: Vector3d, b: Vector3d) -> float:
    return a.x * b.x + a.y * b.y + a.z * b.z


def is_inside(p: Point, line: Line) -> bool:
    a, b = line
    return (b.x - a.x) * (p.y - a.y) > (b.y - a.y) * (p.x - a.x)


def get_edges(polygon: Points) -> list[Line]:
    return list(pairwise(polygon[-1:] + polygon))


def line_intersection(line0: Line, line1: Line) -> Point | None:
    """
    calculate the point of intersection between two lines
    see {@link https://en.wikipedia.org/wiki/Line%E2%80%93line_intersection#Given_two_points_on_each_line|Wikipedia}
    """

    p1, p2 = line0
    p3, p4 = line1
    denominator = (p1.x - p2.x) * (p3.y - p4.y) - (p1.y - p2.y) * (p3.x - p4.x)

    if abs(denominator) < 0.0001:
        return None  # parallel lines

    numerator_x = (p1.x * p2.y - p1.y * p2.x) * (p3.x - p4.x) - (p1.x - p2.x) * (p3.x * p4.y - p3.y * p4.x)
    numerator_y = (p1.x * p2.y - p1.y * p2.x) * (p3.y - p4.y) - (p1.y - p2.y) * (p3.x * p4.y - p3.y * p4.x)

    x = numerator_x / denominator
    y = numerator_y / denominator

    return Point(x, y)


def clip_polygon(clipping_polygon: Points, subject_polygon: Points) -> Points:
    """
    @see {@link https://en.wikipedia.org/wiki/Sutherland%E2%80%93Hodgman_algorithm algorithm}
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


def clip_polygon2(clipping_polygon: Points, subject_polygon: Points, operation: str = "difference") -> list[Points]:
    result = _clip_polygon(subject_polygon, clipping_polygon, operation)
    return [[Point(x, y) for x, y in poly.points] for poly in result]


CAMERA: Vector3d = normalize(Vector3d(-1.0, -1.0, 1.0))

LIGHT: Vector3d = normalize(Vector3d(-1.0, 1.0, 1.0))


def get_3d_lighting(normal: Vector3d) -> tuple[float, float, bool]:
    camera = dotproduct(normal, CAMERA)
    light = dotproduct(normal, LIGHT)
    return camera, light, False


def get_plan_lighting(normal: Vector3d) -> tuple[float, float, bool]:  # noqa: ARG001
    return 0.0, 0.0, True


_get_lighting = get_3d_lighting


def get_lighting(normal: Vector3d) -> tuple[float, float, bool]:
    return _get_lighting(normal)


def point_rotator(
    angle: float, origin_x: float, origin_y: float, offset_x: float, offset_y: float
) -> Callable[[Point], Point]:
    cos_a = cos(radians(angle))
    sin_a = sin(radians(angle))

    def rotate(point: Point) -> Point:
        x1 = point.x - origin_x
        y1 = point.y - origin_y
        return Point(
            offset_x + x1 * cos_a - y1 * sin_a,
            offset_y + x1 * sin_a + y1 * cos_a,
        )

    return rotate
