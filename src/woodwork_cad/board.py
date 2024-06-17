from dataclasses import dataclass, field
from math import cos, radians, sin, sqrt
from typing import Callable, Iterable, Iterator, List, Optional, Tuple

from .svg import Point3d, Points, Points3d, SVGCanvas

DEBUG = False

Interpolator = Callable[[float], float]

Vector3d = Tuple[float, float, float]


def length(a: Vector3d) -> float:
    return sqrt(sum(a1 * a2 for a1, a2 in zip(a, a)))


def normalize(a: Vector3d) -> Vector3d:
    r = length(a)
    return (a[0] / r, a[1] / r, a[2] / r)


CAMERA: Vector3d = normalize((1.0, 1.0, -1.0))
LIGHT: Vector3d = normalize((1.0, -1.0, -1.0))


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


class Cuts:
    @dataclass
    class Cut:
        op: str
        x1: float
        y1: float
        x2: float
        y2: float
        label: str
        lx: float
        ly: float
        colour: str
        fill: str

    def __init__(self, cuts: Optional[List[Cut]] = None) -> None:
        self._cuts: List[Cuts.Cut] = cuts or []

    def __iter__(self) -> Iterator[Cut]:
        yield from self._cuts

    def add(
        self,
        op: str,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        label: str = "",
        lx: float = 0,
        ly: float = 0,
    ):
        if op == "cut":
            colour = "green"
        elif op == "rip":
            colour = "blue"
        else:
            colour = "rgba(255,0,0,0.25)"

        if op == "cut":
            fill = "rgba(0,255,0,0.25)"
        elif op == "rip":
            fill = "rgba(0,0,255,0.25)"
        else:
            fill = "rgba(255,0,0,0.25)"

        self._cuts.append(Cuts.Cut(op, x1, y1, x2, y2, label, lx, ly, colour, fill))


class Shades:
    @dataclass
    class Shade:
        y1: float
        y2: float
        colour: str

    def __init__(self, shades: Optional[List[Shade]] = None) -> None:
        self._shades: List[Shades.Shade] = shades or []

    def __iter__(self) -> Iterator[Shade]:
        yield from self._shades

    def add(self, y1: float, y2: float, colour: str) -> None:
        self._shades.append(Shades.Shade(y1, y2, colour))

    def extend(self, other: "Shades") -> None:
        self._shades.extend(other._shades)

    def select(self, min_y: float, max_y: float, offset_y: float = 0) -> "Shades":
        return Shades(
            [
                Shades.Shade(
                    max(s.y1, min_y) + offset_y, min(s.y2, max_y) + offset_y, s.colour
                )
                for s in self._shades
                if s.y1 < max_y and s.y2 > min_y
            ]
        )


class Grooves:
    @dataclass
    class Groove:
        y1: float
        y2: float
        depth: float
        face: bool

    @dataclass(order=True)
    class Flat:
        z: float
        y1: float
        y2: float

    @dataclass
    class Side:
        y: float
        z1: float
        z2: float

    def __init__(self, grooves: Optional[List[Groove]] = None) -> None:
        self._grooves: List[Grooves.Groove] = grooves or []

    def add(self, y: float, height: float, depth: float, face: bool = True) -> None:
        self._grooves.append(Grooves.Groove(y, y + height, depth, face))

    def select(self, min_y: float, max_y: float, offset_y: float = 0) -> "Grooves":
        return Grooves(
            [
                Grooves.Groove(
                    max(groove.y1, min_y) + offset_y,
                    min(groove.y2, max_y) + offset_y,
                    groove.depth,
                    groove.face,
                )
                for groove in self._grooves
                if groove.y1 < max_y and groove.y2 > min_y
            ]
        )

    def flats(self, W: float, T: float, face: bool) -> Iterable[Flat]:
        y0 = 0.0
        for groove in self._grooves:
            if groove.face == face:
                yield Grooves.Flat(0.0 if face else T, y0, groove.y1)
                yield Grooves.Flat(
                    groove.depth if face else T - groove.depth,
                    groove.y1,
                    groove.y2,
                )
                y0 = groove.y2
        yield Grooves.Flat(0.0 if face else T, y0, W)

    def sides(self, T: float, top: bool, face: bool) -> Iterable[Side]:
        for groove in self._grooves:
            if top:
                if groove.face and face:
                    yield Grooves.Side(groove.y2, 0.0, groove.depth)
                if not groove.face and not face:
                    yield Grooves.Side(groove.y2, T - groove.depth, T)
            else:
                if groove.face and face:
                    yield Grooves.Side(groove.y1, 0.0, groove.depth)
                if not groove.face and not face:
                    yield Grooves.Side(groove.y1, T - groove.depth, T)


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


