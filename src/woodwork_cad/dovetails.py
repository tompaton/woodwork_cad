from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from math import radians, sin

from woodwork_cad.faces import Face
from woodwork_cad.geometry import Point3d, Points3d
from woodwork_cad.profile import Interpolator


# clip polygon needs to be offset from board by a tiny amount to avoid
# issues with "degenerate" polygons when clipping
def peturb(points: Points3d) -> Points3d:
    mid_x = sum(p.x for p in points) / len(points)
    mid_y = sum(p.y for p in points) / len(points)
    mid_z = sum(p.z for p in points) / len(points)

    def e(v: float, mid_v: float) -> float:
        if v < mid_v:
            return -0.01

        return 0.01

    return [Point3d(p.x + e(p.x, mid_x), p.y + e(p.y, mid_y), p.z + e(p.z, mid_z)) for p in points]


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

    def get_face(self, x1: Interpolator, x2: Interpolator, z: float) -> Face | None:
        xz = x2 if self.right else x1
        return Face([Point3d(p.x + xz(p.y, z), p.y, z) for p in self.points_f], colour="red")

    def get_side(self, x1: Interpolator, x2: Interpolator, y: float) -> Face | None:
        min_y = min(p.y for p in self.points_f)
        max_y = max(p.y for p in self.points_f)

        if min_y <= y <= max_y:
            xz = x2 if self.right else x1
            return Face([Point3d(p.x + xz(y, p.z), y, p.z) for p in self.points_s], colour="red")

        return None


@dataclass
class TailX:
    right: bool
    points_f: Points3d = field(default_factory=list)
    points_b: Points3d = field(default_factory=list)

    def get_face(self, x1: Interpolator, x2: Interpolator, z: float) -> Face | None:
        xz = x2 if self.right else x1
        if z:
            return Face([Point3d(p.x + xz(p.y, z), p.y, z) for p in self.points_b], colour="red")

        return Face([Point3d(p.x + xz(p.y, z), p.y, z) for p in self.points_f], colour="red")

    def get_side(self, x1: Interpolator, x2: Interpolator, z: float) -> Face | None:  # noqa: ARG002
        # can ignore this for now as pins don't extend to sides and we'll
        # assume any grooves are near the edge
        return None


