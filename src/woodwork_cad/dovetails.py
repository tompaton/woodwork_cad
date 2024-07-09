from dataclasses import dataclass, field
from math import radians, sin
from typing import Callable, Iterable, List, Optional

from .faces import Face
from .geometry import Point3d, Points3d
from .profile import Interpolator


# clip polygon needs to be offset from board by a tiny amount to avoid
# issues with "degenerate" polygons when clipping
def peturb(points: Points3d) -> Points3d:
    mid_x = sum(p.x for p in points) / len(points)
    mid_y = sum(p.y for p in points) / len(points)
    mid_z = sum(p.z for p in points) / len(points)

    def e(v: float, mid_v: float) -> float:
        if v < mid_v:
            return -0.01
        else:
            return 0.01

    return [
        Point3d(p.x + e(p.x, mid_x), p.y + e(p.y, mid_y), p.z + e(p.z, mid_z))
        for p in points
    ]


@dataclass
class End:
    right: bool
    dx: float
    points: Points3d = field(default_factory=list)


@dataclass
class PinX:
    right: bool
    points_f: Points3d = field(default_factory=list)
    points_s: Points3d = field(default_factory=list)

    def get_face(self, x1: Interpolator, x2: Interpolator, z: float) -> Optional[Face]:
        xz = x2 if self.right else x1
        return Face([Point3d(p.x + xz(z), p.y, z) for p in self.points_f], colour="red")

    def get_side(self, x1: Interpolator, x2: Interpolator, y: float) -> Optional[Face]:
        min_y = min(p.y for p in self.points_f)
        max_y = max(p.y for p in self.points_f)

        if min_y <= y <= max_y:
            xz = x2 if self.right else x1
            return Face(
                [Point3d(p.x + xz(p.z), y, p.z) for p in self.points_s], colour="red"
            )

        return None


@dataclass
class TailX:
    right: bool
    points_f: Points3d = field(default_factory=list)
    points_b: Points3d = field(default_factory=list)

    def get_face(self, x1: Interpolator, x2: Interpolator, z: float) -> Optional[Face]:
        xz = x2 if self.right else x1
        if z:
            return Face(
                [Point3d(p.x + xz(z), p.y, z) for p in self.points_b], colour="red"
            )
        else:
            return Face(
                [Point3d(p.x + xz(z), p.y, z) for p in self.points_f], colour="red"
            )

    def get_side(self, x1: Interpolator, x2: Interpolator, z: float) -> Optional[Face]:
        # can ignore this for now as pins don't extend to sides and we'll
        # assume any grooves are near the edge
        return None


