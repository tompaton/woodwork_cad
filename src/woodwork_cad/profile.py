from dataclasses import dataclass
from math import cos, radians, sin
from typing import Callable, Iterator, List, Optional, Tuple

from .geometry import Point3d, line_length

Interpolator = Callable[[float, float], float]


@dataclass
class ProfilePoint:
    x: float
    z: float


class Profile:
    def __init__(self, points: Optional[List[ProfilePoint]] = None) -> None:
        self._points: List[ProfilePoint] = points or []

    def __iter__(self) -> Iterator[ProfilePoint]:
        yield from self._points

    def __bool__(self) -> bool:
        return bool(self._points)

    @classmethod
    def default(self, L: float, T: float) -> "Profile":
        return Profile(
            [
                ProfilePoint(0, 0),
                ProfilePoint(L, 0),
                ProfilePoint(L, T),
                ProfilePoint(0, T),
            ]
        )

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

    def length(self) -> Tuple[float, float]:
        return line_length(
            self._points[0].x, self._points[0].z, self._points[1].x, self._points[1].z
        ), line_length(
            self._points[2].x, self._points[2].z, self._points[3].x, self._points[3].z
        )

    def interpolate(self, T: float) -> Tuple[Interpolator, Interpolator]:
        # interpolate x along profile
        def x1(y: float, z: float) -> float:
            return self._points[0].x + z * (self._points[3].x - self._points[0].x) / T

        def x2(y: float, z: float) -> float:
            return self._points[1].x + z * (self._points[2].x - self._points[1].x) / T

        return x1, x2

    @property
    def origin(self) -> Point3d:
        offset = self._points[0]
        return Point3d(offset.x, 0.0, offset.z)

    @property
    def mate(self) -> Point3d:
        offset = self._points[1]
        return Point3d(offset.x, 0.0, offset.z)
