from dataclasses import dataclass, field
from operator import attrgetter
from typing import Iterable, Iterator, List, Optional, Tuple

from .cutlist import Cuts
from .defects import Defects
from .dovetails import Dovetails, peturb
from .faces import Face, rotate_faces
from .geometry import Point3d, Points3d, Vector3d
from .grooves import Grooves, Side
from .profile import Interpolator, Profile
from .shades import Shades
from .svg import SVGCanvas


@dataclass
class Size:
    length: float  # x
    width: float  # z
    depth: float  # y

    def expand(
        self, length: float = 0.0, width: float = 0.0, depth: float = 0.0
    ) -> "Size":
        return Size(self.length + length, self.width + width, self.depth + depth)

    def contract(
        self, length: float = 0.0, width: float = 0.0, depth: float = 0.0
    ) -> "Size":
        return Size(self.length - length, self.width - width, self.depth - depth)


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

    def rotate(
        self, rotate_x: float = 0.0, rotate_y: float = 0.0, rotate_z: float = 0.0
    ) -> None:
        # don't actually rotate for now, just switch the dimensions, so this will
        # only work for flat boards for base/lid etc.
        if rotate_x == 90.0:
            self.W, self.T = self.T, self.W
            self._profile = Profile()
        elif rotate_y == 90.0:
            self.L, self.T = self.T, self.L
            self._profile = Profile()
        else:
            msg = f"rotate currently doesn't support {rotate_x=}, {rotate_y=}, {rotate_z=}"
            raise NotImplementedError(msg)

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
        L: float = 0,
        W: float = 0,
    ):
        self.cuts.add(op, x1, y1, x2, y2, label, lx, ly, L, W)
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
                L,
                W,
            )

    def cut(self, length: float, kerf: float = 5):
        self.add_cut("cut", length, 0, length + kerf, self.W, L=length)
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
        self.add_cut("rip", 0, width, self.L, width + kerf, W=width)
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

    def draw_board(
        self,
        canvas: SVGCanvas,
        x: float,
        y: float,
        rotate_y: float = 0.0,
        offset: Vector3d = Vector3d(0.0, 0.0, 0.0),
    ) -> Tuple[Point3d, Point3d]:
        faces: List[Face] = []
        origin, mate = self.rotated_faces(rotate_y, offset, faces)

        # draw all faces separately from back to front to do basic hidden line removal
        for face in sorted(faces, key=attrgetter("_key")):
            face.draw(canvas, x, y)

        for defect in self.defects:
            defect.draw(canvas, x, y)

        self._draw_cuts(canvas, x, y)

        return origin, mate

    def rotated_faces(
        self,
        rotate_y: float,
        offset: Vector3d,
        faces: List[Face],
    ) -> Tuple[Point3d, Point3d]:
        x1, x2 = self.profile.interpolate(self.T)
        origin = self.profile.origin
        mate = self.profile.mate
        origin2d: List[Point3d] = []  # set in rotate_faces

        faces.extend(
            rotate_faces(
                self._get_faces(x1, x2), origin, rotate_y, offset, mate, origin2d
            )
        )

        return origin2d[0], origin2d[1]

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
                Point3d(x1(side.z1), side.y, side.z1),
                Point3d(x2(side.z1), side.y, side.z1),
                Point3d(x2(side.z2), side.y, side.z2),
                Point3d(x1(side.z2), side.y, side.z2),
            ],
        )

    def _get_left_right(self, xz: Interpolator) -> Face:
        points: Points3d = []

        for flat in self.grooves.flats(self.W, self.T, face=True):
            points.extend(
                [
                    Point3d(xz(flat.z), flat.y1, flat.z),
                    Point3d(xz(flat.z), flat.y2, flat.z),
                ]
            )

        for flat in reversed(list(self.grooves.flats(self.W, self.T, face=False))):
            points.extend(
                [
                    Point3d(xz(flat.z), flat.y2, flat.z),
                    Point3d(xz(flat.z), flat.y1, flat.z),
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
                    Point3d(x1(flat.z), flat.y1, flat.z),
                    Point3d(x2(flat.z), flat.y1, flat.z),
                    Point3d(x2(flat.z), flat.y2, flat.z),
                    Point3d(x1(flat.z), flat.y2, flat.z),
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
                    Point3d(x1(flat.z), flat.y1, flat.z),
                    Point3d(x1(flat.z), flat.y2, flat.z),
                    Point3d(x2(flat.z), flat.y2, flat.z),
                    Point3d(x2(flat.z), flat.y1, flat.z),
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
                    Point3d(x1(0), shade.y1, 0),
                    Point3d(x2(0), shade.y1, 0),
                    Point3d(x2(0), shade.y2, 0),
                    Point3d(x1(0), shade.y2, 0),
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
                x = face_clip.points[0].x - x2(0) - x1(0)
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
                    Point3d(0.0, shade.y1, 0),
                    Point3d(0.0, shade.y1, self.T),
                    Point3d(0.0, shade.y2, self.T),
                    Point3d(0.0, shade.y2, 0),
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
            if len({p.x for p in face.points}) == 1:
                yield face.offset_profile(x2)

    def _draw_cuts(self, canvas: SVGCanvas, x: float, y: float) -> None:
        order = 0
        for cut in self.cuts:
            if cut.op:
                if cut.y2 == self.W:
                    points = [
                        Point3d(cut.x1, cut.y1, 0),
                        Point3d(cut.x2 + 1, cut.y1, 0),
                        Point3d(cut.x2 + 1, cut.y2, 0),
                        # continue around edge
                        Point3d(cut.x2 + 1, cut.y2, self.T),
                        Point3d(cut.x1, cut.y2, self.T),
                        Point3d(cut.x1, cut.y2, 0),
                    ]
                else:
                    points = [
                        Point3d(cut.x1, cut.y1, 0),
                        Point3d(cut.x2 + 1, cut.y1, 0),
                        Point3d(cut.x2 + 1, cut.y2, 0),
                        Point3d(cut.x1, cut.y2, 0),
                    ]

                canvas.polyline3d(
                    cut.colour, points, x=x, y=y, fill=cut.fill, closed=True
                )

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

    def get_dimension(
        self, dimension: str, position: str, pad: float = 10
    ) -> Tuple[Point3d, Point3d, Point3d, Point3d, str]:
        if dimension == "W" and position == "right":
            corner_top = Point3d(self.L, 0, 0)
            corner_bottom = Point3d(self.L, self.W, 0)
            arrow_top = corner_top.offset(dx=pad)
            arrow_bottom = corner_bottom.offset(dx=pad)

            return corner_top, corner_bottom, arrow_top, arrow_bottom, f"{self.W:.0f}"

        elif dimension == "W" and position == "left":
            corner_top = Point3d(0, 0, 0)
            corner_bottom = Point3d(0, self.W, 0)
            arrow_top = corner_top.offset(dx=-pad)
            arrow_bottom = corner_bottom.offset(dx=-pad)

            return corner_top, corner_bottom, arrow_top, arrow_bottom, f"{self.W:.0f}"

        elif dimension == "L" and position == "below":
            corner_left = Point3d(0, self.W, 0)
            corner_right = Point3d(self.L, self.W, 0)
            arrow_left = corner_left.offset(dy=pad)
            arrow_right = corner_right.offset(dy=pad)

            return corner_left, corner_right, arrow_left, arrow_right, f"{self.L:.0f}"

        elif dimension == "L" and position == "above":
            corner_left = Point3d(0, 0, 0)
            corner_right = Point3d(self.L, 0, 0)
            arrow_left = corner_left.offset(dy=-pad)
            arrow_right = corner_right.offset(dy=-pad)

            return corner_left, corner_right, arrow_left, arrow_right, f"{self.L:.0f}"

        elif dimension == "T" and position == "below":
            corner_left = Point3d(0, self.W, 0)
            corner_right = Point3d(0, self.W, self.T)
            arrow_left = corner_left.offset(dx=-pad, dy=pad)
            arrow_right = corner_right.offset(dx=-pad, dy=pad)

            return corner_left, corner_right, arrow_left, arrow_right, f"{self.T:.0f}"

        elif dimension == "T" and position == "above":
            corner_left = Point3d(self.L, 0, 0)
            corner_right = Point3d(self.L, 0, self.T)
            arrow_left = corner_left.offset(dx=pad, dy=-pad)
            arrow_right = corner_right.offset(dx=pad, dy=-pad)

            return corner_left, corner_right, arrow_left, arrow_right, f"{self.T:.0f}"

        else:
            msg = f"Unsupported {dimension=} and {position=}"
            raise ValueError(msg)

    def draw_cut_dimensions(self, canvas: SVGCanvas, x: float, y: float) -> float:
        from .operations import draw_dimension_ex

        pad = 30.0
        rip_pad = pad
        for cut in self.cuts:
            if cut.op == "rip":
                corner_top = Point3d(self.L, cut.y1 - cut.W, 0)
                corner_bottom = Point3d(self.L, cut.y1, 0)
                arrow_top = corner_top.offset(dx=rip_pad)
                arrow_bottom = corner_bottom.offset(dx=rip_pad)
                draw_dimension_ex(
                    canvas,
                    x,
                    y,
                    corner_top,
                    corner_bottom,
                    arrow_top,
                    arrow_bottom,
                    f"{cut.W:.0f}",
                    "W",
                    "right",
                )

        # sort and remove duplicates
        seen = set()
        cuts = []
        for cut in self.cuts:
            if cut.op == "cut":
                key = (cut.x1, cut.L)
                if key not in seen:
                    cuts.append(cut)
                seen.add(key)
        cuts = sorted(cuts, key=attrgetter("L"))
        cut_pad = [pad for cut in cuts]

        for i, cut in enumerate(cuts):
            corner_left = Point3d(cut.x1 - cut.L, self.W, 0)
            corner_right = Point3d(cut.x1, self.W, 0)
            arrow_left = corner_left.offset(dy=cut_pad[i])
            arrow_right = corner_right.offset(dy=cut_pad[i])
            draw_dimension_ex(
                canvas,
                x,
                y,
                corner_left,
                corner_right,
                arrow_left,
                arrow_right,
                f"{cut.L:.0f}",
                "L",
                "below",
            )
            for j in range(i + 1, len(cuts)):
                if cut.x1 > (cuts[j].x1 - cuts[j].L) and (cut.x1 - cut.L) < cuts[j].x1:
                    cut_pad[j] = max(cut_pad[j], cut_pad[i] + pad)

        return max(cut_pad, default=0.0)