class Dovetails:
    def __init__(self) -> None:
        self._pin_x: List[PinX] = []
        self._tail_x: List[TailX] = []
        self._ends: List[End] = []
        self.faces_L: List[Face] = []
        self.faces_R: List[Face] = []

    def __bool__(self) -> bool:
        return bool(self._ends)

    def add_pin(
        self,
        right: bool,
        x: float,
        y: float,
        base: float,
        pin_width: float,
        flare1: float,
        flare2: float,
        T: float,
    ) -> float:
        self.add_end(
            right,
            x,
            y,
            0,
            [0, -flare1, pin_width + flare2, pin_width],
            T,
        )
        return pin_width

    def add_pinx(
        self,
        right: bool,
        x: float,
        y: float,
        base: float,
        pin_width: float,
        flare1: float,
        flare2: float,
        T: float,
    ) -> float:
        self._pin_x.append(
            PinX(
                right,
                # face
                peturb(
                    [
                        Point3d(0, y, 0),
                        Point3d(0 + base, y - flare1, 0),
                        Point3d(0 + base, y + pin_width + flare2, 0),
                        Point3d(0, y + pin_width, 0),
                    ]
                ),
                # side
                peturb(
                    [
                        Point3d(0, y, 0),
                        Point3d(0 + base, y, 0),
                        Point3d(0 + base, y, T),
                        Point3d(0, y, T),
                    ]
                ),
            )
        )
        if flare1:
            self.add_face(
                right, 0, y, [0, base, base, 0], [0, -flare1, -flare1, 0], T, False
            )
        self.add_end(
            right,
            x,
            y,
            base,
            [-flare1, -flare1, pin_width + flare2, pin_width + flare2],
            T,
        )
        if flare2:
            self.add_face(
                right,
                0,
                y + pin_width,
                [0, base, base, 0],
                [0, flare2, flare2, 0],
                T,
                True,
            )
        return pin_width

    def add_tail(
        self,
        right: bool,
        x: float,
        y: float,
        base: float,
        tail_width: float,
        flare: float,
        T: float,
    ) -> float:
        self.add_end(right, x, y, 0, [0, 0, tail_width, tail_width], T)

        return tail_width

    def add_tailx(
        self,
        right: bool,
        x: float,
        y: float,
        base: float,
        tail_width: float,
        flare: float,
        T: float,
    ) -> float:
        self._tail_x.append(
            TailX(
                right,
                # front face
                peturb(
                    [
                        Point3d(0, y, 0),
                        Point3d(0 + base, y, 0),
                        Point3d(0 + base, y + tail_width, 0),
                        Point3d(0, y + tail_width, 0),
                    ]
                ),
                # back face
                peturb(
                    [
                        Point3d(0, y + flare, T),
                        Point3d(0 + base, y + flare, T),
                        Point3d(0 + base, y + tail_width - flare, T),
                        Point3d(0, y + tail_width - flare, T),
                    ]
                ),
            )
        )
        self.add_face(right, 0, y, [0, base, base, 0], [0, 0, flare, flare], T, False)
        self.add_end(right, x, y, base, [tail_width, tail_width - flare, flare, 0], T)
        self.add_face(
            right,
            0,
            y + tail_width,
            [0, base, base, 0],
            [0, 0, -flare, -flare],
            T,
            True,
        )
        return tail_width

    def add_end(
        self, right: bool, x: float, y: float, dx: float, dy: List[float], dz: float
    ) -> None:
        points = peturb(
            [
                Point3d(x, y + dy[0], 0),
                Point3d(x, y + dy[1], dz),
                Point3d(x, y + dy[2], dz),
                Point3d(x, y + dy[3], 0),
            ]
        )
        self._ends.append(End(right, dx, points))

    def add_face(
        self,
        right: bool,
        x: float,
        y: float,
        dx: List[float],
        dy: List[float],
        dz: float,
        reverse: bool,
        colour: str = "",
    ) -> None:
        faces = self.faces_R if right else self.faces_L
        face = Face(
            [
                Point3d(x + dx[0], y + dy[0], 0),
                Point3d(x + dx[1], y + dy[1], 0),
                Point3d(x + dx[2], y + dy[2], dz),
                Point3d(x + dx[3], y + dy[3], dz),
            ],
            colour,
        )
        if reverse != right:
            face.points.reverse()
        faces.append(face)

    def faces(
        self, x1: Interpolator, x2: Interpolator
    ) -> Callable[[float], Iterable[Face]]:
        def inner(z: float) -> Iterable[Face]:
            for pin in self._pin_x:
                if face := pin.get_face(x1, x2, z):
                    yield face
            for tail in self._tail_x:
                if face := tail.get_face(x1, x2, z):
                    yield face

        return inner

    def sides(
        self, x1: Interpolator, x2: Interpolator
    ) -> Callable[[float], Iterable[Face]]:
        def inner(y: float) -> Iterable[Face]:
            for pin in self._pin_x:
                if face := pin.get_side(x1, x2, y):
                    yield face
            for tail in self._tail_x:
                if face := tail.get_side(x1, x2, y):
                    yield face

        return inner

    def left_right(
        self, xz: Interpolator, side: Face, right: bool = False
    ) -> Iterable[Face]:
        clipped = False

        for end in self._ends:
            if end.right == right:
                clipped = True
                # yield Face(end.points, "red").offset(dx=end.dx)
                yield (
                    side.clip_end(Face(end.points, "red"))
                    .offset(dx=end.dx)
                    .offset_profile(xz)
                    .check_normal(side)
                )

        if not clipped:
            yield side

    def add_tails(
        self,
        tails: int,
        L: float,
        W: float,
        T: float,
        base: float,
        pin_width: float,
        angle: float,
        right: bool,
    ) -> None:
        x = L if right else 0
        base = -base if right else base
        y = 0.0

        # pin_width = height / (tails * 2 + 1)
        pin_width0 = 2 * pin_width
        tail_width = (W - 2 * pin_width0 - pin_width * (tails - 1)) / tails

        flare = abs(base) * sin(radians(angle))

        y += self.add_pinx(right, x, y, base, pin_width0, 0, flare, T)

        y += self.add_tail(right, x, y, base, tail_width, flare, T)

        for i in range(tails - 1):
            y += self.add_pinx(right, x, y, base, pin_width, flare, flare, T)

            y += self.add_tail(right, x, y, base, tail_width, flare, T)

        self.add_pinx(right, x, y, base, pin_width0, flare, 0, T)

    def add_pins(
        self,
        tails: int,
        L: float,
        W: float,
        T: float,
        base: float,
        pin_width: float,
        angle: float,
        right: bool,
    ) -> None:
        x = L if right else 0.0
        base = -base if right else base
        y = 0.0

        # pin_width = height / (tails * 2 + 1)
        pin_width0 = 2 * pin_width
        tail_width = (W - 2 * pin_width0 - pin_width * (tails - 1)) / tails

        flare = abs(base) * sin(radians(angle))

        y += self.add_pin(right, x, y, base, pin_width0, 0, flare, T)

        for i in range(tails):
            y += self.add_tailx(right, x, y, base, tail_width, flare, T)

            y += self.add_pin(right, x, y, base, pin_width, flare, flare, T)

        self._ends.pop()
        y -= pin_width

        y += self.add_pin(right, x, y, base, pin_width0, flare, 0, T)
