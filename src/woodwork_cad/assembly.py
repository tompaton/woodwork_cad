from typing import Iterator, List

from .board import Board
from .faces import Face, rotate_faces
from .geometry import Point3d, Points, Vector3d
from .svg import SVGCanvas


class Assembly:
    def __init__(self) -> None:
        self.origin: Point3d = (0.0, 0.0, 0.0)
        self.boards: List[Board] = []
        self.positions: List[Point3d] = []
        self.angles: List[float] = []

        self.subassemblies: List["Assembly"] = []

    def add_walls(self, angle: float, sides: List[Board]) -> None:
        rotate_y = 0.0
        offset = (0.0, 0.0, 0.0)
        for side in sides:
            self.boards.append(side)
            self.positions.append(offset)
            self.angles.append(rotate_y)

            # don't actually want to rotate any faces at this point, so pass in
            # empty list, but we want the rotated mate point as the next offset
            origin2d: List[Point3d] = []  # set in rotate_faces
            list(
                rotate_faces(
                    [],
                    side.profile.origin,
                    rotate_y,
                    offset,
                    side.profile.mate,
                    origin2d,
                )
            )

            offset = origin2d[1]

            rotate_y += angle

    def add_subassembly(self, offset: Vector3d, assembly: "Assembly") -> None:
        assembly.origin = offset
        self.subassemblies.append(assembly)

    def draw(self, canvas: SVGCanvas, x: float, y: float) -> None:
        for face in sorted(self.faces):
            face.draw(canvas, x, y)

    @property
    def faces(self) -> Iterator[Face]:
        x0, y0, z0 = self.origin
        for side, offset, rotate_y in zip(self.boards, self.positions, self.angles):
            x1, x2 = side.profile.interpolate(side.T)
            x, y, z = offset
            yield from rotate_faces(
                side._get_faces(x1, x2),
                side.profile.origin,
                rotate_y,
                (x + x0, y + y0, z + z0),
                side.profile.mate,
                [],
            )

        for assembly in self.subassemblies:
            yield from assembly.faces

    def draw_plan(self, canvas: SVGCanvas, x: float, y: float) -> Points:
        corners: Points = []
        for side, position, angle in zip(self.boards, self.positions, self.angles):
            x1, y1, z1 = position
            x2, y2 = side.draw_plan(canvas, x + x1, y + z1, angle)
            canvas.circle(x2, y2, 2, "red")
            corners.append((x2, y2))

        return corners
