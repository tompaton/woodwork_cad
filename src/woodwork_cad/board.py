from dataclasses import dataclass, field
from typing import Iterable, Iterator, Optional, Tuple

from .cutlist import Cuts
from .defects import Defects
from .dovetails import Dovetails, peturb
from .faces import Face
from .geometry import Points3d
from .grooves import Grooves, Side
from .profile import Interpolator, Profile
from .shades import Shades
from .svg import SVGCanvas


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
    dovetails: Dovetails = field(default_factory=Dovetails)

    def __str__(self) -> str:
        label = " " + self.label if self.label else ""
        parent = self
        while parent.parent:
            parent = parent.parent
        parent_label = f" ({parent.label})" if parent.label else ""
        return f"{self.L} x {self.W} x {self.T}{label}{parent_label}"

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

    def dovetail_tails(
        self,
        tails: int = 3,
        base: float = 10.0,
        width: float = 20.0,
        angle: float = 15.0,
        right: bool = False,
    ) -> None:
        self.dovetails.add_tails(
            tails, self.L, self.W, self.T, base, width, angle, right
        )

    def dovetail_pins(
        self,
        tails: int = 3,
        base: float = 10.0,
        width: float = 20.0,
        angle: float = 15.0,
        right: bool = False,
    ) -> None:
        self.dovetails.add_pins(
            tails, self.L, self.W, self.T, base, width, angle, right
        )

    def draw_board(self, canvas: SVGCanvas, x: float, y: float) -> None:
        x1, x2 = self.profile.interpolate(self.T)

        # draw all faces separately from back to front to do basic hidden line removal
        for face in sorted(self._get_faces(x1, x2)):
            face.draw(canvas, x, y)

        for defect in self.defects:
            defect.draw(canvas, x, y)

        self._draw_cuts(canvas, x, y)

    def _get_faces(self, x1: Interpolator, x2: Interpolator) -> Iterable[Face]:
        # punch dovetail out of top & bottom faces and side
        for grooves in [False, True]:
            for face in self._get_front(x1, x2, grooves=grooves):
                yield face.remove(self.dovetails.faces(x1, x2))

            for face in self._get_back(x1, x2, grooves=grooves):
                yield face.remove(self.dovetails.faces(x1, x2))

        yield from self.dovetails.left_right(x1, self._get_left_right(x1), right=False)
        yield from self.dovetails.left_right(
            x2, self._get_left_right(x2).reverse(), right=True
        )

        for face in self.dovetails.faces_L:
            yield face.offset_profile(x1)
        for face in self.dovetails.faces_R:
            yield face.offset_profile(x2)

        yield from self._get_shade_front(x1, x2)
        yield from self._get_shade_right(x1, x2)

        sides = [Side(0.0, 0.0, self.T)]
        sides.extend(self.grooves.sides(self.T, top=True, face=False))
        sides.extend(self.grooves.sides(self.T, top=True, face=True))
        for side in sides:
            yield (
                self._get_top_bottom(x1, x2, side)
                .remove_side(self.dovetails.sides(x1, x2))
                .reverse()
            )

        sides = [Side(self.W, 0.0, self.T)]
        sides.extend(self.grooves.sides(self.T, top=False, face=False))
        sides.extend(self.grooves.sides(self.T, top=False, face=True))
        for side in sides:
            yield self._get_top_bottom(x1, x2, side).remove_side(
                self.dovetails.sides(x1, x2)
            )

    def _get_top_bottom(
        self,
        x1: Interpolator,
        x2: Interpolator,
        side: Side,
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

    def _get_shade_front(self, x1: Interpolator, x2: Interpolator) -> Iterator[Face]:
        face_clip = None
        for face in self._get_front(x1, x2, grooves=False):
            face_clip = face.remove(self.dovetails.faces(x1, x2))
            face_clip.points = peturb(face_clip.points)
            break

        for shade in self.shades:
            face_shade = Face(
                [
                    (x1(0), shade.y1, 0),
                    (x2(0), shade.y1, 0),
                    (x2(0), shade.y2, 0),
                    (x1(0), shade.y2, 0),
                ],
                "none",
                fill=shade.colour,
                zorder=1,
            )
            if face_clip:
                yield face_shade.clip_face(face_clip)
            else:
                yield face_shade

    def _get_shade_right(self, x1: Interpolator, x2: Interpolator) -> Iterator[Face]:
        if self.dovetails:
            for face_clip in self._get_shade_right_clip(x1, x2):
                face_clip.points = peturb(face_clip.points)
                x = face_clip.points[0][0] - x2(0) - x1(0)
                for shade in self._get_shade_right_face():
                    face2 = shade.clip_end_ex(face_clip)
                    if face2:
                        yield face2.offset_profile(x2).offset(dx=x)

        else:
            for shade in self._get_shade_right_face():
                yield shade.offset_profile(x2)

    def _get_shade_right_face(self) -> Iterator[Face]:
        for shade in self.shades:
            yield Face(
                [
                    (0.0, shade.y1, 0),
                    (0.0, shade.y1, self.T),
                    (0.0, shade.y2, self.T),
                    (0.0, shade.y2, 0),
                ],
                "none",
                fill=shade.colour,
                zorder=1,
            )

    def _get_shade_right_clip(
        self, x1: Interpolator, x2: Interpolator
    ) -> Iterator[Face]:
        yield from self.dovetails.left_right(
            x2, self._get_left_right(x2).reverse(), right=True
        )

        for face in self.dovetails.faces_R:
            if len({x for x, y, z in face.points}) == 1:
                yield face.offset_profile(x2)

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
