from collections.abc import Callable, Iterator
from dataclasses import dataclass, replace
from math import cos, radians, sin

from woodwork_cad.geometry import Point, Point3d, Points, clip_polygon, line_length

Interpolator = Callable[[float, float], float]


@dataclass
class ProfilePoint:
    x: float
    z: float


class Profile:
    def __init__(
        self,
        points: list[ProfilePoint] | None = None,
        shape: Points | None = None,
    ) -> None:
        self._points: list[ProfilePoint] = points or []
        self._shape: Points = shape or []

    def __iter__(self) -> Iterator[ProfilePoint]:
        yield from self._points

    def __bool__(self) -> bool:
        return bool(self._points)

    @classmethod
    def default(cls, L: float, W: float, T: float) -> "Profile":
        return cls(
            [
                ProfilePoint(0, 0),
                ProfilePoint(L, 0),
                ProfilePoint(L, T),
                ProfilePoint(0, T),
            ],
            [
                Point(0, 0),
                Point(L, 0),
                Point(L, W),
                Point(0, W),
            ],
        )

    def cut(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        L: float,
        T: float,
        *,
        right: bool,
    ) -> "Profile":
        if right:
            # clip bottom left
            clip = [
                Point(x1, y1 - 1),
                Point(10000, y1 - 1),
                Point(10000, y2 + 1),
                Point(x2, y2 + 1),
            ]
        else:
            # clip bottom right
            clip = [
                Point(-10000, y1 - 1),
                Point(x1, y1 - 1),
                Point(x2, y2 + 1),
                Point(-10000, y2 + 1),
            ]
        shape2 = clip_polygon(clip, [replace(p) for p in self._shape])
        if shape2:
            min_x = min(p.x for p in shape2)
            return Profile(
                [
                    ProfilePoint(0, 0),
                    ProfilePoint(L, 0),
                    ProfilePoint(L, T),
                    ProfilePoint(0, T),
                ],
                [p2.offset(dx=-min_x) for p2 in shape2],
            )

        return Profile()

    def rip(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        L: float,
        T: float,
        *,
        bottom: bool,
    ) -> "Profile":
        if bottom:
            # clip bottom
            clip = [
                Point(x1 - 1, y1),
                Point(x2 + 1, y2),
                Point(x2 + 1, 10000),
                Point(x1 - 1, 10000),
            ]
        else:
            # clip top
            clip = [
                Point(x1 - 1, -10000),
                Point(x2 + 1, -10000),
                Point(x2 + 1, y2),
                Point(x1 - 1, y1),
            ]
        shape2 = clip_polygon(clip, [replace(p) for p in self._shape])
        if shape2:
            min_y = min(p.y for p in shape2)
            if not bottom:
                shape2.append(shape2.pop(0))
            return Profile(
                [
                    ProfilePoint(0, 0),
                    ProfilePoint(L, 0),
                    ProfilePoint(L, T),
                    ProfilePoint(0, T),
                ],
                [p2.offset(dy=-min_y) for p2 in shape2],
            )

        return Profile()

    def mitre(self, T: float, left: float, right: float) -> None:
        # offset the point of rotation
        # length is base + hypotenuse of 60 degree triangle with height equal to the
        # board thickness
        hyp = T / sin(radians(left))
        offset_x = hyp * cos(radians(left))
        x1, y1 = self._points[0].x, self._points[1].z
        self._points[0] = ProfilePoint(x1 + offset_x, y1)

        hyp = T / sin(radians(right))
        offset_x = hyp * cos(radians(right))
        x1, y1 = self._points[1].x, self._points[1].z
        self._points[1] = ProfilePoint(x1 - offset_x, y1)

    def flip(self) -> None:
        a, b, c, d = self._points
        self._points = [
            ProfilePoint(d.x, a.z),
            ProfilePoint(c.x, b.z),
            ProfilePoint(b.x, c.z),
            ProfilePoint(a.x, d.z),
        ]

    def length(self) -> tuple[float, float]:
        return line_length(self._points[0].x, self._points[0].z, self._points[1].x, self._points[1].z), line_length(
            self._points[2].x, self._points[2].z, self._points[3].x, self._points[3].z
        )

    def length2(self) -> tuple[float, float]:
        return line_length(self._shape[0].x, self._shape[0].y, self._shape[1].x, self._shape[1].y), line_length(
            self._shape[2].x, self._shape[2].y, self._shape[3].x, self._shape[3].y
        )

    def interpolate(self, T: float) -> tuple[Interpolator, Interpolator]:
        # interpolate x along profile or shape (not both for now...)

        def x1(y: float, z: float) -> float:
            if self._points[0].x == self._points[3].x and len(self._shape) >= 4:
                return interpolate(
                    y,
                    self._shape[0].x,
                    self._shape[3].x,
                    self._shape[0].y,
                    self._shape[3].y,
                )

            return interpolate(z, self._points[0].x, self._points[3].x, 0.0, T)

        def x2(y: float, z: float) -> float:
            if self._points[1].x == self._points[2].x and len(self._shape) >= 4:
                return interpolate(
                    y,
                    self._shape[1].x,
                    self._shape[2].x,
                    self._shape[1].y,
                    self._shape[2].y,
                )

            return interpolate(z, self._points[1].x, self._points[2].x, 0.0, T)

        return x1, x2

    @property
    def origin(self) -> Point3d:
        offset = self._points[0]
        return Point3d(offset.x, 0.0, offset.z)

    @property
    def mate(self) -> Point3d:
        offset = self._points[1]
        return Point3d(offset.x, 0.0, offset.z)


def interpolate(z: float, x1: float, x2: float, z1: float, z2: float) -> float:
    if z2 - z1:
        return x1 + z * (x2 - x1) / (z2 - z1)

    return x1