class Dovetails:
    def __init__(self) -> None:
        self._pin_x: list[PinX] = []
        self._tail_x: list[TailX] = []
        self._ends: list[End] = []
        self.faces_L: list[Face] = []
        self.faces_R: list[Face] = []

        self.pin_ratio: float = 1.0
        self.pin1_ratio: float = 0.5

    def __bool__(self) -> bool:
        return bool(self._ends)

    def add_pin(
        self,
        x: float,
        y: float,
        base: float,  # noqa: ARG002
        pin_width: float,
        flare1: float,
        flare2: float,
        T: float,
        *,
        right: bool,
    ) -> float:
        self.add_end(
            x,
            y,
            0,
            [0, -flare1, pin_width + flare2, pin_width],
            T,
            right=right,
        )
        return pin_width

    def add_pinx(
        self,
        x: float,
        y: float,
        base: float,
        pin_width: float,
        flare1: float,
        flare2: float,
        T: float,
        *,
        right: bool,
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
                0,
                y,
                [0, base, base, 0],
                [0, -flare1, -flare1, 0],
                T,
                right=right,
                reverse=False,
            )
        self.add_end(
            x,
            y,
            base,
            [-flare1, -flare1, pin_width + flare2, pin_width + flare2],
            T,
            right=right,
        )
        if flare2:
            self.add_face(
                0,
                y + pin_width,
                [0, base, base, 0],
                [0, flare2, flare2, 0],
                T,
                right=right,
                reverse=True,
            )
        return pin_width

    def add_tail(
        self,
        x: float,
        y: float,
        base: float,  # noqa: ARG002
        tail_width: float,
        flare: float,  # noqa: ARG002
        T: float,
        *,
        right: bool,
    ) -> float:
        self.add_end(x, y, 0, [0, 0, tail_width, tail_width], T, right=right)

        return tail_width

    def add_tailx(
        self,
        x: float,
        y: float,
        base: float,
        tail_width: float,
        flare: float,
        T: float,
        *,
        right: bool,
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
        self.add_face(
            0,
            y,
            [0, base, base, 0],
            [0, 0, flare, flare],
            T,
            right=right,
            reverse=False,
        )
        self.add_end(x, y, base, [tail_width, tail_width - flare, flare, 0], T, right=right)
        self.add_face(
            0,
            y + tail_width,
            [0, base, base, 0],
            [0, 0, -flare, -flare],
            T,
            right=right,
            reverse=True,
        )
        return tail_width

    def add_end(self, x: float, y: float, dx: float, dy: list[float], dz: float, *, right: bool) -> None:
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
        x: float,
        y: float,
        dx: list[float],
        dy: list[float],
        dz: float,
        *,
        right: bool,
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

    def faces(self, x1: Interpolator, x2: Interpolator) -> Callable[[float], Iterable[Face]]:
        def inner(z: float) -> Iterable[Face]:
            for pin in self._pin_x:
                if face := pin.get_face(x1, x2, z):
                    yield face
            for tail in self._tail_x:
                if face := tail.get_face(x1, x2, z):
                    yield face

        return inner

    def sides(self, x1: Interpolator, x2: Interpolator) -> Callable[[float], Iterable[Face]]:
        def inner(y: float) -> Iterable[Face]:
            for pin in self._pin_x:
                if face := pin.get_side(x1, x2, y):
                    yield face
            for tail in self._tail_x:
                if face := tail.get_side(x1, x2, y):
                    yield face

        return inner

    def left_right(self, xz: Interpolator, side: Face, *, right: bool = False) -> Iterable[Face]:
        clipped = False

        for end in self._ends:
            if end.right == right:
                clipped = True
                # yield Face(end.points, "red").offset(dx=end.dx)
                yield (side.clip_end(Face(end.points, "red")).offset(dx=end.dx).offset_profile(xz).check_normal(side))

        if not clipped:
            yield side

    def add_tails(
        self,
        tails: int,
        L: float,
        W: float,
        T: float,
        base: float,
        angle: float,
        *,
        right: bool,
    ) -> None:
        x = L if right else 0
        base = -base if right else base
        y = 0.0

        tail_width, pin_width, pin_width0 = self.get_widths(W, tails)

        flare = abs(base) * sin(radians(angle))

        y += self.add_pinx(x, y, base, pin_width0, 0, flare, T, right=right)

        y += self.add_tail(x, y, base, tail_width, flare, T, right=right)

        for _i in range(tails - 1):
            y += self.add_pinx(x, y, base, pin_width, flare, flare, T, right=right)

            y += self.add_tail(x, y, base, tail_width, flare, T, right=right)

        self.add_pinx(x, y, base, pin_width0, flare, 0, T, right=right)

    def add_pins(
        self,
        tails: int,
        L: float,
        W: float,
        T: float,
        base: float,
        angle: float,
        *,
        right: bool,
    ) -> None:
        x = L if right else 0.0
        base = -base if right else base
        y = 0.0

        tail_width, pin_width, pin_width0 = self.get_widths(W, tails)

        flare = abs(base) * sin(radians(angle))

        y += self.add_pin(x, y, base, pin_width0, 0, flare, T, right=right)

        for _i in range(tails):
            y += self.add_tailx(x, y, base, tail_width, flare, T, right=right)

            y += self.add_pin(x, y, base, pin_width, flare, flare, T, right=right)

        self._ends.pop()
        y -= pin_width

        y += self.add_pin(x, y, base, pin_width0, flare, 0, T, right=right)

    def get_widths(self, height: float, tails: int) -> tuple[float, float, float]:
        tail_width = height / (tails + 2 * self.pin1_ratio * self.pin_ratio + (tails - 1) * self.pin_ratio)
        pin_width = tail_width * self.pin_ratio
        pin1_width = pin_width * self.pin1_ratio

        return tail_width, pin_width, pin1_width
