from dataclasses import dataclass, field
from math import cos, radians, sin, sqrt
from typing import Callable, Iterable, List, Optional, Tuple

from .svg import Points, Points3d, SVGCanvas

__all__ = [
    "Board",
    "draw_boards",
    "cut",
    "cut_waste",
    "rip",
    "waste",
    "process",
    "process_all",
    "process_first",
    "joint2",
    "label_all",
    "cube_net",
]

Interpolator = Callable[[float], float]


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

    @property
    def colour(self) -> str:
        if self.op == "cut":
            return "green"
        elif self.op == "rip":
            return "blue"
        else:
            return "rgba(255,0,0,0.25)"

    @property
    def fill(self) -> str:
        if self.op == "cut":
            return "rgba(0,255,0,0.25)"
        elif self.op == "rip":
            return "rgba(0,0,255,0.25)"
        else:
            return "rgba(255,0,0,0.25)"


@dataclass
class Shade:
    y1: float
    y2: float
    colour: str


@dataclass
class Groove:
    y1: float
    y2: float
    depth: float
    face: bool


@dataclass
class Profile:
    x: float
    z: float


class Defect:
    def offset(self, offset_x: float, offset_y: float) -> "Defect":
        raise NotImplementedError

    def visible(self, offset_x: float, offset_y: float, L: float, W: float) -> bool:
        raise NotImplementedError

    def draw(self, canvas: SVGCanvas, x: float, y: float) -> None:
        raise NotImplementedError


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
class Board:
    L: float
    W: float
    T: float

    parent: Optional["Board"] = None
    offset_x: float = 0
    offset_y: float = 0

    cuts: list[Cut] = field(default_factory=list)

    _defects: list[Defect] = field(default_factory=list)
    _profile: List[Profile] = field(default_factory=list)

    label: str = ""
    _shade: List[Shade] = field(default_factory=list)
    _grooves: List[Groove] = field(default_factory=list)

    def __str__(self) -> str:
        return f"{self.L} x {self.W} x {self.T}"

    @property
    def area(self):
        return self.L * self.W

    @property
    def aspect(self):
        return self.L / self.W

    def add_defect(self, defect: Defect) -> None:
        self._defects.append(defect)

    @property
    def defects(self) -> Iterable[Defect]:
        yield from self._defects
        if self.parent:
            for defect in self.parent.defects:
                if defect.visible(self.offset_x, self.offset_y, self.L, self.W):
                    yield defect.offset(-self.offset_x, -self.offset_y)

    def source_defects(self, offset_x: float, offset_y: float) -> Iterable[Defect]:
        for defect in self.defects:
            yield defect.offset(offset_x, offset_y)

    def shade(self, colour: str) -> "Board":
        self._shade.append(Shade(0, self.W, colour))
        return self

    def select_shade(
        self, min_y: float, max_y: float, offset_y: float = 0
    ) -> List[Shade]:
        return [
            Shade(max(s.y1, min_y) + offset_y, min(s.y2, max_y) + offset_y, s.colour)
            for s in self._shade
            if s.y1 < max_y and s.y2 > min_y
        ]

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
        self.cuts.append(Cut(op, x1, y1, x2, y2, label, lx, ly))
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
                _shade=self.select_shade(0, self.W),
                _grooves=self.select_grooves(0, self.W),
            ),
            Board(
                self.L - length - kerf,
                self.W,
                self.T,
                self,
                length + kerf,
                0,
                _shade=self.select_shade(0, self.W),
                _grooves=self.select_grooves(0, self.W),
            ),
        ]

    def rip(self, width: float, kerf: float = 5):
        self.add_cut("rip", 0, width, self.L, width + kerf)
        return [
            Board(
                self.L, width, self.T, self, 0, 0, _shade=self.select_shade(0, width)
            ),
            Board(
                self.L,
                self.W - width - kerf,
                self.T,
                self,
                0,
                width + kerf,
                _shade=self.select_shade(width + kerf, self.W),
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

    @property
    def profile(self) -> List[Profile]:
        return self._profile or [
            Profile(0, 0),
            Profile(self.L, 0),
            Profile(self.L, self.T),
            Profile(0, self.T),
        ]

    def profile_length(self) -> Tuple[float, float]:
        def length(x1: float, y1: float, x2: float, y2: float) -> float:
            return sqrt((x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1))

        return length(
            self.profile[0].x, self.profile[0].z, self.profile[1].x, self.profile[1].z
        ), length(
            self.profile[2].x, self.profile[2].z, self.profile[3].x, self.profile[3].z
        )

    def mitre(self, left: float, right: float) -> List["Board"]:
        self._profile = self.profile

        # offset the point of rotation
        # length is base + hypotenuse of 60 degree triangle with height equal to the
        # board thickness
        hyp = self.T / sin(radians(left))
        offset_x = hyp * cos(radians(left))
        x1, y1 = self._profile[0].x, self._profile[1].z
        self._profile[0] = Profile(x1 + offset_x, y1)

        hyp = self.T / sin(radians(right))
        offset_x = hyp * cos(radians(right))
        x1, y1 = self._profile[1].x, self._profile[1].z
        self._profile[1] = Profile(x1 - offset_x, y1)

        return [self]

    def flip_profile(self) -> None:
        a, b, c, d = self.profile
        self._profile = [
            Profile(d.x, a.z),
            Profile(c.x, b.z),
            Profile(b.x, c.z),
            Profile(a.x, d.z),
        ]

        self.L = self._profile[1].x - self._profile[0].x

    def groove(self, y: float, height: float, depth: float, face: bool = True) -> None:
        self._grooves.append(Groove(y, y + height, depth, face))

    def select_grooves(
        self, min_y: float, max_y: float, offset_y: float = 0
    ) -> List[Groove]:
        return [
            Groove(
                max(groove.y1, min_y) + offset_y,
                min(groove.y2, max_y) + offset_y,
                groove.depth,
                groove.face,
            )
            for groove in self._grooves
            if groove.y1 < max_y and groove.y2 > min_y
        ]

    def dado(self, x: float, width: float, depth: float, face: bool = True) -> None:
        raise NotImplementedError

    def draw_board(self, canvas: SVGCanvas, x: float, y: float) -> None:
        x1, x2 = self._interpolate_profile(self.profile)

        # draw all faces separately from back to front to do basic hidden line removal
        self._draw_top_bottom(canvas, x, y, x1, x2, 0.0, 0.0, self.T)
        self._draw_back(canvas, x, y, x1, x2, grooves=False)
        self._draw_left_right(canvas, x, y, x1)
        for y1, z1, z2 in self._groove_sides(top=True, face=False):
            self._draw_top_bottom(canvas, x, y, x1, x2, y1, z1, z2)
        for y1, z1, z2 in self._groove_sides(top=False, face=False):
            self._draw_top_bottom(canvas, x, y, x1, x2, y1, z1, z2)
        self._draw_back(canvas, x, y, x1, x2, grooves=True)
        self._draw_front(canvas, x, y, x1, x2, grooves=True)
        for y1, z1, z2 in self._groove_sides(top=True, face=True):
            self._draw_top_bottom(canvas, x, y, x1, x2, y1, z1, z2)
        for y1, z1, z2 in self._groove_sides(top=False, face=True):
            self._draw_top_bottom(canvas, x, y, x1, x2, y1, z1, z2)
        self._draw_top_bottom(canvas, x, y, x1, x2, self.W, 0.0, self.T)
        self._draw_left_right(canvas, x, y, x2)
        self._draw_front(canvas, x, y, x1, x2, grooves=False)

        self._draw_shade(canvas, x, y, x1, x2)

        for defect in self.defects:
            defect.draw(canvas, x, y)

        self._draw_cuts(canvas, x, y)

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

    def _groove_flats(self, face: bool) -> Iterable[Tuple[float, float, float]]:
        y0 = 0.0
        for groove in self._grooves:
            if groove.face == face:
                yield (0.0 if face else self.T, y0, groove.y1)
                yield (
                    groove.depth if face else self.T - groove.depth,
                    groove.y1,
                    groove.y2,
                )
                y0 = groove.y2
        yield (0.0 if face else self.T, y0, self.W)

    def _groove_sides(
        self, top: bool, face: bool
    ) -> Iterable[Tuple[float, float, float]]:
        for groove in self._grooves:
            if top:
                if groove.face and face:
                    yield (groove.y2, 0.0, groove.depth)
                if not groove.face and not face:
                    yield (groove.y2, self.T - groove.depth, self.T)
            else:
                if groove.face and face:
                    yield (groove.y1, 0.0, groove.depth)
                if not groove.face and not face:
                    yield (groove.y1, self.T - groove.depth, self.T)

    def _interpolate_profile(
        self, profile: List[Profile]
    ) -> Tuple[Interpolator, Interpolator]:
        # interpolate x along profile
        def x1(z: float) -> float:
            return profile[0].x + z * (profile[3].x - profile[0].x) / self.T

        def x2(z: float) -> float:
            return profile[1].x + z * (profile[2].x - profile[1].x) / self.T

        return x1, x2

    def _draw_top_bottom(
        self,
        canvas: SVGCanvas,
        x: float,
        y: float,
        x1: Interpolator,
        x2: Interpolator,
        y1: float,
        z1: float,
        z2: float,
    ) -> None:
        canvas.polyline3d(
            "silver",
            [
                (x + x1(z1), y + y1, z1),
                (x + x2(z1), y + y1, z1),
                (x + x2(z2), y + y1, z2),
                (x + x1(z2), y + y1, z2),
                (x + x1(z1), y + y1, z1),
            ],
            fill="rgba(192,192,192,0.25)",
        )

    def _draw_left_right(
        self, canvas: SVGCanvas, x: float, y: float, xz: Interpolator
    ) -> None:
        points: Points3d = []

        for z, y1, y2 in self._groove_flats(True):
            points.extend(
                [
                    (x + xz(z), y + y1, z),
                    (x + xz(z), y + y2, z),
                ]
            )

        for z, y1, y2 in reversed(list(self._groove_flats(False))):
            points.extend(
                [
                    (x + xz(z), y + y2, z),
                    (x + xz(z), y + y1, z),
                ]
            )

        canvas.polyline3d("silver", points, fill="rgba(255,255,255,0.75)", closed=True)

    def _draw_front(
        self,
        canvas: SVGCanvas,
        x: float,
        y: float,
        x1: Interpolator,
        x2: Interpolator,
        grooves: bool,
    ) -> None:
        for z, y1, y2 in sorted(self._groove_flats(True), reverse=True):
            if (grooves and z == 0.0) or (not grooves and z != 0.0):
                continue

            canvas.polyline3d(
                "black",
                [
                    (x + x1(z), y + y1, z),
                    (x + x2(z), y + y1, z),
                    (x + x2(z), y + y2, z),
                    (x + x1(z), y + y2, z),
                    (x + x1(z), y + y1, z),
                ],
                fill="rgba(255,255,255,0.75)",
            )

    def _draw_back(
        self,
        canvas: SVGCanvas,
        x: float,
        y: float,
        x1: Interpolator,
        x2: Interpolator,
        grooves: bool,
    ) -> None:
        for z, y1, y2 in sorted(self._groove_flats(False), reverse=True):
            if (grooves and z == self.T) or (not grooves and z != self.T):
                continue

            canvas.polyline3d(
                "silver",
                [
                    (x + x1(z), y + y1, z),
                    (x + x2(z), y + y1, z),
                    (x + x2(z), y + y2, z),
                    (x + x1(z), y + y2, z),
                    (x + x1(z), y + y1, z),
                ],
                fill="rgba(192,192,192,0.25)",
            )

    def _draw_shade(
        self, canvas: SVGCanvas, x: float, y: float, x1: Interpolator, x2: Interpolator
    ) -> None:
        for shade in self._shade:
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

    def draw_plan(
        self,
        canvas: SVGCanvas,
        x: float,
        y: float,
        angle: float,
        colour: str = "black",
    ) -> Tuple[float, float]:
        offset = self.profile[0]
        points = [(p.x - offset.x, p.z - offset.z) for p in self.profile]
        cos_a = cos(radians(angle))
        sin_a = sin(radians(angle))
        rotated = [
            (
                x + x1 * cos_a - y1 * sin_a,
                y + x1 * sin_a + y1 * cos_a,
            )
            for (x1, y1) in points
        ]
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


def mitre(left: float, right: float):
    def operation(board: Board):
        return board.mitre(left, right)

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

    defects: List[Defect] = []
    shade: List[Shade] = []
    offset_y = 0.0
    for board in boards:
        defects.extend(board.source_defects(0, offset_y))
        shade.extend(board.select_shade(0, board.W, offset_y))
        offset_y += board.W

    return Board(
        boards[0].L,
        sum(board.W for board in boards),
        boards[0].T,
        label=label,
        _defects=defects,
        _shade=shade,
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