class Defect:
    def offset(self, offset_x: float, offset_y: float) -> "Defect":
        raise NotImplementedError

    def visible(self, offset_x: float, offset_y: float, L: float, W: float) -> bool:
        raise NotImplementedError

    def draw(self, canvas: SVGCanvas, x: float, y: float) -> None:
        raise NotImplementedError


class Defects:
    def __init__(self, defects: Optional[List[Defect]] = None) -> None:
        self._defects = defects or []

    def __iter__(self) -> Iterator[Defect]:
        yield from self._defects

    def add(self, defect: Defect) -> None:
        self._defects.append(defect)

    def extend(self, other: "Defects") -> None:
        self._defects.extend(other._defects)

    def select(self, offset_x: float, offset_y: float) -> "Defects":
        return Defects([defect.offset(offset_x, offset_y) for defect in self._defects])


@dataclass
class Hole(Defect):
    x: float
    y: float
    r: float = 5

    def offset(self, offset_x: float, offset_y: float) -> "Hole":
        return Hole(self.x + offset_x, self.y + offset_y, self.r)

    def visible(self, offset_x: float, offset_y: float, L: float, W: float) -> bool:
        return (offset_x < self.x < offset_x + L) and (offset_y < self.y < offset_y + W)

    def draw(self, canvas: SVGCanvas, x: float, y: float) -> None:
        canvas.circle(x + self.x, y + self.y, self.r, "orange")


@dataclass
class Notch(Defect):
    x1: float
    y1: float
    x2: float
    y2: float

    def offset(self, offset_x: float, offset_y: float) -> "Notch":
        return Notch(
            self.x1 + offset_x,
            self.y1 + offset_y,
            self.x2 + offset_x,
            self.y2 + offset_y,
        )

    def visible(self, offset_x: float, offset_y: float, L: float, W: float) -> bool:
        return not (
            self.x2 < offset_x
            or self.x1 > offset_x + L
            or self.y2 < offset_y
            or self.y1 > offset_y + W
        )

    def draw(self, canvas: SVGCanvas, x: float, y: float) -> None:
        canvas.rect(
            x + self.x1, y + self.y1, self.x2 - self.x1, self.y2 - self.y1, "orange"
        )


@dataclass
class Face:
    points: Points3d

    def reverse(self) -> "Face":
        self.points.reverse()
        return self

    def draw(self, canvas: SVGCanvas, offset_x: float, offset_y: float) -> None:
        a = subtract(self.points[1], self.points[0])
        b = subtract(self.points[2], self.points[1])
        normal = normalize(cross(a, b))

        dash = ""

        camera = dotproduct(normal, CAMERA)
        light = dotproduct(normal, LIGHT)

        # check angle with camera to find back faces
        if camera > 0:
            dash = "2"
            colour = "gray"
            fill = "none"
        else:
            # angle with camera to determine line colour
            if camera < -0.5:
                colour = "black"
            else:
                colour = "silver"

            # angle with light determine to colour
            if light < 0.5:
                fill = "rgba(255,255,255,0.75)"
            else:
                fill = "rgba(192,192,192,0.75)"

        canvas.polyline3d(
            colour,
            [(x + offset_x, y + offset_y, z) for x, y, z in self.points],
            fill=fill,
            closed=True,
            stroke_dasharray=dash,
        )
        if DEBUG:
            # draw normal from face centroid
            x, y, z = self.centroid
            canvas.polyline3d(
                "red",
                [
                    (x + offset_x, y + offset_y, z),
                    (
                        x + offset_x - 15 * normal[0],
                        y + offset_y - 15 * normal[1],
                        z - 15 * normal[2],
                    ),
                ],
                fill="none",
            )

    @property
    def centroid(self) -> Vector3d:
        min_x = min(x for x, y, z in self.points)
        max_x = max(x for x, y, z in self.points)
        min_y = min(y for x, y, z in self.points)
        max_y = max(y for x, y, z in self.points)
        min_z = min(z for x, y, z in self.points)
        max_z = max(z for x, y, z in self.points)
        return ((max_x + min_x) / 2, (max_y + min_y) / 2, (max_z + min_z) / 2)


