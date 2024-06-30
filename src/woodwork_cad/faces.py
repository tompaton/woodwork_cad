from dataclasses import dataclass
from itertools import pairwise
from typing import Any, Callable, Dict, Iterable, Optional, Tuple

from .geometry import (
    CAMERA,
    LIGHT,
    Points3d,
    Vector3d,
    clip_polygon2,
    cross,
    dotproduct,
    equal_vectors,
    normalize,
    subtract,
)
from .profile import Interpolator
from .svg import SVGCanvas

DEBUG = False


@dataclass
class Face:
    points: Points3d
    colour: str = ""
    fill: str = ""
    zorder: int = 0

    def reverse(self) -> "Face":
        self.points.reverse()
        return self

    def offset(self, dx: float = 0, dy: float = 0, dz: float = 0) -> "Face":
        return Face(
            [(x + dx, y + dy, z + dz) for x, y, z in self.points],
            self.colour,
            self.fill,
            self.zorder,
        )

    def offset_profile(self, xz: Interpolator) -> "Face":
        return Face(
            [(x + xz(z), y, z) for x, y, z in self.points],
            self.colour,
            self.fill,
            self.zorder,
        )

    def __lt__(self, other: Any) -> bool:
        return self._key < other._key

    @property
    def _key(self) -> Tuple[int, float, float, float]:
        # z-order (reversed), then top to bottom, left to right
        center = self.centroid
        return (self.zorder, -center[2], center[0], center[1])

    def draw(self, canvas: SVGCanvas, offset_x: float, offset_y: float) -> None:
        normal = self.normal

        if self.colour:
            colour = self.colour
            styles: Dict[str, Any] = {}
            if self.fill:
                styles["fill"] = self.fill
        else:
            colour, styles = self.get_style(normal)

        canvas.polyline3d(
            colour,
            [(x + offset_x, y + offset_y, z) for x, y, z in self.points],
            closed=True,
            **styles,
        )

        if DEBUG:
            x, y, z = self.points[0]
            dx, dy, dz = normalize(subtract(self.points[1], self.points[0]))
            canvas.polyline3d(
                self.colour or "orange",
                [
                    (x + offset_x - 3, y + offset_y - 5, z),
                    (
                        x + offset_x - 3 + 15 * dx,
                        y + offset_y + 15 * dy - 5,
                        z + 15 * dz,
                    ),
                    (
                        x + offset_x - 3 + 10 * dx - 2,
                        y + offset_y + 15 * dy - 5 - 2,
                        z + 15 * dz,
                    ),
                ],
                fill="none",
            )
            # draw normal from face centroid
            x, y, z = self.centroid
            canvas.polyline3d(
                self.colour or "orange",
                [
                    (x + offset_x, y + offset_y, z),
                    (
                        x + offset_x + 15 * normal[0],
                        y + offset_y + 15 * normal[1],
                        z + 15 * normal[2],
                    ),
                    (
                        x + offset_x + 15 * normal[0] - 2,
                        y + offset_y + 15 * normal[1],
                        z + 10 * normal[2],
                    ),
                ],
                fill="none",
            )

    def get_style(self, normal: Vector3d) -> Tuple[str, Dict[str, Any]]:
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

        return colour, dict(stroke_dasharray=dash, fill=fill)

    @property
    def normal(self) -> Vector3d:
        # for concave polygons we need to sum all cross products
        # between centroid and each pair of points
        C = self.centroid
        sx = sy = sz = 0.0
        for a, b in pairwise(self.points + self.points[:1]):
            n = cross(subtract(b, C), subtract(a, C))
            sx += n[0]
            sy += n[1]
            sz += n[2]
        return normalize((sx, sy, sz))

    @property
    def centroid(self) -> Vector3d:
        min_x = min(x for x, y, z in self.points)
        max_x = max(x for x, y, z in self.points)
        min_y = min(y for x, y, z in self.points)
        max_y = max(y for x, y, z in self.points)
        min_z = min(z for x, y, z in self.points)
        max_z = max(z for x, y, z in self.points)
        return ((max_x + min_x) / 2, (max_y + min_y) / 2, (max_z + min_z) / 2)

    def remove(self, clip_regions: Callable[[float], Iterable["Face"]]) -> "Face":
        # clip the dovetail regions out of the face
        z = self.points[0][2]
        clipped = False
        result_poly = self.points[:]
        for region in clip_regions(z):
            clipped = True
            clip_poly = [(x, y) for x, y, z in region.points]
            result_poly = [
                (x, y, z)
                for x, y in clip_polygon2(
                    clip_poly,
                    [(x, y) for x, y, z in result_poly],
                )[0]
            ]

        if clipped:
            return Face(result_poly, self.colour, self.fill, self.zorder).check_normal(
                self
            )

        return self

    def remove_side(self, clip_regions: Callable[[float], Iterable["Face"]]) -> "Face":
        y = self.points[0][1]
        clipped = False
        result_poly = self.points[:]
        for region in clip_regions(y):
            clipped = True
            clip_poly = [(x, z) for x, y, z in region.points]
            result_poly = [
                (x, y, z)
                for x, z in clip_polygon2(
                    clip_poly,
                    [(x, z) for x, y, z in result_poly],
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
        clip_poly = [(y, z) for x, y, z in clip_region.points]
        result_poly = [
            (0.0, y, z)
            for y, z in clip_polygon2(
                clip_poly, [(y, z) for x, y, z in self.points], "intersection"
            )[0]
        ]

        return (
            Face(result_poly, self.colour, self.fill, self.zorder)
            if result_poly
            else None
        )

    def clip_face(self, clip_region: "Face") -> "Face":
        clip_poly = [(x, y) for x, y, z in clip_region.points]
        z = self.points[0][2]
        result_poly = [
            (x, y, z)
            for x, y in clip_polygon2(
                clip_poly, [(x, y) for x, y, z in self.points], "intersection"
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
