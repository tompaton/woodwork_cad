from dataclasses import dataclass
from itertools import pairwise
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, Tuple

from woodwork_cad.geometry import (
    Point,
    Point3d,
    Points3d,
    Vector3d,
    clip_polygon2,
    cross,
    equal_vectors,
    get_lighting,
    normalize,
    point_rotator,
    subtract,
)
from woodwork_cad.profile import Interpolator
from woodwork_cad.svg import SVGCanvas

DEBUG = False


@dataclass
class Face:
    points: Points3d
    colour: str = ""
    fill: str = ""
    zorder: int = 0

    def __post_init__(self) -> None:
        self.__centroid: Optional[Point3d] = None
        self.__normal: Optional[Vector3d] = None

    def reverse(self) -> "Face":
        self.points.reverse()
        self.__normal = None
        return self

    def offset(self, dx: float = 0, dy: float = 0, dz: float = 0) -> "Face":
        return Face(
            [Point3d(p.x + dx, p.y + dy, p.z + dz) for p in self.points],
            self.colour,
            self.fill,
            self.zorder,
        )

    def offset_profile(self, xz: Interpolator) -> "Face":
        return Face(
            [Point3d(p.x + xz(p.y, p.z), p.y, p.z) for p in self.points],
            self.colour,
            self.fill,
            self.zorder,
        )

    def __lt__(self, other: Any) -> bool:
        # this is pretty slow, make sure sorted() is used with key= to avoid
        # repeated centroid computations
        return self._key < other._key

    @property
    def _key(self) -> Tuple[int, float, float, float]:
        # z-order (reversed), then top to bottom, left to right
        center = self.centroid
        return (self.zorder, -center.z, center.x, center.y)

    def draw(self, canvas: SVGCanvas, offset_x: float, offset_y: float) -> None:
        if not self.points:
            return

        normal = self.normal

        if self.colour:
            colour = self.colour
            styles: Dict[str, Any] = {}
            if self.fill:
                styles["fill"] = self.fill
        else:
            colour, styles = self.get_style(normal)

        canvas.polyline3d(
            colour, self.points, x=offset_x, y=offset_y, closed=True, **styles
        )

        if DEBUG:
            x, y, z = self.points[0].x, self.points[0].y, self.points[0].z
            edge = normalize(subtract(self.points[1], self.points[0]))
            canvas.polyline3d(
                self.colour or "orange",
                [
                    Point3d(x, y, z),
                    Point3d(x + 15 * edge.x, y + 15 * edge.y, z + 15 * edge.z),
                    Point3d(x + 10 * edge.x - 2, y + 15 * edge.y - 2, z + 15 * edge.z),
                ],
                x=offset_x - 3,
                y=offset_y - 5,
                fill="none",
            )
            # draw normal from face centroid
            x, y, z = self.centroid.x, self.centroid.y, self.centroid.z
            canvas.polyline3d(
                self.colour or "orange",
                [
                    Point3d(x, y, z),
                    Point3d(
                        x + 15 * normal.x,
                        y + 15 * normal.y,
                        z + 15 * normal.z,
                    ),
                    Point3d(
                        x + 15 * normal.x - 2,
                        y + 15 * normal.y,
                        z + 10 * normal.z,
                    ),
                ],
                x=offset_x,
                y=offset_y,
                fill="none",
            )

    def get_style(self, normal: Vector3d) -> Tuple[str, Dict[str, Any]]:
        dash = ""

        camera, light, plan = get_lighting(normal)

        if plan:
            return "black", {}

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

        return colour, dict(stroke_dasharray=dash, fill=fill)

    @property
    def normal(self) -> Vector3d:
        if not self.points:
            return Vector3d(0.0, 0.0, 0.0)

        # normal is called a lot, but we can cache it as any change to the
        # original points won't actually change the normal, except we do need
        # to recalculate when the points are reversed.

        if self.__normal is None:
            # for concave polygons we need to sum all cross products
            # between centroid and each pair of points
            C = self.centroid
            sx = sy = sz = 0.0
            for a, b in pairwise(self.points + self.points[:1]):
                n = cross(subtract(b, C), subtract(a, C))
                sx += n.x
                sy += n.y
                sz += n.z
            self.__normal = normalize(Vector3d(sx, sy, sz))
        return self.__normal

    @property
    def centroid(self) -> Point3d:
        if not self.points:
            return Point3d(0.0, 0.0, 0.0)

        # centroid is called a lot.  but we can cache it as it doesn't need to
        # be all that accurate so we can use the original points.
        # even reversing the points won't change it...

        if self.__centroid is None:
            min_x = min(p.x for p in self.points)
            max_x = max(p.x for p in self.points)
            min_y = min(p.y for p in self.points)
            max_y = max(p.y for p in self.points)
            min_z = min(p.z for p in self.points)
            max_z = max(p.z for p in self.points)
            self.__centroid = Point3d(
                (max_x + min_x) / 2,
                (max_y + min_y) / 2,
                (max_z + min_z) / 2,
            )
        return self.__centroid

    def remove(self, clip_regions: Callable[[float], Iterable["Face"]]) -> "Face":
        # clip the dovetail regions out of the face
        z = self.points[0].z
        clipped = False
        result_poly = self.points[:]
        for region in clip_regions(z):
            if result_poly:
                clipped = True
                clip_poly = [Point(q.x, q.y) for q in region.points]
                result_poly = [
                    Point3d(p.x, p.y, z)
                    for p in clip_polygon2(
                        clip_poly,
                        [Point(q.x, q.y) for q in result_poly],
                    )[0]
                ]

        if clipped:
            return Face(result_poly, self.colour, self.fill, self.zorder).check_normal(
                self
            )

        return self

    def remove_side(self, clip_regions: Callable[[float], Iterable["Face"]]) -> "Face":
        y = self.points[0].y
        clipped = False
        result_poly = self.points[:]
        for region in clip_regions(y):
            if result_poly:
                clipped = True
                clip_poly = [Point(q.x, q.z) for q in region.points]
                result_poly = [
                    Point3d(p.x, y, p.y)
                    for p in clip_polygon2(
                        clip_poly,
                        [Point(q.x, q.z) for q in result_poly],
                    )[0]
                ]

        if clipped:
            return Face(result_poly, self.colour, self.fill, self.zorder).check_normal(
                self
            )

        return self

    def clip_end(self, clip_region: "Face") -> "Face":
        return self.clip_end_ex(clip_region) or self

    def clip_end_ex(self, clip_region: "Face") -> Optional["Face"]:
        clip_poly = [Point(q.y, q.z) for q in clip_region.points]
        result_poly = [
            Point3d(0.0, p.x, p.y)
            for p in clip_polygon2(
                clip_poly, [Point(q.y, q.z) for q in self.points], "intersection"
            )[0]
        ]

        return (
            Face(result_poly, self.colour, self.fill, self.zorder)
            if result_poly
            else None
        )

    def clip_face(self, clip_region: "Face") -> "Face":
        clip_poly = [Point(q.x, q.y) for q in clip_region.points]
        z = self.points[0].z
        result_poly = [
            Point3d(p.x, p.y, z)
            for p in clip_polygon2(
                clip_poly, [Point(q.x, q.y) for q in self.points], "intersection"
            )[0]
        ]

        return (
            Face(result_poly, self.colour, self.fill, self.zorder)
            if result_poly
            else self
        )

    def check_normal(self, original: "Face") -> "Face":
        # make sure normal isn't altered
        if not equal_vectors(self.normal, original.normal):
            return self.reverse()
        else:
            return self


def rotate_faces(
    faces: Iterable[Face],
    origin: Point3d,
    rotate_y: float,
    offset: Vector3d,
    mate: Point3d,
    origin2d_out: List[Point3d],
) -> Iterator[Face]:
    if rotate_y == 0.0 and (offset.x, offset.y, offset.z) == (0.0, 0.0, 0.0):
        yield from faces
        origin2d_out.append(origin)
        origin2d_out.append(mate)
        return

    rotate = point_rotator(rotate_y, origin.x, origin.z, offset.x, offset.z)

    def rotate3d(point: Point3d) -> Point3d:
        rotated = rotate(Point(point.x, point.z))
        return Point3d(rotated.x, point.y + offset.y, rotated.y)

    for face in faces:
        yield Face(
            [rotate3d(p) for p in face.points], face.colour, face.fill, face.zorder
        )

    origin2d_out.append(rotate3d(origin))
    origin2d_out.append(rotate3d(mate))