@dataclass
class Board:
    L: float
    W: float
    T: float

    parent: Optional["Board"] = None
    offset_x: float = 0
    offset_y: float = 0

    cuts: Cuts = field(default_factory=Cuts)

    _defects: Optional[Defects] = None
    _profile: Profile = field(default_factory=Profile)

    label: str = ""
    shades: Shades = field(default_factory=Shades)
    grooves: Grooves = field(default_factory=Grooves)

    def __str__(self) -> str:
        return f"{self.L} x {self.W} x {self.T}"

    @property
    def area(self):
        return self.L * self.W

    @property
    def aspect(self):
        return self.L / self.W

    @property
    def defects(self) -> Defects:
        if not self._defects:
            self._defects = Defects()

            if self.parent:
                for defect in self.parent.defects:
                    if defect.visible(self.offset_x, self.offset_y, self.L, self.W):
                        self._defects.add(defect.offset(-self.offset_x, -self.offset_y))

        return self._defects

    @property
    def profile(self) -> Profile:
        if not self._profile:
            self._profile = Profile.default(self.L, self.T)
        return self._profile

    def shade(self, colour: str) -> "Board":
        self.shades.add(0, self.W, colour)
        return self

    def add_cut(
        self,
        op: str,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        label: str = "",
        lx: float = 0,
        ly: float = 0,
    ):
        self.cuts.add(op, x1, y1, x2, y2, label, lx, ly)
        if self.parent:
            self.parent.add_cut(
                op,
                x1 + self.offset_x,
                y1 + self.offset_y,
                x2 + self.offset_x,
                y2 + self.offset_y,
                label,
                lx + self.offset_x,
                ly + self.offset_y,
            )

    def cut(self, length: float, kerf: float = 5):
        self.add_cut("cut", length, 0, length + kerf, self.W)
        return [
            Board(
                length,
                self.W,
                self.T,
                self,
                0,
                0,
                shades=self.shades.select(0, self.W),
                grooves=self.grooves.select(0, self.W),
            ),
            Board(
                self.L - length - kerf,
                self.W,
                self.T,
                self,
                length + kerf,
                0,
                shades=self.shades.select(0, self.W),
                grooves=self.grooves.select(0, self.W),
            ),
        ]

    def rip(self, width: float, kerf: float = 5):
        self.add_cut("rip", 0, width, self.L, width + kerf)
        return [
            Board(
                self.L, width, self.T, self, 0, 0, shades=self.shades.select(0, width)
            ),
            Board(
                self.L,
                self.W - width - kerf,
                self.T,
                self,
                0,
                width + kerf,
                shades=self.shades.select(width + kerf, self.W),
            ),
        ]

    def waste(self):
        self.add_cut("waste", 0, 0, self.L, self.W)
        return []

    def cut_waste(self, length: float):
        self.add_cut("cut_waste", 0, 0, length, self.W)
        return [
            Board(self.L - length, self.W, self.T, self, length, 0),
        ]

    def mitre(self, left: float, right: float) -> None:
        self.profile.mitre(self.T, left, right)

    def flip_profile(self) -> None:
        self.profile.flip()
        self.L = self.profile.length()[0]

    def dado(self, x: float, width: float, depth: float, face: bool = True) -> None:
        raise NotImplementedError

    def draw_board(self, canvas: SVGCanvas, x: float, y: float) -> None:
        x1, x2 = self.profile.interpolate(self.T)

        # draw all faces separately from back to front to do basic hidden line removal
        for face in self._get_faces(x1, x2):
            face.draw(canvas, x, y)

        self._draw_shade(canvas, x, y, x1, x2)

        for defect in self.defects:
            defect.draw(canvas, x, y)

        self._draw_cuts(canvas, x, y)

    def _get_faces(self, x1: Interpolator, x2: Interpolator) -> Iterable[Face]:
        yield self._get_top_bottom(x1, x2, Grooves.Side(0.0, 0.0, self.T)).reverse()

        yield from self._get_back(x1, x2, grooves=False)

        yield self._get_left_right(x1)
        for side in self.grooves.sides(self.T, top=True, face=False):
            yield self._get_top_bottom(x1, x2, side).reverse()

        for side in self.grooves.sides(self.T, top=False, face=False):
            yield self._get_top_bottom(x1, x2, side)

        yield from self._get_back(x1, x2, grooves=True)

        yield from self._get_front(x1, x2, grooves=True)

        for side in self.grooves.sides(self.T, top=True, face=True):
            yield self._get_top_bottom(x1, x2, side).reverse()

        for side in self.grooves.sides(self.T, top=False, face=True):
            yield self._get_top_bottom(x1, x2, side)

        yield self._get_top_bottom(x1, x2, Grooves.Side(self.W, 0.0, self.T))

        yield self._get_left_right(x2).reverse()
        yield from self._get_front(x1, x2, grooves=False)

    def _get_top_bottom(
        self,
        x1: Interpolator,
        x2: Interpolator,
        side: Grooves.Side,
    ) -> Face:
        return Face(
            [
                (x1(side.z1), side.y, side.z1),
                (x2(side.z1), side.y, side.z1),
                (x2(side.z2), side.y, side.z2),
                (x1(side.z2), side.y, side.z2),
            ],
        )

    def _get_left_right(self, xz: Interpolator) -> Face:
        points: Points3d = []

        for flat in self.grooves.flats(self.W, self.T, face=True):
            points.extend(
                [
                    (xz(flat.z), flat.y1, flat.z),
                    (xz(flat.z), flat.y2, flat.z),
                ]
            )

        for flat in reversed(list(self.grooves.flats(self.W, self.T, face=False))):
            points.extend(
                [
                    (xz(flat.z), flat.y2, flat.z),
                    (xz(flat.z), flat.y1, flat.z),
                ]
            )

        return Face(points)

    def _get_front(
        self,
        x1: Interpolator,
        x2: Interpolator,
        grooves: bool,
    ) -> Iterable[Face]:
        for flat in sorted(self.grooves.flats(self.W, self.T, face=True), reverse=True):
            if (grooves and flat.z == 0.0) or (not grooves and flat.z != 0.0):
                continue

            yield Face(
                [
                    (x1(flat.z), flat.y1, flat.z),
                    (x2(flat.z), flat.y1, flat.z),
                    (x2(flat.z), flat.y2, flat.z),
                    (x1(flat.z), flat.y2, flat.z),
                ],
            )

    def _get_back(
        self,
        x1: Interpolator,
        x2: Interpolator,
        grooves: bool,
    ) -> Iterable[Face]:
        for flat in sorted(
            self.grooves.flats(self.W, self.T, face=False), reverse=True
        ):
            if (grooves and flat.z == self.T) or (not grooves and flat.z != self.T):
                continue

            yield Face(
                [
                    (x1(flat.z), flat.y1, flat.z),
                    (x1(flat.z), flat.y2, flat.z),
                    (x2(flat.z), flat.y2, flat.z),
                    (x2(flat.z), flat.y1, flat.z),
                ],
            )

    def _draw_shade(
        self, canvas: SVGCanvas, x: float, y: float, x1: Interpolator, x2: Interpolator
    ) -> None:
        for shade in self.shades:
            canvas.polyline3d(
                "none",
                [
                    (x + x1(0), y + shade.y1, 0),
                    (x + x2(0), y + shade.y1, 0),
                    # extend shading around thickness
                    (x + x2(self.T), y + shade.y1, self.T),
                    (x + x2(self.T), y + shade.y2, self.T),
                    (x + x2(0), y + shade.y2, 0),
                    (x + x1(0), y + shade.y2, 0),
                ],
                fill=shade.colour,
                closed=True,
            )

    def _draw_cuts(self, canvas: SVGCanvas, x: float, y: float) -> None:
        order = 0
        for cut in self.cuts:
            if cut.op:
                if cut.y2 == self.W:
                    points = [
                        (x + cut.x1, y + cut.y1, 0),
                        (x + cut.x2 + 1, y + cut.y1, 0),
                        (x + cut.x2 + 1, y + cut.y2, 0),
                        # continue around edge
                        (x + cut.x2 + 1, y + cut.y2, self.T),
                        (x + cut.x1, y + cut.y2, self.T),
                        (x + cut.x1, y + cut.y2, 0),
                    ]
                else:
                    points = [
                        (x + cut.x1, y + cut.y1, 0),
                        (x + cut.x2 + 1, y + cut.y1, 0),
                        (x + cut.x2 + 1, y + cut.y2, 0),
                        (x + cut.x1, y + cut.y2, 0),
                    ]

                canvas.polyline3d(cut.colour, points, fill=cut.fill, closed=True)

                if cut.op != "waste":
                    order += 1
                    canvas.text(
                        x + cut.x1 + 10,
                        y + cut.y1 + 10,
                        "left",
                        content=str(order),
                        style="",
                    )

            if cut.label:
                canvas.text(
                    x + cut.lx, y + cut.ly, "start", content=cut.label, style=""
                )

        if self.label:
            canvas.text(
                x + self.L / 2,
                y + self.W / 2,
                content=self.label,
                style="",
            )

    def draw_plan(
        self,
        canvas: SVGCanvas,
        x: float,
        y: float,
        angle: float,
        colour: str = "black",
    ) -> Tuple[float, float]:
        rotated = self.profile.plan_points(x, y, angle)
        canvas.polyline(colour, rotated, closed=True)
        return rotated[1]


