from dataclasses import dataclass
from math import cos, radians, sin
from typing import Callable, Iterator, List, Optional, Tuple

from .geometry import line_length

Interpolator = Callable[[float], float]


class Profile:
    @dataclass
    class Point:
        x: float
        z: float

    def __init__(self, points: Optional[List[Point]] = None) -> None:
        self._points: List[Profile.Point] = points or []

    def __iter__(self) -> Iterator[Point]:
        yield from self._points

    def __bool__(self) -> bool:
        return bool(self._points)

    @classmethod
    def default(self, L: float, T: float) -> "Profile":
        return Profile(
            [
                Profile.Point(0, 0),
                Profile.Point(L, 0),
                Profile.Point(L, T),
                Profile.Point(0, T),
            ]
        )

    def mitre(self, T: float, left: float, right: float) -> None:
        # offset the point of rotation
        # length is base + hypotenuse of 60 degree triangle with height equal to the
        # board thickness
        hyp = T / sin(radians(left))
        offset_x = hyp * cos(radians(left))
        x1, y1 = self._points[0].x, self._points[1].z
        self._points[0] = Profile.Point(x1 + offset_x, y1)

        hyp = T / sin(radians(right))
        offset_x = hyp * cos(radians(right))
        x1, y1 = self._points[1].x, self._points[1].z
        self._points[1] = Profile.Point(x1 - offset_x, y1)

    def flip(self) -> None:
        a, b, c, d = self._points
        self._points = [
            Profile.Point(d.x, a.z),
            Profile.Point(c.x, b.z),
            Profile.Point(b.x, c.z),
            Profile.Point(a.x, d.z),
        ]

    def length(self) -> Tuple[float, float]:
        return line_length(
            self._points[0].x, self._points[0].z, self._points[1].x, self._points[1].z
        ), line_length(
            self._points[2].x, self._points[2].z, self._points[3].x, self._points[3].z
        )

    def interpolate(self, T: float) -> Tuple[Interpolator, Interpolator]:
        # interpolate x along profile
        def x1(z: float) -> float:
            return self._points[0].x + z * (self._points[3].x - self._points[0].x) / T

        def x2(z: float) -> float:
            return self._points[1].x + z * (self._points[2].x - self._points[1].x) / T

        return x1, x2

    def plan_points(
        self, x: float, y: float, angle: float
    ) -> List[Tuple[float, float]]:
        offset = self._points[0]
        points = [(p.x - offset.x, p.z - offset.z) for p in self._points]
        cos_a = cos(radians(angle))
        sin_a = sin(radians(angle))
        return [
            (
                x + x1 * cos_a - y1 * sin_a,
                y + x1 * sin_a + y1 * cos_a,
            )
            for (x1, y1) in points
        ]