def draw_boards(canvas: SVGCanvas, x: float, y: float, boards: list[Board]) -> Points:
    points = []
    for board in boards:
        board.draw_board(canvas, x, y)
        points.append((x, y))
        y += board.W + 2 * board.T
    return points


def cut(length: float, kerf: float = 5):
    def operation(board: Board):
        return board.cut(length, kerf)

    return operation


def rip(width: float, kerf: float = 5):
    def operation(board: Board):
        return board.rip(width, kerf)

    return operation


def waste(board: Board):
    return board.waste()


def cut_waste(length: float):
    def operation(board: Board):
        return board.cut_waste(length)

    return operation


def joint(*boards: Board, label: str = ""):
    if not all(
        board1.L == board2.L and board1.T == board2.T
        for board1, board2 in zip(boards, boards[1:])
    ):
        raise ValueError("Board length and thickness must match to be joined")

    defects = Defects()
    shade = Shades()
    offset_y = 0.0
    for board in boards:
        defects.extend(board.defects.select(0, offset_y))
        shade.extend(board.shades.select(0, board.W, offset_y))
        offset_y += board.W

    return Board(
        boards[0].L,
        sum(board.W for board in boards),
        boards[0].T,
        label=label,
        _defects=defects,
        shades=shade,
    )


def process(*operations):
    def inner(board: Board):
        result = [board]
        for operation in operations:
            board = result.pop()
            result.extend(operation(board))
        return result

    return inner


def process_first(*operations):
    def inner(board: Board):
        result, remainder = process(operations[0])(board)
        return process(*operations[1:])(result) + [remainder]

    return inner


def process_all(boards: list[Board], *operations):
    result = []
    for board in boards:
        result.extend(process(*operations)(board))
    return result


def joint2(boards: list[Board], *indexes: int, label: str = ""):
    if len(indexes) < 2:
        raise ValueError("Need 2 or more boards to join")
    if not all(index2 > index1 for index1, index2 in zip(indexes, indexes[1:])):
        raise ValueError("Boards must be joined in order")
    boards2 = []
    for index in reversed(indexes):
        boards2.append(boards.pop(index))
    boards.append(joint(*boards2, label=label))


def label_all(boards: list[Board], *labels):
    for board, label in zip(boards, labels):
        board.label = label
        if board.parent:
            board.parent.add_cut(
                "",
                0,
                0,
                board.L,
                board.W,
                label,
                board.L / 2 + board.offset_x,
                board.W / 2 + board.offset_y,
            )


def cube_net(
    boards: list[Board],
    top: int,
    left: int,
    front: int,
    right: int,
    back: int,
    bottom: int,
):
    all_sides = [top, left, front, right, back, bottom]
    if not len({boards[side].T for side in all_sides}) == 1:
        raise ValueError("Cube sides must have equal thickness")

    if not boards[top].L == boards[front].L == boards[bottom].L == boards[back].L:
        raise ValueError("Cube top, front, bottom and back must be the same length")
    if not boards[top].W == boards[left].L == boards[bottom].W == boards[right].L:
        raise ValueError("Cube top, bottom width must match left and right length")
    if not boards[left].W == boards[front].W == boards[right].W == boards[back].W:
        raise ValueError("Cube left, front, right and back must be the same width")

    if not boards[top].label == "top":
        raise ValueError(f"top label invalid: {boards[top].label}")
    if not boards[left].label == "left":
        raise ValueError(f"left label invalid: {boards[left].label}")
    if not boards[front].label == "front":
        raise ValueError(f"front label invalid: {boards[front].label}")
    if not boards[right].label == "right":
        raise ValueError(f"right label invalid: {boards[right].label}")
    if not boards[back].label == "back":
        raise ValueError(f"back label invalid: {boards[back].label}")
    if not boards[bottom].label == "bottom":
        raise ValueError(f"bottom label invalid: {boards[bottom].label}")

    area = sum(boards[side].area for side in all_sides)
    volume = boards[top].area * boards[front].W
    print(
        f"cube {boards[top].L :.1f} x {boards[top].W :.1f} x {boards[front].W :.1f} "
        f"area = {area / 100 :.2f} volume = {volume / 1000 :.2f} "
        f"aspect = {boards[top].aspect :.2f}"
    )

    return Board(boards[top].L, boards[top].W, boards[front].W)
